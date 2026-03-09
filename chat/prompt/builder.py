"""
提示词构建器
负责提示词模板的创建和管理
"""
from langchain_core.prompts import ChatPromptTemplate


class PromptBuilder:
    """提示词构建器"""
    
    def __init__(self):
        self.templates = {}
        self._init_templates()
    
    def _init_templates(self):
        """初始化所有提示词模板"""
        self.templates['chat'] = self._create_chat_template()
    
    def _create_chat_template(self) -> ChatPromptTemplate:
        """
        创建聊天提示词模板
        
        Returns:
            ChatPromptTemplate: 聊天提示词模板
        """
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
    
    def get_template(self, name: str) -> ChatPromptTemplate:
        """
        获取指定名称的提示词模板
        
        Args:
            name: 模板名称
            
        Returns:
            ChatPromptTemplate: 提示词模板
        """
        if name not in self.templates:
            raise ValueError(f"未找到模板：{name}")
        return self.templates[name]
    
    def format_chat_prompt(self, context: str, memory_context: str, 
                          history: str, input_query: str) -> list:
        """
        格式化聊天提示词
        
        Args:
            context: 专业知识库上下文
            memory_context: 用户记忆上下文
            history: 对话历史
            input_query: 用户输入
            
        Returns:
            list: 格式化后的消息列表
        """
        template = self.get_template('chat')
        return template.format_messages(
            context=context,
            memory_context=memory_context,
            history=history,
            input=input_query
        )
