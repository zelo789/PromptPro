"""应用层服务测试。"""

from src.app import PromptOptimizationRequest, PromptOptimizationService
from src.history import HistoryManager
from src.requirement import RequirementDoc
from src.strategies import PromptFramework


class FakeClient:
    def __init__(self):
        self.calls = []

    def chat(self, messages):
        self.calls.append(messages)
        return f"optimized::{len(self.calls)}"

    def get_current_model(self):
        return "fake-model"


class FlakyClient(FakeClient):
    def __init__(self, failures):
        super().__init__()
        self.failures = failures

    def chat(self, messages):
        self.calls.append(messages)
        call_no = len(self.calls)
        if call_no in self.failures:
            raise RuntimeError(f"boom-{call_no}")
        return f"optimized::{call_no}"


class FakeHistory:
    def __init__(self):
        self.saved = []

    def add(self, **kwargs):
        self.saved.append(kwargs)


def test_service_builds_effective_prompt_with_requirement_doc():
    service = PromptOptimizationService(client=FakeClient())
    doc = RequirementDoc(
        name="登录系统",
        intro="需要支持邮箱登录",
        tune="输出接口设计",
        file_path="",
        updated_at="",
    )

    effective = service.build_effective_prompt("实现登录模块", requirement_doc=doc)

    assert "[需求文档上下文]" in effective
    assert "登录系统" in effective
    assert "实现登录模块" in effective


def test_service_optimizes_and_returns_framework_reason():
    client = FakeClient()
    service = PromptOptimizationService(client=client)

    result = service.optimize(
        PromptOptimizationRequest(
            original_prompt="写一个 Python 排序函数",
            num_versions=2,
        )
    )

    assert result.framework == PromptFramework.APE
    assert result.framework_reason == "检测到代码/技术关键词"
    assert len(result.optimized_prompts) == 3
    assert result.model == "fake-model"


def test_service_saves_history():
    client = FakeClient()
    history = FakeHistory()
    service = PromptOptimizationService(client=client, history_manager=history)
    result = service.optimize(
        PromptOptimizationRequest(
            original_prompt="写一个故事",
            num_versions=1,
        )
    )

    service.save_history(result)

    assert len(history.saved) == 1
    assert history.saved[0]["framework"] == result.framework.value


def test_service_keeps_successful_versions_when_some_calls_fail():
    client = FlakyClient(failures={2})
    service = PromptOptimizationService(client=client)

    result = service.optimize(
        PromptOptimizationRequest(
            original_prompt="写一个 Python 排序函数",
            num_versions=2,
        )
    )

    assert len(result.optimized_prompts) == 2
    assert result.optimized_prompts[0]["level"] == "light"
    assert result.optimized_prompts[1]["level"] == "framework"
