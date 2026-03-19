"""应用层服务。"""

from typing import List, Dict, Optional

from src.app.models import PromptOptimizationRequest, PromptOptimizationResult
from src.history import HistoryManager
from src.logger import get_logger
from src.requirement import RequirementDoc
from src.strategies import (
    LEVEL_CONFIGS,
    PROMPT_FRAMEWORKS,
    OptimizationLevel,
    PromptFramework,
    get_framework_recommendation,
)

logger = get_logger("prompt_optimization_service")


class PromptOptimizationService:
    """统一编排 prompt 重写、推荐和历史保存。"""

    def __init__(self, client, history_manager: Optional[HistoryManager] = None):
        self.client = client
        self.history_manager = history_manager

    def build_effective_prompt(
        self,
        prompt: str,
        requirement_doc: Optional[RequirementDoc] = None,
        clarified_prompt: Optional[str] = None,
    ) -> str:
        """合成最终用于优化的 prompt。"""
        effective_prompt = prompt

        if requirement_doc:
            doc_context = (
                "[需求文档上下文]\n"
                f"文档名称: {requirement_doc.name}\n"
                f"背景介绍: {requirement_doc.intro}\n"
                f"调优要求: {requirement_doc.tune}\n"
            )
            effective_prompt = f"{doc_context}\n[用户原始需求]\n{effective_prompt}"

        if clarified_prompt:
            effective_prompt = clarified_prompt

        return effective_prompt

    def generate_optimized_versions(
        self,
        prompt: str,
        num_versions: int = 3,
        framework: Optional[PromptFramework] = None,
    ) -> List[Dict[str, str]]:
        """生成多个优化版本。"""
        results: List[Dict[str, str]] = []
        levels = list(OptimizationLevel)
        level_names = {
            OptimizationLevel.LIGHT: "轻度优化",
            OptimizationLevel.MODERATE: "中度优化",
            OptimizationLevel.DEEP: "深度优化",
        }

        for level in levels[:num_versions]:
            config = LEVEL_CONFIGS[level]
            messages = [
                {"role": "system", "content": config["system_prompt"]},
                {"role": "user", "content": f"请优化以下 prompt:\n\n{prompt}"},
            ]
            try:
                optimized = self.client.chat(messages)
                results.append(
                    {
                        "level": level.value,
                        "name": level_names[level],
                        "description": config["description"],
                        "prompt": optimized,
                    }
                )
            except Exception as exc:
                logger.warning("生成 %s 版本失败: %s", level_names[level], exc)

        if framework:
            fw_info = PROMPT_FRAMEWORKS[framework]
            messages = [
                {"role": "system", "content": fw_info.system_prompt},
                {"role": "user", "content": f"请优化以下 prompt:\n\n{prompt}"},
            ]
            try:
                optimized = self.client.chat(messages)
                results.append(
                    {
                        "level": "framework",
                        "name": fw_info.name,
                        "description": fw_info.description,
                        "prompt": optimized,
                    }
                )
            except Exception as exc:
                logger.warning("生成 %s 版本失败: %s", fw_info.name, exc)

        return results

    def optimize(self, request: PromptOptimizationRequest) -> PromptOptimizationResult:
        """执行完整优化流程。"""
        effective_prompt = self.build_effective_prompt(
            prompt=request.original_prompt,
            requirement_doc=request.requirement_doc,
            clarified_prompt=request.clarified_prompt,
        )
        framework, reason = (
            (request.selected_framework, f"手动选择 {PROMPT_FRAMEWORKS[request.selected_framework].name}")
            if request.selected_framework
            else get_framework_recommendation(effective_prompt)
        )

        optimized_prompts = self.generate_optimized_versions(
            prompt=effective_prompt,
            num_versions=request.num_versions,
            framework=framework,
        )

        result = PromptOptimizationResult(
            original_prompt=request.original_prompt,
            effective_prompt=effective_prompt,
            framework=framework,
            framework_reason=reason,
            optimized_prompts=optimized_prompts,
            model=self.client.get_current_model(),
        )
        return result

    def save_history(self, result: PromptOptimizationResult) -> None:
        """保存优化历史。"""
        if not self.history_manager:
            return
        self.history_manager.add(
            original_prompt=result.original_prompt,
            optimized_prompts=result.optimized_prompts,
            framework=result.framework.value,
            model=result.model,
        )
