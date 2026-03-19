# PromptPro

<p align="center">
  <strong>Local-first prompt rewriting CLI</strong><br>
  <em>把粗糙输入整理成清晰、结构化、可直接交给大模型执行的 Prompt</em>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+">
  </a>
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
  </a>
  <a href="https://github.com/zelo789/PromptPro/actions/workflows/ci.yml">
    <img src="https://github.com/zelo789/PromptPro/actions/workflows/ci.yml/badge.svg" alt="CI Status">
  </a>
  <a href="https://github.com/zelo789/PromptPro/blob/main/CONTRIBUTING.md">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome">
  </a>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#how-it-works">How It Works</a> •
  <a href="#not-a-fit">Not A Fit</a>
</p>

---

## What It Is

PromptPro focuses on one job:

- Rewrite rough prompts into clearer, more structured prompts.
- Stay local-first with Ollama by default, while keeping other providers configurable.
- Show which parts are rule-based and which parts depend on an LLM response.

It is built for developers and heavy LLM users who prefer a terminal workflow over a SaaS-style prompt builder.

```
Input:  "写一个排序算法"

┌─────────────────────────────────────────────┐
│  需求澄清                                     │
│  为了更好地优化，请回答以下问题：               │
│                                              │
│  1. 需要什么类型的排序算法？（快排/归并/堆排序）│
│     回答: 快速排序，要求稳定                   │
│                                              │
│  2. 数据规模大约多大？                         │
│     回答: 100万条整数                         │
│                                              │
│  3. 对时间复杂度有要求吗？                     │
│     回答: O(n log n)                         │
└─────────────────────────────────────────────┘

Recommended: APE Framework (code/technical tasks)

Versions Generated:
  Light:   "请编写一个排序算法，说明其时间复杂度"
  Moderate: "作为一名算法工程师，请编写一个高效的排序算法..."
  Deep:    "角色：你是一名资深算法工程师
            任务：设计并实现一个排序算法
            要求：..."
```

---

## Features

### Core Workflow

- Prompt rewriting in 3 levels: light, moderate, deep.
- Rule-based framework recommendation for common task types.
- Optional clarifying questions before optimization.
- Local history and requirement-doc context injection.
- Ollama by default, with OpenAI, Claude, and custom OpenAI-compatible endpoints.

### How It Works

- Framework recommendation is rule-based keyword matching plus prompt length heuristics.
- Prompt rewriting itself depends on the configured LLM provider.
- Requirement docs are local Markdown files injected as extra context before optimization.
- History is stored locally under `PROMPTPRO_HOME` or `~/.prompt-optimizer`.

### Why It’s Smaller Now

This project no longer presents itself as an all-in-one AI workflow platform. The current product promise is intentionally narrower than before:

- It does not try to be a universal framework expert.
- It does not claim autonomous requirement understanding.
- It does not replace a full prompt management or team collaboration product.

## Not A Fit

PromptPro is probably not the right tool if you need:

- A polished SaaS collaboration experience for teams.
- Enterprise workflow orchestration or knowledge base integration.
- A no-config GUI-first experience for command-line beginners.

```
你的输入: "帮我写一个登录系统"

┌─ 需求澄清 ─────────────────────────────────────┐
│  为了更好地优化，请回答以下问题：               │
│  （按回车跳过，输入 'skip' 跳过所有）           │
│                                                │
│  1. 登录方式有哪些？（账号密码/手机/第三方）     │
│     回答: 账号密码 + 微信登录                   │
│                                                │
│  2. 需要什么技术栈？                           │
│     回答: Python Flask + JWT                  │
│                                                │
│  3. 有安全要求吗？                             │
│     回答: 需要防暴力破解，密码加密存储          │
└────────────────────────────────────────────────┘

→ 整合后的 Prompt 包含完整需求信息
→ 生成的优化版本更加精准
```

**如何开关：**
- 交互模式输入 `/clarify` 切换开/关
- 配置文件设置 `enable_clarifying_questions: true/false`

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
- **Requirement Documents** - Custom requirement docs for project context
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
PromptPro v0.4.0 - 让 Prompt 更懂 AI
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

Enter version number to copy [dim](1-4)[/dim]:
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
| `/clarify` | | Toggle clarifying questions mode |
| `/docs` | `/d` | List requirement documents |
| `/load <name>` | `/l` | Load a requirement document |
| `/doc` | | Show current document |
| `/savedoc <name>` | | Create new document |
| `/cleardoc` | | Clear current document |

### Quick Model Switching

In interactive mode, enter a number to quickly switch models:

```
> 1  # Switch to first model
> 2  # Switch to second model
```

### 📄 Requirement Documents

Create custom requirement documents to provide project context for prompt optimization.

**Document Format** (Markdown files in `prompts/` directory):

```markdown
name: 登录系统开发文档
intro: |
  这是一个用户登录系统的开发需求，包含账号密码登录和第三方 OAuth 登录。
tune: |
  - 输出代码需要包含详细注释
  - 优先使用 TypeScript
  - 需要考虑安全性（防 SQL 注入、XSS）
```

**Usage:**

```
> /docs              # List all documents
> /load example      # Load document by name or number
> /doc               # Show current document
> /cleardoc          # Clear current document
```

When a document is loaded, its context is automatically integrated into prompt optimization.

---

## Architecture

### Core Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PromptPro 优化流程                             │
└─────────────────────────────────────────────────────────────────────┘

用户输入 Prompt
       │
       ▼
┌──────────────────┐
│ 🎯 需求澄清阶段   │  ◀── 核心创新（默认启用）
│ (Clarifying Q&A) │
└──────────────────┘
       │
       │  AI 生成 3-5 个针对性问题
       │  用户回答补充需求细节
       │  整合为增强后的 Prompt
       ▼
┌──────────────────┐
│ 📊 框架推荐阶段   │
│ (Framework Match)│
└──────────────────┘
       │
       │  分析关键词和内容特征
       │  智能匹配最佳框架
       ▼
┌──────────────────┐
│ ⚡ 多级优化阶段   │
│ (Optimization)   │
└──────────────────┘
       │
       ├─→ Light 版本   (清晰度优化)
       ├─→ Moderate 版本 (结构+上下文)
       ├─→ Deep 版本    (全面优化)
       └─→ Framework 版本 (框架应用)
       │
       ▼
┌──────────────────┐
│ 📋 结果输出       │
│ • 终端展示        │
│ • 剪贴板复制      │
│ • 历史记录        │
└──────────────────┘
```

### Framework Selection Logic

```
Enhanced Prompt (增强后的 Prompt)
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

### 🔐 API Key 配置（推荐环境变量）

**安全最佳实践**：使用环境变量存储 API Key，避免写入配置文件。

```bash
# Linux/macOS - 添加到 ~/.bashrc 或 ~/.zshrc
export OPENAI_API_KEY="sk-your-key"
export CLAUDE_API_KEY="sk-ant-your-key"

# Windows PowerShell
$env:OPENAI_API_KEY = "sk-your-key"

# 或使用 .env 文件（复制 .env.example）
cp .env.example .env
```

| 环境变量 | 说明 |
|----------|------|
| `OPENAI_API_KEY` | OpenAI API Key |
| `CLAUDE_API_KEY` | Claude API Key |
| `CUSTOM_API_KEY` | 自定义 API Key |
| `CUSTOM_BASE_URL` | 自定义 API 端点 |

**优先级**：环境变量 > 配置文件

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
| `openai_api_key` | API key (推荐使用环境变量) | `` |
| `openai_base_url` | API endpoint | `https://api.openai.com/v1` |
| `openai_model` | Model name | `gpt-4o-mini` |

### Claude Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `claude_api_key` | API key (推荐使用环境变量) | `` |
| `claude_base_url` | API endpoint | `https://api.anthropic.com` |
| `claude_model` | Model name | `claude-3-5-sonnet-20241022` |

### History Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `enable_history` | Enable history | `true` |
| `max_history_items` | Maximum records | `100` |
| `auto_clipboard` | Auto-copy to clipboard | `true` |

### Example Configs

项目提供示例配置文件：

```bash
# Ollama 本地
cp examples/config.ollama.json ~/.prompt-optimizer/config.json

# OpenAI
cp examples/config.openai.json ~/.prompt-optimizer/config.json

# Claude
cp examples/config.claude.json ~/.prompt-optimizer/config.json
```

### Switching Providers

Edit `~/.prompt-optimizer/config.json`:

```json
{
  "provider": "openai",
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
.
├── src/
│   ├── __init__.py          # Package exports
│   ├── cli.py               # CLI entry point
│   ├── commands.py          # Interactive commands
│   ├── optimizer.py         # Optimization logic
│   ├── strategies.py        # Framework definitions
│   ├── config.py            # Configuration management
│   ├── ollama_client.py     # LLM API clients
│   ├── history.py           # History management
│   ├── clipboard.py         # Clipboard utilities
│   ├── exceptions.py        # Custom exceptions
│   ├── logger.py            # Logging configuration
│   ├── requirement.py       # Requirement documents
│   └── ui/
│       ├── __init__.py
│       ├── console.py       # Console setup
│       ├── panels.py        # Panel components
│       └── tables.py        # Table components
├── prompts/                 # Requirement documents
│   └── example-login.md     # Example document
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
