from collections import Counter

import typer
from rich.console import Console

from atlas.errors import AtlasError
from atlas.terraform.parser import load_plan

app = typer.Typer(help="Atlas — blast-radius analysis for Terraform plans.")
console = Console()


@app.callback()
def main() -> None:
    """Atlas — blast-radius analysis for Terraform plans."""


@app.command()
def analyze(plan_file: str) -> None:
    """Analyze a Terraform plan JSON and summarize changes."""
    try:
        changes = load_plan(plan_file)
    except AtlasError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e

    if not changes:
        console.print("[green]No changes.[/green] Plan is a no-op.")
        return

    counts = Counter(c.action for c in changes)
    console.print(f"[bold]Atlas[/bold] — {len(changes)} resource change(s)")
    for action, count in sorted(counts.items()):
        console.print(f"  {action}: {count}")