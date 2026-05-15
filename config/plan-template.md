# Plan: {{title}}

**Status**: {{status}}
**Created**: {{created_at}}

## Goal

{{description}}

## Steps

{% for step in steps %}
### Step {{step.index}}: {{step.name}}
- **Action**: {{step.action}}
- **Target**: `{{step.target}}`
- **Expected**: {{step.expected}}
- **Depends on**: {{step.depends_on}}

{% endfor %}
## Affected Files

{% for file in affected_files %}
- `{{file}}`
{% endfor %}

## Notes

{{notes}}
