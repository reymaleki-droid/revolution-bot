#!/usr/bin/env python3
"""Fix ALL remaining indentation issues in handle_callback"""

def fix_all_nested_ifs():
    with open('bot.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    result = []
    in_callback = False
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Detect function boundaries
        if 'async def handle_callback' in line:
            in_callback = True
            result.append(line)
            continue
        
        if in_callback and line.startswith('async def ') and 'handle_callback' not in line:
            in_callback = False
            result.append(line)
            continue
        
        if not in_callback:
            result.append(line)
            continue
        
        # Inside handle_callback
        stripped = line.strip()
        
        if not stripped:
            result.append('\n')
            continue
        
        # Detect patterns that need fixing:
        # 1. "if <condition>:" at 8 spaces followed by content at 8 spaces (should be 12)
        # 2. "else:" at 4 spaces followed by elif (should be 8 spaces)
        
        # Check if previous line was "if" at 8 spaces and current line needs indent
        if len(result) > 0:
            prev_stripped = result[-1].strip()
            prev_indent = len(result[-1]) - len(result[-1].lstrip())
            
            # If previous was "if" at 8 spaces, current should be at least 12
            if prev_stripped.startswith('if ') and prev_indent == 8 and not stripped.startswith(('if', 'elif', 'else:', 'except')):
                if len(line) - len(stripped) < 12:
                    result.append('            ' + stripped + '\n')
                    continue
        
        result.append(line)
    
    with open('bot.py', 'w', encoding='utf-8') as f:
        f.writelines(result)
    
    print("Fixed nested ifs!")

if __name__ == '__main__':
    fix_all_nested_ifs()
