"""
聊天历史管理模块
使用SQLite数据库存储聊天记录
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# 数据库文件路径
CHAT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chat_history.db")


def init_chat_database():
    """初始化聊天历史数据库"""
    # 确保data目录存在
    data_dir = os.path.dirname(CHAT_DB_PATH)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    conn = sqlite3.connect(CHAT_DB_PATH)
    cursor = conn.cursor()
    
    # 创建聊天记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    ''')
    
    # 创建索引
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_session_id ON chat_messages(session_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_timestamp ON chat_messages(timestamp)
    ''')
    
    conn.commit()
    conn.close()


def save_message(session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
    """
    保存消息到聊天历史
    
    Args:
        session_id: 会话ID
        role: 角色 (human/ai/system)
        content: 消息内容
        metadata: 可选的元数据字典
    """
    # 确保数据库已初始化
    if not os.path.exists(CHAT_DB_PATH):
        init_chat_database()
    
    conn = sqlite3.connect(CHAT_DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO chat_messages (session_id, role, content, metadata)
            VALUES (?, ?, ?, ?)
        ''', (session_id, role, content, json.dumps(metadata) if metadata else None))
        
        conn.commit()
    except Exception as e:
        pass
    finally:
        conn.close()


def get_history(session_id: str, limit: int = 50) -> List[Dict]:
    """
    获取聊天历史
    
    Args:
        session_id: 会话ID
        limit: 返回的最大消息数量
        
    Returns:
        消息列表，每个消息包含role, content, timestamp
    """
    # 确保数据库已初始化
    if not os.path.exists(CHAT_DB_PATH):
        init_chat_database()
        return []
    
    conn = sqlite3.connect(CHAT_DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT role, content, timestamp, metadata
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        ''', (session_id, limit))
        
        rows = cursor.fetchall()
        
        messages = []
        for row in rows:
            messages.append({
                'role': row[0],
                'content': row[1],
                'timestamp': row[2],
                'metadata': json.loads(row[3]) if row[3] else None
            })
        
        return messages
    except Exception as e:
        return []
    finally:
        conn.close()


def get_history_as_langchain_messages(session_id: str, limit: int = 50) -> List:
    """
    获取聊天历史并转换为LangChain消息格式
    
    Args:
        session_id: 会话ID
        limit: 返回的最大消息数量
        
    Returns:
        LangChain消息对象列表 (HumanMessage, AIMessage, SystemMessage)
    """
    messages = get_history(session_id, limit)
    
    langchain_messages = []
    for msg in messages:
        role = msg['role']
        content = msg['content']
        
        if role == 'human':
            langchain_messages.append(HumanMessage(content=content))
        elif role == 'ai':
            langchain_messages.append(AIMessage(content=content))
        elif role == 'system':
            langchain_messages.append(SystemMessage(content=content))
    
    return langchain_messages


def clear_history(session_id: str):
    """
    清空指定会话的聊天历史
    
    Args:
        session_id: 会话ID
    """
    if not os.path.exists(CHAT_DB_PATH):
        return
    
    conn = sqlite3.connect(CHAT_DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            DELETE FROM chat_messages WHERE session_id = ?
        ''', (session_id,))
        
        conn.commit()
    except Exception as e:
        pass
    finally:
        conn.close()


def get_all_sessions() -> List[str]:
    """
    获取所有会话ID列表
    
    Returns:
        会话ID列表
    """
    if not os.path.exists(CHAT_DB_PATH):
        return []
    
    conn = sqlite3.connect(CHAT_DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT DISTINCT session_id FROM chat_messages ORDER BY session_id
        ''')
        
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        return []
    finally:
        conn.close()


def get_session_stats(session_id: str) -> Dict:
    """
    获取会话统计信息
    
    Args:
        session_id: 会话ID
        
    Returns:
        统计信息字典
    """
    if not os.path.exists(CHAT_DB_PATH):
        return {'message_count': 0, 'first_message': None, 'last_message': None}
    
    conn = sqlite3.connect(CHAT_DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 获取消息数量
        cursor.execute('''
            SELECT COUNT(*) FROM chat_messages WHERE session_id = ?
        ''', (session_id,))
        message_count = cursor.fetchone()[0]
        
        # 获取第一条和最后一条消息时间
        cursor.execute('''
            SELECT MIN(timestamp), MAX(timestamp) 
            FROM chat_messages 
            WHERE session_id = ?
        ''', (session_id,))
        
        result = cursor.fetchone()
        first_message = result[0]
        last_message = result[1]
        
        return {
            'message_count': message_count,
            'first_message': first_message,
            'last_message': last_message
        }
    except Exception as e:
        return {'message_count': 0, 'first_message': None, 'last_message': None}
    finally:
        conn.close()


# 初始化数据库
if __name__ == "__main__":
    init_chat_database()
