"""
Chat 模块
按功能组织的聊天相关组件
"""

# 导出核心服务
from chat.core import ChatService, ResponseGenerator

# 导出记忆模块
from chat.memory import memory_manager, ContextMemoryManager

# 导出检索模块
from chat.retrieval import query_rewriter, retriever_wrapper, QueryRewriter, RetrieverWrapper

# 导出提示词模块
from chat.prompt import PromptBuilder

__all__ = [
    # 核心服务
    'ChatService',
    'ResponseGenerator',
    
    # 记忆模块
    'memory_manager',
    'ContextMemoryManager',
    
    # 检索模块
    'query_rewriter',
    'retriever_wrapper',
    'QueryRewriter',
    'RetrieverWrapper',
    
    # 提示词模块
    'PromptBuilder',
]
