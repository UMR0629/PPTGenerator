import streamlit as st
import show 



# 初始化状态
if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 主页"

# 导航栏
# with st.sidebar:
#     pages = ["🏠 主页", "📊 大纲", "⚙️ 设置"]
#     st.session_state.current_page = st.selectbox("导航", pages, index=pages.index(st.session_state.current_page))
if st.session_state.current_page == "🏠 主页":
    show.show_home()
elif st.session_state.current_page == "📊 大纲":
    show.show_text()
elif st.session_state.current_page == "⚙️ 设置":
    show.show_settings()

