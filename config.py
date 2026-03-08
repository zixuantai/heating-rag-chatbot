# 项目配置文件
# 供热行业RAG智能客服系统

# Milvus配置
MILVUS_HOST = "localhost"
MILVUS_PORT = 19530
MILVUS_COLLECTION_NAME = "heating_rag"

# 文档切割配置
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
SEPARATORS = ["\n\n", "\n", "##", "###", ".", "!", "?", "。", "！", "？", " ", ""]

# 模型配置
# 智源BGE模型维度：bge-large-zh-v1.5为1024，bge-base-zh-v1.5为768
EMBEDDING_MODEL_NAME = "text-embedding-v4"  # DashScope嵌入模型
CHAT_MODEL_NAME = "qwen3-max"  # 通义千问对话模型
EMBEDDING_DIM = 1024  # 嵌入向量维度，根据实际模型调整

# 文件存储配置
UPLOAD_DIR = "./uploads"
MD5_FILE = "./data/md5_hash.txt"

# 检索配置
SIMILARITY_THRESHOLD = 5  # 检索返回的文档数量

# Milvus索引配置
MILVUS_INDEX_TYPE = "HNSW"
MILVUS_METRIC_TYPE = "COSINE"
MILVUS_INDEX_PARAMS = {"M": 8, "efConstruction": 64}
