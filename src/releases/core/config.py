"""
Settings from RELEASES_ environment variables.
"""

from functools import cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from releases.core.constants import OWNER, REGISTRY, REPOSITORY, SUITES_DIR


class Settings(BaseSettings):
    """
    Registry locations, the allowed owner and the login.
    """

    model_config = SettingsConfigDict(env_prefix="RELEASES_", extra="forbid", frozen=True)

    registry: str = Field(REGISTRY, description="Uploads live at <registry>/<source>:<suite>.")
    repository: str = Field(REPOSITORY, description="The repository lives at <repository>:<suite>.")
    owner: str = Field(OWNER, description="Uploads must come from a repository under this URL.")
    suites_dir: Path = Field(Path(SUITES_DIR), description="Directory of <suite>.yaml files.")
    username: str | None = Field(None, description="Registry user. Reads work without one.")
    password: SecretStr | None = Field(None, description="Registry password or token.")


@cache
def get_settings() -> Settings:
    """
    Return the settings.
    """
    return Settings()
