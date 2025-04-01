import os
import re
from pathlib import Path
from difflib import SequenceMatcher
import shutil

def is_special_text(text):
    """判断是否是特殊文本（图片说明或列表标题）"""
    text = text.strip()
    return (text.startswith("Figure ") or 
            text.startswith("Listing ") or
            text.startswith("Table ") or
            re.match(r'^(Figure|Listing|Table)\s+\d+[:.]?\s*', text))

def clean_text(text):
    """清理文本中的特殊字符和多余空格"""
    text = re.sub(r'[\u4e00-\u9fff]', '', text)  # 移除中文字符
    text = re.sub(r'[^\w\s.,;:\-\[\](){}<>@\'"*/_=+&#%$!?]', '', text)  # 保留基本标点
    text = re.sub(r'\s+', ' ', text).strip()  # 合并多余空格
    return text

def find_overlap(a, b, min_overlap=20):
    """找到两个文本之间的重叠部分"""
    a_clean = clean_text(a)
    b_clean = clean_text(b)
    
    match = SequenceMatcher(None, a_clean, b_clean).find_longest_match(
        0, len(a_clean), 0, len(b_clean))
    
    if match.size >= min_overlap:
        return a[match.a: match.a + match.size]
    return ""

def process_group(group_dir, output_dir):
    """处理单个group文件夹"""
    print(f"处理组: {group_dir}")
    # 获取所有text文件并按数字排序
    text_files = sorted(
        [f for f in group_dir.glob('*_text.txt')],
        key=lambda x: int(x.stem.split('_')[0])
    )
    
    if not text_files:
        print(f"  跳过空组: {group_dir}")
        return
    
    # 创建输出目录结构
    rel_path = group_dir.relative_to(group_dir.parent.parent)
    output_group_dir = output_dir / rel_path
    output_group_dir.mkdir(parents=True, exist_ok=True)
    
    # 分离特殊文本和普通文本
    special_texts = []
    normal_texts = []
    special_text_indices = set()  # 记录特殊文本的索引
    
    for i, text_file in enumerate(text_files):
        with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if is_special_text(content):
                special_texts.append((text_file.name, content))
                special_text_indices.add(i)
            else:
                normal_texts.append(content)
    
    # 处理特殊文本：保持原样单独保存，并保留对应的PNG
    for filename, content in special_texts:
        # 保存文本文件
        with open(output_group_dir / filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  保存特殊文本: {filename}")
        
        # 复制对应的PNG文件（如果有）
        png_file = group_dir / filename.replace('_text.txt', '_text.png')
        if png_file.exists():
            shutil.copy2(png_file, output_group_dir / png_file.name)
            print(f"  复制PNG文件: {png_file.name}")
    
   # 处理普通文本：合并为一个文件（优化重叠检测）
    if normal_texts:
        merged_content = normal_texts[0]
        
        for next_text in normal_texts[1:]:
            # 仅检查前一个文本的末尾是否包含后一个文本的开头
            prev_tail = merged_content[-50:].strip()  # 取前一个文本的最后50字符（可调整长度）
            next_head = next_text[:50].strip()        # 取后一个文本的前50字符
            
            # 如果前文末尾包含后文开头，则去重拼接
            if prev_tail and next_head and prev_tail.endswith(next_head):
                overlap_len = len(next_head)
                merged_content = merged_content[:-overlap_len] + next_text
            else:
                merged_content += "\n" + next_text
        
        # 保存合并后的普通文本
        with open(output_group_dir / 'merged_text.txt', 'w', encoding='utf-8') as f:
            f.write(merged_content)
               
    # 复制其他非文本文件（标题文件等）
    for item in group_dir.iterdir():
        # 跳过普通文本对应的PNG文件（这些不需要复制）
        if item.name.endswith('_text.png'):
            # 检查是否是特殊文本对应的PNG（已经在上面处理过）
            text_index = int(item.stem.split('_')[0])
            if text_index not in special_text_indices:
                continue  # 普通文本的PNG跳过
        
        if not item.name.endswith('_text.txt'):  # 文本文件已经处理过
            if item.is_file():
                shutil.copy2(item, output_group_dir / item.name)
                print(f"  复制其他文件: {item.name}")

def process_page(page_dir, output_dir):
    """处理单个page文件夹"""
    print(f"处理页面: {page_dir}")
    for group_dir in sorted(page_dir.glob('group_*'), key=lambda x: int(x.stem.split('_')[1])):
        if group_dir.is_dir():
            process_group(group_dir, output_dir)

def merge_pages(input_dir, output_dir):
    """跨页面合并group"""
    print("开始跨页面合并...")
    # 获取所有页面
    pages = sorted(input_dir.glob('page_*'), key=lambda x: int(x.stem.split('_')[1]))
    
    if not pages:
        print("没有找到页面文件夹，跳过合并。")
        return
    
    # 创建最终的page_1目录
    final_page_dir = output_dir / 'page_1'
    final_page_dir.mkdir(exist_ok=True)
    print(f"创建最终页面目录: {final_page_dir}")
    
    # 初始化组列表
    groups = []
    
    # 遍历每个页面的组
    for page_idx, page in enumerate(pages):
        print(f"处理页面: {page}")
        page_groups = sorted(page.glob('group_*'), key=lambda x: int(x.stem.split('_')[1]))
        if not page_groups:
            print(f"  页面 {page} 没有组，跳过。")
            continue
        
        # 如果是第一个页面，直接添加所有组
        if page_idx == 0:
            groups.extend(page_groups)
            print(f"  添加第一个页面的所有组: {len(page_groups)}")
            continue
        
        # 检查当前页面的第一个组是否是group_0
        current_first_group = page_groups[0]
        is_group_zero = current_first_group.stem == "group_0"
        
        if is_group_zero and groups:  # 只有当存在group_0且前页有组时才合并
            last_group = groups[-1]
            print(f"  合并 {current_first_group} (group_0) 到 {last_group}")
            
            # 合并文本
            last_merged_text = last_group / 'merged_text.txt'
            current_merged_text = current_first_group / 'merged_text.txt'
            
            if last_merged_text.exists() and current_merged_text.exists():
                with open(last_merged_text, 'r', encoding='utf-8') as f:
                    last_content = f.read()
                with open(current_merged_text, 'r', encoding='utf-8') as f:
                    current_content = f.read()
                
                overlap = find_overlap(last_content, current_content)
                if overlap:
                    overlap_start = last_content.rfind(overlap)
                    last_content = last_content[:overlap_start] + current_content
                else:
                    last_content += "\n" + current_content
                
                # 保存合并后的文本
                with open(last_merged_text, 'w', encoding='utf-8') as f:
                    f.write(last_content)
                print(f"  保存合并后的文本: {last_merged_text}")
            
            # 复制当前页面的group_0的其他文件
            for item in current_first_group.iterdir():
                if item.name != 'merged_text.txt':
                    shutil.copy2(item, last_group / item.name)
                    print(f"  复制文件: {item.name}")
            
            # 添加当前页面的剩余组（从group_1开始）
            groups.extend(page_groups[1:])
            print(f"  添加其他组: {len(page_groups[1:])}")
        else:
            # 如果不是group_0或者前页没有组，直接添加所有组
            groups.extend(page_groups)
            print(f"  添加所有组（无group_0或前页无组）: {len(page_groups)}")
    
    # 将合并后的组复制到最终的page_1目录
    for i, group in enumerate(groups):
        target_group_dir = final_page_dir / f'group_{i}'
        shutil.copytree(group, target_group_dir)
        print(f"复制组 {group} 到 {target_group_dir}")
def main():
    # 定义输入输出路径
    # base_dir = Path(__file__).parent.parent
    # input_dir = base_dir / 'data_clean' / 'output0'
    # output3_dir = base_dir / 'data_clean' / 'output3'
    # output4_dir = base_dir / 'data_clean' / 'output4'
        # 修正后
    base_dir = Path(__file__).parent
    input_dir = base_dir / 'output0'
    output3_dir = base_dir / 'output3'  # 中间结果
    output4_dir = base_dir / 'output4'  # 最终结果

    print(f"输入目录: {input_dir}")
    print(f"中间输出目录: {output3_dir}")
    print(f"最终输出目录: {output4_dir}")
    
    # 清空或创建中间输出目录
    if output3_dir.exists():
        for item in output3_dir.glob('*'):
            if item.is_file():
                item.unlink()
            else:
                shutil.rmtree(item)
    output3_dir.mkdir(exist_ok=True)
    print(f"清空或创建中间输出目录: {output3_dir}")
    
    # 处理每个页面
    for page_dir in sorted(input_dir.glob('page_*'), key=lambda x: int(x.stem.split('_')[1])):
        if page_dir.is_dir():
            process_page(page_dir, output3_dir)
    
    # 清空或创建最终输出目录
    if output4_dir.exists():
        for item in output4_dir.glob('*'):
            if item.is_file():
                item.unlink()
            else:
                shutil.rmtree(item)
    output4_dir.mkdir(exist_ok=True)
    print(f"清空或创建最终输出目录: {output4_dir}")
    
    # 合并页面
    merge_pages(output3_dir, output4_dir)
    
    print(f"处理完成！中间结果已保存到 {output3_dir}")
    print(f"处理完成！最终结果已保存到 {output4_dir}")

if __name__ == '__main__':
    main()