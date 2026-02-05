#!/usr/bin/env python3
"""Fix indentation by parsing Python AST-like structure"""
import re

def smart_indent_fix():
    with open('bot.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    result = []
    in_callback = False
    current_indent = 0
    
    for i, line in enumerate(lines):
        # Detect function start
        if 'async def handle_callback' in line:
            in_callback = True
            result.append(line)
            continue
        
        # Detect function end
        if in_callback and re.match(r'^(async )?def ', line) and 'handle_callback' not in line:
            in_callback = False
            result.append(line)
            continue
        
        if not in_callback:
            result.append(line)
            continue
        
        stripped = line.strip()
        if not stripped:
            result.append('\n')
            continue
        
        # Docstring
        if '"""' in stripped and result and 'handle_callback' in result[-1]:
            result.append('    ' + stripped + '\n')
            continue
        
        # Initial setup lines
        if stripped in ['query = update.callback_query', 'await query.answer()', 'user = update.effective_user', 'data = query.data']:
            result.append('    ' + stripped + '\n')
            current_indent = 4
            continue
        
        # Top-level if/elif/else
        if re.match(r'^(if|elif) data\s*(==|\.startswith)', stripped) or (stripped == 'else:' and current_indent <= 8):
            result.append('    ' + stripped + '\n')
            current_indent = 8
            continue
        
        # Nested if/elif/else
        if re.match(r'^(if|elif) ', stripped) and 'data' not in stripped:
            result.append('        ' + stripped + '\n')
            current_indent = 12
            continue
        
        if stripped == 'else:' and current_indent >= 12:
            result.append('        ' + stripped + '\n')
            current_indent = 12
            continue
        
        # Block-level comments
        if stripped.startswith('#') and any(x in stripped for x in ['Email campaign', 'Conduit', 'Manual', 'User']):
            result.append('    ' + stripped + '\n')
            continue
        
        # Regular content - use current indent level
        if current_indent == 4:
            result.append('    ' + stripped + '\n')
        elif current_indent == 8:
            result.append('        ' + stripped + '\n')
        elif current_indent == 12:
            result.append('            ' + stripped + '\n')
        else:
            result.append('        ' + stripped + '\n')  # Default to 8
    
    with open('bot.py', 'w', encoding='utf-8') as f:
        f.writelines(result)
    
    print("Fixed with smart indentation!")

if __name__ == '__main__':
    smart_indent_fix()
