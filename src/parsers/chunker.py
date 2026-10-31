import re
from typing import Dict, List, Optional

class ChunkStrategy:
    """分块策略枚举"""
    PARAGRAPH = "paragraph"   # 按段落分块
    SENTENCE = "sentence"     # 按句子分块
    CHARACTER = "character"   # 按字符数分块
    SEMANTIC = "semantic"     # 语义分块（阶段三，使用模型）

class TextChunker:
    """文本分块器"""

    def __init__(
        self,
        strategy: str = ChunkStrategy.PARAGRAPH,
        max_chunk_size: int = 1000,
        min_chunk_size: int = 100,
        chunk_overlap: int = 200,
    ):
        """
        初始化分块器

        Args:
            strategy: 分块策略
            max_chunk_size: 最大块大小（字符数）
            min_chunk_size: 最小块大小
            chunk_overlap: 块之间重叠字符数
        """
        self.strategy = strategy
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def split(self, text: str, tables: Optional[List[Dict]] = None) -> List[Dict]:
        '''
        通过策略对文本进行分块
        '''
        if self.strategy == ChunkStrategy.PARAGRAPH:
            chunks = self._split_by_paragraph(text)
        elif self.strategy == ChunkStrategy.SENTENCE:
            chunks = self._split_by_sentence(text)
        elif self.strategy == ChunkStrategy.CHARACTER:
            chunks = self._split_by_character(text)
        else:
            chunks = self._split_by_paragraph(text)
        
        # 添加表格信息
        if tables:
            chunks = self._attach_tables(chunks, tables)

        return chunks

    def _split_by_paragraph(self, text: str) -> List[Dict]:
        '''
        按段落分块
            1. 用双换行符切出段落（split('\\n\\n')），逐段累加到 current_chunk。
            2. 当「当前块 + 本段」超过 max_chunk_size 时：
            - 若当前块已达 min_chunk_size，先将其作为一个块输出。
            - 若本段自身超过 max_chunk_size，则用 _split_long_paragraph 再细分为多个子块。
            - 否则只把本段放入新块，并从当前块尾部保留 chunk_overlap 长度的重叠，实现块间上下文衔接。
            3. 未超长时，继续把本段追加到 current_chunk（段之间用 \\n\\n 连接）。
            4. 循环结束后，若还有未输出的 current_chunk 且长度 >= min_chunk_size，作为最后一块输出。
        '''
        chunks = []
        paragraphs = text.split("\n\n")

        current_chunk = ""
        chunk_index = 0

        for para in paragraphs:
            # 跳过空行
            para = para.strip()
            if not para: 
                continue
            
            # 当前块 + 新块 > 最大块大小
            if len(current_chunk) + len(para) > self.max_chunk_size:
                # 如果当前块长度超过最小块长度，则添加到结果中
                if len(current_chunk) > self.min_chunk_size:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "index": chunk_index,
                        "length": len(current_chunk),
                        "type": "text"
                    })
                    chunk_index += 1  # 块索引加1
                # 处理新块逻辑
                if len(para) > self.max_chunk_size:
                    # 如果新块长度超过最大块长度,需要进行块的分割
                    sub_chunks = self._split_long_paragraph(para, chunk_index)
                    # 将子块添加到结果中
                    chunks.extend(sub_chunks)
                    chunk_index += len(sub_chunks)
                    current_chunk = ""
                else:
                    # 新块内容，没有超过最大块长度，则添加到当前块中
                    overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                    current_chunk = current_chunk[overlap_start:] + '\n\n' + para
            else:
                current_chunk = current_chunk + "\n\n" + para if current_chunk else para

        # 收尾：剩余内容达到最小块大小时作为最后一块
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append({
                "content": current_chunk.strip(),
                "index": chunk_index,
                "length": len(current_chunk),
                "type": "text"
            })
        return chunks

    def _split_long_paragraph(self, text: str, start_index: int) -> List[Dict]:
        """分割过长的段落：先按句子切，超长句子再按字符切，并控制块大小与重叠。"""
        # 用中英文句末标点+可选空白切分，保留分隔符（括号分组）
        sentences = re.split(r'([。！？.!?]\s*)', text)
        # 奇偶配对：前半是“标点前文本”，后半是“标点+空白”，拼成完整句子列表
        sentences = [''.join(pair) for pair in zip(sentences[::2], sentences[1::2])]

        chunks = []           # 最终块列表
        current_chunk = ""    # 当前累积的块内容
        chunk_index = start_index  # 块序号，与调用方已有块衔接

        for sent in sentences:
            # 当前块加上本句会超限 → 先收尾当前块，再处理本句
            if len(current_chunk) + len(sent) > self.max_chunk_size:
                if current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "index": chunk_index,
                        "length": len(current_chunk),
                        "type": "text"
                    })
                    chunk_index += 1

                # 本句单独就超长 → 按固定步长滑动窗口按字符切
                if len(sent) > self.max_chunk_size:
                    # 步长 = 块大小 - 重叠，使相邻子块有 overlap
                    for i in range(0, len(sent), self.max_chunk_size - self.chunk_overlap):
                        sub_chunk = sent[i:i + self.max_chunk_size]
                        if len(sub_chunk) >= self.min_chunk_size:
                            chunks.append({
                                "content": sub_chunk,
                                "index": chunk_index,
                                "length": len(sub_chunk),
                                "type": "text"
                            })
                            chunk_index += 1
                    current_chunk = ""  # 长句已全部切成子块，清空
                else:
                    current_chunk = sent  # 本句不超长，作为下一块的首句
            else:
                current_chunk += sent  # 未超限，直接追加本句

        # 收尾：剩余内容达到最小块大小时作为最后一块
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append({
                "content": current_chunk.strip(),
                "index": chunk_index,
                "length": len(current_chunk),
                "type": "text"
            })

        return chunks

    def _split_by_sentence(self, text: str) -> List[Dict]:
        """按句子分割。

        整体逻辑：先用正则按中英文句末标点切分文本并保留标点，得到“句子+标点”列表；
        然后顺序遍历句子，在不超过 max_chunk_size 的前提下把多句合并成一块；
        若加上当前句会超长，则先输出当前块（若达到 min_chunk_size），再把当前句作为新块起点；
        最后若还有剩余内容且达到最小块大小，作为最后一块输出。
        """
        # 按句末标点（。！？.!?）及其后可选空白切分，括号分组使标点被保留在结果中
        sentences = re.split(r'([。！？.!?]\s*)', text)
        # 奇偶配对：split 结果中偶数位是“标点前文本”，奇数位是“标点+空白”，拼成完整句子列表
        sentences = [''.join(pair) for pair in zip(sentences[::2], sentences[1::2])]

        chunks = []           # 最终输出的块列表
        current_chunk = ""    # 当前正在累积的一块内容
        chunk_index = 0       # 当前块的序号

        for sent in sentences:
            sent = sent.strip()   # 去掉句子首尾空白
            if not sent:          # 空句跳过
                continue

            # 若当前块加上本句会超过最大块大小，需要先收尾再开新块
            if len(current_chunk) + len(sent) > self.max_chunk_size:
                # 当前块已达到最小块大小时，输出为一块
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "index": chunk_index,
                        "length": len(current_chunk),
                        "type": "text"
                    })
                    chunk_index += 1
                # 本句作为新块的起点（可能单句就超长，后续会在别处再切）
                current_chunk = sent
            else:
                # 未超限：拼到当前块，非首句时前加空格
                current_chunk += " " + sent if current_chunk else sent

        # 收尾：剩余内容达到最小块大小时作为最后一块
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append({
                "content": current_chunk.strip(),
                "index": chunk_index,
                "length": len(current_chunk),
                "type": "text"
            })

        return chunks
        
    def _split_by_character(self, text: str) -> List[Dict]:
        """按字符数分割。

        整体逻辑：从文本开头起，以 (max_chunk_size - chunk_overlap) 为步长滑动截取，
        每次取长度为 max_chunk_size 的子串作为一块；步长小于块长从而实现块与块之间的重叠；
        仅当块去掉首尾空白后长度不小于 min_chunk_size 时才加入结果，避免过短碎片。
        """
        chunks = []           # 最终输出的块列表
        chunk_index = 0       # 当前块的序号

        # 按固定步长滑动：步长 = 块长 - 重叠，使相邻块有 chunk_overlap 的重叠
        for i in range(0, len(text), self.max_chunk_size - self.chunk_overlap):
            chunk = text[i:i + self.max_chunk_size]   # 截取本段，最多 max_chunk_size 字符
            # 仅当去掉空白后仍达到最小块大小时才计入
            if len(chunk.strip()) >= self.min_chunk_size:
                chunks.append({
                    "content": chunk.strip(),
                    "index": chunk_index,
                    "length": len(chunk),
                    "type": "text"
                })
                chunk_index += 1

        return chunks

    def _attach_tables(self,chunks: List[Dict], tables: List[Dict]) -> List[Dict]:
        '''
        将表格作为单独的块添加到分块列表中
        '''
        chunk_index = len(chunks)

        for table in tables:
            table_text = f'表格 (第{table.get("page","?")}页)：\n {table.get("markdown", "")}'

            chunks.append({
                "content": table_text,
                "index": chunk_index,
                "length": len(table_text),
                "type": "table",
                "page":table.get("page","?"),
                "table_data":table
            })
            chunk_index += 1
        
        return chunks