#!/usr/bin/env python3
"""Fix indentation - add 4 spaces to all lines between elif and next elif/else in handle_callback"""
import re

def fix_bot_indentation():
    with open('bot.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    fixed_lines = []
    in_handle_callback = False
    in_elif_block = False
    elif_indent_level = 0
    
    for i, line in enumerate(lines):
        # Detect start of handle_callback
        if 'async def handle_callback' in line:
            in_handle_callback = True
            fixed_lines.append(line)
            continue
        
        # Detect end of handle_callback
        if in_handle_callback and re.match(r'^async def ', line) and 'handle_callback' not in line:
            in_handle_callback = False
        
        if in_handle_callback:
            # Check if this is an elif line at the wrong indentation
            if re.match(r'^    elif ', line):
                # This elif needs to become '        elif '
                fixed_lines.append('    ' + line)
                in_elif_block = True
                elif_indent_level = 8  # Should be 8 spaces
            # Check if this is the next elif or else or except
            elif re.match(r'^        elif |^        else:|^    except ', line):
                in_elif_block = False
                fixed_lines.append(line)
            # Check if we're in an elif block and line starts with wrong indentation
            elif in_elif_block and line.startswith('    ') and not line.startswith('        '):
                # Add 4 spaces
                fixed_lines.append('    ' + line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    with open('bot.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))
    
    print("Fixed!")

if __name__ == '__main__':
    fix_bot_indentation()
