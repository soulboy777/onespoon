# Domain Map

Multi-context project. Four contexts:

| Context | Directory | CONTEXT.md |
|---------|-----------|------------|
| agent-engine | `/` (root) | `./CONTEXT.md` |
| rag | `src/rag/` | `src/rag/CONTEXT.md` |
| compression | `src/compression/` | `src/compression/CONTEXT.md` |
| planning | `src/planning/` | `src/planning/CONTEXT.md` |

**Decision rules:**
- Core agent logic, memory, tools, storage, classifier, scheduler → `agent-engine`
- Knowledge base, document ingestion, vector retrieval, BM25 search → `rag`
- Token counting, text summarization, context window/summarize/retrieve strategies → `compression`
- Plan/Execute dual mode, plan generation, step-by-step execution → `planning`
