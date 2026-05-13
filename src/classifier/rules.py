"""文档分类规则引擎"""

import re
from pathlib import Path
from typing import Callable, Dict, List, Optional


class Rule:
    """单条分类规则"""

    def __init__(
        self,
        name: str,
        condition: Callable,
        target_folder: str,
        priority: int = 0,
    ) -> None:
        self.name = name
        self.condition = condition
        self.target_folder = target_folder
        self.priority = priority


class RuleEngine:
    """规则引擎 — 匹配文件到目标文件夹"""

    def __init__(self) -> None:
        self._rules: List[Rule] = []
        self._init_default_rules()

    def _init_default_rules(self) -> None:
        """内置默认规则"""
        # 按扩展名分类
        ext_rules = {
            "图片": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
            "文档": [".doc", ".docx", ".pdf", ".txt", ".md", ".rst"],
            "表格": [".xls", ".xlsx", ".csv"],
            "演示": [".ppt", ".pptx"],
            "代码": [".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".go", ".rs"],
            "配置": [".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"],
            "压缩": [".zip", ".rar", ".7z", ".tar", ".gz"],
            "音频": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
            "视频": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"],
        }

        for folder, exts in ext_rules.items():
            for ext in exts:
                self.add_rule(Rule(
                    name=f"扩展名: {ext} → {folder}",
                    condition=lambda f, e=ext: Path(f).suffix.lower() == e,
                    target_folder=folder,
                ))

    def add_rule(self, rule: Rule) -> None:
        self._rules.append(rule)
        self._rules.sort(key=lambda r: -r.priority)

    def remove_rule(self, name: str) -> bool:
        for i, r in enumerate(self._rules):
            if r.name == name:
                self._rules.pop(i)
                return True
        return False

    def add_custom_rule(
        self,
        name: str,
        pattern: str,
        target_folder: str,
        match_type: str = "regex",
    ) -> None:
        """添加自定义规则"""
        if match_type == "regex":
            compiled = re.compile(pattern)
            condition = lambda f, c=compiled: bool(c.search(Path(f).name))
        elif match_type == "extension":
            condition = lambda f, ext=pattern: Path(f).suffix.lower() == ext.lower()
        elif match_type == "contains":
            condition = lambda f, kw=pattern: kw.lower() in Path(f).name.lower()
        else:
            raise ValueError(f"不支持匹配类型: {match_type}")

        self.add_rule(Rule(name=name, condition=condition, target_folder=target_folder, priority=10))

    def classify(self, file_path: str) -> Optional[str]:
        """分类文件，返回目标文件夹名"""
        for rule in self._rules:
            try:
                if rule.condition(file_path):
                    return rule.target_folder
            except Exception:
                continue
        return None

    def list_rules(self) -> List[dict]:
        return [
            {"name": r.name, "target": r.target_folder, "priority": r.priority}
            for r in self._rules
        ]
