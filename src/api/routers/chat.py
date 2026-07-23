import time

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from src.api.models import ChatRequest,ChatResponse
from src.api.config import settings
from src.api.deps import get_llm,get_search_service
from src.retrieval.search_service import RetrievalConfig
from src.llm.rag import generate_answer,generate_answer_stream

router = APIRouter(prefix='/chat',tags=['聊天'])

@router.post('/',response_model=ChatResponse)
async def chat(request:ChatRequest):
    '''RAG对话'''
    # 开始记时
    start_time = time.time()
    # 确定模型是否存在
    provider = request.model or settings.DEFAULT_MODEL
    # 获取模型
    llm = get_llm(provider)

    # 获取检索服务实例
    search_service = get_search_service(request.collection_name)
    # 创建检索配置对象
    search_config = RetrievalConfig(top_k=settings.SEARCH_TOP_K)
    # 检索
    search_response = search_service.search(request.query,search_config)

    # 生成答案
    result = generate_answer(
        llm = llm,
        question=request.query,
        results=search_response.results,
        temperature=settings.LLM_TEMPERATURE,
        max_token=settings.LLM_MAX_TOKEN
    )

    # 构建来源
    sources = [
            {
                "id":r.get('id'),
                "score":r.get('score'),
                "content": r.get('content')[:200]+'...' if len(r.get('content')) >200 else r.get('content'),      
            }
        for r in search_response.results[:3]     
    ]

    # 获取结束时间
    end_time = time.time()
    # 计算总时间
    total_time_ms = int((end_time - start_time) * 1000)

    # 返回结果
    return ChatResponse(
        query = request.query,
        answer = result.get('answer',''),
        sources = sources,
        token_used = result.get('token_used',{}),
        total_time_ms = total_time_ms
    )

@router.post('/stream')
async def chat_stream(request:ChatRequest):
    '''RAG对话'''
    # 确定模型是否存在
    provider = request.model or settings.DEFAULT_MODEL
    # 获取模型
    llm = get_llm(provider)

    # 获取检索服务实例
    search_service = get_search_service(request.collection_name)
    # 创建检索配置对象
    search_config = RetrievalConfig(top_k=settings.SEARCH_TOP_K)
    # 检索
    search_response = search_service.search(request.query,search_config)

    # 生成答案
    return StreamingResponse(
        generate_answer_stream(
            llm=llm,
            question=request.query,
            results=search_response.results,
            temperature=settings.LLM_TEMPERATURE,
            max_token=settings.LLM_MAX_TOKEN
        ),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache","X-Accel-Buffering": "no"}  # 禁用缓存
    )