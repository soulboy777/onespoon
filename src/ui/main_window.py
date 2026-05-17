"""桌面前端启动器 — QML 窗口 + 系统托盘 + 全局热键"""

import sys
from pathlib import Path

from PySide6.QtCore import QObject, QMetaObject, QSize, QUrl, Qt, QTimer
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQuick import QQuickView
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from loguru import logger

from src.ui.backend import UIBackend
from src.ui.config_manager import load_user_config
from src.ui.version import VERSION, BUILD_DATE, AUTHOR, REPO_URL
from src.utils.logger import setup_logging


class DesktopApp:
    """桌面应用主控制器"""

    def __init__(self):
        setup_logging()

        self._app = QApplication(sys.argv)
        self._app.setApplicationName("Agent 开发助手")
        self._app.setApplicationVersion(VERSION)
        self._app.setQuitOnLastWindowClosed(False)

        self._user_config = load_user_config()

        # 创建 QML 引擎
        self._view = QQuickView()
        self._view.setTitle("Agent 开发助手")
        self._view.setResizeMode(QQuickView.SizeRootObjectToView)
        self._view.setColor(Qt.transparent)
        self._view.setMinimumSize(QSize(620, 420))
        self._view.setMaximumSize(QSize(620, 420))

        # 无边框 + 置顶
        self._view.setFlags(
            Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint
        )
        self._view.setDefaultAlphaBuffer(True)

        # 创建 Backend
        self._backend = UIBackend()

        # 暴露 Backend 到 QML
        engine = self._view.engine()
        context = engine.rootContext()
        context.setContextProperty("uiBackend", self._backend)

        # 加载 QML
        qml_dir = Path(__file__).resolve().parent / "qml"
        qml_path = str(qml_dir / "Main.qml")

        if not Path(qml_path).exists():
            logger.error(f"QML 文件不存在: {qml_path}")
            print(f"错误: QML 文件不存在: {qml_path}")
            sys.exit(1)

        self._view.setSource(QUrl.fromLocalFile(qml_path))

        # 设置窗口位置 (屏幕中央偏上)
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self._view.setPosition(
            (screen.width() - 620) // 2,
            screen.top() + 80,
        )

        # 系统托盘
        self._setup_tray()

        # 加载设置
        self._load_settings_to_qml()

        # 注册全局热键 (通过 QML Shortcut)
        # 已在 Main.qml 中实现

        self._view.show()

    def _setup_tray(self):
        self._tray = QSystemTrayIcon()
        self._tray.setToolTip("Agent 开发助手")

        # 托盘图标 (使用内置图标作为占位)
        icon = QApplication.style().standardIcon(QApplication.style().SP_ComputerIcon)
        self._tray.setIcon(icon)

        menu = QMenu()
        show_action = menu.addAction("显示/隐藏")
        show_action.triggered.connect(self._toggle_visible)

        menu.addSeparator()

        plan_action = menu.addAction("计划模式")
        plan_action.triggered.connect(lambda: self._backend.toggleMode())

        menu.addSeparator()

        settings_action = menu.addAction("设置...")
        settings_action.triggered.connect(self._show_settings)

        menu.addSeparator()

        quit_action = menu.addAction("退出")
        quit_action.triggered.connect(self._quit)

        self._tray.setContextMenu(menu)
        self._tray.show()

    def _toggle_visible(self):
        if self._view.isVisible():
            self._view.hide()
        else:
            self._view.show()
            self._view.raise_()
            self._view.requestActivate()

    def _show_settings(self):
        # 通过 QML 属性触发设置弹出
        root = self._view.rootObject()
        if root:
            # 找到 settingsPopup 并打开
            popup = root.findChild(QObject, "settingsPopup")
            if popup:
                QMetaObject.invokeMethod(popup, "open")

    def _load_settings_to_qml(self):
        settings = self._backend.loadSettings()
        root = self._view.rootObject()
        if root:
            for key, val in settings.items():
                root.setProperty(key, val)

    def _quit(self):
        self._tray.hide()
        self._view.close()
        self._app.quit()

    def run(self):
        return self._app.exec()


def main():
    from PySide6.QtCore import QSize

    app = DesktopApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
