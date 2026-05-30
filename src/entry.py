"""统一入口 — 桌面 UI / CLI 路由

用法:
    agent-dev.exe               → 桌面悬浮窗 UI (默认)
    agent-dev.exe chat          → CLI 对话
    agent-dev.exe models        → 列出模型
    agent-dev.exe kb ...        → 知识库管理
    agent-dev.exe schedule ...  → 日程提醒
    agent-dev.exe classify ...  → 文件分类
    agent-dev.exe init          → 初始化数据库
"""

import os
import sys


def main():
    is_frozen = getattr(sys, "frozen", False)
    if is_frozen:
        os.chdir(os.path.dirname(sys.executable))

    args = sys.argv[1:]

    if not args:
        # 双击 / 无参数 → 桌面 UI
        from src.ui.main_window import main as ui_main
        ui_main()
    else:
        # 有参数 → CLI 模式
        from src.main import app
        app()


if __name__ == "__main__":
    main()
