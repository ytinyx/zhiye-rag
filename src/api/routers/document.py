import hashlib
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from src.api.config import settings
from src.api.deps import get_embedding_model, invalidate_search_cache
from src.database.document_store import DocumentStore
from src.parsers import ParserFactory, parse_file


router = APIRouter(prefix='/document', tags=['文件解析'])
logger = logging.getLogger(__name__)


def _get_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def _save_file_with_hash(
    file_bytes: bytes, original_filename: str, upload_dir: Path
) -> tuple[str, bool]:
    """磁盘文件可复用；文件存在不代表已成功写入某个向量集合。"""
    file_hash = _get_file_hash(file_bytes)
    ext = Path(original_filename).suffix.lower()
    file_path = upload_dir / f'{file_hash}{ext}'
    try:
        with file_path.open('xb') as handle:
            handle.write(file_bytes)
    except FileExistsError:
        return str(file_path), True
    return str(file_path), False


def _ensure_upload_dir() -> Path:
    upload_dir = Path(settings.UPLOAD_DIR).resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


@router.post('/upload')
async def upload_document(
    file: UploadFile = File(...),
    collection_name: Optional[str] = Form(None),
):
    """上传并解析；指定集合后，按文件内容和集合判断是否已完整入库。"""
    filename = file.filename or ''
    ext = Path(filename).suffix.lower()
    if ext not in ParserFactory.supported_extensions():
        raise HTTPException(status_code=400, detail=f'不支持的文件格式{ext}')

    # 边读取边限制大小，避免在校验前将任意大小的文件读入内存。
    chunks = []
    size = 0
    while chunk := await file.read(1024 * 1024):
        size += len(chunk)
        if size > settings.MAX_FILE_SIZE:
            size_mb = settings.MAX_FILE_SIZE / 1024 / 1024
            raise HTTPException(status_code=400, detail=f'文件过大,最大允许{size_mb}MB')
        chunks.append(chunk)
    file_bytes = b''.join(chunks)

    try:
        _save_file_with_hash(file_bytes, filename, _ensure_upload_dir())
        parser = ParserFactory.get_parser(filename)
        result = parser.parse_from_bytes(file_bytes, filename)
        if not collection_name:
            return {
                'success': True,
                'filename': result.filename,
                'stored': False,
                'doc_count': result.total_chunks,
                'duplicate': False,
            }

        if not result.chunks:
            raise HTTPException(status_code=400, detail='文件未解析出可入库的文本')

        store = DocumentStore(
            embedding_model=get_embedding_model(), collection_name=collection_name
        )
        content_hash = _get_file_hash(file_bytes)
        if store.is_parse_result_stored(result, collection_name, content_hash):
            return {
                'success': True,
                'filename': result.filename,
                'stored': False,
                'doc_count': 0,
                'duplicate': True,
                'message': '文件已完整存入当前集合，跳过重复入库',
            }

        doc_ids = store.add_parse_result(result, collection_name, content_hash)
        if not store.is_parse_result_stored(result, collection_name, content_hash):
            raise RuntimeError('向量分块未完整写入，请重试上传')
        invalidate_search_cache()
        return {
            'success': True,
            'filename': result.filename,
            'stored': True,
            'doc_count': len(doc_ids),
            'duplicate': False,
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception('文件解析或入库失败')
        raise HTTPException(status_code=500, detail='文件解析或入库失败，请检查服务日志后重试')


class ParsePathRequest(BaseModel):
    file_path: str


def _resolve_upload_path(file_path: str) -> Path:
    upload_dir = _ensure_upload_dir()
    path = Path(file_path)
    if not path.is_absolute():
        # 兼容 data/uploads/file.md；其他相对路径均相对于上传目录。
        cwd_candidate = path.resolve()
        path = cwd_candidate if cwd_candidate.is_relative_to(upload_dir) else upload_dir / path
    target = path.resolve()
    if not target.is_relative_to(upload_dir):
        raise HTTPException(status_code=403, detail='只允许解析上传目录内的文件')
    if target.suffix.lower() not in ParserFactory.supported_extensions():
        raise HTTPException(status_code=400, detail='不支持的文件格式')
    if not target.is_file():
        raise HTTPException(status_code=404, detail='文件不存在')
    return target


@router.post('/parse-path')
async def parse_document_by_path(body: ParsePathRequest):
    """只解析 UPLOAD_DIR 内的受支持文件；允许文件名或目录内绝对路径。"""
    target_path = _resolve_upload_path(body.file_path)
    try:
        result = parse_file(str(target_path))
        return {
            'message': '文档处理成功',
            'filename': result.filename,
            'total_pages': result.total_pages,
            'chunks_count': result.total_chunks,
            'tables_count': result.table_count,
            'chunks': result.chunks,
        }
    except Exception:
        logger.exception('上传目录文件解析失败')
        raise HTTPException(status_code=500, detail='文件解析失败，请检查服务日志')


@router.get('/supported-formats')
async def supported_formats():
    return {'formats': ParserFactory.supported_extensions()}
