"""文档内容解析"""

from pathlib import Path
from typing import Dict, Optional


class DocumentParser:
    """解析各类文档，提取标题和内容"""

    def parse(self, file_path: str) -> Dict[str, str]:
        """解析文件，返回 {title, content, format}"""
        path = Path(file_path)
        result = {
            "title": path.stem,
            "content": "",
            "format": path.suffix.lower().lstrip("."),
            "file_path": str(path),
        }

        if not path.exists():
            result["content"] = "[文件不存在]"
            return result

        suffix = path.suffix.lower()

        if suffix == ".txt":
            result["content"] = self._parse_txt(path)
        elif suffix == ".md":
            result["content"] = self._parse_txt(path)
        elif suffix == ".docx":
            result["content"] = self._parse_docx(path)
        elif suffix == ".pdf":
            result["content"] = self._parse_pdf(path)
        elif suffix in (".py", ".js", ".ts", ".json", ".yaml", ".yml", ".html", ".css"):
            result["content"] = self._parse_txt(path)
        else:
            result["content"] = f"[不支持的文件格式: {suffix}]"

        return result

    def _parse_txt(self, path: Path) -> str:
        try:
            content = path.read_text(encoding="utf-8")
            return content[:5000]
        except UnicodeDecodeError:
            try:
                content = path.read_text(encoding="gbk")
                return content[:5000]
            except Exception:
                return "[无法读取文件编码]"

    def _parse_docx(self, path: Path) -> str:
        try:
            from docx import Document

            doc = Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs)[:5000]
        except ImportError:
            return "[python-docx 未安装]"
        except Exception as e:
            return f"[解析 docx 失败: {e}]"

    def _parse_pdf(self, path: Path) -> str:
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(str(path))
            text = ""
            for page in reader.pages[:10]:
                text += page.extract_text() or ""
            return text[:5000]
        except ImportError:
            return "[PyPDF2 未安装]"
        except Exception as e:
            return f"[解析 PDF 失败: {e}]"
