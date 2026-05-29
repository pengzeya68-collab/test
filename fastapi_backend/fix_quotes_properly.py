"""
修复 generate_lp15_18.py 中的引号问题
将字符串内部的 ASCII 双引号替换为单引号
"""

import re

file_path = r"C:\Users\lenovo\Desktop\TestMasterProject\fastapi_backend\generate_lp15_18.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 查找所有在字符串内部的 ASCII 双引号对
# 模式：中文字符之间的 "xxx" 应该改为 'xxx'
# 例如："一对多" -> '一对多'

# 使用正则表达式找到所有被ASCII双引号包裹的中文字符串
# 这些在Python字符串内部会导致语法错误
pattern = r'(\u4e00-\u9fff\u3000-\u303f\uff00-\uffef)"(.+?)"(\u4e00-\u9fff\u3000-\u303f\uff00-\uffef)'
# 更简单的做法：直接查找 "中文字符" 模式（在字符串内部的）
# 实际问题是：在Python源代码中，字符串用"..."定义，但内部也用了"..."

# 让我用更直接的方法：找到所有形如：中文字符" 或 "' 的模式
# 在Python字符串中，内部的引号应该转义或用单引号

# 简单粗暴但有效的方法：
# 1. 找到所有 ("....", 这样的行
# 2. 将其中的 "文本" 替换为 '文本'

# 更好的方法：使用正则表达式匹配中文标点后的英文引号
fixes = [
    # 格式：中文标点/文字 + " + 内容 + " + 中文标点/文字
    (
        r'([，。、；：？！\u4e00-\u9fff])"([^"]+)"([，。、；：？！\u4e00-\u9fff])',
        r"\1'\2'\3",
    ),
]

original = content
for pattern, replacement in fixes:
    new_content = re.sub(pattern, replacement, content)
    if new_content != content:
        print(f"应用修复: {pattern[:50]}...")
        content = new_content

# 如果上面的正则没匹配到，手动指定需要修复的位置
# 让我直接查找所有有问题的模式
print("\n查找问题行...")
lines = content.split("\n")
fixed_lines = []
for i, line in enumerate(lines):
    # 检查行中是否有 "中文字" 模式（在字符串内部使用双引号）
    if '"' in line:
        # 计算行中有多少個 "
        quote_count = line.count('"')
        if quote_count >= 4:  # 至少有2对引号
            # 这可能是问题行
            # 尝试修复：将第2个和第倒数第2个引号改为单引号
            parts = line.split('"')
            if len(parts) >= 5:  # 至少3对引号（包括字符串定界符）
                # 保留第一个和最后一个引号（字符串定界符）
                # 将中间的引号对改为单引号
                new_line = parts[0] + '"' + parts[1] + "'"
                for j in range(2, len(parts) - 2, 2):
                    new_line += parts[j] + "'" + parts[j + 1] + "'"
                new_line += parts[-2] + '"' + parts[-1]
                if new_line != line:
                    print(f"  行 {i + 1}: 可能已修复")
                    print(f"    原始: {line[:80]}...")
                    print(f"    修复: {new_line[:80]}...")
                    line = new_line
    fixed_lines.append(line)

content = "\n".join(fixed_lines)

# 写回文件
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n已保存: {file_path}")

# 验证语法
import subprocess

result = subprocess.run(["python", "-m", "py_compile", file_path], capture_output=True, text=True)
if result.returncode == 0:
    print("✅ 语法检查通过！")
else:
    print("❌ 仍有语法错误:")
    print(result.stderr[:500])
