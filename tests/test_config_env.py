"""Environment variable tests for configuration management."""

import os
from unittest.mock import patch

from src.config import Config, _get_env_key


class TestEnvVariables:
    def test_get_env_key_exists(self):
        with patch.dict(os.environ, {"TEST_KEY": "test_value"}):
            assert _get_env_key("TEST_KEY") == "test_value"

    def test_get_env_key_not_exists(self):
        assert _get_env_key("NONEXISTENT_KEY") == ""
        assert _get_env_key("NONEXISTENT_KEY", "default") == "default"

    def test_config_load_with_env_override(self):
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "sk-test-from-env",
                "CLAUDE_API_KEY": "sk-ant-test-from-env",
            },
        ):
            from src import config as config_module

            config_module.global_config = None

            Config.load()
            result = Config._apply_env_overrides({})

            assert result["openai_api_key"] == "sk-test-from-env"
            assert result["claude_api_key"] == "sk-ant-test-from-env"

    def test_env_takes_priority_over_config(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            config_data = {"openai_api_key": "file-key"}
            result = Config._apply_env_overrides(config_data)

            assert result["openai_api_key"] == "env-key"

    def test_promptpro_model_targets_active_provider(self):
        with patch.dict(
            os.environ,
            {
                "PROMPTPRO_PROVIDER": "openai",
                "PROMPTPRO_MODEL": "gpt-4o",
            },
        ):
            result = Config._apply_env_overrides({})

            assert result["provider"] == "openai"
            assert result["openai_model"] == "gpt-4o"
            assert result["default_model"] == "gpt-4o"

    def test_config_without_env(self):
        env_backup = {}
        keys_to_clear = [
            "OPENAI_API_KEY",
            "CLAUDE_API_KEY",
            "CUSTOM_API_KEY",
            "CUSTOM_BASE_URL",
            "PROMPTPRO_PROVIDER",
            "PROMPTPRO_MODEL",
        ]
        for key in keys_to_clear:
            if key in os.environ:
                env_backup[key] = os.environ[key]
                del os.environ[key]

        try:
            test_data = {"openai_api_key": "file-key"}
            result = Config._apply_env_overrides(test_data)
            assert result["openai_api_key"] == "file-key"
        finally:
            for key, value in env_backup.items():
                os.environ[key] = value
