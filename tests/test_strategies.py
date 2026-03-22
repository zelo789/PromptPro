"""Tests for prompt strategy selection and metadata."""

from src.strategies import (
    FRAMEWORK_RULES,
    LEVEL_CONFIGS,
    FrameworkInfo,
    OptimizationLevel,
    PROMPT_FRAMEWORKS,
    PromptFramework,
    PromptStrategy,
    get_framework_match_reason,
    get_recommended_framework,
    recommend_framework,
)


class TestOptimizationLevel:
    def test_levels_exist(self):
        assert OptimizationLevel.LIGHT.value == "light"
        assert OptimizationLevel.MODERATE.value == "moderate"
        assert OptimizationLevel.DEEP.value == "deep"

    def test_level_configs(self):
        for level in OptimizationLevel:
            config = LEVEL_CONFIGS[level]
            assert "system_prompt" in config
            assert "description" in config


class TestPromptFramework:
    def test_frameworks_exist(self):
        assert PromptFramework.CO_STAR.value == "co_star"
        assert PromptFramework.RTF.value == "rtf"
        assert PromptFramework.CREATE.value == "create"
        assert PromptFramework.APE.value == "ape"
        assert PromptFramework.BROKE.value == "broke"
        assert PromptFramework.RISEN.value == "risen"
        assert PromptFramework.TAG.value == "tag"

    def test_all_frameworks_have_info(self):
        for framework in PromptFramework:
            assert framework in PROMPT_FRAMEWORKS
            info = PROMPT_FRAMEWORKS[framework]
            assert isinstance(info, FrameworkInfo)
            assert info.name
            assert info.description
            assert info.system_prompt


class TestFrameworkInfo:
    def test_framework_info_structure(self):
        info = PROMPT_FRAMEWORKS[PromptFramework.CO_STAR]
        assert info.name == "CO-STAR framework"
        assert len(info.components) == 6
        assert "Context" in info.components[0]


class TestRecommendation:
    def test_recommend_for_creative_task(self):
        for prompt in ["创作一篇文案", "写一个故事", "写一首诗"]:
            assert get_recommended_framework(prompt) == PromptFramework.CREATE

    def test_recommend_for_code_task(self):
        for prompt in ["写一个 Python 函数", "编程实现排序", "开发一个脚本"]:
            assert get_recommended_framework(prompt) == PromptFramework.APE

    def test_recommend_for_business_task(self):
        for prompt in ["分析市场数据", "写一份商业报告", "制定项目规划"]:
            assert get_recommended_framework(prompt) == PromptFramework.BROKE

    def test_recommend_for_simple_task(self):
        assert get_recommended_framework("翻译") == PromptFramework.RTF

    def test_recommend_for_complex_task(self):
        prompt = "请给我一个详细完整的系统设计方案，包含上下文、约束、边界和输出格式。"
        assert get_recommended_framework(prompt) == PromptFramework.CO_STAR

    def test_reason_is_returned_from_same_rule_system(self):
        recommendation = recommend_framework("写一个 Python 排序算法")
        assert recommendation.framework == PromptFramework.APE
        assert "technical" in recommendation.reason.lower()
        assert get_framework_match_reason("写一个 Python 排序算法") == recommendation.reason

    def test_rules_are_defined(self):
        assert len(FRAMEWORK_RULES) >= 5


class TestPromptStrategy:
    def test_strategy_init(self):
        strategy = PromptStrategy()
        assert strategy.frameworks == PROMPT_FRAMEWORKS

    def test_get_framework_info(self):
        strategy = PromptStrategy()
        info = strategy.get_framework_info(PromptFramework.CO_STAR)
        assert info.name == "CO-STAR framework"

    def test_get_analysis_prompt(self):
        strategy = PromptStrategy()
        prompt = strategy.get_analysis_prompt()
        assert "Analyze the prompt" in prompt
        assert "clarity" in prompt

    def test_get_all_frameworks(self):
        strategy = PromptStrategy()
        frameworks = strategy.get_all_frameworks()
        assert PromptFramework.TAG in frameworks
