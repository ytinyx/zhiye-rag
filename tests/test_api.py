"""HTTP and configuration regressions without model downloads or paid API calls."""
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from src.api import deps
from src.api.main import app
from src.api.routers import chat as chat_routes
from src.retrieval.search_service import CachedSearchService


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client




def test_health_and_supported_formats(client):
    assert client.get('/api/health/').json()['status'] == 'healthy'
    assert set(client.get('/api/document/supported-formats').json()['formats']) == {
        '.md', '.html', '.docx', '.pdf'
    }


def test_missing_api_key_has_actionable_error(client, monkeypatch):
    monkeypatch.setattr(deps.settings, 'LLM_PROVIDERS', {
        'zhipu': {'api_key': '', 'base_url': 'https://example.invalid', 'default_model': 'test'}
    })
    response = client.post('/api/chat/', json={
        'query': '知识库里有什么？', 'collection_name': 'sample', 'model': 'zhipu'
    })
    assert response.status_code == 503
    assert 'API Key' in response.json()['detail']


@pytest.mark.parametrize('cache_enabled', [None, 'true'])
def test_search_service_defaults_reuse_and_invalidation(monkeypatch, cache_enabled):
    if cache_enabled is None:
        monkeypatch.delenv('ENABLE_SEARCH_CACHE', raising=False)
    else:
        monkeypatch.setenv('ENABLE_SEARCH_CACHE', cache_enabled)
    monkeypatch.setenv('SEARCH_CACHE_MAX_SIZE', '7')
    monkeypatch.setattr(deps, 'get_embedding_model', lambda: object())
    monkeypatch.setattr(deps, 'DocumentStore', lambda **kwargs: SimpleNamespace(**kwargs))
    deps.invalidate_search_cache()
    try:
        first = deps.get_search_service('sample')
        assert deps.get_search_service('sample') is first
        assert isinstance(first, CachedSearchService) == (cache_enabled == 'true')
        if cache_enabled:
            assert first.cache.maxsize == 7
        deps.invalidate_search_cache()
        assert deps.get_search_service('sample') is not first
    finally:
        deps.invalidate_search_cache()


def test_configuration_has_defaults_and_reads_search_top_k():
    env = dict(os.environ, PYTHON_DOTENV_DISABLED='1', SEARCH_TOP_K='7')
    env.pop('DEFAULT_MODEL', None)
    result = subprocess.run(
        [sys.executable, '-c',
         'from src.api.config import settings; print(settings.DEFAULT_MODEL, settings.SEARCH_TOP_K)'],
        cwd=Path(__file__).resolve().parents[1], env=env, check=True,
        capture_output=True, text=True,
    )
    assert result.stdout.strip() == 'zhipu 7'


def test_chat_and_stream_use_retrieved_context(client, monkeypatch):
    results = [{'id': 'sample_0', 'content': '知页支持 Markdown 文档。', 'score': 0.9}]
    service = SimpleNamespace(search=lambda query, config: SimpleNamespace(results=results))

    class FakeLLM:
        def generate(self, messages, **kwargs):
            assert '知页支持 Markdown 文档。' in messages[0]['content']
            return {'content': '支持 Markdown。', 'token_used': {'total': 10, 'prompt': 6, 'completion': 4}, 'model': 'fake'}

        async def generate_stream(self, messages, **kwargs):
            assert '知页支持 Markdown 文档。' in messages[0]['content']
            yield '支持 '
            yield 'Markdown。'

    monkeypatch.setattr(chat_routes, 'get_llm', lambda model: FakeLLM())
    monkeypatch.setattr(chat_routes, 'get_search_service', lambda collection: service)
    payload = {'query': '支持什么文档？', 'collection_name': 'sample'}
    response = client.post('/api/chat/', json=payload)
    assert response.status_code == 200
    assert response.json()['answer'] == '支持 Markdown。'
    assert response.json()['sources'][0]['content'] == results[0]['content']
    stream = client.post('/api/chat/stream', json=payload)
    assert stream.status_code == 200
    assert stream.text == '支持 Markdown。'
