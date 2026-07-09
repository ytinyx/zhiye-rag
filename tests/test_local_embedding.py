"""Real local-model checks require --run-local-model."""
import math
import os

import pytest

pytestmark = pytest.mark.local_model


@pytest.fixture(scope="module")
def embedding_model():
    from src.embeddings.local_embedding import LocalEmbedding

    return LocalEmbedding(model_name=os.getenv("TEST_LOCAL_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5"),
                          device="cpu")


def test_model_info(embedding_model):
    assert embedding_model.get_model_name()
    assert embedding_model.get_dimension() > 0


def test_single_and_batch_embedding(embedding_model):
    texts = ["文档检索先查找相关内容。", "回答应当依据文档中的证据。"]
    vectors = embedding_model.embed_batch(texts)
    assert len(vectors) == len(texts)
    assert all(len(vector) == embedding_model.get_dimension() for vector in vectors)
    assert all(math.isfinite(value) for vector in vectors for value in vector)
    assert embedding_model.embed_text(texts[0]) == pytest.approx(vectors[0], abs=1e-5)


def test_vector_is_nonzero(embedding_model):
    vector = embedding_model.embed_text("本地向量模型测试")
    assert sum(value * value for value in vector) > 0
