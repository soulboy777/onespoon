"""命令行执行工具（沙箱模式）"""

import subprocess
from typing import ClassVar

from pydantic import BaseModel, Field

from src.tools.base import BaseTool


class ShellInput(BaseModel):
    command: str = Field(description="要执行的 shell 命令")
    working_dir: str = Field(default=".", description="工作目录")
    timeout: int = Field(default=30, description="超时秒数")


class ShellExecTool(BaseTool):
    name: str = "shell_exec"
    description: str = (
        "执行命令行指令（仅允许安全命令如 dir/ls/cat/type/echo/wc/find 等）。"
        "参数: command (命令), working_dir (工作目录), timeout (超时秒数)"
    )
    args_schema: type[BaseModel] = ShellInput
    category: str = "system"
    is_readonly: bool = False

    SAFE_PREFIXES: ClassVar[list] = [
        "dir", "ls", "cat", "type", "echo", "wc",
        "find", "which", "where", "pwd", "cd",
        "head", "tail", "sort", "uniq", "grep",
        "python --version", "pip list", "npm --version",
        "node --version", "git status", "git log",
        "git branch", "git diff",
    ]

    def _execute(self, command: str, working_dir: str = ".", timeout: int = 30) -> dict:
        cmd_lower = command.strip().lower()
        is_safe = any(cmd_lower.startswith(p) for p in self.SAFE_PREFIXES)
        if not is_safe:
            return {
                "status": "error",
                "error": f"命令 '{command}' 不在安全列表",
                "allowed": self.SAFE_PREFIXES,
                "command": command,
            }

        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=working_dir,
        )
        output = result.stdout.strip()
        if result.stderr:
            output += "\n[stderr]\n" + result.stderr.strip()
        return {
            "data": output or f"命令完成 (返回码: {result.returncode})",
            "command": command,
            "action": "shell",
            "returncode": result.returncode,
        }
