"""Requirement document parsing and management."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import re

from src.exceptions import ErrorCode, RequirementError


@dataclass
class RequirementDoc:
    name: str
    intro: str
    tune: str
    file_path: str
    updated_at: str

    def to_prompt_context(self) -> str:
        sections = [f"Requirement name: {self.name}"]
        if self.intro.strip():
            sections.append(f"Project context:\n{self.intro.strip()}")
        if self.tune.strip():
            sections.append(f"Tuning requirements:\n{self.tune.strip()}")
        return "\n\n".join(sections)


class RequirementParser:
    MULTILINE_PATTERN = re.compile(r"^(\w+):\s*\|\s*\n((?:[ \t]+.*\n?)*)", re.MULTILINE)
    SINGLELINE_PATTERN = re.compile(r"^(\w+):\s*(.+)$", re.MULTILINE)

    @staticmethod
    def parse_file(file_path: str) -> RequirementDoc:
        path = Path(file_path)
        if not path.exists():
            raise RequirementError(
                f"Requirement file not found: {file_path}",
                error_code=ErrorCode.REQUIREMENT_NOT_FOUND,
            )

        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise RequirementError(
                f"Failed to read requirement file: {exc}",
                error_code=ErrorCode.REQUIREMENT_READ_FAILED,
                details=str(exc),
            ) from exc

        return RequirementParser.parse_content(content, file_path)

    @staticmethod
    def parse_content(content: str, file_path: str = "") -> RequirementDoc:
        fields = RequirementParser._extract_fields(content)
        if "name" not in fields:
            raise RequirementError(
                "Requirement document must include a name field.",
                error_code=ErrorCode.REQUIREMENT_INVALID,
            )

        updated_at = ""
        if file_path:
            try:
                updated_at = str(Path(file_path).stat().st_mtime)
            except OSError:
                updated_at = ""

        return RequirementDoc(
            name=fields.get("name", ""),
            intro=fields.get("intro", ""),
            tune=fields.get("tune", ""),
            file_path=file_path,
            updated_at=updated_at,
        )

    @staticmethod
    def _extract_fields(content: str) -> dict:
        fields = {}

        for match in RequirementParser.MULTILINE_PATTERN.finditer(content):
            field_name = match.group(1).lower()
            raw_value = match.group(2).strip("\n")
            lines = raw_value.splitlines()
            if not lines:
                fields[field_name] = ""
                continue

            min_indent = min(
                len(line) - len(line.lstrip())
                for line in lines
                if line.strip()
            )
            normalized = [
                line[min_indent:] if len(line) > min_indent else line.lstrip()
                for line in lines
            ]
            fields[field_name] = "\n".join(normalized).strip()

        remaining = RequirementParser.MULTILINE_PATTERN.sub("", content)
        for match in RequirementParser.SINGLELINE_PATTERN.finditer(remaining):
            field_name = match.group(1).lower()
            fields.setdefault(field_name, match.group(2).strip())

        return fields


class RequirementManager:
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self._current_doc: Optional[RequirementDoc] = None
        self._docs_cache: Optional[List[RequirementDoc]] = None

    def discover_docs(self) -> List[RequirementDoc]:
        if not self.prompts_dir.exists():
            self._docs_cache = []
            return []

        docs: List[RequirementDoc] = []
        for md_file in sorted(self.prompts_dir.glob("*.md"), key=lambda path: path.name.lower()):
            try:
                docs.append(RequirementParser.parse_file(str(md_file)))
            except RequirementError:
                continue

        self._docs_cache = docs
        return docs

    def list_docs(self) -> List[dict]:
        docs = self.discover_docs() if self._docs_cache is None else self._docs_cache
        result = []
        for doc in docs:
            intro_clean = doc.intro.replace("\n", " ").strip()
            preview = intro_clean[:50] + "..." if len(intro_clean) > 50 else intro_clean
            result.append({"name": doc.name, "file": Path(doc.file_path).stem, "preview": preview})
        return result

    def load_doc(self, file_identifier: str) -> RequirementDoc:
        return RequirementParser.parse_file(str(self._resolve_doc_path(file_identifier)))

    def select_doc(self, file_identifier: str) -> RequirementDoc:
        self._current_doc = self.load_doc(file_identifier)
        return self._current_doc

    def get_current_doc(self) -> Optional[RequirementDoc]:
        return self._current_doc

    def clear_current_doc(self) -> None:
        self._current_doc = None

    def create_doc(
        self,
        name: str,
        intro: str,
        tune: str,
        filename: Optional[str] = None,
    ) -> str:
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        file_stem = filename or self._slugify_filename(name)
        file_path = self.prompts_dir / f"{file_stem}.md"
        content = (
            f"name: {name}\n"
            f"intro: |\n{self._indent_block(intro)}\n"
            f"tune: |\n{self._indent_block(tune)}\n"
        )
        file_path.write_text(content, encoding="utf-8")
        self._docs_cache = None
        return str(file_path)

    def _resolve_doc_path(self, file_identifier: str) -> Path:
        candidate = Path(file_identifier)
        if candidate.is_absolute() or candidate.suffix == ".md":
            return candidate
        return self.prompts_dir / f"{file_identifier}.md"

    @staticmethod
    def _slugify_filename(name: str) -> str:
        slug = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", name).strip("_")
        return slug or "untitled"

    @staticmethod
    def _indent_block(value: str) -> str:
        lines = value.splitlines() or [""]
        return "\n".join(f"  {line}" for line in lines)


_requirement_manager: Optional[RequirementManager] = None


def get_requirement_manager(prompts_dir: str = "prompts") -> RequirementManager:
    global _requirement_manager
    if _requirement_manager is None:
        _requirement_manager = RequirementManager(prompts_dir=prompts_dir)
    return _requirement_manager
