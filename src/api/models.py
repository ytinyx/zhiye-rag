from pydantic import BaseModel,Field
from typing import List,Dict,Optional,Any

class ChatRequest(BaseModel):
    query:str = Field(...,description="用户问题")
    collection_name:str = Field(...,description="数据集名称")
    model:Optional[str] = Field(None,description="模型名称")

class ChatResponse(BaseModel):
    query:str
    answer:str
    sources:List[Dict[str,Any]]
    token_used:Dict[str,int]
    total_time_ms:int