#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""检查emoji库中的重复项"""

import re
from collections import Counter

# 读取文件内容
with open('constants.py', 'r', encoding='utf-8') as f:
    content = f.readlines()

# 找到AVAILABLE_STATUSBAR_ICONS列表的开始和结束
start_line = 0
end_line = 0
for i, line in enumerate(content):
    if 'AVAILABLE_STATUSBAR_ICONS = [' in line:
        start_line = i
    if ']' in line and i > start_line and end_line == 0:
        end_line = i
        break

# 提取所有emoji及其位置
emojis = []
emoji_positions = {}
line_offset = 0

for i in range(start_line + 1, end_line + 1):
    line = content[i]
    matches = re.findall(r'"([^"]+)"', line)
    for emoji in matches:
        emojis.append(emoji)
        if emoji not in emoji_positions:
            emoji_positions[emoji] = []
        emoji_positions[emoji].append((i, line_offset))
        line_offset += 1

# 找出重复项
counter = Counter(emojis)
duplicates = [emoji for emoji, count in counter.items() if count > 1]

# 将结果写入文件
with open('duplicate_emojis_report.txt', 'w', encoding='utf-8') as f:
    if duplicates:
        # 得到一个唯一的名称给每个emoji，避免编码问题
        emoji_names = {}
        for idx, emoji in enumerate(duplicates):
            emoji_names[emoji] = f"EMOJI_{idx+1}"
        
        f.write(f"找到 {len(duplicates)} 个重复的emoji:\n")
        for emoji in duplicates:
            positions = emoji_positions[emoji]
            positions_str = ", ".join([f"第{pos[0]+1}行第{pos[1]+1}个" for pos in positions])
            f.write(f"  {emoji_names[emoji]}: 出现 {counter[emoji]} 次，位置: {positions_str}\n")
        
        # 输出emoji名称对照表
        f.write("\nEmoji对照表:\n")
        for emoji, name in emoji_names.items():
            unicode_points = ' '.join([f'U+{ord(c):04X}' for c in emoji])
            f.write(f"  {name}: Unicode码位: {unicode_points}\n")
    else:
        f.write("没有找到重复的emoji\n")

print("分析完成，结果已保存到 duplicate_emojis_report.txt 文件中") 