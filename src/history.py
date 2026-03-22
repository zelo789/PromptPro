"""History storage for prompt optimization results."""

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from src.config import Config, global_config
from src.exceptions import ErrorCode, HistoryError
from src.logger import get_logger

logger = get_logger("history")


@dataclass
class HistoryItem:
    id: str
    timestamp: str
    original_prompt: str
    optimized_prompts: List[Dict[str, str]]
    framework: Optional[str] = None
    model: Optional[str] = None
    selected_version: Optional[int] = None


class HistoryManager:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or global_config
        self.history_file = self.config.history_file
        self.max_items = self.config.max_history_items
        self.enabled = self.config.enable_history

        if self.enabled:
            try:
                self._ensure_history_directory()
            except HistoryError as exc:
                logger.warning("History disabled because initialization failed: %s", exc)
                self.enabled = False

    def _ensure_history_directory(self) -> None:
        try:
            Path(self.history_file).parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise HistoryError(
                "Failed to initialize history storage.",
                error_code=ErrorCode.HISTORY_SAVE_FAILED,
                details=str(exc),
            ) from exc

    def _load_history(self) -> List[Dict[str, Any]]:
        path = Path(self.history_file)
        if not path.exists():
            return []

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning("Failed to load history file, returning empty history.")
            return []

        if not isinstance(data, list):
            return []
        return [item for item in data if isinstance(item, dict)]

    def _save_history(self, history: List[Dict[str, Any]]) -> None:
        try:
            history_path = Path(self.history_file)
            history_path.parent.mkdir(parents=True, exist_ok=True)
            history_path.write_text(
                json.dumps(history, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise HistoryError(
                "Failed to save history.",
                error_code=ErrorCode.HISTORY_SAVE_FAILED,
                details=str(exc),
            ) from exc

    def add(
        self,
        original_prompt: str,
        optimized_prompts: List[Dict[str, str]],
        framework: Optional[str] = None,
        model: Optional[str] = None,
        selected_version: Optional[int] = None,
    ) -> HistoryItem:
        if not self.enabled:
            return HistoryItem("", "", original_prompt, optimized_prompts)

        now = datetime.now()
        item = HistoryItem(
            id=now.strftime("%Y%m%d%H%M%S%f"),
            timestamp=now.isoformat(),
            original_prompt=original_prompt,
            optimized_prompts=optimized_prompts,
            framework=framework,
            model=model,
            selected_version=selected_version,
        )

        history = self._load_history()
        history.insert(0, asdict(item))
        if len(history) > self.max_items:
            history = history[: self.max_items]
        self._save_history(history)
        return item

    def get_all(self, limit: Optional[int] = None) -> List[HistoryItem]:
        items = [HistoryItem(**item) for item in self._load_history()]
        return items[:limit] if limit else items

    def get_by_id(self, item_id: str) -> Optional[HistoryItem]:
        for item in self._load_history():
            if item.get("id") == item_id:
                return HistoryItem(**item)
        return None

    def search(self, keyword: str) -> List[HistoryItem]:
        needle = keyword.lower()
        matched: List[HistoryItem] = []

        for item in self._load_history():
            original = item.get("original_prompt", "").lower()
            framework = (item.get("framework") or "").lower()
            model = (item.get("model") or "").lower()

            if needle in original or needle in framework or needle in model:
                matched.append(HistoryItem(**item))
                continue

            optimized_prompts = item.get("optimized_prompts", [])
            if any(needle in opt.get("prompt", "").lower() for opt in optimized_prompts):
                matched.append(HistoryItem(**item))

        return matched

    def delete(self, item_id: str) -> bool:
        history = self._load_history()
        updated = [item for item in history if item.get("id") != item_id]
        if len(updated) == len(history):
            return False
        self._save_history(updated)
        return True

    def clear(self) -> int:
        history = self._load_history()
        self._save_history([])
        return len(history)

    def export(self, output_file: str) -> int:
        history = self._load_history()
        try:
            Path(output_file).write_text(
                json.dumps(history, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise HistoryError(
                "Failed to export history.",
                error_code=ErrorCode.HISTORY_SAVE_FAILED,
                details=str(exc),
            ) from exc
        return len(history)


global_history = HistoryManager()
