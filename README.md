# PromptPro

PromptPro is a Python CLI for rewriting rough prompts into clearer and more structured prompts.

The current codebase focuses on:

- Interactive prompt optimization in the terminal
- One-shot CLI usage
- Multiple optimization levels
- Framework-based prompt rewriting
- Provider switching across `ollama`, `openai`, `claude`, and `custom`
- Optional history, clipboard copy, clarifying questions, and requirement documents

## Installation

Requirements:

- Python 3.9+

Install the package:

```bash
pip install -e .
```

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Install clipboard support:

```bash
pip install -e ".[clipboard]"
```

## Quick Start

Start interactive mode:

```bash
pp
```

Optimize one prompt directly:

```bash
pp "Write a clearer prompt for designing a login system"
```

Show current config:

```bash
pp --config
```

List models for the active provider:

```bash
pp --models
```

## Providers

PromptPro currently supports four provider modes:

- `ollama`
- `openai`
- `claude`
- `custom`

`custom` is intended for OpenAI-compatible endpoints.

## Environment Variables

Copy `.env.example` and set only the values you actually need.

Common variables:

- `PROMPTPRO_PROVIDER`
- `PROMPTPRO_MODEL`
- `PROMPTPRO_CONFIG_DIR`
- `PROMPTPRO_TEMPERATURE`
- `PROMPTPRO_TIMEOUT`
- `PROMPTPRO_MAX_RETRIES`
- `PROMPTPRO_NUM_VERSIONS`
- `PROMPTPRO_MAX_HISTORY_ITEMS`
- `PROMPTPRO_ENABLE_HISTORY`
- `PROMPTPRO_AUTO_CLIPBOARD`
- `PROMPTPRO_ENABLE_CLARIFY`

Provider-specific variables:

- `OLLAMA_BASE_URL`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `CLAUDE_API_KEY`
- `CLAUDE_BASE_URL`
- `CUSTOM_API_KEY`
- `CUSTOM_BASE_URL`

Example custom provider setup:

```bash
export PROMPTPRO_PROVIDER=custom
export CUSTOM_BASE_URL=https://your-endpoint.example/v1
export CUSTOM_API_KEY=your-key
export PROMPTPRO_MODEL=your-model-name
pp
```

## Prompt Frameworks

The framework selector currently includes:

- `co_star`
- `rtf`
- `create`
- `ape`
- `broke`
- `risen`
- `tag`

Framework recommendation logic lives in `src/strategies.py`.

## Requirement Documents

Requirement documents are stored in `prompts/` and parsed from a small Markdown-like format:

```md
name: Login System
intro: |
  This project is a web application with authentication and audit requirements.
tune: |
  - Prefer implementation-oriented answers.
  - Be explicit about security constraints.
```

Relevant commands:

- `/docs`
- `/load <name>`
- `/doc`
- `/savedoc <name>`
- `/cleardoc`

## CLI Commands

Core interactive commands:

- `/help`
- `/quit`
- `/model`
- `/provider`
- `/frameworks`
- `/config`
- `/history`
- `/temp <value>`
- `/clarify`
- `/docs`
- `/load <name>`
- `/doc`
- `/savedoc <name>`
- `/cleardoc`

## Development

Run tests:

```bash
python -m pytest -q -o addopts=
```

Run formatting and checks:

```bash
black src tests
isort src tests
flake8 src tests
mypy src
```

## Repository Notes

- Main package code lives in `src/`
- Tests live in `tests/`
- Requirement document samples live in `prompts/`
- Provider config examples live in `examples/`

## Contributing

See `CONTRIBUTING.md`.

## License

MIT