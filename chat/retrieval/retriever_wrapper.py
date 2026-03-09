"""
检索器封装模块
负责检索器的初始化和检索逻辑
"""
from typing import List
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from services.knowledge_base import KnowledgeBaseService
from vector_db.vector_store_service import VectorStoreService
import config
import os


class HybridRetriever:
    """混合检索器：结合向量检索和 BM25 检索"""
    
    def __init__(self, vector_retriever, bm25_retriever, 
                 vector_weight: float = 0.7, bm25_weight: float = 0.3):
        """
        初始化混合检索器
        
        Args:
            vector_retriever: 向量检索器
            bm25_retriever: BM25 检索器
            vector_weight: 向量检索权重
            bm25_weight: BM25 检索权重
        """
        self.vector_retriever = vector_retriever
        self.bm25_retriever = bm25_retriever
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
    
    def invoke(self, query: str) -> List[Document]:
        """
        执行混合检索
        
        Args:
            query: 查询文本
            
        Returns:
            List[Document]: 检索结果文档列表
        """
        # 向量检索
        vector_docs = self.vector_retriever.invoke(query)
        
        # BM25 检索
        bm25_docs = self.bm25_retriever.invoke(query)
        
        # 合并结果并去重
        all_docs = {}
        
        # 添加向量检索结果
        for i, doc in enumerate(vector_docs):
            doc_id = doc.page_content[:100]  # 使用内容前 100 字符作为 ID
            all_docs[doc_id] = {
                'doc': doc,
                'score': self.vector_weight * (1.0 / (i + 1))
            }
        
        # 添加 BM25 检索结果
        for i, doc in enumerate(bm25_docs):
            doc_id = doc.page_content[:100]
            if doc_id in all_docs:
                all_docs[doc_id]['score'] += self.bm25_weight * (1.0 / (i + 1))
            else:
                all_docs[doc_id] = {
                    'doc': doc,
                    'score': self.bm25_weight * (1.0 / (i + 1))
                }
        
        # 按分数排序
        sorted_docs = sorted(all_docs.values(), key=lambda x: x['score'], reverse=True)
        
        return [item['doc'] for item in sorted_docs[:config.SIMILARITY_THRESHOLD]]


class RetrieverWrapper:
    """检索器封装器"""
    
    def __init__(self):
        self.kb_service = KnowledgeBaseService()
        self.vector_service = VectorStoreService()
        self.retriever = self._init_retriever()
    
    def _init_retriever(self) -> HybridRetriever:
        """
        初始化混合检索器
        
        Returns:
            HybridRetriever: 混合检索器实例
        """
        # 向量检索
        vector_retriever = self.vector_service.get_retriever()
        
        # BM25 检索
        bm25_retriever = self._init_bm25_retriever()
        
        # 混合检索器
        return HybridRetriever(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            vector_weight=0.7,
            bm25_weight=0.3
        )
    
    def _init_bm25_retriever(self):
        """
        初始化 BM25 检索器
        
        Returns:
            BM25Retriever: BM25 检索器实例
        """
        documents = []
        data_dir = "./data"
        
        if os.path.exists(data_dir):
            for file_name in os.listdir(data_dir):
                if file_name.endswith(".txt"):
                    file_path = os.path.join(data_dir, file_name)
                    try:
                        loader = TextLoader(file_path, encoding="utf-8")
                        docs = loader.load()
                        splitter = RecursiveCharacterTextSplitter(
                            chunk_size=config.CHUNK_SIZE,
                            chunk_overlap=config.CHUNK_OVERLAP,
                            separators=config.SEPARATORS
                        )
                        split_docs = splitter.split_documents(docs)
                        documents.extend(split_docs)
                    except Exception:
                        pass
        
        if documents:
            return BM25Retriever.from_documents(documents)
        else:
            # 返回一个空的检索器
            class EmptyRetriever:
                def invoke(self, query):
                    return []
            return EmptyRetriever()
    
    def retrieve(self, query: str) -> List[Document]:
        """
        执行检索
        
        Args:
            query: 查询文本
            
        Returns:
            List[Document]: 检索结果文档列表
        """
        return self.retriever.invoke(query)
    
    def format_documents(self, docs: List[Document]) -> str:
        """
        格式化文档
        
        Args:
            docs: 文档列表
            
        Returns:
            str: 格式化后的文档字符串
        """
        if not docs:
            return "暂无相关参考资料"
        
        formatted_str = ""
        for doc in docs:
            formatted_str += f"【参考资料】{doc.page_content}\n"
            if doc.metadata:
                formatted_str += f"【来源】{doc.metadata.get('source', '未知')}\n\n"
        
        return formatted_str


# 全局单例
retriever_wrapper = RetrieverWrapper()
