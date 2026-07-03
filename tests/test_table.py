import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import pandas as pd
from src.parsers.table_parser import TableProcessor


class TestTableProcessor(unittest.TestCase):
    def setUp(self):
        """设置测试环境"""
        self.processor = TableProcessor()

    def test_markdown_to_dataframe_basic(self):
        """测试基本的markdown转dataframe功能"""
        table_markdown = """
| Name | Age | City |
|------|-----|------|
| John | 25  | NYC  |
| Jane | 30  | LA   |
"""
        df = self.processor.markdown_to_dataframe(table_markdown)
        
        self.assertIsNotNone(df)
        self.assertEqual(list(df.columns), ["Name", "Age", "City"])
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]["Name"], "John")
        self.assertEqual(df.iloc[1]["Age"], "30")

    def test_markdown_to_dataframe_empty_input(self):
        """测试空输入的情况"""
        result = self.processor.markdown_to_dataframe("")
        self.assertIsNone(result)

    def test_markdown_to_dataframe_insufficient_lines(self):
        """测试输入行数不足的情况"""
        table_markdown = "| Header |\n"
        result = self.processor.markdown_to_dataframe(table_markdown)
        self.assertIsNone(result)

    def test_dataframe_to_text_basic(self):
        """测试dataframe转text功能"""
        df = pd.DataFrame({
            "Name": ["Alice", "Bob"],
            "Age": ["25", "30"]
        })
        result = self.processor.dataframe_to_text(df)
        
        expected_parts = [
            "表格内容:",
            "Name|Age",
            "Alice|25",  # 修正：DataFrame中第一行是Name和Age的值，即"Alice"和"25"
            "Bob|30"     # 修正：DataFrame中第二行是Name和Age的值，即"Bob"和"30"
        ]
        
        for part in expected_parts:
            self.assertIn(part, result)

        # 额外验证结果的格式
        lines = result.split('\n')
        self.assertEqual(lines[0], "表格内容:")
        self.assertEqual(lines[1], "Name|Age")
        self.assertEqual(lines[2], "Alice|25")
        self.assertEqual(lines[3], "Bob|30")

    def test_dataframe_to_text_empty(self):
        """测试空dataframe的情况"""
        df = pd.DataFrame()
        result = self.processor.dataframe_to_text(df)
        self.assertEqual(result, "")

    def test_table_to_text_basic(self):
        """测试表格到文本的完整转换流程"""
        table_markdown = """
| Product | Price |
|---------|-------|
| Apple   | $1.00 |
| Banana  | $0.50 |
"""
        result = self.processor.table_to_text(table_markdown)
        
        self.assertIn("表格内容:", result)
        self.assertIn("Product", result)
        self.assertIn("Price", result)
        self.assertIn("Apple", result)
        self.assertIn("Banana", result)

    def test_merge_tables_no_merging_needed(self):
        """测试不需要合并的表格列表"""
        tables = [
            {"data": "table1", "page": 1, "cols": ["A", "B"], "markdown": "|A|B|\n|-|-|"}
        ]
        result = self.processor.merge_tables(tables)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], tables[0])

    def test_merge_tables_multiple_non_mergeable(self):
        """测试多个无法合并的表格"""
        tables = [
            {"data": "table1", "page": 1, "cols": ["A", "B"], "markdown": "|A|B|\n|-|-|"},
            {"data": "table2", "page": 3, "cols": ["A", "B"], "markdown": "|A|B|\n|-|-|"},
            {"data": "table3", "page": 5, "cols": ["X", "Y"], "markdown": "|X|Y|\n|-|-|"}
        ]
        result = self.processor.merge_tables(tables)
        
        self.assertEqual(len(result), 3)

    def test_merge_tables_adjacent_pages_same_cols(self):
        """测试相邻页面且列相同的表格应该被合并"""
        tables = [
            {"data": "table1", "page": 1, "cols": ["A", "B"], "markdown": "|A|B|\n|-|-|\n|1|2|"},
            {"data": "table2", "page": 2, "cols": ["A", "B"], "markdown": "|A|B|\n|-|-|\n|3|4|"}
        ]
        result = self.processor.merge_tables(tables)
        
        self.assertEqual(len(result), 1)
        self.assertIn("|1|2|", result[0]["markdown"])
        self.assertIn("|3|4|", result[0]["markdown"])

    def test_merge_tables_different_columns(self):
        """测试不同列名的表格不会被合并"""
        tables = [
            {"data": "table1", "page": 1, "cols": ["A", "B"], "markdown": "|A|B|\n|-|-|"},
            {"data": "table2", "page": 2, "cols": ["C", "D"], "markdown": "|C|D|\n|-|-|"}
        ]
        result = self.processor.merge_tables(tables)
        
        self.assertEqual(len(result), 2)

    def test_extract_key_value_basic(self):
        """测试提取键值对功能"""
        table_markdown = """
| Key      | Value    |
|----------|----------|
| Name     | John     |
| Location | NYC      |
"""
        result = self.processor.extrace_key_value(table_markdown)
        
        expected = {"Name": "John", "Location": "NYC"}
        self.assertEqual(result, expected)

    def test_extract_key_value_with_spaces(self):
        """测试包含空格的键值对提取"""
        table_markdown = """
|      Key      |     Value      |
|---------------|----------------|
|    Company    |    ABC Corp    |
|    Address    |    123 Main St |
"""
        result = self.processor.extrace_key_value(table_markdown)
        
        expected = {"Company": "ABC Corp", "Address": "123 Main St"}
        self.assertEqual(result, expected)

    def test_extract_key_value_insufficient_columns(self):
        """测试列数不足时返回空字典"""
        table_markdown = """
| Key |
|-----|
| A   |
"""
        result = self.processor.extrace_key_value(table_markdown)
        self.assertEqual(result, {})

    def test_extract_key_value_empty_table(self):
        """测试空表格返回空字典"""
        result = self.processor.extrace_key_value("")
        self.assertEqual(result, {})


if __name__ == '__main__':
    unittest.main()
