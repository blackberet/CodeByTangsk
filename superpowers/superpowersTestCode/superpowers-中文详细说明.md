# Superpowers（obra/superpowers）中文详细说明

> 本文基于你本地目录 `superpowers/superpowersTestCode` 与仓库 `superpowers/obra-superpowers` 的实际内容整理，侧重解释它“是什么、怎么运作、目录里有什么、不同平台如何接入、如何验证是否生效”。

## 1. 你现在的本地目录情况

你给的路径是：

- `superpowers/superpowersTestCode`

该目录当前是空目录（只存在目录本身，没有任何文件）。它更像是一个“你自己用来放测试代码/说明文档”的工作区占位符，并不是 `obra/superpowers` 官方仓库的一部分或必须目录。

与之对应，真正的 Superpowers 仓库代码我已经放在：

- `superpowers/obra-superpowers`

后续如果你希望在 `superpowersTestCode` 里写“演示项目/练习计划/技能调用示例”，也完全可以（Superpowers 本身不强制你用某个目录结构，它提供的是工作流与技能库）。

## 2. Superpowers 是什么（核心定位）

Superpowers 是一套给编码代理（Claude Code / Codex / OpenCode 等）使用的“软件开发工作流 + 可组合技能库（skills）”。它的目标不是提供某个框架 SDK，而是把一整套成熟的开发流程变成可触发、可复用、可强制执行的技能集合，从而让代理在做需求→设计→计划→实现→测试→评审→收尾的全过程里，减少随意性与“直接开写”的冲动。

核心理念（仓库 README 中写得很明确）：

- 先澄清要做什么（设计/规格），再动代码
- 计划必须可执行（任务粒度小、文件路径明确、命令明确）
- 强制 TDD（红-绿-重构）
- 重视验证与证据（跑测试/检查输出），不接受“口头完成”

参考：
- 仓库说明：[README.md](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/README.md)

## 3. 它是怎么“接入到代理”的（插件/命令/技能三层）

从仓库结构看，Superpowers 主要由三层组成：

### 3.1 技能库（skills/）

这是最核心的资产：每个技能一个目录，每个技能入口是 `SKILL.md`，并带有 YAML frontmatter：

```md
---
name: brainstorming
description: "You MUST use this before any creative work ..."
---
```

技能内容里会定义：

- 何时使用（触发条件）
- 必须遵守的流程（步骤、检查点、反模式）
- 与其他技能的集成关系（比如“完成后必须调用 finishing-a-development-branch”）

技能目录列表（仓库中现有）：

- brainstorming
- using-git-worktrees
- writing-plans
- executing-plans
- subagent-driven-development
- test-driven-development
- systematic-debugging
- verification-before-completion
- requesting-code-review
- receiving-code-review
- finishing-a-development-branch
- dispatching-parallel-agents
- writing-skills
- using-superpowers

参考：
- 技能目录：[skills/](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/skills)
- 示例技能：[brainstorming/SKILL.md](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/skills/brainstorming/SKILL.md)

### 3.2 命令包装（commands/）

`commands/` 里不是实现代码，而是“快捷命令 → 指向某个技能”的薄封装。比如：

- `commands/brainstorm.md`：要求调用 `superpowers:brainstorming`
- `commands/write-plan.md`：要求调用 `superpowers:writing-plans`
- `commands/execute-plan.md`：要求调用 `superpowers:executing-plans`

它们都带 `disable-model-invocation: true`，意思是“这个命令本身不让模型自由发挥”，而是强制把你导向对应的技能内容。

参考：
- [brainstorm.md](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/commands/brainstorm.md)
- [write-plan.md](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/commands/write-plan.md)
- [execute-plan.md](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/commands/execute-plan.md)

### 3.3 插件入口（不同平台不同实现）

Superpowers 支持多个平台，接入方式不同，但目标一致：把技能库注入对话，并提供“查找技能/加载技能”的能力。

#### Claude Code 插件（.claude-plugin/ + hooks/）

- `.claude-plugin/plugin.json`：插件元信息（名称、版本、repo 等）
- `hooks/session-start.sh` + `hooks/hooks.json`：在会话开始/恢复/compact 等事件里，注入 “You have superpowers” 以及 `using-superpowers` 技能全文

`hooks/hooks.json` 的 matcher 里写了 `startup|resume|clear|compact`，因此多种会话事件都会触发注入，保证技能规则在长对话压缩后仍然存在。

参考：
- [plugin.json](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/.claude-plugin/plugin.json)
- [hooks.json](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/hooks/hooks.json)
- [session-start.sh](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/hooks/session-start.sh)

#### OpenCode 插件（.opencode/plugin/superpowers.js）

OpenCode 这边是一个 JS 插件，提供两个核心工具：

- `use_skill`：按名字加载技能，并把技能内容以 `noReply: true` 的方式插入会话（保证对话压缩后仍可重注入/保留）
- `find_skills`：扫描 project/personal/superpowers 目录列出全部技能

并且它在事件里处理：

- `session.created`：注入 bootstrap（包含 using-superpowers + tool mapping）
- `session.compacted`：注入 compact 版本 bootstrap（节省 token）

技能的优先级解析（README 也有写）：

1. Project skills：`.opencode/skills/`
2. Personal skills：`~/.config/opencode/skills/`
3. Superpowers skills：`superpowers:...`（来自 superpowers 仓库 skills）

参考：
- [superpowers.js](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/.opencode/plugin/superpowers.js)
- OpenCode 文档：[docs/README.opencode.md](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/docs/README.opencode.md)

#### Codex CLI（.codex/superpowers-codex + lib/skills-core.js）

Codex 不是插件系统注入，而是提供一个 Node CLI 脚本：

- `bootstrap`：输出 bootstrap 内容 + 列技能 + 自动加载 using-superpowers
- `find-skills`：列出技能
- `use-skill <name>`：加载某个技能

参考：
- [superpowers-codex](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/.codex/superpowers-codex)
- Codex 文档：[docs/README.codex.md](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/docs/README.codex.md)

#### 共享核心：lib/skills-core.js

为了避免 OpenCode/Codex 各写一套解析逻辑，仓库抽了一个共享模块，包含：

- `extractFrontmatter(filePath)`：从 `SKILL.md` 解析 name/description
- `stripFrontmatter(content)`：移除 frontmatter，得到纯正文
- `findSkillsInDir(dir, sourceType, maxDepth)`：递归查找 SKILL.md
- `resolveSkillPath(skillName, superpowersDir, personalDir)`：按命名规则解析技能路径（支持 `superpowers:` 前缀强制）
- `checkForUpdates(repoDir)`：用 `git fetch` + `git status` 判断是否落后远端

参考：
- [skills-core.js](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/lib/skills-core.js)

## 4. “基础工作流”到底是什么（按顺序解释）

仓库 README 给出的“基础工作流”是一个推荐的、可重复的闭环：

1. brainstorming：先通过对话把想法变成可验证的设计/规格
2. using-git-worktrees：在设计确认后开隔离工作区，避免污染主分支
3. writing-plans：把实现拆成可执行的小任务（每个任务 2–5 分钟）
4. subagent-driven-development 或 executing-plans：按计划执行（同会话多子代理 / 平行会话批次执行）
5. test-driven-development：实现必须遵循 TDD（红-绿-重构）
6. requesting-code-review：每个重要阶段做评审（计划一致性与质量）
7. finishing-a-development-branch：所有任务完成后，做验证、决定 merge/PR/清理

参考：
- [README.md](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/README.md)
- [writing-plans/SKILL.md](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/skills/writing-plans/SKILL.md)
- [executing-plans/SKILL.md](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/skills/executing-plans/SKILL.md)
- [subagent-driven-development/SKILL.md](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/skills/subagent-driven-development/SKILL.md)

## 5. 两种“执行计划”的模式怎么选

### 5.1 executing-plans（批次执行 + 人类检查点）

特点：

- 先读计划并“批判性审阅”（发现计划缺口要先停下提问）
- 默认一批执行 3 个任务
- 每批做完要汇报实现内容与验证输出，然后等待反馈
- 最后必须进入 finishing-a-development-branch 收尾

适用：

- 你希望“每批次可控”，更强调人类 review 节奏
- 计划质量不确定，想先边走边纠偏

参考：
- [executing-plans/SKILL.md](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/skills/executing-plans/SKILL.md)

### 5.2 subagent-driven-development（同会话，每任务 1 实现 + 2 次评审）

特点（这是仓库里写得最“流程化”的部分之一）：

- 每个任务派一个“全新实现子代理”
- 实现结束后强制两阶段 review：
  1) 规格符合性（spec compliance）review
  2) 代码质量（code quality）review
- review 不通过必须回到实现代理修正，并 re-review，直到通过
- 通过后才在 TodoWrite 标记任务完成

适用：

- 计划中的任务相对独立
- 你希望更强的质量闸门与更少的上下文污染

参考：
- [subagent-driven-development/SKILL.md](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/skills/subagent-driven-development/SKILL.md)

## 6. “using-superpowers” 为什么这么重要

`using-superpowers` 这个技能是全局规则引擎：它要求“任何时候只要有 1% 可能适用某个技能，就必须先加载技能再行动/再回答”。它本质上是在约束代理的工作方式，避免“跳过流程直接写代码”。

Claude Code 侧的 hook 也会在 SessionStart 时把它全文注入，让这条规则在会话里始终存在。

参考：
- [using-superpowers/SKILL.md](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/skills/using-superpowers/SKILL.md)
- [session-start.sh](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/hooks/session-start.sh)

## 7. 测试与验证（仓库如何证明这些技能“真的会按预期触发”）

Superpowers 的测试不是传统单元测试为主，而是偏“集成测试/会话回放验证”：

- 在 `tests/` 下有多个测试套件目录（claude-code、opencode、skill-triggering、explicit-skill-requests 等）
- `docs/testing.md` 解释了：会跑真实的 Claude Code headless 会话，然后解析 transcript（jsonl）检查：
  - 是否调用了技能
  - 是否派发了 subagent
  - 是否使用了 TodoWrite
  - 是否真正创建了实现文件/测试文件
  - 是否跑通测试
  - 是否有合理提交历史

参考：
- [docs/testing.md](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/docs/testing.md)
- 测试目录：[tests/](file:///Users/tangshengkui/CodeByTangsk/superpowers/obra-superpowers/tests)

## 8. 你接下来怎么用（结合你当前目录的建议落地方式）

因为你当前的 `superpowersTestCode` 是空的，我建议你把它当成“练习场”，例如：

- 在里面创建一个最小 demo 项目（Node/Python/Go 任意）
- 写一个 `docs/plans/YYYY-MM-DD-demo.md` 的计划（按 writing-plans 的格式）
- 选择执行方式：
  - 想分批 check：用 executing-plans
  - 想同会话高强度 review：用 subagent-driven-development

如果你告诉我你想用哪种语言做 demo（例如 Node + Vitest / Python + pytest），我可以直接在 `superpowersTestCode` 里生成一个完整的“示例计划 + 最小项目 + 一轮 TDD 演示”。

