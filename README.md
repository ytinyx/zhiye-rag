# 知页 RAG

阶段版本：`july-v4`。

- 文档解析与清洗
- 嵌入与文档入库
- 检索与缓存
- RAG API 与上传安全

## 环境与测试

使用 Python 3.12+。`uv sync --locked` 安装应用依赖；轻量检查可在独立虚拟环境中执行 `python -m pip install -r requirements-test.txt`，随后运行 `python -m pytest`。默认不调用真实模型 API，不加载嵌入或 PDF/OCR 模型。

## 使用

运行 `uv run --locked uvicorn src.api.main:app --port 8000`；访问 `http://localhost:8000/docs` 使用 API，`/api/health/` 检查状态。

## 本地数据与许可

按 `.env.example` 配置本地服务。`.env`、模型缓存和运行数据不纳入 Git。代码采用 [MIT License](LICENSE)，保留第三方名称与来源。
