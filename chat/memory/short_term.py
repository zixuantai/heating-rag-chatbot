"""
短时记忆模块
管理最近的对话历史（最近 10 条对话）
"""
import sqlite3
import os
from typing import Dict, List
from datetime import datetime


class ShortTermMemory:
    """短时记忆管理器"""
    
    def __init__(self, db_path: str, limit: int = 10):
        """
        初始化短时记忆
        
        Args:
            db_path: 数据库路径
            limit: 短时记忆限制条数
        """
        self.db_path = db_path
        self.limit = limit
    
    def add(self, session_id: str, role: str, content: str):
        """
        添加到短时记忆
        
        Args:
            session_id: 会话 ID
            role: 角色（用户/助手）
            content: 内容
        """
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
            ''', (session_id, session_id, self.limit))
            
            conn.commit()
        except Exception as e:
            pass
        finally:
            conn.close()
    
    def get(self, session_id: str) -> List[Dict]:
        """
        获取短时记忆
        
        Args:
            session_id: 会话 ID
            
        Returns:
            List[Dict]: 对话历史列表
        """
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
    
    def clear(self, session_id: str):
        """
        清除指定会话的短时记忆
        
        Args:
            session_id: 会话 ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM short_term_memory WHERE session_id = ?', (session_id,))
            conn.commit()
        except Exception as e:
            pass
        finally:
            conn.close()
