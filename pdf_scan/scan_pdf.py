import cv2
import layoutparser as lp
from pdf2image import convert_from_path
import pytesseract
import os
import sys
import numpy as np
import platform
from pathlib import Path
from typing import List, Dict, Tuple,Optional
from anytree import Node, PreOrderIter
from difflib import SequenceMatcher
import re
import shutil
# 获取当前脚本所在目录
current_directory = Path(__file__).resolve().parent
debug_mode = False
# 将 index 目录添加到 sys.path
sys.path.append(str(current_directory.parent / 'index'))

# 导入 index 模块
from index_module import PaperInfo, SectionContent  

# 设置Tesseract路径
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
else:  
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# 构建绝对路径
config_path="lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config"

# 加载模型
model = lp.Detectron2LayoutModel(
    config_path=str(config_path),
    label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8]
)

def sort_blocks(blocks: List[lp.TextBlock], image_width: int) -> List[lp.TextBlock]:
    """按左右分列并从上到下排序区块"""
    mid_line = image_width / 2
    return sorted(blocks, key=lambda b: (0 if b.block.x_1 < mid_line else 1, b.block.y_1))

def group_by_title(blocks: List[lp.TextBlock]) -> List[Dict]:
    """将内容分组到最近的标题下方，若无标题则归类为group0"""
    groups = []
    current_title = None
    current_content = []
    
    for block in blocks:
        if block.type == "Title":
            if not current_title and current_content:
                groups.append({"title": None, "content": current_content})
                current_content = []
            if current_title:
                groups.append({"title": current_title, "content": current_content})
            current_title = block
            current_content = []
        else:
            current_content.append(block)
    
    if not current_title and current_content:
        groups.append({"title": None, "content": current_content})
    elif current_title or current_content:
        groups.append({"title": current_title, "content": current_content})
    
    return groups

def clean_text(text):
    """清理文本，去除多余换行符和空白"""
    text = re.sub(r'\n+', ' ', text)  # 替换多个换行为单个空格
    text = re.sub(r'\s+', ' ', text)  # 合并多个空白字符
    return text.strip()

def extract_text_from_image(image, block, padding=15):
    """从图像区域提取文本并清理"""
    x1, y1, x2, y2 = map(int, [block.block.x_1, block.block.y_1, block.block.x_2, block.block.y_2])
    h, w = image.shape[:2]
    content_image = image[max(0,y1-padding):min(h,y2+padding), max(0,x1-padding):min(w,x2+padding)]
    text = pytesseract.image_to_string(content_image, lang='eng+chi_sim')
    return clean_text(text)

def check_and_recover_missing_blocks(
    sorted_blocks: List[lp.TextBlock], 
    image: np.ndarray, 
    image_height: int,
    image_width: int,
    output_base_dir: str,
    page_num: int,
    min_gap: int = 120,
    edge_gap: int = 310,
    padding: int = 15,
    overlap_threshold: float = 0.2,  # 重合度阈值
    debug: bool = False
) -> List[lp.TextBlock]:
    """
    检查两列布局中的遗漏区域，增加边缘处理和重合度检查
    
    Args:
        overlap_threshold: 最大允许重合比例(默认20%)
    """
    new_blocks = []
    missing_count = 0
    
    # 创建missing目录
    missing_dir = os.path.join(output_base_dir, "missing_blocks")
    if debug:
        os.makedirs(missing_dir, exist_ok=True)
    
    # 将区块分为左列和右列
    mid_line = image_width / 2
    left_col = [b for b in sorted_blocks if b.block.center[0] < mid_line]
    right_col = [b for b in sorted_blocks if b.block.center[0] >= mid_line]
    
    all_blocks_in_col = [b.block for b in sorted_blocks]
    # 处理每列
    for col_idx, col_blocks in enumerate([left_col, right_col]):
        col_name = ["左列", "右列"][col_idx]
        
        if not col_blocks:
            continue
            
        # 按垂直位置排序
        col_blocks_sorted = sorted(col_blocks, key=lambda b: b.block.y_1)
        
        
        # 检查列顶部遗漏 (减去edge_gap)
        first_block = col_blocks_sorted[0]
        top_gap = first_block.block.y_1
        if top_gap > edge_gap:
            missing_count += 1
            if debug_mode:
                print(f"检测{col_name}顶部间隙: {top_gap}px (阈值: {edge_gap}px)")
            
            # 减去edge_gap后的实际可疑区域
            actual_y1 = edge_gap
            if actual_y1 > 10:  # 确保有足够高度
                missing_block = create_and_validate_missing_block(
                    x1=first_block.block.x_1,
                    x2=first_block.block.x_2,
                    y1=actual_y1,
                    y2=first_block.block.y_1,
                    existing_blocks=all_blocks_in_col,
                    image=image,
                    page_num=page_num,
                    missing_count=missing_count,
                    missing_dir=missing_dir,
                    padding=padding,
                    overlap_threshold=overlap_threshold,
                    debug=debug,
                    location="top"
                )
                if missing_block:
                    new_blocks.append(missing_block)
        
        # 检查列内部块间遗漏
        for i in range(len(col_blocks_sorted)):
            current_block = col_blocks_sorted[i]
            new_blocks.append(current_block)
            
            if i == len(col_blocks_sorted) - 1:
                continue
                
            next_block = col_blocks_sorted[i + 1]
            gap = next_block.block.y_1 - current_block.block.y_2
            
            if gap > min_gap:
                missing_count += 1
                if debug_mode:
                    print(f"检测{col_name}内部间隙: {gap}px (阈值: {min_gap}px)")
                
                missing_block = create_and_validate_missing_block(
                    x1=current_block.block.x_1,
                    x2=current_block.block.x_2,
                    y1=current_block.block.y_2,
                    y2=next_block.block.y_1,
                    existing_blocks=all_blocks_in_col,
                    image=image,
                    page_num=page_num,
                    missing_count=missing_count,
                    missing_dir=missing_dir,
                    padding=padding,
                    overlap_threshold=overlap_threshold,
                    debug=debug,
                    location="middle"
                )
                if missing_block:
                    new_blocks.append(missing_block)
        
        # 检查列底部遗漏 (减去edge_gap)
        last_block = col_blocks_sorted[-1]
        bottom_gap = image_height - last_block.block.y_2
        if bottom_gap > edge_gap:
            missing_count += 1
            if debug_mode:
                print(f"检测{col_name}底部间隙: {bottom_gap}px (阈值: {edge_gap}px)")
            
            # 减去edge_gap后的实际可疑区域
            actual_y2 = image_height-edge_gap
            if (image_height - actual_y2) > 10:  # 确保有足够高度
                missing_block = create_and_validate_missing_block(
                    x1=last_block.block.x_1,
                    x2=last_block.block.x_2,
                    y1=last_block.block.y_2,
                    y2=actual_y2,
                    existing_blocks=all_blocks_in_col,
                    image=image,
                    page_num=page_num,
                    missing_count=missing_count,
                    missing_dir=missing_dir,
                    padding=padding,
                    overlap_threshold=overlap_threshold,
                    debug=debug,
                    location="bottom"
                )
                if missing_block:
                    new_blocks.append(missing_block)
    
    return sort_blocks(new_blocks, image_width)

def create_and_validate_missing_block(
    x1: float, x2: float, y1: float, y2: float,
    existing_blocks: List[lp.Rectangle],
    image: np.ndarray, page_num: int, missing_count: int,
    missing_dir: str, padding: int, overlap_threshold: float,
    debug: bool, location: str
) -> Optional[lp.TextBlock]:
    """创建并验证missing区块"""
    # 坐标转换和安全处理
    missing_x1 = int(max(0, x1))
    missing_x2 = int(min(image.shape[1], x2))
    missing_y1 = int(max(0, y1))
    missing_y2 = int(min(image.shape[0], y2))
    
    # 计算missing区域面积
    missing_area = (missing_x2 - missing_x1) * (missing_y2 - missing_y1)
    if missing_area <= 0:
        return None
    
    # 检查与现有区块的重合度
    max_overlap_ratio = 0
    missing_rect = lp.Rectangle(missing_x1, missing_y1, missing_x2, missing_y2)
    
    for block in existing_blocks:
        block_area = (block.x_2 - block.x_1) * (block.y_2 - block.y_1)
        # 计算相交区域
        dx = min(missing_x2, block.x_2) - max(missing_x1, block.x_1)
        dy = min(missing_y2, block.y_2) - max(missing_y1, block.y_1)
        if dx > 0 and dy > 0:
            overlap_area = dx * dy
            overlap_ratio = overlap_area / missing_area
            if debug_mode:
                print(f"缺失区域重合度: {overlap_ratio:.1%}")
                print(f"缺失区域坐标:{missing_x1, missing_y1, missing_x2, missing_y2},block坐标:{block.x_1, block.y_1, block.x_2, block.y_2}")
            max_overlap_ratio = max(max_overlap_ratio, overlap_ratio)
    
    # 如果重合度过高则忽略
    if max_overlap_ratio > overlap_threshold:
        if debug_mode:
            print(f"忽略{location}遗漏区域 (重合度: {max_overlap_ratio:.1%} > {overlap_threshold:.0%}阈值)")
        return None
    
    # 创建区块对象
    missing_block = lp.TextBlock(
        block=missing_rect,
        type="unknown"
    )
    
    # 调试模式保存图像
    if debug:
        missing_img = image[
            max(0, missing_y1-padding):min(image.shape[0], missing_y2+padding),
            max(0, missing_x1-padding):min(image.shape[1], missing_x2+padding)
        ]
        os.makedirs(missing_dir, exist_ok=True)
        missing_path = os.path.join(missing_dir, 
            f"page_{page_num+1}_missing_{missing_count}_{location}.png")
        cv2.imwrite(missing_path, cv2.cvtColor(missing_img, cv2.COLOR_RGB2BGR))
        print(f"保存确认的{location}遗漏区域到: {missing_path}")
    
    return missing_block

def save_block_image(image, block, output_dir, name_prefix, padding=15):
    """保存区块图像到指定目录"""
    x1, y1, x2, y2 = map(int, [block.block.x_1, block.block.y_1, block.block.x_2, block.block.y_2])
    h, w = image.shape[:2]
    content_image = image[max(0,y1-padding):min(h,y2+padding), max(0,x1-padding):min(w,x2+padding)]
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存图像
    img_path = os.path.join(output_dir, f"{name_prefix}.png")
    cv2.imwrite(img_path, cv2.cvtColor(content_image, cv2.COLOR_RGB2BGR))
    return img_path

def get_caption_for_block(blocks, current_index, block_type, image):
    """获取区块的标题或描述文本"""
    caption_patterns = {
        "figure": r"(?:figure|fig|图片|图)\s*(\d+)",
        "table": r"(?:table|tab|表格|表)\s*(\d+)",
        "list": r"(?:list|listing|列表)\s*(\d+)",
        "unknown": r"(?:figure|fig|图片|图|table|tab|表格|表|list|listing|列表)\s*(\d+)"
    }
    
    # 对于表格，查看前一个区块
    if block_type == "table":
        if current_index > 0:
            prev_block = blocks[current_index-1]
            prev_text = extract_text_from_image(image, prev_block)
            if match := re.search(caption_patterns["table"], prev_text, re.IGNORECASE):
                return f"Table {match.group(1)}", True, block_type
            return clean_text(prev_text), False, block_type
    
    # 对于图片和列表，查看后一个区块
    elif block_type in ["figure", "list"]:
        if current_index < len(blocks)-1:
            next_block = blocks[current_index+1]
            next_text = extract_text_from_image(image, next_block)
            if match := re.search(caption_patterns[block_type], next_text, re.IGNORECASE):
                return f"{block_type.capitalize()} {match.group(1)}", True, block_type
            return clean_text(next_text), False, block_type
        
     # 对于unknown类型，查看前后两个区块
    elif block_type == "unknown":
        if debug_mode:
            print("未知类型区块，尝试查找前后两个区块")
        if current_index > 0 and current_index < len(blocks) - 1:
            prev_block = blocks[current_index-1]
            next_block = blocks[current_index+1]
            prev_text = extract_text_from_image(image, prev_block)
            next_text = extract_text_from_image(image, next_block)
            if match := re.search(caption_patterns["table"], prev_text, re.IGNORECASE):
                block_type = "table"
                return f"Table {match.group(1)}", True, block_type
            elif match := re.search(caption_patterns["list"], next_text, re.IGNORECASE):
                block_type = "list"
                return f"List {match.group(1)}", True, block_type
            elif match := re.search(caption_patterns["figure"], next_text, re.IGNORECASE):
                block_type = "figure"
                return f"Figure {match.group(1)}", True, block_type
            else:
                return clean_text(prev_text), False , "other"
    return None, False, "other"

def determine_block_type(block, text):
    """根据内容和文本确定区块类型"""
    # 文字块直接返回
    if block.type.lower() == "text":
        return "text"
    
    text_lower = text.lower()
    block_type = block.type.lower()
    
    # 仅在图片/表格/list中检查algorithm关键字
    if block_type in ["figure", "table", "list"]:
        if ("algorithm" in text_lower or "算法" in text_lower) and ("end" in text_lower) and ("input" in text_lower or "output" in text_lower):
            return "algorithm"
    
    return block_type


def process_content_blocks(image, blocks, page_num, output_base_dir, debug=False):
    """处理内容块并返回结构化数据"""
    content_data = {
        "text": "",
        "tables": [],
        "figures": [],
        "lists": [],
        "algorithms": [],
        "others": []  # 添加others分类
    }
    
    # 在debug模式下保存完整页面图像
    if debug:
        debug_images_dir = os.path.join(output_base_dir, "debug_output", f"page_{page_num + 1}", "images")
        os.makedirs(debug_images_dir, exist_ok=True)
        full_page_path = os.path.join(debug_images_dir, f"page_{page_num + 1}_full.png")
        cv2.imwrite(full_page_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    
    for idx, block in enumerate(blocks):
        raw_text = extract_text_from_image(image, block)
        block_type = determine_block_type(block, raw_text)
        
        
        if block_type == "text":
            content_data["text"] += raw_text + " "
            if debug:
                debug_output_dir = os.path.join(output_base_dir, "debug_output", f"page_{page_num + 1}")
                os.makedirs(debug_output_dir, exist_ok=True)
                with open(os.path.join(debug_output_dir, f"text_{idx + 1}.txt"), "w", encoding="utf-8") as f:
                    f.write(raw_text)
            continue  # 文字块不进入图片列表
        number = None
        # 获取描述文本
        caption, is_numbered, block_type = get_caption_for_block(blocks, idx, block_type, image)
        # 确定命名前缀和分类
        if block_type == "algorithm":
            name_prefix = f"page_{page_num + 1}_algorithm_{len(content_data['algorithms']) + 1}"
            category = "algorithms"
            match = re.search(r"\b(\d+)\b", caption)  # 匹配独立的数字
            number = int(match.group(1)) if match else None
        elif is_numbered and caption:
            name_prefix = f"page_{page_num + 1}_{caption.lower().replace(' ', '_')}"
            category = block_type + "s"  # figure -> figures
            match = re.search(r"\b(\d+)\b", caption)  # 匹配独立的数字
            number = int(match.group(1)) if match else None
        else:
            name_prefix = f"page_{page_num + 1}_other_{len(content_data['others']) + 1}"
            category = "others"
        
        # 创建统一输出目录
        images_output_dir = os.path.join(output_base_dir, "all_images")
        os.makedirs(images_output_dir, exist_ok=True)
        
        # 保存区块图像到统一目录
        img_path = save_block_image(image, block, images_output_dir, name_prefix)
        
        item_data = {
            "position": [block.block.x_1, block.block.y_1, block.block.x_2, block.block.y_2],
            "text": caption if caption else raw_text,
            "path": img_path,
            "original_type": block.type.lower(),  # 记录原始类型
            "nr": number  # 记录编号
        }
        
        # 添加到对应分类
        content_data[category].append(item_data)
        
        if debug:
            debug_output_dir = os.path.join(output_base_dir, "debug_output", f"page_{page_num + 1}")
            os.makedirs(debug_output_dir, exist_ok=True)
            with open(os.path.join(debug_output_dir, f"{block_type}_{idx + 1}.txt"), "w", encoding="utf-8") as f:
                f.write(item_data["text"])
    
    # 清理合并后的文本
    content_data["text"] = clean_text(content_data["text"])
    
    return content_data


def merge_with_previous_group(current_group, previous_group):
    """将当前组与前一组合并"""
    if not previous_group:
        return current_group
    
    # 合并文本内容
    if current_group["content"]["text"] and previous_group["content"]["text"]:
        # 检查是否有重叠部分
        overlap = find_text_overlap(previous_group["content"]["text"], current_group["content"]["text"])
        if overlap:
            current_group["content"]["text"] = previous_group["content"]["text"] + current_group["content"]["text"][len(overlap):]
        else:
            current_group["content"]["text"] = previous_group["content"]["text"] + "\n" + current_group["content"]["text"]
    
    # 合并其他元素
    for key in ["tables", "figures", "lists", "algorithms"]:
        current_group["content"][key] = previous_group["content"][key] + current_group["content"][key]
    
    return current_group

def find_text_overlap(text1, text2, min_overlap=20):
    """找到两个文本之间的重叠部分"""
    match = SequenceMatcher(None, text1, text2).find_longest_match(0, len(text1), 0, len(text2))
    if match.size >= min_overlap:
        return text1[match.a: match.a + match.size]
    return ""

def extract_paper_info_from_pdf(pdf_path: str, output_base_dir: str, dpi: int = 300, debug: bool = False) -> PaperInfo:
    """从PDF提取信息并返回PaperInfo对象"""
    # 清空目标目录内容
    if os.path.exists(output_base_dir):
        shutil.rmtree(output_base_dir)
    # 创建输出目录
    os.makedirs(output_base_dir, exist_ok=True)
    
    # 在debug模式下创建原始页面目录
    if debug:
        original_pages_dir = os.path.join(output_base_dir, "original_pages")
        os.makedirs(original_pages_dir, exist_ok=True)
    
    images = convert_from_path(pdf_path, dpi=dpi)
    paper_info = PaperInfo(
        title="Untitled",  # 临时标题，后面会更新
        authors=["Unknown"],
        date="",
        journal="",
        ppt_presenter="",
        ppt_date=""
    )
    
    previous_groups = []  # 存储上一页的分组信息
    parent_rome = paper_info.outline_root
    for page_num, image in enumerate(images):
        # 在debug模式下保存原始页面图像
        if debug:
            image_path = os.path.join(original_pages_dir, f"page_{page_num + 1}.png")
            image.save(image_path, "PNG")
            image_cv = cv2.imread(image_path)
            print(f"正在处理第{page_num + 1}页")
        else:
            # 非debug模式直接转换图像
            image_cv = np.array(image)
            image_cv = cv2.cvtColor(image_cv, cv2.COLOR_RGB2BGR)
            image_cv = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
            
        h, w = image_cv.shape[:2]

        # 检测布局并分组
        layout = model.detect(image_cv)
        # if debug:
        #     print(f"正在处理第{page_num + 1}页")
        #     print(f"layout: {layout}")
        sorted_blocks = sort_blocks(layout, w)
        # if debug:
        #     print(f"正在处理第{page_num + 1}页")
        #     debug_output_dir = os.path.join(output_base_dir, "debug_output", f"page_{page_num + 1}")
        #     os.makedirs(debug_output_dir, exist_ok=True)
        #     for idx, block in enumerate(sorted_blocks):
        #         print(f"区块类型: {block.type}")
        #         # 截取区块图像
        #         block_image = image_cv[int(block.block.y_1):int(block.block.y_2), int(block.block.x_1):int(block.block.x_2)]
        #         # 保存区块图像
        #         block_image_path = os.path.join(debug_output_dir, f"block_{idx + 1}_{block.type}.png")
        #         cv2.imwrite(block_image_path, block_image)
                
        sorted_blocks = check_and_recover_missing_blocks(sorted_blocks, image_cv, h,w,output_base_dir=output_base_dir,page_num=page_num,debug=debug_mode) 
        if debug:
            print(f"正在处理第{page_num + 1}页")
            debug_output_dir = os.path.join(output_base_dir, "debug_output", f"page_{page_num + 1}")
            os.makedirs(debug_output_dir, exist_ok=True)
            for idx, block in enumerate(sorted_blocks):
                print(f"区块类型: {block.type}")
                # 截取区块图像
                block_image = image_cv[int(block.block.y_1):int(block.block.y_2), int(block.block.x_1):int(block.block.x_2)]
                # 保存区块图像
                block_image_path = os.path.join(debug_output_dir, f"block_{idx + 1}_{block.type}.png")
                cv2.imwrite(block_image_path, block_image)
        grouped_blocks = group_by_title(sorted_blocks)
        
        current_groups = []
        for group_idx, group in enumerate(grouped_blocks):
            # 处理内容块
            content_data = process_content_blocks(
                image_cv, 
                group["content"], 
                page_num, 
                output_base_dir, 
                debug
            )
            
            # 如果是group_0且不是第一页，尝试与前一页的最后一组合并
            if group["title"] is None and page_num > 0 and previous_groups:
                merged_group = merge_with_previous_group({
                    "title": None,
                    "content": content_data
                }, previous_groups[-1])
                content_data = merged_group["content"]
            
            # 创建SectionContent对象
            section_content = SectionContent(text=content_data["text"])
            
            # 如果是标题组，添加到大纲
            if group["title"]:
                title_text = extract_text_from_image(image_cv, group["title"])
                if debug:
                    debug_output_dir = os.path.join(output_base_dir, "debug_output", f"page_{page_num + 1}")
                    os.makedirs(debug_output_dir, exist_ok=True)
                    with open(os.path.join(debug_output_dir, "title.txt"), "w", encoding="utf-8") as f:
                        f.write(title_text)
                
                if paper_info.title == "Untitled":
                    paper_info.title = title_text
                    paper_info.outline_root.name = title_text
                else:
                    # 添加到大纲结构
                    if title_text[0].isdigit():
                        parent = find_parent_for_section(paper_info, title_text)
                        #print(f"数字-当前标题: {title_text}, 父节点: {parent.name if parent else '无'}")
                        Node(title_text, parent=parent, content=section_content)
                    else:
                        if starts_with_roman_numeral(title_text):
                            parent = paper_info.outline_root
                            #print(f"罗马-当前标题: {title_text}, 父节点: {parent.name if parent else '无'}")
                            parent_rome = Node(title_text, parent=parent, content=section_content)
                        else:
                            #print(f"字母-当前标题: {title_text}, 父节点: {parent_rome.name if parent else '无'}")
                            Node(title_text, parent=parent_rome, content=section_content)
            
            current_groups.append({
                "title": group["title"],
                "content": content_data
            })
            
            # 处理各类图片
            for fig in content_data["figures"]:
                paper_info.image_list.append({
                    "number": f'Figure{fig["nr"]}',
                    "path": fig["path"],
                    "description": fig["text"],
                    "type": "figure"
                })
            
            for table in content_data["tables"]:
                paper_info.image_list.append({
                    "number": f'Table{table["nr"]}',
                    "path": table["path"],
                    "description": table["text"],
                    "type": "table"
                })
            
            for lst in content_data["lists"]:
                paper_info.image_list.append({
                    "number":f'List{lst["nr"]}',
                    "path": lst["path"],
                    "description": lst["text"],
                    "type": "list"
                })
            
            for algo in content_data["algorithms"]:
                paper_info.image_list.append({
                    "number": f'Algorithm{algo["nr"]}',
                    "path": algo["path"],
                    "description": algo["text"],
                    "type": "algorithm"
                })
            
            for other in content_data["others"]:
                if debug_mode:
                    paper_info.image_list.append({
                        "number": f"Other{len([img for img in paper_info.image_list if img['number'].startswith('Other')]) + 1}",
                        "path": other["path"],
                        "description": other["text"],
                        "type": "other",
                        "original_type": other["original_type"]  # 保留原始类型信息
                    })
    
    return paper_info

# def find_parent_for_section(paper_info: PaperInfo, title_text: str):
#     """根据标题文本确定父节点"""
#     if "." in title_text:  # 假设包含点的标题是子标题
#         parts = title_text.split(".")
#         parent_title = ".".join(parts[:-1])
#         parent = paper_info.find_outline_section(parent_title)
#         return parent if parent else paper_info.outline_root
#     return paper_info.outline_root


def find_parent_id_for_section(section: str) -> str:
    # 提取章节编号部分，并去除多余空格
    match = re.match(r"([\d\s.]+)", section)  # 仅匹配章节编号部分
    if not match:
        return None  # 如果找不到编号，返回 None

    section_number = match.group(1).replace(" ", "").rstrip(".")  # 去掉空格和尾随的点
    parts = section_number.split(".")

    if len(parts) == 1:
        return None  # 顶级章节没有父节点

    return ".".join(parts[:-1]) + "."

def extract_section_id(text: str) -> str:
    match = re.match(r"([\d\s.]+)", text)  # 仅匹配开头的数字、空格和点
    if not match:
        return ""  # 如果没有匹配到编号，返回空字符串

    section_number = match.group(1).replace(" ", "")  # 去掉空格，保持原本的点
    return section_number

def find_parent_for_section(paper_info: PaperInfo, title_text: str):
    """根据标题文本确定父节点"""
    if "." in title_text:  # 假设包含点的标题是子标题
        parent_id = find_parent_id_for_section(title_text)
        # 类似1. Introduction
        if parent_id is None:
            return paper_info.outline_root
        parent = None
        for node in PreOrderIter(paper_info.outline_root):
            if extract_section_id(node.name) == parent_id:
                parent = node
                break
        return parent if parent else paper_info.outline_root
    return paper_info.outline_root

# 判断是否以罗马数字开头
def starts_with_roman_numeral(text: str) -> bool:
    """ 判断字符串是否以罗马数字开头 """
    # 定义匹配罗马数字的正则表达式
    roman_pattern = r"^[IVX]+"

    # 使用正则表达式匹配文本开头
    match = re.match(roman_pattern, text.strip())  # 去除前后空格后检查

    # 如果匹配成功并且至少有一个字符，说明是罗马数字开头
    return bool(match)

if __name__ == "__main__":
    # 设置输出目录和调试模式
    output_directory = "output"
    debug_mode = True  # 设置为False关闭debug输出
    
    paper_info = extract_paper_info_from_pdf(
        "test.pdf", 
        output_base_dir=output_directory,
    )
    paper_info.display_outline()
