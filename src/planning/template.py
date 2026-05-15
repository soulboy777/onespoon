"""计划模板生成器 — 渲染计划文件"""

from typing import Any, Dict, List, Optional


class PlanTemplate:
    """计划模板"""

    DEFAULT_TEMPLATE = """# Plan: {title}

**Status**: {status}
**Created**: {created_at}

## Goal

{description}

## Steps

{steps_section}

## Affected Files

{affected_files}

## Notes

{notes}
"""

    STEP_TEMPLATE = """### Step {index}: {name}
- **Action**: {action}
- **Target**: {target}{target_value}
- **Expected**: {expected}
- **Dependencies**: {depends_on}
"""

    def render(
        self,
        title: str,
        description: str = "",
        steps: Optional[List[Dict[str, Any]]] = None,
        affected_files: str = "待确定",
        notes: str = "",
        status: str = "draft",
        created_at: str = "",
    ) -> str:
        steps_section = ""
        if steps:
            for i, step in enumerate(steps, 1):
                target = step.get("target", "")
                target_value = f" `{target}`" if target else ""
                depends = step.get("depends_on", "")
                steps_section += self.STEP_TEMPLATE.format(
                    index=i,
                    name=step.get("name", f"Step {i}"),
                    action=step.get("action", ""),
                    target=step.get("target", ""),
                    target_value=target_value,
                    expected=step.get("expected", ""),
                    depends_on=f"Step {depends}" if depends else "无",
                )

        return self.DEFAULT_TEMPLATE.format(
            title=title,
            status=status,
            created_at=created_at,
            description=description or "待补充",
            steps_section=steps_section or "待补充",
            affected_files=affected_files or "待确定",
            notes=notes or "无",
        )
