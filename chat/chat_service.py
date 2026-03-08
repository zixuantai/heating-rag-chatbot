"""
聊天服务
整合 RAG 检索、LLM 生成和上下文记忆
"""
from typing import Dict
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory, RunnableLambda
from services.knowledge_base import KnowledgeBaseService
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models.tongyi import ChatTongyi
import config
from vector_db.vector_store_service import VectorStoreService
from langchain_community.retrievers import BM25Retriever
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
import os
from chat.chat_history import (
    save_message as save_chat_message,
    init_chat_database
)
from chat.memory_manager import memory_manager


class HybridRetriever:
    """混合检索器：结合向量检索和 BM25 检索"""
    
    def __init__(self, vector_retriever, bm25_retriever, vector_weight=0.7, bm25_weight=0.3):
        self.vector_retriever = vector_retriever
        self.bm25_retriever = bm25_retriever
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
    
    def invoke(self, query):
        """执行混合检索"""
        # 向量检索
        vector_docs = self.vector_retriever.invoke(query)
        
        # BM25 检索
        bm25_docs = self.bm25_retriever.invoke(query)
        
        # 合并结果并去重
        all_docs = {}
        
        # 添加向量检索结果
        for i, doc in enumerate(vector_docs):
            doc_id = doc.page_content[:100]  # 使用内容前 100 字符作为 ID
            all_docs[doc_id] = {
                'doc': doc,
                'score': self.vector_weight * (1.0 / (i + 1))
            }
        
        # 添加 BM25 检索结果
        for i, doc in enumerate(bm25_docs):
            doc_id = doc.page_content[:100]
            if doc_id in all_docs:
                all_docs[doc_id]['score'] += self.bm25_weight * (1.0 / (i + 1))
            else:
                all_docs[doc_id] = {
                    'doc': doc,
                    'score': self.bm25_weight * (1.0 / (i + 1))
                }
        
        # 按分数排序
        sorted_docs = sorted(all_docs.values(), key=lambda x: x['score'], reverse=True)
        
        return [item['doc'] for item in sorted_docs[:config.SIMILARITY_THRESHOLD]]


class ChatService:
    """聊天服务 - 带完整上下文记忆功能"""
    
    def __init__(self):
        # 初始化聊天历史数据库
        init_chat_database()
        
        self.kb_service = KnowledgeBaseService()
        self.vector_service = VectorStoreService()
        self.chat_model = ChatTongyi(model=config.CHAT_MODEL_NAME)
        self.retriever = self._init_retriever()
        self.prompt_template = self._create_prompt_template()
    
    def _init_retriever(self):
        """初始化检索器（向量检索 + BM25 混合）"""
        # 向量检索
        vector_retriever = self.vector_service.get_retriever()
        
        # BM25 检索
        bm25_retriever = self._init_bm25_retriever()
        
        # 混合检索器
        hybrid_retriever = HybridRetriever(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            vector_weight=0.7,
            bm25_weight=0.3
        )
        
        return hybrid_retriever
    
    def _init_bm25_retriever(self):
        """初始化 BM25 检索器"""
        documents = []
        data_dir = "./data"
        if os.path.exists(data_dir):
            for file_name in os.listdir(data_dir):
                if file_name.endswith(".txt"):
                    file_path = os.path.join(data_dir, file_name)
                    try:
                        loader = TextLoader(file_path, encoding="utf-8")
                        docs = loader.load()
                        splitter = RecursiveCharacterTextSplitter(
                            chunk_size=config.CHUNK_SIZE,
                            chunk_overlap=config.CHUNK_OVERLAP,
                            separators=config.SEPARATORS
                        )
                        split_docs = splitter.split_documents(docs)
                        documents.extend(split_docs)
                    except Exception:
                        pass
        
        if documents:
            return BM25Retriever.from_documents(documents)
        else:
            # 返回一个空的检索器
            class EmptyRetriever:
                def invoke(self, query):
                    return []
            return EmptyRetriever()
    
    def _create_prompt_template(self):
        """创建提示模板 - 包含完整的系统提示词和记忆整合"""
        return ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的供热行业智能客服助手，具有强大的记忆能力。

## 你的核心能力
1. **专业知识**：基于提供的参考资料回答供热相关问题
2. **记忆能力**：记住用户的历史对话、偏好和重要信息
3. **个性化服务**：根据用户特点提供定制化建议

## 回答原则
- ✅ 优先使用提供的专业知识库内容
- ✅ 结合用户的个人偏好和历史对话
- ✅ 使用温暖、亲切、专业的语气
- ✅ 对于技术问题，提供清晰的操作步骤
- ✅ 对于政策问题，准确引用相关规定
- ✅ 如果资料不足，诚实地告知用户

## 已知信息
### 专业知识库
{context}

### 用户记忆
{memory_context}

## 对话历史
{history}

请基于以上所有信息，专业、友好地回答用户问题。"""),
            ("user", "{input}")
        ])
    
    def _format_documents(self, docs: list[Document]):
        """格式化文档"""
        if not docs:
            return "暂无相关参考资料"
        
        formatted_str = ""
        for doc in docs:
            formatted_str += f"【参考资料】{doc.page_content}\n"
            if doc.metadata:
                formatted_str += f"【来源】{doc.metadata.get('source', '未知')}\n\n"
        
        return formatted_str
    
    def _build_memory_context(self, session_id: str, query: str) -> str:
        """
        构建记忆上下文
        
        这是记忆功能的核心：
        1. 获取短时记忆（最近的对话历史）
        2. 获取长时记忆（用户画像、偏好等）
        3. 将两者结合形成完整的上下文
        """
        # 获取完整的记忆上下文（包括短时和长时记忆）
        memory_context = memory_manager.get_full_memory_context(session_id)
        return memory_context
    
    def _should_update_long_term_memory(self, session_id: str, full_history: str) -> bool:
        """
        判断是否需要更新长时记忆
        
        规则：每 5 轮对话更新一次长时记忆
        """
        should_update, count = memory_manager.should_update_long_term_memory(session_id)
        
        if should_update:
            # 提取并存储长时记忆
            memory_manager.extract_and_store_long_term_memory(session_id, full_history)
            return True
        
        return False
    
    def invoke(self, query: str, session_id: str = "user_001") -> str:
        """
        调用聊天服务（非流式）
        
        完整流程：
        1. 保存用户消息到短时记忆
        2. 检索相关知识库
        3. 获取记忆上下文
        4. 构建提示词
        5. 调用模型生成回复
        6. 保存 AI 回复到短时记忆
        7. 检查是否需要更新长时记忆
        """
        # 1. 保存用户消息到短时记忆
        memory_manager.add_to_short_term_memory(session_id, "用户", query)
        
        # 2. 检索相关文档
        docs = self.retriever.invoke(query)
        context = self._format_documents(docs)
        
        # 3. 获取记忆上下文
        memory_context = self._build_memory_context(session_id, query)
        
        # 4. 构建提示词
        messages = self.prompt_template.format_messages(
            context=context,
            memory_context=memory_context,
            history="当前对话进行中...",  # 历史对话已经在 memory_context 中
            input=query
        )
        
        # 5. 调用模型
        response = self.chat_model.invoke(messages)
        response_content = response.content
        
        # 6. 保存 AI 回复到短时记忆
        memory_manager.add_to_short_term_memory(session_id, "助手", response_content)
        
        # 7. 检查是否需要更新长时记忆
        full_history = "\n".join([
            f"{msg['role']}：{msg['content']}" 
            for msg in memory_manager.get_short_term_memory(session_id)
        ])
        self._should_update_long_term_memory(session_id, full_history)
        
        return response_content
    
    def stream(self, query: str, session_id: str = "user_001"):
        """
        调用聊天服务（流式输出）
        
        流程与 invoke 相同，但使用流式输出提升用户体验
        """
        # 1. 保存用户消息到短时记忆
        memory_manager.add_to_short_term_memory(session_id, "用户", query)
        
        # 2. 检索相关文档
        docs = self.retriever.invoke(query)
        context = self._format_documents(docs)
        
        # 3. 获取记忆上下文
        memory_context = self._build_memory_context(session_id, query)
        
        # 4. 构建提示词
        messages = self.prompt_template.format_messages(
            context=context,
            memory_context=memory_context,
            history="当前对话进行中...",
            input=query
        )
        
        # 5. 流式调用模型
        full_response = ""
        for chunk in self.chat_model.stream(messages):
            if chunk.content:
                full_response += chunk.content
                yield chunk.content
        
        # 6. 保存 AI 回复到短时记忆
        memory_manager.add_to_short_term_memory(session_id, "助手", full_response)
        
        # 7. 检查是否需要更新长时记忆
        full_history = "\n".join([
            f"{msg['role']}：{msg['content']}" 
            for msg in memory_manager.get_short_term_memory(session_id)
        ])
        self._should_update_long_term_memory(session_id, full_history)
    
    def get_memory_info(self, session_id: str) -> Dict:
        """获取当前会话的记忆信息（用于调试和展示）"""
        short_term = memory_manager.get_short_term_memory(session_id)
        long_term = memory_manager.get_long_term_memory(session_id)
        count = memory_manager.increment_conversation_count(session_id)
        
        return {
            'session_id': session_id,
            'conversation_count': count,
            'short_term_memory': short_term,
            'long_term_memory': long_term,
            'memory_context': memory_manager.get_full_memory_context(session_id)
        }
    
    def clear_memory(self, session_id: str):
        """清除指定会话的记忆"""
        memory_manager.clear_memory(session_id)