"""Optional installed-Chroma integration, always isolated in tmp_path."""
import pytest


@pytest.mark.integration
def test_chroma_store(tmp_path):
    pytest.importorskip("chromadb")
    from src.embeddings.chroma_store import ChromaVectorStore
    from src.embeddings.vector_store import Document

    store = ChromaVectorStore(collection_name="test_collection",
                              persist_directory=str(tmp_path / "chroma"), distance="cosine")
    documents = [
        Document("fruit", "A fruit note", {"category": "fruit"}),
        Document("vehicle", "A vehicle note", {"category": "vehicle"}),
    ]
    assert store.add_documents(documents, [[1.0, 0.0], [0.0, 1.0]]) == ["fruit", "vehicle"]
    assert store.get_collection_stats()["count"] == 2

    results = store.search([1.0, 0.0], top_k=2)
    assert results[0].document.id == "fruit"
    assert results[0].score == pytest.approx(1.0)
    filtered = store.search([1.0, 0.0], top_k=1, filter={"category": "vehicle"})
    assert [result.document.id for result in filtered] == ["vehicle"]
    assert store.contains_documents(documents)
    updated = Document("fruit", "An updated fruit note", {"category": "fruit"})
    assert not store.contains_documents([updated])
    store.add_documents([updated], [[1.0, 0.0]])
    assert store.contains_documents([updated])
    assert store.get_collection_stats()["count"] == 2
    assert store.clear()
    assert store.get_collection_stats()["count"] == 0
