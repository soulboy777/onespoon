"""桌面前端启动器 — QML 窗口 + 系统托盘 + 全局热键 + 双布局"""

import sys
from pathlib import Path

from PySide6.QtCore import QObject, QMetaObject, QSize, QUrl, Qt, QTimer
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQuick import QQuickView
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from loguru import logger

from src.ui.backend import UIBackend
from src.ui.config_manager import load_user_config, save_user_config
from src.ui.version import VERSION, BUILD_DATE, AUTHOR, REPO_URL
from src.utils.logger import setup_logging


class DesktopApp:
    """桌面应用主控制器"""

    LAYOUT_SIZES = {
        "sleep": QSize(680, 460),
        "classic": QSize(620, 420),
    }

    def __init__(self):
        setup_logging()

        self._app = QApplication(sys.argv)
        self._app.setApplicationName("Agent 开发助手")
        self._app.setApplicationVersion(VERSION)
        self._app.setQuitOnLastWindowClosed(False)

        self._user_config = load_user_config()
        self._layout = self._user_config.ui.layout or "sleep"

        self._view: QQuickView | None = None
        self._backend = UIBackend()
        self._backend._desktop_app = self

        self._create_window()
        self._setup_tray()

        self._view.show()

    def _create_window(self):
        if self._view:
            self._view.close()
            self._view.deleteLater()

        layout = self._layout
        size = self.LAYOUT_SIZES.get(layout, QSize(680, 460))
        qml_file = "MainSleep.qml" if layout == "sleep" else "Main.qml"

        self._view = QQuickView()
        self._view.setTitle("Agent 开发助手")
        self._view.setResizeMode(QQuickView.SizeRootObjectToView)
        self._view.setColor(Qt.transparent)
        self._view.setMinimumSize(size)
        self._view.setMaximumSize(size)
        self._view.setFlags(
            Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint
        )
        self._view.setDefaultAlphaBuffer(True)

        engine = self._view.engine()
        context = engine.rootContext()
        context.setContextProperty("uiBackend", self._backend)

        qml_dir = Path(__file__).resolve().parent / "qml"
        qml_path = str(qml_dir / qml_file)

        if not Path(qml_path).exists():
            logger.error(f"QML 文件不存在: {qml_path}")
            print(f"错误: QML 文件不存在: {qml_path}")
            sys.exit(1)

        self._view.setSource(QUrl.fromLocalFile(qml_path))

        screen = QGuiApplication.primaryScreen().availableGeometry()
        self._view.setPosition(
            (screen.width() - size.width()) // 2,
            screen.top() + 80,
        )

        self._load_settings_to_qml()

    def switch_layout(self, layout: str):
        """切换布局 sleep ↔ classic"""
        if layout not in self.LAYOUT_SIZES:
            logger.warning(f"未知布局: {layout}")
            return

        self._layout = layout
        self._user_config.ui.layout = layout
        save_user_config(self._user_config)

        self._create_window()
        self._view.show()
        self._view.raise_()
        self._view.requestActivate()
        logger.info(f"布局切换: {layout}")

    def _setup_tray(self):
        self._tray = QSystemTrayIcon()
        self._tray.setToolTip("Agent 开发助手")

        icon_path = self._get_project_root() / "icon" / "agent-dev.ico"
        if icon_path.exists():
            self._tray.setIcon(QIcon(str(icon_path)))
        else:
            self._tray.setIcon(QApplication.style().standardIcon(QApplication.style().SP_ComputerIcon))

        menu = QMenu()
        show_action = menu.addAction("显示/隐藏")
        show_action.triggered.connect(self._toggle_visible)

        menu.addSeparator()

        sleep_action = menu.addAction("切换布局 (sleep ↔ classic)")
        sleep_action.triggered.connect(self._toggle_layout)

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

    def _toggle_layout(self):
        new = "classic" if self._layout == "sleep" else "sleep"
        self.switch_layout(new)

    def _toggle_visible(self):
        if self._view.isVisible():
            self._view.hide()
        else:
            self._view.show()
            self._view.raise_()
            self._view.requestActivate()

    def _show_settings(self):
        root = self._view.rootObject()
        if root:
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

    def _get_project_root(self):
        return Path(__file__).resolve().parent.parent.parent

    def run(self):
        return self._app.exec()


def main():
    app = DesktopApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
