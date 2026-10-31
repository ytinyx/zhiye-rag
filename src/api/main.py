import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.config import PROJECT_ROOT, settings

from src.api.routers import document
from src.api.routers import chat
from src.api.routers import health

app = FastAPI(
    title = '知页 RAG',
    description = '多格式文档解析、向量检索与来源展示的本地知识库问答系统',
    version = '0.1.0'
)

if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=['GET', 'POST'],
        allow_headers=['Content-Type'],
    )

app.include_router(document.router,prefix='/api')
app.include_router(chat.router,prefix='/api')
app.include_router(health.router,prefix='/api')

FRONTEND_DIR = PROJECT_ROOT / 'frontend'
app.mount('/js', StaticFiles(directory=FRONTEND_DIR / 'js'), name='javascript')
app.mount('/css', StaticFiles(directory=FRONTEND_DIR / 'css'), name='stylesheets')


@app.get('/', include_in_schema=False)
async def index():
    return FileResponse(FRONTEND_DIR / 'index.html')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('src.api.main:app', port=8000,reload=True)
