from abc import ABC,abstractmethod
from typing import List,Dict

class BaseEmbedding(ABC):
    '''
    嵌入模型抽象类
    '''
    @abstractmethod
    def embed_text(self,text:str) -> List[float]:
        '''
        嵌入单个文本
        参数：
            text:待嵌入的文本
        返回：
            嵌入向量(浮点类型)
        '''
        pass
    @abstractmethod
    def embed_batch(self,texts:List[str]) -> List[List[float]]:
        '''
        嵌入多个文本
        参数：
            texts:待嵌入的文本列表
        返回：
            嵌入向量列表(浮点类型)
        '''
        pass
    @abstractmethod
    def get_dimension(self) -> int:
        '''
        获取嵌入向量的维度
        返回：
            嵌入向量的维度
        '''
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        '''
        获取模型名称
        返回：
            模型名称
        '''
        pass