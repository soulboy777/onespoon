# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`CONTEXT-MAP.md`** at the repo root — multi-context layout. Map points to:
  - `CONTEXT.md` (root) — agent-engine: Core agent, memory, tools, storage, classifier, scheduler
  - `src/rag/CONTEXT.md` — rag: Knowledge base, ingestion, retrieval, BM25
  - `src/compression/CONTEXT.md` — compression: Token counting, summarization, window/summarize/retrieve strategies
  - `src/planning/CONTEXT.md` — planning: Plan/Execute dual mode, plan generation, step execution
- **`docs/adr/`** — system-wide architecture decisions.
- **`src/rag/docs/adr/`** — rag-specific architecture decisions.
- **`src/compression/docs/adr/`** — compression-specific architecture decisions.
- **`src/planning/docs/adr/`** — planning-specific architecture decisions.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The producer skill (`/grill-with-docs`) creates them lazily when terms or decisions actually get resolved.

## File structure

Multi-context repo:

```
/
├── CONTEXT-MAP.md
├── CONTEXT.md                          ← agent-engine
├── docs/adr/                           ← system-wide decisions
└── src/
    ├── rag/
    │   ├── CONTEXT.md                  ← rag
    │   └── docs/adr/                   ← rag-specific decisions
    ├── compression/
    │   ├── CONTEXT.md                  ← compression
    │   └── docs/adr/                   ← compression-specific decisions
    └── planning/
        ├── CONTEXT.md                  ← planning
        └── docs/adr/                   ← planning-specific decisions
```

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal — either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/grill-with-docs`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007 (event-sourced orders) — but worth reopening because…_
