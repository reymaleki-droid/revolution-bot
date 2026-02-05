#!/usr/bin/env python3
"""Properly restore handle_callback function indentation"""
import re

def restore_indentation():
    with open('bot.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    result = []
    in_callback = False
    skip_until_function = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Find handle_callback function
        if 'async def handle_callback' in line:
            in_callback = True
            result.append(line)
            i += 1
            
            # Add docstring
            if i < len(lines) and '"""' in lines[i]:
                result.append(lines[i])
                i += 1
            
            # Add the initial lines (query, user, data)
            result.append('    query = update.callback_query\n')
            result.append('    await query.answer()\n')
            result.append('    \n')
            result.append('    user = update.effective_user\n')
            result.append('    data = query.data\n')
            result.append('    \n')
            
            # Skip any malformed lines until we hit if/elif
            while i < len(lines) and not (lines[i].strip().startswith('if data ==') or lines[i].strip().startswith('elif data')):
                i += 1
            
            continue
        
        # Detect end of handle_callback
        if in_callback and re.match(r'^async def |^def ', line) and 'handle_callback' not in line:
            in_callback = False
            result.append(line)
            i += 1
            continue
        
        if not in_callback:
            result.append(line)
            i += 1
            continue
        
        # Inside handle_callback - fix structure
        stripped = line.strip()
        
        if not stripped:
            result.append('\n')
            i += 1
            continue
        
        # if/elif/else at wrong level
        if stripped.startswith('if data ==') or stripped.startswith('elif data') or stripped == 'else:':
            result.append('    ' + stripped + '\n')
            i += 1
            continue
        
        # Comments
        if stripped.startswith('#'):
            # Block-level comments (before elif)
            if any(x in stripped for x in ['Email campaign', 'Conduit', 'Manual tier']):
                result.append('    ' + stripped + '\n')
            else:
                result.append('        ' + stripped + '\n')
            i += 1
            continue
        
        # All other content should be indented at 8 spaces
        result.append('        ' + stripped + '\n')
        i += 1
    
    with open('bot.py', 'w', encoding='utf-8') as f:
        f.writelines(result)
    
    print("Restored!")

if __name__ == '__main__':
    restore_indentation()
