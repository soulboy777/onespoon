# Context: rag

## Domain

独立 RAG 知识库子系统。与对话记忆完全解耦，拥有独立的 SQLite 数据库和 ChromaDB 向量库。

## Core Concepts

| 术语 | 定义 |
|------|------|
| **KnowledgeBase** | 一个知识库 = 一个 ChromaDB 集合 + SQLite 元数据 |
| **Document** | 文档元数据（来源路径/URL、标题、类型、标签） |
| **Chunk** | 文档分块（内容、序号、embedding_id、BM25 索引） |
| **Ingestion Pipeline** | 摄取管线：Load → Parse → Chunk → Embed → Store |
| **Chunker** | 分块策略：fixed（固定大小）、recursive（递归分隔符）、sentence（句子边界） |
| **Embedder** | 嵌入模型适配：OpenAI / Ollama / 兼容接口 |
| **Hybrid Retriever** | 混合检索：ChromaDB 向量 + rank_bm25 关键词 → RRF 融合 |
| **BM25** | 关键词检索算法，rank_bm25 库实现，中英文混合分词 |
| **RRF** | Reciprocal Rank Fusion，融合向量和关键词排序 |

## Architecture

```
IngestionPipeline
  → Chunker (fixed/recursive/sentence)
  → Embedder (OpenAI/Ollama/compatible)
  → ChromaDB (data/chroma_kb/) + SQLite (data/knowledge.db) + BM25 Index

HybridRetriever
  → ChromaDB vector search (top-10)
  → BM25 keyword search (top-10)
  → RRF fusion → top-5 results
```

## Key Files

- `src/rag/manager.py` — 知识库管理 API
- `src/rag/ingestion.py` — 摄取管线
- `src/rag/retriever.py` — 混合检索器
- `src/rag/chunker.py` — 分块器
- `src/rag/embedder.py` — 嵌入适配器
- `src/rag/models.py` — ORM 模型
- `src/rag/database.py` — 独立 SQLite 引擎
