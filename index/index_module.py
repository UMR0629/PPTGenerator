############################################

# 还没写完

############################################

# import sys
# #sys.path.append("..")
# from anytree import Node, RenderTree, PreOrderIter
# from extract_function import generate_presentation_summary,generate_with_feedback
# from generate_ppt.generate_ppt import Generate_ppt   #这里先注释掉，因为会报错
# import re

import sys
import os
from itertools import count

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from anytree import Node, RenderTree, PreOrderIter
from index.extract_function import generate_presentation_summary, generate_with_feedback,split_text_into_parts,title_translate_function
from generate_ppt.generate_ppt import Generate_ppt  # 暂时注释掉
import re

class TableorFigure:
    """给summary中的图片或者表格新建一个类，用以存储是否显示和存储路径"""
    def __init__(self,number,enable=0,path=None):
        self.number=number
        self.enable=enable
        self.path=path

class PaperSectionSummary:
    def __init__(
        self,
        #title: str,
        key_points: list[str],
        tables: list[TableorFigure] = None,
        figures: list[TableorFigure] = None
    ):
        #self.title = title
        self.key_points = key_points
        self.tables = tables if tables is not None else []
        self.figures = figures if figures is not None else []

    @property
    def key_point_count(self) -> int:
        """自动计算要点数量"""
        return len(self.key_points)

    def add_table(self, table_num: int) -> None:
        """添加关联表格"""
        if not any(table.number == table_num for table in self.tables):
            # 创建新的表格对象（默认enable=0，path=None）
            new_table = TableorFigure(number=table_num)
            self.tables.append(new_table)

    def add_figure(self, figure_num: int) -> None:
        """添加关联图片""" 
        if not any(figure.number == figure_num for figure in self.figures):
            new_figure = TableorFigure(number=figure_num)
            self.figures.append(new_figure)
    
    def insert_figure(self,path:str) ->None:
        """用户自己选择插入图片"""
        num=100+len(self.figures)
        new_figure=TableorFigure(number=num,enable=1,path=str)
        self.figures.append(new_figure)


    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            #"section_number": self.section_number,
            #"title": self.title,
            "key_points": self.key_points,
            "tables": sorted(self.tables),
            "figures": sorted(self.figures),
            "key_point_count": self.key_point_count
        }

    def __str__(self) -> str:
        """友好字符串表示"""
        return (
            #f"Section {self.section_number}: {self.title}\n"
            f"Key Points ({self.key_point_count}):\n - " + "\n - ".join(self.key_points) + "\n"
            f"Tables: {self.tables}\n"
            f"Figures: {self.figures}"
        )


    
class SectionContent:
    """
    论文大纲叶子节点的内容类。
    存储具体文本内容，并且指向summary部分，以获取大模型处理后的要点、关联图像和表格。
    """

    def __init__(self, text=None,summary:list[PaperSectionSummary]=None):
        # 原始text（来自pdf处理模块）
        self.text = text or ""
        # summary中应当包含大模型处理过后的text要点、img路径、table路径（来自大模型处理模块）
        self.summary=summary if summary is not None else []

    def add_summary(self, summary: PaperSectionSummary):
        """添加单个summary到列表中"""
        self.summary.append(summary)    

    def __repr__(self):
        return f"SectionContent(text={self.text[:30]}...)"
    
    def content_extract(self,lang:str="zh"):     #对每个叶子结点遍历调用，使用大模型提取信息
        tmp_summary=PaperSectionSummary(key_points=[])
        api_output=generate_presentation_summary(self.text,lang)
        parse_output_to_section(api_output, tmp_summary)
        self.summary.append(tmp_summary)

    def user_feedback(self,feedback,lang:str="zh",index=0):   #在用户对大模型有反馈信息时调用
        api_output=generate_with_feedback(self.text,feedback,lang)
        self.summary[index].key_points.clear()
        self.summary[index].key_points.append(api_output)
    
    def split_into_parts(self,num:int=2,lang:str="zh"):  #用户可以选择一部分，多做几页PPT，从这里进行切割和重新赋值
        result=split_text_into_parts(self.text,num)
        parts = result.split("\n---\n")
        tmp_summary=PaperSectionSummary(key_points=[])
        output = generate_presentation_summary(parts[0],lang)
        parse_output_to_section(output, tmp_summary)
        self.summary[0].key_points=tmp_summary.key_points
        for i in range(1, len(parts)):
            tmp_summary2=PaperSectionSummary(key_points=[],tables=self.summary[0].tables,figures=self.summary[0].figures)
            self.summary.append(tmp_summary2)
            tmp_summary3=PaperSectionSummary(key_points=[])
            output = generate_presentation_summary(parts[i],lang)
            parse_output_to_section(output, tmp_summary3)
            self.summary[i].key_points=tmp_summary3.key_points



# 存储论文信息及其大纲的具体信息
class PaperInfo:
    """
    用于存储论文信息及其大纲的类。
    论文大纲使用多叉树结构，每个节点表示论文的一部分，
    叶子节点可以存储该部分的具体内容。
    """

    def __init__(self, title, authors, date, journal, ppt_presenter, ppt_date):
        """
        初始化论文信息。
        :param title: 论文标题
        :param authors: 作者列表
        :param date: 论文发表日期
        :param journal: 发表期刊名称
        :param ppt_presenter: PPT 讲述者
        :param ppt_date: PPT 讲述日期
        """
        self.title = title
        self.authors = authors
        self.date = date
        self.journal = journal
        self.ppt_presenter = ppt_presenter
        self.ppt_date = ppt_date
        # 根节点使用论文标题（而非目录名）
        self.outline_root = Node(title, content=None)  # 临时占位，实际内容在后续填充
        # “名称-路径”对应表（来自pdf处理模块）
        self.image_list = []

    def add_outline_section(self, parent_title, section_title):
        """
        在指定的父节点下添加新的大纲部分。
        :param parent_title: 父节点的标题
        :param section_title: 新增部分的标题
        :return: 是否添加成功（True/False）
        """
        parent_node = self.find_outline_section(parent_title)
        if parent_node:
            Node(section_title, parent=parent_node, content=None)  # 默认无内容
            return True
        return False

    def add_content_to_leaf(self, section_title, content):
        """
        向指定的叶子节点添加具体内容。
        :param section_title: 叶子节点的标题
        :param content: 需要存储的内容（可以是 SectionContent 实例）
        :return: 是否添加成功（True/False）
        """
        node = self.find_outline_section(section_title)
        if node and not node.children:  # 仅允许叶子节点存储内容
            if isinstance(content, SectionContent):
                node.content = content
            else:
                node.content = SectionContent(text=str(content))  # 兼容直接传入文本的情况
            return True
        return False  # 失败原因：节点不存在或不是叶子节点

    def remove_outline_section(self, section_title):
        """
        删除指定的大纲部分。
        :param section_title: 需要删除的部分的标题
        :return: 是否删除成功（True/False）
        """
        node = self.find_outline_section(section_title)
        if node and node.parent:
            node.parent.children = tuple(child for child in node.parent.children if child != node)
            return True
        return False

    def find_outline_section(self, section_title):
        """
        在大纲树中查找指定的部分。
        :param section_title: 需要查找的部分标题
        :return: 找到的节点（如果存在），否则返回 None
        """
        for node in PreOrderIter(self.outline_root):
            if node.name == section_title:
                return node
        return None

    def find_children_of_section(self, section_title):
        """
        查找某个大纲部分的所有子节点。
        :param section_title: 需要查找子节点的部分标题
        :return: 子节点列表（如果存在），否则返回 None
        """
        node = self.find_outline_section(section_title)
        return list(node.children) if node else None

    def find_parent_of_section(self, section_title):
        """
        查找某个大纲部分的父节点。
        :param section_title: 需要查找父节点的部分标题
        :return: 父节点（如果存在），否则返回 None
        """
        node = self.find_outline_section(section_title)
        return node.parent if node else None

    def update_outline_section(self, section_title, new_title):
        """
        更新某个大纲部分的标题。
        :param section_title: 需要修改的部分标题
        :param new_title: 新的标题
        :return: 是否更新成功（True/False）
        """
        node = self.find_outline_section(section_title)
        if node:
            node.name = new_title
            return True
        return False

    # def display_outline(self):
    #     """
    #     以层次结构打印论文大纲，并显示叶子节点的内容。
    #     """
    #     for pre, _, node in RenderTree(self.outline_root):
    #         content_info = f" (Content: {node.content})" if node.content else ""
    #         print(f"{pre}{node.name}{content_info}")
    def display_outline(self):
        """显示大纲和图片信息"""
        # 1. 显示章节结构
        for pre, _, node in RenderTree(self.outline_root):
            content_info = f" (Content: {node.content})" if node.content else ""
            print(f"{pre}{node.name}{content_info}")
        
        # 2. 显示图片信息
        if hasattr(self, 'image_list') and self.image_list:
            print("\n=== 图片列表 ===")
            for img_info in self.image_list:
                print(f"{img_info['number']}:")
                print(f"  路径: {img_info['path']}")
                print(f"  描述: {img_info['description'][:100]}...")  # 显示前100字符
        else:
            print("\n未找到任何图片文件")

    def traverse_outline(self):
        """
        以前序遍历方式获取大纲结构。
        :return: 包含 (节点名称, 内容) 的列表
        """
        return [(node.name, node.content) for node in PreOrderIter(self.outline_root)]

    def find_root_children(self):
        """
        查找所有根目录（Paper Outline）的直接子节点名称，并按照顺序返回列表。
        :return: 根节点的子节点名称列表
        """
        return [child.name for child in self.outline_root.children]

    def dfs_recursive_with_depth(self, node=None, depth=0, result=None):
        """
        递归进行深度优先遍历（DFS），记录节点名称和深度。
        :param node: 当前遍历的节点（默认从根节点开始）
        :param depth: 当前节点的深度
        :param result: 递归存储遍历结果的列表
        :return: 包含 (节点名称, 深度) 的列表
        """
        if result is None:
            result = []
        if node is None:
            node = self.outline_root  # 默认从根节点开始

        # 记录当前节点的名称和深度
        result.append((node.name, depth))

        # 遍历子节点，深度 +1
        for child in node.children:
            self.dfs_recursive_with_depth(child, depth + 1, result)

        return result

    def find_image_addr(self, img_num):
        """
        查找图片的地址
        """
        for img in self.image_list:
            if img['number'] == f"Figure{img_num}":
                return img['path']
            if img['number'] == f"FIGURE{img_num}":
                return img['path']
        return None

    def find_table_addr(self, table_num):
        """
        查找表格的地址
        """
        for img in self.image_list:
            if img['number'] == f"Table{table_num}":
                return img['path']
            if img['number'] == f"TABLE{table_num}":
                return img['path']
        return None

    def generate_ppt(self):
        """
        生成ppt
        """
        ppt_path = "../source/ppt_model/1.百廿红-李一.pptx"
        generate_ppt = Generate_ppt(ppt_path)
        author_text = ""
        for author in self.ppt_presenter:
            author_text += author + " "
        # 增加标题页
        generate_ppt.add_cover(self.title, author_text, self.ppt_date)

        index_content = self.find_root_children()
        index_num = len(index_content)

        # 增加目录页
        generate_ppt.add_menu("../source/img/image22.jpg", index_num, index_content)
        main_title_count = 0

        # 遍历树，添加正文内容
        node_list = self.dfs_recursive_with_depth()
        for node in node_list:
            title = node[0]
            depth = node[1]
            content_node = self.find_outline_section(title)
            # 添加大标题页
            if depth == 1:
                main_title_count += 1
                title = generate_ppt.process_title(title)
                generate_ppt.add_main_title(title,str(main_title_count))
            # 添加正文页
            if content_node.content is not None:
                # 每个summary_content为用户指定的一页ppt
                for summary_content in content_node.content.summary:
                    tables_all = summary_content.tables
                    figures_all = summary_content.figures
                    tables = []
                    figures = []
                    table_num = 0
                    figure_num = 0
                    for table in tables_all:
                        if table.enable == 1:
                            tables.append(table)
                            table_num += 1
                    for figure in figures_all:
                        if figure.enable == 1:
                            figures.append(figure)
                            figure_num += 1
                    img_num = table_num + figure_num
                    #print("generate_ppt",title,img_num)
                    # 根据不同的图片数量和文字长度，选择合适的模板
                    # 如果为纯文字
                    if img_num == 0:
                        text_combined = ""
                        for point in summary_content.key_points:
                            text_combined  += (point + "\n")
                        generate_ppt.add_all_text(title,text_combined)
                    # 一张图片+文字
                    if img_num == 1:
                        text_combined = ""
                        for point in summary_content.key_points:
                            text_combined  += (point + "\n")
                        if len(tables) == 1:
                            #table_path = self.find_table_addr(tables[0])
                            table_path = tables[0].path
                            generate_ppt.add_text_image(title,text_combined,table_path)
                        elif len(figures) == 1:
                            #figure_path = self.find_image_addr(figures[0])
                            figure_path = figures[0].path
                            generate_ppt.add_text_image(title,text_combined,figure_path)
                    # 两张图片+文字
                    if img_num == 2:
                        text_combined = ""
                        for point in summary_content.key_points:
                            text_combined  += (point + "\n")
                        # 如果文字很长，自动拆分为2图ppt+纯文字ppt
                        if len(text_combined) < 200:
                            if len(tables) == 2:
                                # table_path1 = self.find_table_addr(tables[0])
                                # table_path2 = self.find_table_addr(tables[1])
                                table_path1 = tables[0].path
                                table_path2 = tables[1].path
                                generate_ppt.add_text_double_image(title,text_combined,table_path1,table_path2)
                            elif len(figures) == 2:
                                # figure_path1 = self.find_image_addr(figures[0])
                                # figure_path2 = self.find_image_addr(figures[1])
                                figure_path1 = figures[0].path
                                figure_path2 = figures[1].path
                                generate_ppt.add_text_double_image(title,text_combined,figure_path1,figure_path2)
                            elif len(tables) == 1 and len(figures) == 1:
                                # table_path = self.find_table_addr(tables[0])
                                # figure_path = self.find_image_addr(figures[0])
                                table_path = tables[0].path
                                figure_path = figures[0].path
                                generate_ppt.add_text_double_image(title,text_combined,table_path,figure_path)
                        else:
                            if len(tables) == 2:
                                # table_path1 = self.find_table_addr(tables[0])
                                # table_path2 = self.find_table_addr(tables[1])
                                table_path1 = tables[0].path
                                table_path2 = tables[1].path
                                generate_ppt.add_double_image(title,table_path1,table_path2)
                                generate_ppt.add_all_text(title,text_combined)
                            elif len(figures) == 2:
                                # figure_path1 = self.find_image_addr(figures[0])
                                # figure_path2 = self.find_image_addr(figures[1])
                                figure_path1 = figures[0].path
                                figure_path2 = figures[1].path
                                generate_ppt.add_double_image(title,figure_path1,figure_path2)
                                generate_ppt.add_all_text(title,text_combined)
                            elif len(tables) == 1 and len(figures) == 1:
                                # table_path = self.find_table_addr(tables[0])
                                # figure_path = self.find_image_addr(figures[0])
                                table_path = tables[0].path
                                figure_path = figures[0].path
                                generate_ppt.add_double_image(title,table_path,figure_path)
                                generate_ppt.add_all_text(title,text_combined)
                    # 三图+文字（自动拆分为2图ppt+1图1文ppt）
                    if img_num == 3:
                        text_combined = ""
                        for point in summary_content.key_points:
                            text_combined  += (point + "\n")
                        if len(figures) == 0:
                            table_path1 = tables[0].path
                            table_path2 = tables[1].path
                            table_path3 = tables[2].path
                            generate_ppt.add_double_image(title, table_path1, table_path2)
                            generate_ppt.add_text_image(title, text_combined, table_path3)
                        elif len(figures) == 1:
                            figure_path = figures[0].path
                            table_path1 = tables[0].path
                            table_path2 = tables[1].path
                            generate_ppt.add_double_image(title, table_path1, table_path2)
                            generate_ppt.add_text_image(title, text_combined, figure_path)
                        elif len(figures) == 2:
                            figure_path1 = figures[0].path
                            figure_path2 = figures[1].path
                            table_path = tables[0].path
                            generate_ppt.add_double_image(title, figure_path1, figure_path2)
                            generate_ppt.add_text_image(title, text_combined, table_path)
                        else:
                            figure_path1 = figures[0].path
                            figure_path2 = figures[1].path
                            figure_path3 = figures[2].path
                            generate_ppt.add_double_image(title, figure_path1, figure_path2)
                            generate_ppt.add_text_image(title, text_combined, figure_path3)

        generate_ppt.add_thanks()
        title_first_part = self.title.split(' ')[0]
        title = re.sub(r'[^\w]', '', title_first_part).lower()
        print(title)
        ppt_presenter_first_part = self.ppt_presenter.split(' ')[0]
        ppt_presenter = re.sub(r'[^\w]', '', ppt_presenter_first_part).lower()
        print(ppt_presenter)
        ppt_save_path = "../source/ppt_model/" + title + "_" + ppt_presenter + ".pptx"
        #ppt_save_path = "source/ppt_model/output.pptx"
        generate_ppt.save_ppt(ppt_save_path)

    def generate_summary(self,lang:str="zh"):
        for node in PreOrderIter(self.outline_root):
            if isinstance(node.content, SectionContent):
                print("正在翻译标题")
                if(lang=="zh"):
                    tmp=title_translate_function(node.name)
                    node.name=tmp
                print(f"正在提取{node.name}要点")
                node.content.content_extract()
                print(f"{node.name}提取完成")
        for node in PreOrderIter(self.outline_root):
            if isinstance(node.content, SectionContent):
                print(f"正在提取{node.name}中的图片信息")
                for figure in node.content.summary[0].figures:
                    figure_path=self.find_image_addr(figure.number)
                    if figure_path is not None:
                        figure.path = figure_path
                    else:
                        node.content.summary[0].figures.remove(figure)
                for table in node.content.summary[0].tables:
                    table_path=self.find_table_addr(table.number)
                    if table_path is not None:
                        table.path = table_path
                    else:
                        node.content.summary[0].tables.remove(table)
                print("提取完成")

    def clear_nonexistent(self):
        """
        清除不存在的图片和表格
        """
        for node in PreOrderIter(self.outline_root):
            if isinstance(node.content, SectionContent):
                for summary_item in node.content.summary:
                    # 清除不存在的图片
                    for figure in summary_item.figures:
                        figure_path = figure.path
                        if figure_path is None:
                            summary_item.figures.remove(figure)
                    # 清除不存在的表格
                    for table in summary_item.tables:
                        table_path = table.path
                        if table_path is None:
                            summary_item.tables.remove(table)

def parse_output_to_section(output: str, section: PaperSectionSummary) -> None:
    """
    从特定格式输出中提取信息并填充PaperSectionSummary实例
    
    输入格式示例：
    3
    [2,3]
    []
    输入开销类型与实证分析
    ◆ 要点1...
    ◆ 要点2...
    ◆ 要点3...
    Usage: ...
    
    :param output: 程序输出字符串
    :param section: 需要填充的PaperSectionSummary实例
    """
    # 预处理输出内容
    lines = [
        line.strip() 
        for line in output.split('\n') 
        if line.strip() and not line.strip().startswith('None')
    ]
    
    # 解析表格和图片编号
    array_pattern = re.compile(r'^\[([\d,\s]*)\]$')
    parsed_arrays = []
    
    for line in lines:
        if match := array_pattern.match(line):
            numbers = [int(n) for n in match.group(1).split(',') if n.strip()]
            parsed_arrays.append(numbers)
            if len(parsed_arrays) == 2:
                break
    
    # 设置表格和图片（确保容错）
    section.tables = [TableorFigure(number=num) for num in parsed_arrays[0]] if len(parsed_arrays) >= 1 else []
    section.figures = [TableorFigure(number=num) for num in parsed_arrays[1]] if len(parsed_arrays) >= 2 else []
    
    # 提取标题（第一个非数组行）
    title_line = None
    for line in lines:
        if not array_pattern.match(line) and not line.isdigit():
            title_line = line
            break
    
    if title_line:
        section.title = title_line
    
    # 提取要点内容（◆开头的行）
    section.key_points = [
        line.strip("◆ ").strip()
        for line in lines
        if line.startswith('◆')
    ]
    
    # # 自动处理关联关系（示例中的图引用）
    # figure_refs = set()
    # for point in section.key_points:
    #     if matches := re.findall(r'图(\d+)', point):
    #         figure_refs.update(int(m) for m in matches)
    # section.figures = list(set(section.figures) | figure_refs)