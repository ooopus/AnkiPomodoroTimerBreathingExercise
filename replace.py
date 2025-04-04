import os
import re
import argparse
import logging

# 配置日志记录
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# 定义要查找和替换的模式
# 使用正则表达式捕获函数名、括号、字符串内容以及其他参数
# 正则表达式解释:
# (tooltip|QLabel)   : 捕获 "tooltip" 或 "QLabel" (组 1)
# \(\s*              : 匹配左括号和可选的空格
# (["'])             : 捕获开始的引号（单引号或双引号）(组 2)
# ((?:(?!\2).)*)     : 非贪婪地捕获引号内的所有内容，直到遇到相同的结束引号 (组 3)
#                     (?:...) : 非捕获组
#                     (?!\2)  : 负向前瞻，确保不是匹配之前捕获的那个引号
#                     .       : 匹配任何字符
#                     *       : 匹配零次或多次
# \2                 : 匹配与组 2 相同的结束引号
# (\s*,\s*.*?)?      : 可选地捕获逗号、可选空格和后面的任何参数（非贪婪）(组 4)
# \s*\)              : 匹配可选的空格和右括号
#
# 替换字符串解释:
# \1                 : 第一个捕获组 (函数名)
# _(\2\3\2)          : 将捕获的引号和内容包裹在 _() 中
# \4                 : 第四个捕获组 (逗号和后面的参数，如果存在)
# )                  : 添加结束括号
PATTERN = re.compile(
    r'(tooltip|QLabel|QAction|QGroupBox)\(\s*(["\'])((?:(?!\2).)*)\2(\s*,\s*.*?)?\s*\)'
)
REPLACEMENT = r"\1(_(\2\3\2)\4)"

# 另一种写法，可能更清晰地分离参数捕获
# PATTERN = re.compile(r'(tooltip|QLabel)\(\s*(["\'])((?:(?!\2).)*)\2(\s*(?:,.*)?)(\))')
# REPLACEMENT = r'\1(_(\2\3\2)\4\5' # \4 包含逗号和参数, \5 是右括号


def process_file(filepath):
    """处理单个文件，查找并替换模式"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            original_content = f.read()
    except Exception as e:
        logging.error(f"无法读取文件 {filepath}: {e}")
        return

    modified_content, num_replacements = PATTERN.subn(REPLACEMENT, original_content)

    if num_replacements > 0:
        logging.info(f"正在修改文件: {filepath} ({num_replacements} 个替换)")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(modified_content)
        except Exception as e:
            logging.error(f"无法写入文件 {filepath}: {e}")
            # 考虑是否要恢复原文件（如果需要更安全的操作）
    # else: # 如果需要，可以取消注释以查看未修改的文件
    #     logging.debug(f"文件无需修改: {filepath}")


def process_directory(root_dir):
    """递归处理目录下的所有 .py 文件"""
    if not os.path.isdir(root_dir):
        logging.error(f"错误：目录 '{root_dir}' 不存在或不是一个有效的目录。")
        return

    logging.info(f"开始处理目录: {root_dir}")
    file_count = 0
    processed_count = 0

    for subdir, _, files in os.walk(root_dir):
        for filename in files:
            if filename.lower().endswith(".py"):
                file_count += 1
                filepath = os.path.join(subdir, filename)
                process_file(filepath)
                processed_count += 1  # 无论是否修改都计数

    logging.info(f"处理完成。共检查 {processed_count} 个 .py 文件。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="递归地将特定函数调用中的字符串参数用 _() 包裹起来，用于 i18n。",
        epilog="示例: python replace_script.py /path/to/your/project",
    )
    parser.add_argument("directory", help="需要处理的根目录路径。")

    args = parser.parse_args()

    # 在开始前再次提醒备份
    print("=" * 50)
    print("警告：此脚本将直接修改您指定目录下的 .py 文件。")
    print("请确保您已经备份了相关代码！")
    print("=" * 50)
    confirm = input(f"您确定要处理目录 '{args.directory}' 吗？(yes/no): ")

    if confirm.lower() == "yes":
        process_directory(args.directory)
    else:
        print("操作已取消。")
