"""上传接口回归测试：使用真实存储逻辑和内存 Chroma 替身，不下载模型。"""
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routers import document
from src.embeddings import chroma_store
from src.parsers.base import ParseResult


class MemoryCollection:
    def __init__(self, state):
        self.state = state
        self.entries = {}

    def upsert(self, ids, documents, metadatas, embeddings):
        for index, doc_id in enumerate(ids):
            self.entries[doc_id] = (documents[index], metadatas[index])
            if index == 0 and self.state.partial_write:
                mode = self.state.partial_write
                self.state.partial_write = None
                if mode == 'raise':
                    raise RuntimeError('simulated interrupted write')
                return

    def get(self, ids, include):
        present = [doc_id for doc_id in ids if doc_id in self.entries]
        return {
            'ids': present,
            'documents': [self.entries[doc_id][0] for doc_id in present],
            'metadatas': [self.entries[doc_id][1] for doc_id in present],
        }


@pytest.fixture
def upload_api(monkeypatch, tmp_path):
    state = SimpleNamespace(
        collections={}, partial_write=None, embedding_failure=False,
        parser_failure=False, invalidations=0, embedding_calls=0,
    )

    class MemoryClient:
        def get_or_create_collection(self, name, metadata):
            return state.collections.setdefault(name, MemoryCollection(state))

    class Embedding:
        def embed_batch(self, texts):
            state.embedding_calls += 1
            if state.embedding_failure:
                state.embedding_failure = False
                raise RuntimeError('simulated embedding failure')
            return [[1.0, 0.0] for _ in texts]

    class Parser:
        def parse_from_bytes(self, content, filename):
            if state.parser_failure:
                state.parser_failure = False
                raise RuntimeError('simulated parser failure')
            text = content.decode('utf-8')
            chunks = [
                {'index': index, 'content': line, 'length': len(line), 'type': 'text'}
                for index, line in enumerate(text.splitlines()) if line
            ]
            return ParseResult(filename, 1, len(chunks), 0, chunks, text, [], {})

    def invalidate():
        state.invalidations += 1

    monkeypatch.setattr(document.settings, 'UPLOAD_DIR', tmp_path / 'uploads')
    monkeypatch.setattr(document, 'get_embedding_model', lambda: Embedding())
    monkeypatch.setattr(document, 'invalidate_search_cache', invalidate)
    monkeypatch.setattr(document.ParserFactory, 'get_parser', lambda _: Parser())
    monkeypatch.setattr(document, 'parse_file', lambda path: Parser().parse_from_bytes(
        Path(path).read_bytes(), Path(path).name
    ))
    monkeypatch.setattr(chroma_store, 'get_chroma_client', lambda **_: MemoryClient())
    app = FastAPI()
    app.include_router(document.router, prefix='/api')
    with TestClient(app) as client:
        yield client, state, tmp_path


def upload(client, collection='collection_a', content=b'first chunk\nsecond chunk', filename='sample.md'):
    data = {'collection_name': collection} if collection else {}
    return client.post('/api/document/upload', files={'file': (filename, content)}, data=data)


def test_parse_only_then_store_and_deduplicate(upload_api):
    client, state, _ = upload_api
    parsed = upload(client, collection=None)
    assert parsed.status_code == 200
    assert parsed.json()['stored'] is False
    assert not state.collections

    stored = upload(client)
    assert stored.status_code == 200
    assert stored.json()['stored'] is True
    assert stored.json()['doc_count'] == 2
    duplicate = upload(client)
    assert duplicate.status_code == 200
    assert duplicate.json()['duplicate'] is True
    assert duplicate.json()['stored'] is False
    assert state.embedding_calls == 1
    assert state.invalidations == 1


def test_same_content_can_be_stored_in_different_collections(upload_api):
    client, state, _ = upload_api
    assert upload(client, 'collection_a').json()['stored'] is True
    assert upload(client, 'collection_b').json()['stored'] is True
    assert len(state.collections['collection_a'].entries) == 2
    assert len(state.collections['collection_b'].entries) == 2


def test_same_filename_with_different_content_keeps_both_documents(upload_api):
    client, state, _ = upload_api
    assert upload(client, content=b'old content').json()['stored'] is True
    assert upload(client, content=b'new content').json()['stored'] is True
    entries = state.collections['collection_a'].entries.values()
    assert {content for content, _ in entries} == {'old content', 'new content'}


def test_same_content_with_different_filename_is_duplicate(upload_api):
    client, state, _ = upload_api
    assert upload(client, filename='first.md').json()['stored'] is True
    assert upload(client, filename='second.md').json()['duplicate'] is True
    assert len(state.collections['collection_a'].entries) == 2


@pytest.mark.parametrize('failure', ['parser_failure', 'embedding_failure'])
def test_failed_first_attempt_can_be_retried(upload_api, failure):
    client, state, _ = upload_api
    setattr(state, failure, True)
    assert upload(client).status_code == 500
    retried = upload(client)
    assert retried.status_code == 200
    assert retried.json()['stored'] is True
    assert upload(client).json()['duplicate'] is True


@pytest.mark.parametrize('mode', ['raise', 'silent'])
def test_partial_write_is_not_complete_and_retry_upserts_all_chunks(upload_api, mode):
    client, state, _ = upload_api
    state.partial_write = mode
    assert upload(client).status_code == 500
    assert len(state.collections['collection_a'].entries) == 1
    assert state.invalidations == 0
    retried = upload(client)
    assert retried.status_code == 200
    assert retried.json()['stored'] is True
    assert len(state.collections['collection_a'].entries) == 2
    assert upload(client).json()['duplicate'] is True


def test_empty_document_is_not_marked_as_stored(upload_api):
    client, state, _ = upload_api
    assert upload(client, content=b'').status_code == 400
    assert not state.collections


@pytest.mark.parametrize('mismatch', ['content', 'chunk_count'])
def test_matching_ids_with_incomplete_contents_are_repaired(upload_api, mismatch):
    client, state, _ = upload_api
    assert upload(client).json()['stored'] is True
    entries = state.collections['collection_a'].entries
    doc_id = next(iter(entries))
    content, metadata = entries[doc_id]
    if mismatch == 'content':
        entries[doc_id] = ('incomplete content', metadata)
    else:
        entries[doc_id] = (content, {**metadata, 'chunk_count': 1})
    repaired = upload(client)
    assert repaired.status_code == 200
    assert repaired.json()['stored'] is True
    assert upload(client).json()['duplicate'] is True


def test_unsupported_and_oversized_files_are_rejected_before_saving(upload_api, monkeypatch):
    client, _, tmp_path = upload_api
    assert upload(client, filename='secret.env').status_code == 400
    monkeypatch.setattr(document.settings, 'MAX_FILE_SIZE', 3)
    assert upload(client, content=b'four').status_code == 400
    assert not (tmp_path / 'uploads').exists()


@pytest.mark.parametrize('relative', [True, False])
def test_parse_path_accepts_files_inside_upload_directory(upload_api, relative):
    client, _, tmp_path = upload_api
    target = tmp_path / 'uploads' / 'nested' / 'sample.md'
    target.parent.mkdir(parents=True)
    target.write_text('document', encoding='utf-8')
    path = 'nested/sample.md' if relative else str(target)
    response = client.post('/api/document/parse-path', json={'file_path': path})
    assert response.status_code == 200
    assert response.json()['chunks'][0]['content'] == 'document'


@pytest.mark.parametrize('relative', [True, False])
def test_parse_path_rejects_parent_traversal_and_absolute_outside_path(upload_api, relative):
    client, _, tmp_path = upload_api
    outside = tmp_path / 'private.md'
    outside.write_text('private content', encoding='utf-8')
    path = '../private.md' if relative else str(outside)
    response = client.post('/api/document/parse-path', json={'file_path': path})
    assert response.status_code == 403
    assert 'private content' not in response.text


def test_parse_path_rejects_unsupported_extension(upload_api):
    client, _, tmp_path = upload_api
    target = tmp_path / 'uploads' / 'secret.env'
    target.parent.mkdir()
    target.write_text('secret', encoding='utf-8')
    response = client.post('/api/document/parse-path', json={'file_path': str(target)})
    assert response.status_code == 400


def test_parse_path_rejects_symlink_leaving_upload_directory(upload_api):
    client, _, tmp_path = upload_api
    outside = tmp_path / 'private.md'
    outside.write_text('private content', encoding='utf-8')
    link = tmp_path / 'uploads' / 'link.md'
    link.parent.mkdir()
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip('This platform does not permit creating symlinks')
    response = client.post('/api/document/parse-path', json={'file_path': str(link)})
    assert response.status_code == 403
