# 供热行业 RAG 智能客服系统

基于 RAG（Retrieval-Augmented Generation）技术的供热行业智能客服系统。

## 项目结构

```
heating-rag-chatbot/
├── app.py                      # Streamlit 应用入口
├── config.py                   # 配置文件
├── requirements.txt            # 依赖包
├── .env.example                # 环境变量示例
├── uploads/                    # 上传文件临时目录
├── data/                       # 数据目录
│   └── *.pdf                   # PDF 文档（示例文件）
├── utils/                      # 工具函数
│   ├── __init__.py
│   ├── file_utils.py          # 文件处理工具
│   └── document_parser.py     # 文档解析工具
├── vector_db/                  # 向量数据库
│   ├── __init__.py
│   ├── milvus_client.py       # Milvus 客户端
│   ├── simple_vector_store.py # 简化版向量存储（备用）
│   └── vector_store_service.py # 向量存储服务
├── services/                   # 服务层
│   ├── __init__.py
│   └── knowledge_base.py      # 知识库服务
└── chat/                       # 聊天模块
    ├── __init__.py
    ├── chat_service.py        # 聊天服务
    ├── chat_history.py        # 聊天历史
    └── memory_manager.py      # 上下文记忆管理器
```

## 功能特点

- **多文档格式支持**：PDF、Word、PPT、TXT
- **MD5 去重**：避免重复上传相同内容
- **Milvus 向量数据库**：高性能向量检索（支持 Milvus Lite 本地模式）
- **BM25 混合检索**：结合向量检索和关键词检索
- **上下文记忆**：短时记忆 + 长时记忆，提供个性化服务
- **智能客服**：基于供热行业知识库的问答系统

## 文档切割

针对供热行业文档特点：

- **chunk_size**：800 tokens
- **chunk_overlap**：150 tokens
- **separators**：["\n\n", "\n", "##", "###", ".", "!", "?", "。", "！", "？", " ", ""]

## 技术栈

- **向量数据库**：Milvus（支持 Milvus Lite 本地模式）
- **嵌入模型**：DashScope（智源 BGE）
- **对话模型**：通义千问
- **文档处理**：PyPDF2、python-docx、python-pptx
- **Web 框架**：Streamlit
- **记忆系统**：SQLite + LLM 信息提取
