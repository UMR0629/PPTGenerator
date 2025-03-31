import re
from pathlib import Path
import shutil
import logging
from typing import Dict, List, Optional

class TitleProcessor:
    def __init__(self, output4_dir: Path, output5_dir: Path):
        self.output4_dir = output4_dir
        self.output5_dir = output5_dir
        self.groups: List[Dict] = []
        self.hierarchy: List[Dict] = []
        self.special_cases = {
        }

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('title_processor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def clean_title(self, title: str) -> str:
        title = title.strip()
        title = re.sub(r'[,，、]', '.', title)
        title = re.sub(r'\.{2,}', '.', title)
        title = re.sub(r'\s+', ' ', title)
        return title

    def parse_title(self, title_content: str) -> Dict[str, Optional[str]]:
        lines = [line.strip() for line in title_content.split('\n') if line.strip()]
        if not lines:
            self.logger.warning("空标题内容")
            return {'raw': '', 'level': None, 'cleaned': '', 'prefix': None}

        first_line = self.clean_title(lines[0])
        
        for wrong, correct in self.special_cases.items():
            if first_line.startswith(wrong):
                corrected = first_line.replace(wrong, correct, 1)
                self.logger.info(f"特殊案例修正: {first_line} → {corrected}")
                first_line = corrected
                break
        
        num_pattern = r'^((\d+)(\.\d+)*|Appendix [A-Z])([\.\s].*)?$'
        if match := re.match(num_pattern, first_line):
            prefix = match.group(1)
            level = prefix.count('.') + 1 if '.' in prefix else 1
            if 'Appendix' in prefix:
                level = 1
            return {
                'raw': first_line,
                'level': level,
                'cleaned': first_line,
                'prefix': prefix
            }
        
        if corrected := re.sub(r'(\d+)[,，](\d+)', r'\1.\2', first_line):
            if corrected != first_line:
                self.logger.info(f"格式修正: {first_line} → {corrected}")
                return {
                    'raw': first_line,
                    'level': corrected.count('.') + 1,
                    'cleaned': corrected,
                    'prefix': corrected.split()[0]
                }
        
        return {
            'raw': first_line,
            'level': None,
            'cleaned': first_line,
            'prefix': None
        }

    def is_same_parent(self, curr: str, prev: str) -> bool:
        if not (curr and prev):
            return False
            
        curr_parts = curr.split('.')
        prev_parts = prev.split('.')
        return (
            len(curr_parts) == len(prev_parts) and
            all(curr_parts[i] == prev_parts[i] for i in range(len(curr_parts)-1))
        )

    def calculate_expected_number(self, prev_prefix: str) -> Optional[str]:
        try:
            parts = prev_prefix.split('.')
            last_num = int(parts[-1])
            return '.'.join(parts[:-1] + [str(last_num + 1)])
        except (ValueError, IndexError):
            return None

    def correct_title(self, group: Dict, new_prefix: str) -> None:
        old_title = group['title_info']['cleaned']
        old_prefix = group['title_info']['prefix']
        
        if old_prefix and old_prefix in old_title:
            description = old_title[len(old_prefix):].lstrip('. ')
            new_title = f"{new_prefix}. {description}" if description else new_prefix
        else:
            new_title = f"{new_prefix}. {old_title}" if old_title else new_prefix
        
        group['title_info'].update({
            'cleaned': new_title,
            'prefix': new_prefix,
            'level': new_prefix.count('.') + 1
        })
        self.logger.warning(f"编号修正: {old_title} → {new_title}")

    def validate_sequence(self, current: Dict, prev: Dict) -> Optional[str]:
        curr_prefix = current.get('prefix')
        prev_prefix = prev.get('prefix')
        
        # 检查None值
        if curr_prefix is None or prev_prefix is None:
            return None
            
        # 情况1：严格同级标题检查
        if self.is_same_parent(curr_prefix, prev_prefix):
            if expected := self.calculate_expected_number(prev_prefix):
                try:
                    curr_num = int(curr_prefix.split('.')[-1])
                    expected_num = int(expected.split('.')[-1])
                    if curr_num != expected_num:
                        return expected
                except ValueError:
                    pass
        
        # 情况2：异常跳级修正
        elif '.' in prev_prefix:
            prev_parent = '.'.join(prev_prefix.split('.')[:-1])
            if curr_prefix and not curr_prefix.startswith(prev_parent):
                return self.calculate_expected_number(prev_prefix)
        
        return None

    def infer_hierarchy(self) -> None:
        if not self.groups:
            return
            
        if self.groups[0]['title_info']['level'] is None:
            self.groups[0]['title_info']['level'] = 1
        
        for i in range(1, len(self.groups)):
            curr, prev = self.groups[i], self.groups[i-1]
            
            if curr['title_info']['level'] is not None:
                continue
                
            if prev['title_info']['prefix']:
                curr_level = min(prev['title_info']['level'] + 1, 4)
                curr['title_info']['level'] = curr_level
                
                if expected := self.validate_sequence(curr['title_info'], prev['title_info']):
                    self.correct_title(curr, expected)
                elif curr['title_info']['prefix'] is None:
                    if expected := self.calculate_expected_number(prev['title_info']['prefix']):
                        self.correct_title(curr, expected)
            else:
                curr['title_info']['level'] = prev['title_info']['level']

    def process_groups(self) -> None:
        group_dirs = sorted(
            (d for d in (self.output4_dir / 'page_1').glob('group_*') if d.name != 'group_0'),
            key=lambda x: int(x.name.split('_')[-1])
        )
        
        for group_dir in group_dirs:
            if not (title_files := list(group_dir.glob('*title*'))):
                self.logger.warning(f"跳过 {group_dir.name}（无标题文件）")
                continue
                
            try:
                with open(title_files[0], 'r', encoding='utf-8') as f:
                    title_info = self.parse_title(f.read())
                
                self.groups.append({
                    'dir': group_dir,
                    'title_info': title_info,
                    'has_merged': (group_dir / 'merged_text.txt').exists()
                })
                self.logger.info(f"处理 {group_dir.name}: {title_info['cleaned']}")
            except Exception as e:
                self.logger.error(f"处理 {title_files[0]} 出错: {str(e)}")

        self.infer_hierarchy()
        self.hierarchy = self.groups.copy()

    def process_article_title(self) -> None:
        group_0_dir = self.output4_dir / 'page_1' / 'group_0'
        if not group_0_dir.exists():
            return
            
        if not (title_files := list(group_0_dir.glob('*title*'))):
            return
            
        article_dir = self.output5_dir / "文章标题"
        article_dir.mkdir(exist_ok=True)
        
        try:
            shutil.copy(title_files[0], article_dir / 'title.txt')
            if (merged_file := group_0_dir / 'merged_text.txt').exists():
                shutil.copy(merged_file, article_dir / 'merged_text.txt')
            self.logger.info(f"保存文章标题到: {article_dir}")
        except Exception as e:
            self.logger.error(f"处理文章标题出错: {str(e)}")

    def create_output_structure(self) -> None:
        level_dirs = {1: self.output5_dir}
        
        for group in self.hierarchy:
            info = group['title_info']
            parent = level_dirs.get(info['level'] - 1, self.output5_dir)
            
            safe_name = re.sub(r'[\\/*?:"<>|]', '_', info['cleaned'])
            current_dir = parent / safe_name
            
            try:
                current_dir.mkdir(exist_ok=True)
                self.logger.info(f"创建目录: {current_dir} (层级 {info['level']})")
                
                shutil.copy(next(group['dir'].glob('*title*')), current_dir / 'title.txt')
                if group['has_merged']:
                    shutil.copy(group['dir'] / 'merged_text.txt', current_dir / 'merged_text.txt')
                
                level_dirs[info['level']] = current_dir
                for l in range(info['level'] + 1, 5):
                    level_dirs.pop(l, None)
            except Exception as e:
                self.logger.error(f"创建目录失败: {current_dir} - {str(e)}")

    def run(self) -> None:
        self.logger.info(f"开始处理目录: {self.output4_dir}")
        self.output5_dir.mkdir(exist_ok=True, parents=True)
        
        if self.output5_dir.exists():
            self.logger.warning("清空输出目录")
            shutil.rmtree(self.output5_dir)
            self.output5_dir.mkdir()
        
        self.process_article_title()
        self.process_groups()
        self.create_output_structure()
        self.logger.info(f"处理完成！输出目录: {self.output5_dir}")

def main():
    try:
        base_dir = Path(__file__).parent.parent
        processor = TitleProcessor(
            output4_dir=base_dir / 'data_clean' / 'output4',
            output5_dir=base_dir / 'data_clean' / 'output5'
        )
        processor.run()
    except Exception as e:
        logging.critical(f"程序运行失败: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    main()