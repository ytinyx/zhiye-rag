"""DocumentStore unit tests inject both embedding and vector storage."""
from unittest.mock import Mock

from src.database.document_store import DocumentStore
from src.embeddings.vector_store import Document, SearchResult
from src.parsers.base import ParseResult


def make_store():
    embedding = Mock()
    embedding.embed_batch.side_effect = lambda texts: [[1.0, 0.0] for _ in texts]
    embedding.embed_text.return_value = [1.0, 0.0]
    embedding.get_dimension.return_value = 2
    embedding.get_model_name.return_value = "fake-embedding"
    vectors = Mock()
    vectors.add_documents.side_effect = lambda documents, embeddings: [doc.id for doc in documents]
    vectors.get_collection_stats.return_value = {"count": 2, "distance": "cosine"}
    return DocumentStore(embedding_model=embedding, vector_store=vectors), embedding, vectors


def test_add_parse_result_preserves_source_metadata():
    store, embedding, vectors = make_store()
    result = ParseResult(
        filename="sample.docx", total_pages=1, total_chunks=2, table_count=1,
        raw_text="Original fixture text", tables=[],
        chunks=[
            {"index": 0, "content": "A passage", "type": "text", "length": 9},
            {"index": 1, "content": "| A | B |", "type": "table", "length": 9, "page": 1},
        ], metadata={},
    )
    ids = store.add_parse_result(result, namespace="notes", content_hash="fixture-hash")
    assert ids == ["notes_fixture-hash_0", "notes_fixture-hash_1"]
    embedding.embed_batch.assert_called_once_with(["A passage", "| A | B |"])
    documents, embeddings = vectors.add_documents.call_args.args
    assert embeddings == [[1.0, 0.0], [1.0, 0.0]]
    assert documents[0].metadata["filename"] == "sample.docx"
    assert documents[0].metadata["namespace"] == "notes"
    assert documents[1].metadata["page"] == 1


def test_add_documents_sets_namespace_and_generates_unique_ids():
    store, embedding, vectors = make_store()
    ids = store.add_documents(["first", "second"], [{"source": "one.md"}], namespace="notes")
    assert len(set(ids)) == 2
    assert all(doc_id.startswith("notes_") for doc_id in ids)
    documents = vectors.add_documents.call_args.args[0]
    assert documents[0].metadata["source"] == "one.md"
    assert documents[1].metadata == {"namespace": "notes"}
    embedding.embed_batch.assert_called_once_with(["first", "second"])


def test_search_passes_namespace_filter_and_returns_sources():
    store, embedding, vectors = make_store()
    vectors.search.return_value = [
        SearchResult(Document("one", "A passage", {"namespace": "notes"}), 0.9, {}),
    ]
    results = store.search("question", top_k=2, namespace="notes")
    embedding.embed_text.assert_called_once_with("question")
    vectors.search.assert_called_once_with([1.0, 0.0], 2, {"namespace": "notes"})
    assert results == [{"id": "one", "content": "A passage",
                        "metadata": {"namespace": "notes"}, "score": 0.9}]


def test_stats_include_embedding_details():
    store, _, _ = make_store()
    assert store.get_stats() == {
        "count": 2, "distance": "cosine", "embedding_dim": 2, "embedding_model": "fake-embedding",
    }
