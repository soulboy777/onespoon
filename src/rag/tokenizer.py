"""分词器 — 中英文混合分词"""

import re


def tokenize(text: str) -> list:
    """简单中英文混合分词

    英文按空格/NLTK分词，中文按单字+常用词组切分。
    用于 BM25 关键词索引。
    """
    if not text:
        return []

    tokens = []

    # 分离中英文混合
    pattern = re.compile(r'[a-zA-Z0-9]+|[\u4e00-\u9fff]+|[^\s]')
    matches = pattern.findall(text)

    for m in matches:
        if re.match(r'[a-zA-Z0-9]+', m):
            # 英文单词，转小写
            tokens.append(m.lower())
        elif re.match(r'[\u4e00-\u9fff]+', m):
            # 中文：单字切分
            for ch in m:
                tokens.append(ch)
            # 也保留原始序列作为 token
            tokens.append(m)
        else:
            tokens.append(m)

    # 去重保序
    seen = set()
    result = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            result.append(t)

    return result
