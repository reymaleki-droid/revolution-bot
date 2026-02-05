#!/usr/bin/env python3
"""
Comprehensive fix for handle_callback indentation.
This script will ensure all if/elif blocks have consistent 4-space indentation
and their content blocks have 8-space indentation.
"""

def fix_callback_indentation():
    with open('bot.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    in_callback = False
    current_block_indent = 0
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Detect function start
        if 'async def handle_callback' in line:
            in_callback = True
            fixed_lines.append(line)
            continue
        
        # Detect function end
        if in_callback and (line.startswith('async def ') or line.startswith('def ')) and 'handle_callback' not in line:
            in_callback = False
            fixed_lines.append(line)
            continue
        
        if not in_callback:
            fixed_lines.append(line)
            continue
        
        # Inside handle_callback
        stripped = line.strip()
        
        # Skip blank lines
        if not stripped:
            fixed_lines.append('\n')
            continue
        
        # Lines that should be at 4-space indent
        if any(stripped.startswith(x) for x in ['query = ', 'await query.answer()', 'user = ', 'data = ']):
            fixed_lines.append('    ' + stripped + '\n')
            continue
        
        # if/elif/else blocks should be at 4-space indent
        if stripped.startswith('if data ==') or stripped.startswith('elif data') or (stripped == 'else:' and current_block_indent == 0):
            fixed_lines.append('    ' + stripped + '\n')
            current_block_indent = 8
            continue
        
        # Comments at block level
        if stripped.startswith('#'):
            # Check if it's a block-level comment
            if 'Email campaign' in stripped or 'Conduit' in stripped or 'Manual' in stripped:
                fixed_lines.append('    ' + stripped + '\n')
            else:
                # Content-level comment
                fixed_lines.append('        ' + stripped + '\n')
            continue
        
        # Everything else should be at 8-space indent (content of if/elif blocks)
        fixed_lines.append('        ' + stripped + '\n')
    
    with open('bot.py', 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("Fixed all indentation!")

if __name__ == '__main__':
    fix_callback_indentation()
