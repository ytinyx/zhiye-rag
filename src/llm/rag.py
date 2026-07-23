from typing import List,Dict,Any
from src.llm.llm import LLM

def format_context(results:List[Dict[str,Any]],max_chars:int =1500) -> str:
    '''
        格式化上下文
        Args:
            results: 检索结果
        Returns:
            str: 格式化后的上下文
    '''
    seen = set()  # 用于去重
    parts = []  # 用于存储格式化后的结果
    total = 0 

    for result in results:
        content = result.get('content','').strip()
        if not content or content  in seen:
            continue

        next_total = total + len(content) + (2 if len(parts) else 0)
        if next_total > max_chars:  # 超过最大字符数，则跳过
            continue

        seen.add(content)       # 添加到已处理的内容中
        parts.append(content)   #   添加到结果列表中
        total = next_total          # 更新总字符数

    return '\n\n'.join(parts)

def build_prompt(question:str,context:str) -> str:
    '''
        构建提示词
        Args:
            question: 问题
            context: 上下文
        Returns:
            str: 提示词
    '''
    # 提示词要求：
    instrution = (
        '你是一个基于文档的问答助手，请严格依据上下文回答问题：'
        '如果上下文缺失相关信息，请回答“不知道”。'
    )

    return (
        f'{instrution}\n\n'
        f'[上下文]\n{context}\n\n'
        f'[问题]\n问:{question}\n答：'
    )
def generate_answer(
        llm:LLM, 
        question:str,
        results:List[Dict[str,Any]],
        temperature:float=0.7,
        max_token:int=2000
        ) -> Dict[str,Any]:
    '''
        生成答案
        Args:
            llm: LLM 对象
            question: 问题
            results: 检索结果
            temperature: 模型温度
            max_token: 最大token数
        Returns:
            Dict[str,Any]: 模型输出
    '''
    if not results:
        return {
            "answer": "我不知道",
            "question": question,
            "context": "",
            "token_used":{"total":0,"prompt":0,"completion":0},
            "model": ""
        }

    #　格式化上下文
    context = format_context(results,max_token)
    # 构建提示词
    prompt = build_prompt(question,context)
    # 调用LLM
    messages = [{"role": "user", "content": prompt}]
    result = llm.generate(messages,temperature=temperature,max_token=max_token)
    #　返回结果
    return {
        "answer": result['content'],
        "question": question,
        "context": context,
        "token_used": result["token_used"],
        "model": result['model']
    }

async def generate_answer_stream(
        llm:LLM, 
        question:str,
        results:List[Dict[str,Any]],
        temperature:float=0.7,
        max_token:int=2000
        ):
    '''
        生成答案
        Args:
            llm: LLM 对象
            question: 问题
            results: 检索结果
            temperature: 模型温度
            max_token: 最大token数
        
    '''
    if not results:
        yield '我不知道'
        return

    #　格式化上下文
    context = format_context(results,max_token)
    # 构建提示词
    prompt = build_prompt(question,context)
    # 调用LLM
    messages = [{"role": "user", "content": prompt}]

    # 流式生成答案
    async for chunk in llm.generate_stream(messages,temperature=temperature,max_token=max_token):
        yield chunk