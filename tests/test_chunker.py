"""测试 TextChunker 文本分块器"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parsers.chunker import TextChunker, ChunkStrategy


def test_paragraph_strategy():
    """测试按段落分块"""
    print("=== 测试按段落分块 ===")
    chunker = TextChunker(
        strategy=ChunkStrategy.PARAGRAPH,
        max_chunk_size=500,
        min_chunk_size=50,
        chunk_overlap=50
    )

    # 测试文本：多段内容
    test_text = """第一段内容。这是一段较短的文本，用于测试段落分块功能。

第二段内容。这段文本稍微长一些，包含了更多的描述性内容。段落分块是文档处理中的常用策略。

第三段内容。这是第三个段落，用于测试分块器如何处理多个连续的段落。分块器应该能够正确地将文本按照段落进行分割。

第四段内容。最后一段文本，用于验证分块结果的正确性。分块结果应该包含content、index、length和type等字段。"""

    chunks = chunker.split(test_text)

    print(f"分块数量: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"\n块 {i}:")
        print(f"  索引: {chunk['index']}")
        print(f"  长度: {chunk['length']}")
        print(f"  类型: {chunk['type']}")
        print(f"  内容预览: {chunk['content'][:50]}...")

    # 验证结果
    assert len(chunks) > 0, "至少应该有一个分块"
    for chunk in chunks:
        assert "content" in chunk
        assert "index" in chunk
        assert "length" in chunk
        assert "type" in chunk
        assert chunk["type"] == "text"
        assert chunk["length"] >= chunker.min_chunk_size
        assert chunk["content"].strip()

    print("[OK] 按段落分块测试通过")


def test_sentence_strategy():
    """测试按句子分块"""
    print("\n=== 测试按句子分块 ===")
    chunker = TextChunker(
        strategy=ChunkStrategy.SENTENCE,
        max_chunk_size=100,
        min_chunk_size=20
    )

    test_text = "这是第一句。这是第二句！这是第三句？这是第四句。这是第五句。"

    chunks = chunker.split(test_text)

    print(f"分块数量: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"块 {i}: {chunk['content']}")

    # 验证结果
    assert len(chunks) > 0
    # 验证分块包含句子分隔符
    has_sentence_end = any(any(punct in c["content"] for punct in ["。", "！", "？", "."]) for c in chunks)
    assert has_sentence_end

    print("[OK] 按句子分块测试通过")


def test_character_strategy():
    """测试按字符数分块"""
    print("\n=== 测试按字符数分块 ===")
    chunker = TextChunker(
        strategy=ChunkStrategy.CHARACTER,
        max_chunk_size=50,
        min_chunk_size=10,
        chunk_overlap=10
    )

    # 创建一个较长的文本
    test_text = "这是一段用于测试字符分块的文本。" * 10

    chunks = chunker.split(test_text)

    print(f"分块数量: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"块 {i}: 长度={chunk['length']}, 内容={chunk['content'][:30]}...")

    # 验证结果
    assert len(chunks) > 1
    assert all(c["length"] <= chunker.max_chunk_size for c in chunks)

    print("[OK] 按字符数分块测试通过")


def test_with_tables():
    """测试带表格的分块"""
    print("\n=== 测试带表格的分块 ===")
    chunker = TextChunker(
        strategy=ChunkStrategy.PARAGRAPH,
        max_chunk_size=500,
        min_chunk_size=50
    )

    test_text = """这是第一段文本内容。这是一段较长的文本内容，确保能够满足最小块大小的要求。

这是第二段文本内容。用于测试带表格的分块功能。这段内容也比较长，确保能够通过最小块大小的过滤。"""

    tables = [
        {
            "table_number": 1,
            "page": 1,
            "markdown": "| 列1 | 列2 |\n|---|---|\n| A | B |"
        },
        {
            "table_number": 2,
            "page": 2,
            "markdown":"| 列A | 列B |\n|---|---|\n| X | Y |"
        }
    ]

    chunks = chunker.split(test_text, tables=tables)

    print(f"总块数量: {len(chunks)} (文本块 + 表格块)")
    for i, chunk in enumerate(chunks):
        print(f"块 {i}: 类型={chunk['type']}, 长度={chunk['length']}")
        if chunk['type'] == 'table':
            print(f"  页码: {chunk.get('page')}")

    # 验证结果
    text_chunks = [c for c in chunks if c["type"] == "text"]
    table_chunks = [c for c in chunks if c["type"] == "table"]

    assert len(text_chunks) > 0, "应该有文本块"
    assert len(table_chunks) == len(tables), "表格数量应该匹配"

    # 验证表格块的结构
    for table_chunk in table_chunks:
        assert "page" in table_chunk
        assert "table_data" in table_chunk
        assert "表格 (第" in table_chunk["content"]

    print("[OK] 带表格分块测试通过")


def test_long_paragraph():
    """测试超长段落的处理"""
    print("\n=== 测试超长段落处理 ===")
    chunker = TextChunker(
        strategy=ChunkStrategy.PARAGRAPH,
        max_chunk_size=100,
        min_chunk_size=20,
        chunk_overlap=20
    )

    # 创建一个超长段落（超过 max_chunk_size）
    long_text = "这是一个非常长的段落。" * 20

    chunks = chunker.split(long_text)

    print(f"分块数量: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"块 {i}: 长度={chunk['length']}")

    assert len(chunks) > 1
    # 验证每个块都不超过最大块大小
    for chunk in chunks:
        assert chunk["length"] <= chunker.max_chunk_size, f"块大小超过限制: {chunk['length']}"

    print("[OK] 超长段落处理测试通过")


def test_empty_text():
    """测试空文本处理"""
    print("\n=== 测试空文本处理 ===")
    chunker = TextChunker()

    chunks = chunker.split("")
    print(f"空文本分块数量: {len(chunks)}")
    assert chunks == []

    chunks = chunker.split("   \n\n   ")
    assert chunks == []
    print(f"空白文本分块数量: {len(chunks)}")

    print("[OK] 空文本处理测试通过")


def test_min_chunk_size():
    """测试小块过滤"""
    print("\n=== 测试小块过滤 ===")
    chunker = TextChunker(
        strategy=ChunkStrategy.PARAGRAPH,
        max_chunk_size=500,
        min_chunk_size=100  # 设置较大的最小块大小
    )

    # 创建包含短段落的文本
    test_text = """短段落一。

短段落二。

这是一个较长的段落，应该能够满足最小块大小的要求。它包含更多的内容。"""

    chunks = chunker.split(test_text)

    print(f"分块数量: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"块 {i}: 长度={chunk['length']}")

    assert chunks == []  # 整篇文本仍短于设定的 100 字符下限
    # 验证所有块都满足最小块大小
    for chunk in chunks:
        assert chunk["length"] >= chunker.min_chunk_size, f"块小于最小大小: {chunk['length']}"

    print("[OK] 小块过滤测试通过")


def test_chunk_overlap():
    """测试块重叠功能"""
    print("\n=== 测试块重叠功能 ===")
    chunker = TextChunker(
        strategy=ChunkStrategy.CHARACTER,
        max_chunk_size=150,
        min_chunk_size=50,
        chunk_overlap=30  # 设置重叠
    )

    test_text = "用于检验相邻文本块的重叠。" * 30

    chunks = chunker.split(test_text)

    print(f"分块数量: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"块 {i}:\n{chunk['content']}\n")

    # 验证相邻块之间有重叠
    assert len(chunks) > 1
    if len(chunks) > 1:
        for i in range(len(chunks) - 1):
            end_of_current = chunks[i]["content"][-30:]
            start_of_next = chunks[i + 1]["content"][:30]
            assert end_of_current == start_of_next
            print(f"块{i}末尾: {end_of_current}")
            print(f"块{i+1}开头: {start_of_next}\n")

    print("[OK] 块重叠功能测试通过")


def test_default_strategy():
    """测试默认分块策略"""
    print("\n=== 测试默认分块策略 ===")
    # 不指定策略，应该使用默认的段落策略
    chunker = TextChunker(max_chunk_size=300, min_chunk_size=5)

    test_text = """第一段内容。

第二段内容。

第三段内容。"""

    chunks = chunker.split(test_text)

    print(f"使用默认策略的分块数量: {len(chunks)}")
    assert chunker.strategy == ChunkStrategy.PARAGRAPH
    assert len(chunks) == 1
    assert chunks[0]["content"] == test_text

    print("[OK] 默认策略测试通过")


def test_mixed_english_chinese():
    """测试中英文混合文本"""
    print("\n=== 测试中英文混合文本 ===")
    chunker = TextChunker(
        strategy=ChunkStrategy.SENTENCE,
        max_chunk_size=100,
        min_chunk_size=20
    )

    test_text = "这是中文句子。This is an English sentence. 另一个中文句子！Another English sentence!"

    chunks = chunker.split(test_text)

    print(f"分块数量: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"块 {i}: {chunk['content']}")

    # 验证中英文标点都能正确处理
    assert len(chunks) > 0

    print("[OK] 中英文混合文本测试通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("开始运行 TextChunker 测试")
    print("=" * 50)

    try:
        test_paragraph_strategy()
        test_sentence_strategy()
        test_character_strategy()
        test_with_tables()
        test_long_paragraph()
        test_empty_text()
        test_min_chunk_size()
        test_chunk_overlap()
        test_default_strategy()
        test_mixed_english_chinese()

        print("\n" + "=" * 50)
        print("[PASS] 所有测试通过！")
        print("=" * 50)
    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n[FAIL] 发生错误: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
