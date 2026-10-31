import os
from pathlib import Path

from dotenv import load_dotenv
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / '.env')


def project_path(value: str) -> str:
    path = Path(value).expanduser()
    return str(path if path.is_absolute() else PROJECT_ROOT / path)

class Settings:
    """API配置"""

    # 文件上传配置
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE_MB', '150')) * 1024 * 1024
    ALLOWED_EXTENSIONS = ['.pdf', '.md', '.html','.docx']

    # 上传文件存储目录
    UPLOAD_DIR = project_path(os.getenv('UPLOAD_DIR', 'data/uploads'))

    # The bundled UI is served from the same origin.
    CORS_ORIGINS = [origin.strip() for origin in os.getenv('CORS_ORIGINS', '').split(',') if origin.strip()]

    # LLM模型配置
    LLM_PROVIDERS = {
        'zhipu':{
            'api_key':os.getenv('ZHIPU_API_KEY',''),
            'base_url':os.getenv('ZHIPU_BASE_URL','https://open.bigmodel.cn/api/paas/v4'),
            'default_model':os.getenv('ZHIPU_MODEL','glm-4-flash')
        },
        'qwen':{
            'api_key':os.getenv('DASHSCOPE_API_KEY',''),
            'base_url':os.getenv('DASHSCOPE_BASE_URL','https://dashscope.aliyuncs.com/compatible-mode/v1'),
            'default_model':os.getenv('DASHSCOPE_MODEL','qwen-plus')
        },
    }

    # 默认模型
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'zhipu')

    # LLM生成参数
    LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.7'))
    LLM_MAX_TOKEN = int(os.getenv('LLM_MAX_TOKEN', '2000'))

    # 检索配置
    SEARCH_TOP_K = int(os.getenv('SEARCH_TOP_K', '3'))


# 全局配置对象
settings = Settings()
