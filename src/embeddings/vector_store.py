from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class Document:
    """文档对象"""
    id: str                                # 文档ID
    content: str                           # 文档内容
    metadata: Dict[str, Any]               # 元数据
    embedding: Optional[List[float]] = None  # 向量（可选）

@dataclass
class SearchResult:
    """检索结果"""
    document: Document                     # 文档
    score: float                           # 相似度分数
    metadata: Dict[str, Any]               # 额外元数据

class BaseVectorStore(ABC):
    """向量数据库接口"""
    @abstractmethod
    def add_documents(self, 
                      documents: List[Document],
                      embeddings: List[List[float]],
                      ) -> List[str]:
        '''
        添加文档到向量数据库
        Args:
            documents (List[Document]): 文档列表
            embeddings (List[List[float]]): 文档向量列表
        Returns:
            List[str]: 文档ID列表
        '''
        pass

    @abstractmethod
    def search(self, 
               query_embedding: List[float],
               top_k: int = 5,
               filter:Dict[str, Any] = None,
               ) -> List[SearchResult]:
        '''
        搜索向量数据库
        Args:
            query_embedding (List[float]): 查询向量
            top_k (int, optional): 返回结果数量. Defaults to 5.
        Returns:
            List[SearchResult]: 搜索结果列表
        '''
        pass

    @abstractmethod
    def get_collection_stats(self) -> Dict[str, int]:
        '''
        获取向量数据库中的集合名称
        Returns:
            统计信息(文档数量、维度)
        '''
        pass

    @abstractmethod
    def clear(self) -> bool:
        '''
        清空向量数据库中的所有文档
        Returns:
            True: 成功
            False: 失败
        '''
        pass