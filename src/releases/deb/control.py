"""
A .changes, and Packages and Sources stanzas.
"""

from pathlib import PurePosixPath

from debian.deb822 import Changes, Packages, Sources
from debian.debian_support import Version
from pydantic import BaseModel, ConfigDict, Field, GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from releases.deb.stanza import Stanza
from releases.oci.models import Digest


class DebianVersion(Version):
    """
    A Debian version. Compares like dpkg and serialises as text.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: type, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """
        Accept a str or a version. Write a str.
        """
        return core_schema.no_info_plain_validator_function(
            cls.coerce, serialization=core_schema.to_string_ser_schema()
        )

    @classmethod
    def coerce(cls, value: object) -> DebianVersion:
        """
        Return the value as a DebianVersion.
        """
        return value if isinstance(value, cls) else cls(str(value))


class Checksum(BaseModel):
    """
    A line of Checksums-Sha256.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    sha256: str

    @property
    def digest(self) -> Digest:
        """
        Return the checksum as a digest.
        """
        return Digest(f"sha256:{self.sha256}")


class IndexedFile(BaseModel):
    """
    A file in the repository, with its source and version.
    """

    model_config = ConfigDict(frozen=True)

    source: str
    version: DebianVersion
    name: str
    digest: Digest


class ChangesFile(Stanza):
    """
    A .changes.
    """

    kind = Changes

    source: str = Field(alias="Source")
    version: DebianVersion = Field(alias="Version")
    distribution: str = Field(alias="Distribution")
    files: list[Checksum] = Field(alias="Checksums-Sha256")


class Binary(Stanza):
    """
    A Packages stanza.
    """

    kind = Packages

    package: str = Field(alias="Package")
    version: DebianVersion = Field(alias="Version")
    source_field: str | None = Field(None, alias="Source")
    filename: PurePosixPath = Field(alias="Filename")
    sha256: str = Field(alias="SHA256")

    @property
    def indexed(self) -> IndexedFile:
        """
        Return the file under its source name and version.
        """
        # Source reads "name (version)" when the binary version differs.
        source, _, version = (self.source_field or self.package).partition(" ")
        return IndexedFile(
            source=source,
            version=version.strip("()") or self.version,
            name=self.filename.name,
            digest=f"sha256:{self.sha256}",
        )


class SourceStanza(Stanza):
    """
    A Sources stanza.
    """

    kind = Sources

    package: str = Field(alias="Package")
    version: DebianVersion = Field(alias="Version")
    files: list[Checksum] = Field(alias="Checksums-Sha256")

    @property
    def indexed(self) -> list[IndexedFile]:
        """
        Return each file of the source package.
        """
        return [
            IndexedFile(source=self.package, version=self.version, name=f.name, digest=f.digest)
            for f in self.files
        ]
