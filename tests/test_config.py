"""
配置模块测试
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from src.config import Config, CONFIG_VERSION


class TestConfig:
    """Config 类测试"""

    def test_default_config(self):
        """测试默认配置"""
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