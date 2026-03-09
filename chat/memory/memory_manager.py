"""
上下文记忆管理器
整合短时记忆、长时记忆、记忆提取和对话计数
"""
import os
from typing import Dict, List, Tuple
from .short_term import ShortTermMemory
from .long_term import LongTermMemory
from .extractor import MemoryExtractor
from .counter import ConversationCounter


class ContextMemoryManager:
    """上下文记忆管理器"""
    
    def __init__(self):
        # 数据库路径
        self.db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "data", 
            "memory.db"
        )
        
        # 初始化数据库
        self._init_database()
        
        # 初始化各组件
        self.short_term = ShortTermMemory(self.db_path, limit=10)
        self.long_term = LongTermMemory(self.db_path)
        self.extractor = MemoryExtractor()
        self.counter = ConversationCounter(self.db_path, update_threshold=5)
    
    def _init_database(self):
        """初始化记忆数据库"""
        import sqlite3
        
        data_dir = os.path.dirname(self.db_path)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建短时记忆表（最近对话）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS short_term_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建长时记忆表（用户画像和偏好）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS long_term_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL UNIQUE,
                user_profile TEXT,
                preferences TEXT,
                important_facts TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建对话计数表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_counter (
                session_id TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_short ON short_term_memory(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_long ON long_term_memory(session_id)')
        
        conn.commit()
        conn.close()
    
    def add_to_short_term_memory(self, session_id: str, role: str, content: str):
        """添加到短时记忆"""
        self.short_term.add(session_id, role, content)
    
    def get_short_term_memory(self, session_id: str) -> List[Dict]:
        """获取短时记忆"""
        return self.short_term.get(session_id)
    
    def extract_and_store_long_term_memory(self, session_id: str, conversation_history: str) -> Dict:
        """从对话历史中提取并存储长时记忆"""
        # 提取信息
        extracted_info = self.extractor.extract(conversation_history)
        
        # 保存长时记忆
        self.long_term.save(
            session_id=session_id,
            user_profile=extracted_info.get('user_info', ''),
            preferences=extracted_info.get('preferences', ''),
            important_facts=extracted_info.get('important_facts', '')
        )
        
        return extracted_info
    
    def get_long_term_memory(self, session_id: str) -> Dict:
        """获取长时记忆"""
        return self.long_term.get(session_id)
    
    def increment_conversation_count(self, session_id: str) -> int:
        """增加对话计数"""
        return self.counter.increment(session_id)
    
    def should_update_long_term_memory(self, session_id: str) -> Tuple[bool, int]:
        """判断是否应该更新长时记忆"""
        return self.counter.should_update(session_id)
    
    def get_full_memory_context(self, session_id: str) -> str:
        """获取完整的记忆上下文"""
        # 获取短时记忆
        short_term = self.short_term.get(session_id)
        
        # 获取长时记忆
        long_term = self.long_term.get(session_id)
        
        # 构建记忆上下文
        context_parts = []
        
        # 添加长时记忆
        if long_term:
            if long_term.get('user_profile'):
                context_parts.append(f"用户信息：{long_term['user_profile']}")
            if long_term.get('preferences'):
                context_parts.append(f"用户偏好：{long_term['preferences']}")
            if long_term.get('important_facts'):
                context_parts.append(f"重要事实：{long_term['important_facts']}")
        
        # 添加短时记忆
        if short_term:
            recent_dialogue = "\n".join([
                f"{msg['role']}:{msg['content']}" 
                for msg in short_term[-5:]
            ])
            context_parts.append(f"近期对话：\n{recent_dialogue}")
        
        return "\n".join(context_parts) if context_parts else "暂无记忆信息"
    
    def clear_memory(self, session_id: str):
        """清除指定会话的所有记忆"""
        self.short_term.clear(session_id)
        self.long_term.clear(session_id)
        self.counter.clear(session_id)
