"""
策略模块测试
"""
import pytest

from src.strategies import (
    OptimizationLevel,
    PromptFramework,
    FrameworkInfo,
    PromptStrategy,
    get_recommended_framework,
    PROMPT_FRAMEWORKS,
    LEVEL_CONFIGS,
)


class TestOptimizationLevel:
    """优化级别测试"""

    def test_levels_exist(self):
        """测试级别存在"""
        assert OptimizationLevel.LIGHT.value == "light"
        assert OptimizationLevel.MODERATE.value == "moderate"
        assert OptimizationLevel.DEEP.value == "deep"

    def test_level_configs(self):
        """测试级别配置"""
        assert OptimizationLevel.LIGHT in LEVEL_CONFIGS
        assert OptimizationLevel.MODERATE in LEVEL_CONFIGS
        assert OptimizationLevel.DEEP in LEVEL_CONFIGS

        for level in [OptimizationLevel.LIGHT, OptimizationLevel.MODERATE, OptimizationLevel.DEEP]:
            config = LEVEL_CONFIGS[level]
            assert "system_prompt" in config
            assert "description" in config


class TestPromptFramework:
    """Prompt 框架测试"""

    def test_frameworks_exist(self):
        """测试框架存在"""
        assert PromptFramework.CO_STAR.value == "co_star"
        assert PromptFramework.RTF.value == "rtf"
        assert PromptFramework.CREATE.value == "create"
        assert PromptFramework.APE.value == "ape"
        assert PromptFramework.BROKE.value == "broke"
        assert PromptFramework.RISEN.value == "risen"
        assert PromptFramework.TAG.value == "tag"

    def test_all_frameworks_have_info(self):
        """测试所有框架都有信息"""
        for framework in PromptFramework:
            assert framework in PROMPT_FRAMEWORKS
            info = PROMPT_FRAMEWORKS[framework]
            assert isinstance(info, FrameworkInfo)
            assert info.name
            assert info.description
            assert info.system_prompt


class TestFrameworkInfo:
    """框架信息测试"""

    def test_framework_info_structure(self):
        """测试框架信息结构"""
        info = PROMPT_FRAMEWORKS[PromptFramework.CO_STAR]
        assert info.name == "CO-STAR 框架"
        assert len(info.components) == 6
        assert "Context" in info.components[0]


class TestGetRecommendedFramework:
    """框架推荐测试"""

    def test_recommend_for_creative_task(self):
        """测试创意任务推荐"""
        prompts = ["创作一篇文案", "写一首诗歌", "写一个故事"]
        for prompt in prompts:
            framework = get_recommended_framework(prompt)
            assert framework == PromptFramework.CREATE

    def test_recommend_for_code_task(self):
        """测试代码任务推荐"""
        prompts = ["写一个Python函数", "编程实现排序", "开发一个程序", "实现一个算法"]
        for prompt in prompts:
            framework = get_recommended_framework(prompt)
            assert framework == PromptFramework.APE

    def test_recommend_for_business_task(self):
        """测试商业任务推荐"""
        prompts = ["分析市场数据", "写一份商业报告", "制定项目规划"]
        for prompt in prompts:
            framework = get_recommended_framework(prompt)
            assert framework == PromptFramework.BROKE

    def test_recommend_for_simple_task(self):
        """测试简单任务推荐"""
        framework = get_recommended_framework("翻译")
        assert framework == PromptFramework.RTF

    def test_recommend_for_complex_task(self):
        """测试复杂任务推荐"""
        long_prompt = "这是一个非常长的提示词，需要详细地描述各种细节和上下文信息，以便AI能够更好地理解用户的需求并生成高质量的输出结果。"
        framework = get_recommended_framework(long_prompt)
        assert framework == PromptFramework.CO_STAR


class TestPromptStrategy:
    """Prompt 策略测试"""

    def test_strategy_init(self):
        """测试策略初始化"""
        strategy = PromptStrategy()
        assert strategy.frameworks == PROMPT_FRAMEWORKS

    def test_get_framework_info(self):
        """测试获取框架信息"""
        strategy = PromptStrategy()
        info = strategy.get_framework_info(PromptFramework.CO_STAR)
        assert info.name == "CO-STAR 框架"

    def test_get_analysis_prompt(self):
        """测试获取分析 prompt"""
        strategy = PromptStrategy()
        prompt = strategy.get_analysis_prompt()
        assert "分析" in prompt
        assert "清晰度" in prompt