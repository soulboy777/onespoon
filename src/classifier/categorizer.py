"""文档分类执行器 — 整合监控、解析、规则引擎"""

import shutil
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from src.classifier.parser import DocumentParser
from src.classifier.rules import RuleEngine
from src.classifier.watcher import FileWatcher
from src.core.config import get_config


class Categorizer:
    """文档自动分类执行器"""

    def __init__(self) -> None:
        config = get_config()
        self._engine = RuleEngine()
        self._parser = DocumentParser()
        self._watcher = FileWatcher()
        self._base_dir = Path(".")

        if config.classifier.auto_categorize:
            self._watcher.on_change(self._on_file_change)

    def set_base_dir(self, directory: str) -> None:
        self._base_dir = Path(directory)

    def classify_file(self, file_path: str) -> Dict[str, str]:
        """分类单个文件并移动"""
        info = self._parser.parse(file_path)
        category = self._engine.classify(file_path)

        result = {
            "file": file_path,
            "title": info["title"],
            "format": info["format"],
            "category": category or "未分类",
            "moved": False,
        }

        if category:
            target_dir = self._base_dir / category
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / Path(file_path).name

            if target_path.exists():
                logger.debug(f"目标已存在，跳过: {target_path}")
            else:
                shutil.move(file_path, target_path)
                result["moved"] = True
                logger.info(f"分类: {file_path} → {target_path}")

        return result

    def batch_classify(self, directory: str) -> List[Dict[str, str]]:
        """批量分类目录下所有文件"""
        path = Path(directory)
        if not path.exists():
            return []

        results = []
        for item in path.iterdir():
            if item.is_file():
                result = self.classify_file(str(item))
                results.append(result)

        return results

    def add_custom_rule(
        self,
        name: str,
        pattern: str,
        target_folder: str,
        match_type: str = "regex",
    ) -> None:
        self._engine.add_custom_rule(name, pattern, target_folder, match_type)

    def list_rules(self) -> List[dict]:
        return self._engine.list_rules()

    def watch_directory(self, directory: str) -> None:
        """开始监控目录并自动分类"""
        self._base_dir = Path(directory)
        self._watcher.watch(directory)
        self._watcher.start()
        logger.info(f"自动分类已启用: {directory}")

    def stop_watching(self) -> None:
        self._watcher.stop()

    def _on_file_change(self, event_type: str, *args) -> None:
        if event_type == "created":
            file_path = args[0]
            time.sleep(1)
            self.classify_file(file_path)
