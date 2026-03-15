"""
Console 基础模块

提供 Rich Console 封装和基础组件。
"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich import box

# 全局 Rich Console 对象
console = Console(force_terminal=True, force_jupyter=False)