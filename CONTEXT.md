# Context: agent-engine

## Domain

桌面 AI 智能助手核心引擎。常驻桌面搜索式输入框 + 二次元虚拟角色，背后是支持多模型、记忆系统、文档分类、日程管理的 Agent 引擎。

## Core Concepts

| 术语 | 定义 |
|------|------|
| **Agent** | ReAct 模式的 AI 智能体，接收用户指令，选择工具执行，返回结果 |
| **ReAct** | Reasoning + Acting 循环：Thought → Action → Observation → Final Answer |
| **LLM** | 大语言模型抽象层，支持 OpenAI / Claude / 通义千问 / Ollama 本地模型 |
| **Tool** | Agent 可调用的功能单元（文件操作、命令执行、搜索、笔记、记忆查询） |
| **Memory** | 四层记忆系统：L0 滑动窗口 → L1 摘要 → L2 语义向量 → L3 情景记忆 |
| **Compression** | 上下文压缩管线：窗口截断 → 摘要压缩 → 检索压缩 |
| **Workflow** | 任务拆解引擎，将复杂目标分解为 DAG 子任务 |
| **Classifier** | 文档自动分类：文件监控 → 解析 → 规则匹配 → 移动 |
| **Scheduler** | 日程调度：一次性提醒 + 周期性 cron 任务 |
| **ErrorTracker** | 错误追踪器：失败任务写入 SQLite + loguru 日志 |

## Architecture

```
CLI / FastAPI / PySide6 → Agent (ReAct) → LLM
                              ├─ Tools
                              ├─ Memory (L0-L3)
                              └─ Compression
                                     │
                              SQLite / ChromaDB
```

## Key Files

- `src/core/agent.py` — ReAct Agent 主循环
- `src/core/llm.py` — 多模型工厂
- `src/memory/manager.py` — 记忆编排器
- `src/compression/compressor.py` — 压缩管线
- `src/tools/registry.py` — 工具注册中心
- `src/main.py` — CLI 入口
