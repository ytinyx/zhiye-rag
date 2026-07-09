from typing import List

from openai import OpenAI
from tenacity import retry,stop_after_attempt,wait_exponential

from src.embeddings.base import BaseEmbedding

class OpenAIEmbedding(BaseEmbedding):
    def __init__(
            self,
            model:str,
            api_key:str,
            base_url:str,
            dimension:int=None
            ):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.dimension = dimension

        self.client = OpenAI(api_key=api_key,base_url=base_url)

    def embed_text(self,text:str) -> List[float]:
        '''
        处理单个文本
        '''    
        rs = self.embed_batch([text])
        return rs[0]

    @retry(stop=stop_after_attempt(3),wait=wait_exponential(multiplier=1,min=2,max=10)) # 重试 3 次 
    # 第1次请求失败，会自动重试，等待 2 秒，最大等待时间为 10 秒
    # 第2次请求失败，会自动重试，等待 4 秒，最大等待时间为 10 秒
    def embed_batch(self,texts:List[str]) -> List[List[float]]:
        '''
        批量处理文本
        '''    
        params = {'input':texts,'model':self.model}
        # 判断是否指定了维度
        if self.dimension:
            params['dimensions'] = self.dimension
        
        # 发送请求
        resp = self.client.embeddings.create(**params)
        # 提取向量
        embeddings = [item.embedding for item in resp.data]
        return embeddings

    def get_dimension(self) -> int:
        '''
        获取向量的维度
        '''    
        return self.dimension
    
    def get_model_name(self) -> str:
        '''
        获取模型名称
        '''    
        return self.model