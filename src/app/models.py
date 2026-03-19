"""应用层数据模型。"""

from dataclasses import dataclass
from typing import List, Optional, Dict

from src.strategies import PromptFramework
from src.requirement import RequirementDoc


@dataclass
class PromptOptimizationRequest:
    """Prompt 优化请求。"""

    original_prompt: str
    num_versions: int = 3
    selected_framework: Optional[PromptFramework] = None
    requirement_doc: Optional[RequirementDoc] = None
    clarified_prompt: Optional[str] = None


@dataclass
class PromptOptimizationResult:
    """Prompt 优化结果。"""

    original_prompt: str
    effective_prompt: str
    framework: PromptFramework
    framework_reason: str
    optimized_prompts: List[Dict[str, str]]
    model: Optional[str] = None
