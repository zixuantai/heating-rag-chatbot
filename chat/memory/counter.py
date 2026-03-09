"""
对话计数模块
管理会话对话次数，用于触发长时记忆更新
"""
import sqlite3
import os


class ConversationCounter:
    """对话计数器"""
    
    def __init__(self, db_path: str, update_threshold: int = 5):
        """
        初始化对话计数器
        
        Args:
            db_path: 数据库路径
            update_threshold: 长时记忆更新阈值（每 N 轮对话更新一次）
        """
        self.db_path = db_path
        self.update_threshold = update_threshold
    
    def increment(self, session_id: str) -> int:
        """
        增加对话计数并返回当前计数
        
        Args:
            session_id: 会话 ID
            
        Returns:
            int: 当前对话次数
        """
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
    
    def should_update(self, session_id: str) -> tuple:
        """
        判断是否应该更新长时记忆
        
        Args:
            session_id: 会话 ID
            
        Returns:
            tuple: (是否应该更新，当前计数)
        """
        count = self.increment(session_id)
        return count % self.update_threshold == 0, count
    
    def clear(self, session_id: str):
        """
        清除指定会话的计数
        
        Args:
            session_id: 会话 ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM conversation_counter WHERE session_id = ?', (session_id,))
            conn.commit()
        except Exception as e:
            pass
        finally:
            conn.close()
