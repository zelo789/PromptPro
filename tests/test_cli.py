"""Regression tests for CLI orchestration helpers."""

from pathlib import Path

import src.cli as cli
from src.config import Config


class DummyClient:
    def __init__(self, models=None, current_model="", connected=True):
        self.models = models or []
        self.current_model = current_model
        self.connected = connected
        self.temperature = 0.7
        self.set_model_calls = []
        self.chat_responses = []
        self.chat_calls = []

    def check_connection(self):
        return self.connected

    def list_models(self):
        return self.models

    def get_available_models(self):
        return self.models

    def set_model(self, model):
        self.current_model = model
        self.set_model_calls.append(model)
        return True

    def get_current_model(self):
        return self.current_model

    def set_temperature(self, temperature):
        self.temperature = temperature

    def chat(self, messages):
        self.chat_calls.append(messages)
        if self.chat_responses:
            return self.chat_responses.pop(0)
        return "optimized"


def test_generate_clarifying_questions_strips_numbering_and_comments():
    client = DummyClient()
    client.chat_responses = ["1. Who is the audience?\n2) What constraints matter?\n# ignored"]

    result = cli.generate_clarifying_questions("Improve this prompt", client)

    assert result == ["Who is the audience?", "What constraints matter?"]


def test_connect_client_uses_requested_ollama_model_when_available(monkeypatch):
    monkeypatch.setattr(cli.global_config, "provider", "ollama")
    monkeypatch.setattr(cli.global_config, "default_model", "llama3")
    client = DummyClient(models=["qwen2", "llama3"], connected=True)

    assert cli._connect_client(client, requested_model="qwen2") is True
    assert client.set_model_calls == ["qwen2"]


def test_connect_client_falls_back_to_first_ollama_model(monkeypatch):
    monkeypatch.setattr(cli.global_config, "provider", "ollama")
    monkeypatch.setattr(cli.global_config, "default_model", "missing-model")
    client = DummyClient(models=["qwen2", "llama3"], connected=True)

    assert cli._connect_client(client) is True
    assert client.set_model_calls == ["qwen2"]


def test_handle_slash_command_reports_unknown_command(monkeypatch):
    captured = []
    monkeypatch.setattr(cli, "print_error", captured.append)

    cli.handle_slash_command("/unknown", DummyClient())

    assert captured == ["Unknown command: /unknown"]


def test_get_interactive_num_versions_clamps_to_supported_range(monkeypatch):
    monkeypatch.setattr(cli.global_config, "num_versions", 99)
    assert cli._get_interactive_num_versions() == 3

    monkeypatch.setattr(cli.global_config, "num_versions", 0)
    assert cli._get_interactive_num_versions() == 1


def test_quick_optimize_writes_output_file(monkeypatch, tmp_path):
    output_path = tmp_path / "optimized.txt"
    dummy_client = DummyClient(models=["demo-model"], current_model="demo-model", connected=True)

    monkeypatch.setattr(cli, "LLMClient", lambda config: dummy_client)
    monkeypatch.setattr(cli, "show_optimized_versions", lambda results: None)
    monkeypatch.setattr(
        cli,
        "generate_optimized_versions",
        lambda prompt, client, num_versions, framework: [
            {
                "level": "light",
                "name": "Light optimization",
                "description": "Light pass",
                "prompt": "optimized prompt",
            }
        ],
    )
    monkeypatch.setattr(cli.global_config, "provider", "custom")
    monkeypatch.setattr(cli.global_config, "enable_history", False)
    monkeypatch.setattr(cli.global_config, "custom_model", "demo-model")
    monkeypatch.setattr(cli.global_config, "default_model", "demo-model")

    cli.quick_optimize("test prompt", output=str(output_path))

    content = output_path.read_text(encoding="utf-8")
    assert "optimized prompt" in content
    assert "Light optimization" in content
