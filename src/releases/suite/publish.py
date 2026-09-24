"""
Pull uploads and push the repository.
"""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from releases.core.config import Settings
from releases.core.constants import WORKERS
from releases.oci.models import Digest
from releases.oci.registry import Registry
from releases.suite.models import Upload


def pull_uploads(settings: Settings, uploads: list[Upload], directory: Path) -> None:
    """
    Download each upload by digest, in parallel.
    """

    # One client for each upload: each repository needs its own token.
    def pull(upload: Upload) -> list[Path]:
        registry = Registry(settings.username, settings.password)
        return registry.pull(f"{settings.registry}/{upload.source}@{upload.digest}", directory)

    with ThreadPoolExecutor(WORKERS) as pool:
        list(pool.map(pull, uploads))


def push_repository(
    registry: Registry,
    settings: Settings,
    suite: str,
    directory: Path,
    tags: list[str],
    annotations: dict[str, str],
) -> Digest:
    """
    Push the repository as <repository>:<suite> and add the other tags.
    """
    digest = registry.push(directory, f"{settings.repository}:{suite}", annotations)
    for tag in tags:
        registry.tag(f"{settings.repository}@{digest}", f"{settings.repository}:{tag}")
    return digest
