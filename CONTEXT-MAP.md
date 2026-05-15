# Domain Map

Multi-context project. Three contexts:

| Context | Directory | CONTEXT.md |
|---------|-----------|------------|
| agent-engine | `/` (root) | `./CONTEXT.md` |
| rag | `src/rag/` | `src/rag/CONTEXT.md` |
| compression | `src/compression/` | `src/compression/CONTEXT.md` |

**Decision rules:**
- Core agent logic, memory, tools, storage, classifier, scheduler → `agent-engine`
- Knowledge base, document ingestion, vector retrieval, BM25 search → `rag`
- Token counting, text summarization, context window/summarize/retrieve strategies → `compression`
