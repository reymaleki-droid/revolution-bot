#!/usr/bin/env python3
"""Properly fix indentation in handle_callback function"""
import re

def fix_handle_callback():
    with open('bot.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    result = []
    
    in_function = False
    in_try_block = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Detect function start
        if 'async def handle_callback' in line:
            in_function = True
            result.append(line)
            i += 1
            continue
        
        # Detect function end
        if in_function and re.match(r'^async def ', line) and 'handle_callback' not in line:
            in_function = False
            result.append(line)
            i += 1
            continue
        
        if not in_function:
            result.append(line)
            i += 1
            continue
        
        # Within handle_callback function
        # The structure should be:
        # try:
        #     if/elif blocks (each with 8 spaces)
        #         content (each with 12 spaces or more)
        # except:
        #     error handling
        
        stripped = line.lstrip()
        indent_count = len(line) - len(stripped)
        
        # Skip query.answer() and try: lines (should have 4 spaces)
        if stripped.startswith('query = ') or stripped.startswith('await query.answer()') or stripped.startswith('try:') or stripped.startswith('user = ') or stripped.startswith('data = '):
            result.append(line)
            i += 1
            continue
        
        # if/elif/else at wrong indent (should be 8 spaces inside try block)
        if (stripped.startswith('if data ==') or stripped.startswith('elif data') or (stripped == 'else:' and in_function)):
            if indent_count == 4:
                result.append('    ' + line)  # Add 4 more spaces
            else:
                result.append(line)
            i += 1
            continue
        
        # except block (should be 4 spaces, closing the try)
        if stripped.startswith('except '):
            result.append(line if indent_count == 4 else '    ' + stripped)
            i += 1
            continue
        
        # Everything else inside try block needs proper indentation
        # Content inside if/elif blocks should have at least 12 spaces
        if in_function and indent_count < 8 and indent_count > 0 and not line.strip() == '':
            # This line needs more indent
            result.append('        ' + stripped)  # Make it 8+ spaces
        else:
            result.append(line)
        
        i += 1
    
    with open('bot_fixed.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(result))
    
    print("Created bot_fixed.py!")

if __name__ == '__main__':
    fix_handle_callback()
