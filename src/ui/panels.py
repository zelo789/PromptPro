"""
面板组件模块

提供各种 Panel 组件的显示函数。
"""
from typing import Optional, List

from rich.panel import Panel
from rich.markdown import Markdown
from rich import box

from src.ui.console import console


def print_banner() -> None:
    """打印欢迎横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║    ██████╗ ██████╗  ██████╗ ██████╗ ██╗   ██╗███████╗██████╗  ██████╗   ║
║    ██╔══██╗██╔══██╗██╔═══██╗██╔══██╗██║   ██║██╔════╝██╔══██╗██╔═══██╗  ║
║    ██████╔╝██████╔╝██║   ██║██████╔╝██║   ██║█████╗  ██████╔╝██║   ██║  ║
║    ██╔══██╗██╔══██╗██║   ██║██╔══██╗██║   ██║██╔══╝  ██╔══██╗██║   ██║  ║
║    ██████╔╝██║  ██║╚██████╔╝██║  ██║╚██████╔╝███████╗██████╔╝╚██████╔╝  ║
║    ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═════╝  ╚═════╝   ║
║                                                                           ║
║                      PromptPro v0.4.0                                     ║
║                  让 Prompt 更懂 AI | Professional Optimizer               ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold cyan")
    console.print()


def print_help() -> None:
    """打印帮助信息"""
    from rich.table import Table
    table = Table(
        show_header=True,
        header_style="bold magenta",
        box=box.ROUNDED,
        border_style="cyan",
        title="[cyan]使用提示[/cyan]",
    )
    table.add_column("命令", style="green", width=20)
    table.add_column("说明", style="white", width=40)

    table.add_row("[green]quit[/green] / [green]q[/green]", "退出程序")
    table.add_row("[green]help[/green] / [green]h[/green]", "查看帮助信息")
    table.add_row("[green]frameworks[/green]", "查看所有 Prompt 框架")
    table.add_row("[green]config[/green]", "查看当前配置")
    table.add_row("[green]model[/green] / [green]m[/green]", "切换 AI 模型")
    table.add_row("[green]history[/green]", "查看优化历史")
    table.add_row("[green]temp[/green] / [green]t[/green]", "设置温度参数")

    console.print()
    console.print(table)
    console.print()
    console.print("[dim] 提示：直接输入你的 prompt，AI 会自动分析并优化[/dim]\n")


def print_error(message: str, title: str = "错误") -> None:
    """打印错误面板"""
    console.print()
    console.print(Panel(
        f"[bold red]{message}[/bold red]",
        title=f"[red]{title}[/red]",
        border_style="red",
        box=box.ROUNDED,
    ))
    console.print()


def print_success(message: str, title: str = "成功") -> None:
    """打印成功面板"""
    console.print()
    console.print(Panel(
        f"[bold green]{message}[/bold green]",
        title=f"[green]{title}[/green]",
        border_style="green",
        box=box.ROUNDED,
    ))
    console.print()


def print_warning(message: str, title: str = "警告") -> None:
    """打印警告面板"""
    console.print()
    console.print(Panel(
        f"[bold yellow]{message}[/bold yellow]",
        title=f"[yellow]{title}[/yellow]",
        border_style="yellow",
        box=box.ROUNDED,
    ))
    console.print()


def print_info(message: str, title: Optional[str] = None) -> None:
    """打印信息面板"""
    console.print()
    if title:
        console.print(Panel(
            message,
            title=title,
            border_style="cyan",
            box=box.ROUNDED,
        ))
    else:
        console.print(Panel(
            message,
            border_style="cyan",
            box=box.ROUNDED,
        ))
    console.print()


def print_prompt_panel(prompt: str, title: str = "原始 Prompt", style: str = "blue") -> None:
    """打印 Prompt 面板"""
    console.print()
    console.print(Panel(
        f"[bold white]{prompt}[/bold white]",
        title=f"[{style}]{title}[/{style}]",
        border_style=style,
        box=box.ROUNDED,
    ))
    console.print()


def print_analysis(analysis: str) -> None:
    """打印分析结果"""
    console.print()
    console.print(Panel(
        Markdown(analysis),
        title="[yellow]Prompt 分析结果[/yellow]",
        border_style="yellow",
        box=box.ROUNDED,
    ))
    console.print()


def print_framework_recommendation(framework_info, is_selected: bool = False, match_reason: str = "") -> None:
    """打印框架推荐"""
    border_style = "green" if is_selected else "cyan"

    content = f"[bold]{framework_info.name}[/bold]\n{framework_info.description}\n\n"

    if match_reason:
        content += f"[dim]匹配原因：{match_reason}[/dim]\n\n"
    else:
        content += f"[dim]推荐原因：适合{framework_info.recommended_for}[/dim]"

    console.print()
    console.print(Panel(
        content,
        title="推荐框架",
        border_style=border_style,
        box=box.ROUNDED,
    ))
    console.print()


def print_divergent_questions(questions: List[str]) -> None:
    """打印发散性问题"""
    if not questions:
        return

    console.print()
    console.print(Panel(
        "[bold]为了更好地优化，请回答以下问题：[/bold]\n"
        "[dim]（这些问题帮助 AI 更全面地理解你的需求）[/dim]",
        title="需求澄清",
        border_style="cyan",
        box=box.ROUNDED,
    ))
    console.print()

    for i, q in enumerate(questions, 1):
        console.print(f"  [cyan][bold]{i}[/bold][/cyan] {q}")


def print_versions_prompt() -> None:
    """打印版本数量选择提示"""
    console.print()
    console.print(Panel(
        "[bold]选择优化版本数量[/bold]\n"
        "[dim]1 = 轻度优化 | 2 = 轻度+中度 | 3 = 轻度+中度+深度[/dim]",
        border_style="cyan",
        box=box.ROUNDED,
    ))


def print_welcome_guide() -> None:
    """打印首次使用欢迎引导"""
    console.print()
    console.print(Panel(
        "[bold cyan]欢迎使用 PromptPro！[/bold cyan]\n\n"
        "PromptPro 是一个专业的 Prompt 优化工具，可以帮助你：\n\n"
        "  [green]✓[/green] 智能匹配最适合的 Prompt 框架\n"
        "  [green]✓[/green] 生成多个优化版本供对比选择\n"
        "  [green]✓[/green] 挖掘深层需求，完善 prompt 细节\n\n"
        "[dim]提示：直接输入你的 prompt 开始优化[/dim]",
        title="[bold]首次使用引导[/bold]",
        border_style="cyan",
        box=box.ROUNDED,
    ))
    console.print()


def print_first_run_tips() -> None:
    """打印首次运行提示"""
    console.print()
    console.print(Panel(
        "[bold]快速体验示例[/bold]\n\n"
        "试试以下 prompt，快速体验优化效果：\n\n"
        "  [cyan]1.[/cyan] 写一个排序算法\n"
        "  [cyan]2.[/cyan] 帮我写一封请假邮件\n"
        "  [cyan]3.[/cyan] 分析销售数据\n\n"
        "[dim]输入 prompt 后，AI 会自动分析并推荐框架[/dim]",
        title="[bold]示例 Prompt[/bold]",
        border_style="yellow",
        box=box.ROUNDED,
    ))
    console.print()