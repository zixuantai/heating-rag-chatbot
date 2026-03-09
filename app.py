"""
Streamlit应用入口
供热行业智能客服系统
"""
import streamlit as st
from services.knowledge_base import KnowledgeBaseService
from chat.core.chat_service import ChatService
import config


# 设置页面配置
st.set_page_config(
    page_title="供热行业智能客服系统",
    page_icon="❄️",
    layout="wide"
)


# 初始化服务
def init_services():
    """初始化所有服务"""
    if "kb_service" not in st.session_state:
        try:
            st.session_state["kb_service"] = KnowledgeBaseService()
            st.success("知识库服务初始化成功")
        except Exception as e:
            st.error(f"知识库服务初始化失败: {e}")
    
    if "chat_service" not in st.session_state:
        try:
            st.session_state["chat_service"] = ChatService()
            st.success("聊天服务初始化成功")
        except Exception as e:
            st.error(f"聊天服务初始化失败: {e}")


# 页面导航
def main():
    """主函数"""
    st.title("❄️ 供热行业智能客服系统")
    st.divider()
    
    # 初始化服务
    init_services()
    
    # 侧边栏导航
    page = st.sidebar.radio(
        "功能导航",
        ["💬 智能客服", "📁 知识库管理"],
        index=0
    )
    
    if page == "💬 智能客服":
        chat_page()
    elif page == "📁 知识库管理":
        knowledge_base_page()


# 智能客服页面
def chat_page():
    """智能客服页面"""
    st.header("智能客服")
    st.divider()
    
    # 聊天历史
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "assistant", "content": "您好！我是供热行业智能客服，可以帮您解答供热政策、设备操作、故障处理等方面的问题。请问有什么可以帮助您的？"}
        ]
    
    # 显示聊天历史
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # 用户输入
    prompt = st.chat_input("请输入您的问题...")
    
    if prompt:
        # 显示用户消息
        st.chat_message("user").write(prompt)
        st.session_state["messages"].append({"role": "user", "content": prompt})
        
        # 生成 AI 回复（流式输出）
        with st.chat_message("assistant"):
            with st.spinner("正在思考中..."):
                try:
                    response_placeholder = st.empty()
                    full_response = ""
                    
                    # 使用流式输出
                    for chunk in st.session_state["chat_service"].stream(
                        prompt, 
                        session_id="user_001"
                    ):
                        full_response += chunk
                        response_placeholder.write(full_response)
                    
                    # 更新聊天历史
                    st.session_state["messages"].append({"role": "assistant", "content": full_response})
                except Exception as e:
                    error_msg = f"抱歉，处理您的问题时出现了错误：{str(e)}"
                    response_placeholder.write(error_msg)
                    st.session_state["messages"].append({"role": "assistant", "content": error_msg})


# 知识库管理页面
def knowledge_base_page():
    """知识库管理页面"""
    st.header("知识库管理")
    st.divider()
    
    # 上传文档
    st.subheader("上传文档")
    st.write("支持PDF、Word、PPT、TXT格式的供热行业相关文档")
    
    uploaded_file = st.file_uploader(
        "请选择要上传的文档",
        type=["pdf", "docx", "pptx", "txt"],
        accept_multiple_files=False
    )
    
    if uploaded_file is not None:
        file_name = uploaded_file.name
        file_size = uploaded_file.size / 1024
        file_type = uploaded_file.type
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"📄 文件名: {file_name}")
        with col2:
            st.info(f"📏 大小: {file_size:.2f} KB")
        with col3:
            st.info(f"📝 格式: {file_type}")
        
        file_content = uploaded_file.getvalue()
        
        if st.button("上传到知识库"):
            with st.spinner("正在处理文档..."):
                result = st.session_state["kb_service"].upload_by_file(
                    file_content, 
                    file_name
                )
                
                if result["status"] == "success":
                    st.success(result["message"])
                elif result["status"] == "skip":
                    st.warning(result["message"])
                else:
                    st.error(result["message"])
    
    # 知识库统计
    st.subheader("知识库统计")
    stats = st.session_state["kb_service"].get_collection_stats()
    
    if "error" not in stats:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总分块数", stats.get("total_chunks", 0))
        with col2:
            st.metric("总文件数", stats.get("total_files", 0))
        with col3:
            st.metric("文件类型分布", len(stats.get("file_types", {})))
    else:
        st.warning("无法获取知识库统计信息")
    
    # 清空知识库
    st.subheader("操作")
    if st.button("清空知识库"):
        if st.confirm("确定要清空知识库吗？此操作不可恢复！"):
            result = st.session_state["kb_service"].clear_knowledge_base()
            if result["status"] == "success":
                st.success(result["message"])
                st.rerun()
            else:
                st.error(result["message"])


# 运行应用
if __name__ == "__main__":
    main()
