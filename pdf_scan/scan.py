import cv2
import layoutparser as lp
from pdf2image import convert_from_path
import pytesseract
import os
import numpy as np

# 设置Tesseract路径（如果需要）
pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# 加载预训练模型（使用PubLayNet）
model = lp.Detectron2LayoutModel(
    config_path="./config.yml",
    model_path="./model_final.pth",
    label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8]  # 设置置信度阈值
)

def extract_blocks_from_pdf(pdf_path, output_dir, dpi=300,padding=10):
    """
    从PDF中提取分块（文本、表格、图片等）
    :param pdf_path: PDF文件路径
    :param output_dir: 输出目录
    :param dpi: 图像分辨率
    """
    # 将PDF转换为图像
    images = convert_from_path(pdf_path, dpi=dpi)
    os.makedirs(output_dir, exist_ok=True)

    for page_num, image in enumerate(images):
        print(f"Processing page {page_num + 1}...")
        image_path = os.path.join(output_dir, f"page_{page_num + 1}.png")
        image.save(image_path, "PNG")

        # 使用OpenCV加载图像
        image_cv = cv2.imread(image_path)
        image_cv = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
        h, w = image_cv.shape[:2]
        # 使用LayoutParser检测布局
        layout = model.detect(image_cv)

        # 修改后
        viz_image = lp.draw_box(image_cv, layout, box_width=3)
        viz_path = os.path.join(output_dir, f"page_{page_num + 1}_layout.png")
        # 确保图像是numpy数组格式
        if isinstance(viz_image, np.ndarray):
            # 直接从RGB保存为BGR格式
            cv2.imwrite(viz_path, viz_image[:, :, ::-1])  # 替代cvtColor
        else:
            print(f"无图像，page {page_num + 1}")

        # 提取并保存各分块
        for block in layout:
            block_type = block.type
            # 将坐标值转换为整数
            x1, y1, x2, y2 = map(int, block.coordinates)
            
            # 应用padding
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(w, x2 + padding)
            y2 = min(h, y2 + padding)
            block_image = image_cv[y1:y2, x1:x2]

            # 保存分块图像
            block_dir = os.path.join(output_dir, f"page_{page_num + 1}_blocks")
            os.makedirs(block_dir, exist_ok=True)
            block_path = os.path.join(block_dir, f"{block_type}_{x1}_{y1}_{x2}_{y2}.png")
            cv2.imwrite(block_path, cv2.cvtColor(block_image, cv2.COLOR_RGB2BGR))

            # 如果是文本块，使用Tesseract提取文字
            if block_type in ["Text", "Title", "List"]:
                text = pytesseract.image_to_string(block_image)
                text_path = os.path.join(block_dir, f"{block_type}_{x1}_{y1}_{x2}_{y2}.txt")
                with open(text_path, "w", encoding="utf-8") as f:
                    f.write(text)

            # 如果是表格块，保存为单独图像（后续可用Camelot/pdfplumber处理）
            elif block_type == "Table":
                print(f"Table detected on page {page_num + 1}, saved to {block_path}")

            # 如果是图片块，直接保存
            elif block_type == "Figure":
                print(f"Figure detected on page {page_num + 1}, saved to {block_path}")

# 示例调用
pdf_path = "test.pdf"  # 替换为你的PDF路径
output_dir = "output"     # 输出目录
extract_blocks_from_pdf(pdf_path, output_dir)
