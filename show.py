import streamlit as st
from index import index_module
from PIL import Image
from data_base.save_tree import PaperInfoDB
import os,re
import time
import pandas as pd
import pdf_scan.scan_pdf as scan_pdf
# 展示主页
def show_home():
    """显示主页内容"""
    # with st.sidebar:
    #     pages = ["🏠 主页", "📊 大纲", "⚙️ 设置"]
    #     st.session_state.current_page = st.selectbox("导航", pages, index=pages.index(st.session_state.current_page))
        
    st.title("🏠 论文PPT自动生成器")
    st.info("欢迎使用论文PPT自动生成器！")
    
    uploaded_files = st.file_uploader(
        label="请上传PDF文件",
        type=["pdf"],
        accept_multiple_files=True
    )
    st.session_state.ppt_presenter = st.text_input("请输入报告人姓名")
    st.session_state.ppt_date = st.text_input("请输入报告时间")
    
    if uploaded_files:
        for file in uploaded_files:
            if file.type != "application/pdf":
                st.error(f"❌ 文件 {file.name} 类型不支持")
                continue
            st.success(f"✅ 已接收文件: {file.name}")
            st.session_state.pdf_files = uploaded_files
            
    # 连接数据库
    db = PaperInfoDB()
    papers = db.get_all_papers()

    st.header("📚 论文列表")

    if not papers:
        st.info("数据库中没有论文")
        print("no artical")
    else:
        df = pd.DataFrame(papers)
        df["authors"] = df["authors"].apply(lambda x: ", ".join(x))  # 将作者列表转换为字符串

        # 配置交互式表格
        st.dataframe(
            df[["id", "title"]],
            use_container_width=True,
            column_config={
                "id": "ID",
                "title": "论文标题",
            },
            hide_index=True
        )
    st.session_state.papernumber = st.text_input("请选择列表中的论文")
    
    if st.button("点击生成PPT大纲"):
        if not uploaded_files and not st.session_state.papernumber:
            st.error("请上传PDF文件或选择论文列表中的论文!")
        else:
            st.session_state.current_page = "📊 大纲"



def initialize_paper():
    """初始化论文数据结构"""
    db = PaperInfoDB()
    if st.session_state.papernumber:
        paper = db.load_paper(st.session_state.papernumber)
        paper.display_outline()
    else:
        for file in st.session_state.pdf_files:
            # 获取文件的保存路径
            file_path = os.path.join(".", file.name)
            # 将文件保存到当前目录
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
        
            # 定义输出目录
            output_dir = os.path.join("./data_clean/", "output", file.name.split(" ")[0])
            # 创建输出目录（如果不存在）
            os.makedirs(output_dir, exist_ok=True)
            print(file_path)
            print(output_dir)
            # 调用extract_blocks_from_pdf函数
            paper=scan_pdf.extract_paper_info_from_pdf(pdf_path=file_path, output_base_dir=output_dir)
            db.save_paper(paper)
            paper.generate_summary(lang="en")
            db.save_paper(paper)
            paper.display_outline()
    paper.ppt_presenter = st.session_state.ppt_presenter
    paper.ppt_date = st.session_state.ppt_date
    paper.clear_nonexistent()
    return paper

def toggle_expand(node_key):
    """切换节点展开状态"""
    st.session_state.expanded_nodes[node_key] = not st.session_state.expanded_nodes.get(node_key, False)

def render_outline_node(node, depth=0):
    """递归渲染大纲节点"""
    if node.parent is None:
        for child in node.children:
            render_outline_node(child, depth+1)
        return

    node_key = f"node_{'_'.join(n.name for n in node.path)}"
    default_expanded = (depth < 1)  # 默认展开前两层
    
    is_expanded = st.session_state.expanded_nodes.get(node_key, default_expanded)
    
    col1, col2 = st.columns([1, 10],gap="medium")
    with col1:
        if node.children:
            st.button(
                "▶" if not is_expanded else "▼",
                key=f"expand_{node_key}",
                on_click=lambda: toggle_expand(node_key))
    with col2:
        if st.button(
            node.name,
            key=f"select_{node_key}",
            use_container_width=True,
            help="点击查看内容"
        ):
            print(node.name)
            st.session_state.selected_node = node

    if is_expanded and node.children:
        for child in node.children:
            render_outline_node(child, depth+1)
    
    

def show_content_editor():
    """显示内容编辑器"""
    if "selected_node" not in st.session_state or not st.session_state.selected_node:
        st.write("请从左侧选择节点")
        return
    
    node = st.session_state.selected_node
    if not node or not node.content:
        return
    
    # 初始化当前摘要索引
    if "current_summary_index" not in st.session_state:
        st.session_state.current_summary_index = 0
    
    # 获取摘要列表
    summaries = node.content.summary
    if not summaries:  # 处理空摘要的情况
        st.write("该节点暂无摘要内容")
        return
    
    # 确保索引合法
    current_index = st.session_state.current_summary_index
    total_pages = len(summaries)
    if current_index >= total_pages or current_index < 0:
        st.session_state.current_summary_index = 0
        current_index = 0
    
    # 初始化状态变量
    if "show_page_input" not in st.session_state:
        st.session_state.show_page_input = False
        st.session_state.new_page_num = ""
    # 显示翻页控件
    col_prev, col_next, col_add, col_page = st.columns([1, 1, 1, 5])
    with col_prev:
        if st.button("← 上一页", disabled=(current_index == 0)):
            st.session_state.current_summary_index -= 1
            st.rerun()
    with col_next:
        if st.button("下一页 →", disabled=(current_index == total_pages-1)):
            st.session_state.current_summary_index += 1
            st.rerun()
    with col_add:
        if st.button("✨ 更改页数"):
            st.session_state.show_page_input = True
    with col_page:
        st.write(f"📄 第 {current_index+1} 页 / 共 {total_pages} 页")
    
    #更改ppt页数
    if st.session_state.show_page_input:
        new_page_num = st.text_input("请输入页数", value=st.session_state.new_page_num)   
        col_sure, col_cancle = st.columns([1,5])
        # 确认按钮
        with col_sure:
            if st.button("确认修改"):
                st.session_state.new_page_num = new_page_num
                if new_page_num.strip():
                    try:
                        node.content.split_into_parts(int(new_page_num))
                        st.success("页数修改成功！")
                    except ValueError:
                        st.error("请输入有效数字")
                st.session_state.show_page_input = False  # 隐藏输入框
                st.rerun()
        
        # 取消按钮
        with col_cancle:
            if st.button("取消"):
                st.session_state.show_page_input = False
                st.session_state.new_page_num = ""
    
    # 获取当前摘要内容
    current_summary = summaries[current_index]
    current_content = "\n".join(current_summary.key_points) if current_summary.key_points else ""
    
    # 编辑表单
    with st.form(f"content_form_{current_index}"):  # 动态key防止内容残留
        new_content = st.text_area(
            "编辑节点内容",
            value=current_content,
            height=150,
            key=f"editor_{node.name}_{current_index}"
        )
        
        if st.form_submit_button("💾 保存修改"):
            # 更新当前摘要的key_points（按换行分割）
            new_key_points = [kp.strip() for kp in new_content.split("\n") if kp.strip()]
            current_summary.key_points = new_key_points
            st.success("✅ 修改已保存")
    
    # 用户反馈功能（保持原功能）
    with st.expander("📌 向AI提要求"):
        prompt = st.chat_input("请输入您的要求")
        if prompt:
            node.content.user_feedback(prompt, "zh")
            st.rerun()      
    # 在表单外上传图片
    # 处理图片上传和展示

    save_dir = "uploads"
    os.makedirs(save_dir, exist_ok=True)

    # 使用回调函数处理上传逻辑
    def handle_uploaded_files():
        # 获取当前上传器的key
        current_key = st.session_state.get("uploader_key", "initial_uploader")
        
        # 通过动态key获取上传文件
        if uploaded_files := st.session_state.get(current_key):
            for uploaded_file in uploaded_files:
                # 生成唯一文件名（时间戳+原始文件名）
                timestamp = int(time.time()*1000)
                clean_name = re.sub(r"[^\w_.-]", "_", uploaded_file.name)
                file_path = os.path.join(save_dir, f"{timestamp}_{clean_name}")

                # 保存文件内容（添加二进制写入验证）
                try:
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    print(f"成功保存文件到：{file_path}")  # 调试输出
                except Exception as e:
                    st.error(f"文件保存失败：{str(e)}")
                    continue
                
                # 创建新对象（添加number生成保护）
                existing_numbers = [f.number for f in current_summary.figures]
                new_number = max(existing_numbers) + 1 if existing_numbers else 1
                current_summary.figures.append(
                    index_module.TableorFigure(
                        number=new_number,
                        enable=0,
                        path=file_path
                    )
                )
            
            # 通过改变widget key来重置上传器
            st.session_state.uploader_key = f"uploader_{time.time_ns()}"
            print("上传器已重置，新key：", st.session_state.uploader_key)  # 调试输出

    # 创建带唯一key的上传组件
    uploader_key = st.session_state.get("uploader_key", "initial_uploader")
    uploaded_files = st.file_uploader(
        "上传图片", 
        type=["png", "jpg"],
        accept_multiple_files=True,
        key=uploader_key,
        on_change=handle_uploaded_files
    )

    with st.expander("图片展示与选择", expanded=True):
        if not current_summary.figures and not current_summary.tables:
            st.info("暂无已上传图片")
        else:
            # 动态列布局
            num_cols = min(4, len(current_summary.figures + current_summary.tables))
            cols = st.columns(num_cols)
            
            # 遍历所有图片对象
            for idx, fig_obj in enumerate(current_summary.figures + current_summary.tables):
                if(fig_obj.path):
                    with cols[idx % num_cols]:
                        # 图片展示
                        try:
                            img = Image.open(fig_obj.path)
                            st.image(img, caption=f"图 {fig_obj.number}", width=150)
                            
                            # 状态切换（关键修复：使用唯一key）
                            is_active = st.checkbox(
                                f"显示图 {fig_obj.number}",
                                value=fig_obj.enable == 1,
                                key=f"fig_toggle_{fig_obj.number}"  # 基于唯一编号
                            )
                            fig_obj.enable = 1 if is_active else 0
                        
                        except FileNotFoundError:
                            st.error(f"图片文件丢失: {fig_obj.path}")
                            fig_obj.enable = 0  # 自动禁用丢失的图片


def show_text():
    """展示与修改大纲的核心功能"""
    # 初始化数据结构
    if 'paper' not in st.session_state:
        st.session_state.paper = initialize_paper()
    if 'expanded_nodes' not in st.session_state:
        st.session_state.expanded_nodes = {}
    if 'selected_node' not in st.session_state:
        st.session_state.selected_node = None
    
    # 页面布局
    st.set_page_config(layout="wide")
    # 左侧导航栏
    with st.sidebar:
        st.header("论文大纲导航")
        root_node = st.session_state.paper.outline_root
        render_outline_node(root_node)
    
    # 右侧内容区域
    with st.container():
        st.header("内容编辑区域")
        
        show_content_editor()
        db = PaperInfoDB()
        db.save_paper(st.session_state.paper)
        col1, col2 = st.columns([1,5])
        with col1:
            return_home = st.button("返回主页面")
            if(return_home):
                st.session_state.current_page = "🏠 主页"
        with col2:
            generatePPT = st.button("生成 PPT")
            if(generatePPT):
                st.session_state.paper.generate_ppt()
    