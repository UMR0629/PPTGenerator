import re
from pathlib import Path
import shutil
import logging
from typing import List, Dict, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('picture_classify.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PictureProcessor:
    def __init__(self, output2_dir: Path, output_picture_dir: Path):
        self.output2_dir = output2_dir
        self.output_picture_dir = output_picture_dir

    def process_pages(self) -> None:
        """处理所有页面目录"""
        page_dirs = sorted(
            (d for d in self.output2_dir.glob('page_*') if d.is_dir()),
            key=lambda x: int(x.name.split('_')[-1])
        )
        for page_dir in page_dirs:
            logger.info(f"现在处理页面目录: {page_dir.name}")
            group_dirs = sorted(
                (d for d in page_dir.glob('group_*') if d.is_dir()),
                key=lambda x: int(x.name.split('_')[-1])
            )
            if not group_dirs:
                logger.info(f"页面 {page_dir.name} 中没有符合条件的 group 目录")
                continue
            
            for group_dir in group_dirs:
                self.process_group(page_dir, group_dir)

    def process_group(self, page_dir: Path, group_dir: Path) -> None:
        """处理单个 group 目录"""
        logger.info(f"现在处理目录: {group_dir.name}")
        files = list(group_dir.glob('*'))
        if not files:
            logger.warning(f"目录 {group_dir.name} 中没有文件，跳过")
            return
        
        for file in files:
            if self.is_file_valid(file):
                self.copy_file(page_dir, group_dir, file)
            else:
                logger.info(f"跳过文件: {file.name} (不符合条件)")

    def is_file_valid(self, file: Path) -> bool:
        """判断文件是否符合条件"""
        # 条件1：文件名中包含特定关键词（不区分大小写）
        keywords = ['table', 'figure', 'list']
        if any(keyword.lower() in file.name.lower() for keyword in keywords):
            return True
        
        # 条件2：如果是 .txt 文件，检查文件内容是否以特定关键词开头
        if file.suffix.lower() == '.txt':
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip().lower()
                if first_line.startswith(('figure', 'list', 'table')):
                    return True
            except Exception as e:
                logger.warning(f"无法读取文件 {file.name} 的内容: {str(e)}")
        
        return False

    def copy_file(self, page_dir: Path, group_dir: Path, file: Path) -> None:
        """复制文件到输出目录"""
        output_page_dir = self.output_picture_dir / page_dir.name
        output_group_dir = output_page_dir / group_dir.name
        output_page_dir.mkdir(parents=True, exist_ok=True)
        output_group_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_group_dir / file.name
        shutil.copy(file, output_file)
        logger.info(f"复制 {file} 到 {output_file}")

    def run(self) -> None:
        """执行处理流程"""
        logger.info(f"开始处理目录: {self.output2_dir}")
        self.output_picture_dir.mkdir(exist_ok=True, parents=True)
        
        # 处理所有页面
        self.process_pages()
        
        logger.info(f"处理完成！输出目录: {self.output_picture_dir}")

def main():
    try:
        # base_dir = Path(__file__).parent.parent
        # output2_dir = base_dir / 'data_clean' / 'output2'
        # output_picture_dir = base_dir / 'data_clean' / 'output_picture'
                # 修正后
        base_dir = Path(__file__).parent
        output2_dir = base_dir / 'output2'           # 输入目录
        output_picture_dir = base_dir / 'output_picture'  # 输出目录
        
        logger.info("="*50)
        logger.info(f"开始处理图片分类")
        logger.info(f"输入目录: {output2_dir}")
        logger.info(f"输出目录: {output_picture_dir}")
        logger.info("="*50)
        
        if not output2_dir.exists():
            raise FileNotFoundError(f"输入目录不存在: {output2_dir}")
        
        # 清空输出目录
        if output_picture_dir.exists():
            logger.warning(f"清空现有输出目录: {output_picture_dir}")
            shutil.rmtree(output_picture_dir)
        
        processor = PictureProcessor(output2_dir, output_picture_dir)
        processor.run()
        logger.info("处理成功完成！")
    except Exception as e:
        logger.critical(f"程序运行时出错: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    main()