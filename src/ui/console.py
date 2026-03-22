"""Shared Rich console instance."""

from rich.console import Console

console = Console(force_terminal=True, force_jupyter=False)
