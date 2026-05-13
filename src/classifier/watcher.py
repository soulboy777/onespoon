"""文件监控 — watchdog 封装"""

import threading
import time
from pathlib import Path
from typing import Callable, List, Optional

from loguru import logger
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class FileWatcher:
    """文件变化监控器"""

    def __init__(self) -> None:
        self._observer = Observer()
        self._handlers: List[Callable] = []
        self._running = False

    def watch(self, directory: str, recursive: bool = True) -> None:
        """开始监控目录"""
        path = Path(directory)
        if not path.exists():
            logger.warning(f"监控目录不存在: {directory}")
            return

        event_handler = _WatcherHandler(self._handlers)
        self._observer.schedule(event_handler, str(path), recursive=recursive)
        logger.info(f"开始监控: {directory}")

    def on_change(self, callback: Callable) -> None:
        """注册变化回调"""
        self._handlers.append(callback)

    def start(self) -> None:
        """启动监控（非阻塞）"""
        if not self._running:
            self._observer.start()
            self._running = True
            logger.info("文件监控已启动")

    def stop(self) -> None:
        """停止监控"""
        if self._running:
            self._observer.stop()
            self._observer.join()
            self._running = False
            logger.info("文件监控已停止")

    def start_blocking(self) -> None:
        """启动监控（阻塞当前线程）"""
        self.start()
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()


class _WatcherHandler(FileSystemEventHandler):
    def __init__(self, callbacks: List[Callable]) -> None:
        super().__init__()
        self._callbacks = callbacks

    def on_created(self, event: FileSystemEvent) -> None:
        for cb in self._callbacks:
            try:
                cb("created", event.src_path)
            except Exception as e:
                logger.error(f"文件监控回调出错: {e}")

    def on_modified(self, event: FileSystemEvent) -> None:
        for cb in self._callbacks:
            try:
                cb("modified", event.src_path)
            except Exception as e:
                logger.error(f"文件监控回调出错: {e}")

    def on_moved(self, event: FileSystemEvent) -> None:
        for cb in self._callbacks:
            try:
                cb("moved", event.src_path, event.dest_path)
            except Exception as e:
                logger.error(f"文件监控回调出错: {e}")
