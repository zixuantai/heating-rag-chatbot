"""
知识库服务
整合文档解析、MD5 去重和向量存储
"""
import os
import json
import config
from typing import List, Dict
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
        self.metadata_file = "./data/file_metadata.json"
        ensure_dir(config.UPLOAD_DIR)
        self._init_metadata_file()
    
    def _init_metadata_file(self):
        """初始化元数据文件"""
        if not os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)
    
    def _load_metadata(self) -> List[Dict]:
        """加载文件元数据"""
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def _save_metadata(self, metadata_list: List[Dict]):
        """保存文件元数据"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata_list, f, ensure_ascii=False, indent=2)
    
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
            
            # 保存 MD5
            save_md5_to_file(md5_hex, config.MD5_FILE)
            
            # 保存文件元数据
            file_metadata = self._load_metadata()
            file_metadata.append({
                "filename": filename,
                "file_type": metadata["file_type"],
                "file_size": len(file_content),
                "chunk_count": len(knowledge_chunks),
                "create_time": metadata["create_time"],
                "md5": md5_hex
            })
            self._save_metadata(file_metadata)
            
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
            file_metadata = self._load_metadata()
            
            # 统计文件类型分布
            file_types = {}
            for file_info in file_metadata:
                file_type = file_info.get("file_type", "unknown")
                file_types[file_type] = file_types.get(file_type, 0) + 1
            
            return {
                "total_chunks": sum(f.get("chunk_count", 0) for f in file_metadata),
                "total_files": len(file_metadata),
                "file_types": file_types
            }
        except Exception as e:
            return {"error": str(e)}
    
    def list_files(self) -> List[Dict]:
        """获取文件列表"""
        try:
            return self._load_metadata()
        except Exception as e:
            return []
    
    def delete_file(self, filename: str) -> Dict:
        """删除指定文件"""
        try:
            # 获取文件元数据
            file_metadata = self._load_metadata()
            
            # 查找要删除的文件
            file_info = None
            for f in file_metadata:
                if f["filename"] == filename:
                    file_info = f
                    break
            
            if not file_info:
                return {"status": "error", "message": f"文件 {filename} 不存在"}
            
            # 从向量库删除（通过 MD5 过滤）
            md5 = file_info.get("md5")
            if md5:
                # 从向量库中删除包含该 MD5 的所有分块
                self.vector_service.delete_by_md5(md5)
            
            # 从元数据列表移除
            file_metadata = [f for f in file_metadata if f["filename"] != filename]
            self._save_metadata(file_metadata)
            
            # 从 MD5 文件移除（可选，因为内容已删除）
            # 这里简化处理，不修改 MD5 文件
            
            return {
                "status": "success", 
                "message": f"[成功]文件 {filename} 已删除"
            }
        except Exception as e:
            return {"status": "error", "message": f"删除失败：{str(e)}"}
    
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
