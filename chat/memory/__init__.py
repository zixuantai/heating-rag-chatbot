"""
记忆模块
实现短时记忆、长时记忆、记忆提取和对话计数
"""
from .memory_manager import ContextMemoryManager

# 导出全局实例
memory_manager = ContextMemoryManager()

__all__ = ['ContextMemoryManager', 'memory_manager']
