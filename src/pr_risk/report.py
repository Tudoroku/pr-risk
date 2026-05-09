from rich import box
from rich.console import Console
from rich.table import Table

from pr_risk.diff_stats import DiffStats
from pr_risk.risk import RiskResult


def print_report(changed_files: list[str], risk: RiskResult, diff_stats: DiffStats | None = None) -> None:
    console = Console()

    console.print("PR Risk Report", style="bold")
    console.print(_changed_files_table(changed_files))
    if diff_stats is not None:
        console.print(_diff_stats_table(diff_stats))
    console.print(f"Risk score: {risk.score}/100")
    console.print(f"Risk level: {risk.level}")
    console.print("Reasons:")
    for reason in risk.reasons:
        console.print(f"- {reason}")


def _changed_files_table(changed_files: list[str]) -> Table:
    table = Table(title="Changed Files", box=box.ASCII)
    table.add_column("#", justify="right")
    table.add_column("File")

    for index, path in enumerate(changed_files, start=1):
        table.add_row(str(index), path)

    return table


def _diff_stats_table(diff_stats: DiffStats) -> Table:
    table = Table(title="Diff Stats", box=box.ASCII)
    table.add_column("Metric")
    table.add_column("Value", justify="right")

    table.add_row("Files changed", str(diff_stats.files_changed))
    table.add_row("Lines added", str(diff_stats.lines_added))
    table.add_row("Lines deleted", str(diff_stats.lines_deleted))
    table.add_row("Total churn", str(diff_stats.total_churn))
    table.add_row("Binary files changed", str(diff_stats.binary_files_changed))

    return table
