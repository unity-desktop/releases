"""
GitHub Actions outputs, summary, annotations and push metadata.
"""

from datetime import UTC, datetime
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console

from releases.core.constants import CREATED, REVISION, SOURCE


class GitHub(BaseSettings):
    """
    The runner environment of a step. Outside Actions, every call does nothing.
    """

    model_config = SettingsConfigDict(frozen=True, extra="ignore")

    actions: bool = Field(False, validation_alias="GITHUB_ACTIONS")
    output: Path | None = Field(None, validation_alias="GITHUB_OUTPUT")
    step_summary: Path | None = Field(None, validation_alias="GITHUB_STEP_SUMMARY")
    server_url: str = Field("https://github.com", validation_alias="GITHUB_SERVER_URL")
    repository: str | None = Field(None, validation_alias="GITHUB_REPOSITORY")
    sha: str | None = Field(None, validation_alias="GITHUB_SHA")

    @property
    def annotations(self) -> dict[str, str]:
        """
        Return OCI annotations for a push: the time and the source commit.
        """
        annotations = {CREATED: datetime.now(UTC).isoformat(timespec="seconds")}
        if self.repository:
            annotations[SOURCE] = f"{self.server_url}/{self.repository}"
        if self.sha:
            annotations[REVISION] = self.sha
        return annotations

    def set_output(self, name: str, value: str) -> None:
        """
        Set a step output.
        """
        if self.output:
            with self.output.open("a") as file:
                file.write(f"{name}={value}\n")

    def summary(self, markdown: str) -> None:
        """
        Add Markdown to the job summary.
        """
        if self.step_summary:
            with self.step_summary.open("a") as file:
                file.write(markdown)

    def error(self, console: Console, title: str, message: str) -> None:
        """
        Add an error annotation.
        """
        if self.actions:
            console.print(f"::error title={title}::{message}", markup=False, highlight=False)
