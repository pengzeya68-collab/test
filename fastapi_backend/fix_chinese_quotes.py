"""
修复 generate_lp15_18.py 中的中文引号问题
将中文引号 ""'' 替换为英文引号
"""
import re

file_path = r'C:\Users\lenovo\Desktop\TestMasterProject\fastapi_backend\generate_lp15_18.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换中文引号为英文单引号
# 中文双引号 "" -> 英文单引号 ''
fixes = [
    ('\u201c', "'"),  # 左双引号 -> 单引号
    ('\u201d', "'"),  # 右双引号 -> 单引号
    ('\u2018', "'"),  # 左单引号 -> 单引号
    ('\u2019', "'"),  # 右单引号 -> 单引号
]

original_len = len(content)
for old, new in fixes:
    content = content.replace(old, new)

fixed_len = len(content)
print(f'原始字符数: {original_len}')
print(f'修复后字符数: {fixed_len}')
print(f'替换次数检查:')

# 检查是否还有中文引号
remaining = []
for char, name in [('\u201c', '左双引号'), ('\u201d', '右双引号'), 
                    ('\u2018', '左单引号'), ('\u2019', '右单引号')]:
    count = content.count(char)
    if count > 0:
        remaining.append(f'{name}: {count}处')
        
if remaining:
    print(f'还剩: {", ".join(remaining)}')
else:
    print('已全部修复！')

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\n已修复并保存: {file_path}')
print('现在尝试编译检查...')

import subprocess
result = subprocess.run(
    ['python', '-m', 'py_compile', file_path],
    capture_output=True,
    text=True
)
if result.returncode == 0:
    print('✅ 语法检查通过！')
else:
    print('❌ 仍有语法错误:')
    print(result.stderr)
