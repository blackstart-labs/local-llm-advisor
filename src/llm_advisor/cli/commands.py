"""Typer CLI commands implementation."""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich.console import Console

from llm_advisor import __version__
from llm_advisor.analysis.recommender import RecommendationEngine
from llm_advisor.hardware.detector import SystemHardwareDetector
from llm_advisor.models.registry import DefaultModelRegistry
from llm_advisor.reporting.html import generate_html_report
from llm_advisor.reporting.terminal import render_terminal_report
from llm_advisor.utils.browser import open_in_browser

app = typer.Typer(
    name="llm-advisor",
    help="Analyze local machine hardware and recommend compatible local LLMs.",
    add_completion=False,
)

console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold cyan]llm-advisor[/bold cyan] version [bold white]{__version__}[/bold white]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show application version and exit.",
        callback=version_callback,
        is_eager=True,
    )
) -> None:
    pass


@app.command()
def scan(
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Generate HTML report and save to specified file path (e.g. report.html).",
    ),
    open_browser: bool = typer.Option(
        False,
        "--open",
        help="Automatically open generated HTML report in default browser.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON results to stdout.",
    ),
) -> None:
    """Scan local machine hardware and generate LLM recommendations."""
    if not json_output:
        console.print("[dim]Scanning local machine hardware...[/dim]")

    detector = SystemHardwareDetector()
    hardware = detector.detect()

    recommender = RecommendationEngine()
    report = recommender.recommend(hardware)

    if json_output:
        console.print(report.model_dump_json(indent=2))
        return

    render_terminal_report(report, console=console)

    if output or open_browser:
        target_path = output if output else "report.html"
        generated_file = generate_html_report(report, output_path=target_path)
        console.print(f"[bold green]✓[/bold green] Generated HTML report: [bold white]{generated_file}[/bold white]")

        if open_browser:
            console.print("[dim]Opening HTML report in your default browser...[/dim]")
            open_in_browser(generated_file)


@app.command()
def recommend(
    purpose: Optional[str] = typer.Option(
        None,
        "--purpose",
        "-p",
        help="Target use-case: coding, reasoning, general, rag, lightweight, privacy.",
    ),
    ram: Optional[float] = typer.Option(
        None,
        "--ram",
        help="Simulate maximum RAM limit in GB (e.g. 16.0).",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output recommendations as JSON.",
    ),
) -> None:
    """Get recommendations tailored to a specific purpose or memory constraint."""
    detector = SystemHardwareDetector()
    hardware = detector.detect()

    recommender = RecommendationEngine()
    report = recommender.recommend(hardware, purpose=purpose, max_ram_gb=ram)

    if json_output:
        console.print(report.model_dump_json(indent=2))
        return

    render_terminal_report(report, console=console)


@app.command()
def models(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output model catalog as JSON.",
    ),
) -> None:
    """List all open-weight models registered in the catalog."""
    registry = DefaultModelRegistry()
    all_models = registry.list_all()

    if json_output:
        data = [m.model_dump() for m in all_models]
        console.print(json.dumps(data, indent=2))
        return

    console.print(f"[bold cyan]Registered LLM Catalog ({len(all_models)} models)[/bold cyan]\n")
    for m in all_models:
        console.print(f"• [bold white]{m.name}[/bold white] ({m.id}) — {m.parameter_count_billions}B params [{m.family}]")
        console.print(f"  Use cases: [dim]{', '.join(m.use_cases)}[/dim]")


@app.command()
def model(
    model_name: str = typer.Argument(..., help="Model ID or name (e.g. qwen2.5-7b-instruct)."),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output model details as JSON.",
    ),
) -> None:
    """Display technical details for a specific model."""
    registry = DefaultModelRegistry()
    m = registry.get_by_id(model_name)

    if not m:
        console.print(f"[bold red]Error:[/bold red] Model '{model_name}' not found in catalog.")
        raise typer.Exit(code=1)

    if json_output:
        console.print(m.model_dump_json(indent=2))
        return

    console.print(f"[bold cyan]{m.name}[/bold cyan] ({m.id})")
    console.print(f"Family: [white]{m.family}[/white] | Parameters: [white]{m.parameter_count_billions}B[/white]")
    console.print(f"Default Context: [white]{m.context_length} tokens[/white] | License: [white]{m.license}[/white]\n")

    console.print("[bold white]Quantization Profiles:[/bold white]")
    for q in m.supported_quantizations:
        console.print(
            f"  • {q.level.value}: file size {q.file_size_gb:.1f} GB, rec RAM {q.recommended_ram_gb:.1f} GB, rec VRAM {q.recommended_vram_gb:.1f} GB"
        )


@app.command()
def report(
    output: str = typer.Option(
        "report.html",
        "--output",
        "-o",
        help="File path to save the HTML report.",
    ),
    open_browser: bool = typer.Option(
        True,
        "--open",
        help="Open in default browser after generation.",
    ),
) -> None:
    """Generate standalone HTML report and open in browser."""
    detector = SystemHardwareDetector()
    hardware = detector.detect()

    recommender = RecommendationEngine()
    rec_report = recommender.recommend(hardware)

    generated_file = generate_html_report(rec_report, output_path=output)
    console.print(f"[bold green]✓[/bold green] Generated HTML report: [bold white]{generated_file}[/bold white]")

    if open_browser:
        console.print("[dim]Opening in default browser...[/dim]")
        open_in_browser(generated_file)


if __name__ == "__main__":
    app()
