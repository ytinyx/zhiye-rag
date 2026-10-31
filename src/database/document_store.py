# 解析数据 -> 向量 - > 存储向量 -> 检索向量 -> 获取结果
from typing import Optional,List,Dict,Any
import hashlib
import json
import uuid

from src.embeddings.base import BaseEmbedding
from src.embeddings.chroma_store import ChromaVectorStore
from src.parsers.base import ParseResult
from src.embeddings.vector_store import Document

class DocumentStore:
    def __init__(self, 
                 embedding_model: BaseEmbedding,
                 vector_store: Optional[ChromaVectorStore]=None,
                 collection_name: str ='rag_documents',
                 ):
        self.embedding = embedding_model
        self.vector_store = vector_store or ChromaVectorStore(collection_name=collection_name)

    @staticmethod
    def _parsed_documents(
        parse_result: ParseResult, namespace: str, content_hash: str | None = None
    ) -> List[Document]:
        """文件内容决定身份；同名但内容不同的文件可在同一集合共存。"""
        if content_hash is None:
            content_hash = hashlib.sha256(
                json.dumps(
                    [chunk['content'] for chunk in parse_result.chunks], ensure_ascii=False
                ).encode("utf-8")
            ).hexdigest()
        documents =[]

        # 遍历文件内容
        for index, chunk in enumerate(parse_result.chunks):
            doc_id = f'{namespace}_{content_hash}_{index}'
            metadata = {
                "filename": parse_result.filename,
                "chunk_index": chunk["index"],
                "chunk_type": chunk.get('type', 'text'),
                "namespace": namespace,
                "length":chunk['length'],
                "content_hash": content_hash,
                "chunk_count": len(parse_result.chunks),
            }

            # 如果是表格，添加页面
            if chunk.get('type') == 'table' and 'page'in chunk:
                metadata['page'] = chunk['page']

            documents.append(
                Document(
                    id=doc_id, 
                    content=chunk['content'], 
                    metadata=metadata)
            )
        return documents

    def is_parse_result_stored(
        self, parse_result: ParseResult, namespace: str = 'default',
        content_hash: str | None = None,
    ) -> bool:
        documents = self._parsed_documents(parse_result, namespace, content_hash)
        return self.vector_store.contains_documents(documents)

    def add_parse_result(
        self, parse_result: ParseResult, namespace: str = 'default',
        content_hash: str | None = None,
    ) -> List[str]:
        """写入解析结果。稳定 ID 允许在一次未完成的写入后安全重试。"""
        documents = self._parsed_documents(parse_result, namespace, content_hash)
        if not documents:
            return []
        texts_to_embed = [document.content for document in documents]
        embeddings = self.embedding.embed_batch(texts_to_embed)
        # add to vector store
        doc_ids = self.vector_store.add_documents(documents,embeddings)
        return doc_ids
    def search(self, query: str, top_k: int = 5, namespace: Optional[str]=None):
        '''
        语义搜索
        Args:
            query (str): 查询内容
            top_k (int, optional): 搜索结果数量. Defaults to 5.
            namespace (Optional[str], optional): 命名空间. Defaults to None.

        '''
        # 生成向量
        query_embedding = self.embedding.embed_text(query)
        # 构造过滤条件
        filter_conditions = { "namespace": namespace} if namespace else None

        results = self.vector_store.search(query_embedding, top_k, filter_conditions)

        return [
            {
                'id':rs.document.id,
                'content':rs.document.content,
                'metadata':rs.document.metadata,
                'score':rs.score
            } for rs in results
        ]
        
    def add_documents(self, texts: list[str],metadatas:List[Dict[str,Any]],namespace:str='default') -> list[str]:
        '''
        直接追加文档向量
        '''
        documents =[]
        for i,text in enumerate(texts):
            doc_id = f'{namespace}_{uuid.uuid4().hex[:8]}'
            metadata = metadatas[i] if i<len(metadatas) else {}
            metadata['namespace'] =namespace

            documents.append(
                Document(
                    id=doc_id, 
                    content=text, 
                    metadata=metadata)
            )
        embeddings = self.embedding.embed_batch(texts)

        return self.vector_store.add_documents(documents,embeddings)
    
    def get_stats(self) -> dict[str, int]:
        '''
        获取存储统计信息
        '''
        stats = self.vector_store.get_collection_stats()
        stats['embedding_dim'] = self.embedding.get_dimension()
        stats['embedding_model'] = self.embedding.get_model_name()
        return stats
