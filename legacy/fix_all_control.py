#!/usr/bin/env python3
"""Fix all for loops and if statements in handle_callback"""
import re

def fix_all_control_structures():
    with open('bot.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    result = []
    in_callback = False
    fix_next_n_lines = 0
    add_indent = 0
    
    for i, line in enumerate(lines):
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
        
        stripped = line.strip()
        current_indent = len(line) - len(stripped)
        
        if not stripped:
            result.append('\n')
            continue
        
        # Check if line is a control structure that needs following lines indented
        if re.match(r'^(if |for |while |try:|with |elif |else:)', stripped):
            result.append(line)
            # Next lines need more indent
            expected_next_indent = current_indent + 4
            
            # Look ahead and fix following lines
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                next_stripped = next_line.strip()
                next_indent = len(next_line) - len(next_stripped)
                
                if not next_stripped:
                    result.append('\n')
                    j += 1
                    continue
                
                # If it's another control structure at same or lower level, stop
                if re.match(r'^(if |elif |else:|except |finally:|for |while )', next_stripped) and next_indent <= current_indent:
                    break
                
                # If content has wrong indent, fix it
                if next_indent < expected_next_indent and not re.match(r'^(elif |else:|except |finally:)', next_stripped):
                    result.append(' ' * expected_next_indent + next_stripped + '\n')
                else:
                    result.append(next_line)
                
                j += 1
                
                # Stop after one statement group
                if re.match(r'^(if |elif |else:|for |while |def |class |async )', next_stripped):
                    break
            
            # Skip processed lines
            i = j - 1
            continue
        
        result.append(line)
    
    with open('bot.py', 'w', encoding='utf-8') as f:
        f.writelines(result)
    
    print("Fixed all control structures!")

if __name__ == '__main__':
    fix_all_control_structures()
