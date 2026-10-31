import re
from typing import List

class TextCleaner:
    '''
    文本清洗器
    '''
    def __init__(self,custom_patterns:List[str] = None):
        '''
        Args:
            custom_patterns (List[str], optional): 自定义正则表达式列表. 
        '''
        # 常见的无意义模式
        self.patterns_to_remove = [
            r'^\s*\d+\s*$',               # 单独的页码
            r'^\s*[-=_]+\s*$',            # 分隔线
            r'^\s*第\s*\d+\s*页\s*$',     # 中文页码标记
            r'^\s*Page\s*\d+\s*$',        # 英文页码
            r'^\s*\d+\s*/\s*\d+\s*$',     # 页码格式：1/10
        ]

        # 添加自定义模式
        if custom_patterns:
            self.patterns_to_remove.extend(custom_patterns)
    def clean(self,text:str) -> str:
        '''
        清洗文版，去除无意义内容
        Args:
            text (str): 文本
        Returns:
            str: 清洗后的文本
        '''
        lines = text.splitlines()
        cleaned_lines = []

        for line in lines:
            # 保留段落分隔，让后续按段落分块仍能识别文档结构。
            line = line.strip()
            if not line:
                cleaned_lines.append("")
                continue
            # 匹配自定义模式
            for pattern in self.patterns_to_remove:
                if re.match(pattern,line):
                    break
            else:
                cleaned_lines.append(line)

        return re.sub(r'\n{3,}', '\n\n', '\n'.join(cleaned_lines)).strip()
    def normalize_whitespace(self,text:str) -> str:
        '''
        去除多余的空白字符
        -  合并多个空格
        -  合并多个换行
        -  去除行首行尾的空白字符
        Args:
            text (str): 输入文本
        Returns:
            str: 处理后的文本
        '''
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # 只合并横向空白；\s+ 会同时吞掉段落换行。
        text = re.sub(r'[^\S\n]+', ' ', text)
        text = '\n'.join(line.strip() for line in text.split('\n'))
        # 合并多个换行
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    def remove_extra_chars(self,text:str) -> str:
        '''
        去除多余的字符
        Args:
            text (str): 输入文本
        Returns:
            str: 处理后的文本
        '''
        # 仅移除零宽字符和 BOM，保留英文、数字、标点及文档布局。
        text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
        return text
    
    def full_clean(self,text:str) -> str:
        '''
        文本清理
        Args:
            text (str): 输入文本
        Returns:
            str: 处理后的文本
        '''
        text = self.clean(text)
        text = self.normalize_whitespace(text)
        text = self.remove_extra_chars(text)
        return text
