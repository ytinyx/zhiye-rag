# 知页 RAG

阶段版本：`july-v3`。

- 文档解析与清洗
- 嵌入与文档入库
- 检索与缓存

## 环境与测试

使用 Python 3.12+。`uv sync --locked` 安装应用依赖；轻量检查可在独立虚拟环境中执行 `python -m pip install -r requirements-test.txt`，随后运行 `python -m pytest`。默认不调用真实模型 API，不加载嵌入或 PDF/OCR 模型。

## 使用

此阶段提供 Python 库模块，可从 `src.parsers` 导入 `ParserFactory` 或 `parse_file` 解析本地文件。其他模块按上述功能范围提供。

## 本地数据与许可

按 `.env.example` 配置本地服务。`.env`、模型缓存和运行数据不纳入 Git。代码采用 [MIT License](LICENSE)，保留第三方名称与来源。
