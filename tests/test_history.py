"""
历史记录模块测试
"""
import pytest
import json
import os
from datetime import datetime
from unittest.mock import patch, mock_open

from src.history import HistoryManager, HistoryItem


class TestHistoryItem:
    """HistoryItem 测试"""

    def test_history_item_creation(self):
        """测试历史记录项创建"""
        item = HistoryItem(
            id="20240101120000",
            timestamp="2024-01-01T12:00:00",
            original_prompt="测试 prompt",
            optimized_prompts=[{"prompt": "优化后", "name": "轻度"}],
        )
        assert item.id == "20240101120000"
        assert item.original_prompt == "测试 prompt"
        assert len(item.optimized_prompts) == 1

    def test_history_item_with_optional_fields(self):
        """测试带可选字段的历史记录项"""
        item = HistoryItem(
            id="20240101120000",
            timestamp="2024-01-01T12:00:00",
            original_prompt="测试",
            optimized_prompts=[],
            framework="co_star",
            model="llama2",
            selected_version=1,
        )
        assert item.framework == "co_star"
        assert item.model == "llama2"
        assert item.selected_version == 1


class TestHistoryManager:
    """HistoryManager 测试"""

    @pytest.fixture
    def temp_history_file(self, tmp_path):
        """临时历史文件"""
        return str(tmp_path / "history.json")

    @pytest.fixture
    def history_manager(self, temp_history_file):
        """历史管理器"""
        from src.config import Config
        config = Config()
        manager = HistoryManager(config)
        # 直接设置 history_file 属性（它是实例属性）
        manager.history_file = temp_history_file
        manager.enabled = True
        manager._ensure_history_file()
        return manager

    def test_add_history_item(self, history_manager):
        """测试添加历史记录"""
        item = history_manager.add(
            original_prompt="测试 prompt",
            optimized_prompts=[{"prompt": "优化后", "name": "轻度"}],
        )
        assert item.id
        assert item.original_prompt == "测试 prompt"

    def test_get_all_history(self, history_manager):
        """测试获取所有历史"""
        history_manager.add("prompt1", [{"prompt": "opt1", "name": "轻度"}])
        history_manager.add("prompt2", [{"prompt": "opt2", "name": "轻度"}])

        items = history_manager.get_all()
        assert len(items) == 2

    def test_get_history_with_limit(self, history_manager):
        """测试限制历史数量"""
        for i in range(5):
            history_manager.add(f"prompt{i}", [{"prompt": f"opt{i}", "name": "轻度"}])

        items = history_manager.get_all(limit=3)
        assert len(items) == 3

    def test_search_history(self, history_manager):
        """测试搜索历史"""
        history_manager.add("Python 编程", [{"prompt": "opt", "name": "轻度"}])
        history_manager.add("Java 开发", [{"prompt": "opt", "name": "轻度"}])

        items = history_manager.search("Python")
        assert len(items) == 1
        assert "Python" in items[0].original_prompt

    def test_delete_history(self, history_manager):
        """测试删除历史"""
        item = history_manager.add("prompt", [{"prompt": "opt", "name": "轻度"}])

        result = history_manager.delete(item.id)
        assert result is True

        items = history_manager.get_all()
        assert len(items) == 0

    def test_clear_history(self, history_manager):
        """测试清空历史"""
        history_manager.add("prompt1", [{"prompt": "opt", "name": "轻度"}])
        history_manager.add("prompt2", [{"prompt": "opt", "name": "轻度"}])

        count = history_manager.clear()
        assert count == 2

        items = history_manager.get_all()
        assert len(items) == 0