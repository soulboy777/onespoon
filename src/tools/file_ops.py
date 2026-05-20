"""文件操作工具"""

from pathlib import Path

from pydantic import BaseModel, Field

from src.tools.base import BaseTool


class ReadFileInput(BaseModel):
    file_path: str = Field(description="要读取的文件路径")
    encoding: str = Field(default="utf-8", description="文件编码")


class WriteFileInput(BaseModel):
    file_path: str = Field(description="要写入的文件路径")
    content: str = Field(description="要写入的内容")
    encoding: str = Field(default="utf-8", description="文件编码")


class ListDirInput(BaseModel):
    directory: str = Field(default=".", description="要列出内容的目录路径")


class MoveFileInput(BaseModel):
    source: str = Field(description="源文件路径")
    destination: str = Field(description="目标文件路径")


class DeleteFileInput(BaseModel):
    file_path: str = Field(description="要删除的文件路径")


class ReadFileTool(BaseTool):
    name: str = "read_file"
    description: str = "读取文件内容。参数: file_path (文件路径), encoding (编码，默认utf-8)"
    args_schema: type[BaseModel] = ReadFileInput
    category: str = "file"

    def _execute(self, file_path: str, encoding: str = "utf-8") -> dict:
        path = Path(file_path)
        if not path.exists():
            return {"status": "error", "error": f"文件不存在: {file_path}", "file": file_path}
        content = path.read_text(encoding=encoding)
        if len(content) > 10000:
            content = content[:10000] + f"\n... (已截断，共 {len(content)} 字符)"
        return {"data": content, "file": file_path, "action": "read", "size": len(content)}


class WriteFileTool(BaseTool):
    name: str = "write_file"
    description: str = "写入文件。参数: file_path (文件路径), content (内容), encoding (编码)"
    args_schema: type[BaseModel] = WriteFileInput
    category: str = "file"
    is_readonly: bool = False

    def _execute(self, file_path: str, content: str, encoding: str = "utf-8") -> dict:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)
        return {"data": f"写入成功: {file_path}", "file": file_path, "action": "write", "size": len(content)}


class ListDirTool(BaseTool):
    name: str = "list_dir"
    description: str = "列出目录内容。参数: directory (目录路径)"
    args_schema: type[BaseModel] = ListDirInput
    category: str = "file"

    def _execute(self, directory: str = ".") -> dict:
        path = Path(directory)
        if not path.exists():
            return {"status": "error", "error": f"目录不存在: {directory}", "file": directory}
        items = []
        for item in sorted(path.iterdir()):
            prefix = "📁 " if item.is_dir() else "📄 "
            items.append(f"{prefix}{item.name}")
        return {"data": "\n".join(items) if items else "目录为空", "file": directory, "action": "list", "count": len(items)}


class MoveFileTool(BaseTool):
    name: str = "move_file"
    description: str = "移动/重命名文件。参数: source (源路径), destination (目标路径)"
    args_schema: type[BaseModel] = MoveFileInput
    category: str = "file"
    is_readonly: bool = False

    def _execute(self, source: str, destination: str) -> dict:
        src = Path(source)
        if not src.exists():
            return {"status": "error", "error": f"源文件不存在: {source}", "file": source}
        dst = Path(destination)
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        return {"data": f"已移动: {source} → {destination}", "file": source, "dest": destination, "action": "move"}


class DeleteFileTool(BaseTool):
    name: str = "delete_file"
    description: str = "删除文件。参数: file_path (文件路径)"
    args_schema: type[BaseModel] = DeleteFileInput
    category: str = "file"
    is_readonly: bool = False

    def _execute(self, file_path: str) -> dict:
        path = Path(file_path)
        if not path.exists():
            return {"status": "error", "error": f"文件不存在: {file_path}", "file": file_path}
        path.unlink()
        return {"data": f"已删除: {file_path}", "file": file_path, "action": "delete"}
