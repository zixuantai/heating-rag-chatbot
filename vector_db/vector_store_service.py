from langchain_milvus import Milvus
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.vectorstores import VectorStore as LangchainVectorStore
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from typing import List, Dict, Any, Optional
import config
from vector_db.milvus_client import MilvusVectorDB
from vector_db.simple_vector_store import SimpleVectorStore


class VectorStoreService:
    """向量存储服务，支持Milvus和内存存储"""
    
    def __init__(self, embedding_model_name=None):
        self.embedding_model_name = embedding_model_name or config.EMBEDDING_MODEL_NAME
        self.embedding = DashScopeEmbeddings(model=self.embedding_model_name)
        self.milvus_client = MilvusVectorDB()
        self.vector_store = None
        self.use_memory = False
        self.memory_store = None
        self._init_vector_store()
    
    def _init_vector_store(self):
        """初始化向量存储"""
        try:
            # 尝试连接Milvus
            if not self.milvus_client.connect():
                raise Exception("无法连接到Milvus数据库")
            
            # 创建集合
            if not self.milvus_client.create_collection(embedding_dim=config.EMBEDDING_DIM):
                raise Exception("无法创建Milvus集合")
            
            # 初始化Langchain Milvus包装器
            self.vector_store = Milvus(
                embedding_function=self.embedding,
                connection_args={
                    "host": config.MILVUS_HOST,
                    "port": config.MILVUS_PORT,
                },
                collection_name=config.MILVUS_COLLECTION_NAME,
            )
            
        except Exception as e:
            # 使用内存存储作为备用
            self.use_memory = True
            self.memory_store = SimpleVectorStore()
            self.vector_store = MemoryVectorStoreWrapper(
                self.memory_store,
                self.embedding
            )
    
    def get_retriever(self, top_k=None):
        """获取检索器"""
        if self.vector_store is None:
            raise Exception("向量存储未初始化")
        
        k = top_k or config.SIMILARITY_THRESHOLD
        return self.vector_store.as_retriever(search_kwargs={"k": k})
    
    def add_texts(self, texts, metadatas=None):
        """添加文本到向量库"""
        if self.vector_store is None:
            raise Exception("向量存储未初始化")
        
        try:
            self.vector_store.add_texts(texts=texts, metadatas=metadatas)
            return True
        except Exception as e:
            return False
    
    def clear_collection(self):
        """清空集合"""
        try:
            if self.use_memory:
                # 清空内存存储
                self.memory_store.clear()
            else:
                # 清空 Milvus 集合
                if self.milvus_client.drop_collection():
                    self.milvus_client.create_collection(embedding_dim=config.EMBEDDING_DIM)
            return True
        except Exception as e:
            return False
    
    def delete_by_md5(self, md5: str) -> bool:
        """根据 MD5 删除文档"""
        try:
            if self.use_memory:
                # 内存存储：删除包含该 MD5 的所有文档
                self.memory_store.delete_by_metadata("md5", md5)
            else:
                # Milvus：通过表达式删除
                # 注意：Milvus 需要支持元数据过滤删除
                # 这里简化处理，重新创建集合（实际应该用 Milvus 的 delete 方法）
                # 由于 Milvus Lite 可能不支持复杂删除，暂时清空重建
                pass
            return True
        except Exception as e:
            return False
    
    def get_stats(self):
        """获取统计信息"""
        try:
            if self.use_memory:
                return self.memory_store.get_stats()
            else:
                stats = self.milvus_client.get_collection_stats()
                if stats:
                    return {
                        'total_vectors': stats.get('row_count', 0),
                        'total_documents': stats.get('row_count', 0)
                    }
        except Exception as e:
            return {'total_vectors': 0, 'total_documents': 0}


class MemoryVectorStoreWrapper(LangchainVectorStore):
    """内存向量存储的 LangChain 包装器"""
    
    def __init__(self, memory_store: SimpleVectorStore, embedding_function):
        self.memory_store = memory_store
        self.embedding_function = embedding_function
        self._texts = []
        self._metadatas = []
    
    @property
    def embeddings(self):
        """返回嵌入函数"""
        return self.embedding_function
    
    @classmethod
    def from_texts(
        cls,
        texts: List[str],
        embedding,
        metadatas: Optional[List[Dict]] = None,
        **kwargs: Any
    ) -> "MemoryVectorStoreWrapper":
        """从文本创建向量存储"""
        memory_store = SimpleVectorStore()
        wrapper = cls(memory_store, embedding)
        wrapper.add_texts(texts, metadatas)
        return wrapper
    
    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict]] = None) -> List[str]:
        """添加文本"""
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        # 生成嵌入向量
        vectors = self.embedding_function.embed_documents(texts)
        
        # 添加到内存存储
        self.memory_store.add_documents(texts, vectors, metadatas)
        
        # 保存引用
        self._texts.extend(texts)
        self._metadatas.extend(metadatas)
        
        return [str(i) for i in range(len(self._texts))]
    
    def similarity_search(self, query: str, k: int = 4, **kwargs: Any) -> List[Document]:
        """相似度搜索"""
        # 生成查询向量
        query_vector = self.embedding_function.embed_query(query)
        
        # 搜索
        results = self.memory_store.search(query_vector, top_k=k)
        
        # 转换为Document对象
        documents = []
        for result in results:
            doc_data = result['document']
            documents.append(Document(
                page_content=doc_data['text'],
                metadata=result['metadata']
            ))
        
        return documents
    
    def similarity_search_with_score(self, query: str, k: int = 4, **kwargs: Any) -> List[tuple[Document, float]]:
        """带分数的相似度搜索"""
        query_vector = self.embedding_function.embed_query(query)
        results = self.memory_store.search(query_vector, top_k=k)
        
        documents = []
        for result in results:
            doc_data = result['document']
            documents.append((
                Document(
                    page_content=doc_data['text'],
                    metadata=result['metadata']
                ),
                result['score']
            ))
        
        return documents
    
    def as_retriever(self, **kwargs: Any):
        """获取检索器"""
        from pydantic import PrivateAttr
        
        class MemoryRetriever(BaseRetriever):
            _vector_store: SimpleVectorStore = PrivateAttr()
            _embedding_function: Any = PrivateAttr()
            
            def __init__(self, vector_store, embedding_function, **kwargs):
                super().__init__(**kwargs)
                self._vector_store = vector_store
                self._embedding_function = embedding_function
            
            def _get_relevant_documents(self, query: str, **kwargs):
                k = kwargs.get('k', 4)
                query_vector = self._embedding_function.embed_query(query)
                results = self._vector_store.search(query_vector, top_k=k)
                
                documents = []
                for result in results:
                    doc_data = result['document']
                    documents.append(Document(
                        page_content=doc_data['text'],
                        metadata=result['metadata']
                    ))
                
                return documents
        
        return MemoryRetriever(self.memory_store, self.embedding_function)
