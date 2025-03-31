############################################

# 还没写完

############################################

import sys
#sys.path.append("..")
from anytree import Node, RenderTree, PreOrderIter
from result_extraction import parse_output_to_section 
from extract_function import generate_presentation_summary,generate_with_feedback
import re

class PaperSectionSummary:
    def __init__(
        self,
        section_number: int,
        title: str,
        key_points: list[str],
        tables: list[int] = None,
        figures: list[int] = None
    ):
        #self.section_number = section_number
        self.title = title
        self.key_points = key_points
        self.tables = tables if tables is not None else []
        self.figures = figures if figures is not None else []

    @property
    def key_point_count(self) -> int:
        """自动计算要点数量"""
        return len(self.key_points)

    def add_table(self, table_num: int) -> None:
        """添加关联表格"""
        if table_num not in self.tables:
            self.tables.append(table_num)

    def add_figure(self, figure_num: int) -> None:
        """添加关联图片""" 
        if figure_num not in self.figures:
            self.figures.append(figure_num)

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "section_number": self.section_number,
            "title": self.title,
            "key_points": self.key_points,
            "tables": sorted(self.tables),
            "figures": sorted(self.figures),
            "key_point_count": self.key_point_count
        }

    def __str__(self) -> str:
        """友好字符串表示"""
        return (
            f"Section {self.section_number}: {self.title}\n"
            f"Key Points ({self.key_point_count}):\n - " + "\n - ".join(self.key_points) + "\n"
            f"Tables: {self.tables}\n"
            f"Figures: {self.figures}"
        )

class SectionContent:
    """
    论文大纲叶子节点的内容类。
    可以存储具体文本内容、引用、公式等信息。
    """

    def __init__(self, text=None, references=None, equations=None,summary:PaperSectionSummary=None):

        self.text = text or ""
        self.references = references or []
        self.equations = equations or []
        self.summary=summary
        

    def __repr__(self):
        return f"SectionContent(text={self.text[:30]}..., references={len(self.references)}, equations={len(self.equations)})"
    
    def content_extract(self,title,lang:str="zh"):
        self.summary=PaperSectionSummary(title=title)
        api_output=generate_presentation_summary(self.content,lang)
        parse_output_to_section(api_output, self.summary)

    def user_feedback(self,feedback,lang:str="zh"):
        api_output=generate_with_feedback(feedback,lang)
        self.summary=api_output


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
        self.outline_root = Node("Paper Outline", content=None)  # 根节点不存储内容

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

    def display_outline(self):
        """
        以层次结构打印论文大纲，并显示叶子节点的内容。
        """
        for pre, _, node in RenderTree(self.outline_root):
            content_info = f" (Content: {node.content})" if node.content else ""
            print(f"{pre}{node.name}{content_info}")

    def traverse_outline(self):
        """
        以前序遍历方式获取大纲结构。
        :return: 包含 (节点名称, 内容) 的列表
        """
        return [(node.name, node.content) for node in PreOrderIter(self.outline_root)]
