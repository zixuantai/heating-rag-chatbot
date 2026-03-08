"""
上下文记忆管理器
实现短时记忆和长时记忆功能
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models.tongyi import ChatTongyi
import config


class ContextMemoryManager:
    """上下文记忆管理器"""
    
    def __init__(self):
        self.chat_model = ChatTongyi(model=config.CHAT_MODEL_NAME)
        self.short_term_limit = 10  # 短时记忆限制
        self.long_term_threshold = 5  # 长时记忆更新阈值（每5轮对话）
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "memory.db")
        self._init_database()
        self.extraction_prompt = self._create_extraction_prompt()
    
    def _init_database(self):
        """初始化记忆数据库"""
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
    
    def _create_extraction_prompt(self):
        """创建信息提取提示模板"""
        return ChatPromptTemplate.from_messages([
            ("system", """你是专业的信息提取助手。从对话中提取以下信息：

1. **用户偏好**：如温度偏好、设备偏好、服务偏好等
2. **用户信息**：如姓名、职业、家庭情况等
3. **重要事实**：如房屋类型、设备型号、特殊需求、历史问题等
4. **性格特点**：如沟通风格、喜好等

请以JSON格式返回提取的信息，格式如下：
{
  "preferences": "用户偏好描述",
  "user_info": "用户基本信息",
  "important_facts": "重要事实",
  "personality": "性格特点"
}"""),
            ("user", "请从以下对话中提取用户的关键信息：\n\n{conversation}")
        ])
    
    def add_to_short_term_memory(self, session_id: str, role: str, content: str):
        """添加到短时记忆"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 插入新消息
            cursor.execute('''
                INSERT INTO short_term_memory (session_id, role, content)
                VALUES (?, ?, ?)
            ''', (session_id, role, content))
            
            # 保持只保留最近的对话
            cursor.execute('''
                DELETE FROM short_term_memory
                WHERE session_id = ? AND id NOT IN (
                    SELECT id FROM short_term_memory
                    WHERE session_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                )
            ''', (session_id, session_id, self.short_term_limit))
            
            conn.commit()
        except Exception as e:
            pass
        finally:
            conn.close()
    
    def get_short_term_memory(self, session_id: str) -> List[Dict]:
        """获取短时记忆（最近的对话历史）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT role, content, timestamp
                FROM short_term_memory
                WHERE session_id = ?
                ORDER BY timestamp ASC
            ''', (session_id,))
            
            rows = cursor.fetchall()
            memory = []
            for row in rows:
                memory.append({
                    'role': row[0],
                    'content': row[1],
                    'timestamp': row[2]
                })
            
            return memory
        except Exception as e:
            return []
        finally:
            conn.close()
    
    def extract_and_store_long_term_memory(self, session_id: str, conversation_history: str):
        """从对话历史中提取并存储长时记忆"""
        try:
            # 使用大模型提取信息
            messages = self.extraction_prompt.format_messages(conversation=conversation_history)
            response = self.chat_model.invoke(messages)
            
            # 解析响应
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            extracted_info = json.loads(content)
            
            # 保存到长时记忆
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO long_term_memory 
                (session_id, user_profile, preferences, important_facts, last_updated)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                session_id,
                json.dumps(extracted_info.get('user_info', ''), ensure_ascii=False),
                json.dumps(extracted_info.get('preferences', ''), ensure_ascii=False),
                json.dumps(extracted_info.get('important_facts', ''), ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
            
            return extracted_info
        except Exception as e:
            return {}
    
    def get_long_term_memory(self, session_id: str) -> Dict:
        """获取长时记忆"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT user_profile, preferences, important_facts, last_updated
                FROM long_term_memory
                WHERE session_id = ?
            ''', (session_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'user_profile': json.loads(row[0]) if row[0] else "",
                    'preferences': json.loads(row[1]) if row[1] else "",
                    'important_facts': json.loads(row[2]) if row[2] else "",
                    'last_updated': row[3]
                }
            return {}
        except Exception as e:
            return {}
        finally:
            conn.close()
    
    def increment_conversation_count(self, session_id: str) -> int:
        """增加对话计数并返回当前计数"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 如果不存在则创建记录
            cursor.execute('''
                INSERT OR IGNORE INTO conversation_counter (session_id, count)
                VALUES (?, 0)
            ''', (session_id,))
            
            # 增加计数
            cursor.execute('''
                UPDATE conversation_counter
                SET count = count + 1
                WHERE session_id = ?
            ''', (session_id,))
            
            # 获取新的计数
            cursor.execute('''
                SELECT count FROM conversation_counter
                WHERE session_id = ?
            ''', (session_id,))
            
            row = cursor.fetchone()
            new_count = row[0] if row else 1
            
            conn.commit()
            return new_count
        except Exception as e:
            return 1
        finally:
            conn.close()
    
    def should_update_long_term_memory(self, session_id: str) -> Tuple[bool, int]:
        """判断是否应该更新长时记忆"""
        count = self.increment_conversation_count(session_id)
        return count % self.long_term_threshold == 0, count
    
    def get_full_memory_context(self, session_id: str) -> str:
        """获取完整的记忆上下文（短时+长时）"""
        # 获取短时记忆
        short_term = self.get_short_term_memory(session_id)
        
        # 获取长时记忆
        long_term = self.get_long_term_memory(session_id)
        
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
            recent_dialogue = "\n".join([f"{msg['role']}：{msg['content']}" for msg in short_term[-5:]])  # 最近5轮对话
            context_parts.append(f"近期对话：\n{recent_dialogue}")
        
        return "\n".join(context_parts) if context_parts else "暂无记忆信息"
    
    def clear_memory(self, session_id: str):
        """清除指定会话的所有记忆"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM short_term_memory WHERE session_id = ?', (session_id,))
            cursor.execute('DELETE FROM long_term_memory WHERE session_id = ?', (session_id,))
            cursor.execute('DELETE FROM conversation_counter WHERE session_id = ?', (session_id,))
            
            conn.commit()
        except Exception as e:
            pass
        finally:
            conn.close()


# 全局记忆管理器实例
memory_manager = ContextMemoryManager()