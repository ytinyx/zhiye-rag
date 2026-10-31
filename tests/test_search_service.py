"""Retrieval filtering and cache tests do not load models or write databases."""
from unittest.mock import Mock

from src.retrieval.search_service import CachedSearchService, RetrievalConfig, SearchService


def make_service():
    store = Mock()
    store.search.return_value = [
        {"id": "one", "content": "first", "score": 0.9, "metadata": {}},
        {"id": "two", "content": "second", "score": 0.5, "metadata": {}},
        {"id": "three", "content": "third", "score": 0.1, "metadata": {}},
    ]
    store.get_stats.side_effect = lambda: {"count": 3}
    return SearchService(store), store


def test_search_filters_scores_and_passes_config():
    service, store = make_service()
    response = service.search("question", RetrievalConfig(top_k=2, min_score=0.6, namespace="notes"))
    store.search.assert_called_once_with(query="question", top_k=2, namespace="notes")
    assert response.query == "question"
    assert response.total_results == 1
    assert response.results[0]["id"] == "one"
    assert response.retrieval_time_ms >= 0


def test_default_config_and_empty_results():
    service, store = make_service()
    store.search.return_value = []
    response = service.search("missing")
    store.search.assert_called_once_with(query="missing", top_k=5, namespace=None)
    assert response.results == []
    assert response.total_results == 0


def test_cache_reuses_queries_and_separates_namespaces():
    service, store = make_service()
    cached = CachedSearchService(service, ttl=60, maxsize=10)
    first = cached.search("question", RetrievalConfig(namespace="one"))
    assert cached.search("question", RetrievalConfig(namespace="one")) == first
    cached.search("question", RetrievalConfig(namespace="two"))
    assert store.search.call_count == 2
    assert cached.get_stats()["cache_hits"] == 1
    assert cached.get_stats()["cache_misses"] == 2
    assert cached.clear_cache()
    assert cached.get_stats()["cache_hits"] == 0
    cached.search("question", RetrievalConfig(namespace="one"))
    assert store.search.call_count == 3
