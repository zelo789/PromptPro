"""
需求文档模块测试
"""
import pytest
from pathlib import Path
import tempfile
import os

from src.requirement import (
    RequirementDoc,
    RequirementParser,
    RequirementManager,
)
from src.exceptions import RequirementError, ErrorCode


class TestRequirementParser:
    """测试需求文档解析器"""

    def test_parse_single_line_fields(self):
        """测试单行字段解析"""
        content = """name: 测试文档
intro: 这是一个简介
tune: 调优要求
"""
        doc = RequirementParser.parse_content(content)

        assert doc.name == "测试文档"
        assert doc.intro == "这是一个简介"
        assert doc.tune == "调优要求"

    def test_parse_multiline_fields(self):
        """测试多行字段解析"""
        content = """name: 多行文档
intro: |
  这是第一行简介
  这是第二行简介
  这是第三行简介
tune: |
  - 调优要求1
  - 调优要求2
"""
        doc = RequirementParser.parse_content(content)

        assert doc.name == "多行文档"
        assert "第一行简介" in doc.intro
        assert "第二行简介" in doc.intro
        assert "调优要求1" in doc.tune

    def test_parse_mixed_fields(self):
        """测试混合字段解析"""
        content = """name: 混合文档
intro: |
  多行简介内容
  第二行简介
tune: 单行调优要求
"""
        doc = RequirementParser.parse_content(content)

        assert doc.name == "混合文档"
        assert "多行简介内容" in doc.intro
        assert doc.tune == "单行调优要求"

    def test_parse_missing_name_raises_error(self):
        """测试缺少 name 字段时抛出错误"""
        content = """intro: 简介
tune: 调优
"""
        with pytest.raises(RequirementError) as exc_info:
            RequirementParser.parse_content(content)

        assert exc_info.value.error_code == ErrorCode.REQUIREMENT_INVALID

    def test_parse_file(self, tmp_path):
        """测试文件解析"""
        file_path = tmp_path / "test.md"
        file_path.write_text("name: 文件测试\nintro: 简介\ntune: 调优", encoding='utf-8')

        doc = RequirementParser.parse_file(str(file_path))

        assert doc.name == "文件测试"
        assert doc.file_path == str(file_path)

    def test_parse_nonexistent_file_raises_error(self):
        """测试解析不存在的文件时抛出错误"""
        with pytest.raises(RequirementError) as exc_info:
            RequirementParser.parse_file("/nonexistent/path.md")

        assert exc_info.value.error_code == ErrorCode.REQUIREMENT_NOT_FOUND

    def test_parse_chinese_filename(self, tmp_path):
        """测试中文文件名"""
        file_path = tmp_path / "中文文档.md"
        file_path.write_text("name: 中文测试\nintro: 简介内容", encoding='utf-8')

        doc = RequirementParser.parse_file(str(file_path))

        assert doc.name == "中文测试"


class TestRequirementManager:
    """测试需求文档管理器"""

    def test_discover_docs_empty_dir(self, tmp_path):
        """测试空目录发现文档"""
        manager = RequirementManager(prompts_dir=str(tmp_path))
        docs = manager.discover_docs()

        assert docs == []

    def test_discover_docs_with_files(self, tmp_path):
        """测试目录中发现文档"""
        # 创建测试文件
        file1 = tmp_path / "doc1.md"
        file1.write_text("name: 文档1\nintro: 简介1", encoding='utf-8')

        file2 = tmp_path / "doc2.md"
        file2.write_text("name: 文档2\nintro: 简介2", encoding='utf-8')

        manager = RequirementManager(prompts_dir=str(tmp_path))
        docs = manager.discover_docs()

        assert len(docs) == 2
        names = [d.name for d in docs]
        assert "文档1" in names
        assert "文档2" in names

    def test_list_docs(self, tmp_path):
        """测试列出文档"""
        file = tmp_path / "test.md"
        file.write_text("name: 测试文档\nintro: 这是一个很长的简介内容需要截断显示", encoding='utf-8')

        manager = RequirementManager(prompts_dir=str(tmp_path))
        docs = manager.list_docs()

        assert len(docs) == 1
        assert docs[0]['name'] == "测试文档"
        assert 'preview' in docs[0]

    def test_load_doc(self, tmp_path):
        """测试加载文档"""
        file = tmp_path / "load_test.md"
        file.write_text("name: 加载测试\nintro: 简介内容\ntune: 调优要求", encoding='utf-8')

        manager = RequirementManager(prompts_dir=str(tmp_path))
        doc = manager.load_doc("load_test")

        assert doc.name == "加载测试"

    def test_select_and_get_current_doc(self, tmp_path):
        """测试选择和获取当前文档"""
        file = tmp_path / "current.md"
        file.write_text("name: 当前文档\nintro: 简介", encoding='utf-8')

        manager = RequirementManager(prompts_dir=str(tmp_path))

        # 选择文档
        doc = manager.select_doc("current")
        assert doc.name == "当前文档"

        # 获取当前文档
        current = manager.get_current_doc()
        assert current is not None
        assert current.name == "当前文档"

    def test_clear_current_doc(self, tmp_path):
        """测试清除当前文档"""
        file = tmp_path / "clear.md"
        file.write_text("name: 清除测试\nintro: 简介", encoding='utf-8')

        manager = RequirementManager(prompts_dir=str(tmp_path))
        manager.select_doc("clear")

        assert manager.get_current_doc() is not None

        manager.clear_current_doc()
        assert manager.get_current_doc() is None

    def test_create_doc(self, tmp_path):
        """测试创建文档"""
        manager = RequirementManager(prompts_dir=str(tmp_path))

        file_path = manager.create_doc(
            name="新建文档",
            intro="这是简介",
            tune="这是调优要求",
            filename="new_doc",
        )

        assert Path(file_path).exists()

        # 验证内容
        doc = manager.load_doc("new_doc")
        assert doc.name == "新建文档"
        assert doc.intro == "这是简介"

    def test_create_doc_with_auto_filename(self, tmp_path):
        """测试自动生成文件名"""
        manager = RequirementManager(prompts_dir=str(tmp_path))

        file_path = manager.create_doc(
            name="自动命名测试",
            intro="简介",
            tune="调优",
        )

        assert Path(file_path).exists()
        assert "自动命名测试" in file_path or "test" in file_path.lower()


class TestRequirementDoc:
    """测试需求文档数据模型"""

    def test_doc_creation(self):
        """测试文档创建"""
        doc = RequirementDoc(
            name="测试",
            intro="简介",
            tune="调优",
            file_path="/path/to/file.md",
            updated_at="2024-01-01",
        )

        assert doc.name == "测试"
        assert doc.intro == "简介"
        assert doc.tune == "调优"