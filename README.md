# 供热行业 RAG 智能客服系统

基于 RAG（Retrieval-Augmented Generation）技术的供热行业智能客服系统。

## 项目结构

```
heating-rag-chatbot/
├── app.py                      # Streamlit 应用入口
├── config.py                   # 配置文件
├── requirements.txt            # 依赖包
├── .env.example                # 环境变量示例
├── .gitignore                  # Git 忽略配置
├── README.md                   # 项目说明文档
├── data/                       # 数据目录
│   ├── *.pdf                   # PDF 文档（知识库文件）
│   └── memory.db               # 记忆数据库（SQLite）
├── models/                     # 模型文件目录（Git 忽略）
│   └── models/                 # Hugging Face 模型
│       └── bce-reranker-base_v1/  # Rerank 模型
├── utils/                      # 工具函数
│   ├── __init__.py
│   ├── file_utils.py           # 文件处理工具
│   └── document_parser.py      # 文档解析工具（PDF/Word/PPT/TXT）
├── vector_db/                  # 向量数据库模块
│   ├── __init__.py
│   ├── milvus_client.py        # Milvus 客户端
│   ├── simple_vector_store.py  # 内存向量存储（备用）
│   └── vector_store_service.py # 向量存储服务（统一接口）
├── services/                   # 服务层
│   ├── __init__.py
│   └── knowledge_base.py       # 知识库服务（上传/解析/存储）
└── chat/                       # 聊天模块（按功能组织）
    ├── __init__.py             # 模块导出
    ├── chat_history.py         # 聊天历史（SQLite 存储）
    ├── core/                   # 核心服务
    │   ├── __init__.py
    │   ├── chat_service.py     # 聊天主服务（协调层）
    │   └── response_generator.py # 响应生成器（流式/非流式）
    ├── memory/                 # 记忆模块
    │   ├── __init__.py
    │   ├── memory_manager.py   # 记忆管理器（统一接口）
    │   ├── short_term.py       # 短时记忆（最近 10 条对话）
    │   ├── long_term.py        # 长时记忆（用户画像/偏好）
    │   ├── extractor.py        # 记忆提取器（LLM 提取关键信息）
    │   └── counter.py          # 对话计数器（触发长时记忆更新）
    ├── retrieval/              # 检索模块
    │   ├── __init__.py
    │   ├── retriever_wrapper.py # 检索器封装（混合检索 + Query 改写）
    │   ├── query_rewriter.py   # Query 改写（术语标准化/问题具体化）
    │   └── reranker.py         # Rerank 重排序（Cross-Encoder）
    └── prompt/                 # 提示词模块
        ├── __init__.py
        └── builder.py          # 提示词构建器
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

## 安装与配置

### 1. 克隆项目
```bash
git clone <repository-url>
cd heating-rag-chatbot
```

### 2. 创建虚拟环境
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置环境变量
```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，填入 DashScope API Key
# DASHSCOPE_API_KEY=your_actual_api_key_here
```

**获取 API Key**：访问 [DashScope 控制台](https://dashscope.console.aliyun.com/)

### 5. 下载 Rerank 模型（可选）
```bash
# 如果启用 Rerank 功能，需要下载模型
# 模型文件较大（约 400MB），首次下载需要耐心等待
python download_rerank_model.py
```

### 6. 运行应用
```bash
streamlit run app.py
```

访问 http://localhost:8501 查看应用

## 安全与隐私

### Git 安全配置

项目已配置 `.gitignore`，以下文件**不会**被上传到云端：

- ✅ **模型文件**：`models/` 目录（体积较大，需本地下载）
- ✅ **虚拟环境**：`venv/` 目录
- ✅ **数据库文件**：`*.db`, `*.sqlite`, `*.sqlite3`
- ✅ **API 密钥**：`.env` 文件（包含敏感信息）
- ✅ **缓存文件**：`__pycache__/`, `*.pyc`
- ✅ **临时文件**：`uploads/`, `*.log`, `*.tmp`

### 敏感信息保护

**请勿将以下信息提交到 Git**：

- 🔒 API Keys（DashScope、阿里云等）
- 🔒 数据库密码
- 🔒 私人密钥文件
- 🔒 用户数据文件

### 检查敏感文件

在提交前，可以使用以下命令检查是否有敏感文件：

```bash
# 查看将要提交的文件
git status

# 查看未跟踪的文件
git ls-files --others --exclude-standard
```

## 项目结构详解

### 核心模块

#### 1. 检索模块 (`chat/retrieval/`)
- **retriever_wrapper.py**：混合检索器封装，整合向量检索和 BM25 检索
- **query_rewriter.py**：Query 改写模块，使用 LLM 将口语化问题转为专业术语
- **reranker.py**：Rerank 重排序模块，使用 Cross-Encoder 模型提升相关性排序

#### 2. 记忆模块 (`chat/memory/`)
- **memory_manager.py**：记忆管理器，统一管理短时记忆和长时记忆
- **short_term.py**：短时记忆，保存最近 10 条对话
- **long_term.py**：长时记忆，保存用户画像和偏好
- **extractor.py**：记忆提取器，使用 LLM 提取关键信息
- **counter.py**：对话计数器，触发长时记忆更新

#### 3. 核心服务 (`chat/core/`)
- **chat_service.py**：聊天主服务，协调检索、记忆、响应生成
- **response_generator.py**：响应生成器，支持流式和非流式输出

#### 4. 向量数据库 (`vector_db/`)
- **milvus_client.py**：Milvus 向量数据库客户端
- **vector_store_service.py**：向量存储服务，提供统一接口

#### 5. 服务层 (`services/`)
- **knowledge_base.py**：知识库服务，处理文件上传、解析、存储

#### 6. 工具函数 (`utils/`)
- **file_utils.py**：文件处理工具
- **document_parser.py**：文档解析工具，支持 PDF/Word/PPT/TXT

## 总结

本项目是一个完整的供热行业 RAG 智能客服系统，具备以下特点：

- 🎯 **专业性**：基于供热行业知识库，提供精准的专业回答
- 🔒 **安全性**：完善的 Git 安全配置，保护敏感信息
- 🚀 **高性能**：使用 Milvus 向量数据库和混合检索架构
- 🧠 **智能化**：支持 Query 改写、Rerank 重排序、上下文记忆
- 📦 **易部署**：详细的环境配置说明，快速上手

---

**更新日期**：2026-03-09
