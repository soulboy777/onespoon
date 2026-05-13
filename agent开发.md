# agent开发

## 项目概述

桌面 AI 智能助手 — 常驻桌面的搜索式输入框 + 二次元虚拟角色，背后是支持多模型、记忆系统、文档自动分类、日程管理的 Agent 引擎。

---

## 一、技术栈

| 层 | 技术 | 用途 |
|---|------|------|
| 语言 | **Python 3.11+** | |
| Agent 框架 | **LangChain** | ReAct 工作流、Tool 抽象、多模型切换 |
| 模型抽象 | **LangChain ChatModel + LiteLLM** | 统一 OpenAI / Claude / 通义千问 / Ollama 本地模型 |
| CLI | **Typer + Rich** | 命令行界面 |
| 数据库 | **SQLite + SQLAlchemy** | 文档索引、任务记录、配置存储 |
| 向量库 | **ChromaDB** | 语义记忆检索 |
| 文件监控 | **watchdog** | 目录监听触发自动分类 |
| 文档解析 | **unstructured + PyPDF2 + python-docx** | 读取各类文档内容 |
| 定时任务 | **APScheduler** | 日程调度 |
| Token 计数 | **tiktoken** | 精确 token 计数 |
| 日志 | **loguru** | 结构化日志 |
| API 服务 | **FastAPI** (Phase 2) | REST + WebSocket |
| 桌面 UI | **PySide6 + QML** (Phase 2) | 悬浮窗 + 角色 |
| 打包 | **PyInstaller** (Phase 3) | 独立 exe |

---

## 二、核心功能

### 1. 大模型接入

支持云端和本地模型切换：

- OpenAI: gpt-4o / gpt-4o-mini
- Anthropic: claude-opus / claude-sonnet
- 通义千问: qwen-turbo / qwen-plus
- Ollama 本地: llama3 / qwen2
- DeepSeek: deepseek-chat

配置: `config/models.yaml`

### 2. 记忆系统

四层记忆架构：

| 层级 | 类型 | 存储 | 生命周期 | 用途 |
|------|------|------|---------|------|
| L0 | 感知记忆 | 内存缓冲 | 当前会话 | 最近 N 轮对话 |
| L1 | 摘要记忆 | SQLite | 跨会话 | 压缩后历史对话摘要 |
| L2 | 语义记忆 | ChromaDB (向量) | 永久 | 用户偏好、重要事实、知识片段 |
| L3 | 情景记忆 | SQLite + 向量 | 永久 | 已完成任务、决策过程、失败经验 |

### 3. 上下文压缩

三种压缩策略，按优先级执行：

| 策略 | 触发条件 | 做法 |
|------|---------|------|
| 窗口截断 (window) | token < 80% 限额 | 保留最近消息 |
| 摘要压缩 (summarize) | 80% ~ 100% | LLM 生成摘要替换原文 |
| 检索压缩 (retrieve) | > 100% | 向量检索只取最相关片段 |

### 4. 工具系统

ReAct Agent 可调用的工具：

- `read_file` / `write_file` — 文件读写
- `list_dir` — 列出目录
- `move_file` / `delete_file` — 文件移动/删除
- `shell_exec` — 安全命令行（白名单模式）
- `web_search` — 网络搜索
- `create_note` — 创建笔记
- `query_memory` — 查询自身记忆

### 5. 文档自动分类

- watchdog 监控文件夹变化
- 解析文档标题/格式/内容 (txt, md, docx, pdf...)
- 规则引擎匹配 (默认按扩展名 + 自定义正则规则)
- 自动移动文件到分类文件夹

### 6. RAG 知识库（独立数据库）

独立的文档知识库系统，与对话记忆完全解耦：

| 组件 | 对话记忆 | RAG 知识库 |
|------|---------|-----------|
| SQLite | `data/agent.db` | `data/knowledge.db` |
| ChromaDB | `data/chroma/` | `data/chroma_kb/` |
| 用途 | 用户偏好、历史任务 | 文档检索、领域知识问答 |

**摄取管线：**

```
文件/文本/URL
  → Loader (读取源: txt/md/docx/pdf/url)
  → Parser (提取纯文本)
  → Chunker (分块: fixed / recursive / sentence)
  → Embedder (向量化: OpenAI / Ollama / 兼容接口)
  → Store (SQLite 元数据 + ChromaDB 向量 + BM25 索引)
```

**混合检索：**

```
用户查询
  → 向量嵌入
  ├─ ChromaDB 检索 (向量相似度 top-10)
  ├─ BM25 关键词检索 (rank_bm25 top-10)
  └─ Reciprocal Rank Fusion (RRF 融合排序 → top-5)
```

**知识库管理 CLI：**
```bash
agent-dev kb create --name tech_docs --desc "技术文档"
agent-dev kb ingest --kb tech_docs --path ./docs/ -r
agent-dev kb search --kb tech_docs --query "Python 协程"
agent-dev kb list
agent-dev kb stats --name tech_docs
agent-dev kb delete --name tech_docs
```

**Agent 工具：**
- `search_knowledge` — 搜索知识库获取文档内容
- `list_knowledge_bases` — 列出所有可用知识库

### 7. 日程调度

- 一次性提醒（指定时间）
- 周期性任务（cron 表达式）
- 基于 APScheduler

### 8. 报错日志

- 任务执行自检
- 失败任务写入 SQLite + loguru 日志
- 错误统计摘要
- 标记已解决

### 9. 工作流引擎

- 任务拆解（将复杂目标分解为子任务）
- 依赖管理（DAG 有向无环图）
- 顺序/并行执行
- Phase 3 接入 LLM 智能拆解

---

## 三、项目结构

```
agent开发/
├── src/
│   ├── main.py               # CLI 入口
│   │
│   ├── core/                  # 核心引擎
│   │   ├── config.py         # 配置管理
│   │   ├── llm.py            # 多模型适配
│   │   ├── agent.py          # ReAct Agent
│   │   └── workflow.py       # 工作流引擎
│   │
│   ├── memory/                # 记忆系统
│   │   ├── base.py           # 数据结构
│   │   ├── buffer.py         # L0 滑动窗口
│   │   ├── summary.py        # L1 对话摘要
│   │   ├── semantic.py       # L2 语义记忆
│   │   ├── episodic.py       # L3 情景记忆
│   │   └── manager.py        # 编排器
│   │
│   ├── compression/           # 上下文压缩
│   │   ├── counter.py        # Token 计数
│   │   ├── summarizer.py     # LLM 摘要
│   │   ├── strategies.py     # 压缩策略
│   │   └── compressor.py     # 压缩管线
│   │
│   ├── tools/                 # 工具系统
│   │   ├── base.py           # 基类 + 注册
│   │   ├── file_ops.py       # 文件操作
│   │   ├── shell_exec.py     # 命令执行
│   │   ├── web_search.py     # 网络搜索
│   │   ├── note.py           # 笔记
│   │   ├── memory_tool.py    # 记忆查询
│   │   ├── rag_tool.py       # RAG 检索
│   │   └── registry.py       # 注册入口
│   │
│   ├── rag/                    # ★RAG 知识库
│   │   ├── database.py         # 独立 SQLite (knowledge.db)
│   │   ├── models.py           # KnowledgeBase/Document/Chunk/Bm25Index
│   │   ├── chunker.py          # 3 种分块策略
│   │   ├── embedder.py         # 嵌入模型适配
│   │   ├── tokenizer.py        # 中英文分词
│   │   ├── ingestion.py        # 摄取管线
│   │   ├── retriever.py        # 混合检索 (向量+BM25)
│   │   └── manager.py          # 知识库管理 API
│   │
│   ├── storage/               # 存储层
│   │   ├── database.py       # 数据库引擎
│   │   ├── models.py         # ORM 模型
│   │   └── vector_store.py   # ChromaDB
│   │
│   ├── classifier/            # 文档分类
│   │   ├── watcher.py        # 文件监控
│   │   ├── parser.py         # 文档解析
│   │   ├── rules.py          # 规则引擎
│   │   └── categorizer.py    # 分类执行
│   │
│   ├── scheduler/             # 日程
│   │   └── schedule.py
│   │
│   └── utils/                 # 工具
│       ├── logger.py         # 日志
│       └── error_tracker.py  # 错误追踪
│
├── config/
│   ├── default.yaml          # 默认配置
│   └── models.yaml           # 模型列表
│
├── tests/
│   ├── conftest.py
│   ├── test_agent.py
│   ├── test_tools.py
│   ├── test_llm.py
│   ├── test_memory.py
│   ├── test_compression.py
│   └── test_classifier.py
│
├── data/                     # 运行时数据 (gitignore)
├── pyproject.toml
├── requirements.txt
└── agent开发.md
```

---

## 四、架构图

```
┌─────────────────────────────────────────────┐
│  交互层                                      │
│  ┌──────┐  ┌──────────┐  ┌──────────────┐  │
│  │ CLI  │  │ FastAPI  │  │ PySide6 悬浮窗│  │
│  │(Phase1)│ │(Phase 2) │  │  (Phase 2)   │  │
│  └──┬───┘  └────┬─────┘  └──────┬───────┘  │
│     │           │               │           │
│     └───────────┼───────────────┘           │
│                 ▼                            │
│  ┌──────────────────────────────────┐       │
│  │         Agent 核心引擎            │       │
│  │  ┌──────────┐  ┌──────────────┐  │       │
│  │  │  ReAct   │  │  Tool 注册   │  │       │
│  │  │ 工作流   │  │   + 调度     │  │       │
│  │  └────┬─────┘  └──────┬───────┘  │       │
│  │       │               │          │       │
│  │  ┌────┴───────────────┴───────┐  │       │
│  │  │      LLM 抽象层            │  │       │
│  │  │  (OpenAI/Claude/Ollama/…)  │  │       │
│  │  └────────────────────────────┘  │       │
│  │                                   │       │
│  │  ┌──────────┐  ┌──────────────┐  │       │
│  │  │ 记忆系统  │  │ 上下文压缩    │  │       │
│  │  │ L0~L3    │  │ 窗口/摘要/检索│  │       │
│  │  └──────────┘  └──────────────┘  │       │
│  └──────────────────────────────────┘       │
│                 │                            │
│     ┌───────────┼───────────┐               │
│     ▼           ▼           ▼               │
│  ┌──────┐  ┌───────┐  ┌─────────┐          │
│  │SQLite│  │ChromaDB│ │watchdog │          │
│  │ 存储  │  │向量检索 │ │文件监控 │          │
│  └──────┘  └───────┘  └─────────┘          │
├─────────────────────────────────────────────┤
│  扩展模块                                     │
│  ┌────────┐  ┌──────────┐  ┌───────────┐   │
│  │ 文档分类│  │ 日程调度  │  │ 错误日志  │   │
│  └────────┘  └──────────┘  └───────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │         RAG 知识库 (独立)             │   │
│  │  ┌──────────┐  ┌────────────────┐  │   │
│  │  │knowledge.db│  │data/chroma_kb/│  │   │
│  │  │(SQLite元数据)│ │(ChromaDB向量) │  │   │
│  │  └──────────┘  └────────────────┘  │   │
│  │  ┌──────────────────────────────┐  │   │
│  │  │  摄取管线 → 混合检索(BM25+向量)│  │   │
│  │  └──────────────────────────────┘  │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

---

## 五、开发阶段

### Phase 1：CLI 核心引擎（当前）

- [x] 项目骨架搭建
- [x] 多模型 LLM 抽象层
- [x] ReAct Agent + 工具系统
- [x] 四层记忆系统 (L0~L3)
- [x] 上下文压缩管线
- [x] SQLite + ChromaDB 存储
- [x] RAG 知识库独立数据库
- [x] CLI 交互界面
- [x] 文档分类器
- [x] 日程调度器
- [x] 错误追踪
- [x] 工作流引擎

### Phase 2：交互扩展

- [ ] FastAPI REST + WebSocket 接口
- [ ] PySide6 桌面悬浮窗
- [ ] 二次元角色动画（QML）
- [ ] 对话历史面板

### Phase 3：打磨发布

- [ ] 自定义分类规则 UI
- [ ] 性能优化
- [ ] PyInstaller 打包
- [ ] 安装器/文档

---

## 六、快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 初始化数据库
python -m src.main init

# 3. 设置 API Key (选其一)
set OPENAI_API_KEY=sk-xxx
set ANTHROPIC_API_KEY=sk-ant-xxx
set DASHSCOPE_API_KEY=sk-xxx

# 4. 启动 CLI 对话
python -m src.main chat

# 5. RAG 知识库
python -m src.main init                         # 初始化（含 RAG）
python -m src.main kb create -n tech_docs       # 创建知识库
python -m src.main kb ingest -k tech_docs -p ./docs/ -r  # 导入文档
python -m src.main kb search -k tech_docs -q "Python"     # 搜索

# 6. 文件分类
python -m src.main classify ./my-files

# 7. 添加提醒
python -m src.main schedule -t "开会" -a "2026-05-14 15:00"

# 8. 查看可用模型
python -m src.main models
```

---

## 七、UI 设计

类似微软搜索窗，输入框常驻桌面，可输入任何内容和指令，同时有二次元角色挂在一旁。

（UI 具体设计由画师神启小白负责）
