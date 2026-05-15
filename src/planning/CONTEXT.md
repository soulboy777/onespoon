# Context: planning

## Domain

计划与执行双模式子系统。Plan Mode 生成结构化计划（只读工具），Execute Mode 按计划逐步执行任务。

## Core Concepts

| 术语 | 定义 |
|------|------|
| **Plan Mode** | 计划模式：Agent 只能用只读工具（读取、搜索、记忆查询），输出结构化计划 |
| **Execute Mode** | 执行模式：Agent 可使用全部工具，按计划步骤逐步执行 |
| **Plan** | 一个执行计划，包含标题、描述、步骤列表、状态 |
| **PlanStep** | 单个执行步骤，包含行动、目标、预期结果、依赖关系、状态 |
| **PlanManager** | 计划 CRUD 管理器，SQLite 存储 + Markdown 文件双写 |
| **PlanTemplate** | 计划模板，用于格式化输出计划文件 |
| **PlanModeAgent** | 计划生成器，调用 LLM 分析需求生成 JSON 计划 |
| **ExecuteModeAgent** | 计划执行器，按步骤逐一执行并更新进度 |

## Plan State Machine

```
draft → ready → running → done
                  ↓
                failed
```

## Step State Machine

```
pending → running → done
  ↓         ↓
skipped   failed
```

## Key Files

- `src/planning/models.py` — Plan + PlanStep ORM
- `src/planning/manager.py` — CRUD + Markdown I/O
- `src/planning/planner.py` — Plan Mode Agent
- `src/planning/executor.py` — Execute Mode Agent
- `src/planning/template.py` — 计划模板
