"""
命令处理模块

提供各种命令的处理逻辑，如模型切换、配置查看、历史记录等。
"""
from typing import Optional, Tuple, List

from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.config import Config, global_config
from src.ollama_client import LLMClient
from src.history import HistoryManager, global_history
from src.strategies import (
    PromptFramework,
    PROMPT_FRAMEWORKS,
    get_recommended_framework,
    get_framework_match_reason,
)
from src.ui import (
    console,
    print_error,
    print_success,
    print_warning,
    print_framework_recommendation,
)
from src.ui.tables import (
    show_models,
    show_config,
    show_frameworks,
    show_history_items,
    show_history_detail,
    show_framework_components,
)
from src.clipboard import copy_to_clipboard
from src.logger import get_logger

logger = get_logger("commands")


def check_ollama(config: Optional[Config] = None, preferred_model: Optional[str] = None, non_interactive: bool = False) -> Tuple[bool, LLMClient, str]:
    """
    检查 LLM 服务并选择模型

    Args:
        config: 配置对象
        preferred_model: 优先使用的模型（如命令行指定）
        non_interactive: 非交互模式，不提示用户选择

    Returns:
        tuple: (成功标志，LLM 客户端，模型名称或错误信息)
    """
    client = LLMClient(config)

    if not client.check_connection():
        provider = config.provider if config else "ollama"
        if provider == "ollama":
            return False, client, "无法连接到 Ollama 服务"
        else:
            return False, client, f"无法连接到 {provider} API 服务"

    try:
        if config and config.provider != "ollama":
            # 远程 API，直接使用配置的模型
            model = preferred_model or client.get_current_model()
            if model:
                client.set_model(model)
            return True, client, model or "default"

        # Ollama 需要列出本地模型
        models = client.list_models()
        if not models:
            return False, client, "未找到任何已安装的模型"

        # 优先使用命令行指定的模型
        if preferred_model:
            if preferred_model in models:
                client.set_model(preferred_model)
                return True, client, preferred_model
            else:
                if non_interactive:
                    return False, client, f"指定的模型 '{preferred_model}' 不存在"
                console.print(f"[yellow]警告：指定的模型 [bold]{preferred_model}[/bold] 未安装[/yellow]")

        # 检查配置的默认模型
        configured_model = config.default_model if config else ""
        if configured_model and configured_model in models:
            client.set_model(configured_model)
            return True, client, configured_model
        elif configured_model and configured_model not in models and not non_interactive:
            console.print(f"\n[yellow]警告：配置的默认模型 [bold]{configured_model}[/bold] 未安装[/yellow]\n")
            selected = select_model(client, config)
            if selected:
                client.set_model(selected)
                if Confirm.ask(f"是否将 [green]{selected}[/green] 保存为默认模型？", default=True):
                    config.update(default_model=selected)
                return True, client, selected
            else:
                first_model = models[0]
                client.set_model(first_model)
                console.print(f"[dim]使用第一个可用模型：{first_model}[/dim]")
                return True, client, first_model
        else:
            # 使用第一个可用模型
            first_model = models[0]
            client.set_model(first_model)
            return True, client, first_model
    except Exception as e:
        return False, client, str(e)


def select_model(client, config: Config) -> Optional[str]:
    """让用户选择模型"""
    models = client.get_available_models()

    console.print()
    for i, model in enumerate(models, 1):
        console.print(f"  [cyan]{i}[/cyan]. {model}")

    console.print(f"\n当前配置模型：[yellow]{config.default_model or '（未配置）'}[/yellow]")
    console.print("[dim]输入模型编号切换，或直接输入模型名称，或按回车取消[/dim]")

    choice = Prompt.ask("\n[bold cyan]请选择模型[/bold cyan]")

    if not choice:
        return None

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(models):
            return models[idx]
        else:
            console.print("[red]无效的编号[/red]")
            return None

    if choice in models:
        return choice
    else:
        console.print(f"[red]模型 '{choice}' 不存在[/red]")
        return None


def handle_model_command(client, config: Config) -> None:
    """处理模型切换命令"""
    new_model = select_model(client, config)
    if new_model:
        client.set_model(new_model)
        config.update(default_model=new_model)
        print_success(f"已切换到模型：[bold]{new_model}[/bold]")


def handle_config_command(config: Config) -> None:
    """处理配置查看命令"""
    show_config(config)


def handle_frameworks_command() -> None:
    """处理框架查看命令"""
    show_frameworks()


def handle_history_command(history: HistoryManager) -> None:
    """处理历史记录命令"""
    items = history.get_all(limit=20)
    show_history_items(items, limit=10)

    if items:
        choice = Prompt.ask(
            "\n[bold cyan]输入编号查看详情，或按回车返回[/bold cyan]",
            default=""
        )
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                show_history_detail(items[idx])

                # 询问是否复制
                if Confirm.ask("\n是否复制某个版本到剪贴板？", default=False):
                    version = Prompt.ask(
                        "输入版本号",
                        choices=[str(i) for i in range(1, len(items[idx].optimized_prompts) + 1)],
                    )
                    selected = items[idx].optimized_prompts[int(version) - 1]
                    copy_to_clipboard(selected.get("prompt", ""))
                    print_success("已复制到剪贴板")


def handle_temperature_command(client, config: Config) -> None:
    """处理温度参数设置命令"""
    current = client.temperature
    console.print(f"\n当前温度参数：[yellow]{current}[/yellow]")
    console.print("[dim]温度范围：0.0 - 2.0（越低越确定，越高越随机）[/dim]\n")

    value = Prompt.ask(
        "[bold cyan]请输入新的温度值[/bold cyan]",
        default=str(current)
    )

    try:
        new_temp = float(value)
        if 0.0 <= new_temp <= 2.0:
            client.set_temperature(new_temp)
            config.update(temperature=new_temp)
            print_success(f"温度已设置为：[bold]{new_temp}[/bold]")
        else:
            print_error("温度必须在 0.0 到 2.0 之间")
    except ValueError:
        print_error(f"无效的温度值：{value}")


def select_framework(prompt_text: str) -> Optional[PromptFramework]:
    """让用户选择或确认 Prompt 框架"""
    recommended = get_recommended_framework(prompt_text)
    info = PROMPT_FRAMEWORKS[recommended]

    # 获取匹配原因
    match_reason = get_framework_match_reason(prompt_text, recommended)

    print_framework_recommendation(info, match_reason=match_reason)
    show_framework_components(recommended)

    console.print("\n[bold yellow]请选择：[/bold yellow]")
    console.print("  [green]1[/green]. 使用推荐框架 [dim](按回车默认)[/dim]")
    console.print("  [green]2[/green]. 选择其他框架")
    console.print("  [green]3[/green]. 跳过框架选择 [dim](直接优化)[/dim]")

    choice = Prompt.ask("\n[bold cyan]请选择[/bold cyan]", choices=["1", "2", "3"], default="1")

    if choice == "1":
        return recommended
    elif choice == "2":
        return choose_manual_framework()
    else:
        return None


def choose_manual_framework() -> PromptFramework:
    """手动选择框架"""
    console.print()
    console.print("[bold]请选择一个 Prompt 框架：[/bold]\n")

    for i, (fw, info) in enumerate(PROMPT_FRAMEWORKS.items(), 1):
        console.print(f"  [cyan]{i}[/cyan]. [bold]{info.name}[/bold] - {info.description}")

    choice = Prompt.ask(
        "\n[bold cyan]请输入框架编号[/bold cyan]",
        choices=[str(i) for i in range(1, len(PROMPT_FRAMEWORKS) + 1)],
        default="1"
    )

    fw_list = list(PROMPT_FRAMEWORKS.keys())
    return fw_list[int(choice) - 1]


def handle_copy_version(results: List, config: Config) -> None:
    """处理复制版本到剪贴板"""
    if not config.auto_clipboard:
        return

    choice = Prompt.ask(
        "\n[bold cyan]输入版本号复制到剪贴板，或按回车继续[/bold cyan]",
        default=""
    )

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(results):
            prompt = results[idx].get("prompt", "")
            if prompt:
                copy_to_clipboard(prompt)
                print_success("已复制到剪贴板")


def get_version_count() -> int:
    """获取用户选择的版本数量"""
    console.print()
    versions = Prompt.ask(
        "[bold cyan]要生成几个优化版本？[/bold cyan] (1-3)",
        choices=["1", "2", "3"],
        default="3"
    )
    console.print()
    return int(versions)
