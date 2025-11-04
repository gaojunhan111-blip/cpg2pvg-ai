#!/usr/bin/env python3
"""
Fix Long Lines Script
自动修复长行问题的脚本
"""

import os
import re
from pathlib import Path

def fix_long_lines_in_file(file_path: str) -> int:
    """修复文件中的长行"""
    fixed_count = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()

        new_lines = []

        for line_num, line in enumerate(lines, 1):
            if len(line) > 120:
                # 尝试修复长行
                fixed_line = fix_single_line(line)
                if fixed_line != line:
                    new_lines.extend(fixed_line)
                    fixed_count += 1
                    print(f"  Fixed line {line_num}: {len(line)} -> {sum(len(l) for l in fixed_line)} chars")
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        if fixed_count > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

    return fixed_count

def fix_single_line(line: str) -> list:
    """修复单行长行"""

    # 模式1: 函数定义长行
    if 'def ' in line and '(' in line and ')' in line:
        return fix_function_definition_line(line)

    # 模式2: 列表/字典/集合推导式长行
    if ('[' in line and ']' in line) or ('{' in line and '}' in line):
        return fix_comprehension_line(line)

    # 模式3: 长的字符串连接
    if (' "' in line or " '" in line) and ('+"' in line or '"+ ' in line):
        return fix_string_concatenation_line(line)

    # 模式4: 长的条件表达式
    if ' and ' in line or ' or ' in line:
        return fix_conditional_line(line)

    # 模式5: 长的链式调用
    if '.(' in line and line.count('.(') > 1:
        return fix_method_chain_line(line)

    # 模式6: 长的列表内容
    if '[' in line and ']' in line and line.count(',') > 2:
        return fix_long_list_line(line)

    # 如果没有匹配到模式，返回原行
    return [line]

def fix_function_definition_line(line: str) -> list:
    """修复函数定义长行"""
    indent = len(line) - len(line.lstrip())

    # 分割函数定义
    if 'def ' in line and '(' in line:
        func_start = line.index('def ')
        paren_start = line.index('(')
        paren_end = line.rfind(')')

        func_name = line[func_start:paren_start]
        params = line[paren_start+1:paren_end]
        return_part = line[paren_end+1:]

        # 如果参数很多，分行
        if ',' in params and len(line) > 120:
            indent_str = ' ' * (indent + 4)

            result = [
                line[:paren_start+1],
                indent_str + params,
                ')' + return_part
            ]
            return result

    return [line]

def fix_comprehension_line(line: str) -> list:
    """修复推导式长行"""
    indent = len(line) - len(line.lstrip())
    indent_str = ' ' * (indent + 4)

    # 简单的推导式分行
    if '[' in line and ' for ' in line and ' in ' in line:
        if line.count(',') > 2:  # 多个元素
            # 分割元素
            elements_part = line[line.index('[')+1:line.rfind(']')]
            for_part = ''
            if ' for ' in elements_part:
                for_idx = elements_part.rfind(' for ')
                for_part = elements_part[for_idx:]
                elements_part = elements_part[:for_idx]

            elements = [e.strip() for e in elements_part.split(',')]

            result = [
                line[:line.index('[')] + '[',
                indent_str + ',\n'.join(elements),
                indent_str + ']' + for_part
            ]
            return result

    return [line]

def fix_string_concatenation_line(line: str) -> list:
    """修复字符串连接长行"""
    # 简单的字符串连接分行
    if '"+' in line or '" +' in line or "'+" in line:
        # 简单的字符串分割
        if '"+' in line:
            parts = line.split('+"')
        elif '" +' in line:
            parts = line.split('" +')
        elif "'+" in line:
            parts = line.split("'+"")"
        else:
            parts = [line]
        if len(parts) > 1:
            indent = len(line) - len(line.lstrip())
            indent_str = ' ' * (indent + 4)

            result = []
            for i, part in enumerate(parts):
                part = part.strip()
                if part:
                    if i == 0:
                        result.append(part)
                    else:
                        result.append(indent_str + part)
                    if i < len(parts) - 1:
                        result[-1] += ' +'

            return result

    return [line]

def fix_conditional_line(line: str) -> list:
    """修复条件表达式长行"""
    # 简单的条件分行
    if ' and ' in line:
        parts = line.split(' and ')
        if len(parts) > 1:
            indent = len(line) - len(line.lstrip())
            indent_str = ' ' * (indent + 4)

            result = [parts[0]]
            for part in parts[1:]:
                result.append(indent_str + 'and ' + part.strip())
            return result

    if ' or ' in line:
        parts = line.split(' or ')
        if len(parts) > 1:
            indent = len(line) - len(line.lstrip())
            indent_str = ' ' * (indent + 4)

            result = [parts[0]]
            for part in parts[1:]:
                result.append(indent_str + 'or ' + part.strip())
            return result

    return [line]

def fix_method_chain_line(line: str) -> list:
    """修复方法链长行"""
    # 简单的方法链分行
    if '.(' in line:
        indent = len(line) - len(line.lstrip())
        indent_str = ' ' * (indent + 4)

        # 找到第一个'.'后的位置
        first_dot = line.find('.')
        if first_dot > 0:
            base = line[:first_dot]
            methods = line[first_dot:]

            # 分割方法调用
            method_parts = []
            current = methods
            depth = 0
            start = 0

            for i, char in enumerate(current):
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                elif char == '.' and depth == 0:
                    method_parts.append(current[start:i])
                    start = i

            if start < len(current):
                method_parts.append(current[start:])

            if len(method_parts) > 2:
                result = [base]
                for i, part in enumerate(method_parts):
                    if i == 0:
                        result[-1] += part
                    else:
                        result.append(indent_str + part.lstrip())
                return result

    return [line]

def fix_long_list_line(line: str) -> list:
    """修复长列表行"""
    # 简单的列表分行
    if '[' in line and ']' in line:
        content_start = line.index('[') + 1
        content_end = line.rfind(']')

        if content_start < content_end:
            content = line[content_start:content_end]
            elements = [e.strip() for e in content.split(',')]

            if len(elements) > 3:
                indent = len(line) - len(line.lstrip())
                indent_str = ' ' * (indent + 4)

                result = [
                    line[:content_start] + '[',
                    indent_str + ',\n'.join(elements),
                    indent_str + ']' + line[content_end+1:]
                ]
                return result

    return [line]

def main():
    """主函数"""
    print("AUTO FIX LONG LINES")
    print("=" * 40)

    # 要修复的文件
    files_to_fix = [
        'app/services/knowledge_graph.py',
        'app/services/multimodal_processor.py',
        'app/services/medical_parser.py',
        'app/models/knowledge_graph.py',
        'app/models/multimodal_content.py',
        'app/models/medical_document.py',
        'celery_worker/workflow_nodes/node3_knowledge_graph.py',
        'celery_worker/workflow_nodes/node2_multimodal_processor.py',
        'celery_worker/workflow_nodes/node1_medical_parser.py',
    ]

    total_fixed = 0

    for file_path in files_to_fix:
        if os.path.exists(file_path):
            print(f"\nFixing {file_path}:")
            fixed = fix_long_lines_in_file(file_path)
            total_fixed += fixed
            print(f"  Fixed {fixed} lines")
        else:
            print(f"\nFile not found: {file_path}")

    print(f"\n{'='*40}")
    print(f"Total lines fixed: {total_fixed}")
    print("Fix completed!")

if __name__ == "__main__":
    main()