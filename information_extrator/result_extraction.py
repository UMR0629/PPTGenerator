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
        """
        论文要点存储类
        
        :param section_number: 章节编号 (e.g. 4.1 -> 传入41)
        :param title: 章节标题
        :param key_points: 提取的要点文本列表
        :param tables: 涉及的表格编号列表
        :param figures: 涉及的图片编号列表
        """
        self.section_number = section_number
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
    if len(parsed_arrays) >= 1:
        section.tables = parsed_arrays[0]
    if len(parsed_arrays) >= 2:
        section.figures = parsed_arrays[1]
    
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
    
    # 自动处理关联关系（示例中的图引用）
    figure_refs = set()
    for point in section.key_points:
        if matches := re.findall(r'图(\d+)', point):
            figure_refs.update(int(m) for m in matches)
    section.figures = list(set(section.figures) | figure_refs)

section = PaperSectionSummary(
    section_number=41,  # 假设章节号已设置
    title="",
    key_points=[]
)

output_text = '''
NoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNoneNone3  
[2,3]  
[]  
输入开销类型与实证分析  
◆ 定义两种输入开销类型：完全开销（无相关位）与部分开销（部分位影响固件逻辑）。完全开销导致模糊器资源浪费，因需猜测无效位值（如示例1中HAS_DATA值）。  
◆ 示例1（见图2）：串口读取函数引入92%部分开销，因MMIO需读取4字节但仅使用1字节，且需多次猜测特定状态值，导致输入空间利用率极低。  
◆ 示例2（见图3）：硬件控制流分支引入94%-97%部分开销，因32位MMIO输入中仅需1-2位有效（如操作类型判断），其余冗余位被掩码丢弃。Usage: CompletionUsage(completion_tokens=1092, prompt_tokens=1734, total_tokens=2826, completion_tokens_details=None, prompt_tokens_details=None)
'''

parse_output_to_section(output_text, section)
print(section)