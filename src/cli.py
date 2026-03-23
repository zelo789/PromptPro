"""PromptPro CLI entrypoint."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional

from rich import box
from rich import print as rprint
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table

from src.clipboard import copy_to_clipboard
from src.config import global_config
from src.exceptions import PromptProError
from src.history import global_history
from src.logger import get_logger, setup_logging
from src.ollama_client import LLMClient
from src.requirement import get_requirement_manager
from src.strategies import (
    LEVEL_CONFIGS,
    PROMPT_FRAMEWORKS,
    OptimizationLevel,
    PromptFramework,
    get_framework_match_reason,
    get_recommended_framework,
)
from src.ui import console, print_error, print_success, print_warning
from src.ui.tables import show_docs_list, show_doc_detail, show_optimized_versions

logger = get_logger("cli")

CLARIFYING_QUESTIONS_PROMPT = """You are an expert requirements analyst specializing in prompt engineering.
Your task is to ask targeted clarifying questions to deeply understand the user's prompt.

Analyze the original prompt and generate 6-10 specific questions that cover:

1. **Context & Background**: Why is this needed? What's the bigger picture?
2. **Target Audience**: Who will use the output? What expertise level?
3. **Output Format**: What format should the result be in? Length? Structure?
4. **Constraints**: Any limitations, rules, or requirements to follow?
5. **Examples**: Any reference materials or style guides?
6. **Edge Cases**: What should happen in special situations?

Requirements:
- Questions must be specific and actionable for the given prompt
- Ask follow-up questions based on what you don't know about the prompt
- Each question should help significantly improve the optimization
- Return one question per line, no numbering
- Return ONLY questions, no explanations

Original prompt:
{prompt}"""

REFINE_PROMPT = """You are a prompt refinement expert. Based on the user's feedback, refine the optimized prompt to better meet user needs.

Original prompt: {original}

Current optimized version:
{current_version}

User feedback: {feedback}

Please provide a refined version of the prompt that addresses the user's feedback."""

_encoding_fixed = False


def _fix_windows_encoding() -> None:
    global _encoding_fixed
    if _encoding_fixed or sys.platform != "win32":
        return

    stream = sys.stdout
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")
        _encoding_fixed = True
        return

    buffer = getattr(stream, "buffer", None)
    if buffer is None:
        return

    import io

    # Fallback for environments without TextIOBase.reconfigure.
    sys.stdout = io.TextIOWrapper(buffer, encoding="utf-8", errors="replace")
    _encoding_fixed = True


def generate_clarifying_questions(prompt: str, client: LLMClient) -> List[str]:
    messages = [{"role": "user", "content": CLARIFYING_QUESTIONS_PROMPT.format(prompt=prompt)}]

    try:
        response = client.chat(messages)
    except Exception as exc:
        logger.error("Failed to generate clarifying questions: %s", exc)
        return []

    questions: List[str] = []
    for line in response.strip().splitlines():
        cleaned = line.strip()
        # Remove numbering like "1.", "1)", "①", etc.
        cleaned = re.sub(r"^[\d\u2460-\u249b]+[.)]\s*", "", cleaned)
        cleaned = re.sub(r"^[①-⑨]\s*", "", cleaned)
        if cleaned and not cleaned.startswith("#") and len(cleaned) > 5:
            questions.append(cleaned)
    return questions[:8]  # Increased from 5 to 8


def ask_clarifying_questions(prompt: str, client: LLMClient) -> str:
    # Always ask clarifying questions to get better results
    rprint("[dim]深入分析需求中...[/dim]")
    questions = generate_clarifying_questions(prompt, client)

    # If no questions generated, try again with simpler prompt
    if not questions:
        simpler_prompt = prompt + "\n\n请生成3-5个关于这个需求的澄清问题。"
        messages = [{"role": "user", "content": simpler_prompt}]
        try:
            response = client.chat(messages)
            for line in response.strip().splitlines():
                cleaned = line.strip()
                if cleaned and len(cleaned) > 5 and not cleaned.startswith("#"):
                    questions.append(cleaned)
        except Exception:
            pass

    if not questions:
        rprint("[yellow]无法生成澄清问题，继续优化...[/yellow]\n")
        return prompt

    console.print()
    console.print(
        Panel(
            "[bold]请回答以下问题以获得更好的优化结果:[/bold]",
            title="Clarify",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )
    console.print()

    answers: List[str] = []
    for index, question in enumerate(questions, 1):
        console.print(f"  [cyan][bold]{index}[/bold][/cyan] {question}")
        answer = Prompt.ask("  [dim]请输入你的回答 (直接回车跳过问题)[/dim]", default="")
        if answer.lower() == "skip":
            break
        if answer.strip():
            answers.append(f"问: {question}\n答: {answer.strip()}")
        console.print()

    if not answers:
        rprint("[yellow]未回答任何问题，将直接进行优化...[/yellow]\n")
        return prompt

    return f"原始需求:\n{prompt}\n\n补充信息:\n" + "\n".join(answers)


def show_help() -> None:
    console.print()
    console.print(
        Panel(
            "[bold]PromptPro command reference[/bold]",
            border_style="cyan",
            box=box.DOUBLE,
        )
    )
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 3))
    table.add_column("Command", style="green", width=20)
    table.add_column("Description", style="white")
    table.add_row("/help, /h", "Show help")
    table.add_row("/quit, /q, /exit", "Exit")
    table.add_row("/model, /m", "List or switch model")
    table.add_row("/provider, /p", "List or switch provider")
    table.add_row("/frameworks, /f", "Show supported frameworks")
    table.add_row("/config", "Show current config")
    table.add_row("/history", "Show optimization history")
    table.add_row("/temp <value>", "Set temperature")
    table.add_row("/clarify", "Toggle clarifying questions")
    table.add_row("/docs, /d", "List requirement docs")
    table.add_row("/load, /l <name>", "Load requirement doc")
    table.add_row("/doc", "Show current requirement doc")
    table.add_row("/savedoc <name>", "Create requirement doc")
    table.add_row("/cleardoc", "Clear current requirement doc")
    console.print(table)
    console.print()


def show_models(client: LLMClient) -> None:
    models = client.get_available_models()
    current = client.get_current_model()

    rprint("\n[bold]Available models[/bold]\n")
    for index, model in enumerate(models, 1):
        marker = " [cyan](current)[/cyan]" if model == current else ""
        rprint(f"  [green]{index}[/green]. {model}{marker}")
    rprint("\n[dim]Use /model <name> or enter a number to switch.[/dim]\n")


def show_providers() -> None:
    current = global_config.provider
    providers = [
        ("ollama", "Local Ollama", global_config.ollama_base_url),
        ("openai", "OpenAI API", global_config.openai_base_url),
        ("claude", "Claude API", global_config.claude_base_url),
        ("custom", "OpenAI-compatible custom API", global_config.custom_base_url or "<unset>"),
    ]

    rprint("\n[bold]Providers[/bold]\n")
    for name, description, url in providers:
        marker = " [cyan](current)[/cyan]" if name == current else ""
        rprint(f"  [green]{name}[/green] - {description}{marker}")
        rprint(f"       [dim]{url}[/dim]")
    rprint()


def switch_provider(args: str) -> None:
    if not args:
        show_providers()
        return

    provider = args.lower()
    valid_providers = {"ollama", "openai", "claude", "custom"}
    if provider not in valid_providers:
        print_error(f"Invalid provider: {args}")
        return

    missing_message = None
    if provider == "openai" and not global_config.openai_api_key:
        missing_message = "OPENAI_API_KEY is not configured"
    elif provider == "claude" and not global_config.claude_api_key:
        missing_message = "CLAUDE_API_KEY is not configured"
    elif provider == "custom" and not global_config.custom_base_url:
        missing_message = "CUSTOM_BASE_URL is not configured"

    if missing_message:
        print_warning(missing_message)

    global_config.update(provider=provider)
    print_success(f"Provider switched to [bold]{provider}[/bold]")
    rprint("[dim]Restart PromptPro to reconnect with the new provider.[/dim]")


def _persist_model_for_provider(model: str) -> None:
    provider = global_config.provider
    if provider == "ollama":
        global_config.update(default_model=model)
    elif provider == "openai":
        global_config.update(openai_model=model)
    elif provider == "claude":
        global_config.update(claude_model=model)
    elif provider == "custom":
        global_config.update(custom_model=model)


def switch_model(args: str, client: LLMClient) -> None:
    if not args:
        show_models(client)
        return

    models = client.get_available_models()
    if args.isdigit():
        index = int(args) - 1
        if not 0 <= index < len(models):
            print_error(f"Invalid model index: {args}")
            return
        model = models[index]
    else:
        model = args

    client.set_model(model)
    _persist_model_for_provider(model)
    print_success(f"Model switched to [bold]{model}[/bold]")


def show_frameworks() -> None:
    console.print()
    table = Table(box=box.ROUNDED, border_style="cyan")
    table.add_column("Framework", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Recommended for", style="green")

    for framework, info in PROMPT_FRAMEWORKS.items():
        table.add_row(framework.value, info.description, info.recommended_for)

    console.print(table)
    console.print()


def show_history() -> None:
    items = global_history.get_all(limit=10)
    if not items:
        rprint("\n[dim]No history yet.[/dim]\n")
        return

    rprint("\n[bold]Recent history[/bold]\n")
    for index, item in enumerate(items, 1):
        preview = item.original_prompt[:40] + "..." if len(item.original_prompt) > 40 else item.original_prompt
        framework = item.framework or "-"
        rprint(f"  [green]{index}[/green]. {preview} [yellow]{framework}[/yellow]")
    rprint()


def set_temperature(args: str, client: LLMClient) -> None:
    if not args:
        rprint(f"\nCurrent temperature: [yellow]{client.temperature}[/yellow]\n")
        return

    try:
        temperature = float(args)
    except ValueError:
        print_error(f"Invalid temperature: {args}")
        return

    if not 0.0 <= temperature <= 2.0:
        print_error("Temperature must be between 0.0 and 2.0")
        return

    client.set_temperature(temperature)
    global_config.update(temperature=temperature)
    print_success(f"Temperature set to [bold]{temperature}[/bold]")


def show_config() -> None:
    current_model = global_config.get_current_model() or "<auto>"

    rprint("\n[bold]Current config[/bold]\n")
    rprint(f"  [cyan]Provider[/cyan]: {global_config.provider}")
    rprint(f"  [cyan]Model[/cyan]: {current_model}")
    rprint(f"  [cyan]Temperature[/cyan]: {global_config.temperature}")
    rprint(f"  [cyan]History[/cyan]: {'on' if global_config.enable_history else 'off'}")
    rprint(f"  [cyan]Clipboard[/cyan]: {'on' if global_config.auto_clipboard else 'off'}")
    rprint(f"  [cyan]Clarify[/cyan]: {'on' if global_config.enable_clarifying_questions else 'off'}")
    rprint(f"\n[dim]Config file: {global_config.config_file}[/dim]\n")


def toggle_clarify() -> None:
    value = not global_config.enable_clarifying_questions
    global_config.update(enable_clarifying_questions=value)
    print_success(f"Clarifying questions {'enabled' if value else 'disabled'}")


def show_docs() -> None:
    manager = get_requirement_manager()
    docs = manager.list_docs()
    current_doc = manager.get_current_doc()
    current_info = None
    if current_doc:
        current_info = {"name": current_doc.name, "file": Path(current_doc.file_path).stem}
    show_docs_list(docs, current_info)


def load_requirement_doc(args: str) -> None:
    if not args:
        print_error("Usage: /load <name-or-index>")
        return

    manager = get_requirement_manager()
    identifier = args
    if args.isdigit():
        docs = manager.list_docs()
        index = int(args) - 1
        if not 0 <= index < len(docs):
            print_error(f"Invalid doc index: {args}")
            return
        identifier = docs[index]["file"]

    try:
        doc = manager.select_doc(identifier)
    except Exception as exc:
        print_error(f"Failed to load document: {exc}")
        return

    print_success(f"Loaded document [bold]{doc.name}[/bold]")


def show_current_doc() -> None:
    show_doc_detail(get_requirement_manager().get_current_doc())


def clear_current_doc() -> None:
    get_requirement_manager().clear_current_doc()
    print_success("Current requirement document cleared")


def save_requirement_doc(args: str) -> None:
    if not args:
        print_error("Usage: /savedoc <name>")
        return

    console.print()
    console.print(
        Panel(
            f"[bold]Create requirement doc[/bold]\n[dim]Name: {args}[/dim]",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )
    console.print()

    intro = Prompt.ask("[cyan]Project context[/cyan]", default="")
    tune = Prompt.ask("[cyan]Tuning requirements[/cyan]", default="")

    if not intro and not tune:
        print_warning("Empty document skipped")
        return

    path = get_requirement_manager().create_doc(name=args, intro=intro, tune=tune)
    print_success(f"Document created: {path}")


def generate_optimized_versions(
    prompt: str,
    client: LLMClient,
    num_versions: int = 3,
    framework: Optional[PromptFramework] = None,
) -> List[dict]:
    results: List[dict] = []
    levels = list(OptimizationLevel)
    num_versions = max(1, min(num_versions, len(levels)))
    level_names = {
        OptimizationLevel.LIGHT: "Light optimization",
        OptimizationLevel.MODERATE: "Moderate optimization",
        OptimizationLevel.DEEP: "Deep optimization",
    }

    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[progress.description]{task.description}", style="cyan"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Optimizing...[/cyan]", total=num_versions)
        for level in levels[:num_versions]:
            config = LEVEL_CONFIGS[level]
            messages = [
                {"role": "system", "content": config["system_prompt"]},
                {"role": "user", "content": f"Please optimize this prompt:\n\n{prompt}"},
            ]
            try:
                optimized = client.chat(messages)
                results.append(
                    {
                        "level": level.value,
                        "name": level_names[level],
                        "description": config["description"],
                        "prompt": optimized,
                    }
                )
            except Exception as exc:
                logger.error("Failed to generate %s version: %s", level.value, exc)
            progress.advance(task)

    if framework:
        info = PROMPT_FRAMEWORKS[framework]
        messages = [
            {"role": "system", "content": info.system_prompt},
            {"role": "user", "content": f"Please optimize this prompt:\n\n{prompt}"},
        ]
        try:
            optimized = client.chat(messages)
            results.append(
                {
                    "level": "framework",
                    "name": info.name,
                    "description": info.description,
                    "prompt": optimized,
                }
            )
        except Exception as exc:
            logger.error("Failed to generate framework version: %s", exc)

    return results


def _get_interactive_num_versions() -> int:
    return max(1, min(global_config.num_versions, len(OptimizationLevel)))


def _offer_copy_to_clipboard(results: List[dict]) -> None:
    if not global_config.auto_clipboard or not results:
        return

    choice = Prompt.ask("\n[cyan]Enter version to copy[/cyan] [dim](1-4)[/dim]", default="")
    if not choice.isdigit():
        return

    index = int(choice) - 1
    if 0 <= index < len(results):
        if copy_to_clipboard(results[index]["prompt"]):
            print_success("Copied to clipboard")
        else:
            print_warning("Clipboard is not available")


def refine_prompt(
    original_prompt: str,
    results: List[dict],
    client: LLMClient,
    selected_version_idx: int,
) -> None:
    """Allow user to provide feedback and refine a specific version."""
    selected = results[selected_version_idx]
    current_version = selected["prompt"]

    console.print()
    console.print(
        Panel(
            f"[bold]Refine Version {selected_version_idx + 1}: {selected['name']}[/bold]\n"
            "[dim]Enter your feedback to improve the prompt, or press Enter to go back.[/dim]",
            border_style="yellow",
            box=box.ROUNDED,
        )
    )
    console.print()

    # Show current version for reference
    console.print(Panel(
        f"[dim]Current version:[/dim]\n{current_version[:500]}{'...' if len(current_version) > 500 else ''}",
        border_style="dim",
        box=box.ROUNDED,
    ))
    console.print()

    feedback = Prompt.ask("[yellow]Your feedback[/yellow] [dim](e.g., 'make it more concise', 'add more examples')[/dim]")

    if not feedback.strip():
        return

    # Generate refined version
    messages = [
        {"role": "user", "content": REFINE_PROMPT.format(
            original=original_prompt,
            current_version=current_version,
            feedback=feedback,
        )}
    ]

    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[progress.description]{task.description}", style="cyan"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Refining prompt...[/cyan]", total=1)
        try:
            refined = client.chat(messages)
            progress.advance(task)
        except Exception as exc:
            logger.error("Failed to refine prompt: %s", exc)
            print_error(f"Refinement failed: {exc}")
            return

    # Update the selected version with refined result
    results[selected_version_idx] = {
        **selected,
        "prompt": refined,
        "name": f"{selected['name']} (refined)",
    }

    console.print()
    console.print(
        Panel(
            f"[bold green]Refined Version {selected_version_idx + 1}[/bold green]",
            border_style="green",
            box=box.ROUNDED,
        )
    )
    console.print()
    console.print(Panel(
        refined,
        border_style="cyan",
        box=box.ROUNDED,
    ))
    console.print()


def _offer_refine_or_copy(results: List[dict], original_prompt: str, client: LLMClient) -> None:
    """Simplified options after optimization."""
    while True:
        console.print()
        choice = Prompt.ask(
            "[cyan]选择版本复制[/cyan] [dim](1-4)[/dim]，或 [yellow]输入数字+空格+反馈来细化[/yellow] [dim]例如: 3 添加更多安全约束[/dim]",
            default="",
        )

        # Empty input - exit
        if not choice.strip():
            break

        # If just a number, copy
        if choice.strip().isdigit():
            index = int(choice.strip()) - 1
            if 0 <= index < len(results):
                if copy_to_clipboard(results[index]["prompt"]):
                    print_success("已复制到剪贴板")
                else:
                    print_warning("剪贴板不可用")
            else:
                print_error(f"无效版本号: {choice}")
            continue

        # Parse "number + feedback" format: "3 添加更多安全约束"
        parts = choice.strip().split(maxsplit=1)
        if len(parts) >= 1 and parts[0].isdigit():
            idx = int(parts[0]) - 1
            if 0 <= idx < len(results):
                feedback = parts[1] if len(parts) > 1 else ""
                if feedback:
                    refine_prompt(original_prompt, results, client, idx)
                else:
                    print_warning("请输入反馈内容，例如: 3 添加更多安全约束")
            else:
                print_error(f"无效版本号: {parts[0]}")
            continue

        print_error("输入格式: 1-4 复制，3 你的反馈 细化版本")


def optimize_prompt(prompt: str, client: LLMClient) -> None:
    manager = get_requirement_manager()
    current_doc = manager.get_current_doc()

    if current_doc:
        prompt_with_doc = (
            "[Requirement document context]\n"
            f"{current_doc.to_prompt_context()}\n\n"
            f"[Original user request]\n{prompt}"
        )
    else:
        prompt_with_doc = prompt

    if global_config.enable_clarifying_questions:
        enhanced_prompt = ask_clarifying_questions(prompt_with_doc, client)
    else:
        enhanced_prompt = prompt_with_doc

    framework = get_recommended_framework(enhanced_prompt)
    reason = get_framework_match_reason(enhanced_prompt)
    framework_info = PROMPT_FRAMEWORKS[framework]
    rprint(f"\n[dim]Recommended framework: [cyan]{framework_info.name}[/cyan] ({reason})[/dim]\n")

    results = generate_optimized_versions(
        enhanced_prompt,
        client,
        num_versions=_get_interactive_num_versions(),
        framework=framework,
    )
    if not results:
        print_error("Optimization failed, please retry")
        return

    show_optimized_versions(results)

    if global_config.enable_history:
        global_history.add(
            original_prompt=prompt,
            optimized_prompts=results,
            framework=framework.value,
            model=client.get_current_model(),
        )

    _offer_refine_or_copy(results, prompt, client)


def _setup_provider_interactive() -> bool:
    """Interactive provider setup when connection fails."""
    from src.ui.console import console

    console.print()
    console.print(
        Panel(
            "[bold]Unable to connect to the configured LLM service[/bold]\n"
            "[dim]Please select a provider to use:[/dim]",
            border_style="yellow",
            box=box.ROUNDED,
        )
    )
    console.print()

    providers = [
        ("1", "ollama", "Local Ollama (free, runs on your machine)"),
        ("2", "openai", "OpenAI API (GPT-4, GPT-4o, etc.)"),
        ("3", "claude", "Claude API (Anthropic Claude)"),
        ("4", "custom", "Custom OpenAI-compatible API"),
    ]

    for num, name, desc in providers:
        console.print(f"  [cyan]{num}[/cyan]. [bold]{name}[/bold] - {desc}")

    console.print()

    while True:
        choice = Prompt.ask("[cyan]Select provider[/cyan] [dim](1-4)[/dim]", default="")
        if choice not in {"1", "2", "3", "4"}:
            print_error("Please enter a number between 1 and 4")
            continue

        provider_map = {"1": "ollama", "2": "openai", "3": "claude", "4": "custom"}
        provider = provider_map[choice]
        break

    # Configure provider-specific settings
    if provider == "ollama":
        url = Prompt.ask(
            "[cyan]Ollama URL[/cyan]",
            default=global_config.ollama_base_url or "http://localhost:11434",
        )
        global_config.update(provider="ollama", ollama_base_url=url)
        print_success(f"Provider set to [bold]ollama[/bold] (URL: {url})")

    elif provider == "openai":
        api_key = Prompt.ask(
            "[cyan]OpenAI API Key[/cyan]",
            password=True,
            default=global_config.openai_api_key,
        )
        url = Prompt.ask(
            "[cyan]API Base URL[/cyan]",
            default=global_config.openai_base_url or "https://api.openai.com/v1",
        )
        model = Prompt.ask(
            "[cyan]Model[/cyan]",
            default=global_config.openai_model or "gpt-4o-mini",
        )
        global_config.update(
            provider="openai",
            openai_api_key=api_key,
            openai_base_url=url,
            openai_model=model,
        )
        print_success(f"Provider set to [bold]openai[/bold] (Model: {model})")

    elif provider == "claude":
        api_key = Prompt.ask(
            "[cyan]Claude API Key[/cyan]",
            password=True,
            default=global_config.claude_api_key,
        )
        url = Prompt.ask(
            "[cyan]API Base URL[/cyan]",
            default=global_config.claude_base_url or "https://api.anthropic.com",
        )
        model = Prompt.ask(
            "[cyan]Model[/cyan]",
            default=global_config.claude_model or "claude-3-5-sonnet-20241022",
        )
        global_config.update(
            provider="claude",
            claude_api_key=api_key,
            claude_base_url=url,
            claude_model=model,
        )
        print_success(f"Provider set to [bold]claude[/bold] (Model: {model})")

    elif provider == "custom":
        api_key = Prompt.ask(
            "[cyan]API Key[/cyan]",
            password=True,
            default=global_config.custom_api_key,
        )
        url = Prompt.ask(
            "[cyan]API Base URL[/cyan]",
            default=global_config.custom_base_url or "",
        )
        model = Prompt.ask(
            "[cyan]Model[/cyan]",
            default=global_config.custom_model or "",
        )
        global_config.update(
            provider="custom",
            custom_api_key=api_key,
            custom_base_url=url,
            custom_model=model,
        )
        print_success(f"Provider set to [bold]custom[/bold] (Model: {model})")

    console.print()
    console.print("[dim]Configuration saved. Please restart PromptPro to use the new provider.[/dim]")
    console.print()
    return False


def _connect_client(client: LLMClient, requested_model: Optional[str] = None) -> bool:
    if not client.check_connection():
        # Offer interactive setup
        console.print()
        setup_choice = Prompt.ask(
            "[yellow]Connection failed. Setup new provider?[/yellow] [dim](y/n)[/dim]",
            default="y",
        )
        if setup_choice.lower() == "y":
            if not _setup_provider_interactive():
                return False
            # Try again with new config - create new client
            client = LLMClient(global_config)
            if not client.check_connection():
                print_error("Still unable to connect with the new configuration")
                return False
        else:
            print_error("Unable to connect to the configured LLM service")
            return False

    if global_config.provider == "ollama":
        models = client.list_models()
        if not models:
            print_error("No Ollama models are installed")
            return False

        chosen_model = requested_model or global_config.default_model
        if chosen_model in models:
            client.set_model(chosen_model)
        else:
            client.set_model(models[0])
        return True

    chosen_model = requested_model or global_config.get_current_model()
    if chosen_model:
        client.set_model(chosen_model)
    return True


def interactive_mode() -> None:
    _fix_windows_encoding()

    rprint(
        "\n[bold cyan]PromptPro[/bold cyan] [dim]v0.4.0[/dim]\n"
        "[dim]Type /help for commands, or enter a prompt to optimize.[/dim]\n"
    )

    client = LLMClient(global_config)
    if not _connect_client(client):
        return

    rprint(
        f"[dim]Provider: [green]{global_config.provider}[/green] | "
        f"Model: [green]{client.get_current_model() or '<unset>'}[/green][/dim]\n"
    )

    while True:
        try:
            user_input = Prompt.ask("[bold green]>[/bold green]").strip()
            if not user_input:
                continue

            if user_input.startswith("/"):
                handle_slash_command(user_input, client)
                continue

            if user_input.isdigit():
                models = client.get_available_models()
                index = int(user_input) - 1
                if 0 <= index < len(models):
                    switch_model(models[index], client)
                else:
                    print_error(f"Invalid model index: {user_input}")
                continue

            optimize_prompt(user_input, client)
        except KeyboardInterrupt:
            rprint("\n[dim]Bye.[/dim]")
            break
        except SystemExit:
            break
        except PromptProError as exc:
            print_error(str(exc))
        except Exception as exc:
            logger.exception("Unhandled CLI error")
            print_error(f"Error: {exc}")


def handle_slash_command(input_str: str, client: LLMClient) -> None:
    parts = input_str[1:].split(maxsplit=1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    commands = {
        "help": lambda: show_help(),
        "h": lambda: show_help(),
        "model": lambda: switch_model(args, client),
        "m": lambda: switch_model(args, client),
        "provider": lambda: switch_provider(args),
        "p": lambda: switch_provider(args),
        "frameworks": lambda: show_frameworks(),
        "f": lambda: show_frameworks(),
        "config": lambda: show_config(),
        "history": lambda: show_history(),
        "temp": lambda: set_temperature(args, client),
        "clarify": lambda: toggle_clarify(),
        "docs": lambda: show_docs(),
        "d": lambda: show_docs(),
        "load": lambda: load_requirement_doc(args),
        "l": lambda: load_requirement_doc(args),
        "doc": lambda: show_current_doc(),
        "savedoc": lambda: save_requirement_doc(args),
        "cleardoc": lambda: clear_current_doc(),
        "quit": lambda: sys.exit(0),
        "q": lambda: sys.exit(0),
        "exit": lambda: sys.exit(0),
    }

    handler = commands.get(command)
    if handler is None:
        print_error(f"Unknown command: /{command}")
        return
    handler()


def quick_optimize(
    prompt: str,
    model: Optional[str] = None,
    level: int = 3,
    framework: Optional[str] = None,
    output: Optional[str] = None,
) -> None:
    _fix_windows_encoding()
    rprint("[bold cyan]PromptPro[/bold cyan] [dim]v0.4.0[/dim]\n")

    client = LLMClient(global_config)
    if not _connect_client(client, requested_model=model):
        return

    if framework:
        try:
            selected_framework = PromptFramework(framework.lower())
        except ValueError:
            selected_framework = get_recommended_framework(prompt)
    else:
        selected_framework = get_recommended_framework(prompt)

    reason = get_framework_match_reason(prompt)
    rprint(
        f"[dim]Provider: [green]{global_config.provider}[/green] | "
        f"Model: [green]{client.get_current_model() or '<unset>'}[/green][/dim]"
    )
    rprint(
        f"[dim]Framework: [cyan]{PROMPT_FRAMEWORKS[selected_framework].name}[/cyan] "
        f"({reason})[/dim]\n"
    )

    # CLI mode: skip clarify (requires interactive input)
    # Use interactive mode (pp without prompt) for clarify

    results = generate_optimized_versions(prompt, client, num_versions=level, framework=selected_framework)
    if not results:
        print_error("Optimization failed")
        return

    show_optimized_versions(results)

    if global_config.enable_history:
        global_history.add(
            original_prompt=prompt,
            optimized_prompts=results,
            framework=selected_framework.value,
            model=client.get_current_model(),
        )

    if output:
        output_path = Path(output)
        output_path.write_text(
            "\n\n".join(
                f"=== Version {index}: {result['name']} ===\n\n{result['prompt']}"
                for index, result in enumerate(results, 1)
            ),
            encoding="utf-8",
        )
        print_success(f"Saved output to {output_path}")


def run() -> None:
    setup_logging()
    _fix_windows_encoding()

    parser = argparse.ArgumentParser(description="PromptPro prompt optimization CLI")
    parser.add_argument("prompt", nargs="?", help="Prompt to optimize")
    parser.add_argument("-m", "--model", help="Model name")
    parser.add_argument("-l", "--level", type=int, default=3, choices=[1, 2, 3], help="Version count")
    parser.add_argument("-f", "--framework", help="Prompt framework")
    parser.add_argument("-o", "--output", help="Write results to file")
    parser.add_argument("--models", action="store_true", help="List models")
    parser.add_argument("--config", action="store_true", help="Show config")
    parser.add_argument("--history", action="store_true", help="Show history")
    args = parser.parse_args()

    if args.models:
        client = LLMClient(global_config)
        if not _connect_client(client):
            return
        show_models(client)
        return

    if args.config:
        show_config()
        return

    if args.history:
        show_history()
        return

    if args.prompt:
        quick_optimize(args.prompt, args.model, args.level, args.framework, args.output)
    else:
        interactive_mode()


if __name__ == "__main__":
    run()
