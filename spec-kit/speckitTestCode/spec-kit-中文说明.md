# Spec Kit（spec-kit）中文说明与用法整理

> 项目地址：https://github.com/github/spec-kit  
> 核心理念：Spec-Driven Development（规格驱动开发）

## 1. Spec Kit 是什么

Spec Kit 是一套开源“工具包”，目标是让你把注意力放在**产品场景（scenarios）**和**可预期结果（outcomes）**上，而不是从零开始“凭感觉”拼凑实现。它强调把规格（spec）从一次性文档，提升为能够驱动后续实现流程的“第一等产物”。

它提供了一个 CLI（Specify CLI）来初始化项目模板、检查依赖，并与支持的 AI Agent 工作流配合使用。

## 2. Spec-Driven Development（规格驱动开发）要点

根据 Spec Kit 的描述，Spec-Driven Development 的核心变化是：

- 传统模式：代码是中心；规格只是脚手架，写完就丢。
- 规格驱动：规格变成“可执行”的核心产物，后续实现围绕规格来展开，并可直接驱动生成实现。

你可以把它理解为：把“我想要什么”写清楚、结构化、可复用，并把实现过程变成更可控的流水线，而不是一次性大改动。

## 3. 前置条件与安装

Spec Kit 推荐使用 `uv` 来安装和运行 Specify CLI。

### 3.1 持久安装（推荐）

安装一次，全局可用：

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

安装后常用命令：

```bash
# 创建新项目（会新建目录）
specify init <PROJECT_NAME>

# 在现有项目中初始化（当前目录）
specify init . --ai claude

# 或显式使用 --here
specify init --here --ai claude

# 检查已安装工具与 Agent 可用性
specify check
```

升级（快速方式）：

```bash
uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git
```

### 3.2 一次性运行（不安装）

```bash
uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME>
```

持久安装的主要收益（Spec Kit 给出的点）：

- 工具在 PATH 中可用，无需自己写 shell alias
- 便于用 `uv tool list / upgrade / uninstall` 管理
- shell 配置更干净

## 4. Specify CLI：常用命令与参数

Spec Kit 提供的 CLI 以 `specify` 为入口，常见命令如下：

### 4.1 `specify init`

用途：初始化一个新的 Spec Kit 项目模板，或在现有项目中完成初始化。

参数与选项（来自 Spec Kit 的说明）：

- `<project-name>`：新项目目录名（使用 `--here` 时可省略；或用 `.` 指当前目录）
- `--ai`：指定 AI assistant/agent（例如 `claude`、`gemini`、`copilot` 等）
- `--script`：脚本变体（`sh` 用于 bash/zsh，`ps` 用于 PowerShell）
- `--ignore-agent-tools`：跳过 AI agent 工具检查
- `--no-git`：跳过 git 仓库初始化
- `--here`：在当前目录初始化而不是新建目录
- `--force`：初始化时强制合并/覆盖（用于已存在文件的情况）

### 4.2 `specify check`

用途：检查已安装工具可用性。Spec Kit 的说明里包含：

- `git`
- 以及多种 AI agent 工具（例如 claude / gemini / cursor-agent / windsurf / qwen / opencode / codex / shai / qoder 等）

你可以把它当成“环境体检”，避免在后续流程中才发现缺工具。

## 5. Agent 侧的 /speckit.* 斜杠命令工作流

Spec Kit 的流程（按官方的“Get Started”步骤）可以概括为：

1. 初始化与检查（`specify init` / `specify check`）
2. 建立项目原则（constitution）
3. 写规格（specify）
4. 写技术实现方案（plan）
5. 拆分任务（tasks）
6. 执行实现（implement）

这些步骤在支持 slash commands 的 AI agent 中，通过以下命令串起来：

### 5.1 `/speckit.constitution`

目的：为项目创建“治理原则”和开发准则，指导之后所有开发。

官方示例输入（原意）：

- 创建围绕代码质量、测试标准、用户体验一致性、性能要求的原则

使用建议（实践上）：

- 明确“必须写测试/何时写测试”
- 明确“性能/可观测性/错误处理”的底线
- 明确“代码风格与依赖选择”的原则（例如尽量少依赖）

### 5.2 `/speckit.specify`

目的：描述你想构建的东西，强调 **what/why**，避免一开始就纠结技术选型。

官方示例（照片相册应用，原意）：

- 以日期分组相册
- 主页面拖拽排序
- 相册不嵌套
- 相册内以 tile 方式预览照片

### 5.3 `/speckit.plan`

目的：给出技术栈与架构选择，把“怎么做”落到技术层面。

官方示例（原意）：

- 使用 Vite
- 尽量用原生 HTML/CSS/JS，减少库
- 图片不上传
- 元数据使用本地 SQLite 存储

### 5.4 `/speckit.tasks`

目的：把 plan 拆成可执行的任务清单（actionable task list）。

### 5.5 `/speckit.implement`

目的：根据 tasks 执行实现，完成构建。

## 6. 支持的 AI Agents（摘录）

Spec Kit 的说明列出了一批支持的 AI Agents（示例）：

- Claude Code
- Gemini CLI
- GitHub Copilot
- Cursor
- Windsurf
- Codex CLI
- Qwen Code
- opencode
- 以及更多（Spec Kit 列表中包含 Qoder、Auggie、Kilo Code、Roo Code、IBM Bob 等）

注：Spec Kit 也提到某些 Agent 可能有参数支持限制（例如 Amazon Q Developer CLI 不支持为 slash commands 传自定义参数）。

## 7. 两套典型使用姿势

### 7.1 新项目从零开始

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
specify init my-new-project
cd my-new-project
specify check
```

然后在你选择的 AI agent 中按顺序执行：

- `/speckit.constitution ...`
- `/speckit.specify ...`
- `/speckit.plan ...`
- `/speckit.tasks`
- `/speckit.implement`

### 7.2 在已有项目中引入 Spec Kit

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
cd <你的已有项目>
specify init . --ai claude
specify check
```

接着同样走 slash 命令流程，把项目原则与规格补齐，再按任务逐步落地。

## 8. 常见问题排查思路（基于工具链）

- `specify check` 不通过：先把缺失的依赖（git 或指定 agent 工具）补齐，再重跑
- 初始化覆盖冲突：使用 `specify init ... --force`（确保你理解会覆盖/合并的内容）
- 在不同 shell/平台运行：用 `--script sh` 或 `--script ps` 选择合适脚本变体

## 9. 本地目录说明（与你给的路径相关）

你给出的路径是：

- `/Users/tangshengkui/CodeByTangsk/spec-kit/speckitTestCode`

在当前工作区里我没有看到现成的 `spec-kit/` 目录结构，所以我将本说明文档直接写入该路径下，便于你后续把它当作 speckitTestCode 的“使用说明”来维护。如果你本地实际的 spec-kit 仓库在另一个工作区目录，需要把该文件移动过去即可。

