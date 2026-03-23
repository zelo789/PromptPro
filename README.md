# PromptPro

将粗糙的提示词优化为更清晰、结构化的提示词。

## 安装

```bash
pip install -e .
```

## 快速开始

### 交互模式（推荐）

```bash
pp
```

输入你的需求，会依次进行：
1. **需求澄清** - 回答问题让优化更精准
2. **生成4个版本** - Light / Moderate / Deep / Framework
3. **选择复制** - 输入版本号复制到剪贴板
4. **细化优化** - 可以继续输入反馈细化某个版本

### 命令行模式

```bash
pp "设计一个登录功能"
```

快速优化，适合脚本调用。

## 使用流程

```
1. 输入需求
   > 设计一个电商用户系统

2. 回答澄清问题（可选）
   1. 这个系统面向什么用户？ → 普通消费者
   2. 需要支持哪些登录方式？ → 手机号、邮箱、微信
   ...

3. 查看优化结果
   ╭──────────────────────────────────────╮
   │ Version 1: Light optimization       │
   │ Version 2: Moderate optimization     │
   │ Version 3: Deep optimization         │
   │ Version 4: RTF framework             │
   ╰──────────────────────────────────────╯

4. 选择并复制
   选择版本复制 (1-4)，或 输入数字+空格+反馈来细化
   例如: 3 添加更多安全约束

   → 输入 2 复制版本2到剪贴板
```

## 配置 LLM 提供商

首次运行如果连接失败，会自动弹出选择框：

```
1. ollama - 本地 Ollama
2. openai - OpenAI API
3. claude - Anthropic Claude
4. custom - 自定义 API（如 SiliconFlow）
```

### SiliconFlow 示例

```
选择 provider: 4 (custom)
API Base URL: https://api.siliconflow.cn/v1
API Key: 你的key
Model: Qwen/Qwen2.5-7B-Instruct
```

或通过环境变量：

```bash
export PROMPTPRO_PROVIDER=custom
export CUSTOM_BASE_URL=https://api.siliconflow.cn/v1
export CUSTOM_API_KEY=sk-xxx
export PROMPTPRO_MODEL=Qwen/Qwen2.5-7B-Instruct
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `pp` | 交互模式 |
| `pp "prompt"` | 命令行快速优化 |
| `pp --config` | 查看当前配置 |
| `pp --models` | 列出可用模型 |

交互模式命令：

| 命令 | 说明 |
|------|------|
| `/help` | 帮助 |
| `/quit` | 退出 |
| `/provider` | 切换提供商 |
| `/model` | 切换模型 |
| `/config` | 查看配置 |
| `/history` | 查看历史 |
| `/clarify` | 开关澄清问题 |

## 配置文件

配置文件位于 `~/.prompt-optimizer/config.json`

## License

MIT