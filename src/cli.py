"""
CLI 入口模块 - PromptPro 的用户交互界面

提供 Claude Code 风格的单行输入交互界面，支持斜杠命令。
"""
from typing import Optional, List
from pathlib import Path
import sys
import re

from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
from rich.panel import Panel
from rich import box

# Windows 编码修复（延迟执行）
_encoding_fixed = False


def _fix_windows_encoding() -> None:
    """修复 Windows 控制台编码"""
    global _encoding_fixed
    if _encoding_fixed:
        return

    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        _encoding_fixed = True


from src.config import Config, global_config
from src.ollama_client import LLMClient
from src.optimizer import PromptOptimizer
from src.history import global_history
from src.strategies import (
    PromptFramework,
    LEVEL_CONFIGS,
    OptimizationLevel,
    PROMPT_FRAMEWORKS,
    get_recommended_framework,
    get_framework_match_reason,
)
from src.logger import setup_logging, get_logger
from src.exceptions import PromptProError
from src.requirement import get_requirement_manager, RequirementDoc
from src.app import PromptOptimizationRequest, PromptOptimizationService

from src.ui import (
    console,
    print_error,
    print_success,
    print_warning,
    print_info,
    print_prompt_panel,
    print_analysis,
)
from src.ui.tables import show_optimized_versions, show_framework_selection, show_docs_list, show_doc_detail
from src.clipboard import copy_to_clipboard

logger = get_logger("cli")


# ==================== 发散问题生成 ====================

CLARIFYING_QUESTIONS_PROMPT = """你是一个专业的需求分析专家。分析用户的原始 prompt，生成 3-5 个帮助澄清需求的问题。

要求：
1. 问题要具体、有针对性
2. 帮助用户明确目标、受众、格式等关键信息
3. 每个问题一行，不要编号
4. 只输出问题，不要其他解释

用户的原始 prompt：
{prompt}
"""


def generate_clarifying_questions(prompt: str, client) -> List[str]:
    """生成澄清问题"""
    messages = [
        {"role": "user", "content": CLARIFYING_QUESTIONS_PROMPT.format(prompt=prompt)}
    ]

    try:
        response = client.chat(messages)
        # 解析问题列表
        questions = []
        for line in response.strip().split('\n'):
            line = line.strip()
            # 移除可能的编号
            if line and not line.startswith('#'):
                # 移除数字编号如 "1. "、"1) "、"1、"
                cleaned = re.sub(r'^\d+[.、)]\s*', '', line)
                if cleaned:
                    questions.append(cleaned)
        return questions[:5]  # 最多5个问题
    except Exception as e:
        logger.error(f"生成澄清问题失败: {e}")
        return []


def ask_clarifying_questions(prompt: str, client) -> str:
    """询问澄清问题并返回增强后的 prompt"""
    # 检查 prompt 长度，太短的 prompt 不需要澄清
    # 中文每个字符都算，所以阈值设小一点
    if len(prompt) < 5:
        logger.debug(f"Prompt too short ({len(prompt)} chars), skipping clarifying questions")
        return prompt

    # 生成问题
    logger.info("正在分析需求...")
    rprint("[dim]正在分析需求...[/dim]")
    questions = generate_clarifying_questions(prompt, client)

    logger.debug(f"生成了 {len(questions)} 个澄清问题")

    if not questions:
        logger.debug("没有生成问题，使用原始 prompt")
        return prompt

    # 显示问题
    console.print()
    console.print(Panel(
        "[bold]为了更好地优化，请回答以下问题：[/bold]\n"
        "[dim]（按回车跳过，输入 'skip' 跳过所有）[/dim]",
        title="需求澄清",
        border_style="cyan",
        box=box.ROUNDED,
    ))
    console.print()

    answers = []
    for i, question in enumerate(questions, 1):
        console.print(f"  [cyan][bold]{i}[/bold][/cyan] {question}")
        answer = Prompt.ask(f"  [dim]回答[/dim]", default="")

        if answer.lower() == 'skip':
            break
        if answer.strip():
            answers.append(f"Q: {question}\nA: {answer.strip()}")

        console.print()

    if not answers:
        return prompt

    # 整合答案到 prompt
    enhanced_prompt = f"""原始需求：
{prompt}

补充信息：
{chr(10).join(answers)}
"""
    return enhanced_prompt


# ==================== 斜杠命令处理 ====================

def show_help() -> None:
    """显示帮助信息"""
    from rich.table import Table
    from rich.panel import Panel
    from rich import box

    # 标题
    title = Panel(
        "[bold]PromptPro 命令帮助[/bold]",
        border_style="cyan",
        box=box.DOUBLE,
    )
    console.print()
    console.print(title)
    console.print()

    # 核心命令
    rprint("[bold cyan]  核心命令[/bold cyan]")
    core = Table(show_header=False, box=None, padding=(0, 4))
    core.add_column("cmd", style="green", width=16)
    core.add_column("desc", style="white")
    core.add_row("/help, /h", "显示帮助信息")
    core.add_row("/quit, /q", "退出程序")
    console.print(core)
    console.print()

    # 模型与提供商
    rprint("[bold cyan]  模型与提供商[/bold cyan]")
    model = Table(show_header=False, box=None, padding=(0, 4))
    model.add_column("cmd", style="green", width=16)
    model.add_column("desc", style="white")
    model.add_row("/model, /m", "查看和切换模型")
    model.add_row("/provider, /p", "切换 API 提供商 (ollama/openai/claude/custom)")
    model.add_row("/temp <值>", "设置温度参数 (0.0-2.0)")
    console.print(model)
    console.print()

    # 框架与优化
    rprint("[bold cyan]  框架与优化[/bold cyan]")
    fw = Table(show_header=False, box=None, padding=(0, 4))
    fw.add_column("cmd", style="green", width=16)
    fw.add_column("desc", style="white")
    fw.add_row("/frameworks, /f", "查看 7 种 Prompt 框架")
    fw.add_row("/history", "查看优化历史")
    fw.add_row("/clarify", "切换问答式需求确认 (开/关)")
    console.print(fw)
    console.print()

    # 需求文档
    rprint("[bold cyan]  需求文档[/bold cyan]")
    req = Table(show_header=False, box=None, padding=(0, 4))
    req.add_column("cmd", style="green", width=16)
    req.add_column("desc", style="white")
    req.add_row("/docs, /d", "列出所有需求文档")
    req.add_row("/load, /l <名称>", "加载指定文档")
    req.add_row("/doc", "显示当前文档")
    req.add_row("/savedoc <名称>", "创建新文档")
    req.add_row("/cleardoc", "清除当前文档")
    console.print(req)
    console.print()

    # 配置
    rprint("[bold cyan]  配置[/bold cyan]")
    cfg = Table(show_header=False, box=None, padding=(0, 4))
    cfg.add_column("cmd", style="green", width=16)
    cfg.add_column("desc", style="white")
    cfg.add_row("/config", "显示当前配置")
    console.print(cfg)
    console.print()

    # 快捷方式面板
    shortcuts = Panel(
        "[bold]快捷方式[/bold]\n\n"
        "  直接输入数字 → 快速切换模型 (如: 1, 2, 3)\n"
        "  直接输入文本 → 自动优化 Prompt\n"
        "  Ctrl+C      → 退出程序",
        border_style="cyan",
        box=box.ROUNDED,
    )
    console.print(shortcuts)
    console.print()


def show_models(client) -> None:
    """显示可用模型"""
    models = client.get_available_models()
    current = client.get_current_model()

    rprint("\n[bold]可用模型[/bold]\n")

    for i, model in enumerate(models, 1):
        marker = " [cyan]← 当前[/cyan]" if model == current else ""
        rprint(f"  [green]{i}[/green]. {model}{marker}")

    rprint(f"\n[dim]直接输入数字切换模型，或使用 /model <名称>[/dim]\n")


def show_providers() -> None:
    """显示支持的提供商"""
    current = global_config.provider

    rprint("\n[bold]API 提供商[/bold]\n")

    providers = [
        ("ollama", "Ollama 本地", "http://localhost:11434"),
        ("openai", "OpenAI API", "https://api.openai.com/v1"),
        ("claude", "Claude API", "https://api.anthropic.com"),
        ("custom", "自定义 API", "自定义 OpenAI 兼容 API"),
    ]

    for name, desc, url in providers:
        marker = " [cyan]<- 当前[/cyan]" if name == current else ""
        status = ""
        if name == "openai":
            status = " [green]已配置[/green]" if global_config.openai_api_key else " [red]未配置 API Key[/red]"
        elif name == "claude":
            status = " [green]已配置[/green]" if global_config.claude_api_key else " [red]未配置 API Key[/red]"
        elif name == "custom":
            status = " [green]已配置[/green]" if global_config.custom_base_url else " [red]未配置[/red]"

        rprint(f"  [green]{name}[/green] - {desc}{marker}")
        rprint(f"       [dim]{url}[/dim]{status}")

    rprint(f"\n[dim]使用 /provider <名称> 切换提供商[/dim]")
    rprint("[dim]配置文件: ~/.prompt-optimizer/config.json[/dim]\n")


def switch_provider(args: str) -> None:
    """切换提供商"""
    if not args:
        show_providers()
        return

    valid_providers = ["ollama", "openai", "claude", "custom"]
    provider = args.lower()

    if provider not in valid_providers:
        print_error(f"无效的提供商: {args}")
        rprint(f"[dim]支持的提供商: {', '.join(valid_providers)}[/dim]")
        return

    # 检查配置
    if provider == "openai" and not global_config.openai_api_key:
        print_warning("OpenAI API Key 未配置")
        rprint("[dim]请编辑配置文件设置 openai_api_key[/dim]")
    elif provider == "claude" and not global_config.claude_api_key:
        print_warning("Claude API Key 未配置")
        rprint("[dim]请编辑配置文件设置 claude_api_key[/dim]")
    elif provider == "custom" and not global_config.custom_base_url:
        print_warning("自定义 API Base URL 未配置")
        rprint("[dim]请编辑配置文件设置 custom_base_url[/dim]")

    global_config.update(provider=provider)
    print_success(f"已切换到: [bold]{provider}[/bold]")
    rprint("[dim]重启 PromptPro 以使用新的提供商[/dim]")


def switch_model(args: str, client) -> None:
    """切换模型"""
    if not args:
        show_models(client)
        return

    models = client.get_available_models()

    if args.isdigit():
        idx = int(args) - 1
        if 0 <= idx < len(models):
            model = models[idx]
        else:
            print_error(f"无效的编号: {args}")
            return
    elif args in models:
        model = args
    else:
        # 允许直接输入模型名称（对于远程 API）
        model = args

    client.set_model(model)

    # 更新配置中的模型
    provider = global_config.provider
    if provider == "ollama":
        global_config.update(default_model=model)
    elif provider == "openai":
        global_config.update(openai_model=model)
    elif provider == "claude":
        global_config.update(claude_model=model)
    elif provider == "custom":
        global_config.update(custom_model=model)

    print_success(f"已切换到模型: [bold]{model}[/bold]")


def show_frameworks() -> None:
    """显示所有框架"""
    from src.ui.tables import show_frameworks_table
    show_frameworks_table()


def show_history() -> None:
    """显示历史记录"""
    items = global_history.get_all(limit=10)

    if not items:
        rprint("\n[dim]暂无历史记录[/dim]\n")
        return

    rprint("\n[bold]最近优化记录[/bold]\n")

    for i, item in enumerate(items, 1):
        preview = item.original_prompt[:40] + "..." if len(item.original_prompt) > 40 else item.original_prompt
        framework = f"[yellow]{item.framework}[/yellow]" if item.framework else "[dim]-[/dim]"
        rprint(f"  [green]{i}[/green]. {preview} {framework}")

    rprint(f"\n[dim]共 {len(items)} 条记录[/dim]\n")


def set_temperature(args: str, client) -> None:
    """设置温度"""
    if not args:
        rprint(f"\n当前温度: [yellow]{client.temperature}[/yellow]")
        rprint("[dim]用法: /temp <0.0-2.0>[/dim]\n")
        return

    try:
        temp = float(args)
        if 0.0 <= temp <= 2.0:
            client.set_temperature(temp)
            global_config.update(temperature=temp)
            print_success(f"温度已设置为: [bold]{temp}[/bold]")
        else:
            print_error("温度范围: 0.0 - 2.0")
    except ValueError:
        print_error(f"无效的温度值: {args}")


def show_config() -> None:
    """显示配置"""
    from src.ui.tables import show_config_table

    rprint("\n[bold]当前配置[/bold]\n")

    provider = global_config.provider
    provider_name = {
        "ollama": "Ollama (本地)",
        "openai": "OpenAI API",
        "claude": "Claude API",
        "custom": "自定义 API",
    }.get(provider, provider)

    rprint(f"  [cyan]提供商[/cyan]: {provider_name}")

    if provider == "ollama":
        rprint(f"  [cyan]模型[/cyan]: {global_config.default_model or '自动选择'}")
        rprint(f"  [cyan]Ollama 地址[/cyan]: {global_config.ollama_base_url}")
    elif provider == "openai":
        rprint(f"  [cyan]模型[/cyan]: {global_config.openai_model}")
        key_status = "已配置" if global_config.openai_api_key else "[red]未配置[/red]"
        rprint(f"  [cyan]API Key[/cyan]: {key_status}")
    elif provider == "claude":
        rprint(f"  [cyan]模型[/cyan]: {global_config.claude_model}")
        key_status = "已配置" if global_config.claude_api_key else "[red]未配置[/red]"
        rprint(f"  [cyan]API Key[/cyan]: {key_status}")
    elif provider == "custom":
        rprint(f"  [cyan]模型[/cyan]: {global_config.custom_model or '未指定'}")
        rprint(f"  [cyan]Base URL[/cyan]: {global_config.custom_base_url or '未配置'}")

    rprint(f"  [cyan]温度[/cyan]: {global_config.temperature}")
    rprint(f"  [cyan]历史记录[/cyan]: {'启用' if global_config.enable_history else '禁用'}")
    rprint(f"  [cyan]剪贴板[/cyan]: {'启用' if global_config.auto_clipboard else '禁用'}")
    rprint(f"  [cyan]问答确认[/cyan]: {'启用' if global_config.enable_clarifying_questions else '禁用'}")

    rprint(f"\n[dim]配置文件: ~/.prompt-optimizer/config.json[/dim]")
    rprint("[dim]使用 /provider 切换提供商[/dim]\n")


def toggle_clarify() -> None:
    """切换问答式需求确认功能"""
    current = global_config.enable_clarifying_questions
    new_value = not current
    global_config.update(enable_clarifying_questions=new_value)

    status = "已启用" if new_value else "已禁用"
    print_success(f"问答式需求确认: [bold]{status}[/bold]")


# ==================== 需求文档命令 ====================

def show_docs() -> None:
    """列出所有需求文档"""
    manager = get_requirement_manager()
    docs = manager.list_docs()

    # 获取当前文档
    current_doc = manager.get_current_doc()
    current_info = None
    if current_doc:
        current_info = {
            'name': current_doc.name,
            'file': Path(current_doc.file_path).stem,
        }

    show_docs_list(docs, current_info)


def load_requirement_doc(args: str) -> None:
    """加载指定文档"""
    if not args:
        print_error("请指定文档编号或文件名")
        rprint("[dim]用法: /load <编号或文件名>[/dim]")
        rprint("[dim]使用 /docs 查看可用文档[/dim]\n")
        return

    manager = get_requirement_manager()

    # 判断是否为编号
    if args.isdigit():
        docs = manager.list_docs()
        idx = int(args) - 1
        if 0 <= idx < len(docs):
            file_identifier = docs[idx]['file']
        else:
            print_error(f"无效编号: {args} (可用 1-{len(docs)})")
            return
    else:
        file_identifier = args

    try:
        doc = manager.select_doc(file_identifier)
        print_success(f"已加载: [bold]{doc.name}[/bold]")
        rprint(f"[dim]优化 Prompt 时将整合此文档内容[/dim]\n")
    except Exception as e:
        print_error(f"加载失败: {e}")


def show_current_doc() -> None:
    """显示当前文档"""
    manager = get_requirement_manager()
    doc = manager.get_current_doc()
    show_doc_detail(doc)


def clear_current_doc() -> None:
    """清除当前文档"""
    manager = get_requirement_manager()
    manager.clear_current_doc()
    print_success("已清除当前需求文档")


def save_requirement_doc(args: str) -> None:
    """创建新文档"""
    if not args:
        print_error("请指定文档名称")
        rprint("[dim]用法: /savedoc <名称>[/dim]\n")
        return

    # 询问文档内容
    console.print()
    console.print(Panel(
        "[bold]创建需求文档[/bold]\n"
        f"[dim]名称: {args}[/dim]",
        border_style="cyan",
        box=box.ROUNDED,
    ))
    console.print()

    intro = Prompt.ask("  [cyan]背景介绍[/cyan]", default="")
    tune = Prompt.ask("  [cyan]调优要求[/cyan]", default="")

    if not intro and not tune:
        print_warning("内容为空，已取消创建")
        return

    try:
        manager = get_requirement_manager()
        file_path = manager.create_doc(
            name=args,
            intro=intro,
            tune=tune,
        )
        print_success(f"文档已创建: {file_path}")
        rprint("[dim]使用 /load 加载此文档[/dim]\n")
    except Exception as e:
        print_error(f"创建失败: {e}")


# ==================== 核心功能 ====================

def generate_optimized_versions(
    prompt: str,
    client,
    num_versions: int = 3,
    framework: Optional[PromptFramework] = None,
) -> List[dict]:
    """生成优化版本"""
    results = []
    levels = list(OptimizationLevel)
    level_names = {
        OptimizationLevel.LIGHT: "轻度优化",
        OptimizationLevel.MODERATE: "中度优化",
        OptimizationLevel.DEEP: "深度优化",
    }

    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[progress.description]{task.description}", style="cyan"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]正在优化...[/cyan]", total=num_versions)

        for level in levels[:num_versions]:
            config = LEVEL_CONFIGS[level]

            messages = [
                {"role": "system", "content": config["system_prompt"]},
                {"role": "user", "content": f"请优化以下 prompt:\n\n{prompt}"}
            ]

            try:
                optimized = client.chat(messages)
                results.append({
                    "level": level.value,
                    "name": level_names[level],
                    "description": config["description"],
                    "prompt": optimized,
                })
            except Exception as e:
                logger.error(f"生成 {level_names[level]} 版本失败：{e}")

            progress.advance(task)

    if framework:
        fw_info = PROMPT_FRAMEWORKS[framework]
        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[cyan]{task.description}[/cyan]"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"[cyan]生成 {fw_info.name} 版本...[/cyan]")

            messages = [
                {"role": "system", "content": fw_info.system_prompt},
                {"role": "user", "content": f"请优化以下 prompt:\n\n{prompt}"}
            ]

            try:
                optimized = client.chat(messages)
                results.append({
                    "level": "framework",
                    "name": fw_info.name,
                    "description": fw_info.description,
                    "prompt": optimized,
                })
            except Exception as e:
                logger.error(f"生成框架版本失败：{e}")

    return results


def optimize_prompt(prompt: str, client) -> None:
    """优化 Prompt"""
    manager = get_requirement_manager()
    current_doc = manager.get_current_doc()
    service = PromptOptimizationService(client=client, history_manager=global_history)
    prompt_with_doc = service.build_effective_prompt(prompt, requirement_doc=current_doc)

    if global_config.enable_clarifying_questions:
        enhanced_prompt = ask_clarifying_questions(prompt_with_doc, client)
    else:
        enhanced_prompt = prompt_with_doc

    result = service.optimize(
        PromptOptimizationRequest(
            original_prompt=prompt,
            num_versions=3,
            requirement_doc=current_doc,
            clarified_prompt=enhanced_prompt,
        )
    )
    fw_info = PROMPT_FRAMEWORKS[result.framework]

    rprint(f"\n[dim]推荐框架: [cyan]{fw_info.name}[/cyan] ({result.framework_reason})[/dim]\n")
    results = result.optimized_prompts

    if not results:
        print_error("优化失败，请重试")
        return

    # 显示结果
    show_optimized_versions(results)

    if global_config.enable_history:
        service.save_history(result)

    # 选择复制
    choice = Prompt.ask("\n[cyan]输入版本号复制[/cyan] [dim](1-4)[/dim]", default="")

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(results):
            copy_to_clipboard(results[idx]["prompt"])
            print_success("已复制到剪贴板")


# ==================== 主循环 ====================

def interactive_mode() -> None:
    """交互模式主循环 - Claude Code 风格"""
    _fix_windows_encoding()

    # 简洁的欢迎信息
    rprint("""
[bold cyan]PromptPro[/bold cyan] [dim]v0.4.0[/dim] - 让 Prompt 更懂 AI
[dim]输入 /help 查看命令，或直接输入文本开始优化[/dim]
""")

    # 连接 LLM
    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[cyan]{task.description}[/cyan]"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("连接 LLM 服务...")

        client = LLMClient(global_config)

        if not client.check_connection():
            provider = global_config.provider
            if provider == "ollama":
                print_error("无法连接 Ollama 服务\n[dim]请确保 Ollama 正在运行: ollama serve[/dim]")
            elif provider == "openai":
                print_error("OpenAI API 连接失败\n[dim]请检查 API Key 配置[/dim]")
            elif provider == "claude":
                print_error("Claude API 连接失败\n[dim]请检查 API Key 配置[/dim]")
            else:
                print_error("无法连接 API 服务\n[dim]请检查配置[/dim]")
            return

        try:
            if global_config.provider == "ollama":
                models = client.list_models()
                if not models:
                    print_error("未找到已安装的模型\n[dim]请先下载模型: ollama pull llama3[/dim]")
                    return

                # 选择模型
                configured = global_config.default_model
                if configured and configured in models:
                    client.set_model(configured)
                else:
                    client.set_model(models[0])
            else:
                # 远程 API，使用配置的模型
                model = client.get_current_model()
                if not model:
                    # 使用默认模型
                    default_models = {
                        "openai": "gpt-4o-mini",
                        "claude": "claude-3-5-sonnet-20241022",
                        "custom": "default",
                    }
                    client.set_model(default_models.get(global_config.provider, "default"))

        except Exception as e:
            print_error(f"连接失败: {e}")
            return

    provider_name = {
        "ollama": "Ollama",
        "openai": "OpenAI",
        "claude": "Claude",
        "custom": "Custom",
    }.get(global_config.provider, global_config.provider)

    rprint(f"[dim]提供商: [green]{provider_name}[/green] | 模型: [green]{client.get_current_model()}[/green][/dim]\n")

    # 主循环
    while True:
        try:
            user_input = Prompt.ask("[bold green]>[/bold green]").strip()

            if not user_input:
                continue

            # 处理斜杠命令
            if user_input.startswith('/'):
                handle_slash_command(user_input, client)
                continue

            # 处理纯数字输入 - 快捷切换模型
            if user_input.isdigit():
                models = client.get_available_models()
                idx = int(user_input) - 1
                if 0 <= idx < len(models):
                    model = models[idx]
                    client.set_model(model)
                    # 更新配置
                    provider = global_config.provider
                    if provider == "ollama":
                        global_config.update(default_model=model)
                    elif provider == "openai":
                        global_config.update(openai_model=model)
                    elif provider == "claude":
                        global_config.update(claude_model=model)
                    elif provider == "custom":
                        global_config.update(custom_model=model)
                    print_success(f"已切换到: [bold]{model}[/bold]")
                else:
                    print_error(f"无效编号: {user_input} (可用 1-{len(models)})")
                continue

            # 处理 Prompt 优化
            optimize_prompt(user_input, client)

        except KeyboardInterrupt:
            rprint("\n[dim]再见！[/dim]")
            break
        except PromptProError as e:
            print_error(str(e))
        except Exception as e:
            logger.exception("错误")
            print_error(f"错误: {e}")


def handle_slash_command(input_str: str, client) -> None:
    """处理斜杠命令"""
    parts = input_str[1:].split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    commands = {
        'help': lambda: show_help(),
        'h': lambda: show_help(),
        'model': lambda: switch_model(args, client),
        'm': lambda: switch_model(args, client),
        'provider': lambda: switch_provider(args),
        'p': lambda: switch_provider(args),
        'frameworks': lambda: show_frameworks(),
        'f': lambda: show_frameworks(),
        'config': lambda: show_config(),
        'history': lambda: show_history(),
        'temp': lambda: set_temperature(args, client),
        'clarify': lambda: toggle_clarify(),
        # 需求文档命令
        'docs': lambda: show_docs(),
        'd': lambda: show_docs(),
        'load': lambda: load_requirement_doc(args),
        'l': lambda: load_requirement_doc(args),
        'doc': lambda: show_current_doc(),
        'savedoc': lambda: save_requirement_doc(args),
        'cleardoc': lambda: clear_current_doc(),
        # 退出
        'quit': lambda: sys.exit(0),
        'q': lambda: sys.exit(0),
        'exit': lambda: sys.exit(0),
    }

    if cmd in commands:
        commands[cmd]()
    else:
        print_error(f"未知命令: /{cmd}\n[dim]输入 /help 查看可用命令[/dim]")


# ==================== 快速模式 ====================

def quick_optimize(
    prompt: str,
    model: Optional[str] = None,
    level: int = 3,
    framework: Optional[str] = None,
    output: Optional[str] = None,
) -> None:
    """快速优化模式"""
    _fix_windows_encoding()

    rprint("[bold cyan]PromptPro[/bold cyan] [dim]v0.4.0[/dim]\n")

    # 连接
    client = LLMClient(global_config)

    if not client.check_connection():
        print_error("无法连接 LLM 服务")
        return

    if global_config.provider == "ollama":
        models = client.list_models()
        if not models:
            print_error("未找到已安装的模型")
            return

        if model and model in models:
            client.set_model(model)
        else:
            client.set_model(models[0])
    else:
        if model:
            client.set_model(model)

    provider_name = {
        "ollama": "Ollama",
        "openai": "OpenAI",
        "claude": "Claude",
        "custom": "Custom",
    }.get(global_config.provider, global_config.provider)

    rprint(f"[dim]提供商: [green]{provider_name}[/green] | 模型: [green]{client.get_current_model()}[/green][/dim]\n")

    service = PromptOptimizationService(client=client, history_manager=global_history)

    if framework:
        try:
            fw = PromptFramework(framework.lower())
        except ValueError:
            fw = get_recommended_framework(prompt)
    else:
        fw = get_recommended_framework(prompt)

    reason = get_framework_match_reason(prompt, fw)
    rprint(f"[dim]框架: [cyan]{PROMPT_FRAMEWORKS[fw].name}[/cyan] ({reason})[/dim]\n")

    result = service.optimize(
        PromptOptimizationRequest(
            original_prompt=prompt,
            num_versions=level,
            selected_framework=fw,
        )
    )
    results = result.optimized_prompts

    if results:
        show_optimized_versions(results)

        if global_config.enable_history:
            service.save_history(result)

        # 输出到文件
        if output:
            try:
                with open(output, "w", encoding="utf-8") as f:
                    for i, r in enumerate(results, 1):
                        f.write(f"=== 版本 {i}: {r['name']} ===\n\n{r['prompt']}\n\n")
                print_success(f"已保存到: {output}")
            except Exception as e:
                print_error(f"保存失败: {e}")


# ==================== 入口 ====================

def run() -> None:
    """CLI 入口"""
    setup_logging()
    _fix_windows_encoding()

    import argparse

    parser = argparse.ArgumentParser(
        description="PromptPro - 让 Prompt 更懂 AI"
    )
    parser.add_argument("prompt", nargs="?", help="要优化的 prompt")
    parser.add_argument("-m", "--model", help="指定模型")
    parser.add_argument("-l", "--level", type=int, default=3, choices=[1, 2, 3])
    parser.add_argument("-f", "--framework", help="指定框架")
    parser.add_argument("-o", "--output", help="输出到文件")
    parser.add_argument("--models", action="store_true", help="列出模型")
    parser.add_argument("--config", action="store_true", help="显示配置")
    parser.add_argument("--history", action="store_true", help="查看历史")

    args = parser.parse_args()

    # 子命令
    if args.models:
        client = LLMClient()
        if client.check_connection():
            show_models(client)
        else:
            print_error("无法连接 LLM 服务")
        return

    if args.config:
        show_config()
        return

    if args.history:
        show_history()
        return

    # 主功能
    if args.prompt:
        quick_optimize(args.prompt, args.model, args.level, args.framework, args.output)
    else:
        interactive_mode()


if __name__ == "__main__":
    run()
