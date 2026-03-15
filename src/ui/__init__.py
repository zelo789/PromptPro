"""
UI 模块

提供 CLI 界面的所有 UI 组件。
"""
from src.ui.console import console
from src.ui.panels import (
    print_banner,
    print_help,
    print_error,
    print_success,
    print_warning,
    print_info,
    print_prompt_panel,
    print_analysis,
    print_framework_recommendation,
    print_divergent_questions,
    print_versions_prompt,
    print_welcome_guide,
    print_first_run_tips,
)
from src.ui.tables import (
    create_choice_table,
    create_data_table,
    show_frameworks,
    show_frameworks_table,
    show_models,
    show_config,
    show_config_table,
    show_optimized_versions,
    show_history_items,
    show_history_detail,
    show_framework_selection,
    show_framework_components,
)

__all__ = [
    # Console
    "console",
    # Panels
    "print_banner",
    "print_help",
    "print_error",
    "print_success",
    "print_warning",
    "print_info",
    "print_prompt_panel",
    "print_analysis",
    "print_framework_recommendation",
    "print_divergent_questions",
    "print_versions_prompt",
    "print_welcome_guide",
    "print_first_run_tips",
    # Tables
    "create_choice_table",
    "create_data_table",
    "show_frameworks",
    "show_frameworks_table",
    "show_models",
    "show_config",
    "show_config_table",
    "show_optimized_versions",
    "show_history_items",
    "show_history_detail",
    "show_framework_selection",
    "show_framework_components",
]