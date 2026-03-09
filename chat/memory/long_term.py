"""
长时记忆模块
管理用户画像、偏好和重要事实
"""
import sqlite3
import json
import os
from typing import Dict


class LongTermMemory:
    """长时记忆管理器"""
    
    def __init__(self, db_path: str):
        """
        初始化长时记忆
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
    
    def save(self, session_id: str, user_profile: str = "", 
             preferences: str = "", important_facts: str = ""):
        """
        保存长时记忆
        
        Args:
            session_id: 会话 ID
            user_profile: 用户信息
            preferences: 用户偏好
            important_facts: 重要事实
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO long_term_memory 
                (session_id, user_profile, preferences, important_facts, last_updated)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                session_id,
                user_profile if isinstance(user_profile, str) else json.dumps(user_profile, ensure_ascii=False),
                preferences if isinstance(preferences, str) else json.dumps(preferences, ensure_ascii=False),
                important_facts if isinstance(important_facts, str) else json.dumps(important_facts, ensure_ascii=False)
            ))
            
            conn.commit()
        except Exception as e:
            pass
        finally:
            conn.close()
    
    def get(self, session_id: str) -> Dict:
        """
        获取长时记忆
        
        Args:
            session_id: 会话 ID
            
        Returns:
            Dict: 长时记忆字典
        """
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
                    'user_profile': self._parse_json(row[0]),
                    'preferences': self._parse_json(row[1]),
                    'important_facts': self._parse_json(row[2]),
                    'last_updated': row[3]
                }
            return {}
        except Exception as e:
            return {}
        finally:
            conn.close()
    
    def _parse_json(self, data: str) -> str:
        """解析 JSON 数据"""
        if not data:
            return ""
        try:
            return json.loads(data)
        except:
            return data
    
    def clear(self, session_id: str):
        """
        清除指定会话的长时记忆
        
        Args:
            session_id: 会话 ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM long_term_memory WHERE session_id = ?', (session_id,))
            conn.commit()
        except Exception as e:
            pass
        finally:
            conn.close()
