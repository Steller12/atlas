from collections import Counter

import typer
from rich.console import Console

from atlas.errors import AtlasError
from atlas.terraform.parser import load_plan

from atlas.graph.impact import build_graph, downstream
from atlas.terraform.parser import read_plan_json


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


@app.command()
def impact(
    plan_file: str,
    max_depth: int = typer.Option(3, "--max-depth", help="How many hops to follow."),
) -> None:
    """Show the blast radius of the changes in a terraform plan."""
    try:
        changes = load_plan(plan_file)
        data = read_plan_json(plan_file)
    except AtlasError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e

    graph = build_graph(data)
    changed = {c.address for c in changes}
    impacted = downstream(changed, graph, max_depth=max_depth)

    console.print(
        f"[bold]Atlas impact[/bold] — {len(changed)} changed, "
        f"{len(impacted)} impacted downstream"
    )
    for addr, path in sorted(impacted.items()):
        console.print(f"  [yellow]{addr}[/yellow]  [dim]why: {' -> '.join(path)}[/dim]")