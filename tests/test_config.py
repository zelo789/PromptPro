"""Tests for configuration management."""

from src.config import Config


class TestConfig:
    def test_default_config(self):
        config = Config()
        assert config.ollama_base_url == "http://localhost:11434"
        assert config.default_model == ""
        assert config.request_timeout == 300
        assert config.temperature == 0.7
        assert config.max_retries == 3
        assert config.num_versions == 3
        assert config.enable_history is True
        assert config.auto_clipboard is True

    def test_config_validation_valid(self):
        config = Config()
        assert config.validate() == []
        assert config.is_valid()

    def test_config_validation_invalid_temperature(self):
        config = Config(temperature=3.0)
        errors = config.validate()
        assert errors
        assert any("temperature" in error for error in errors)

    def test_config_validation_invalid_num_versions(self):
        config = Config(num_versions=10)
        assert config.validate()

    def test_config_update(self, tmp_path):
        config = Config(config_dir=str(tmp_path))
        config.update(temperature=0.5, default_model="test-model")
        assert config.temperature == 0.5
        assert config.default_model == "test-model"

    def test_config_to_dict(self):
        config = Config(temperature=0.8)
        data = config.to_dict()
        assert isinstance(data, dict)
        assert data["temperature"] == 0.8

    def test_config_to_safe_dict_masks_secrets(self):
        config = Config(openai_api_key="secret")
        data = config.to_safe_dict()
        assert data["openai_api_key"] == "***"

    def test_config_migrate_v1_to_v3(self):
        old_config = {
            "ollama_base_url": "http://localhost:11434",
            "default_model": "",
        }
        migrated = Config._migrate_config(old_config)
        assert "provider" in migrated
        assert "openai_api_key" in migrated
        assert migrated["version"] == 3
        assert "_validators" not in migrated


class TestConfigFile:
    def test_config_file_path(self):
        config = Config()
        assert config.config_file.endswith("config.json")
        assert ".prompt-optimizer" in config.config_file

    def test_history_file_path(self):
        config = Config()
        assert config.history_file.endswith("history.json")
        assert ".prompt-optimizer" in config.history_file

    def test_load_respects_config_dir_override(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PROMPTPRO_CONFIG_DIR", str(tmp_path))
        config = Config.load()
        assert config.config_dir == str(tmp_path)
