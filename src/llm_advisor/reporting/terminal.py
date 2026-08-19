"""Terminal renderer using Rich panels, tables, and colors."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from llm_advisor.analysis.recommender import RecommendationReport


def render_terminal_report(
    report: RecommendationReport,
    console: Console | None = None,
) -> None:
    """Render a beautiful, colorful, professional terminal report."""
    con = console if console is not None else Console()

    # Header Panel
    header_text = Text("Local LLM Hardware Advisor", style="bold white on blue", justify="center")
    con.print(
        Panel(header_text, border_style="cyan", subtitle="Know what your machine can actually run")
    )
    con.print()

    # Hardware Summary
    hw = report.hardware
    con.print(Rule("[bold cyan]System Hardware Overview[/bold cyan]"))

    hw_table = Table(show_header=False, box=None, padding=(0, 2))
    hw_table.add_row("[bold grey70]OS[/bold grey70]", f"[white]{hw.os_info.summary_string}[/white]")
    hw_table.add_row("[bold grey70]CPU[/bold grey70]", f"[white]{hw.cpu.summary_string}[/white]")
    hw_table.add_row(
        "[bold grey70]RAM[/bold grey70]",
        f"[white]{hw.memory.total_gb:.1f} GB total ([green]{hw.memory.available_gb:.1f} GB available[/green], safe budget: [bold green]{hw.memory.safe_budget_gb:.1f} GB[/bold green])[/white]",
    )

    gpu_str = "Unavailable / CPU Only"
    if hw.gpus:
        gpu_parts = []
        for g in hw.gpus:
            gpu_parts.append(f"{g.name} ({g.vram_gb:.1f} GB VRAM)")
        gpu_str = ", ".join(gpu_parts)
    hw_table.add_row("[bold grey70]GPU[/bold grey70]", f"[yellow]{gpu_str}[/yellow]")
    hw_table.add_row(
        "[bold grey70]Storage[/bold grey70]",
        f"[white]{hw.storage.free_gb:.1f} GB available ({hw.storage.storage_type.value})[/white]",
    )

    con.print(hw_table)
    con.print()

    # Hardware Assessment
    con.print(Rule("[bold cyan]Hardware Assessment[/bold cyan]"))
    assess_panel = Panel(
        f"[bold yellow]{report.overall_rating_badge}[/bold yellow]\n"
        f"[white]{report.overall_rating_text}[/white]\n\n"
        f"[grey70]Primary Bottleneck:[/grey70] [bold magenta]{report.primary_bottleneck}[/bold magenta]\n"
        f"[grey70]Recommended Model Size Class:[/grey70] [bold green]{report.recommended_model_size_class}[/bold green]",
        border_style="yellow",
        title="[bold yellow]Capability Summary[/bold yellow]",
    )
    con.print(assess_panel)
    con.print()

    # Top Recommendations Table
    con.print(Rule("[bold green]Top Recommendations[/bold green]"))

    rec_table = Table(box=None, header_style="bold cyan")
    rec_table.add_column("#", style="dim", width=4)
    rec_table.add_column("Model", style="bold white")
    rec_table.add_column("Quant", style="yellow")
    rec_table.add_column("Fit", style="bold")
    rec_table.add_column("Score", justify="right")
    rec_table.add_column("Best For")

    for rec in report.top_recommendations:
        fit_badge = f"{rec.compatibility.level.badge_emoji} {rec.compatibility.level.value}"
        score_color = "green" if rec.score >= 80 else ("yellow" if rec.score >= 65 else "orange3")
        best_for_str = ", ".join(rec.best_for)

        rec_table.add_row(
            str(rec.rank),
            rec.model.name,
            rec.recommended_quantization.value,
            fit_badge,
            f"[{score_color}]{rec.score}/100[/{score_color}]",
            best_for_str,
        )

    con.print(rec_table)
    con.print()

    # Detailed Spotlight for #1 Recommendation
    if report.top_recommendations:
        top = report.top_recommendations[0]
        con.print(Rule(f"[bold gold1]Spotlight: #1 {top.model.name}[/bold gold1]"))

        why_bullets = "\n".join([f"  • [green]{w}[/green]" for w in top.why_recommended])
        pros_bullets = "\n".join([f"  + {p}" for p in top.pros])
        cons_bullets = "\n".join([f"  - {c}" for c in top.cons])

        spotlight_content = (
            f"[bold white]Why Recommended:[/bold white]\n{why_bullets}\n\n"
            f"[bold white]Pros:[/bold white]\n[green]{pros_bullets}[/green]\n\n"
            f"[bold white]Cons:[/bold white]\n[red]{cons_bullets}[/red]\n\n"
            f"[grey70]Suggested Runtime:[/grey70] [cyan]{top.suggested_runtime}[/cyan]\n"
            f"[grey70]Suggested Context:[/grey70] [cyan]{top.suggested_context_range}[/cyan]"
        )
        con.print(
            Panel(
                spotlight_content,
                border_style="gold1",
                title="[bold gold1]Model Breakdown[/bold gold1]",
            )
        )
        con.print()
