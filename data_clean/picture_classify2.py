import re
from pathlib import Path
import shutil
import logging
from typing import Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('picture_classify2.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PictureRenamer:
    def __init__(self, input_dir: Path, output_dir: Path):
        self.input_dir = input_dir
        self.output_dir = output_dir

    def process_pages(self) -> None:
        """处理所有 page 目录"""
        page_dirs = sorted(
            (d for d in self.input_dir.glob('page_*') if d.is_dir()),
            key=lambda x: int(x.name.split('_')[-1])
        )
        for page_dir in page_dirs:
            logger.info(f"正在处理页面目录: {page_dir.name}")
            self.process_groups(page_dir)

    def process_groups(self, page_dir: Path) -> None:
        """处理单个 page 目录中的所有 group"""
        group_dirs = sorted(
            (d for d in page_dir.glob('group_*') if d.is_dir()),
            key=lambda x: int(x.name.split('_')[-1])
        )
        for group_dir in group_dirs:
            logger.info(f"正在处理组目录: {group_dir.name}")
            self.process_group(group_dir)

    def process_group(self, group_dir: Path) -> None:
        """处理单个 group 目录"""
        # 获取当前 group 中的所有 png 文件
        png_files = sorted(
            (f for f in group_dir.glob('*.png') if any(keyword.lower() in f.name.lower() for keyword in ['figure', 'table', 'list']))
        )
        # 获取当前 group 中的所有 txt 文件
        txt_files = sorted(
            (f for f in group_dir.glob('*.txt'))
        )
        processed_txt_files = set()  # 用于记录已处理的 txt 文件，避免重复处理

        for png_file in png_files:
            logger.info(f"处理 PNG 文件: {png_file.name}")
            # 提取 PNG 文件名称中的关键词（figure、table、list 等）
            png_keyword = self.extract_keyword(png_file.name)
            if not png_keyword:
                logger.warning(f"PNG 文件 {png_file.name} 中未找到有效关键词，跳过")
                continue

            # 在 TXT 文件中查找 PNG 文件名称
            for txt_file in txt_files:
                if txt_file in processed_txt_files:
                    continue  # 如果该 TXT 文件已处理，则跳过
                txt_content = self.read_txt_file(txt_file)
                if not txt_content:
                    logger.warning(f"TXT 文件 {txt_file.name} 为空或无法读取，跳过")
                    continue

                # 在 TXT 文件内容中查找 PNG 文件名称
                match = re.search(rf'({png_keyword}\s+\d+)', txt_content, re.IGNORECASE)
                if match:
                    logger.info(f"在 TXT 文件 {txt_file.name} 中找到 PNG 文件名称 {match.group(1)}")
                    new_name = match.group(1).replace(' ', '')  # 构造新的 PNG 文件名称
                    new_png_file = self.output_dir / new_name / f"{new_name}.png"
                    new_txt_file = self.output_dir / new_name / f"{new_name}.txt"

                    # 创建输出目录
                    new_png_file.parent.mkdir(parents=True, exist_ok=True)

                    # 复制并重命名 PNG 文件和 TXT 文件到输出目录
                    shutil.copy(png_file, new_png_file)
                    logger.info(f"复制并重命名 PNG 文件 {png_file.name} 为 {new_png_file.name}")
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    with open(new_txt_file, 'w', encoding='utf-8') as f:
                        # 从匹配到的部分之后的内容开始截取，并去掉首尾空白字符
                        modified_content = content[match.end():].strip()
                        # 删除头部的冒号及其后的空白字符
                        modified_content = re.sub(r'^:\s*', '', modified_content)
                        # 写入新的 TXT 文件
                        f.write(modified_content)
                    logger.info(f"复制并重命名 TXT 文件 {txt_file.name} 为 {new_txt_file.name}")
                    processed_txt_files.add(txt_file)  # 将已处理的 TXT 文件加入集合
                    break  # 找到匹配的 TXT 文件后，跳出循环

    def extract_keyword(self, filename: str) -> Optional[str]:
        """从文件名中提取关键词"""
        keywords = ['figure', 'table', 'list']
        for keyword in keywords:
            if keyword.lower() in filename.lower():
                return keyword
        return None

    def read_txt_file(self, txt_file: Path) -> Optional[str]:
        """读取 TXT 文件内容"""
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"无法读取 TXT 文件 {txt_file.name}: {str(e)}")
            return None

    def run(self) -> None:
        """执行处理流程"""
        logger.info(f"开始处理目录: {self.input_dir}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.process_pages()
        logger.info(f"处理完成！输出目录: {self.output_dir}")

def main():
    try:
        base_dir = Path(__file__).parent.parent
        input_dir = base_dir / 'data_clean' / 'output_picture'
        output_dir = base_dir / 'data_clean' / 'output_picture0'
        
        logger.info("="*50)
        logger.info(f"开始处理图片重命名")
        logger.info(f"输入目录: {input_dir}")
        logger.info(f"输出目录: {output_dir}")
        logger.info("="*50)
        
        if not input_dir.exists():
            raise FileNotFoundError(f"输入目录不存在: {input_dir}")
        
        renamer = PictureRenamer(input_dir, output_dir)
        renamer.run()
        logger.info("处理成功完成！")
    except Exception as e:
        logger.critical(f"程序运行时出错: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    main()