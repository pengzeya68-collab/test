import re

with open('generate_lp15_18.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed_lines = []
for line in lines:
    stripped = line.strip()
    # Only process lines that are part of the exercise tuples
    if stripped.startswith('("') and '?' in stripped:
        # Count quotes
        quote_count = stripped.count('"')
        if quote_count > 2:
            # This line has inner quotes that conflict with Python string boundary
            # Replace all inner "text" patterns with 'text'
            # Strategy: replace pairs of quotes around words with single quotes
            line = re.sub(r'"([^"\n]{1,30})"', r"'\1'", line)
    fixed_lines.append(line)

with open('generate_lp15_18.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print('Fixed inner quotes')
