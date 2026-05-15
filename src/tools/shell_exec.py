"""命令行执行工具（沙箱模式）"""

import subprocess
from typing import Optional

from pydantic import BaseModel, Field

from src.tools.base import BaseTool


class ShellInput(BaseModel):
    command: str = Field(description="要执行的 shell 命令")
    working_dir: str = Field(default=".", description="工作目录")
    timeout: int = Field(default=30, description="超时秒数")


class ShellExecTool(BaseTool):
    name: str = "shell_exec"
    description: str = (
        "执行命令行指令（只读模式，仅允许 dir/ls/cat/type/echo/wc/find/which/where 等安全命令）。"
        "参数: command (命令), working_dir (工作目录), timeout (超时秒数)"
    )
    args_schema: type[BaseModel] = ShellInput
    category: str = "system"
    is_readonly: bool = False

    SAFE_PREFIXES = [
        "dir", "ls", "cat", "type", "echo", "wc",
        "find", "which", "where", "pwd", "cd",
        "head", "tail", "sort", "uniq", "grep",
        "python --version", "pip list", "npm --version",
        "node --version", "git status", "git log",
        "git branch", "git diff",
    ]

    def _run(
        self,
        command: str,
        working_dir: str = ".",
        timeout: int = 30,
    ) -> str:
        cmd_lower = command.strip().lower()

        is_safe = any(cmd_lower.startswith(p) for p in self.SAFE_PREFIXES)
        if not is_safe:
            return (
                f"安全限制: 命令 '{command}' 不在允许列表。\n"
                f"允许的命令前缀: {', '.join(self.SAFE_PREFIXES)}"
            )

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_dir,
            )
            output = result.stdout
            if result.stderr:
                output += "\n[stderr]\n" + result.stderr
            return output.strip() or f"命令执行完成 (返回码: {result.returncode})"
        except subprocess.TimeoutExpired:
            return f"命令超时 ({timeout}s): {command}"
        except Exception as e:
            return f"执行失败: {e}"
