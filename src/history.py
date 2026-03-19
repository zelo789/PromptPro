"""
历史记录管理模块

提供 Prompt 优化历史的存储和查询功能。
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from src.config import Config, get_config
from src.exceptions import HistoryError, ErrorCode
from src.logger import get_logger

logger = get_logger("history")


@dataclass
class HistoryItem:
    """历史记录条目"""

    id: str
    timestamp: str
    original_prompt: str
    optimized_prompts: List[Dict[str, str]]
    framework: Optional[str] = None
    model: Optional[str] = None
    selected_version: Optional[int] = None


class HistoryManager:
    """历史记录管理器"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        self.history_file = self.config.history_file
        self.max_items = self.config.max_history_items
        self.enabled = self.config.enable_history

    def _load_history(self) -> List[Dict[str, Any]]:
        """加载历史记录。"""
        if not self.enabled or not os.path.exists(self.history_file):
            return []

        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"历史记录文件解析失败：{e}")
            return []
        except OSError as e:
            logger.error(f"读取历史记录文件失败：{e}")
            return []

    def _save_history(self, history: List[Dict[str, Any]]) -> None:
        """保存历史记录。"""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            logger.debug(f"历史记录已保存，共 {len(history)} 条")
        except OSError as e:
            logger.error(f"保存历史记录失败：{e}")
            raise HistoryError(
                "保存历史记录失败",
                error_code=ErrorCode.HISTORY_SAVE_FAILED,
                details=str(e),
            )

    def add(
        self,
        original_prompt: str,
        optimized_prompts: List[Dict[str, str]],
        framework: Optional[str] = None,
        model: Optional[str] = None,
        selected_version: Optional[int] = None,
    ) -> HistoryItem:
        """添加历史记录。"""
        if not self.enabled:
            logger.debug("历史记录已禁用，跳过保存")
            return HistoryItem(
                id="",
                timestamp="",
                original_prompt=original_prompt,
                optimized_prompts=optimized_prompts,
            )

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
            history = history[:self.max_items]
            logger.debug(f"历史记录已裁剪至 {self.max_items} 条")

        self._save_history(history)
        logger.info(f"已添加历史记录：{item.id}")
        return item

    def get_all(self, limit: Optional[int] = None) -> List[HistoryItem]:
        history = self._load_history()
        items = [HistoryItem(**item) for item in history]
        if limit:
            items = items[:limit]
        return items

    def get_by_id(self, item_id: str) -> Optional[HistoryItem]:
        history = self._load_history()
        for item in history:
            if item.get("id") == item_id:
                return HistoryItem(**item)
        return None

    def search(self, keyword: str) -> List[HistoryItem]:
        history = self._load_history()
        keyword_lower = keyword.lower()
        items = []
        for item in history:
            original = item.get("original_prompt", "").lower()
            if keyword_lower in original:
                items.append(HistoryItem(**item))
                continue

            for opt in item.get("optimized_prompts", []):
                if keyword_lower in opt.get("prompt", "").lower():
                    items.append(HistoryItem(**item))
                    break

        logger.debug(f"搜索 '{keyword}' 找到 {len(items)} 条记录")
        return items

    def delete(self, item_id: str) -> bool:
        history = self._load_history()
        original_len = len(history)
        history = [item for item in history if item.get("id") != item_id]

        if len(history) < original_len:
            self._save_history(history)
            logger.info(f"已删除历史记录：{item_id}")
            return True
        return False

    def clear(self) -> int:
        history = self._load_history()
        count = len(history)
        self._save_history([])
        logger.info(f"已清空历史记录，共删除 {count} 条")
        return count

    def export(self, output_file: str) -> int:
        history = self._load_history()

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            logger.info(f"已导出历史记录到：{output_file}")
            return len(history)
        except OSError as e:
            logger.error(f"导出历史记录失败：{e}")
            raise HistoryError(
                "导出历史记录失败",
                error_code=ErrorCode.HISTORY_SAVE_FAILED,
                details=str(e),
            )


_global_history: Optional[HistoryManager] = None


def get_history_manager(force_reload: bool = False) -> HistoryManager:
    """懒加载全局历史管理器。"""
    global _global_history
    if force_reload or _global_history is None:
        _global_history = HistoryManager()
    return _global_history


class LazyHistoryProxy:
    """向后兼容的懒加载历史代理。"""

    def __getattr__(self, name: str) -> Any:
        return getattr(get_history_manager(), name)

    def __repr__(self) -> str:
        return repr(get_history_manager())


global_history = LazyHistoryProxy()
