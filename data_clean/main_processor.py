import subprocess
from pathlib import Path
import sys

# 导入 storedata.py 中的函数
from storedata import store_paper_data

def run_script(script_name):
    """更健壮的脚本执行函数"""
    script_path = Path(__file__).parent / script_name
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'  # 替换无法解码的字符
        )
        return True
    except subprocess.CalledProcessError as e:
        # 尝试多种编码方式读取错误信息
        for encoding in ['utf-8', 'gbk', 'latin1']:
            try:
                error_msg = e.stderr.decode(encoding)
                print(f"❌ 执行失败: {script_name}\n错误信息:\n{error_msg}")
                break
            except:
                continue
        else:
            print(f"❌ 执行失败: {script_name}\n无法解码的错误输出")
        return False

def main():
    print("=== 开始处理数据 ===")
    
    steps = [
        "storedata_dataclean.py",
        "storedata_datacombine.py",
        "picture_classify.py",
        "picture_classify2.py",
        "title_classify.py"
    ]

    for script in steps:
        print(f"\n▶ 正在执行: {script}")
        if not run_script(script):
            print("❗ 处理中断！")
            return

    print("\n▶ 正在执行: storedata.py")
    # 获取 storedata.py 的输出目录路径
    base_dir = Path(__file__).parent
    output5_dir = base_dir / "output5"
    output_picture0_dir = base_dir / "output_picture0"

    # 调用 storedata.py 中的 store_paper_data 函数
    paper_info = store_paper_data(output5_dir, output_picture0_dir)

    if paper_info:
        print("\n✅ 所有处理步骤已完成")
        print("\n=== 最终处理结果 ===")
        print("=== 论文大纲 ===")
        paper_info.display_outline()

        print("\n=== 图片信息 ===")
        for img in paper_info.image_list:
            print(f"图片编号: {img['number']}")
            print(f"路径: {img['path']}")
            print(f"描述: {img['description']}")
            print("-" * 40)
    else:
        print("❌ storedata.py 未成功返回论文信息。")

if __name__ == "__main__":
    main()