from typing import Dict, Optional, Any,List
from dataclasses import dataclass
import time
import os

from cachetools import TTLCache

from src.database.document_store import DocumentStore


@dataclass
class RetrievalConfig:
    """检索配置"""
    top_k: int = 5                        # 返回结果数
    min_score: float = 0.0                # 最低分数阈值
    namespace: Optional[str] = None       # 命名空间过滤
    metadata_filter: Optional[Dict] = None # 元数据过滤


@dataclass
class SearchResponse:
    ''' 检索结果 '''
    query: str          # 查询文本
    total_results: int  # 总结果数
    results:List[Dict[str,Any]]     # 检索结果列表
    retrieval_time_ms:int      # 检索时间

class SearchService:
    '''检索服务的统一入口'''
    def __init__(self,document_store:DocumentStore):
        self.document_store = document_store

    def search(self,query:str,config:Optional[RetrievalConfig]=None) -> SearchResponse:
        '''
        执行查询功能
        Args:
            query: 查询文本
            config: 检索配置
        Returns:
            SearchResponse: 检索结果
        '''
        # 开始时间
        start_time = time.time()

        # 判断config有没有传递
        if config is None:
            config = RetrievalConfig()

        results = self.document_store.search(
            query=query,
            top_k=config.top_k,
            namespace=config.namespace,
        )

        # 过滤分数较低的
        results = [result for result in results if result.get('score') >= config.min_score]
        # top_k
        results = results[:config.top_k]
        end_time = time.time()
        # 检索时间
        retrieval_time_ms = int((end_time - start_time) * 1000)

        return SearchResponse(
            query=query,
            total_results=len(results),
            results=results,
            retrieval_time_ms=retrieval_time_ms,
        )

    def get_stats(self) -> Dict[str, int]:
        '''
        获取存储库的统计信息
        Returns:
            Dict[str, int]: 统计信息
        '''
        return self.document_store.get_stats()


class CachedSearchService:
    '''缓存的检索服务'''
    def __init__(self,search_service:SearchService,ttl:int=None, maxsize:int =None):
        self.service = search_service
        ttl = ttl or int(os.getenv('SEARCH_CACHE_TTL', 300))
        maxsize = maxsize or int(os.getenv('SEARCH_CACHE_MAX_SIZE', os.getenv('SEARCH_CACHE_MAXSIZE', 100)))
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.cache_hits = 0  # 缓存命中次数
        self.cache_misses = 0 # 缓存未命中次数
       
    def search(self,query:str,config:Optional[RetrievalConfig]=None) -> SearchResponse:
        '''
        带缓存的查询功能
        Args:
            query: 检索文本
            config: 检索配置
        Returns:
            SearchResponse: 检索结果
        '''
        # 处理config
        if config is None:
            config = RetrievalConfig()
        
        # 生成缓存键
        cache_key = (query,config.top_k,config.min_score,config.namespace)

        # 检查缓存
        if cache_key in self.cache:
            self.cache_hits += 1
            return self.cache[cache_key]
        
        # 缓存未命中
        self.cache_misses += 1
        result =self.service.search(query,config)

        # 添加到缓存
        self.cache[cache_key] = result

        return result
    
    def get_stats(self) -> Dict[str, int]:
        '''
        获取统计信息（包含缓存统计）

        Returns:
            Dict[str, int]: 统计信息
        '''
        stats = self.service.get_stats()
        stats['cache_hits'] = self.cache_hits
        stats['cache_misses'] = self.cache_misses
        total = self.cache_hits + self.cache_misses
        if total > 0:
            stats['cache_hit_rate'] = round(self.cache_hits / total * 100, 2)
        else:
            stats['cache_hit_rate'] = 0
        return stats
    
    def clear_cache(self) -> bool:
        '''
        清除缓存
        Returns:
            bool: 是否成功
        '''
        self.cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        return True
