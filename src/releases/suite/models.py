"""
Suite file and check results.
"""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, field_validator

from releases.core.constants import SOURCE_NAME
from releases.core.enums import Status
from releases.core.errors import SuiteError
from releases.core.strings import PatternStr
from releases.deb.control import DebianVersion
from releases.oci.models import Digest


class SourceName(PatternStr):
    """
    A source package name.
    """

    __slots__ = ()
    PATTERN = SOURCE_NAME


class Suite(BaseModel):
    """
    The source packages of one Ubuntu series.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    sources: list[SourceName] = Field(min_length=1)

    @field_validator("sources")
    @classmethod
    def unique(cls, sources: list[SourceName]) -> list[SourceName]:
        """
        Refuse duplicate sources.
        """
        twice = sorted({source for source in sources if sources.count(source) > 1})
        if twice:
            raise ValueError(f"listed more than once: {', '.join(twice)}")
        return sources

    @classmethod
    def load(cls, name: str, directory: Path) -> Suite:
        """
        Read <directory>/<name>.yaml.
        """
        path = directory / f"{name}.yaml"
        try:
            content = yaml.safe_load(path.read_text())
        except FileNotFoundError as error:
            raise SuiteError(f"no suite file {path}") from error
        except yaml.YAMLError as error:
            raise SuiteError(f"{path}: {error}") from error
        if not isinstance(content, dict):
            raise SuiteError(f"{path}: expected a mapping with a sources list")
        try:
            return cls.model_validate({**content, "name": name})
        except ValidationError as error:
            raise SuiteError(f"{path}: {error}") from error


class Upload(BaseModel):
    """
    A checked upload, pinned by digest.
    """

    model_config = ConfigDict(frozen=True)

    source: str
    version: DebianVersion
    digest: Digest
    repository: str
    revision: str
    status: Status
    previous: DebianVersion | None = None


class Problem(BaseModel):
    """
    Why an upload cannot go into the suite.
    """

    model_config = ConfigDict(frozen=True)

    source: str
    message: str


class Report(BaseModel):
    """
    The result of a suite check.
    """

    model_config = ConfigDict(frozen=True)

    suite: str
    uploads: list[Upload]
    removed: dict[str, DebianVersion] = {}
    problems: list[Problem] = []

    @property
    def ok(self) -> bool:
        """
        Return True if every upload passed.
        """
        return not self.problems


UPLOADS = TypeAdapter(list[Upload])
