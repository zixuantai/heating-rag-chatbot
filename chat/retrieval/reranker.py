"""
Rerank 重排序模块
使用 Cross-Encoder 对检索结果进行重排序，提升相关性
"""
from typing import List
from langchain_core.documents import Document
from sentence_transformers.cross_encoder import CrossEncoder
import os


class Reranker:
    """Rerank 重排序器"""
    
    def __init__(self, model_name: str = None, top_k: int = None):
        """
        初始化 Reranker
        
        Args:
            model_name: Cross-Encoder 模型名称（从 config 读取）
            top_k: 返回前 K 个最相关的文档
        """
        # 从 config 读取配置
        import config
        self.model_name = model_name or config.RERANK_MODEL_NAME
        self.top_k = top_k or config.RERANK_TOP_K
        self.model = None
    
    def _ensure_model_loaded(self):
        """确保模型已加载（延迟加载）"""
        if self.model is None:
            import os
            
            # 检查是否是本地路径
            is_local_path = os.path.exists(self.model_name)
            
            print(f"\n{'='*60}")
            print(f"[Rerank] 模型加载检查")
            print(f"{'='*60}")
            print(f"模型路径：{self.model_name}")
            print(f"本地路径：{'是' if is_local_path else '否'}")
            
            if is_local_path:
                print(f"\n检查本地文件:")
                try:
                    files = os.listdir(self.model_name)
                    for f in files:
                        if not f.startswith('.'):
                            print(f"  ✓ {f}")
                    
                    # 检查关键文件
                    critical_files = ['pytorch_model.bin', 'model.safetensors', 'config.json']
                    print(f"\n关键文件检查:")
                    for cf in critical_files:
                        exists = os.path.exists(os.path.join(self.model_name, cf))
                        print(f"  {'✓' if exists else '✗'} {cf}")
                except Exception as e:
                    print(f"  无法读取目录：{e}")
            
            try:
                # 设置 HuggingFace 镜像源
                os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
                
                print(f"\n正在加载 Cross-Encoder 模型...")
                
                # 加载 Cross-Encoder 模型
                self.model = CrossEncoder(
                    self.model_name,
                    trust_remote_code=True,
                    local_files_only=is_local_path  # 本地路径则只使用本地文件
                )
                print(f"\n✓ Rerank 模型加载成功！")
                print(f"{'='*60}\n")
            except Exception as e:
                print(f"\n✗ Rerank 模型加载失败：{e}")
                print(f"⚠️ 将跳过 Rerank，直接返回检索结果")
                if is_local_path:
                    print(f"\n💡 提示：本地模型文件不完整，缺少权重文件")
                    print(f"   请确保模型文件夹包含以下文件:")
                    print(f"   - pytorch_model.bin 或 model.safetensors")
                    print(f"   - config.json")
                    print(f"   - tokenizer_config.json")
                else:
                    print(f"\n💡 提示：网络问题导致模型下载失败")
                    print(f"   建议：使用 git lfs 手动下载模型")
                    print(f"   git clone https://hf-mirror.com/maidalun1020/bce-reranker-base_v1.git")
                print(f"{'='*60}\n")
                # 不抛出异常，让模型保持为 None，后续会降级处理
                self.model = None
    
    def rerank(self, query: str, documents: List[Document], top_k: int = None) -> List[Document]:
        """
        对检索结果进行重排序
        
        Args:
            query: 用户查询
            documents: 待排序的文档列表
            top_k: 返回前 K 个结果
            
        Returns:
            重排序后的文档列表
        """
        if not documents:
            print(f"\n[Rerank] 文档列表为空，跳过重排序")
            return []
        
        # 确保模型已加载
        self._ensure_model_loaded()
        
        if self.model is None:
            # 模型加载失败，直接返回原始文档
            k = self.top_k if top_k is None else top_k
            print(f"\n[Rerank] 模型未加载，降级处理：返回原始 Top-{k} 文档")
            return documents[:k]
        
        k = top_k if top_k is not None else self.top_k
        print(f"\n{'='*60}")
        print(f"[Rerank] 开始重排序")
        print(f"{'='*60}")
        print(f"原始查询：{query}")
        print(f"原始文档数：{len(documents)}")
        print(f"目标返回：{k}")
        
        # 1. 构建 query-document 对
        pairs = [[query, doc.page_content] for doc in documents]
        
        # 2. 使用模型预测相关性分数
        print(f"\n正在计算 {len(pairs)} 个 query-document 对的相关性分数...")
        scores = self.model.predict(pairs)
        
        # 3. 将文档和分数配对
        doc_scores = list(zip(documents, scores))
        
        # 4. 按分数降序排序
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 5. 打印调试信息
        print(f"\n[Rerank] 重排序结果（Top-{k}）:")
        print(f"{'='*60}")
        for i, (doc, score) in enumerate(doc_scores[:k], 1):
            content_preview = doc.page_content[:60].replace('\n', ' ')
            source = doc.metadata.get('source', 'unknown')
            print(f"  {i}. 分数：{score:.4f} - 来源：{source}")
            print(f"     内容：{content_preview}...")
        
        print(f"{'='*60}\n")
        
        # 6. 返回 top-k 个文档
        return [doc for doc, score in doc_scores[:k]]


# 全局实例
reranker = Reranker()
