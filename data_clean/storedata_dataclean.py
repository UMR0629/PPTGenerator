import os
import re
from pathlib import Path
import shutil

def is_title(text):
    """判断文本是否是标题，并提取标题内容"""
    first_line = text.strip().split('\n')[0]  # 获取第一行
    # 检查第一行是否以数字开头
    if first_line[0].isdigit():
        # 找到第一个非数字字符
        first_non_digit_index = None
        for i, char in enumerate(first_line):
            if not char.isdigit() and char not in ['.', '。']:
                first_non_digit_index = i
                break
        
        if first_non_digit_index is not None:
            # 从第一个非数字字符开始查找句号
            for j in range(first_non_digit_index, len(first_line)):
                if first_line[j] in ['.', '。']:
                    title_content = first_line[:j + 1]  # 包括句号
                    return True, title_content  # 返回标题内容
    return False, None

def process_group(group_dir, output_dir, next_group_index):
    """处理单个group文件夹"""
    print(f"处理组: {group_dir}")
    
    # 创建初始输出组
    current_output_group = output_dir / f"group_{next_group_index}"
    current_output_group.mkdir(parents=True, exist_ok=True)
    print(f"  创建输出组: {current_output_group}")
    
    # 复制标题文本文件
    for item in group_dir.iterdir():
        if item.is_file() and (item.name in ['00_title.txt']):
            shutil.copy2(item, current_output_group / item.name)
            print(f"    复制文件: {item.name} 到 {current_output_group}")
    
    # 获取所有普通文本文件并按数字排序
    text_files = sorted(
        [f for f in group_dir.glob('*_text.txt') if f.name not in ['00_title.txt']],
        key=lambda x: int(x.stem.split('_')[0])
    )
    
    i = 0
    while i < len(text_files):
        text_file = text_files[i]
        with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        is_title_result, title_content = is_title(content)
        if is_title_result:
            print(f"    发现标题: {title_content}")
            # 创建新组
            next_group_index += 1
            current_output_group = output_dir / f"group_{next_group_index}"
            current_output_group.mkdir(exist_ok=True)
            print(f"    创建新组: {current_output_group}")
            
            # 将标题存储为新组的00_title.txt
            with open(current_output_group / '00_title.txt', 'w', encoding='utf-8') as f:
                f.write(title_content)
            
            # 将标题之后的内容存储为新组的00_text.txt
            remaining_content = content[len(title_content):].strip()
            if remaining_content:
                with open(current_output_group / '00_text.txt', 'w', encoding='utf-8') as f:
                    f.write(remaining_content)
        else:
            # 不包含标题，将该文件复制到当前组
            output_text_file = current_output_group / text_file.name
            shutil.copy2(text_file, output_text_file)
            print(f"    复制普通文本文件: {text_file.name} 到 {current_output_group}")
        
        i += 1  # 处理下一个文件
    
    return next_group_index + 1  # 返回下一个可用的group索引
def process_page(page_dir, output_dir, page_index):
    """处理单个page文件夹"""
    print(f"\n处理页面: {page_dir}")
    # 创建输出page目录
    output_page_dir = output_dir / f"page_{page_index}"
    output_page_dir.mkdir(exist_ok=True)
    print(f"创建输出页面: {output_page_dir}")
    
    # 获取当前页面的第一个group的索引
    first_group = sorted(page_dir.glob('group_*'), key=lambda x: int(x.stem.split('_')[1]))
    if first_group:
        next_group_index = int(first_group[0].stem.split('_')[1])  # 从第一个group的索引开始
    else:
        next_group_index = 0  # 如果没有group，从0开始
    
    # 按group编号排序处理
    for group_dir in sorted(page_dir.glob('group_*'), key=lambda x: int(x.stem.split('_')[1])):
        if group_dir.is_dir():
            print(f"\n处理输入组: {group_dir}")
            next_group_index = process_group(group_dir, output_page_dir, next_group_index)

def main():
    # 定义输入输出路径
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / 'generate_ppt' / 'output2'
    output0_dir = base_dir / 'generate_ppt' / 'output0'
    
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output0_dir}")
    
    # 清空或创建输出目录
    if output0_dir.exists():
        for item in output0_dir.glob('*'):
            if item.is_file():
                item.unlink()
            else:
                shutil.rmtree(item)
    output0_dir.mkdir(exist_ok=True)
    print(f"清空或创建输出目录: {output0_dir}")
    
    # 处理每个页面（按page编号排序）
    page_dirs = sorted(input_dir.glob('page_*'), key=lambda x: int(x.stem.split('_')[1]))
    for page_index, page_dir in enumerate(page_dirs, start=1):
        if page_dir.is_dir():
            process_page(page_dir, output0_dir, page_index)

if __name__ == '__main__':
    main()