"""
Upload checks.
"""

from loguru import logger

from releases.core.config import Settings
from releases.core.constants import UPLOAD_TYPE
from releases.core.enums import Status
from releases.deb.archive import Published, read_archive
from releases.deb.control import ChangesFile
from releases.oci.models import Manifest
from releases.oci.registry import Registry
from releases.suite.models import Problem, Report, Suite, Upload


class Checker:
    """
    Check a suite's uploads against the published repository.
    """

    def __init__(self, settings: Settings, registry: Registry) -> None:
        """
        Keep the settings and the registry.
        """
        self.settings = settings
        self.registry = registry

    def check(self, suite: Suite) -> Report:
        """
        Check every source of the suite.
        """
        published = read_archive(self.registry, self.settings.repository, suite.name)
        uploads: list[Upload] = []
        problems: list[Problem] = []

        for source in suite.sources:
            upload, messages = self._check(suite.name, source, published.get(source))
            problems += [Problem(source=source, message=message) for message in messages]
            if upload is not None:
                uploads.append(upload)

        removed = {s: p.version for s, p in sorted(published.items()) if s not in suite.sources}
        return Report(suite=suite.name, uploads=uploads, removed=removed, problems=problems)

    def _check(
        self, suite: str, source: str, published: Published | None
    ) -> tuple[Upload | None, list[str]]:
        tagged = f"{self.settings.registry}/{source}:{suite}"
        digest = self.registry.resolve(tagged)
        if digest is None:
            return None, [f"{tagged} does not exist"]
        reference = f"{self.settings.registry}/{source}@{digest}"
        manifest = self.registry.manifest(reference)
        logger.debug("checking {}", reference)

        problems = self._origin(manifest)
        layers = [layer for layer in manifest.layers if layer.title.suffix == ".changes"]
        if len(layers) != 1:
            return None, [*problems, f"the upload has {len(layers)} .changes files, not 1"]

        changes = ChangesFile.read(self.registry.blob(reference, layers[0]).decode())
        problems += self._changes(changes, manifest, suite, source)
        status, problem = self._version(changes, manifest, published)
        if problem:
            problems.append(problem)

        upload = Upload(
            source=source,
            version=changes.version,
            digest=digest,
            repository=manifest.source or "",
            revision=manifest.revision,
            status=status,
            previous=published.version if published else None,
        )
        return upload, problems

    def _origin(self, manifest: Manifest) -> list[str]:
        """
        Require a Debian upload from a repository of the owner.
        """
        problems = []
        if manifest.artifact_type != UPLOAD_TYPE:
            problems.append(f"the artifact type is {manifest.artifact_type}, not {UPLOAD_TYPE}")
        if not (manifest.source or "").startswith(f"{self.settings.owner}/"):
            problems.append(
                f"built in {manifest.source or 'an unknown repository'}, "
                f"not under {self.settings.owner}"
            )
        return problems

    @staticmethod
    def _changes(changes: ChangesFile, manifest: Manifest, suite: str, source: str) -> list[str]:
        """
        Require the .changes to match the source, the suite and the upload's files.
        """
        problems = []
        if changes.source != source:
            problems.append(f"the .changes is for source {changes.source}")
        if changes.distribution != suite:
            problems.append(f"the .changes targets {changes.distribution}, not {suite}")
        files = manifest.files
        problems += [
            f"{f.name} is missing or differs from the .changes"
            for f in changes.files
            if files.get(f.name) != f.digest
        ]
        return problems

    @staticmethod
    def _version(
        changes: ChangesFile, manifest: Manifest, published: Published | None
    ) -> tuple[Status, str | None]:
        """
        Require a higher version, or the same version with the same files.
        """
        if published is None:
            return Status.NEW, None
        if changes.version > published.version:
            return Status.UPGRADE, None
        if changes.version < published.version:
            return Status.DOWNGRADE, f"{changes.version} is lower than the published version"

        # apt never replaces an installed version with another build of it.
        files = manifest.files
        changed = sorted(n for n, d in published.files.items() if files.get(n, d) != d)
        if changed:
            return Status.UNCHANGED, (
                f"{', '.join(changed)} changed without a new version. Add a debian/changelog entry"
            )
        return Status.UNCHANGED, None
