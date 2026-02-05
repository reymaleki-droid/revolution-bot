#!/usr/bin/env python3
"""Fix all indentation in handle_callback - add 4 spaces to lines that need it"""

def fix_indentation():
    with open('bot.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Lines 560 to 1110 need indentation fixes
    # Rules:
    # - Lines starting with '    ' (4 spaces) but not '        elif ' or '        else:' need +4 spaces
    # - Lines starting with '        elif ' stay as is
    # - Lines starting with '        else:' stay as is  
    # - Everything else in that range gets +4 spaces if it starts with exactly 4 spaces
    
    fixed_lines = []
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Only fix lines 560-1115 (handle_callback function body)
        if 560 <= line_num <= 1115:
            # Skip lines that are already correctly indented (8+ spaces or blank)
            if line.startswith('        ') or line.strip() == '':
                fixed_lines.append(line)
            # Lines that start with exactly 4 spaces need +4
            elif line.startswith('    ') and not line.startswith('        '):
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
