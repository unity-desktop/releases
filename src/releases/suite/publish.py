"""
Pull uploads and push the repository.
"""

from pathlib import Path

from releases.core.config import Settings
from releases.oci.models import Digest
from releases.oci.registry import Registry
from releases.suite.models import Upload


def pull_uploads(
    registry: Registry, settings: Settings, uploads: list[Upload], directory: Path
) -> dict[str, list[Path]]:
    """
    Download each upload by digest. Return the files of each source.
    """
    return {
        upload.source: registry.pull(
            f"{settings.registry}/{upload.source}@{upload.digest}", directory
        )
        for upload in uploads
    }


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
