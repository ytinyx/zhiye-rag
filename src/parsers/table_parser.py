from typing import List,Dict,Optional

import pandas as pd

class TableProcessor:
    '''表格解析器'''
    def markdown_to_dataframe(self,table_markdown:str) ->  Optional[pd.DataFrame]:
        '''
        将markdown表格转换为DataFrame
        参数：
           table_markdown: markdown表格字符串
        返回：
           pd.DataFrame: 转换后的DataFrame
        '''
        lines = [line.strip() for line in table_markdown.strip().split('\n') if line.strip()]

        if len(lines) < 2:
            return None
        # 解析表头
        headers = [cell.strip() for cell in lines[0].split('|')[1:-1]]  
        # 跳过分割线
        data_lines = lines[2:] if len(lines)>2 else []
        # 解析数据行
        data = []
        for line in data_lines:
            if '|' in line:
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                if len(cells) == len(headers):
                    data.append(cells)
        return pd.DataFrame(data,columns=headers)

    def dataframe_to_text(self,df:pd.DataFrame) -> str:
        '''
        将DataFrame转换为markdown表格
        参数：
           df: DataFrame对象
        返回：
           str: markdown表格字符串
        '''
        if df.empty:
            return ''
        
        # 生成文本数据
        parts = ['表格内容:']
        parts.append('|'.join(df.columns))

        for _,row in df.iterrows():
            parts.append('|'.join(row))

        return '\n'.join(parts)

    def table_to_text(self,table_markdown:str) -> str:
        '''
        将markdown表格转换为纯文本
        参数：
           table_markdown: markdown表格字符串
        返回：
           str: 纯文本字符串
        '''
        df = self.markdown_to_dataframe(table_markdown)
        if df is None:
            return ''
        
        return self.dataframe_to_text(df)
    

    def merge_tables(self,tables:List[Dict]) -> List[Dict]:
        '''
        合并跨页的拆分表格
        参数：
           tables: 表格数据,page,cols,markdown,row
        返回：
           str: 合并后的markdown表格字符串
        '''
        if len(tables) <=1:
            return tables
        merged = [tables[0]]

        for i in range(1,len(tables)):
            current = tables[i]
            last = merged[-1]

            # 判断是否需要合并
            should_merge = (
                current.get('cols') == last.get('cols') and
                current.get('page') == last.get('page')+1
            )

            if should_merge:
                last['markdown'] += '\n' + current['markdown']   # 合并markdown
                if 'row' in last and 'row' in current:
                    last['row'] += current['row']   # 合并行号
            else:
                merged.append(current)

        return merged

    def extrace_key_value(self,table_text:str) -> Dict[str,str]:
        '''
        从markdown表格中提取键值对
        参数：
           table_markdown: markdown表格字符串
        返回：
           Dict[str,str]: 键值对字典
        '''
        df = self.markdown_to_dataframe(table_text)
        if df is None or len(df.columns)<2:
            return {}
        
        result ={}

        for _ ,row in df.iterrows():
            key = str(row.iloc[0].strip())
            value = str(row.iloc[1].strip())
            if key:
                result[key] = value

        return result