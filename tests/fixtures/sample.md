# RAG sample notes

This is an original sample document for the parser tests. It contains no personal data, credentials, or material copied from a published report.

## Processing steps

- Read the document and preserve its filename.
- Divide the text into useful passages.
- Retrieve relevant passages before generating an answer.

```python
question = "What happens before an answer is generated?"
```

The retrieval step chooses passages from the uploaded documents. An answer should identify the passages that support it and acknowledge missing information.

## 中文演示说明

这个示例的文档处理流程是：读取文件并保留文件名，将文本分成片段，检索与问题相关的片段，再根据片段生成回答。回答应附上支持结论的来源；资料不足时应说明不知道。
