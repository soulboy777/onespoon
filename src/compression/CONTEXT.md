# Context: compression

## Domain

上下文压缩子系统。确保 Agent 的输入不超过 LLM token 上限，通过多策略压缩管线智能裁剪和摘要上下文。

## Core Concepts

| 术语 | 定义 |
|------|------|
| **TokenCounter** | 基于 tiktoken 的精确 token 计数，使用 cl100k_base 编码 |
| **CompressionStrategy** | 压缩策略抽象基类：`should_apply()` + `compress()` |
| **WindowStrategy** | 窗口截断：保留最近的消息，从后往前截取直到不超限 |
| **SummarizeStrategy** | 摘要压缩：用 LLM 将长上下文浓缩为摘要 |
| **RetrieveStrategy** | 检索压缩：向量检索只取与当前问题最相关的片段 |
| **ContextCompressor** | 压缩管线编排器：按策略优先级依次执行，直到 token 达标 |
| **Summarizer** | LLM 摘要生成器，将长文本压缩为指定 token 数的摘要 |

## Compression Pipeline

```
原始上下文 (current_tokens)
  → 判断是否超 max_context_tokens
  → 按 strategy_sequence 顺序:
     [window → summarize → retrieve]
  → 每层压缩后重新计数
  → 达标则提前退出
  → 返回压缩后上下文
```

## Configuration

```yaml
compression:
  max_context_tokens: 8000          # 总上下文 token 上限
  strategy_sequence:                # 压缩策略优先级
    - window
    - summarize
    - retrieve
  summary_max_tokens: 500           # 单条摘要最大 token
```

## Key Files

- `src/compression/compressor.py` — 压缩管线编排
- `src/compression/strategies.py` — 三种压缩策略实现
- `src/compression/counter.py` — Token 计数
- `src/compression/summarizer.py` — LLM 摘要生成
