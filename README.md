# PromptPro

<p align="center">
  <strong>Professional AI Prompt Optimization CLI Tool</strong><br>
  <em>Make your prompts work better with AI</em>
</p>

<p align="center">
  <a href="https://pypi.org/project/promptpro/">
    <img src="https://img.shields.io/pypi/v/promptpro.svg" alt="PyPI version">
  </a>
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+">
  </a>
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
  </a>
  <a href="https://github.com/zelo789/PromptPro/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/zelo789/PromptPro/ci.yml?branch=main" alt="Build Status">
  </a>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#frameworks">Frameworks</a> •
  <a href="#configuration">Configuration</a>
</p>

---

## Why PromptPro?

Writing effective prompts is the key to getting great results from AI models. PromptPro helps you craft better prompts through:

- **Intelligent Framework Matching** - Automatically recommends the optimal prompt framework based on your content
- **Multi-Level Optimization** - Generate light, moderate, and deep optimization versions for comparison
- **Privacy-First Design** - Runs locally via Ollama, your data never leaves your machine

```
Input:  "写一个排序算法"

Recommended: APE Framework (code/technical tasks)
Matched: Detected keyword '算法' → action-oriented framework

Versions Generated:
  Light:   "请编写一个排序算法，说明其时间复杂度"
  Moderate: "作为一名算法工程师，请编写一个高效的排序算法..."
  Deep:    "角色：你是一名资深算法工程师
            任务：设计并实现一个排序算法
            要求：..."
```

---

## Features

### 7 Professional Prompt Frameworks

| Framework | Key Components | Best For |
|-----------|---------------|----------|
| **CO-STAR** | Context, Objective, Style, Tone, Audience, Response | Complex tasks, professional content |
| **RTF** | Role, Task, Format | Simple tasks, quick prototyping |
| **CREATE** | Character, Request, Examples, Adjustments, Type, Expectations | Creative writing, content creation |
| **APE** | Action, Purpose, Expectation | Code generation, technical tasks |
| **BROKE** | Background, Role, Objective, Key Results, Evolution | Business analysis, strategic planning |
| **RISEN** | Role, Instructions, Steps, End Goal, Narrowing | Multi-step procedures, workflows |
| **TAG** | Task, Action, Goal | Simple queries, daily conversations |

### 3 Optimization Levels

- **Light** - Clarity improvements only, preserves original structure
- **Moderate** - Adds structure, clarity, and context
- **Deep** - Full optimization with all dimensions

### Multi-Provider Support

- **Ollama** (default) - Local, privacy-focused
- **OpenAI API** - GPT-4, GPT-3.5
- **Claude API** - Claude 3.5 Sonnet, Claude 3 Opus
- **Custom API** - Any OpenAI-compatible endpoint

### Additional Features

- Smart framework recommendation based on content analysis
- History management with search and export
- Cross-platform clipboard support
- Interactive and command-line modes
- Configurable temperature and model parameters

---

## Quick Start

### Prerequisites

- Python 3.9 or higher
- For local inference: [Ollama](https://ollama.ai)

### Installation

```bash
# Install PromptPro
pip install promptpro

# For local inference, install and set up Ollama
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Download a model
ollama pull llama3
```

### Usage

```bash
# Interactive mode
pp

# Quick optimization
pp "Write a sorting algorithm"

# Specify model and optimization level
pp -m llama3 -l 2 "Design a login system"

# Output to file
pp -o result.txt "Write a web scraper"
```

---

## Usage

### Interactive Mode

Start the interactive session:

```bash
pp
```

```
PromptPro v0.4.0 - Make your prompts work better with AI
Type /help for commands, or enter text to optimize

Provider: Ollama | Model: llama3

> Write a sorting algorithm

Recommended: APE Framework (code/technical tasks)

Optimizing...

✓ Generated 4 versions

[V1] Light Optimization
     "Please write a sorting algorithm and explain its time complexity..."

[V2] Moderate Optimization
     "As an algorithm engineer, write an efficient sorting algorithm..."

[V3] Deep Optimization
     "Role: You are a senior algorithm engineer
      Task: Design and implement a sorting algorithm..."

[FW] APE Framework
     "Action: Write a sorting algorithm..."

Enter version number to copy (1-4):
```

### CLI Commands

```bash
# View available models
pp --models

# View current configuration
pp --config

# View history
pp --history

# Specify provider (via config)
# Edit ~/.prompt-optimizer/config.json
```

### Interactive Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `/help` | `/h` | Show help |
| `/quit` | `/q` | Exit program |
| `/model` | `/m` | View or switch model |
| `/provider` | `/p` | Switch API provider |
| `/frameworks` | `/f` | View all frameworks |
| `/config` | | Show configuration |
| `/history` | | View optimization history |
| `/temp <value>` | | Set temperature (0.0-2.0) |

### Quick Model Switching

In interactive mode, enter a number to quickly switch models:

```
> 1  # Switch to first model
> 2  # Switch to second model
```

---

## Frameworks

### Framework Selection Decision

```
Your Prompt
    │
    ├─ Contains code/technical keywords? ────→ APE Framework
    │
    ├─ Contains analysis/report/strategy? ───→ BROKE Framework
    │
    ├─ Contains steps/process/workflow? ────→ RISEN Framework
    │
    ├─ Contains creative/writing/story? ─────→ CREATE Framework
    │
    ├─ Long or requires detailed output? ────→ CO-STAR Framework
    │
    ├─ Short and simple (<20 chars)? ────────→ RTF Framework
    │
    └─ Other simple queries ─────────────────→ TAG Framework
```

### Framework Details

#### CO-STAR Framework
**Best for:** Complex tasks requiring comprehensive context

Components:
- **C**ontext - Background information
- **O**bjective - Clear goal definition
- **S**tyle - Writing style specification
- **T**one - Emotional tone setting
- **A**udience - Target reader definition
- **R**esponse - Expected output format

#### APE Framework
**Best for:** Code generation, technical tasks

Components:
- **A**ction - Specific action to perform
- **P**urpose - Intent and objective
- **E**xpectation - Expected results and standards

#### CREATE Framework
**Best for:** Creative writing, content generation

Components:
- **C**haracter - AI role definition
- **R**equest - Task specification
- **E**xamples - Reference examples
- **A**djustments - Optimization direction
- **T**ype - Content type
- **E**xpectations - Desired outcomes

---

## Configuration

Configuration file: `~/.prompt-optimizer/config.json`

### Basic Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `provider` | API provider (ollama/openai/claude/custom) | `ollama` |
| `temperature` | Model temperature | `0.7` |
| `request_timeout` | Request timeout (seconds) | `300` |
| `max_retries` | Maximum retry attempts | `3` |

### Ollama Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `ollama_base_url` | Ollama server URL | `http://localhost:11434` |
| `default_model` | Default model name | auto-select |

### OpenAI Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `openai_api_key` | API key | `` |
| `openai_base_url` | API endpoint | `https://api.openai.com/v1` |
| `openai_model` | Model name | `gpt-4o-mini` |

### Claude Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `claude_api_key` | API key | `` |
| `claude_base_url` | API endpoint | `https://api.anthropic.com` |
| `claude_model` | Model name | `claude-3-5-sonnet-20241022` |

### History Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `enable_history` | Enable history | `true` |
| `max_history_items` | Maximum records | `100` |
| `auto_clipboard` | Auto-copy to clipboard | `true` |

### Switching Providers

Edit `~/.prompt-optimizer/config.json`:

```json
{
  "provider": "openai",
  "openai_api_key": "sk-...",
  "openai_model": "gpt-4o-mini"
}
```

Or use the interactive command:

```
> /provider openai
```

---

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/zelo789/PromptPro.git
cd PromptPro

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting
black src tests
isort src tests

# Type checking
mypy src
```

### Project Structure

```
promptpro/
├── src/
│   ├── __init__.py          # Package exports
│   ├── cli.py               # CLI entry point
│   ├── optimizer.py         # Optimization logic
│   ├── strategies.py        # Framework definitions
│   ├── config.py            # Configuration management
│   ├── ollama_client.py     # LLM API clients
│   ├── history.py           # History management
│   ├── clipboard.py         # Clipboard utilities
│   ├── exceptions.py        # Custom exceptions
│   ├── logger.py            # Logging configuration
│   └── ui/
│       ├── __init__.py
│       ├── console.py       # Console setup
│       ├── panels.py        # Panel components
│       └── tables.py        # Table components
├── tests/
├── pyproject.toml
├── README.md
├── CHANGELOG.md
└── CONTRIBUTING.md
```

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [Ollama](https://ollama.ai) for local LLM inference
- [Rich](https://github.com/Textualize/rich) for beautiful terminal UI
- [Typer](https://typer.tiangolo.com) for CLI framework

---

<p align="center">
  <strong>PromptPro</strong> - Make your prompts work better with AI
</p>