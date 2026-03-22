"""Tests for requirement document parsing and management."""

from pathlib import Path

import pytest

from src.exceptions import ErrorCode, RequirementError
from src.requirement import RequirementDoc, RequirementManager, RequirementParser


class TestRequirementParser:
    def test_parse_single_line_fields(self):
        content = "name: Test Doc\nintro: Intro text\ntune: Tune text\n"
        doc = RequirementParser.parse_content(content)

        assert doc.name == "Test Doc"
        assert doc.intro == "Intro text"
        assert doc.tune == "Tune text"

    def test_parse_multiline_fields(self):
        content = (
            "name: Multi Line\n"
            "intro: |\n"
            "  first line\n"
            "  second line\n"
            "tune: |\n"
            "  - item 1\n"
            "  - item 2\n"
        )
        doc = RequirementParser.parse_content(content)

        assert doc.name == "Multi Line"
        assert "first line" in doc.intro
        assert "second line" in doc.intro
        assert "- item 1" in doc.tune

    def test_parse_missing_name_raises_error(self):
        with pytest.raises(RequirementError) as exc_info:
            RequirementParser.parse_content("intro: missing name")

        assert exc_info.value.error_code == ErrorCode.REQUIREMENT_INVALID

    def test_parse_file(self, tmp_path):
        file_path = tmp_path / "test.md"
        file_path.write_text("name: File Test\nintro: Intro\ntune: Tune", encoding="utf-8")

        doc = RequirementParser.parse_file(str(file_path))
        assert doc.name == "File Test"
        assert doc.file_path == str(file_path)

    def test_parse_nonexistent_file_raises_error(self):
        with pytest.raises(RequirementError) as exc_info:
            RequirementParser.parse_file("/nonexistent/path.md")

        assert exc_info.value.error_code == ErrorCode.REQUIREMENT_NOT_FOUND


class TestRequirementManager:
    def test_discover_docs_empty_dir(self, tmp_path):
        manager = RequirementManager(prompts_dir=str(tmp_path))
        assert manager.discover_docs() == []

    def test_discover_docs_sorted(self, tmp_path):
        (tmp_path / "b.md").write_text("name: B\nintro: second", encoding="utf-8")
        (tmp_path / "a.md").write_text("name: A\nintro: first", encoding="utf-8")

        manager = RequirementManager(prompts_dir=str(tmp_path))
        docs = manager.discover_docs()

        assert [doc.name for doc in docs] == ["A", "B"]

    def test_list_docs(self, tmp_path):
        (tmp_path / "test.md").write_text(
            "name: Preview Doc\nintro: This is a long intro for preview generation.",
            encoding="utf-8",
        )
        manager = RequirementManager(prompts_dir=str(tmp_path))
        docs = manager.list_docs()

        assert len(docs) == 1
        assert docs[0]["name"] == "Preview Doc"
        assert "preview" in docs[0]

    def test_load_doc(self, tmp_path):
        (tmp_path / "load_test.md").write_text(
            "name: Load Test\nintro: Intro\ntune: Tune",
            encoding="utf-8",
        )
        manager = RequirementManager(prompts_dir=str(tmp_path))

        doc = manager.load_doc("load_test")
        assert doc.name == "Load Test"

    def test_select_and_get_current_doc(self, tmp_path):
        (tmp_path / "current.md").write_text("name: Current\nintro: Intro", encoding="utf-8")
        manager = RequirementManager(prompts_dir=str(tmp_path))

        selected = manager.select_doc("current")
        current = manager.get_current_doc()

        assert selected.name == "Current"
        assert current is not None
        assert current.name == "Current"

    def test_clear_current_doc(self, tmp_path):
        (tmp_path / "clear.md").write_text("name: Clear\nintro: Intro", encoding="utf-8")
        manager = RequirementManager(prompts_dir=str(tmp_path))
        manager.select_doc("clear")

        manager.clear_current_doc()
        assert manager.get_current_doc() is None

    def test_create_doc(self, tmp_path):
        manager = RequirementManager(prompts_dir=str(tmp_path))
        file_path = manager.create_doc(
            name="New Doc",
            intro="This is intro",
            tune="This is tune",
            filename="new_doc",
        )

        assert Path(file_path).exists()
        loaded = manager.load_doc("new_doc")
        assert loaded.name == "New Doc"
        assert loaded.intro == "This is intro"

    def test_create_doc_with_auto_filename(self, tmp_path):
        manager = RequirementManager(prompts_dir=str(tmp_path))
        file_path = manager.create_doc(name="Auto Name", intro="Intro", tune="Tune")

        assert Path(file_path).exists()
        assert "Auto_Name" in Path(file_path).stem or "Auto Name" not in Path(file_path).name


class TestRequirementDoc:
    def test_doc_creation(self):
        doc = RequirementDoc(
            name="Test",
            intro="Intro",
            tune="Tune",
            file_path="/path/to/file.md",
            updated_at="2024-01-01",
        )

        assert doc.name == "Test"
        assert doc.intro == "Intro"
        assert doc.tune == "Tune"

    def test_to_prompt_context(self):
        doc = RequirementDoc(
            name="Login",
            intro="Project background",
            tune="- be specific",
            file_path="/tmp/login.md",
            updated_at="2024-01-01",
        )

        context = doc.to_prompt_context()
        assert "Requirement name: Login" in context
        assert "Project context" in context
        assert "Tuning requirements" in context
