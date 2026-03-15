"""
Prompt 优化核心逻辑模块

提供 Prompt 质量分析和多级别优化功能。
"""
import logging
from typing import Optional

from src.ollama_client import LLMClient
from src.strategies import PromptStrategy, OptimizationLevel, LEVEL_CONFIGS
from src.exceptions import OptimizerError, ErrorCode
from src.logger import get_logger

logger: logging.Logger


class PromptOptimizer:
    """Prompt 优化器"""

    def __init__(self, client: Optional[LLMClient] = None):
        """初始化优化器"""
        global logger
        logger = get_logger("optimizer")

        self.client = client or LLMClient()
        self.strategy = PromptStrategy()
        logger.debug("PromptOptimizer 初始化完成")

    def analyze(self, prompt: str) -> str:
        """
        分析 prompt 质量

        Args:
            prompt: 待分析的 prompt

        Returns:
            str: 分析结果

        Raises:
            OptimizerError: 分析失败时抛出
        """
        logger.info(f"开始分析 prompt (长度：{len(prompt)})")

        messages = [
            {"role": "system", "content": self.strategy.get_analysis_prompt()},
            {"role": "user", "content": f"请分析以下 prompt:\n\n{prompt}"}
        ]

        try:
            result = self.client.chat(messages)
            logger.info("Prompt 分析完成")
            return result
        except Exception as e:
            logger.error(f"Prompt 分析失败：{e}")
            raise OptimizerError(
            f"Prompt 分析失败：{e}",
            error_code=ErrorCode.OPTIMIZER_FAILED,
            details=str(e),
        )

    def optimize(
        self,
        prompt: str,
        level: OptimizationLevel = OptimizationLevel.MODERATE,
    ) -> str:
        """
        优化 prompt

        Args:
            prompt: 待优化的 prompt
            level: 优化级别，默认为 MODERATE

        Returns:
            str: 优化后的 prompt

        Raises:
            OptimizerError: 优化失败时抛出
        """
        logger.info(f"开始优化 prompt (级别：{level.value}, 长度：{len(prompt)})")

        config = LEVEL_CONFIGS[level]

        messages = [
            {"role": "system", "content": config["system_prompt"]},
            {"role": "user", "content": f"请优化以下 prompt:\n\n{prompt}"}
        ]

        try:
            result = self.client.chat(messages)
            logger.info(f"Prompt 优化完成 (级别：{level.value})")
            return result
        except Exception as e:
            logger.error(f"Prompt 优化失败：{e}")
            raise OptimizerError(
            f"Prompt 优化失败：{e}",
            error_code=ErrorCode.OPTIMIZER_FAILED,
            details=str(e),
        )
