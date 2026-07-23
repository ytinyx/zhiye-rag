from functools import lru_cache
import os

from fastapi import HTTPException

from src.database.document_store import DocumentStore
from src.retrieval.search_service import SearchService,CachedSearchService
from src.api.config import settings
from src.llm.llm import LLM

@lru_cache(maxsize=1)
def get_embedding_model():
    '''
    获取embedding模型实例
    '''
    from src.embeddings.local_embedding import LocalEmbedding

    model = os.getenv('EMBEDDING_MODEL','BAAI/bge-small-zh-v1.5')
    device = os.getenv('EMBEDDING_DEVICE','cpu')
    # 创建embedding模型
    embedding_model = LocalEmbedding(model_name=model,device=device)
    return embedding_model

@lru_cache(maxsize=32)
def get_search_service(collection_name:str):
    '''
    获取检索服务实例
    '''
    # 创建embedding模型
    embedding_model = get_embedding_model()
    # 创建向量存储实例
    store = DocumentStore(embedding_model=embedding_model,collection_name=collection_name)
    # 创建检索服务实例
    search_service = SearchService(document_store=store)
    # 创建缓存检索服务实例
    if os.getenv('ENABLE_SEARCH_CACHE', 'false').lower() in ('1','true','yes'):
        search_service = CachedSearchService(search_service=search_service)

    return search_service


def invalidate_search_cache():
    """Discard cached search results after a document is indexed."""
    get_search_service.cache_clear()

def get_llm(model:str):
    '''
    获取LLM实例
    '''
    # 验证模型名称
    if model not in settings.LLM_PROVIDERS:
        raise HTTPException(status_code=400,detail=f'不支持:{model}模型，目前支持的模型有:{settings.LLM_PROVIDERS.keys()}')
    # 获取模型配置
    config = settings.LLM_PROVIDERS.get(model)
    if not config.get('api_key', '').strip():
        raise HTTPException(status_code=503, detail=f'请在 .env 中配置 {model} 的 API Key 后再提问')

    # 创建LLM实例
    llm = LLM(
        model=config.get('default_model'),
        api_key=config.get('api_key'),
        base_url=config.get('base_url')
        )

    return llm
