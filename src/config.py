"""Configuration management for PromptPro."""

from dataclasses import MISSING, asdict, dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Dict, List
import json
import os
import shutil

from src.exceptions import ConfigError
from src.logger import get_logger

logger = get_logger("config")

CONFIG_VERSION = 3
DEFAULT_CONFIG_DIRNAME = ".prompt-optimizer"
CONFIG_FILENAME = "config.json"
HISTORY_FILENAME = "history.json"
CONFIG_DIR_ENV_VAR = "PROMPTPRO_CONFIG_DIR"

ENV_TO_CONFIG_MAP: Dict[str, str] = {
    "OLLAMA_BASE_URL": "ollama_base_url",
    "OPENAI_API_KEY": "openai_api_key",
    "OPENAI_BASE_URL": "openai_base_url",
    "CLAUDE_API_KEY": "claude_api_key",
    "CLAUDE_BASE_URL": "claude_base_url",
    "CUSTOM_API_KEY": "custom_api_key",
    "CUSTOM_BASE_URL": "custom_base_url",
    "PROMPTPRO_PROVIDER": "provider",
}

SECRET_FIELDS = {"openai_api_key", "claude_api_key", "custom_api_key"}


def _get_env_key(var_name: str, default: str = "") -> str:
    return os.getenv(var_name, default)


def _get_env_bool(var_name: str) -> bool | None:
    value = os.getenv(var_name)
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None


def _get_default_config_home() -> Path:
    configured_dir = _get_env_key(CONFIG_DIR_ENV_VAR)
    if configured_dir:
        return Path(configured_dir).expanduser()
    return Path.home() / DEFAULT_CONFIG_DIRNAME


@dataclass
class Config:
    version: int = CONFIG_VERSION
    provider: str = "ollama"

    ollama_base_url: str = "http://localhost:11434"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    claude_api_key: str = ""
    claude_base_url: str = "https://api.anthropic.com"
    claude_model: str = "claude-3-5-sonnet-20241022"

    custom_api_key: str = ""
    custom_base_url: str = ""
    custom_model: str = ""

    default_model: str = ""

    temperature: float = 0.7
    request_timeout: int = 300
    max_retries: int = 3
    retry_delay: float = 1.0

    optimization_dimensions: List[str] = field(
        default_factory=lambda: ["structure", "clarity", "context", "constraints", "examples"]
    )
    num_versions: int = 3

    enable_history: bool = True
    max_history_items: int = 100
    auto_clipboard: bool = True
    enable_clarifying_questions: bool = True
    log_level: str = "INFO"

    config_dir: str = field(default_factory=lambda: str(_get_default_config_home()))

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
        Path(self.config_dir).mkdir(parents=True, exist_ok=True)

    @property
    def config_file(self) -> str:
        return str(Path(self.config_dir) / CONFIG_FILENAME)

    @property
    def history_file(self) -> str:
        return str(Path(self.config_dir) / HISTORY_FILENAME)

    def validate(self) -> List[str]:
        errors: List[str] = []
        for field_name, rules in self._validators.items():
            value = getattr(self, field_name, None)
            if value is None:
                continue
            if "min" in rules and "max" in rules and not (rules["min"] <= value <= rules["max"]):
                errors.append(f"{field_name} must be between {rules['min']} and {rules['max']}")
            if "choices" in rules and value not in rules["choices"]:
                errors.append(f"{field_name} must be one of {rules['choices']}")
        return errors

    def is_valid(self) -> bool:
        return not self.validate()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_safe_dict(self) -> Dict[str, Any]:
        data = self.to_dict()
        for key in SECRET_FIELDS:
            if data.get(key):
                data[key] = "***"
        return data

    def save(self) -> None:
        config_path = Path(self.config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        if config_path.exists():
            backup_path = config_path.with_suffix(config_path.suffix + ".bak")
            try:
                shutil.copy2(config_path, backup_path)
            except OSError as exc:
                logger.warning("Failed to back up config file: %s", exc)

        try:
            config_path.write_text(
                json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise ConfigError(f"Failed to save config: {exc}", details=str(exc)) from exc

    @classmethod
    def load(cls, config_dir: str = "") -> "Config":
        config_home = Path(config_dir).expanduser() if config_dir else _get_default_config_home()
        config_path = config_home / CONFIG_FILENAME
        if not config_path.exists():
            config_data = cls._apply_env_overrides({})
            config_data["config_dir"] = str(config_home)
            return cls(**config_data)

        try:
            config_data = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Failed to parse config file: {exc}", details=str(exc)) from exc

        config_data = {
            key: value for key, value in config_data.items()
            if not str(key).startswith("_")
        }
        config_data = cls._migrate_config(config_data)
        config_data = cls._apply_env_overrides(config_data)
        config_data["config_dir"] = str(config_home)

        try:
            return cls(**config_data)
        except TypeError as exc:
            raise ConfigError(f"Invalid config data: {exc}", details=str(exc)) from exc

    @classmethod
    def _apply_env_overrides(cls, config_data: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(config_data)
        for env_var, config_key in ENV_TO_CONFIG_MAP.items():
            value = os.getenv(env_var)
            if value:
                merged[config_key] = value

        model_override = os.getenv("PROMPTPRO_MODEL")
        if model_override:
            provider = merged.get("provider", "ollama")
            merged["default_model"] = model_override
            provider_model_keys = {
                "ollama": "default_model",
                "openai": "openai_model",
                "claude": "claude_model",
                "custom": "custom_model",
            }
            merged[provider_model_keys.get(provider, "default_model")] = model_override

        float_overrides = {
            "PROMPTPRO_TEMPERATURE": "temperature",
            "PROMPTPRO_RETRY_DELAY": "retry_delay",
        }
        for env_var, config_key in float_overrides.items():
            value = os.getenv(env_var)
            if value:
                try:
                    merged[config_key] = float(value)
                except ValueError:
                    logger.warning("Ignoring invalid %s value: %s", env_var, value)

        int_overrides = {
            "PROMPTPRO_TIMEOUT": "request_timeout",
            "PROMPTPRO_MAX_RETRIES": "max_retries",
            "PROMPTPRO_NUM_VERSIONS": "num_versions",
            "PROMPTPRO_MAX_HISTORY_ITEMS": "max_history_items",
        }
        for env_var, config_key in int_overrides.items():
            value = os.getenv(env_var)
            if value:
                try:
                    merged[config_key] = int(value)
                except ValueError:
                    logger.warning("Ignoring invalid %s value: %s", env_var, value)

        bool_overrides = {
            "PROMPTPRO_ENABLE_HISTORY": "enable_history",
            "PROMPTPRO_AUTO_CLIPBOARD": "auto_clipboard",
            "PROMPTPRO_ENABLE_CLARIFY": "enable_clarifying_questions",
        }
        for env_var, config_key in bool_overrides.items():
            value = _get_env_bool(env_var)
            if value is not None:
                merged[config_key] = value
        return merged

    @classmethod
    def _migrate_config(cls, config_data: Dict[str, Any]) -> Dict[str, Any]:
        version = config_data.get("version", 1)
        migrated = dict(config_data)
        valid_fields = {name for name, info in cls.__dataclass_fields__.items() if info.init}

        if version < 3:
            migrated.setdefault("provider", "ollama")
            migrated.setdefault("openai_api_key", "")
            migrated.setdefault("openai_base_url", "https://api.openai.com/v1")
            migrated.setdefault("openai_model", "gpt-4o-mini")
            migrated.setdefault("claude_api_key", "")
            migrated.setdefault("claude_base_url", "https://api.anthropic.com")
            migrated.setdefault("claude_model", "claude-3-5-sonnet-20241022")
            migrated.setdefault("custom_api_key", "")
            migrated.setdefault("custom_base_url", "")
            migrated.setdefault("custom_model", "")

        for field_name, field_info in cls.__dataclass_fields__.items():
            if not field_info.init:
                continue
            if field_name in migrated:
                continue
            if field_info.default_factory is not MISSING:  # type: ignore[attr-defined]
                migrated[field_name] = field_info.default_factory()
            elif field_info.default is not MISSING:
                migrated[field_name] = field_info.default

        migrated["version"] = CONFIG_VERSION
        return {
            key: value for key, value in migrated.items()
            if key in valid_fields and not str(key).startswith("_")
        }

    def update(self, **kwargs: Any) -> List[str]:
        unknown_keys: List[str] = []
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                unknown_keys.append(key)
        self.save()
        return unknown_keys

    def reset(self) -> None:
        defaults = Config(config_dir=self.config_dir)
        for field_name, field_info in self.__dataclass_fields__.items():
            if not field_info.init:
                continue
            if field_name == "config_dir":
                continue
            setattr(self, field_name, getattr(defaults, field_name))
        self.save()

    def get_current_model(self) -> str:
        if self.provider == "ollama":
            return self.default_model
        if self.provider == "openai":
            return self.openai_model
        if self.provider == "claude":
            return self.claude_model
        if self.provider == "custom":
            return self.custom_model
        return ""

    def get_api_key(self) -> str:
        if self.provider == "openai":
            return self.openai_api_key
        if self.provider == "claude":
            return self.claude_api_key
        if self.provider == "custom":
            return self.custom_api_key
        return ""

    def get_base_url(self) -> str:
        if self.provider == "ollama":
            return self.ollama_base_url
        if self.provider == "openai":
            return self.openai_base_url
        if self.provider == "claude":
            return self.claude_base_url
        if self.provider == "custom":
            return self.custom_base_url
        return ""


global_config = Config.load()
