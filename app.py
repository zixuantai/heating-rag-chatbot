"""
Streamlit 应用入口
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
            st.error(f"知识库服务初始化失败：{e}")
    
    if "chat_service" not in st.session_state:
        try:
            st.session_state["chat_service"] = ChatService()
            st.success("聊天服务初始化成功")
        except Exception as e:
            st.error(f"聊天服务初始化失败：{e}")


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
        ["💬 智能客服", "⬆️ 上传文档", "📚 文档管理"],
        index=0
    )
    
    if page == "💬 智能客服":
        chat_page()
    elif page == "⬆️ 上传文档":
        upload_page()
    elif page == "📚 文档管理":
        document_management_page()


# 智能客服页面
def chat_page():
    """智能客服页面"""
    st.header("💬 智能客服")
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


# 上传文档页面
def upload_page():
    """上传文档页面"""
    st.header("⬆️ 上传文档")
    st.divider()
    
    st.write("支持 PDF、Word、PPT、TXT 格式的供热行业相关文档")
    
    uploaded_file = st.file_uploader(
        "请选择要上传的文档",
        type=["pdf", "docx", "pptx", "txt"],
        accept_multiple_files=False,
        key="upload_file"
    )
    
    if uploaded_file is not None:
        file_name = uploaded_file.name
        file_size = uploaded_file.size / 1024
        file_type = uploaded_file.type
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"📄 文件名：{file_name}")
        with col2:
            st.info(f"📏 大小：{file_size:.2f} KB")
        with col3:
            st.info(f"📝 格式：{file_type}")
        
        file_content = uploaded_file.getvalue()
        
        if st.button("上传到知识库", key="upload_btn"):
            with st.spinner("正在处理文档..."):
                result = st.session_state["kb_service"].upload_by_file(
                    file_content, 
                    file_name
                )
                
                if result["status"] == "success":
                    st.success(result["message"])
                    st.balloons()
                elif result["status"] == "skip":
                    st.warning(result["message"])
                else:
                    st.error(result["message"])
    
    st.divider()
    
    # 知识库统计
    st.subheader("📊 知识库统计")
    stats = st.session_state["kb_service"].get_collection_stats()
    
    if "error" not in stats:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总文件数", stats.get("total_files", 0))
        with col2:
            st.metric("总分块数", stats.get("total_chunks", 0))
        with col3:
            file_types = stats.get("file_types", {})
            st.metric("文件类型", len(file_types))
    else:
        st.warning("无法获取知识库统计信息")


# 文档管理页面
def document_management_page():
    """文档管理页面"""
    st.header("📚 文档管理")
    st.divider()
    
    # 获取文件列表
    files = st.session_state["kb_service"].list_files()
    
    if files:
        st.write(f"当前共有 **{len(files)}** 个文档")
        
        # 搜索框
        search_query = st.text_input(
            "🔍 搜索文档", 
            placeholder="输入文件名关键词进行搜索...",
            key="doc_search"
        )
        
        # 过滤文件
        if search_query:
            filtered_files = [f for f in files if search_query.lower() in f["filename"].lower()]
            st.caption(f"找到 {len(filtered_files)} 个匹配的文档")
        else:
            filtered_files = files
        
        if filtered_files:
            st.divider()
            
            # 文件列表
            for file_info in filtered_files:
                filename = file_info["filename"]
                file_type = file_info.get("file_type", "unknown")
                file_size = file_info.get("file_size", 0) / 1024  # KB
                chunk_count = file_info.get("chunk_count", 0)
                create_time = file_info.get("create_time", "")
                
                # 文件卡片
                with st.container():
                    col1, col2, col3, col4 = st.columns([4, 1, 2, 1])
                    
                    with col1:
                        st.write(f"**📄 {filename}**")
                        st.caption(f"上传时间：{create_time}")
                    
                    with col2:
                        st.caption(f"📝 {file_type}")
                        st.caption(f"📦 {file_size:.1f} KB")
                    
                    with col3:
                        st.caption(f"分块数：{chunk_count}")
                    
                    with col4:
                        # 删除按钮
                        if st.button("🗑️ 删除", key=f"delete_{filename}", type="secondary"):
                            with st.spinner(f"正在删除 {filename}..."):
                                result = st.session_state["kb_service"].delete_file(filename)
                                if result["status"] == "success":
                                    st.success(result["message"])
                                    st.rerun()
                                else:
                                    st.error(result["message"])
                    
                    st.divider()
        else:
            st.info("没有找到匹配的文档")
    else:
        st.info("📭 暂无文档，请前往「上传文档」页面添加文档")
        st.image("https://cdn-icons-png.flaticon.com/512/7486/7486747.png", width=200)
    
    # 清空知识库
    if files:
        st.divider()
        st.subheader("⚠️ 批量操作")
        st.warning("批量操作会影响所有文档，请谨慎使用！")
        
        if st.button("🗑️ 清空整个知识库", type="secondary", key="clear_all"):
            if st.confirm("确定要清空整个知识库吗？此操作不可恢复！"):
                with st.spinner("正在清空知识库..."):
                    result = st.session_state["kb_service"].clear_knowledge_base()
                    if result["status"] == "success":
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])


# 运行应用
if __name__ == "__main__":
    main()
