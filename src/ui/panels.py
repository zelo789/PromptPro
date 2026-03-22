"""Panel-based CLI presentation helpers."""

from __future__ import annotations

from typing import List, Optional

from rich import box
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.ui.console import console


def print_banner() -> None:
    """Render the project banner."""
    console.print(
        Panel(
            "[bold cyan]PromptPro[/bold cyan]\n[dim]Make prompts clearer, stricter, and easier for LLMs to execute.[/dim]",
            border_style="cyan",
            box=box.DOUBLE,
        )
    )
    console.print()


def print_help() -> None:
    """Render a compact command reference."""
    table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
    table.add_column("Command", style="green", width=20)
    table.add_column("Description", style="white")
    table.add_row("quit / q", "Exit PromptPro")
    table.add_row("help / h", "Show help")
    table.add_row("frameworks", "List supported prompt frameworks")
    table.add_row("config", "Show current configuration")
    table.add_row("model / m", "List or switch models")
    table.add_row("history", "Show optimization history")
    table.add_row("temp / t", "Set temperature")
    console.print()
    console.print(table)
    console.print()


def print_error(message: str, title: str = "Error") -> None:
    """Render an error panel."""
    console.print()
    console.print(
        Panel(
            f"[bold red]{message}[/bold red]",
            title=f"[red]{title}[/red]",
            border_style="red",
            box=box.ROUNDED,
        )
    )
    console.print()


def print_success(message: str, title: str = "Success") -> None:
    """Render a success panel."""
    console.print()
    console.print(
        Panel(
            f"[bold green]{message}[/bold green]",
            title=f"[green]{title}[/green]",
            border_style="green",
            box=box.ROUNDED,
        )
    )
    console.print()


def print_warning(message: str, title: str = "Warning") -> None:
    """Render a warning panel."""
    console.print()
    console.print(
        Panel(
            f"[bold yellow]{message}[/bold yellow]",
            title=f"[yellow]{title}[/yellow]",
            border_style="yellow",
            box=box.ROUNDED,
        )
    )
    console.print()


def print_info(message: str, title: Optional[str] = None) -> None:
    """Render a neutral informational panel."""
    console.print()
    console.print(
        Panel(
            message,
            title=title,
            border_style="cyan",
            box=box.ROUNDED,
        )
    )
    console.print()


def print_prompt_panel(prompt: str, title: str = "Original Prompt", style: str = "blue") -> None:
    """Render a prompt inside a panel."""
    console.print()
    console.print(
        Panel(
            prompt,
            title=f"[{style}]{title}[/{style}]",
            border_style=style,
            box=box.ROUNDED,
        )
    )
    console.print()


def print_analysis(analysis: str) -> None:
    """Render markdown analysis output."""
    console.print()
    console.print(
        Panel(
            Markdown(analysis),
            title="[yellow]Analysis[/yellow]",
            border_style="yellow",
            box=box.ROUNDED,
        )
    )
    console.print()


def print_framework_recommendation(framework_info, is_selected: bool = False, match_reason: str = "") -> None:
    """Render a framework recommendation panel."""
    border_style = "green" if is_selected else "cyan"
    reason = match_reason or f"Recommended for: {framework_info.recommended_for}"
    content = (
        f"[bold]{framework_info.name}[/bold]\n"
        f"{framework_info.description}\n\n"
        f"[dim]{reason}[/dim]"
    )
    console.print()
    console.print(
        Panel(
            content,
            title="Framework Recommendation",
            border_style=border_style,
            box=box.ROUNDED,
        )
    )
    console.print()


def print_divergent_questions(questions: List[str]) -> None:
    """Render clarifying questions."""
    if not questions:
        return
    console.print()
    console.print(
        Panel(
            "[bold]Answer any useful question below to refine the prompt further.[/bold]",
            title="Clarifying Questions",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )
    for index, question in enumerate(questions, 1):
        console.print(f"  [cyan][bold]{index}[/bold][/cyan] {question}")
    console.print()


def print_versions_prompt() -> None:
    """Render version selection guidance."""
    console.print()
    console.print(
        Panel(
            "[bold]Choose how many optimization versions to generate.[/bold]\n"
            "[dim]1 = light, 2 = light + moderate, 3 = light + moderate + deep[/dim]",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )


def print_welcome_guide() -> None:
    """Render a first-run guide."""
    console.print()
    console.print(
        Panel(
            "[bold cyan]Welcome to PromptPro[/bold cyan]\n\n"
            "- Match the prompt to a framework automatically\n"
            "- Generate multiple optimized versions\n"
            "- Refine prompts with optional requirement docs and clarifying questions",
            title="Getting Started",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )
    console.print()


def print_first_run_tips() -> None:
    """Render sample prompts for first-time users."""
    console.print()
    console.print(
        Panel(
            "[bold]Try prompts like:[/bold]\n\n"
            "1. Write a robust API design prompt\n"
            "2. Improve this hiring email prompt\n"
            "3. Analyze this market research request",
            title="Starter Ideas",
            border_style="yellow",
            box=box.ROUNDED,
        )
    )
    console.print()
