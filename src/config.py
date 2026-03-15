"""
配置管理模块

提供全局配置管理功能，支持多种 LLM API 提供商。
配置文件位置：~/.prompt-optimizer/config.json
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, ClassVar
import json
import os
from pathlib import Path
import shutil

from src.logger import get_logger
from src.exceptions import ConfigError

logger = get_logger("config")

# 配置版本号，用于迁移
CONFIG_VERSION = 3


@dataclass
class Config:
    """
    PromptPro 配置类

    支持多种 LLM API 提供商：Ollama、OpenAI、Claude、自定义 OpenAI 兼容 API
    """

    # 版本号
    version: int = CONFIG_VERSION

    # 当前使用的提供商: ollama, openai, claude, custom
    provider: str = "ollama"

    # Ollama 配置
    ollama_base_url: str = "http://localhost:11434"

    # OpenAI 配置
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    # Claude 配置
    claude_api_key: str = ""
    claude_base_url: str = "https://api.anthropic.com"
    claude_model: str = "claude-3-5-sonnet-20241022"

    # 自定义 API 配置 (OpenAI 兼容格式)
    custom_api_key: str = ""
    custom_base_url: str = ""
    custom_model: str = ""

    # 默认模型 (向后兼容)
    default_model: str = ""

    # 模型参数
    temperature: float = 0.7
    request_timeout: int = 300
    max_retries: int = 3
    retry_delay: float = 1.0

    # 优化配置
    optimization_dimensions: List[str] = field(default_factory=lambda: [
        "structure", "clarity", "context", "constraints", "examples",
    ])
    num_versions: int = 3

    # 历史记录配置
    enable_history: bool = True
    max_history_items: int = 100

    # 剪贴板配置
    auto_clipboard: bool = True

    # 日志配置
    log_level: str = "INFO"

    # 路径配置
    config_dir: str = field(default_factory=lambda: str(Path.home() / ".prompt-optimizer"))

    # 验证规则
    _validators: ClassVar[Dict[str, Any]] = {
        "temperature": {"min": 0.0, "max": 2.0},
        "max_retries": {"min": 0, "max": 10},
        "retry_delay": {"min": 0.0, "max": 30.0},
        "num_versions": {"min": 1, "max": 5},
        "max_history_items": {"min": 0, "max": 1000},
        "request_timeout": {"min": 10, "max": 3600},
        "log_level": {"choices": ["DEBUG", "INFO", "WARNING", "ERROR"]},
        "provider": {"choices": ["ollama", "openai", "claude", "custom"]},
    }

    def __post_init__(self) -> None:
        os.makedirs(self.config_dir, exist_ok=True)

    @property
    def config_file(self) -> str:
        return os.path.join(self.config_dir, "config.json")

    @property
    def history_file(self) -> str:
        return os.path.join(self.config_dir, "history.json")

    def validate(self) -> List[str]:
        errors = []

        for field_name, rules in self._validators.items():
            value = getattr(self, field_name, None)
            if value is None:
                continue

            if "min" in rules and "max" in rules:
                if not (rules["min"] <= value <= rules["max"]):
                    errors.append(f"{field_name} 必须在 {rules['min']} 到 {rules['max']} 之间")
            elif "choices" in rules:
                if value not in rules["choices"]:
                    errors.append(f"{field_name} 必须是 {rules['choices']} 之一")

        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    def save(self) -> None:
        if os.path.exists(self.config_file):
            backup_file = self.config_file + ".bak"
            try:
                shutil.copy2(self.config_file, backup_file)
            except OSError as e:
                logger.warning(f"备份配置文件失败：{e}")

        config_data = asdict(self)
        # 敏感信息脱敏（日志中不显示）
        safe_data = {**config_data}
        for key in ['openai_api_key', 'claude_api_key', 'custom_api_key']:
            if safe_data.get(key):
                safe_data[key] = '***'

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            logger.info(f"配置已保存到：{self.config_file}")
        except OSError as e:
            logger.error(f"保存配置文件失败：{e}")
            raise ConfigError(f"保存配置文件失败：{e}")

    @classmethod
    def load(cls) -> "Config":
        config_file = str(Path.home() / ".prompt-optimizer" / "config.json")

        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)

                config_data = cls._migrate_config(config_data)
                logger.info(f"配置已加载：{config_file}")
                return cls(**config_data)

            except json.JSONDecodeError as e:
                logger.error(f"配置文件解析失败：{e}")
                raise ConfigError(f"配置文件解析失败：{e}")
            except TypeError as e:
                logger.error(f"配置文件内容无效：{e}")
                raise ConfigError(f"配置文件内容无效：{e}")

        logger.debug("配置文件不存在，使用默认配置")
        return cls()

    @classmethod
    def _migrate_config(cls, config_data: Dict[str, Any]) -> Dict[str, Any]:
        version = config_data.get("version", 1)

        valid_fields = {name for name in cls.__dataclass_fields__}

        # v2 -> v3: 添加多 API 提供商支持
        if version < 3:
            logger.info("正在迁移配置从 v2 到 v3...")
            config_data["provider"] = "ollama"
            config_data["openai_api_key"] = ""
            config_data["openai_base_url"] = "https://api.openai.com/v1"
            config_data["openai_model"] = "gpt-4o-mini"
            config_data["claude_api_key"] = ""
            config_data["claude_base_url"] = "https://api.anthropic.com"
            config_data["claude_model"] = "claude-3-5-sonnet-20241022"
            config_data["custom_api_key"] = ""
            config_data["custom_base_url"] = ""
            config_data["custom_model"] = ""
            config_data["version"] = CONFIG_VERSION

        # v1 -> v2
        if version < 2:
            for field_name in valid_fields:
                if field_name not in config_data:
                    field_info = cls.__dataclass_fields__[field_name]
                    default_value = field_info.default
                    if default_value is not None and callable(default_value):
                        default_value = field_info.default_factory()
                    config_data[field_name] = default_value
            config_data["version"] = 2

        # 过滤无效字段
        return {k: v for k, v in config_data.items() if k in valid_fields}

    def update(self, **kwargs: Any) -> List[str]:
        unknown_keys = []
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.debug(f"配置项已更新：{key}")
            else:
                unknown_keys.append(key)

        self.save()
        return unknown_keys

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def reset(self) -> None:
        default_config = Config()
        for field_name in self.__dataclass_fields__:
            if field_name != "config_dir":
                setattr(self, field_name, getattr(default_config, field_name))
        self.save()
        logger.info("配置已重置为默认值")

    def get_current_model(self) -> str:
        """获取当前提供商的默认模型"""
        if self.provider == "ollama":
            return self.default_model
        elif self.provider == "openai":
            return self.openai_model
        elif self.provider == "claude":
            return self.claude_model
        elif self.provider == "custom":
            return self.custom_model
        return ""

    def get_api_key(self) -> str:
        """获取当前提供商的 API Key"""
        if self.provider == "openai":
            return self.openai_api_key
        elif self.provider == "claude":
            return self.claude_api_key
        elif self.provider == "custom":
            return self.custom_api_key
        return ""

    def get_base_url(self) -> str:
        """获取当前提供商的 Base URL"""
        if self.provider == "ollama":
            return self.ollama_base_url
        elif self.provider == "openai":
            return self.openai_base_url
        elif self.provider == "claude":
            return self.claude_base_url
        elif self.provider == "custom":
            return self.custom_base_url
        return ""


# 全局配置单例
global_config = Config.load()