"""统一入口 — CLI / GUI 路由

用法:
    agent-dev.exe chat          → CLI 对话
    agent-dev.exe models        → 列出模型
    agent-dev.exe kb ...        → 知识库管理
    agent-dev.exe desktop       → 桌面悬浮窗 UI
    agent-dev.exe schedule ...  → 日程提醒
    agent-dev.exe classify ...  → 文件分类
    agent-dev.exe init          → 初始化数据库
    agent-dev.exe               → 交互式选择
"""

import os
import sys


def main():
    # 打包后：确保 CWD 在 exe 同级，config/data 路径正确
    is_frozen = getattr(sys, "frozen", False)
    if is_frozen:
        exe_dir = os.path.dirname(sys.executable)
        os.chdir(exe_dir)

    args = sys.argv[1:]

    if not args:
        _interactive_prompt()
    elif args[0] == "desktop":
        from src.ui.main_window import main as ui_main

        ui_main()
    else:
        from src.main import app

        app()


def _interactive_prompt():
    print(f"\n  Agent 开发助手  v1.0.1\n")
    print("  1. CLI 命令行  (agent-dev chat)")
    print("  2. 桌面悬浮窗 UI  (agent-dev desktop)")
    print()
    choice = input("  选择 [1/2] (默认 2): ").strip()

    if choice == "1":
        print("\n启动 CLI 对话...\n")
        from src.main import app
        import sys as _sys
        _sys.argv = [_sys.argv[0], "chat"]
        app()
    else:
        print("\n启动桌面 UI...\n")
        from src.ui.main_window import main as ui_main
        ui_main()


if __name__ == "__main__":
    main()
