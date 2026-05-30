with open("generate_lp15_18.py", "r", encoding="utf-8") as f:
    content = f.read()

# 替换中文引号为英文单引号
content = content.replace("\u201c", "'").replace("\u201d", "'")

with open("generate_lp15_18.py", "w", encoding="utf-8") as f:
    f.write(content)

print("中文引号已替换")
