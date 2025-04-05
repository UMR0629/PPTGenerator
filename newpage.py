import streamlit as st
import show 



# 初始化状态
if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 主页"

# 导航栏

if st.session_state.current_page == "🏠 主页":
    show.show_home()
elif st.session_state.current_page == "📊 大纲":
    show.show_text()


