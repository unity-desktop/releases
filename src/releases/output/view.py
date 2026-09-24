"""
Report views for the terminal and the job summary.
"""

from rich.table import Table
from tabulate import tabulate

from releases.core.enums import Status
from releases.suite.models import Report, Upload

STYLES = {
    Status.NEW: "green",
    Status.UPGRADE: "cyan",
    Status.DOWNGRADE: "red",
    Status.UNCHANGED: "dim",
    Status.REMOVED: "yellow",
}
HEADERS = ["source", "version", "status", "built in", "digest"]


def _status(upload: Upload) -> str:
    if upload.status in (Status.UPGRADE, Status.DOWNGRADE):
        return f"{upload.status} from {upload.previous}"
    return upload.status


def _commit(upload: Upload) -> str:
    return f"{upload.repository.removeprefix('https://github.com/')}@{upload.revision[:7]}"


def _digest(upload: Upload) -> str:
    return upload.digest.removeprefix("sha256:")[:12]


def report_table(report: Report) -> Table:
    """
    Build the terminal table.
    """
    table = Table(title=report.suite, title_justify="left", box=None, pad_edge=False)
    for header in HEADERS:
        table.add_column(header)
    failed = {problem.source for problem in report.problems}

    for upload in report.uploads:
        style = "red" if upload.source in failed else STYLES[upload.status]
        table.add_row(
            f"[bold]{upload.source}[/bold]",
            str(upload.version),
            f"[{style}]{_status(upload)}[/{style}]",
            f"[dim]{_commit(upload)}[/dim]",
            f"[dim]{_digest(upload)}[/dim]",
        )
    for source, version in report.removed.items():
        table.add_row(source, str(version), f"[yellow]{Status.REMOVED}[/yellow]", "", "")
    return table


def report_markdown(report: Report) -> str:
    """
    Build the job summary, with links to the commits.
    """
    rows = [
        [
            upload.source,
            str(upload.version),
            _status(upload),
            f"[{_commit(upload)}]({upload.repository}/commit/{upload.revision})",
            f"`{_digest(upload)}`",
        ]
        for upload in report.uploads
    ]
    rows += [
        [source, str(version), Status.REMOVED, "", ""] for source, version in report.removed.items()
    ]
    problems = "".join(f"- **{p.source}**: {p.message}\n" for p in report.problems)
    table = tabulate(rows, headers=HEADERS, tablefmt="github")
    return f"## {report.suite}\n\n{table}\n\n{problems}"
