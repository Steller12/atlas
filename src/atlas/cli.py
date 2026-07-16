from collections import Counter

import typer
from rich.console import Console

from atlas.errors import AtlasError
from atlas.terraform.parser import load_plan, read_plan_json

from atlas.graph.impact import build_graph, downstream

from atlas.scoring.heuristics import score_plan

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
        data = read_plan_json(plan_file)
        changes = load_plan(plan_file, data=data)
    except AtlasError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e

    graph = build_graph(data)
    changed = {c.address for c in changes}
    impacted = downstream(changed, graph, max_depth=max_depth)

    risks = score_plan(changes, graph)
    overall = max((r.score for r in risks), default=0)
    worst = next((r.level for r in risks if r.score == overall), "low")

    console.print(
        f"[bold]Atlas impact[/bold] — {len(changed)} changed, "
        f"{len(impacted)} impacted downstream — "
        f"risk: [bold]{worst.upper()}[/bold] ({overall}/10)"
    )
    for addr, path in sorted(impacted.items()):
        console.print(f"  [yellow]{addr}[/yellow]  [dim]why: {' -> '.join(path)}[/dim]")
    for r in risks:
        reasons = "; ".join(r.reasons)
        console.print(f"  [bold]{r.address}[/bold] — {r.level} ({r.score}/10)  [dim]{reasons}[/dim]")