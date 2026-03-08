from pymilvus import MilvusClient, DataType
import config
from utils.file_utils import ensure_dir
import os


class MilvusVectorDB:
    """Milvus 向量数据库服务 - 使用 Milvus Lite 本地模式"""
    
    def __init__(self):
        self.collection_name = config.MILVUS_COLLECTION_NAME
        self.db_path = "./data/milvus_data.db"
        self.client = None
        
    def connect(self):
        """连接到 Milvus 数据库（本地文件模式）"""
        try:
            ensure_dir(os.path.dirname(self.db_path))
            self.client = MilvusClient(uri=self.db_path)
            return True
        except Exception as e:
            return False
    
    def create_collection(self, embedding_dim=None):
        """创建向量集合（如果不存在）"""
        if self.client is None:
            if not self.connect():
                return False
        
        try:
            if self.client.has_collection(collection_name=self.collection_name):
                return True
            
            dim = embedding_dim or config.EMBEDDING_DIM
            
            schema = self.client.create_schema(
                auto_id=False,
                enable_dynamic_field=True,
            )
            
            schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True, auto_id=True)
            schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=dim)
            schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=65535)
            schema.add_field(field_name="source", datatype=DataType.VARCHAR, max_length=255)
            schema.add_field(field_name="file_type", datatype=DataType.VARCHAR, max_length=10)
            schema.add_field(field_name="create_time", datatype=DataType.VARCHAR, max_length=50)
            
            self.client.create_collection(
                collection_name=self.collection_name,
                schema=schema
            )
            
            self.client.create_index(
                collection_name=self.collection_name,
                index_params={
                    "index_type": config.MILVUS_INDEX_TYPE,
                    "metric_type": config.MILVUS_METRIC_TYPE,
                    "params": config.MILVUS_INDEX_PARAMS
                },
                field_name="vector"
            )
            
            return True
            
        except Exception as e:
            return False
    
    def insert_data(self, data):
        """插入数据"""
        if self.client is None:
            if not self.connect():
                return False
        
        try:
            self.client.insert(
                collection_name=self.collection_name,
                data=data
            )
            return True
        except Exception as e:
            return False
    
    def search(self, vectors, limit=5):
        """搜索向量"""
        if self.client is None:
            if not self.connect():
                return []
        
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                data=vectors,
                limit=limit,
                output_fields=["text", "source", "file_type", "create_time"]
            )
            return results
        except Exception as e:
            return []
    
    def get_collection_info(self):
        """获取集合信息"""
        if self.client is None:
            if not self.connect():
                return None
        
        try:
            info = self.client.describe_collection(
                collection_name=self.collection_name
            )
            return info
        except Exception as e:
            return None
    
    def get_collection_stats(self):
        """获取集合统计信息"""
        if self.client is None:
            if not self.connect():
                return None
        
        try:
            stats = self.client.get_collection_stats(
                collection_name=self.collection_name
            )
            return stats
        except Exception as e:
            return None
    
    def delete_collection(self):
        """删除集合"""
        if self.client is None:
            if not self.connect():
                return False
        
        try:
            self.client.drop_collection(
                collection_name=self.collection_name
            )
            return True
        except Exception as e:
            return False
