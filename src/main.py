"""CLI 入口 — Agent 开发助手命令行"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.core.config import get_config, load_config, load_models
from src.core.llm import get_llm, get_llm_factory
from src.tools.registry import create_default_tools
from src.utils.logger import setup_logging

app = typer.Typer(
    name="agent-dev",
    help="桌面 AI 智能助手 — 支持多模型、记忆、文档分类、日程管理、RAG 知识库",
)
console = Console()

kb_app = typer.Typer(help="知识库管理")
app.add_typer(kb_app, name="kb")


@app.command()
def chat(
    model: Optional[str] = typer.Option(None, "--model", "-m", help="使用的模型名称"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出"),
) -> None:
    """启动交互式对话"""
    from src.core.agent import Agent
    from src.memory.manager import MemoryManager
    from src.planning.manager import PlanManager
    from src.planning.planner import PlanModeAgent
    from src.planning.executor import ExecuteModeAgent
    from src.rag.manager import KnowledgeBaseManager

    setup_logging()
    config = get_config()
    config.agent.verbose = verbose

    console.print(Panel.fit(
        f"[bold cyan]{config.agent.name}[/bold cyan]\n"
        "输入指令开始对话，输入 /exit 退出，输入 /help 查看帮助",
        title="Agent 开发助手",
    ))

    llm = get_llm(model)
    tools = create_default_tools()
    memory_manager = MemoryManager(llm)
    agent = Agent(llm, tools, memory_manager=memory_manager, mode="execute")
    plan_manager = PlanManager()
    planner = None
    executor = None

    # 初始化 RAG 工具
    try:
        kb_manager = KnowledgeBaseManager()
        for tool in tools:
            if hasattr(tool, "set_manager") and "rag" in getattr(tool, "category", ""):
                tool.set_manager(kb_manager)
            if hasattr(tool, "set_memory_manager"):
                tool.set_memory_manager(memory_manager)
    except Exception:
        kb_manager = None

    console.print("[dim]模型: {}[/dim]".format(model or config.llm.default_model))
    console.print("[dim]模式: [bold green]EXECUTE[/bold green] (输入 /plan 切换)[/dim]")
    console.print("[dim]工具: {}[/dim]".format(", ".join(t.name for t in tools)))
    console.print()

    while True:
        try:
            mode_label = f"[{'PLAN' if agent.mode == 'plan' else 'EXEC'}] "
            user_input = typer.prompt(mode_label + "You", prompt_suffix=" > ")
        except (KeyboardInterrupt, EOFError):
            console.print("\n再见！")
            break

        inp = user_input.strip()

        if inp == "/exit":
            console.print("再见！")
            break
        elif inp == "/desktop":
            console.print("[bold cyan]正在启动桌面 UI...[/bold cyan]")
            try:
                from src.ui.main_window import main as ui_main
                ui_main()
            except ImportError as e:
                console.print(f"[red]PySide6 未安装或 QML 加载失败: {e}[/red]")
                console.print("[dim]请运行: pip install PySide6[/dim]")
            except Exception as e:
                console.print(f"[red]UI 启动失败: {e}[/red]")
            continue
        elif inp == "/help":
            _show_help()
            continue
        elif inp == "/models":
            _list_models()
            continue
        elif inp == "/tools":
            _list_tools(agent.active_tools)
            continue
        elif inp == "/mode":
            current = agent.mode
            mode_name = "[bold green]EXECUTE[/bold green]" if current == "plan" else "[bold cyan]PLAN[/bold cyan]"
            console.print(f"当前模式: {mode_name}")
            continue

        # ---- Plan Commands ----
        elif inp == "/plan":
            agent.set_mode("plan")
            console.print(Panel(
                "[bold cyan]PLAN MODE[/bold cyan] — 只读模式，Agent 只能读取和搜索，不能修改文件\n"
                "输入 /plan new <描述> 创建新计划\n"
                "输入 /execute 切换回执行模式\n"
                "输入 /execute <id> 执行指定计划",
                border_style="cyan",
            ))
            continue

        elif inp == "/execute":
            agent.set_mode("execute")
            console.print(Panel(
                "[bold green]EXECUTE MODE[/bold green] — 全部工具可用\n"
                "输入 /plans 查看已有计划\n"
                "输入 /execute <id> 执行指定计划",
                border_style="green",
            ))
            continue

        elif inp.startswith("/plan"):
            parts = inp.split(maxsplit=2)
            if len(parts) < 2:
                _show_plan_help()
                continue

            sub = parts[1]
            if sub == "new":
                desc = parts[2] if len(parts) > 2 else ""
                if not desc:
                    console.print("[red]用法: /plan new <描述>[/red]")
                    continue
                if agent.mode != "plan":
                    agent.set_mode("plan")
                if planner is None:
                    planner = PlanModeAgent(llm, tools)
                with console.status("[bold cyan]生成计划中..."):
                    result = planner.generate_plan(desc)
                console.print()
                console.print(Panel(Markdown(result), title="Plan"))
                console.print()
                continue

            elif sub == "show":
                plan_id = parts[2] if len(parts) > 2 else ""
                if not plan_id:
                    plans = plan_manager.list_plans()
                    console.print(Panel(Markdown(plan_manager.to_display_list(plans)), title="计划列表"))
                    continue
                plan = plan_manager.get_plan(plan_id)
                if plan:
                    console.print(Panel(Markdown(plan_manager.to_detail_string(plan)), title=f"计划: {plan.title}"))
                else:
                    console.print(f"[red]计划不存在: {plan_id}[/red]")
                continue

            elif sub == "delete":
                plan_id = parts[2] if len(parts) > 2 else ""
                if not plan_id:
                    console.print("[red]用法: /plan delete <id>[/red]")
                    continue
                ok = plan_manager.delete_plan(plan_id)
                if ok:
                    console.print("[green]✓ 计划已删除[/green]")
                else:
                    console.print(f"[red]计划不存在: {plan_id}[/red]")
                continue

            else:
                _show_plan_help()
                continue

        elif inp == "/plans":
            plans = plan_manager.list_plans()
            console.print(Panel(Markdown(plan_manager.to_display_list(plans)), title="计划列表"))
            continue

        elif inp.startswith("/execute"):
            parts = inp.split(maxsplit=2)
            if len(parts) >= 2:
                sub = parts[1]
                if sub == "continue":
                    # 找最近未完成的计划
                    plans = plan_manager.list_plans()
                    running = [p for p in plans if p.status in ("running", "draft", "ready")]
                    done = [p for p in plans if p.status == "done"]
                    if running:
                        plan_id = running[0].id
                    elif done:
                        console.print("[dim]所有计划已完成[/dim]")
                        continue
                    else:
                        console.print("[dim]暂无计划[/dim]")
                        continue
                    if executor is None:
                        executor = ExecuteModeAgent(llm, tools)
                    with console.status("[bold green]执行计划中..."):
                        result = executor.continue_plan(plan_id)
                    console.print()
                    console.print(Panel(Markdown(result), title="执行结果"))
                    console.print()
                    continue

                else:
                    plan_id = sub
                    if executor is None:
                        executor = ExecuteModeAgent(llm, tools)
                    with console.status("[bold green]执行计划中..."):
                        result = executor.execute_plan(plan_id)
                    console.print()
                    console.print(Panel(Markdown(result), title="执行结果"))
                    console.print()
                    continue
            else:
                plans = plan_manager.list_plans()
                ready = [p for p in plans if p.status in ("ready", "draft")]
                if ready:
                    console.print(Panel(Markdown(plan_manager.to_display_list(ready)), title="可选计划"))
                    console.print("[dim]输入 /execute <id> 执行指定计划[/dim]")
                else:
                    console.print("[dim]没有可执行的计划，先用 /plan new 创建[/dim]")
                continue

        elif not inp:
            continue

        with console.status("[bold green]思考中..."):
            result = agent.run(inp)

        output = result.get("output", "无输出")
        main_text = result.get("main", "")
        sub_text = result.get("sub", "")

        console.print()
        if main_text:
            console.print(Panel(Markdown(main_text), title="Agent", border_style="cyan"))
        if sub_text:
            console.print(Panel(Markdown(f"_{sub_text}_"), border_style="dim", padding=(0, 2)))
        if not main_text and not sub_text:
            console.print(Panel(Markdown(output), title="Agent"))
        console.print()


@app.command()
def models() -> None:
    """列出可用模型"""
    _list_models()


@app.command()
def classify(
    directory: str = typer.Argument(..., help="要分类的目录"),
    watch: bool = typer.Option(False, "--watch", "-w", help="持续监控"),
) -> None:
    """对目录中的文件进行分类"""
    setup_logging()
    from src.classifier.categorizer import Categorizer

    cat = Categorizer()
    cat.set_base_dir(directory)

    console.print(f"[bold]正在分类目录: {directory}[/bold]")
    results = cat.batch_classify(directory)

    table = Table(title="分类结果")
    table.add_column("文件", style="cyan")
    table.add_column("格式", style="dim")
    table.add_column("类别", style="green")
    table.add_column("操作", style="yellow")

    for r in results:
        table.add_row(r["file"], r["format"], r["category"], "已移动" if r["moved"] else "跳过")

    console.print(table)

    if watch:
        cat.watch_directory(directory)
        console.print("[bold yellow]持续监控中... Ctrl+C 退出[/bold yellow]")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            cat.stop_watching()
            console.print("监控已停止")


@app.command()
def schedule(
    title: str = typer.Option(..., "--title", "-t", help="提醒标题"),
    time_str: str = typer.Option(..., "--at", "-a", help="提醒时间 (YYYY-MM-DD HH:MM)"),
    description: str = typer.Option("", "--desc", "-d", help="提醒描述"),
) -> None:
    """添加日程提醒"""
    from datetime import datetime

    setup_logging()
    from src.scheduler.schedule import ScheduleManager

    try:
        trigger_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    except ValueError:
        console.print("[red]时间格式错误，请使用: YYYY-MM-DD HH:MM[/red]")
        raise typer.Exit(1)

    mgr = ScheduleManager()
    mgr.start()
    job_id = mgr.add_reminder(title, trigger_time, description=description)

    console.print(f"[green]✓ 提醒已添加[/green]")
    console.print(f"  标题: {title}")
    console.print(f"  时间: {trigger_time}")
    console.print(f"  任务ID: {job_id}")


# ══════════════════════════════════════════════
#  知识库管理命令
# ══════════════════════════════════════════════

@kb_app.command("create")
def kb_create(
    name: str = typer.Option(..., "--name", "-n", help="知识库名称"),
    description: str = typer.Option("", "--desc", "-d", help="知识库描述"),
    strategy: str = typer.Option("recursive", "--strategy", "-s", help="分块策略 (fixed/recursive/sentence)"),
    chunk_size: int = typer.Option(500, "--chunk-size", help="分块大小"),
) -> None:
    """创建知识库"""
    setup_logging()
    load_config()

    from src.rag.manager import KnowledgeBaseManager

    mgr = KnowledgeBaseManager()
    kb = mgr.create(
        name=name,
        description=description,
        chunk_strategy=strategy,
        chunk_size=chunk_size,
    )
    console.print(f"[green]✓ 知识库已创建: {kb.name}[/green]")
    console.print(f"  集合名: {kb.collection_name}")
    console.print(f"  分块策略: {kb.chunk_strategy} ({kb.chunk_size}字符)")


@kb_app.command("list")
def kb_list() -> None:
    """列出所有知识库"""
    setup_logging()
    load_config()

    from src.rag.manager import KnowledgeBaseManager

    mgr = KnowledgeBaseManager()
    kbs = mgr.list_all()

    if not kbs:
        console.print("[dim]暂无知识库[/dim]")
        return

    table = Table(title="知识库列表")
    table.add_column("名称", style="cyan")
    table.add_column("描述")
    table.add_column("文档数", style="green")
    table.add_column("分块数", style="green")
    table.add_column("策略", style="dim")

    for kb in kbs:
        table.add_row(
            kb.name,
            kb.description or "-",
            str(kb.document_count or 0),
            str(kb.chunk_count or 0),
            kb.chunk_strategy,
        )

    console.print(table)


@kb_app.command("ingest")
def kb_ingest(
    kb_name: str = typer.Option(..., "--kb", "-k", help="目标知识库名称"),
    path: str = typer.Option(..., "--path", "-p", help="文件或目录路径"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="递归导入子目录"),
    tags: str = typer.Option("", "--tags", help="标签，逗号分隔"),
) -> None:
    """向知识库导入文档"""
    setup_logging()
    load_config()

    from src.rag.manager import KnowledgeBaseManager

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    mgr = KnowledgeBaseManager()

    import os
    file_path = Path(path)
    if not file_path.exists():
        console.print(f"[red]路径不存在: {path}[/red]")
        raise typer.Exit(1)

    if file_path.is_file():
        with console.status(f"[bold green]正在摄取: {path}..."):
            doc = mgr.ingest_file(kb_name, str(file_path), tags=tag_list)
        console.print(f"[green]✓ 文档已导入: {doc.title} ({doc.chunk_count} 分块)[/green]")
    elif file_path.is_dir():
        pattern = "**/*" if recursive else "*.*"
        with console.status(f"[bold green]正在摄取目录: {path}..."):
            docs = mgr.ingest_directory(kb_name, str(file_path), glob_pattern=pattern, tags=tag_list)
        console.print(f"[green]✓ 已导入 {len(docs)} 个文档[/green]")
        for d in docs[:10]:
            console.print(f"  - {d.title} ({d.chunk_count} 分块)")
        if len(docs) > 10:
            console.print(f"  ... 还有 {len(docs) - 10} 个文档")


@kb_app.command("search")
def kb_search(
    kb_name: str = typer.Option("", "--kb", "-k", help="知识库名称，留空搜索全部"),
    query: str = typer.Option(..., "--query", "-q", help="搜索内容"),
    top_k: int = typer.Option(5, "--top", "-t", help="返回条数"),
) -> None:
    """搜索知识库"""
    setup_logging()
    load_config()

    from src.rag.manager import KnowledgeBaseManager

    mgr = KnowledgeBaseManager()

    with console.status("[bold green]搜索中..."):
        if kb_name:
            results = mgr.search(kb_name, query, top_k=top_k)
        else:
            results = mgr.search_all(query, top_k=top_k)

    if not results:
        console.print("[dim]未找到相关内容[/dim]")
        return

    console.print(f"\n[bold]搜索结果: {len(results)} 条[/bold]\n")
    for i, r in enumerate(results, 1):
        meta = r.get("metadata", {})
        source_name = meta.get("doc_title", meta.get("source", ""))
        console.print(f"[cyan]── 结果 {i} [{r.get('source', '')}] score={r.get('score', 0):.4f}[/cyan]")
        if source_name:
            console.print(f"[dim]来源: {source_name}[/dim]")
        console.print(r.get("content", "")[:300])
        console.print()


@kb_app.command("delete")
def kb_delete(
    name: str = typer.Option(..., "--name", "-n", help="要删除的知识库名称"),
) -> None:
    """删除知识库"""
    setup_logging()
    load_config()

    from src.rag.manager import KnowledgeBaseManager

    mgr = KnowledgeBaseManager()
    ok = mgr.delete(name)

    if ok:
        console.print(f"[green]✓ 知识库已删除: {name}[/green]")
    else:
        console.print(f"[red]知识库不存在: {name}[/red]")


@kb_app.command("stats")
def kb_stats(
    name: str = typer.Option(..., "--name", "-n", help="知识库名称"),
) -> None:
    """查看知识库统计"""
    setup_logging()
    load_config()

    from src.rag.manager import KnowledgeBaseManager

    mgr = KnowledgeBaseManager()
    stats = mgr.get_stats(name)
    if not stats:
        console.print(f"[red]知识库不存在: {name}[/red]")
        return

    for key, val in stats.items():
        console.print(f"[cyan]{key}:[/cyan] {val}")


@kb_app.command("docs")
def kb_docs(
    name: str = typer.Option(..., "--kb", "-k", help="知识库名称"),
) -> None:
    """列出知识库中的文档"""
    setup_logging()
    load_config()

    from src.rag.manager import KnowledgeBaseManager

    mgr = KnowledgeBaseManager()
    docs = mgr.list_documents(name)

    if not docs:
        console.print("[dim]暂无文档[/dim]")
        return

    table = Table(title=f"{name} — 文档列表")
    table.add_column("标题", style="cyan")
    table.add_column("类型", style="dim")
    table.add_column("来源")
    table.add_column("分块数", style="green")
    table.add_column("导入时间", style="dim")

    for d in docs:
        table.add_row(
            d["title"],
            d["file_type"],
            d["source"][:60],
            str(d["chunk_count"]),
            d["ingested_at"][:19],
        )

    console.print(table)


@app.command()
def init() -> None:
    """初始化数据库和配置"""
    setup_logging()
    from src.storage.database import init_db
    from src.rag.database import init_rag_db

    load_config()
    load_models()

    init_db()
    init_rag_db()

    # 初始化 Planning 表
    from src.planning.manager import PlanManager
    PlanManager().init_db()

    console.print("[green]✓ 主数据库已初始化[/green]")
    console.print("[green]✓ RAG 知识库已初始化[/green]")
    console.print("[green]✓ 计划系统已初始化[/green]")
    console.print("[green]✓ 配置已加载[/green]")

    # 创建必要目录
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    (data_dir / "logs").mkdir(exist_ok=True)
    (data_dir / "notes").mkdir(exist_ok=True)
    (data_dir / "plans").mkdir(exist_ok=True)
    console.print("[green]✓ 工作目录已创建[/green]")


def _show_help() -> None:
    help_text = """
**模式命令:**
- `/plan` — 切换到计划模式（只读）
- `/execute` — 切换到执行模式
- `/mode` — 查看当前模式

**计划命令:**
- `/plan new <描述>` — 创建新计划
- `/plan show [id]` — 查看计划详情
- `/plan delete <id>` — 删除计划
- `/plans` — 列出所有计划
- `/execute <id>` — 执行指定计划
- `/execute continue` — 继续上次未完成的计划

**其他命令:**
- `/exit` — 退出对话
- `/help` — 显示此帮助
- `/models` — 列出可用模型
- `/tools` — 列出可用工具

**使用方式:**
直接输入自然语言指令即可，Agent 会自动选择合适的工具执行。
"""
    console.print(Panel(Markdown(help_text), title="帮助"))


def _list_models() -> None:
    factory = get_llm_factory()
    models_list = factory.list_models()

    table = Table(title="可用模型")
    table.add_column("名称", style="cyan")
    table.add_column("Provider", style="green")
    table.add_column("Model ID", style="dim")
    table.add_column("说明")

    for m in models_list:
        table.add_row(m.name, m.provider, m.model_id, m.description)

    console.print(table)


def _list_tools(tools) -> None:
    table = Table(title="可用工具")
    table.add_column("工具名", style="cyan")
    table.add_column("类别", style="green")
    table.add_column("只读", style="yellow")
    table.add_column("描述")

    for t in tools:
        readonly = "✓" if getattr(t, "is_readonly", True) else "✗"
        table.add_row(t.name, t.category, readonly, t.description[:70])

    console.print(table)


def _show_plan_help() -> None:
    text = """
**计划命令:**
- `/plan new <描述>` — 创建新计划
- `/plan show [id]` — 查看计划详情
- `/plan delete <id>` — 删除计划
- `/plans` — 列出所有计划
"""
    console.print(Panel(Markdown(text), title="Plan 命令"))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
