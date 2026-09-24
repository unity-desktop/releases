"""
Registry access through oras-py.
"""

from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from http import HTTPStatus
from pathlib import Path

import oras.oci
import oras.provider
from loguru import logger
from oras.container import Container
from pydantic import SecretStr
from requests import Response

from releases.core.constants import FILE_TYPE, MANIFEST_TYPE, TITLE, WORKERS
from releases.core.errors import RegistryError
from releases.oci.models import Descriptor, Digest, Manifest


@contextmanager
def failure(what: str) -> Iterator[None]:
    """
    Raise a RegistryError for an oras-py or network error.
    """
    try:
        yield
    except (OSError, ValueError) as error:
        raise RegistryError(f"{what}: {error}") from error


def checked(what: str, response: Response) -> Response:
    """
    Raise a RegistryError for an HTTP error status.
    """
    if not response.ok:
        raise RegistryError(f"{what}: HTTP {response.status_code} {response.reason}")
    return response


class Registry:
    """
    Resolve, read, pull and push artifacts by host/name:tag or host/name@digest.
    """

    def __init__(self, username: str | None = None, password: SecretStr | None = None) -> None:
        """
        Log in if a user and password are given. Read anonymously if not.
        """
        self._client = oras.provider.Registry()
        if username and password:
            self._client.auth.set_basic_auth(username, password.get_secret_value())

    def resolve(self, reference: str) -> Digest | None:
        """
        Return the digest of a tag, or None if the tag does not exist.
        """
        # oras-py has no resolve call, so send a HEAD request like its delete_tag does.
        container = self._client.get_container(reference)
        with failure(reference):
            response = self._client.do_request(
                f"{self._client.prefix}://{container.manifest_url()}",
                "HEAD",
                headers={"Accept": MANIFEST_TYPE},
            )
        if response.status_code == HTTPStatus.NOT_FOUND:
            logger.debug("{} does not exist", reference)
            return None
        return Digest(checked(reference, response).headers["Docker-Content-Digest"])

    def manifest(self, reference: str) -> Manifest:
        """
        Return a manifest.
        """
        with failure(reference):
            found = self._client.get_manifest(reference, allowed_media_type=[MANIFEST_TYPE])
        return Manifest.model_validate(found)

    def blob(self, reference: str, layer: Descriptor) -> bytes:
        """
        Return the content of a layer.
        """
        what = f"{reference} {layer.title}"
        with failure(what):
            response = self._client.get_blob(reference, layer.digest)
        return checked(what, response).content

    def pull(self, reference: str, directory: Path) -> list[Path]:
        """
        Download each file of an artifact into a directory.
        """
        with failure(reference):
            files = [Path(file) for file in self._client.pull(reference, outdir=str(directory))]
        logger.info("pulled {} files of {}", len(files), reference)
        return files

    def push(self, directory: Path, target: str, annotations: dict[str, str]) -> Digest:
        """
        Push every file under a directory as one artifact. Return its digest.
        """
        container = self._client.get_container(target)
        files = sorted(path for path in directory.rglob("*") if path.is_file())
        logger.info("pushing {} files to {}", len(files), target)

        # push() uploads one file at a time, so build the same manifest in parallel.
        with failure(target), ThreadPoolExecutor(WORKERS) as pool:
            layers = list(pool.map(lambda path: self._upload(container, directory, path), files))
            config, _ = oras.oci.ManifestConfig()
            with oras.provider.temporary_empty_config() as config_file:
                checked(target, self._client.upload_blob(config_file, container, config))
            manifest = oras.oci.NewManifest() | {
                "config": config,
                "layers": layers,
                "annotations": annotations,
            }
            response = checked(target, self._client.upload_manifest(manifest, container))

        digest = Digest(response.headers["Docker-Content-Digest"])
        logger.info("pushed {} as {}", target, digest)
        return digest

    def _upload(self, container: Container, directory: Path, path: Path) -> dict:
        # apt-transport-oci reads the title as the file path.
        title = path.relative_to(directory).as_posix()
        layer = oras.oci.NewLayer(str(path), media_type=FILE_TYPE)
        layer["annotations"] = {TITLE: title}
        checked(title, self._client.upload_blob(str(path), container, layer))
        logger.debug("uploaded {}", title)
        return layer

    def tag(self, reference: str, target: str) -> None:
        """
        Add a tag to a pushed manifest.
        """
        with failure(target):
            manifest = self._client.get_manifest(reference, allowed_media_type=[MANIFEST_TYPE])
            response = self._client.upload_manifest(manifest, self._client.get_container(target))
        checked(target, response)
        logger.info("tagged {}", target)
