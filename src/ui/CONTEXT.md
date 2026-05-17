# Context: ui

## Domain

桌面 UI 子系统。基于 PySide6 + QML 的常驻桌面悬浮窗，类似微软搜索框 + 二次元角色。

## Core Concepts

| 术语 | 定义 |
|------|------|
| **MainWindow** | 透明无边框置顶窗口，包含全部 UI 组件 |
| **SearchBar** | 搜索输入框组件，发光焦点效果 |
| **ResponsePanel** | Agent 回答展示区，支持 Markdown 渲染 |
| **CharacterWidget** | 二次元角色渲染（PNG + QML 呼吸/眨眼/表情切换动画） |
| **ModeIndicator** | Plan/Execute 模式指示灯 |
| **PlanPanel** | 计划列表和详情查看面板 |
| **SettingsWindow** | 7 个 Tab 设置窗口（LLM/API/嵌入/RAG/记忆/界面） |
| **AboutPanel** | 关于面板（版本/作者/画师/链接） |
| **UIBackend** | Python ↔ QML 桥接层（Signals/Slots） |
| **ConfigManager** | 用户配置读写（user.yaml） |
| **SystemTray** | 系统托盘图标 + 右键菜单 |

## Architecture

```
QML Layer
  ├── Main.qml (根窗口)
  ├── SearchBar.qml / ResponsePanel.qml
  ├── CharacterWidget.qml (PNG 动画)
  ├── SettingsWindow.qml (7-Tab 设置)
  ├── AboutPanel.qml
  └── Components (IconButton, ModeButton, SettingRow, KeyRow...)

Python Layer
  ├── main_window.py (QQuickView + Tray + Hotkey)
  ├── backend.py (UIBackend: Signals ↔ Slots)
  ├── config_manager.py (user.yaml I/O)
  ├── user_config.py (Pydantic 模型)
  ├── version.py (版本常量)
  └── theme.py (深色/浅色)

│     UIBackend (Signals/Slots)
│     └─→ Agent 核心引擎
```

## Key Files

- `src/ui/main_window.py` — 启动器
- `src/ui/backend.py` — 桥接层
- `src/ui/qml/Main.qml` — 主窗口 QML
- `src/ui/qml/SettingsWindow.qml` — 设置窗口
- `src/ui/qml/CharacterWidget.qml` — 角色渲染
- `src/ui/config_manager.py` — 配置管理
