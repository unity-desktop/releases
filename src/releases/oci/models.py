"""
OCI digests and manifests.
"""

from fnmatch import fnmatch
from pathlib import PurePosixPath

from pydantic import AliasPath, BaseModel, ConfigDict, Field

from releases.core.constants import REVISION, SOURCE, TITLE
from releases.core.strings import PatternStr


class Digest(PatternStr):
    """
    A sha256 digest.
    """

    __slots__ = ()
    PATTERN = r"^sha256:[0-9a-f]{64}$"


class Descriptor(BaseModel):
    """
    A manifest layer. Here, one file.
    """

    model_config = ConfigDict(frozen=True)

    digest: Digest
    title: PurePosixPath = Field(PurePosixPath(), validation_alias=AliasPath("annotations", TITLE))


class Manifest(BaseModel):
    """
    An OCI image manifest.
    """

    model_config = ConfigDict(frozen=True)

    artifact_type: str | None = Field(None, alias="artifactType")
    layers: list[Descriptor] = []
    source: str | None = Field(None, validation_alias=AliasPath("annotations", SOURCE))
    revision: str = Field("", validation_alias=AliasPath("annotations", REVISION))

    def titled(self, pattern: str) -> list[Descriptor]:
        """
        Return the layers whose title matches a shell pattern.
        """
        return [layer for layer in self.layers if fnmatch(str(layer.title), pattern)]

    @property
    def files(self) -> dict[str, Digest]:
        """
        Map each file name to its digest.
        """
        return {layer.title.name: layer.digest for layer in self.layers}
