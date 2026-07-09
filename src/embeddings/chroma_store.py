import uuid
from typing import List, Dict
from functools import lru_cache
import os

from src.embeddings.vector_store import BaseVectorStore,Document,SearchResult

@lru_cache
def get_chroma_client(persist_directory:str=None):
    '''
    获取Chroma客户端实例
    '''
    import chromadb

    if persist_directory is None:
        persist_directory = os.getenv('CHROMA_DB_PATH','./data/chroma_db')
    
    return chromadb.PersistentClient(
        path=persist_directory,
        settings=chromadb.Settings(anonymized_telemetry=False)  # 禁用遥测
        )


class ChromaVectorStore(BaseVectorStore):
    '''
    Chroma 向量数据存储实现
    '''
    def __init__(self, 
                 collection_name: str ='rag_documents',
                 persist_directory: str | None = None,
                 distance: str ='cosine',
                 ):
        
        self.collection_name = collection_name
        self.distance = distance
        # 创建客户端
        self.client = get_chroma_client(persist_directory=persist_directory)

        # 获取或者创建集合
        self.collection = self.client.get_or_create_collection(name=collection_name,
                                                               metadata={"hnsw:space": distance})

    def add_documents(self, 
                      documents: List[Document],
                      embeddings: List[List[float]],
                      ) -> List[str]:
        '''
        添加文档
        '''
        ids = []
        metadatas = []
        texts = []
        
        for doc in documents:
            doc_id = doc.id or str(uuid.uuid4())
            ids.append(doc_id)
            metadatas.append(doc.metadata)
            texts.append(doc.content)


        if not ids:
            return []

        # 稳定的文档 ID 配合 upsert，使部分写入后的重试不会产生重复分块。
        self.collection.upsert(
            ids =ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        return ids

    def contains_documents(self, documents: List[Document]) -> bool:
        """只有所有预期分块及其内容均已存储，才视为一次完整入库。"""
        if not documents:
            return False
        stored = self.collection.get(
            ids=[document.id for document in documents],
            include=["documents", "metadatas"],
        )
        entries = {
            doc_id: (content, metadata or {})
            for doc_id, content, metadata in zip(
                stored["ids"], stored["documents"], stored["metadatas"]
            )
        }
        for document in documents:
            content, metadata = entries.get(document.id, (None, {}))
            if content != document.content:
                return False
            for key in ("content_hash", "chunk_count", "namespace"):
                if metadata.get(key) != document.metadata.get(key):
                    return False
        return True
    
    def search(self, query_embedding, top_k = 5, filter = None):
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter
        )

        search_results = []

        if results['ids'] and results['ids'][0]:
            for i,doc_id in enumerate(results['ids'][0]):

                search_results.append(
                    SearchResult(
                        document = Document(
                            id = doc_id,
                            content = results['documents'][0][i],
                            metadata = results['metadatas'][0][i] if results.get('metadatas') else {}
                        ),
                        metadata = {},
                        score = 1- results['distances'][0][i] if results.get('distances') else 0,
                    )
                )
        return search_results
    
    def clear(self) -> bool:
        '''
        清空数据
        '''
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(name=self.collection_name,
                                                               metadata={"hnsw:space": self.distance})
        return True

    def get_collection_stats(self) -> Dict[str, int]:
        '''
        获取集合统计信息
        '''
        return {
            'count':self.collection.count(),
            'name':self.collection.name,
            'distance':self.distance
        }
    
