"""Prompt analysis and optimization orchestration."""

from __future__ import annotations

from typing import Optional

from src.exceptions import ErrorCode, OptimizerError
from src.logger import get_logger
from src.ollama_client import LLMClient
from src.strategies import LEVEL_CONFIGS, OptimizationLevel, PromptStrategy

logger = get_logger("optimizer")


class PromptOptimizer:
    """High-level helper for prompt analysis and optimization."""

    def __init__(self, client: Optional[LLMClient] = None):
        self.client = client or LLMClient()
        self.strategy = PromptStrategy()
        logger.debug("PromptOptimizer initialized.")

    def analyze(self, prompt: str) -> str:
        """Analyze a prompt and return improvement suggestions."""
        messages = [
            {"role": "system", "content": self.strategy.get_analysis_prompt()},
            {"role": "user", "content": f"Please analyze this prompt:\n\n{prompt}"},
        ]

        try:
            return self.client.chat(messages)
        except Exception as exc:
            logger.error("Prompt analysis failed: %s", exc)
            raise OptimizerError(
                f"Prompt analysis failed: {exc}",
                error_code=ErrorCode.OPTIMIZER_FAILED,
                details=str(exc),
            ) from exc

    def optimize(
        self,
        prompt: str,
        level: OptimizationLevel = OptimizationLevel.MODERATE,
    ) -> str:
        """Optimize a prompt using the requested optimization level."""
        config = LEVEL_CONFIGS[level]
        messages = [
            {"role": "system", "content": config["system_prompt"]},
            {"role": "user", "content": f"Please optimize this prompt:\n\n{prompt}"},
        ]

        try:
            return self.client.chat(messages)
        except Exception as exc:
            logger.error("Prompt optimization failed: %s", exc)
            raise OptimizerError(
                f"Prompt optimization failed: {exc}",
                error_code=ErrorCode.OPTIMIZER_FAILED,
                details=str(exc),
            ) from exc
