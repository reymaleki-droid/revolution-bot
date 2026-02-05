#!/usr/bin/env python3
"""Fix indentation in handle_callback function"""

def fix_indentation():
    with open('bot.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the handle_callback function (starts around line 520)
    in_handle_callback = False
    fixed_lines = []
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Detect start of handle_callback
        if 'async def handle_callback' in line:
            in_handle_callback = True
            fixed_lines.append(line)
            continue
        
        # Detect end of handle_callback (next function definition)
        if in_handle_callback and line.startswith('async def ') and 'handle_callback' not in line:
            in_handle_callback = False
            fixed_lines.append(line)
            continue
        
        # Fix indentation within handle_callback
        if in_handle_callback:
            # Lines that should be indented after try:
            if line.startswith('    elif data'):
                # Add 4 spaces
                fixed_lines.append('    ' + line)
            elif line.startswith('    # ') and 'Email campaign' in line or 'Conduit' in line or 'Manual' in line:
                # Comments at same level as elif
                fixed_lines.append('    ' + line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    with open('bot.py', 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("Fixed indentation!")

if __name__ == '__main__':
    fix_indentation()
