"""
知识库服务
整合文档解析、MD5去重和向量存储
"""
import os
import config
from utils.file_utils import (
    get_string_md5, 
    check_md5_in_file, 
    save_md5_to_file,
    ensure_dir
)
from utils.document_parser import parse_document
from vector_db.vector_store_service import VectorStoreService
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime


class KnowledgeBaseService:
    """知识库服务"""
    
    def __init__(self):
        self.vector_service = VectorStoreService()
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=config.SEPARATORS,
            length_function=len,
        )
        ensure_dir(config.UPLOAD_DIR)
    
    def upload_by_file(self, file_content, filename):
        """通过文件上传"""
        try:
            # 解析文档内容
            content = parse_document(file_content, filename)
            
            # 计算MD5避免重复
            md5_hex = get_string_md5(content)
            if check_md5_in_file(md5_hex, config.MD5_FILE):
                return {"status": "skip", "message": f"[跳过]内容已经存在知识库中"}
            
            # 分块处理
            if len(content) > config.CHUNK_SIZE:
                knowledge_chunks = self.spliter.split_text(content)
            else:
                knowledge_chunks = [content]
            
            # 生成元数据
            metadata = {
                "source": filename,
                "file_type": os.path.splitext(filename)[1].lower(),
                "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "operator": "system"
            }
            
            # 批量添加到向量库
            texts = [chunk for chunk in knowledge_chunks]
            metadatas = [metadata for _ in knowledge_chunks]
            
            self.vector_service.add_texts(texts, metadatas)
            
            # 保存MD5
            save_md5_to_file(md5_hex, config.MD5_FILE)
            
            return {
                "status": "success", 
                "message": f"[成功]文件 {filename} 已载入向量库，共分块 {len(knowledge_chunks)} 个",
                "chunks": len(knowledge_chunks)
            }
            
        except ValueError as e:
            return {"status": "error", "message": f"[失败]不支持的文件类型: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"[失败]上传失败: {str(e)}"}
    
    def upload_by_str(self, data: str, filename):
        """通过字符串上传"""
        try:
            # 计算MD5避免重复
            md5_hex = get_string_md5(data)
            if check_md5_in_file(md5_hex, config.MD5_FILE):
                return {"status": "skip", "message": "[跳过]内容已经存在知识库中"}
            
            # 分块处理
            if len(data) > config.CHUNK_SIZE:
                knowledge_chunks = self.spliter.split_text(data)
            else:
                knowledge_chunks = [data]
            
            # 生成元数据
            metadata = {
                "source": filename,
                "file_type": ".txt",
                "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "operator": "system"
            }
            
            # 批量添加到向量库
            texts = [chunk for chunk in knowledge_chunks]
            metadatas = [metadata for _ in knowledge_chunks]
            
            self.vector_service.add_texts(texts, metadatas)
            
            # 保存MD5
            save_md5_to_file(md5_hex, config.MD5_FILE)
            
            return {
                "status": "success", 
                "message": f"[成功]内容已经载入向量库，共分块 {len(knowledge_chunks)} 个",
                "chunks": len(knowledge_chunks)
            }
            
        except Exception as e:
            return {"status": "error", "message": f"[失败]上传失败: {str(e)}"}
    
    def get_collection_stats(self):
        """获取知识库统计信息"""
        try:
            # 这里需要从Milvus获取实际统计信息
            # 暂时返回占位信息
            return {
                "total_chunks": 0,
                "total_files": 0,
                "file_types": {}
            }
        except Exception as e:
            return {"error": str(e)}
    
    def clear_knowledge_base(self):
        """清空知识库"""
        try:
            self.vector_service.clear_collection()
            # 清空MD5文件
            if os.path.exists(config.MD5_FILE):
                os.remove(config.MD5_FILE)
            return {"status": "success", "message": "知识库已清空"}
        except Exception as e:
            return {"status": "error", "message": f"清空失败: {str(e)}"}
