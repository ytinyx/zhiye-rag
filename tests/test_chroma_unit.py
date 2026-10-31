"""Chroma configuration tests with an in-memory client substitute."""
import sys
from types import SimpleNamespace

from src.embeddings.chroma_store import ChromaVectorStore, get_chroma_client


def test_default_store_respects_configured_database_path(monkeypatch, tmp_path):
    observed = {}

    class Client:
        def get_or_create_collection(self, name, metadata):
            observed['collection'] = name
            return object()

    def persistent_client(**kwargs):
        observed.update(kwargs)
        return Client()

    monkeypatch.setenv('CHROMA_DB_PATH', str(tmp_path / 'isolated_database'))
    monkeypatch.setitem(sys.modules, 'chromadb', SimpleNamespace(
        PersistentClient=persistent_client, Settings=lambda **kwargs: kwargs,
    ))
    get_chroma_client.cache_clear()
    try:
        ChromaVectorStore(collection_name='test_collection')
        assert observed['path'] == str(tmp_path / 'isolated_database')
        assert observed['collection'] == 'test_collection'
        assert not (tmp_path / 'isolated_database').exists()
    finally:
        get_chroma_client.cache_clear()
