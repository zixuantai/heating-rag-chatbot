"""
Query 重写模块
使用 LLM 将用户问题改写为更专业的检索 query
"""
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate
import config


class QueryRewriter:
    """Query 重写器"""
    
    def __init__(self):
        self.chat_model = ChatTongyi(model=config.CHAT_MODEL_NAME)
        self.prompt_template = self._create_prompt_template()
    
    def _create_prompt_template(self):
        """创建 Query 重写提示模板"""
        return ChatPromptTemplate.from_messages([
            ("system", """你是供热行业智能客服系统的 Query 优化专家。

## 你的任务
将用户的原始问题改写为更适合检索的专业 query。

## 改写原则
1. **术语标准化**：使用供热行业标准术语
   - "暖气包" → "暖气片"
   - "地暖管" → "地暖管道"
   - "热力公司" → "供热企业"

2. **问题具体化**：将模糊表达转为具体描述
   - "不暖和" → "温度过低"
   - "坏了" → "故障"
   - "咋整" → "处理方法"

3. **类型识别**：明确问题类型
   - 设备故障类：添加"原因"、"解决方法"、"排查步骤"
   - 政策咨询类：添加"政策规定"、"收费标准"
   - 操作指导类：添加"操作步骤"、"使用方法"

4. **保持简洁**：query 长度控制在 20-50 字

## 输出格式
直接输出改写后的 query，不要任何解释。"""),
            ("user", "用户问题：{query}\n\n改写后的 query：")
        ])
    
    def rewrite(self, query: str) -> str:
        """
        重写单个 query
        
        Args:
            query: 用户原始问题
            
        Returns:
            改写后的专业 query
        """
        try:
            messages = self.prompt_template.format_messages(query=query)
            response = self.chat_model.invoke(messages)
            rewritten_query = response.content.strip()
            
            # 清理可能的多余内容
            if rewritten_query.startswith("改写后的 query："):
                rewritten_query = rewritten_query.replace("改写后的 query：", "").strip()
            if rewritten_query.startswith("改写后："):
                rewritten_query = rewritten_query.replace("改写后：", "").strip()
            
            return rewritten_query
        except Exception as e:
            # 如果重写失败，返回原始 query
            print(f"Query 重写失败，使用原始 query: {e}")
            return query
    
    def rewrite_batch(self, queries: list) -> list:
        """
        批量重写 query
        
        Args:
            queries: 原始 query 列表
            
        Returns:
            改写后的 query 列表
        """
        return [self.rewrite(query) for query in queries]


# 全局实例
query_rewriter = QueryRewriter()
