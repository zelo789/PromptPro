"""CLI 行为测试。"""

from src import cli
from src.config import Config


class FakeLLMClient:
    def __init__(self, config):
        self.config = config
        self.model = ""

    def check_connection(self):
        return True

    def list_models(self):
        return ["model-a", "model-b"]

    def set_model(self, model):
        self.model = model

    def get_current_model(self):
        return self.model


def test_quick_optimize_prefers_configured_default_model(monkeypatch, tmp_path):
    config = Config(config_dir=str(tmp_path), default_model="model-b")

    captured = {}

    class FakeService:
        def __init__(self, client, history_manager):
            captured["client"] = client

        def optimize(self, request):
            captured["request"] = request
            return type(
                "Result",
                (),
                {
                    "optimized_prompts": [{"name": "轻度优化", "prompt": "done"}],
                    "framework": request.selected_framework,
                    "framework_reason": "手动选择",
                    "model": captured["client"].get_current_model(),
                    "original_prompt": request.original_prompt,
                },
            )()

        def save_history(self, result):
            captured["saved"] = result

    monkeypatch.setattr(cli, "LLMClient", FakeLLMClient)
    monkeypatch.setattr(cli, "PromptOptimizationService", FakeService)
    monkeypatch.setattr(cli, "show_optimized_versions", lambda results: captured.setdefault("shown", results))
    monkeypatch.setattr(cli, "print_error", lambda message: (_ for _ in ()).throw(AssertionError(message)))
    monkeypatch.setattr(cli, "global_config", config)

    cli.quick_optimize("写一个测试 prompt")

    assert captured["client"].get_current_model() == "model-b"
