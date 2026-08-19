"""Typer CLI command definitions."""

import typer

app = typer.Typer(
    name="llm-advisor",
    help="Analyze local hardware and recommend compatible local LLMs.",
    add_completion=False,
)


@app.command()
def scan() -> None:
    """Scan local hardware and generate recommendations."""
    typer.echo("Local LLM Advisor initial setup complete.")


if __name__ == "__main__":
    app()
