"""
聊天服务
整合 RAG 检索、LLM 生成和上下文记忆
"""
from typing import Dict
from chat.chat_history import (
    save_message as save_chat_message,
    init_chat_database
)
from chat.memory import memory_manager
from chat.retrieval import query_rewriter, retrieve, retriever_wrapper_instance
from chat.prompt import PromptBuilder
from .response_generator import ResponseGenerator


class ChatService:
    """聊天服务 - 带完整上下文记忆功能"""
    
    def __init__(self):
        """初始化聊天服务"""
        # 初始化聊天历史数据库
        init_chat_database()
        
        # 初始化组件
        self.response_generator = ResponseGenerator()
        self.retriever_func = retrieve  # 检索函数
        self.retriever_instance = retriever_wrapper_instance  # 检索器实例（用于 format_documents）
        self.prompt_builder = PromptBuilder()
    
    def invoke(self, query: str, session_id: str = "user_001") -> str:
        """
        调用聊天服务（非流式）
        
        完整流程：
        1. 保存用户消息到短时记忆
        2. Query 重写优化
        3. 检索相关知识库
        4. 获取记忆上下文
        5. 构建提示词
        6. 调用模型生成回复
        7. 保存 AI 回复到短时记忆
        8. 检查是否需要更新长时记忆
        """
        # 1. 保存用户消息到短时记忆
        memory_manager.add_to_short_term_memory(session_id, "用户", query)
        
        # 2. Query 重写优化
        rewritten_query = query_rewriter.rewrite(query)
        if rewritten_query != query:
            print(f"Query 重写：{query} → {rewritten_query}")
        
        # 3. 检索相关文档（使用重写后的 query）
        docs = self.retriever_func(rewritten_query)
        context = self.retriever_instance.format_documents(docs)
        
        # 4. 获取记忆上下文
        memory_context = memory_manager.get_full_memory_context(session_id)
        
        # 5. 构建提示词
        messages = self.prompt_builder.format_chat_prompt(
            context=context,
            memory_context=memory_context,
            history="当前对话进行中...",
            input_query=query
        )
        
        # 6. 调用模型生成回复
        response_content = self.response_generator.generate(messages)
        
        # 7. 保存 AI 回复到短时记忆
        memory_manager.add_to_short_term_memory(session_id, "助手", response_content)
        
        # 8. 检查是否需要更新长时记忆
        self._update_long_term_memory_if_needed(session_id)
        
        return response_content
    
    def stream(self, query: str, session_id: str = "user_001"):
        """
        调用聊天服务（流式输出）
        
        流程与 invoke 相同，但使用流式输出提升用户体验
        """
        # 1. 保存用户消息到短时记忆
        memory_manager.add_to_short_term_memory(session_id, "用户", query)
        
        # 2. Query 重写优化
        rewritten_query = query_rewriter.rewrite(query)
        if rewritten_query != query:
            print(f"Query 重写：{query} → {rewritten_query}")
        
        # 3. 检索相关文档（使用重写后的 query）
        docs = self.retriever_func(rewritten_query)
        context = self.retriever_instance.format_documents(docs)
        
        # 4. 获取记忆上下文
        memory_context = memory_manager.get_full_memory_context(session_id)
        
        # 5. 构建提示词
        messages = self.prompt_builder.format_chat_prompt(
            context=context,
            memory_context=memory_context,
            history="当前对话进行中...",
            input_query=query
        )
        
        # 6. 流式调用模型
        full_response = ""
        for chunk in self.response_generator.generate_stream(messages):
            full_response += chunk
            yield chunk
        
        # 7. 保存 AI 回复到短时记忆
        memory_manager.add_to_short_term_memory(session_id, "助手", full_response)
        
        # 8. 检查是否需要更新长时记忆
        self._update_long_term_memory_if_needed(session_id)
    
    def _update_long_term_memory_if_needed(self, session_id: str):
        """检查并更新长时记忆"""
        should_update, count = memory_manager.should_update_long_term_memory(session_id)
        
        if should_update:
            full_history = "\n".join([
                f"{msg['role']}:{msg['content']}" 
                for msg in memory_manager.get_short_term_memory(session_id)
            ])
            memory_manager.extract_and_store_long_term_memory(session_id, full_history)
    
    def get_memory_info(self, session_id: str) -> Dict:
        """获取当前会话的记忆信息（用于调试和展示）"""
        short_term = memory_manager.get_short_term_memory(session_id)
        long_term = memory_manager.get_long_term_memory(session_id)
        count = memory_manager.increment_conversation_count(session_id)
        
        return {
            'session_id': session_id,
            'conversation_count': count,
            'short_term_memory': short_term,
            'long_term_memory': long_term,
            'memory_context': memory_manager.get_full_memory_context(session_id)
        }
    
    def clear_memory(self, session_id: str):
        """清除指定会话的记忆"""
        memory_manager.clear_memory(session_id)
