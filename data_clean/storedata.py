import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from index.index import PaperInfo, SectionContent
from anytree import Node, PreOrderIter

def collect_images(paper_info, output_picture0_dir):
    """精确收集图片文件（修复路径问题）"""
    paper_info.image_list = []
    paper_info.image_descriptions = {}
    
    if not os.path.exists(output_picture0_dir):
        print(f"警告：图片目录不存在 {os.path.abspath(output_picture0_dir)}")
        return

    print(f"\n正在扫描图片目录：{os.path.abspath(output_picture0_dir)}")
    print("目录内容：", os.listdir(output_picture0_dir))

    # 遍历所有子目录（如Figure1/, Table1/等）
    for item in os.listdir(output_picture0_dir):
        item_path = os.path.join(output_picture0_dir, item)
        if os.path.isdir(item_path):
            print(f"\n扫描子目录：{item}")
            # 在子目录中查找png和txt文件
            png_files = [f for f in os.listdir(item_path) if f.lower().endswith('.png')]
            txt_files = [f for f in os.listdir(item_path) if f.lower().endswith('.txt')]
            
            print(f"找到PNG文件：{png_files}")
            print(f"找到TXT文件：{txt_files}")

            # 处理找到的PNG文件
            for png_file in png_files:
                img_num = os.path.splitext(png_file)[0]  # 提取Figure1/Table1等名称
                img_path = os.path.join(item_path, png_file)
                
                # 查找对应的描述文件（支持两种命名方式）
                possible_txt_names = [
                    f"{img_num}.txt",          # Figure1.txt
                    f"{item}.txt",             # Figure1/Figure1.txt
                    "description.txt"          # Figure1/description.txt
                ]
                
                description = ""
                for txt_name in possible_txt_names:
                    txt_path = os.path.join(item_path, txt_name)
                    if os.path.exists(txt_path):
                        with open(txt_path, 'r', encoding='utf-8') as f:
                            description = f.read().strip()
                        break
                
                # 存储信息
                paper_info.image_list.append({
                    'number': img_num,
                    'path': img_path,
                    'description': description
                })
                print(f"已登记图片：{img_num} (路径: {img_path})")

    # 按图片编号排序
    paper_info.image_list.sort(key=lambda x: (
        int(''.join(filter(str.isdigit, x['number']))) if any(c.isdigit() for c in x['number']) else float('inf'),
        x['number']
    ))
    print(f"\n共找到 {len(paper_info.image_list)} 张图片")

def store_paper_data(output5_dir, output_picture0_dir):
    """主函数（带完整路径检查）"""
    # 转换为绝对路径
    output5_dir = os.path.abspath(output5_dir)
    output_picture0_dir = os.path.abspath(output_picture0_dir)
    
    print(f"论文文本目录：{output5_dir}")
    print(f"图片资源目录：{output_picture0_dir}")
    
    paper_info = initialize_paper_info(output5_dir)
    build_outline_structure(paper_info, output5_dir)
    add_content_to_sections(paper_info, output5_dir)
    collect_images(paper_info, output_picture0_dir)
    return paper_info
def initialize_paper_info(output5_dir):
    """从title.txt获取论文标题，并初始化PaperInfo"""
    # 1. 获取论文标题
    title_file = os.path.join(output5_dir, "文章标题", "title.txt")
    if os.path.exists(title_file):
        with open(title_file, 'r', encoding='utf-8') as f:
            paper_title = f.read().strip()
    else:
        paper_title = "Untitled Paper"  # 默认标题

    # 2. 初始化PaperInfo
    ppt_date = datetime.now().strftime("%Y-%m-%d")
    paper_info = PaperInfo(
        title=paper_title,
        authors=["待补充"],
        date="待补充",
        journal="待补充",
        ppt_presenter="汇报人",
        ppt_date=ppt_date
    )
    # 3. 添加摘要内容（来自merged_text.txt）
    abstract_file = os.path.join(output5_dir, "文章标题", "merged_text.txt")
    if os.path.exists(abstract_file):
        with open(abstract_file, 'r', encoding='utf-8') as f:
            abstract_content = SectionContent(text=f.read())
        paper_info.outline_root.name = paper_title  # 更新根节点名称
        paper_info.outline_root.content = abstract_content
    
    return paper_info

def build_outline_structure(paper_info, output5_dir):
    """构建大纲结构，正确处理数字章节和附录"""
    chapters = []
    for entry in os.listdir(output5_dir):
        if entry == "文章标题":  # 跳过标题目录
            continue
        if os.path.isdir(os.path.join(output5_dir, entry)):
            chapters.append(entry)
    
    # 改进的排序逻辑：数字章节在前，附录在后
    chapters.sort(key=lambda x: (
        float(x.split('.')[0]) if x[0].isdigit() else float('inf'),  # 数字章节按数字排序
        x  # 附录按字母排序
    ))
    
    for chapter in chapters:
        chapter_path = os.path.join(output5_dir, chapter)
        _add_chapter_recursive(paper_info.outline_root, chapter_path)

def _add_chapter_recursive(parent_node, current_path):
    """递归添加章节和子章节"""
    chapter_name = os.path.basename(current_path)
    current_node = Node(chapter_name, parent=parent_node, content=None)
    
    # 添加内容
    content_file = os.path.join(current_path, "merged_text.txt")
    if os.path.exists(content_file):
        with open(content_file, 'r', encoding='utf-8') as f:
            current_node.content = SectionContent(text=f.read())
    
    # 处理子章节
    subchapters = []
    for entry in os.listdir(current_path):
        entry_path = os.path.join(current_path, entry)
        if os.path.isdir(entry_path):
            subchapters.append(entry)
    
    # 子章节排序逻辑
    subchapters.sort(key=lambda x: (
        float(x.split('.')[1]) if '.' in x and x.split('.')[1].isdigit() else float('inf'),
        x
    ))
    
    for subchapter in subchapters:
        _add_chapter_recursive(current_node, os.path.join(current_path, subchapter))
def add_content_to_sections(paper_info, output5_dir):
    """添加内容到章节"""
    for node in PreOrderIter(paper_info.outline_root):
        if not node.children:
            path_parts = []
            current = node
            while current.parent:
                path_parts.insert(0, current.name)
                current = current.parent
                
            content_file = os.path.join(output5_dir, *path_parts, "merged_text.txt")
            if os.path.exists(content_file):
                with open(content_file, 'r', encoding='utf-8') as f:
                    node.content = SectionContent(text=f.read())


if __name__ == "__main__":
    # 使用相对路径时自动转换为基于脚本位置的绝对路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output5_dir = os.path.join(base_dir, "output5")
    output_picture0_dir = os.path.join(base_dir, "output_picture0")
    
    paper_info = store_paper_data(output5_dir, output_picture0_dir)
    paper_info.display_outline()