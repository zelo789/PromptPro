# 更新日志

## [0.5.0] - 2026-03-16

### 新增功能

- **需求文档功能**
  - 支持自定义需求文档（Markdown 格式）
  - 文档结构: `name` / `intro` / `tune` 三个字段
  - 存放在项目 `prompts/` 目录
  - 新增命令: `/docs`, `/load`, `/doc`, `/savedoc`, `/cleardoc`
  - 优化 Prompt 时自动整合文档上下文

- **新增模块**
  - `src/requirement.py` - 需求文档解析和管理
  - `RequirementDoc` 数据模型
  - `RequirementParser` 解析器（支持多行块）
  - `RequirementManager` 管理器

- **异常处理**
  - 新增错误码 7xx 用于需求文档错误
  - 新增 `RequirementError` 异常类

### 新增文件

- `src/requirement.py` - 需求文档模块
- `prompts/example-login.md` - 示例需求文档
- `tests/test_requirement.py` - 单元测试（16 个测试用例）

## [0.4.0] - 2026-03-14

### 品牌更新

- **项目重命名**: Bytory → PromptPro
- **品牌标语**: "让 Prompt 更懂 AI"
- **命令更新**: `pp` (小写) 作为主命令
- **异常重命名**: `BytoryError` → `PromptProError`

### 新增功能

- **首次使用引导**
  - 检测首次运行，显示欢迎引导
  - 提供示例 prompt 快速体验
  - 优化 Ollama 连接失败提示

- **框架推荐增强**
  - 显示框架匹配原因
  - 可视化推荐逻辑

### 代码重构

- **UI 模块重构**
  - 合并 `ui.py` 和 `display.py` 到 `src/ui/` 目录
  - 新模块结构: `console.py`, `panels.py`, `tables.py`
  - 统一导出入口 `src/ui/__init__.py`

### 文档更新

- **README 重构**
  - 突出三大创新点
  - 添加框架选择决策图
  - 简化快速开始步骤
  - 添加效果对比示例

## [0.3.0] - 2026-03-13

### 新增功能

- **配置系统增强**
  - 添加配置验证功能
  - 支持配置迁移（版本升级）
  - 新增 `temperature`、`max_retries`、`retry_delay` 等配置项
  - 新增 `enable_history`、`max_history_items` 历史配置
  - 新增 `auto_clipboard` 剪贴板配置

- **Ollama 客户端优化**
  - 添加自动重试机制（指数退避）
  - 使用连接池提升性能
  - 支持可配置的温度参数
  - 添加 `set_temperature()` 方法

- **历史记录功能**
  - 新增 `HistoryManager` 模块
  - 支持保存/查询/搜索/删除历史
  - 支持导出历史记录

- **剪贴板支持**
  - 新增 `clipboard` 模块
  - 跨平台支持（Windows/macOS/Linux）
  - 可选安装 `pyperclip` 依赖

- **命令行参数**
  - 支持 `--model` 指定模型
  - 支持 `--level` 指定优化级别
  - 支持 `--framework` 指定框架
  - 支持 `--output` 输出到文件
  - 新增 `models`、`config`、`history` 子命令

- **错误处理**
  - 添加错误码系统
  - 完善异常类层次结构
  - 统一使用 logger

- **代码重构**
  - 拆分 `cli.py` 为 `ui.py`、`display.py`、`commands.py`
  - 改进代码组织结构

- **测试**
  - 添加单元测试
  - 测试覆盖配置、异常、策略、历史模块

### 改进

- 版本号升级至 0.3.0
- `Config` 类使用 `dataclasses.asdict()` 替代手动序列化
- `OllamaClient` 使用 `requests.Session` 连接池
- 改进 Windows 编码处理（延迟执行）

### 修复

- 修复 `cli.py` 顶层副作用问题
- 统一日志使用（移除 `print` 混用）

## [0.2.0] - 2026-03-03

### 新增功能

- 7 种 Prompt 框架支持
- 智能框架推荐
- 多版本优化对比
- 交互模式
- 基本配置管理
- 模型管理功能
- Windows 编码修复

### 框架

- CO-STAR、RTF、CREATE、APE、BROKE、RISEN、TAG 框架
- 轻度/中度/深度三级优化
- 发散性问题澄清
- 模型切换功能

## [0.1.0]

- 初始版本
- 基本 Ollama 集成
- 简单 Prompt 优化功能