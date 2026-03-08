"""
简化版向量存储服务
使用内存存储，无需外部依赖
"""
import numpy as np
from typing import List, Dict
import json
import os
from utils.file_utils import ensure_dir


class SimpleVectorStore:
    """简化版向量存储"""
    
    def __init__(self):
        self.storage_path = "./data/vector_store.json"
        self.vectors = []
        self.documents = []
        self.load_from_file()
    
    def load_from_file(self):
        """从文件加载向量数据"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.vectors = [np.array(v) for v in data.get('vectors', [])]
                    self.documents = data.get('documents', [])
            except Exception:
                pass
    
    def save_to_file(self):
        """保存向量数据到文件"""
        ensure_dir(os.path.dirname(self.storage_path))
        try:
            data = {
                'vectors': [v.tolist() for v in self.vectors],
                'documents': self.documents
            }
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def add_documents(self, texts: List[str], vectors: List[List[float]], metadatas: List[Dict] = None):
        """添加文档和向量"""
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        for i, (text, vector) in enumerate(zip(texts, vectors)):
            self.vectors.append(np.array(vector))
            self.documents.append({
                'text': text,
                'metadata': metadatas[i]
            })
        
        self.save_to_file()
    
    def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict]:
        """搜索相似向量"""
        if not self.vectors:
            return []
        
        query_vec = np.array(query_vector)
        similarities = []
        
        for i, vec in enumerate(self.vectors):
            similarity = self._cosine_similarity(query_vec, vec)
            similarities.append((i, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, sim in similarities[:top_k]:
            results.append({
                'document': self.documents[idx],
                'score': sim,
                'metadata': self.documents[idx]['metadata']
            })
        
        return results
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'total_vectors': len(self.vectors),
            'total_documents': len(self.documents)
        }
    
    def clear(self):
        """清空存储"""
        self.vectors = []
        self.documents = []
        self.save_to_file()
