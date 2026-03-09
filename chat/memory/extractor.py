"""
记忆提取器模块
使用 LLM 从对话中提取关键信息
"""
import json
from typing import Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models.tongyi import ChatTongyi
import config


class MemoryExtractor:
    """记忆信息提取器"""
    
    def __init__(self):
        self.chat_model = ChatTongyi(model=config.CHAT_MODEL_NAME)
        self.prompt_template = self._create_prompt_template()
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """创建信息提取提示模板"""
        return ChatPromptTemplate.from_messages([
            ("system", """你是专业的信息提取助手。从对话中提取以下信息：

1. **用户偏好**：如温度偏好、设备偏好、服务偏好等
2. **用户信息**：如姓名、职业、家庭情况等
3. **重要事实**：如房屋类型、设备型号、特殊需求、历史问题等
4. **性格特点**：如沟通风格、喜好等

请以 JSON 格式返回提取的信息，格式如下：
{{
  "preferences": "用户偏好描述",
  "user_info": "用户基本信息",
  "important_facts": "重要事实",
  "personality": "性格特点"
}}"""),
            ("user", "请从以下对话中提取用户的关键信息：\n\n{conversation}")
        ])
    
    def extract(self, conversation_history: str) -> Dict:
        """
        从对话历史中提取信息
        
        Args:
            conversation_history: 对话历史字符串
            
        Returns:
            Dict: 提取的信息字典
        """
        try:
            # 使用大模型提取信息
            messages = self.prompt_template.format_messages(conversation=conversation_history)
            response = self.chat_model.invoke(messages)
            
            # 解析响应
            content = response.content.strip()
            content = self._clean_json_content(content)
            
            extracted_info = json.loads(content)
            return extracted_info
        except Exception as e:
            print(f"记忆提取失败：{e}")
            return {}
    
    def _clean_json_content(self, content: str) -> str:
        """清理 JSON 内容"""
        # 移除可能的 markdown 标记
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        # 移除首尾空格
        content = content.strip()
        return content
