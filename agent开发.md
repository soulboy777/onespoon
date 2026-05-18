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
| 桌面 UI | **PySide6 + QML** | 悬浮窗 + 角色动画 + 设置面板 |
| 打包 | **PyInstaller + Inno Setup** | 独立 exe + 安装器 (开机启动) |

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

### 10. Plan/Execute 双模式

参考 opencode 计划模式的 Plan/Build 双模式设计：

**Plan Mode（计划模式）：**
- Agent 只能使用只读工具（读取文件、搜索、记忆查询）
- 生成结构化计划（标题、描述、步骤、依赖）
- 计划存储：Markdown 文件 + SQLite 索引
- 支持计划修改和迭代

**Execute Mode（执行模式）：**
- Agent 可使用全部工具
- 按计划步骤逐步执行
- 实时更新步骤状态（pending → running → done/failed）
- 支持失败恢复和继续执行

**CLI 命令：**
```
/plan              # 切换到计划模式
/execute           # 切换到执行模式
/plan new <描述>    # 创建新计划
/plan show [id]    # 查看计划
/plan delete <id>  # 删除计划
/plans             # 列出所有计划
/execute <id>      # 执行指定计划
/execute continue  # 继续未完成计划
```

**工具读写标记：**
| 工具 | Plan | Execute |
|------|:----:|:-------:|
| read_file, list_dir, web_search, query_memory | ✓ | ✓ |
| search_knowledge, list_knowledge_bases | ✓ | ✓ |
| write_file, delete_file, move_file | ✗ | ✓ |
| shell_exec, create_note | ✗ | ✓ |

**计划模板：** `config/plan-template.md`（自动生成 `data/plans/` 下的计划文件）

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
│   ├── planning/               # ★Plan/Execute 双模式
│   │   ├── models.py           # Plan + PlanStep ORM
│   │   ├── manager.py          # 计划 CRUD + Markdown I/O
│   │   ├── template.py         # 计划模板渲染
│   │   ├── planner.py          # Plan Mode Agent (只读工具)
│   │   └── executor.py         # Execute Mode Agent (逐步执行)
│   │
│   ├── ui/                     # ★ 桌面 UI
│   │   ├── main_window.py      # QML 启动器 + 托盘 + 热键
│   │   ├── backend.py          # UI ↔ Agent 桥接层
│   │   ├── config_manager.py   # 用户配置管理
│   │   ├── user_config.py      # UserConfig 模型
│   │   ├── version.py          # 版本常量
│   │   ├── theme.py            # 主题色彩
│   │   ├── qml/                # QML 组件 (15 个文件)
│   │   └── resources/          # 角色立绘/图标/字体
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
│   ├── models.yaml           # 模型列表
│   └── plan-template.md     # 计划模板
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
├── agent-dev.spec            # PyInstaller 打包配置
├── src/entry.py              # 统一入口 (CLI/GUI路由)
├── scripts/
│   └── build.ps1            # 一键构建脚本
├── installer/
│   └── setup.iss             # Inno Setup 安装脚本
├── icon/
│   └── agent-dev.ico         # 应用图标
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
- [x] Plan/Execute 双模式
- [x] QML 桌面 UI (悬浮窗 + 角色 + 设置 + 关于)
- [x] PyInstaller 打包配置 + Inno Setup 安装器

### Phase 2：交互扩展

- [ ] FastAPI REST + WebSocket 接口
- [ ] 对话历史面板
- [ ] 自定义分类规则 UI

### Phase 3：打磨发布

- [x] PySide6 桌面悬浮窗 (Layout C)
- [x] 二次元角色动画（QML）
- [x] PyInstaller 打包
- [x] Inno Setup 安装器 + 开机启动
- [ ] 性能优化
- [ ] 角色立绘替换

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
python -m src.main init                         # 初始化（含 RAG + Plans）
python -m src.main kb create -n tech_docs       # 创建知识库
python -m src.main kb ingest -k tech_docs -p ./docs/ -r  # 导入文档
python -m src.main kb search -k tech_docs -q "Python"     # 搜索

# 6. Plan/Execute
python -m src.main chat                         # 启动对话
/plan                                           # 切换计划模式
/plan new 实现用户登录功能                        # 创建计划
/plans                                          # 查看计划列表
/execute 1                                      # 执行计划 #1

# 7. 文件分类
python -m src.main classify ./my-files

# 8. 添加提醒
python -m src.main schedule -t "开会" -a "2026-05-14 15:00"

# 9. 查看可用模型
python -m src.main models

# 10. 桌面 UI
python -m src.ui.main_window

# 11. 打包为 exe
pip install PyInstaller
.\scripts\build.ps1
```

---

## 七、UI 设计

### 布局 (Layout C)

```
┌────────────────────────────────────────────────────┐
│  ┌─────────┐  ┌──────────────────────────────────┐ │
│  │  角色    │  │                                  │ │
│  │ 160×280 │  │      Agent 响应 (Markdown)        │ │
│  │  (PNG)  │  │      可滚动区域                    │ │
│  │         │  │                                  │ │
│  └─────────┘  └──────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────┐│
│  │ [PLAN] [EXEC]  🔍 输入指令...      ⚙ ℹ − ×    ││
│  └────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────┘
  总窗口: 620 × 420 | 底部栏: 60px | 角色: 160×280
```

类似微软搜索窗，输入框常驻桌面，可输入任何内容和指令，同时有二次元角色挂在一旁。

（UI 具体设计由画师神启小白负责）

---

## 八、从画到 UI 配置 — 完整流程

### 1. 画师交付物

| 文件名 | 用途 | 说明 |
|--------|------|------|
| `idle.png` | 待机表情 | 角色平常的样子 |
| `thinking.png` | 思考中 | 用户输入后、等待回答时 |
| `happy.png` | 完成 | 回答成功后短暂显示 |
| `busy.png` | 忙碌/错误 | 执行出错时 |

**规格要求：**
- 格式：PNG (RGBA, 透明背景)
- 角色本体占 140×280 像素区域（QML 会自动 PreserveAspectFit 缩放）
- 建议画布：宽 300px，高 500px（给角色留呼吸空间）
- 所有表情用**同一画布尺寸**，避免切换时跳变

### 2. 图片放置

```
src/ui/resources/character/
├── idle.png          ← 把画师给的图改名为此 4 个文件名
├── thinking.png
├── happy.png
└── busy.png
```

QML 引用路径已写死：`"resources/character/" + charState + ".png"`
当后端发信号 `characterState = "thinking"` → 自动显示 `thinking.png`。

### 3. 角色状态机

```
idle ──(用户输入)──→ thinking ──(回答完成)──→ happy ──(4s后)──→ idle
 │                     │
 └──(超时)──→ idle      └──(出错)──→ busy ──(4s后)──→ idle
```

### 4. 调整角色位置/大小

| 想改的 | 文件 | 参数 |
|--------|------|------|
| 角色容器总大小 | `CharacterWidget.qml` | `width: 150` `height: 300` |
| 角色图片显示大小 | `CharacterWidget.qml` | Image `width: 140` `height: 280` |
| 角色缩放模式 | `CharacterWidget.qml` | Image `fillMode: Image.PreserveAspectFit` |
| 角色水平位置 | `Main.qml` | 角色 Item `anchors.horizontalCenter` |
| 角色垂直位置 | `Main.qml` | 角色 Item `anchors.top` `anchors.topMargin` |
| 角色呼吸速度 | `CharacterWidget.qml` | Opacity动画 `duration: 1500` |
| 角色眨眼频率 | `CharacterWidget.qml` | Timer `interval: 4000` |
| 表情切换速度 | `CharacterWidget.qml` | Opacity动画 `duration: 150` |

### 5. 调整窗口和布局

| 想改的 | 文件 | 参数 |
|--------|------|------|
| 窗口总大小 | `Main.qml` | `width: 620` `height: 420` |
| 窗口默认位置 | `main_window.py` | `setPosition(x, y)` |
| 窗口圆角 | `Main.qml` | Rectangle `radius: 16` |
| 窗口透明度 | `Main.qml` | Rectangle `opacity: 0.92` |
| 底部栏高度 | `Main.qml` | 底部 Rectangle `Layout.preferredHeight: 56` |
| 底部栏色彩 | `Main.qml` | 底部 Rectangle `color: theme.bg_secondary` |
| 搜索框高度 | `Main.qml` | SearchBar `Layout.preferredHeight: 38` |
| 呼入动画速度 | `Main.qml` | Opacity动画 `duration: 200` |
| 快捷键 | `Main.qml` | Shortcut `sequence: "Alt+Space"` |

### 6. 调整色彩主题

所有颜色集中在 `src/ui/theme.py`，改一次全局生效：

```python
THEMES = {
    "dark": {
        "bg_primary": "#1a1a2e",     # 窗口主背景
        "bg_secondary": "#16213e",   # 面板/底部栏背景
        "text_primary": "#eeeeee",   # 主文字色
        "text_secondary": "#a0a0b0", # 次要文字色
        "glow_color": "#7c4dff",     # 输入框发光色
        "highlight": "#e94560",      # 强调色（关闭按钮等）
        "plan_color": "#4fc3f7",     # Plan 模式蓝
        "exec_color": "#66bb6a",     # Execute 模式绿
        "border_color": "#2a2a4e",   # 边框色
    },
    "light": { ... }
}
```

### 7. 调整设置面板

设置面板在 `SettingsWindow.qml` 中，7 个 Tab：

| Tab | 配置项来源 |
|-----|-----------|
| LLM | `user_config.py` → `UserLLMConfig` |
| API | `user_config.py` → `ApiKeyConfig` (密码框 + 👁 切换) |
| 嵌入 | `user_config.py` → `UserRagConfig` |
| RAG | `user_config.py` → `UserRagConfig` |
| 记忆 | `user_config.py` → `UserMemoryConfig` |
| 界面 | `user_config.py` → `UIConfig` |

保存时 → `config/user.yaml` + 环境变量注入。

### 8. 测试 UI

```bash
# 开发时直接运行（改 QML 后重新运行即生效，无需编译）
python -m src.ui.main_window

# 如果 QML 有问题，控制台会打印具体错误行号
# QML 模块缺失时: pip install PySide6
```

### 9. 关于面板信息

`src/ui/version.py` 中修改：

```python
VERSION = "0.2.0"
BUILD_DATE = "2026-05-17"
AUTHOR = "soulboy777"
ARTIST = "神启小白"
REPO_URL = "https://github.com/soulboy777/onespoon"
```
