from typing import Optional
from pathlib import Path

from markdownify import markdownify

from src.parsers.base import BaseParser,ParseResult
from src.parsers.chunker import TextChunker,ChunkStrategy
from src.parsers.cleaner import TextCleaner

class HTMLParser(BaseParser):
    '''
    HTML 解析器
    '''
    def __init__(
            self,
            chunker: Optional[TextChunker] = None,
            cleaner: Optional[TextCleaner] = None
    ):
        self.cleaner = cleaner if cleaner else TextCleaner()
        self.chunker = chunker if chunker else TextChunker(
            strategy=ChunkStrategy.PARAGRAPH,
            max_chunk_size=1000,
            chunk_overlap=200
        )
    
    def parse(self, file_path:str) ->ParseResult:
        '''
        解析HTML文件
        '''
        with open(file_path,'r',encoding='utf-8') as f:
            raw_text = f.read()

        # 转换为markdown
        raw_text = markdownify(raw_text)

        cleaned_text = self.cleaner.clean(raw_text)
        chunks = self.chunker.split(cleaned_text)

        return ParseResult(
            filename=Path(file_path).name,
            total_pages=1,
            total_chunks=len(chunks),
            table_count=0,
            chunks=chunks,
            raw_text=raw_text,
            tables=[],
            metadata={'parser':'markdownify','filename':Path(file_path).name}
        )
    
    def parse_from_bytes(self, file_bytes:bytes, filename:str):

        raw_text = file_bytes.decode('utf-8')

        # 转换为markdown
        raw_text = markdownify(raw_text)

        cleaned_text = self.cleaner.clean(raw_text)
        chunks = self.chunker.split(cleaned_text)

        return ParseResult(
            filename=filename,
            total_pages=1,
            total_chunks=len(chunks),
            table_count=0,
            chunks=chunks,
            raw_text=raw_text,
            tables=[],
            metadata={'parser':'markdown','filename':filename}
        )
    
    
    def supported_extensions(self) -> list[str]:
        return ['.html','.htm','.HTML','.HTM']