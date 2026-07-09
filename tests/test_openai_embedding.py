"""Mocked OpenAI-compatible embedding tests plus an explicit remote smoke test."""
import math
import os
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.embeddings import openai_embedding


def test_batch_embedding_parameters_and_result(monkeypatch):
    create = Mock(return_value=SimpleNamespace(data=[
        SimpleNamespace(embedding=[1.0, 0.0]), SimpleNamespace(embedding=[0.0, 1.0]),
    ]))
    client = SimpleNamespace(embeddings=SimpleNamespace(create=create))
    monkeypatch.setattr(openai_embedding, "OpenAI", Mock(return_value=client))
    embedder = openai_embedding.OpenAIEmbedding("test-model", "test-key", "https://example.invalid", dimension=2)
    assert embedder.embed_batch(["first", "second"]) == [[1.0, 0.0], [0.0, 1.0]]
    create.assert_called_once_with(input=["first", "second"], model="test-model", dimensions=2)
    assert embedder.get_dimension() == 2
    assert embedder.get_model_name() == "test-model"


def test_single_embedding_omits_unset_dimensions(monkeypatch):
    create = Mock(return_value=SimpleNamespace(data=[SimpleNamespace(embedding=[0.5, 0.5])]))
    monkeypatch.setattr(openai_embedding, "OpenAI",
                        Mock(return_value=SimpleNamespace(embeddings=SimpleNamespace(create=create))))
    embedder = openai_embedding.OpenAIEmbedding("test-model", "test-key", "https://example.invalid")
    assert embedder.embed_text("sample") == [0.5, 0.5]
    create.assert_called_once_with(input=["sample"], model="test-model")


@pytest.mark.external_api
def test_dashscope_embedding():
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        pytest.skip("Set DASHSCOPE_API_KEY explicitly to run this test")
    embedder = openai_embedding.OpenAIEmbedding(
        model=os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v3"),
        api_key=api_key,
        base_url=os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    )
    vectors = embedder.embed_batch(["本地文档检索测试"])
    assert len(vectors) == 1
    assert vectors[0] and all(math.isfinite(value) for value in vectors[0])
