"""
Command line interface.
"""

from pathlib import Path

import typer
from pydantic import ValidationError
from rich.console import Console

from releases.core.config import get_settings
from releases.core.errors import ReleasesError
from releases.core.logs import configure
from releases.oci.registry import Registry
from releases.output.github import GitHub
from releases.output.view import report_markdown, report_table
from releases.suite.check import Checker
from releases.suite.models import UPLOADS, Suite
from releases.suite.publish import pull_uploads, push_repository

app = typer.Typer(no_args_is_help=True)
console = Console(stderr=True)


def main() -> None:
    """
    Run the app. Print an error and exit with 1 on failure.
    """
    try:
        app()
    except (ReleasesError, ValidationError) as error:
        console.print(f"[red]error[/red]: {error}")
        raise SystemExit(1) from error


def registry() -> Registry:
    """
    Open the registry with the configured login.
    """
    settings = get_settings()
    return Registry(settings.username, settings.password)


@app.callback()
def root(verbose: bool = False) -> None:
    """
    Check and assemble the unity-desktop apt repository.
    """
    configure(verbose)


@app.command()
def check(suite: str, json: bool = False) -> None:
    """
    Check the uploads of SUITE against the published repository.
    """
    settings = get_settings()
    github = GitHub()
    report = Checker(settings, registry()).check(Suite.load(suite, settings.suites_dir))

    console.print(report_table(report))
    github.summary(report_markdown(report))
    for problem in report.problems:
        console.print(f"[red]error[/red]: [bold]{problem.source}[/bold]: {problem.message}")
        github.error(console, problem.source, problem.message)
    if not report.ok:
        raise typer.Exit(1)

    uploads = UPLOADS.dump_json(report.uploads).decode()
    github.set_output("uploads", uploads)
    if json:
        typer.echo(uploads)


@app.command()
def pull(uploads: str, directory: Path) -> None:
    """
    Download each upload in the UPLOADS JSON from check into DIRECTORY.
    """
    pull_uploads(get_settings(), UPLOADS.validate_json(uploads), directory)


@app.command()
def push(suite: str, directory: Path, tag: list[str] | None = None) -> None:
    """
    Push DIRECTORY as the repository of SUITE, and add each --tag.
    """
    settings = get_settings()
    github = GitHub()
    digest = push_repository(registry(), settings, suite, directory, tag or [], github.annotations)
    github.set_output("digest", digest)
