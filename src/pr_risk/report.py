from rich import box
from rich.console import Console
from rich.table import Table

from pr_risk.risk import RiskResult


def print_report(changed_files: list[str], risk: RiskResult) -> None:
    console = Console()

    console.print("PR Risk Report", style="bold")
    console.print(_changed_files_table(changed_files))
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
