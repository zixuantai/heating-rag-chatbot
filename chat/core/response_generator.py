"""
响应生成模块
负责 LLM 调用和响应处理（流式/非流式）
"""
from typing import Generator
from langchain_core.messages import BaseMessage
from langchain_community.chat_models.tongyi import ChatTongyi
import config


class ResponseGenerator:
    """响应生成器"""
    
    def __init__(self):
        self.chat_model = ChatTongyi(model=config.CHAT_MODEL_NAME)
    
    def generate(self, messages: list) -> str:
        """
        生成响应（非流式）
        
        Args:
            messages: 消息列表
            
        Returns:
            str: 生成的响应内容
        """
        response = self.chat_model.invoke(messages)
        return response.content
    
    def generate_stream(self, messages: list) -> Generator[str, None, None]:
        """
        生成响应（流式输出）
        
        Args:
            messages: 消息列表
            
        Yields:
            str: 响应内容片段
        """
        full_response = ""
        for chunk in self.chat_model.stream(messages):
            if chunk.content:
                full_response += chunk.content
                yield chunk.content
    
    def generate_with_retry(self, messages: list, max_retries: int = 2) -> str:
        """
        生成响应（带重试机制）
        
        Args:
            messages: 消息列表
            max_retries: 最大重试次数
            
        Returns:
            str: 生成的响应内容
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return self.generate(messages)
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    print(f"响应生成失败，重试 {attempt + 1}/{max_retries}: {e}")
        
        raise Exception(f"响应生成失败，已重试 {max_retries} 次：{last_error}")
