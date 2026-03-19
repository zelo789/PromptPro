"""
配置模块测试
"""
import pytest
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, mock_open

from src.config import Config, CONFIG_VERSION, resolve_config_dir


class TestConfig:
    """Config 类测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = Config(config_dir="/tmp/promptpro-test-config")
        assert config.ollama_base_url == "http://localhost:11434"
        assert config.default_model == ""
        assert config.request_timeout == 300
        assert config.temperature == 0.7
        assert config.max_retries == 3
        assert config.num_versions == 3
        assert config.enable_history is True
        assert config.auto_clipboard is True
        assert config.config_dir == "/tmp/promptpro-test-config"

    def test_config_validation_valid(self):
        """测试有效配置验证"""
        config = Config()
        errors = config.validate()
        assert len(errors) == 0
        assert config.is_valid()

    def test_config_validation_invalid_url(self):
        """测试无效温度验证（URL 验证已移除）"""
        # URL 验证已移除，现在测试温度验证
        config = Config(temperature=3.0)
        errors = config.validate()
        assert len(errors) > 0
        assert any("temperature" in e for e in errors)

    def test_config_validation_invalid_temperature(self):
        """测试无效温度验证"""
        config = Config(temperature=3.0)
        errors = config.validate()
        assert len(errors) > 0
        assert any("temperature" in e for e in errors)

    def test_config_validation_invalid_num_versions(self):
        """测试无效版本数验证"""
        config = Config(num_versions=10)
        errors = config.validate()
        assert len(errors) > 0

    def test_config_update(self):
        """测试配置更新"""
        config = Config()
        config.update(temperature=0.5, default_model="test-model")
        assert config.temperature == 0.5
        assert config.default_model == "test-model"

    def test_config_to_dict(self):
        """测试配置转字典"""
        config = Config(temperature=0.8)
        data = config.to_dict()
        assert isinstance(data, dict)
        assert data["temperature"] == 0.8

    def test_config_migrate_v1_to_v2(self):
        """测试配置迁移"""
        old_config = {
            "ollama_base_url": "http://localhost:11434",
            "default_model": "",
        }
        migrated = Config._migrate_config(old_config)
        # v1 迁移会添加所有默认字段
        assert "provider" in migrated
        assert "openai_api_key" in migrated
        # 版本号会被设置
        assert "version" in migrated


class TestConfigFile:
    """配置文件测试"""

    def test_config_file_path(self):
        """测试配置文件路径"""
        config = Config()
        assert config.config_file.endswith("config.json")
        assert ".prompt-optimizer" in config.config_file

    def test_history_file_path(self):
        """测试历史文件路径"""
        config = Config()
        assert config.history_file.endswith("history.json")
        assert ".prompt-optimizer" in config.history_file

    def test_promptpro_home_env_override(self, monkeypatch, tmp_path):
        monkeypatch.setenv("PROMPTPRO_HOME", str(tmp_path / "promptpro-home"))
        assert resolve_config_dir() == tmp_path / "promptpro-home"

    def test_import_has_no_filesystem_side_effect(self, tmp_path):
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        result = subprocess.run(
            [sys.executable, "-c", "import src.config, src.history, src.strategies"],
            cwd=Path(__file__).resolve().parents[1],
            env={**os.environ, "HOME": str(home_dir), "PROMPTPRO_HOME": str(home_dir / 'pp-home')},
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert not (home_dir / ".prompt-optimizer").exists()
        assert not (home_dir / "pp-home").exists()
