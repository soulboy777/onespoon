# Domain Map

Multi-context project. Two contexts:

| Context | Directory | CONTEXT.md |
|---------|-----------|------------|
| agent-engine | `/` (root) | `./CONTEXT.md` |
| rag | `src/rag/` | `src/rag/CONTEXT.md` |

**Decision rules:**
- Core agent logic, memory, compression, tools, storage, classifier, scheduler → `agent-engine`
- Knowledge base, document ingestion, vector retrieval, BM25 search → `rag`
