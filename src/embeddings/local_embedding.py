from typing import List
import os
from pathlib import Path

from sentence_transformers import SentenceTransformer

from src.embeddings.base import BaseEmbedding

class LocalEmbedding(BaseEmbedding):

    def __init__(self,
                 model_name:str,
                 device:str='cpu'):
        '''
        初始化本地嵌入模型

        Args:
            model_name: 模型名称（HuggingFace）
                - BAAI/bge-small-zh-v1.5: 中文推荐（默认，性能优秀）
                - BAAI/bge-base-zh-v1.5: 中文高质量（更大，效果更好）
                - BAAI/bge-large-zh-v1.5: 中文顶级效果（最大，资源消耗高）
                - shibing624/text2vec-base-chinese: 中文通用（经典模型）
                - moka-ai/m3e-base: 中文高质量
                - sentence-transformers/all-MiniLM-L6-v2: 英文
            device: 运行设备（cpu / cuda）
        '''
        self.model_name = model_name
        self.device = device

        # 获取缓存目录
        cache_folder = os.getenv('EMBEDDING_CACHE_DIR','./models/cache')
        Path(cache_folder).mkdir(parents=True,exist_ok=True)

        # 加载模型
        self.model = SentenceTransformer(model_name,device=device,cache_folder=cache_folder)
    
    def embed_text(self, text:str) -> List[float]:
        '''获取单个文本的向量表示'''
        embedding = self.model.encode(text,convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts:List[str]) -> List[List[float]]:
        '''
        批量嵌入文本
        '''
        embeddings = self.model.encode(texts,convert_to_numpy=True)
        return embeddings.tolist()
    

    def get_dimension(self) -> int:
        '''获取向量维度'''
        return self.model.get_sentence_embedding_dimension()
    
    def get_model_name(self) -> str:
        '''获取模型名称'''
        return self.model_name