import re
with open('frontend/src/views/JmeterAssistant.vue', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

VOID_TAGS = {'br','hr','img','input','meta','link','col','area','base','embed','source','track','wbr'}
skip_tags = {'p','strong','small','b','code','pre','span','label','a','table','tr','td','th','thead','tbody'}

in_template = False
stack = []

for i, line in enumerate(lines, 1):
    s = line.strip()
    if s == '<template>':
        in_template = True
        continue
    if s == '</template>':
        break
    if not in_template:
        continue

    for m in re.finditer(r'<(/?)([a-zA-Z][\w-]*)', line):
        is_close = m.group(1) == '/'
        tag = m.group(2)
        if tag in VOID_TAGS:
            continue
        if tag in skip_tags:
            continue

        after = line[m.end():]
        gt_pos = after.find('>')
        if not is_close and gt_pos >= 0 and after[:gt_pos+1].rstrip().endswith('/'):
            continue

        if is_close:
            if stack and stack[-1][1] == tag:
                stack.pop()
            else:
                exp = stack[-1] if stack else ('?','?')
                print(f'L{i}: MISMATCH </{tag}>, expected </{exp[1]}> (opened L{exp[0]})')
        else:
            stack.append((i, tag))

if stack:
    print(f'\nUnclosed tags ({len(stack)}):')
    for ln, tag in stack:
        print(f'  <{tag}> opened at L{ln}')
else:
    print('All tags matched!')
