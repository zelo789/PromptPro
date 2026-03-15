"""
历史记录管理模块

提供 Prompt 优化历史的存储和查询功能。
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

from src.config import Config, global_config
from src.exceptions import HistoryError, ErrorCode
from src.logger import get_logger

logger = get_logger("history")


@dataclass
class HistoryItem:
    """历史记录条目"""

    id: str
    """唯一标识符（时间戳）"""

    timestamp: str
    """记录时间"""

    original_prompt: str
    """原始 prompt"""

    optimized_prompts: List[Dict[str, str]]
    """优化后的 prompt 列表"""

    framework: Optional[str] = None
    """使用的框架"""

    model: Optional[str] = None
    """使用的模型"""

    selected_version: Optional[int] = None
    """用户选择的版本索引"""


class HistoryManager:
    """历史记录管理器"""

    def __init__(self, config: Optional[Config] = None):
        """
        初始化历史管理器

        Args:
            config: 配置对象
        """
        self.config = config or global_config
        self.history_file = self.config.history_file
        self.max_items = self.config.max_history_items
        self.enabled = self.config.enable_history

        if self.enabled:
            self._ensure_history_file()
            logger.debug(f"历史记录已启用，文件：{self.history_file}")

    def _ensure_history_file(self) -> None:
        """确保历史记录文件存在"""
        if not os.path.exists(self.history_file):
            self._save_history([])
            logger.debug("已创建历史记录文件")

    def _load_history(self) -> List[Dict[str, Any]]:
        """加载历史记录"""
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
        """保存历史记录"""
        try:
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
        """
        添加历史记录

        Args:
            original_prompt: 原始 prompt
            optimized_prompts: 优化后的 prompt 列表
            framework: 使用的框架
            model: 使用的模型
            selected_version: 用户选择的版本

        Returns:
            HistoryItem: 创建的历史记录条目
        """
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

        # 加载现有历史
        history = self._load_history()

        # 添加新记录
        history.insert(0, asdict(item))

        # 限制记录数量
        if len(history) > self.max_items:
            history = history[:self.max_items]
            logger.debug(f"历史记录已裁剪至 {self.max_items} 条")

        # 保存
        self._save_history(history)
        logger.info(f"已添加历史记录：{item.id}")

        return item

    def get_all(self, limit: Optional[int] = None) -> List[HistoryItem]:
        """
        获取所有历史记录

        Args:
            limit: 限制数量

        Returns:
            List[HistoryItem]: 历史记录列表
        """
        history = self._load_history()
        items = [HistoryItem(**item) for item in history]

        if limit:
            items = items[:limit]

        return items

    def get_by_id(self, item_id: str) -> Optional[HistoryItem]:
        """
        根据 ID 获取历史记录

        Args:
            item_id: 记录 ID

        Returns:
            HistoryItem or None: 历史记录条目
        """
        history = self._load_history()
        for item in history:
            if item.get("id") == item_id:
                return HistoryItem(**item)
        return None

    def search(self, keyword: str) -> List[HistoryItem]:
        """
        搜索历史记录

        Args:
            keyword: 搜索关键词

        Returns:
            List[HistoryItem]: 匹配的历史记录
        """
        history = self._load_history()
        keyword_lower = keyword.lower()

        items = []
        for item in history:
            original = item.get("original_prompt", "").lower()
            if keyword_lower in original:
                items.append(HistoryItem(**item))
                continue

            # 搜索优化后的 prompt
            for opt in item.get("optimized_prompts", []):
                if keyword_lower in opt.get("prompt", "").lower():
                    items.append(HistoryItem(**item))
                    break

        logger.debug(f"搜索 '{keyword}' 找到 {len(items)} 条记录")
        return items

    def delete(self, item_id: str) -> bool:
        """
        删除历史记录

        Args:
            item_id: 记录 ID

        Returns:
            bool: 是否成功删除
        """
        history = self._load_history()
        original_len = len(history)

        history = [item for item in history if item.get("id") != item_id]

        if len(history) < original_len:
            self._save_history(history)
            logger.info(f"已删除历史记录：{item_id}")
            return True

        return False

    def clear(self) -> int:
        """
        清空所有历史记录

        Returns:
            int: 删除的记录数量
        """
        history = self._load_history()
        count = len(history)
        self._save_history([])
        logger.info(f"已清空历史记录，共删除 {count} 条")
        return count

    def export(self, output_file: str) -> int:
        """
        导出历史记录到文件

        Args:
            output_file: 输出文件路径

        Returns:
            int: 导出的记录数量
        """
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


# 全局历史管理器
global_history = HistoryManager()