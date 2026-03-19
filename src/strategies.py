"""
Prompt 优化策略模块

定义 Prompt 优化的核心策略和框架，包括：
- 7 种主流 Prompt 框架（CO-STAR、RTF、CREATE、APE、BROKE、RISEN、TAG）
- 3 种优化级别（轻度、中度、深度）
- 智能框架推荐逻辑
- Prompt 质量分析指令

每个框架包含：
- 框架名称和描述
- 组成要素列表
- 适用场景说明
- 用于生成优化版本的 system prompt

Example:
    ```python
    from src.strategies import PromptStrategy, PromptFramework, OptimizationLevel

    strategy = PromptStrategy()

    # 获取所有框架
    frameworks = strategy.get_all_frameworks()

    # 根据 prompt 推荐框架
    recommendation = strategy.recommend_framework("帮我写一个 Python 函数")

    # 获取特定框架信息
    info = strategy.get_framework_info(PromptFramework.CO_STAR)
    ```
"""
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

from src.logger import get_logger

logger = get_logger("strategies")


# ==================== 常量定义 ====================
MIN_PROMPT_LENGTH_FOR_RTF = 20
"""使用 RTF 框架的最大 prompt 长度（小于此值）"""

MAX_PROMPT_LENGTH_FOR_CO_STAR = 50
"""使用 CO-STAR 框架的最小 prompt 长度（大于此值）"""


class OptimizationLevel(Enum):
    """优化级别枚举"""
    LIGHT = "light"
    MODERATE = "moderate"
    DEEP = "deep"


class PromptFramework(Enum):
    """Prompt 框架枚举"""
    CO_STAR = "co_star"
    RTF = "rtf"
    CREATE = "create"
    APE = "ape"
    BROKE = "broke"
    RISEN = "risen"
    TAG = "tag"


@dataclass
class FrameworkInfo:
    """框架信息数据类"""
    name: str
    description: str
    components: List[str]
    recommended_for: str
    system_prompt: str


# ==================== Prompt 框架定义 ====================
PROMPT_FRAMEWORKS = {
    PromptFramework.CO_STAR: FrameworkInfo(
        name="CO-STAR 框架",
        description="全面的情境化提示框架，适合复杂任务",
        components=[
            "C - Context (上下文): 提供任务背景信息",
            "O - Objective (目标): 明确任务目标",
            "S - Style (风格): 指定写作风格",
            "T - Tone (语气): 设定情感基调",
            "A - Audience (受众): 定义目标读者",
            "R - Response (响应): 指定期望的输出格式",
        ],
        recommended_for="复杂任务、需要详细上下文的场景、专业内容生成",
        system_prompt="""你是一个专业的 Prompt 优化专家，使用 CO-STAR 框架优化用户的 prompt。

CO-STAR 框架包含：
- Context (上下文): 提供任务背景信息
- Objective (目标): 明确任务目标
- Style (风格): 指定写作风格
- Tone (语气): 设定情感基调
- Audience (受众): 定义目标读者
- Response (响应): 指定期望的输出格式

请根据用户原始 prompt，使用 CO-STAR 框架生成一个结构完整、信息丰富的优化版本。
输出只包含优化后的 prompt，不要添加解释。""",
    ),
    PromptFramework.RTF: FrameworkInfo(
        name="RTF 框架",
        description="简单直接的三要素框架，适合快速任务",
        components=[
            "R - Role (角色): AI 应该扮演的角色",
            "T - Task (任务): 需要完成的具体任务",
            "F - Format (格式): 期望的输出格式",
        ],
        recommended_for="简单任务、快速原型、日常查询",
        system_prompt="""你是一个专业的 Prompt 优化专家，使用 RTF 框架优化用户的 prompt。

RTF 框架包含：
- Role (角色): AI 应该扮演的角色
- Task (任务): 需要完成的具体任务
- Format (格式): 期望的输出格式

请根据用户原始 prompt，使用 RTF 框架生成一个简洁清晰的优化版本。
输出只包含优化后的 prompt，不要添加解释。""",
    ),
    PromptFramework.CREATE: FrameworkInfo(
        name="CREATE 框架",
        description="创造性任务专用框架，适合内容创作",
        components=[
            "C - Character (角色): 定义 AI 角色",
            "R - Request (请求): 明确任务请求",
            "E - Examples (示例): 提供参考示例",
            "A - Adjustments (调整): 指定调整和优化方向",
            "T - Type (类型): 定义内容类型",
            "E - Expectations (期望): 说明期望结果",
        ],
        recommended_for="创意写作、内容创作、营销文案、故事生成",
        system_prompt="""你是一个专业的 Prompt 优化专家，使用 CREATE 框架优化用户的 prompt。

CREATE 框架包含：
- Character (角色): 定义 AI 角色
- Request (请求): 明确任务请求
- Examples (示例): 提供参考示例
- Adjustments (调整): 指定调整和优化方向
- Type (类型): 定义内容类型
- Expectations (期望): 说明期望结果

请根据用户原始 prompt，使用 CREATE 框架生成一个富有创意的优化版本。
输出只包含优化后的 prompt，不要添加解释。""",
    ),
    PromptFramework.APE: FrameworkInfo(
        name="APE 框架",
        description="行动导向框架，适合执行类任务",
        components=[
            "A - Action (行动): 需要执行的具体行动",
            "P - Purpose (目的): 行动的目的和意图",
            "E - Expectation (期望): 期望的结果和标准",
        ],
        recommended_for="代码生成、数据分析、问题解决、执行类任务",
        system_prompt="""你是一个专业的 Prompt 优化专家，使用 APE 框架优化用户的 prompt。

APE 框架包含：
- Action (行动): 需要执行的具体行动
- Purpose (目的): 行动的目的和意图
- Expectation (期望): 期望的结果和标准

请根据用户原始 prompt，使用 APE 框架生成一个行动导向的优化版本。
输出只包含优化后的 prompt，不要添加解释。""",
    ),
    PromptFramework.BROKE: FrameworkInfo(
        name="BROKE 框架",
        description="结果导向框架，适合商业和专业场景",
        components=[
            "B - Background (背景): 任务背景信息",
            "R - Role (角色): AI 的角色定位",
            "O - Objective (目标): 明确的目标",
            "K - Key Results (关键结果): 需要达成的具体结果",
            "E - Evolution (改进): 进化和优化方向",
        ],
        recommended_for="商业分析、项目规划、专业报告、策略制定",
        system_prompt="""你是一个专业的 Prompt 优化专家，使用 BROKE 框架优化用户的 prompt。

BROKE 框架包含：
- Background (背景): 任务背景信息
- Role (角色): AI 的角色定位
- Objective (目标): 明确的目标
- Key Results (关键结果): 需要达成的具体结果
- Evolution (改进): 进化和优化方向

请根据用户原始 prompt，使用 BROKE 框架生成一个专业的优化版本。
输出只包含优化后的 prompt，不要添加解释。""",
    ),
    PromptFramework.RISEN: FrameworkInfo(
        name="RISEN 框架",
        description="分步执行框架，适合多步骤复杂任务",
        components=[
            "R - Role (角色): AI 的角色",
            "I - Instructions (指令): 详细的步骤指令",
            "S - Steps (步骤): 分解的执行步骤",
            "E - End Goal (最终目标): 最终要达成的目标",
            "N - Narrowing (约束): 限制和边界条件",
        ],
        recommended_for="多步骤任务、流程执行、复杂问题解决",
        system_prompt="""你是一个专业的 Prompt 优化专家，使用 RISEN 框架优化用户的 prompt。

RISEN 框架包含：
- Role (角色): AI 的角色
- Instructions (指令): 详细的步骤指令
- Steps (步骤): 分解的执行步骤
- End Goal (最终目标): 最终要达成的目标
- Narrowing (约束): 限制和边界条件

请根据用户原始 prompt，使用 RISEN 框架生成一个结构化的优化版本。
输出只包含优化后的 prompt，不要添加解释。""",
    ),
    PromptFramework.TAG: FrameworkInfo(
        name="TAG 框架",
        description="极简框架，适合快速简单的查询",
        components=[
            "T - Task (任务): 简单描述任务",
            "A - Action (行动): 需要执行的行动",
            "G - Goal (目标): 要达成的目标",
        ],
        recommended_for="简单查询、快速问答、日常对话",
        system_prompt="""你是一个专业的 Prompt 优化专家，使用 TAG 框架优化用户的 prompt。

TAG 框架包含：
- Task (任务): 简单描述任务
- Action (行动): 需要执行的行动
- Goal (目标): 要达成的目标

请根据用户原始 prompt，使用 TAG 框架生成一个简洁的优化版本。
输出只包含优化后的 prompt，不要添加解释。""",
    ),
}


def get_recommended_framework(prompt: str) -> PromptFramework:
    """
    根据 prompt 内容推荐合适的框架

    Args:
        prompt: 用户输入的原始 prompt

    Returns:
        PromptFramework: 推荐的框架
    """
    framework, _ = get_framework_recommendation(prompt)
    return framework


def get_framework_recommendation(prompt: str) -> Tuple[PromptFramework, str]:
    """返回推荐框架和推荐原因。"""
    prompt_lower = prompt.lower()

    code_keywords = ["代码", "编程", "函数", "程序", "开发", "技术", "python", "javascript", "java", "算法", "排序", "爬虫"]
    if any(word in prompt_lower for word in code_keywords):
        logger.debug("推荐框架：APE (代码/技术类任务)")
        return PromptFramework.APE, "检测到代码/技术关键词"

    if any(word in prompt_lower for word in ["分析", "报告", "商业", "策略", "规划", "项目"]):
        logger.debug("推荐框架：BROKE (商业/专业任务)")
        return PromptFramework.BROKE, "检测到商业分析关键词"

    if any(word in prompt_lower for word in ["步骤", "流程", "过程", "顺序", "逐步"]):
        logger.debug("推荐框架：RISEN (多步骤任务)")
        return PromptFramework.RISEN, "检测到流程关键词"

    creative_keywords = ["创作", "故事", "文案", "诗歌", "广告", "营销", "小说", "剧本", "写"]
    if any(word in prompt_lower for word in creative_keywords):
        logger.debug("推荐框架：CREATE (创意类任务)")
        return PromptFramework.CREATE, "检测到创意关键词"

    if len(prompt) > MAX_PROMPT_LENGTH_FOR_CO_STAR or any(
        word in prompt_lower for word in ["详细", "完整", "全面", "深入"]
    ):
        logger.debug("推荐框架：CO-STAR (复杂任务)")
        return PromptFramework.CO_STAR, "检测到复杂任务特征"

    if len(prompt) < MIN_PROMPT_LENGTH_FOR_RTF:
        logger.debug("推荐框架：RTF (简单任务)")
        return PromptFramework.RTF, "简短 prompt"

    logger.debug("推荐框架：TAG (默认)")
    return PromptFramework.TAG, "通用查询"


def get_framework_match_reason(prompt: str, framework: PromptFramework) -> str:
    """兼容旧接口，返回共享推荐原因。"""
    recommended, reason = get_framework_recommendation(prompt)
    if framework == recommended:
        return reason
    return f"手动选择 {PROMPT_FRAMEWORKS[framework].name}"


# ==================== 优化级别配置 ====================
LEVEL_CONFIGS = {
    OptimizationLevel.LIGHT: {
        "dimensions": ["clarity"],
        "description": "轻度优化 - 主要改善清晰度，保持原有结构",
        "system_prompt": """你是一个专业的 Prompt 优化助手。
你的任务是轻度优化用户的 prompt，主要是：
1. 消除歧义，提高清晰度
2. 修正语法和表述问题
3. 保持原有的结构和风格

请直接输出优化后的 prompt，不要添加额外解释。""",
    },
    OptimizationLevel.MODERATE: {
        "dimensions": ["clarity", "structure", "context"],
        "description": "中度优化 - 改善结构、清晰度和上下文",
        "system_prompt": """你是一个专业的 Prompt 优化助手。
你的任务是中度优化用户的 prompt，包括：
1. 消除歧义，提高清晰度
2. 添加清晰的结构（角色、任务、格式）
3. 补充必要的上下文信息
4. 保持合理简洁

请输出优化后的 prompt，可以包含简要的结构标记。""",
    },
    OptimizationLevel.DEEP: {
        "dimensions": ["clarity", "structure", "context", "constraints", "examples"],
        "description": "深度优化 - 全面优化，包含所有维度",
        "system_prompt": """你是一个专业的 Prompt 优化专家。
你的任务是深度优化用户的 prompt，进行全面改进：
1. 消除所有歧义，使意图极其明确
2. 添加完整的结构（角色定义、任务描述、上下文、输出格式、约束条件）
3. 补充充分的背景信息和上下文
4. 添加明确的约束和边界
5. 如适用，包含示例或模板

请输出一个完整、专业、可直接使用的高质量 prompt。""",
    },
}


class PromptStrategy:
    """Prompt 优化策略类"""

    def __init__(self) -> None:
        """初始化策略实例"""
        self.frameworks: Dict[PromptFramework, FrameworkInfo] = PROMPT_FRAMEWORKS
        self._analysis_prompt: str = """你是一个专业的 Prompt 分析专家。
请分析用户提供的 prompt 质量，包括：
1. 清晰度：是否有歧义，表述是否清晰
2. 完整性：是否缺少必要的上下文或约束
3. 结构：是否有清晰的结构
4. 可执行性：AI 是否能明确理解并执行

请给出具体的分析结果和改进建议。"""
        logger.debug("PromptStrategy 初始化完成")

    def get_framework_info(self, framework: PromptFramework) -> FrameworkInfo:
        """获取指定框架的详细信息"""
        logger.debug(f"获取框架信息：{framework.value}")
        return self.frameworks[framework]

    def get_analysis_prompt(self) -> str:
        """获取分析 prompt"""
        return self._analysis_prompt


# ==================== 全局策略实例 ====================
global_strategy = PromptStrategy()
"""全局策略单例，可直接导入使用"""
