"""笔记/文档创建工具"""

from pathlib import Path

from pydantic import BaseModel, Field

from src.tools.base import BaseTool


class CreateNoteInput(BaseModel):
    title: str = Field(description="笔记标题")
    content: str = Field(description="笔记内容")
    folder: str = Field(default="notes", description="存储文件夹")


class NoteTool(BaseTool):
    name: str = "create_note"
    description: str = "创建笔记/文档。参数: title (标题), content (内容), folder (文件夹)"
    args_schema: type[BaseModel] = CreateNoteInput
    category: str = "productivity"

    def _run(self, title: str, content: str, folder: str = "notes") -> str:
        try:
            note_dir = Path(folder)
            note_dir.mkdir(parents=True, exist_ok=True)

            safe_title = "".join(c for c in title if c.isalnum() or c in " _-()（）")
            file_path = note_dir / f"{safe_title}.md"

            timestamp = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            full_content = f"# {title}\n\n> 创建时间: {timestamp}\n\n{content}\n"

            file_path.write_text(full_content, encoding="utf-8")
            return f"笔记已创建: {file_path}"
        except Exception as e:
            return f"创建笔记失败: {e}"
