import typer
from rich.console import Console

app = typer.Typer(help="Atlas — blast-radius analysis for Terraform plans.")
console = Console()


@app.callback()
def main() -> None:
    """Atlas — blast-radius analysis for Terraform plans."""


@app.command()
def analyze(plan_file: str) -> None:
    """Analyze a Terraform plan JSON and summarize changes."""
    console.print(f"[bold]Atlas[/bold] would analyze {plan_file}")


if __name__ == "__main__":
    app()