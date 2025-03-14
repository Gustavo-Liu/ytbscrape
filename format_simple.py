import os
import re

# 定义输入和输出文件路径
input_file = r'output\一口气了解AMD ｜ 别光盯着英伟达了~.txt'
output_file = r'output\一口气了解AMD_格式化.txt'

# 读取输入文件内容
with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 将空格替换为换行符
formatted_content = content.replace(' ', '\n')

# 写入格式化后的内容到输出文件
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(formatted_content)

print(f"文本已格式化并保存到 {output_file}") 