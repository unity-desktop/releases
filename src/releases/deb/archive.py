"""
What the published repository serves.
"""

from loguru import logger
from pydantic import BaseModel, ConfigDict

from releases.core.constants import PACKAGES_INDEX, SOURCES_INDEX
from releases.deb.control import Binary, DebianVersion, IndexedFile, SourceStanza
from releases.oci.models import Digest
from releases.oci.registry import Registry


class Published(BaseModel):
    """
    A published source: its newest version and that version's files.
    """

    model_config = ConfigDict(frozen=True)

    version: DebianVersion
    files: dict[str, Digest] = {}


def read_archive(registry: Registry, repository: str, suite: str) -> dict[str, Published]:
    """
    Read the suite's Packages and Sources. Return nothing before the first publish.
    """
    digest = registry.resolve(f"{repository}:{suite}")
    if digest is None:
        logger.debug("{}:{} is not published yet", repository, suite)
        return {}
    reference = f"{repository}@{digest}"
    manifest = registry.manifest(reference)

    indexed: list[IndexedFile] = []
    for layer in manifest.titled(PACKAGES_INDEX.format(suite=suite)):
        text = registry.blob(reference, layer).decode()
        indexed += [binary.indexed for binary in Binary.read_all(text)]
    for layer in manifest.titled(SOURCES_INDEX.format(suite=suite)):
        text = registry.blob(reference, layer).decode()
        indexed += [file for stanza in SourceStanza.read_all(text) for file in stanza.indexed]

    newest = {}
    for file in indexed:
        newest[file.source] = max(file.version, newest.get(file.source, file.version))

    return {
        source: Published(
            version=version,
            files={f.name: f.digest for f in indexed if (f.source, f.version) == (source, version)},
        )
        for source, version in newest.items()
    }
