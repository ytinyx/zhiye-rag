"""Remote embedding smoke test; requires explicit CLI opt-in and credentials."""
import math
import os

import pytest


@pytest.mark.external_api
def test_zhipu_embedding():
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        pytest.skip("Set ZHIPU_API_KEY explicitly to run this test")
    from src.embeddings.openai_embedding import OpenAIEmbedding

    embedder = OpenAIEmbedding(
        model=os.getenv("ZHIPU_EMBEDDING_MODEL", "embedding-3"),
        api_key=api_key,
        base_url=os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/"),
    )
    vectors = embedder.embed_batch(["本地文档检索测试"])
    assert len(vectors) == 1
    assert vectors[0] and all(math.isfinite(value) for value in vectors[0])
