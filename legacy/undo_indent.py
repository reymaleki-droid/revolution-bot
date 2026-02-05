#!/usr/bin/env python3
"""Remove extra indentation added to handle_callback"""

def fix():
    with open('bot.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    in_function = False
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Detect start
        if 'async def handle_callback' in line:
            in_function = True
            fixed_lines.append(line)
            continue
        
        # Detect end
        if in_function and line.startswith('async def ') and 'handle_callback' not in line:
            in_function = False
            fixed_lines.append(line)
            continue
        
        # Remove extra 4 spaces from lines 529-1120
        if in_function and 529 <= line_num <= 1120:
            # Remove 4 spaces from lines that have 8 or more spaces
            if line.startswith('        '):
                fixed_lines.append(line[4:])
            elif line.startswith('    except '):
                # Skip except block lines
                continue
            elif 'except Exception as e:' in line:
                continue
            elif 'logger.error(f"Error in handle_callback' in line:
                continue
            elif line.strip().startswith('await query.answer("⚠️') and 'show_alert=True' in line and line_num > 1110:
                continue
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    with open('bot.py', 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("Fixed!")

if __name__ == '__main__':
    fix()
