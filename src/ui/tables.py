"""
表格组件模块

提供各种数据表格的显示函数。
"""
from typing import List, Dict, Optional

from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich import box
from rich import print as rprint

from src.ui.console import console
from src.strategies import PromptFramework, PROMPT_FRAMEWORKS, get_recommended_framework


def create_choice_table(choices: List[Dict[str, str]]) -> Table:
    """创建选项表格"""
    table = Table(
        show_header=False,
        box=box.SIMPLE,
        padding=(0, 2),
    )
    table.add_column("选项", style="green")
    table.add_column("说明", style="white")

    for choice in choices:
        table.add_row(choice.get("option", ""), choice.get("description", ""))

    return table


def create_data_table(
    headers: List[str],
    rows: List[List[str]],
    title: Optional[str] = None,
) -> Table:
    """创建数据表格"""
    table = Table(
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold magenta",
        row_styles=["dim", "none"],
    )

    if title:
        table.title = f"[cyan]{title}[/cyan]"

    for header in headers:
        table.add_column(header)

    for row in rows:
        table.add_row(*row)

    return table


def show_frameworks_table() -> None:
    """显示所有 Prompt 框架（简洁版）"""
    rprint = console.print

    rprint("\n[bold]Prompt 框架[/bold]\n")

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("框架", style="cyan", width=12)
    table.add_column("描述", width=25)
    table.add_column("适用场景", width=30)

    for fw, info in PROMPT_FRAMEWORKS.items():
        table.add_row(info.name.replace(" 框架", ""), info.description, info.recommended_for)

    rprint(table)
    rprint("\n[dim]提示: 输入 prompt 时会自动推荐框架[/dim]\n")


def show_config_table(config) -> None:
    """显示配置（简洁版）"""
    rprint = console.print

    rprint("\n[bold]当前配置[/bold]\n")

    provider = config.provider
    provider_name = {
        "ollama": "Ollama (本地)",
        "openai": "OpenAI API",
        "claude": "Claude API",
        "custom": "自定义 API",
    }.get(provider, provider)

    rprint(f"  [cyan]提供商[/cyan]: {provider_name}")

    if provider == "ollama":
        rprint(f"  [cyan]模型[/cyan]: {config.default_model or '自动选择'}")
        rprint(f"  [cyan]Ollama 地址[/cyan]: {config.ollama_base_url}")
    elif provider == "openai":
        rprint(f"  [cyan]模型[/cyan]: {config.openai_model}")
        key_status = "已配置" if config.openai_api_key else "[red]未配置[/red]"
        rprint(f"  [cyan]API Key[/cyan]: {key_status}")
    elif provider == "claude":
        rprint(f"  [cyan]模型[/cyan]: {config.claude_model}")
        key_status = "已配置" if config.claude_api_key else "[red]未配置[/red]"
        rprint(f"  [cyan]API Key[/cyan]: {key_status}")
    elif provider == "custom":
        rprint(f"  [cyan]模型[/cyan]: {config.custom_model or '未指定'}")
        rprint(f"  [cyan]Base URL[/cyan]: {config.custom_base_url or '未配置'}")

    rprint(f"  [cyan]温度[/cyan]: {config.temperature}")
    rprint(f"  [cyan]历史记录[/cyan]: {'启用' if config.enable_history else '禁用'}")
    rprint(f"  [cyan]剪贴板[/cyan]: {'启用' if config.auto_clipboard else '禁用'}")

    rprint(f"\n[dim]配置文件: ~/.prompt-optimizer/config.json[/dim]\n")


def show_frameworks() -> None:
    """显示所有 Prompt 框架"""
    console.print()
    console.print(Panel(
        "[bold]7 种主流 Prompt 优化框架[/bold]\n"
        "[dim]根据你的 prompt 内容自动推荐最适合的框架[/dim]",
        title="Prompt 框架大全",
        border_style="cyan",
        box=box.ROUNDED,
    ))
    console.print()

    table = Table(
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold magenta",
        row_styles=["dim", "none"],
    )
    table.add_column("框架", style="bold cyan", width=14)
    table.add_column("描述", style="white", width=22)
    table.add_column("适用场景", style="green", width=28)
    table.add_column("推荐度", style="yellow", width=12)

    recommended = get_recommended_framework("")
    for fw, info in PROMPT_FRAMEWORKS.items():
        is_recommended = fw == recommended
        rec_mark = "推荐" if is_recommended else ""
        table.add_row(
            info.name,
            info.description,
            info.recommended_for,
            rec_mark,
        )

    console.print(table)
    console.print("\n[dim] 注：实际推荐会根据你输入的具体 prompt 内容动态调整[/dim]\n")


def show_models(models: List[str], current_model: str) -> None:
    """显示所有已安装的模型"""
    console.print()
    console.print(Panel(
        "[bold]已安装的 Ollama 模型列表[/bold]",
        title="可用模型",
        border_style="cyan",
        box=box.ROUNDED,
    ))
    console.print()

    table = Table(
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold magenta",
    )
    table.add_column("编号", style="cyan", width=8)
    table.add_column("模型名称", style="white", width=35)
    table.add_column("状态", style="green", width=12)

    for i, model in enumerate(models, 1):
        is_current = model == current_model
        status = "[green]当前使用[/green]" if is_current else ""
        table.add_row(str(i), model, status)

    console.print(table)
    console.print(f"\n[dim]当前使用模型：[bold green]{current_model}[/bold green][/dim]\n")


def show_config(config) -> None:
    """显示当前配置"""
    console.print()
    console.print(Panel(
        "[bold]当前系统配置[/bold]",
        title="配置信息",
        border_style="cyan",
        box=box.ROUNDED,
    ))
    console.print()

    table = Table(
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold magenta",
    )
    table.add_column("配置项", style="cyan", width=22)
    table.add_column("值", style="green", width=40)

    provider = config.provider
    provider_name = {
        "ollama": "Ollama (本地)",
        "openai": "OpenAI API",
        "claude": "Claude API",
        "custom": "自定义 API",
    }.get(provider, provider)

    table.add_row("提供商", provider_name)

    if provider == "ollama":
        table.add_row("Ollama 地址", config.ollama_base_url)
        table.add_row("默认模型", config.default_model or "自动选择")
    elif provider == "openai":
        table.add_row("模型", config.openai_model)
        key_status = "已配置" if config.openai_api_key else "未配置"
        table.add_row("API Key", key_status)
    elif provider == "claude":
        table.add_row("模型", config.claude_model)
        key_status = "已配置" if config.claude_api_key else "未配置"
        table.add_row("API Key", key_status)
    elif provider == "custom":
        table.add_row("模型", config.custom_model or "未指定")
        table.add_row("Base URL", config.custom_base_url or "未配置")

    table.add_row("请求超时", f"{config.request_timeout} 秒")
    table.add_row("温度参数", f"{config.temperature}")
    table.add_row("优化维度", ", ".join(config.optimization_dimensions))
    table.add_row("历史记录", "启用" if config.enable_history else "禁用")
    table.add_row("剪贴板", "启用" if config.auto_clipboard else "禁用")
    table.add_row("日志级别", config.log_level)

    console.print(table)
    console.print(f"\n[dim]配置文件: ~/.prompt-optimizer/config.json[/dim]")
    console.print("[dim]使用 /provider 切换提供商[/dim]\n")


def show_optimized_versions(results: List[Dict]) -> None:
    """显示优化版本"""
    if not results:
        console.print("[red]未能生成优化版本[/red]")
        return

    console.print()
    console.print(Panel(
        f"[bold green]优化完成！[/bold green] 共生成 [cyan]{len(results)}[/cyan] 个版本",
        border_style="green",
        box=box.ROUNDED,
    ))
    console.print()

    level_styles = {
        "light": ("[V1]", "green"),
        "moderate": ("[V2]", "cyan"),
        "deep": ("[V3]", "magenta"),
        "framework": ("[FW]", "yellow"),
    }

    for i, version in enumerate(results, 1):
        icon, border_color = level_styles.get(version["level"], ("[OK]", "white"))

        # 版本标题面板
        title_panel = Panel(
            f"[bold]{version['name']}[/bold]\n[dim]{version['description']}[/dim]",
            title=f"{icon} 版本 {i}",
            border_style=border_color,
            box=box.ROUNDED,
        )
        console.print(title_panel)

        # 优化内容面板
        content_panel = Panel(
            Markdown(version['prompt']),
            border_style="green",
            box=box.SIMPLE,
            padding=(1, 2),
        )
        console.print(content_panel)
        console.print()

    # 选择提示
    tip_table = Table(
        show_header=False,
        box=box.SIMPLE,
        padding=(0, 1),
    )
    tip_table.add_column("提示", style="dim")
    tip_table.add_row("[dim]输入版本号 (1/2/3) 复制该版本到剪贴板，或按回车继续。[/dim]")

    console.print(tip_table)


def show_history_items(items: List, limit: int = 10) -> None:
    """显示历史记录列表"""
    if not items:
        console.print()
        console.print(Panel(
            "[dim]暂无历史记录[/dim]",
            title="历史记录",
            border_style="cyan",
            box=box.ROUNDED,
        ))
        return

    console.print()
    console.print(Panel(
        f"[bold]最近 {min(len(items), limit)} 条优化记录[/bold]",
        title="历史记录",
        border_style="cyan",
        box=box.ROUNDED,
    ))
    console.print()

    table = Table(
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold magenta",
    )
    table.add_column("编号", style="cyan", width=6)
    table.add_column("时间", style="white", width=20)
    table.add_column("原始 Prompt", style="green", width=40)
    table.add_column("框架", style="yellow", width=12)

    for i, item in enumerate(items[:limit], 1):
        # 截断显示
        prompt_preview = item.original_prompt[:37] + "..." if len(item.original_prompt) > 40 else item.original_prompt
        time_str = item.timestamp[:19].replace("T", " ") if item.timestamp else ""

        table.add_row(
            str(i),
            time_str,
            prompt_preview,
            item.framework or "-",
        )

    console.print(table)
    console.print(f"\n[dim]共 {len(items)} 条记录[/dim]\n")


def show_history_detail(item) -> None:
    """显示历史记录详情"""
    console.print()
    console.print(Panel(
        f"[bold]记录详情[/bold]\n"
        f"[dim]时间：{item.timestamp}[/dim]\n"
        f"[dim]模型：{item.model or '未知'}[/dim]\n"
        f"[dim]框架：{item.framework or '无'}[/dim]",
        title=f"历史记录 {item.id}",
        border_style="cyan",
        box=box.ROUNDED,
    ))
    console.print()

    # 原始 prompt
    console.print(Panel(
        item.original_prompt,
        title="[blue]原始 Prompt[/blue]",
        border_style="blue",
        box=box.ROUNDED,
    ))

    # 优化版本
    for i, opt in enumerate(item.optimized_prompts, 1):
        console.print(Panel(
            Markdown(opt.get("prompt", "")),
            title=f"[green]优化版本 {i}[/green] - {opt.get('name', '')}",
            border_style="green",
            box=box.ROUNDED,
        ))


def show_framework_selection(framework: PromptFramework) -> None:
    """显示已选择的框架"""
    info = PROMPT_FRAMEWORKS[framework]
    console.print(Panel(
        f"[green]将使用 [bold]{info.name}[/bold] 进行优化[/green]",
        border_style="green",
        box=box.ROUNDED,
    ))
    console.print()


def show_framework_components(framework: PromptFramework) -> None:
    """显示框架组成要素"""
    info = PROMPT_FRAMEWORKS[framework]
    console.print("\n[bold yellow]框架组成要素：[/bold yellow]")
    for comp in info.components:
        console.print(f"  [cyan]•[/cyan] {comp}")


def show_docs_list(docs: List[dict], current_doc: Optional[dict] = None) -> None:
    """显示文档列表

    Args:
        docs: 文档信息列表 [{'name': ..., 'file': ..., 'preview': ...}, ...]
        current_doc: 当前文档信息（可选）
    """
    if not docs:
        console.print()
        console.print(Panel(
            "[dim]prompts/ 目录下暂无需求文档[/dim]\n"
            "[dim]使用 /savedoc <名称> 创建新文档[/dim]",
            title="需求文档",
            border_style="cyan",
            box=box.ROUNDED,
        ))
        return

    console.print()
    console.print(Panel(
        f"[bold]需求文档列表[/bold]\n"
        f"[dim]共 {len(docs)} 个文档[/dim]",
        border_style="cyan",
        box=box.ROUNDED,
    ))
    console.print()

    table = Table(
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold magenta",
    )
    table.add_column("编号", style="cyan", width=6)
    table.add_column("文件名", style="green", width=20)
    table.add_column("名称", style="white", width=25)
    table.add_column("简介预览", style="dim", width=30)
    table.add_column("状态", style="yellow", width=10)

    current_file = current_doc.get('file') if current_doc else None

    for i, doc in enumerate(docs, 1):
        is_current = doc.get('file') == current_file
        status = "[green]当前[/green]" if is_current else ""
        table.add_row(
            str(i),
            doc.get('file', ''),
            doc.get('name', ''),
            doc.get('preview', '')[:30],
            status,
        )

    console.print(table)
    console.print("\n[dim]使用 /load <编号或文件名> 加载文档[/dim]")
    console.print("[dim]使用 /doc 查看当前文档详情[/dim]\n")


def show_doc_detail(doc) -> None:
    """显示文档详情

    Args:
        doc: RequirementDoc 对象
    """
    from src.requirement import RequirementDoc

    if not doc:
        console.print()
        console.print(Panel(
            "[dim]未加载任何需求文档[/dim]\n"
            "[dim]使用 /docs 查看可用文档[/dim]",
            title="当前文档",
            border_style="cyan",
            box=box.ROUNDED,
        ))
        return

    console.print()
    console.print(Panel(
        f"[bold]{doc.name}[/bold]\n"
        f"[dim]文件: {doc.file_path}[/dim]",
        title="需求文档",
        border_style="green",
        box=box.ROUNDED,
    ))
    console.print()

    # 背景介绍
    if doc.intro:
        console.print(Panel(
            doc.intro,
            title="[cyan]背景介绍[/cyan]",
            border_style="cyan",
            box=box.ROUNDED,
        ))

    # 调优要求
    if doc.tune:
        console.print(Panel(
            doc.tune,
            title="[yellow]调优要求[/yellow]",
            border_style="yellow",
            box=box.ROUNDED,
        ))

    console.print("\n[dim]优化 Prompt 时将自动整合此文档内容[/dim]\n")