"""Strategy selection and prompt framework metadata for PromptPro."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple

from src.logger import get_logger

logger = get_logger("strategies")

MIN_PROMPT_LENGTH_FOR_RTF = 20
MIN_PROMPT_LENGTH_FOR_CO_STAR = 50

CODE_KEYWORDS: Tuple[str, ...] = (
    "code",
    "coding",
    "programming",
    "developer",
    "function",
    "script",
    "python",
    "javascript",
    "java",
    "typescript",
    "api",
    "algorithm",
    "debug",
    "refactor",
    "代码",
    "编程",
    "函数",
    "脚本",
    "算法",
    "调试",
    "开发",
)
BUSINESS_KEYWORDS: Tuple[str, ...] = (
    "analysis",
    "report",
    "strategy",
    "business",
    "planning",
    "market",
    "分析",
    "报告",
    "策略",
    "商业",
    "规划",
    "市场",
    "项目",
)
PROCEDURE_KEYWORDS: Tuple[str, ...] = (
    "workflow",
    "process",
    "steps",
    "procedure",
    "playbook",
    "流程",
    "步骤",
    "过程",
    "操作",
    "指南",
)
CREATIVE_KEYWORDS: Tuple[str, ...] = (
    "story",
    "poem",
    "creative",
    "copywriting",
    "fiction",
    "advertisement",
    "创作",
    "故事",
    "诗",
    "文案",
    "小说",
    "广告",
    "营销",
)
COMPLEXITY_KEYWORDS: Tuple[str, ...] = (
    "detailed",
    "comprehensive",
    "complete",
    "in-depth",
    "constraint",
    "constraints",
    "tradeoff",
    "architecture",
    "详细",
    "完整",
    "全面",
    "深入",
    "约束",
    "边界",
    "架构",
)


class OptimizationLevel(Enum):
    LIGHT = "light"
    MODERATE = "moderate"
    DEEP = "deep"


class PromptFramework(Enum):
    CO_STAR = "co_star"
    RTF = "rtf"
    CREATE = "create"
    APE = "ape"
    BROKE = "broke"
    RISEN = "risen"
    TAG = "tag"


@dataclass(frozen=True)
class FrameworkInfo:
    name: str
    description: str
    components: List[str]
    recommended_for: str
    system_prompt: str


@dataclass(frozen=True)
class FrameworkRule:
    framework: PromptFramework
    reason: str
    keywords: Tuple[str, ...] = ()
    min_length: int = 0
    max_length: int = 0

    def matches(self, prompt: str, prompt_lower: str) -> bool:
        prompt_length = len(prompt.strip())
        if self.keywords and any(word in prompt_lower for word in self.keywords):
            return True
        if self.min_length and prompt_length >= self.min_length:
            return True
        if self.max_length and prompt_length <= self.max_length:
            return True
        return False


@dataclass(frozen=True)
class FrameworkRecommendation:
    framework: PromptFramework
    reason: str


PROMPT_FRAMEWORKS: Dict[PromptFramework, FrameworkInfo] = {
    PromptFramework.CO_STAR: FrameworkInfo(
        name="CO-STAR framework",
        description="Structured prompt template for complex tasks.",
        components=["Context", "Objective", "Style", "Tone", "Audience", "Response"],
        recommended_for="Complex tasks with clear context and output requirements.",
        system_prompt=(
            "You are a professional prompt optimization assistant. "
            "Rewrite the user's prompt with the CO-STAR structure: "
            "Context, Objective, Style, Tone, Audience, Response. "
            "Return only the optimized prompt."
        ),
    ),
    PromptFramework.RTF: FrameworkInfo(
        name="RTF framework",
        description="Minimal role-task-format structure for simple requests.",
        components=["Role", "Task", "Format"],
        recommended_for="Short and simple prompts.",
        system_prompt=(
            "You are a professional prompt optimization assistant. "
            "Rewrite the user's prompt with the RTF structure: "
            "Role, Task, Format. Return only the optimized prompt."
        ),
    ),
    PromptFramework.CREATE: FrameworkInfo(
        name="CREATE framework",
        description="Creative prompt template for content generation.",
        components=["Character", "Request", "Examples", "Adjustments", "Type", "Expectations"],
        recommended_for="Creative writing and content generation tasks.",
        system_prompt=(
            "You are a professional prompt optimization assistant. "
            "Rewrite the user's prompt with the CREATE structure: "
            "Character, Request, Examples, Adjustments, Type, Expectations. "
            "Return only the optimized prompt."
        ),
    ),
    PromptFramework.APE: FrameworkInfo(
        name="APE framework",
        description="Action-oriented prompt template for execution tasks.",
        components=["Action", "Purpose", "Expectation"],
        recommended_for="Coding, implementation, and technical problem solving.",
        system_prompt=(
            "You are a professional prompt optimization assistant. "
            "Rewrite the user's prompt with the APE structure: "
            "Action, Purpose, Expectation. Return only the optimized prompt."
        ),
    ),
    PromptFramework.BROKE: FrameworkInfo(
        name="BROKE framework",
        description="Result-focused prompt template for business tasks.",
        components=["Background", "Role", "Objective", "Key Results", "Evolution"],
        recommended_for="Business analysis, planning, and reporting.",
        system_prompt=(
            "You are a professional prompt optimization assistant. "
            "Rewrite the user's prompt with the BROKE structure: "
            "Background, Role, Objective, Key Results, Evolution. "
            "Return only the optimized prompt."
        ),
    ),
    PromptFramework.RISEN: FrameworkInfo(
        name="RISEN framework",
        description="Step-driven prompt template for procedural tasks.",
        components=["Role", "Instructions", "Steps", "End Goal", "Narrowing"],
        recommended_for="Workflows, procedures, and multi-step tasks.",
        system_prompt=(
            "You are a professional prompt optimization assistant. "
            "Rewrite the user's prompt with the RISEN structure: "
            "Role, Instructions, Steps, End Goal, Narrowing. "
            "Return only the optimized prompt."
        ),
    ),
    PromptFramework.TAG: FrameworkInfo(
        name="TAG framework",
        description="Compact task-action-goal structure for generic prompts.",
        components=["Task", "Action", "Goal"],
        recommended_for="General-purpose prompts that do not fit other rules.",
        system_prompt=(
            "You are a professional prompt optimization assistant. "
            "Rewrite the user's prompt with the TAG structure: "
            "Task, Action, Goal. Return only the optimized prompt."
        ),
    ),
}

FRAMEWORK_RULES: Sequence[FrameworkRule] = (
    FrameworkRule(
        PromptFramework.APE,
        "Detected coding or technical intent, so APE is the best execution-oriented fit.",
        CODE_KEYWORDS,
    ),
    FrameworkRule(
        PromptFramework.BROKE,
        "Detected business or analysis intent, so BROKE fits result-driven tasks better.",
        BUSINESS_KEYWORDS,
    ),
    FrameworkRule(
        PromptFramework.RISEN,
        "Detected workflow or step-based intent, so RISEN fits procedural tasks better.",
        PROCEDURE_KEYWORDS,
    ),
    FrameworkRule(
        PromptFramework.CREATE,
        "Detected creative writing intent, so CREATE is the best content-oriented fit.",
        CREATIVE_KEYWORDS,
    ),
    FrameworkRule(
        PromptFramework.CO_STAR,
        "Detected a complex or detail-heavy request, so CO-STAR adds stronger structure.",
        COMPLEXITY_KEYWORDS,
        min_length=MIN_PROMPT_LENGTH_FOR_CO_STAR,
    ),
    FrameworkRule(
        PromptFramework.RTF,
        "Detected a very short prompt, so RTF keeps the optimization minimal and direct.",
        max_length=MIN_PROMPT_LENGTH_FOR_RTF,
    ),
)

LEVEL_CONFIGS = {
    OptimizationLevel.LIGHT: {
        "dimensions": ["clarity"],
        "description": "Light optimization focused on clarity.",
        "system_prompt": (
            "You are a professional prompt optimization assistant. "
            "Improve clarity, remove ambiguity, and preserve the original intent. "
            "Return only the optimized prompt."
        ),
    },
    OptimizationLevel.MODERATE: {
        "dimensions": ["clarity", "structure", "context"],
        "description": "Moderate optimization focused on clarity, structure, and context.",
        "system_prompt": (
            "You are a professional prompt optimization assistant. "
            "Improve clarity, add structure, and fill obvious context gaps. "
            "Return only the optimized prompt."
        ),
    },
    OptimizationLevel.DEEP: {
        "dimensions": ["clarity", "structure", "context", "constraints", "examples"],
        "description": "Deep optimization across all prompt dimensions.",
        "system_prompt": (
            "You are a professional prompt optimization assistant. "
            "Rewrite the prompt into a complete, structured, production-ready prompt "
            "with context, task, constraints, and examples when useful. "
            "Return only the optimized prompt."
        ),
    },
}

ANALYSIS_PROMPT = (
    "You are a professional prompt analysis assistant. "
    "Analyze the prompt for clarity, completeness, structure, and executability. "
    "Provide concrete improvement suggestions."
)

LEGACY_REASON_MAP: Dict[PromptFramework, str] = {
    PromptFramework.APE: "检测到代码/技术关键词",
    PromptFramework.BROKE: "检测到商业/分析关键词",
    PromptFramework.RISEN: "检测到流程/步骤关键词",
    PromptFramework.CREATE: "检测到创意/写作关键词",
    PromptFramework.CO_STAR: "检测到复杂或详细需求",
    PromptFramework.RTF: "检测到简单短 prompt",
    PromptFramework.TAG: "通用任务，使用默认框架",
}


def recommend_framework(prompt: str) -> FrameworkRecommendation:
    prompt_lower = prompt.lower()
    for rule in FRAMEWORK_RULES:
        if rule.matches(prompt, prompt_lower):
            return FrameworkRecommendation(rule.framework, rule.reason)
    return FrameworkRecommendation(
        PromptFramework.TAG,
        "No strong specialized signal was detected, so TAG is the default general-purpose fit.",
    )


def get_recommended_framework(prompt: str) -> PromptFramework:
    return recommend_framework(prompt).framework


def get_framework_match_reason(prompt: str, framework: Optional[PromptFramework] = None) -> str:
    if framework is not None:
        return LEGACY_REASON_MAP.get(framework, LEGACY_REASON_MAP[PromptFramework.TAG])
    return recommend_framework(prompt).reason


def get_framework_recommendation(prompt: str) -> Tuple[PromptFramework, str]:
    framework = get_recommended_framework(prompt)
    return framework, LEGACY_REASON_MAP.get(framework, LEGACY_REASON_MAP[PromptFramework.TAG])


class PromptStrategy:
    def __init__(self) -> None:
        self.frameworks: Dict[PromptFramework, FrameworkInfo] = PROMPT_FRAMEWORKS
        self._analysis_prompt = ANALYSIS_PROMPT

    def get_framework_info(self, framework: PromptFramework) -> FrameworkInfo:
        return self.frameworks[framework]

    def get_analysis_prompt(self) -> str:
        return self._analysis_prompt

    def recommend_framework(self, prompt: str) -> FrameworkRecommendation:
        return recommend_framework(prompt)

    def get_all_frameworks(self) -> Dict[PromptFramework, FrameworkInfo]:
        return self.frameworks


global_strategy = PromptStrategy()
