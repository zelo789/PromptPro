"""Table-based UI helpers used by the CLI."""

from __future__ import annotations

from typing import Dict, List, Optional

from rich import box
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.strategies import PROMPT_FRAMEWORKS, PromptFramework
from src.ui.console import console


def create_choice_table(choices: List[Dict[str, str]]) -> Table:
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    table.add_column("Option", style="green")
    table.add_column("Description", style="white")
    for choice in choices:
        table.add_row(choice.get("option", ""), choice.get("description", ""))
    return table


def create_data_table(
    headers: List[str],
    rows: List[List[str]],
    title: Optional[str] = None,
) -> Table:
    table = Table(
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold magenta",
        row_styles=["dim", "none"],
        title=title,
    )
    for header in headers:
        table.add_column(header)
    for row in rows:
        table.add_row(*row)
    return table


def show_frameworks_table() -> None:
    show_frameworks()


def show_config_table(config) -> None:
    show_config(config)


def show_frameworks() -> None:
    table = Table(box=box.ROUNDED, border_style="cyan")
    table.add_column("Framework", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Recommended for", style="green")
    for framework, info in PROMPT_FRAMEWORKS.items():
        table.add_row(framework.value, info.description, info.recommended_for)
    console.print()
    console.print(table)
    console.print()


def show_models(models: List[str], current_model: str) -> None:
    table = Table(box=box.ROUNDED, border_style="cyan")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Model", style="white")
    table.add_column("Status", style="green", width=12)
    for index, model in enumerate(models, 1):
        status = "current" if model == current_model else ""
        table.add_row(str(index), model, status)
    console.print()
    console.print(table)
    console.print()


def show_config(config) -> None:
    table = Table(box=box.ROUNDED, border_style="cyan")
    table.add_column("Setting", style="cyan", width=22)
    table.add_column("Value", style="white")
    table.add_row("Provider", config.provider)
    table.add_row("Model", config.get_current_model() or "<auto>")
    table.add_row("Temperature", str(config.temperature))
    table.add_row("History", "on" if config.enable_history else "off")
    table.add_row("Clipboard", "on" if config.auto_clipboard else "off")
    table.add_row("Clarify", "on" if config.enable_clarifying_questions else "off")
    table.add_row("Config dir", config.config_dir)
    console.print()
    console.print(table)
    console.print()


def show_optimized_versions(results: List[Dict]) -> None:
    if not results:
        console.print("[red]No optimized versions were generated.[/red]")
        return

    console.print()
    console.print(
        Panel(
            f"[bold green]Optimization complete.[/bold green] Generated [cyan]{len(results)}[/cyan] versions.",
            border_style="green",
            box=box.ROUNDED,
        )
    )
    console.print()

    for index, version in enumerate(results, 1):
        console.print(
            Panel(
                Markdown(version["prompt"]),
                title=f"Version {index}: {version['name']}",
                subtitle=version.get("description", ""),
                border_style="cyan" if version["level"] != "framework" else "yellow",
                box=box.ROUNDED,
            )
        )
        console.print()


def show_history_items(items: List, limit: int = 10) -> None:
    if not items:
        console.print()
        console.print(Panel("[dim]No history yet.[/dim]", border_style="cyan", box=box.ROUNDED))
        console.print()
        return

    table = Table(box=box.ROUNDED, border_style="cyan")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Time", style="white", width=19)
    table.add_column("Prompt", style="green")
    table.add_column("Framework", style="yellow", width=12)

    for index, item in enumerate(items[:limit], 1):
        preview = item.original_prompt[:40] + "..." if len(item.original_prompt) > 40 else item.original_prompt
        timestamp = item.timestamp[:19].replace("T", " ") if item.timestamp else ""
        table.add_row(str(index), timestamp, preview, item.framework or "-")

    console.print()
    console.print(table)
    console.print()


def show_history_detail(item) -> None:
    console.print()
    console.print(
        Panel(
            f"[bold]Record {item.id}[/bold]\n"
            f"[dim]Time: {item.timestamp}[/dim]\n"
            f"[dim]Model: {item.model or '<unknown>'}[/dim]\n"
            f"[dim]Framework: {item.framework or '-'}[/dim]",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )
    console.print(Panel(item.original_prompt, title="Original Prompt", border_style="blue", box=box.ROUNDED))
    for index, optimized in enumerate(item.optimized_prompts, 1):
        console.print(
            Panel(
                Markdown(optimized.get("prompt", "")),
                title=f"Version {index}: {optimized.get('name', '')}",
                border_style="green",
                box=box.ROUNDED,
            )
        )
    console.print()


def show_framework_selection(framework: PromptFramework) -> None:
    info = PROMPT_FRAMEWORKS[framework]
    console.print()
    console.print(
        Panel(
            f"[green]Using [bold]{info.name}[/bold] for optimization.[/green]",
            border_style="green",
            box=box.ROUNDED,
        )
    )
    console.print()


def show_framework_components(framework: PromptFramework) -> None:
    info = PROMPT_FRAMEWORKS[framework]
    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column("Component", style="cyan")
    for component in info.components:
        table.add_row(component)
    console.print()
    console.print(table)
    console.print()


def show_docs_list(docs: List[dict], current_doc: Optional[dict] = None) -> None:
    if not docs:
        console.print()
        console.print(
            Panel(
                "[dim]No requirement documents found in prompts/.[/dim]\n"
                "[dim]Use /savedoc <name> to create one.[/dim]",
                title="Requirement Docs",
                border_style="cyan",
                box=box.ROUNDED,
            )
        )
        console.print()
        return

    current_file = current_doc.get("file") if current_doc else None
    table = Table(box=box.ROUNDED, border_style="cyan")
    table.add_column("#", style="cyan", width=4)
    table.add_column("File", style="green", width=22)
    table.add_column("Name", style="white", width=25)
    table.add_column("Preview", style="dim")
    table.add_column("Status", style="yellow", width=10)

    for index, doc in enumerate(docs, 1):
        status = "current" if doc.get("file") == current_file else ""
        table.add_row(
            str(index),
            doc.get("file", ""),
            doc.get("name", ""),
            doc.get("preview", ""),
            status,
        )

    console.print()
    console.print(table)
    console.print()


def show_doc_detail(doc) -> None:
    if not doc:
        console.print()
        console.print(
            Panel(
                "[dim]No requirement document is currently loaded.[/dim]",
                title="Current Requirement Doc",
                border_style="cyan",
                box=box.ROUNDED,
            )
        )
        console.print()
        return

    console.print()
    console.print(
        Panel(
            f"[bold]{doc.name}[/bold]\n[dim]{doc.file_path}[/dim]",
            title="Requirement Document",
            border_style="green",
            box=box.ROUNDED,
        )
    )
    if doc.intro:
        console.print(Panel(doc.intro, title="Project Context", border_style="cyan", box=box.ROUNDED))
    if doc.tune:
        console.print(Panel(doc.tune, title="Tuning Requirements", border_style="yellow", box=box.ROUNDED))
    console.print()
