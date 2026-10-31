from typing import List, Dict, Any

from openai import OpenAI,AsyncClient


class LLM:
    def __init__(self,model:str,api_key:str,base_url:str):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

        self.client = OpenAI(api_key=api_key,base_url=base_url)
        self.async_client = AsyncClient(api_key=api_key,base_url=base_url)

    
    def generate(self,messages:List[Dict[str,str]],temperature:float=0.7,max_token=2000) -> Dict[str,Any]:
        '''
        生成内容
        Args:
            messages: 聊天消息
            temperature: 采样温度
            max_token: 最大生成长度
        return: 生成结果
        '''
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_token)
        
        choice = response.choices[0]

        return {
            'content':choice.message.content,       # 内容
            'finish_reason':choice.finish_reason,   # 结束原因
            'token_used':{
                'total':response.usage.total_tokens,  # 总计消耗
                'prompt':response.usage.prompt_tokens,  # 提示消耗
                'completion':response.usage.completion_tokens # 完成消耗
            },
            'model':response.model  # 模型名称
        }
    async def generate_stream(self,messages:List[Dict[str,str]],temperature:float=0.7,max_token=2000):
        '''
        流式生成结果
        '''
        stream = await self.async_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_token,
            stream=True)
        
        async for chunk in stream:
            if (content := chunk.choices[0].delta.content):
                yield content