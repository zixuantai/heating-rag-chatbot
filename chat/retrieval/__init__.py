"""
检索模块
包含检索器封装和 Query 改写功能
"""
from .retriever_wrapper import RetrieverWrapper, HybridRetriever
from .query_rewriter import QueryRewriter, query_rewriter

# 创建全局检索器实例
retriever_wrapper_instance = RetrieverWrapper()

# 导出便捷函数
def retrieve(query: str):
    """执行检索（带 Rerank）"""
    return retriever_wrapper_instance.retrieve(query)

__all__ = ['RetrieverWrapper', 'HybridRetriever', 'QueryRewriter', 'query_rewriter', 'retrieve', 'retriever_wrapper_instance']
