"""测试 TextCleaner 文本清理器"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parsers.cleaner import TextCleaner


def test_clean():
    """测试基本文本清理功能"""
    print("=== 测试基本文本清理 ===")
    cleaner = TextCleaner()

    # 测试文本（包含页码、分隔线等无意义内容）
    test_text = """这是第一段有用的内容。

1

这是第二段内容。

___

这是第三段内容。

第 5 页

这是第四段内容。

Page 10

3

这是第五段内容。

1/10

这是最后一段。"""

    result = cleaner.clean(test_text)
    print("原始文本:")
    print(test_text)
    print("\n清理后文本:")
    print(result)
    print()

    # 验证结果
    assert "这是第一段有用的内容" in result
    assert "这是第二段内容" in result
    assert "这是第三段内容" in result
    assert "这是第四段内容" in result
    assert "这是第五段内容" in result
    assert "这是最后一段" in result
    # 验证页码和分隔线被移除
    assert "\n1\n" not in result
    assert "___" not in result
    assert "第 5 页" not in result
    assert "Page 10" not in result
    assert "1/10" not in result

    print("✓ 基本清理测试通过")


def test_normalize_whitespace():
    """测试空白字符规范化"""
    print("\n=== 测试空白字符规范化 ===")
    cleaner = TextCleaner()

    test_text = "这是    多个    空格\n\n\n\n这是多个换行\n   这是行首行尾空白   "
    result = cleaner.normalize_whitespace(test_text)

    print("原始文本:")
    print(repr(test_text))
    print("\n规范化后文本:")
    print(repr(result))
    print()

    # 验证多个空格被合并
    assert "这是    多个    空格" not in result
    assert "这是 多个 空格" in result
    # 验证多个换行被合并
    assert "\n\n\n\n" not in result

    print("✓ 空白字符规范化测试通过")


def test_remove_extra_chars():
    """测试移除特殊字符"""
    print("\n=== 测试移除特殊字符 ===")
    cleaner = TextCleaner()

    # 包含零宽字符的文本
    test_text = "正常文本\u200b\u200c\u200d\ufeff更多内容"
    result = cleaner.remove_extra_chars(test_text)

    print("原始文本:")
    print(repr(test_text))
    print("\n移除后文本:")
    print(repr(result))
    print()

    # 验证零宽字符被移除
    assert "\u200b" not in result
    assert "\u200c" not in result
    assert "\u200d" not in result
    assert "\ufeff" not in result
    assert "正常文本更多内容" in result

    print("✓ 移除特殊字符测试通过")


def test_remove_extra_chars_preserves_english_numbers_and_punctuation():
    text = "RAG 2026: 中文内容。\u200b\u200c\u200d\ufeff"
    assert TextCleaner().remove_extra_chars(text) == "RAG 2026: 中文内容。"


def test_normalize_whitespace_preserves_paragraphs():
    text = "first    paragraph\n\n\n\nsecond paragraph"
    assert TextCleaner().normalize_whitespace(text) == "first paragraph\n\nsecond paragraph"


def test_full_clean_preserves_paragraphs_and_non_chinese_text():
    text = "RAG    notes 2026.\n\nPage 2\n\n第二段包含 API 和 123。\u200b"
    assert TextCleaner().full_clean(text) == "RAG notes 2026.\n\n第二段包含 API 和 123。"


def test_full_clean():
    """测试完整清洗流程"""
    print("\n=== 测试完整清洗流程 ===")
    cleaner = TextCleaner()

    test_text = """这是第一段    有用内容。


2

这是第二段     内容。


___


这是第三段内容\u200b\u200b\u200b。


第 10 页


这是最后一段。   """

    result = cleaner.full_clean(test_text)

    print("原始文本:")
    print(test_text)
    print("\n完整清洗后:")
    print(result)
    print()

    # 验证所有清理步骤都生效
    assert "2" not in result.splitlines()
    assert "这是第二段 内容。" in result
    assert "___" not in result  # 分隔线被移除
    assert "第 10 页" not in result  # 中文页码被移除
    assert "\u200b" not in result  # 零宽字符被移除
    assert "    " not in result  # 多余空格被合并

    print("✓ 完整清洗流程测试通过")


def test_custom_patterns():
    """测试自定义清理模式"""
    print("\n=== 测试自定义清理模式 ===")

    # 添加自定义模式：移除包含 "TODO:" 的行
    custom_patterns = [r'^\s*TODO:.*$']
    cleaner = TextCleaner(custom_patterns=custom_patterns)

    test_text = """这是有用的内容。

TODO: 这是一个待办事项

这是另一段有用内容。"""

    result = cleaner.clean(test_text)

    print("原始文本:")
    print(test_text)
    print("\n清理后文本:")
    print(result)
    print()

    # 验证自定义模式生效
    assert "这是有用的内容" in result
    assert "这是另一段有用内容" in result
    assert "TODO: 这是一个待办事项" not in result

    print("✓ 自定义清理模式测试通过")


def test_empty_text():
    """测试空文本处理"""
    print("\n=== 测试空文本处理 ===")
    cleaner = TextCleaner()

    result = cleaner.clean("")
    assert result == ""

    result = cleaner.full_clean("   \n\n   \n   ")
    assert result == "" or result.strip() == ""

    print("✓ 空文本处理测试通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("开始运行 TextCleaner 测试")
    print("=" * 50)

    try:
        test_clean()
        test_normalize_whitespace()
        test_remove_extra_chars()
        test_full_clean()
        test_custom_patterns()
        test_empty_text()

        print("\n" + "=" * 50)
        print("✅ 所有测试通过！")
        print("=" * 50)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
