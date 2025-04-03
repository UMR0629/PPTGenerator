import cv2
import layoutparser as lp
from pdf2image import convert_from_path
import pytesseract
import os
import numpy as np
from typing import List, Dict, Tuple

# 设置Tesseract路径
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# 加载模型
model = lp.Detectron2LayoutModel(
    config_path="./config.yml",
    model_path="./model_final.pth",
    label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8]
)

def sort_blocks(blocks: List[lp.TextBlock], image_width: int) -> List[lp.TextBlock]:
    """按左右分列并从上到下排序区块"""
    # 计算图像的中线
    mid_line = image_width / 2
    
    # 先按列排序（左列优先），然后按 y_1 排序
    return sorted(blocks, key=lambda b: (0 if b.block.x_1 < mid_line else 1, b.block.y_1))


def group_by_title(blocks: List[lp.TextBlock]) -> List[Dict]:
    """将内容分组到最近的标题下方，若无标题则归类为group0"""
    groups = []
    current_title = None
    current_content = []
    
    for block in blocks:
        if block.type == "Title":
            # 如果遇到标题，先将当前无标题引导的内容添加到分组中
            if not current_title and current_content:
                groups.append({"title": None, "content": current_content})
                current_content = []
            # 保存上一个标题组
            if current_title:
                groups.append({"title": current_title, "content": current_content})
            current_title = block
            current_content = []
        else:
            current_content.append(block)
    
    # 处理最后一组
    if not current_title and current_content:
        groups.append({"title": None, "content": current_content})
    elif current_title or current_content:
        groups.append({"title": current_title, "content": current_content})
    
    return groups



def extract_blocks_from_pdf(pdf_path: str, output_dir: str, dpi: int = 300, padding: int = 15):
    images = convert_from_path(pdf_path, dpi=dpi)
    os.makedirs(output_dir, exist_ok=True)

    for page_num, image in enumerate(images):
        print(f"Processing page {page_num + 1}...")
        page_dir = os.path.join(output_dir, f"page_{page_num + 1}")
        os.makedirs(page_dir, exist_ok=True)

        # 保存原始页面图像
        image_path = os.path.join(page_dir, "original.png")
        image.save(image_path, "PNG")
        image_cv = cv2.imread(image_path)
        image_cv = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
        h, w = image_cv.shape[:2]

        # 检测布局并排序
        layout = model.detect(image_cv)
        sorted_blocks = sort_blocks(layout,w)
        grouped_blocks = group_by_title(sorted_blocks)

        # 可视化布局
        # 修改后
        viz_image = lp.draw_box(image_cv, layout, box_width=3)
        viz_path = os.path.join(output_dir, f"page_{page_num + 1}_layout.png")
        # 确保图像是numpy数组格式
        if isinstance(viz_image, np.ndarray):
            # 直接从RGB保存为BGR格式
            cv2.imwrite(viz_path, viz_image[:, :, ::-1])  # 替代cvtColor
        else:
            print(f"无图像，page {page_num + 1}")

        # 按分组处理内容
        for group_idx, group in enumerate(grouped_blocks):
            # 判断是否为无标题引导的部分
            group_dir_name = f"group_{group_idx}" if group["title"] is None else f"group_{group_idx + 1}"
            group_dir = os.path.join(page_dir, group_dir_name)
            os.makedirs(group_dir, exist_ok=True)

            # 保存标题（如果存在）
            if group["title"]:
                title = group["title"]
                x1, y1, x2, y2 = map(int, [title.block.x_1, title.block.y_1, 
                                        title.block.x_2, title.block.y_2])
                title_image = image_cv[max(0,y1-padding):min(h,y2+padding), 
                                    max(0,x1-padding):min(w,x2+padding)]
                cv2.imwrite(os.path.join(group_dir, "00_title.png"), 
                        cv2.cvtColor(title_image, cv2.COLOR_RGB2BGR))
                
                # 提取标题文本
                title_text = pytesseract.image_to_string(title_image, lang='eng+chi_sim')
                with open(os.path.join(group_dir, "00_title.txt"), "w", encoding="utf-8") as f:
                    f.write(title_text.strip())

            # 保存内容区块
            for content_idx, content in enumerate(group["content"]):
                x1, y1, x2, y2 = map(int, [content.block.x_1, content.block.y_1,
                                        content.block.x_2, content.block.y_2])
                content_image = image_cv[max(0,y1-padding):min(h,y2+padding),
                                    max(0,x1-padding):min(w,x2+padding)]
                
                # 按类型处理
                prefix = f"{content_idx + 1:02d}_{content.type.lower()}"
                cv2.imwrite(os.path.join(group_dir, f"{prefix}.png"),
                        cv2.cvtColor(content_image, cv2.COLOR_RGB2BGR))

                if content.type in ["Text", "List"]:
                    text = pytesseract.image_to_string(content_image, lang='eng+chi_sim')
                    with open(os.path.join(group_dir, f"{prefix}.txt"), "w", encoding="utf-8") as f:
                        f.write(text.strip())
                elif content.type == "Table":
                    print(f"Table saved to {group_dir}/{prefix}.png")
                elif content.type == "Figure":
                    print(f"Figure saved to {group_dir}/{prefix}.png") 


# 调用示例
extract_blocks_from_pdf("test.pdf", "output2", padding=10)