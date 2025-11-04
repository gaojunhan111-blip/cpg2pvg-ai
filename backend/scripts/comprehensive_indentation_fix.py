#!/usr/bin/env python3
"""
Comprehensive Indentation Fix Tool
全面缩进修复工具
"""

import os
import re
from pathlib import Path
from typing import List, Dict

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent

def fix_comprehensive_indentation(file_path: Path) -> bool:
    """全面修复文件的缩进问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        lines = content.split('\n')
        fixed_lines = []
        indent_stack = [0]  # 缩进级别栈
        current_indent = 0
        in_multiline_string = False
        multiline_delimiter = None

        for i, line in enumerate(lines):
            # 处理多行字符串
            if (not in_multiline_string and
                (('"""' in line and not line.strip().startswith('"""')) or
                 ("'''" in line and not line.strip().startswith("'''")))):
                in_multiline_string = True
                multiline_delimiter = '"""' if '"""' in line else "'''"
                fixed_lines.append(line)
                continue

            if in_multiline_string:
                fixed_lines.append(line)
                if multiline_delimiter in line and not line.strip().endswith(multiline_delimiter):
                    in_multiline_string = False
                    multiline_delimiter = None
                continue

            stripped = line.strip()

            # 空行保持原样
            if not stripped:
                fixed_lines.append('')
                continue

            # 注释行
            if stripped.startswith('#'):
                fixed_lines.append('    ' * current_indent + stripped)
                continue

            # 减少缩进的情况
            if stripped.startswith(('return ', 'pass ', 'break ', 'continue ', 'raise ', 'elif ', 'else:', 'except ', 'finally:')):
                if current_indent > 0:
                    current_indent -= 1
                    indent_stack.pop()
            elif stripped == ')' or stripped == ']':
                # 结构结束
                if len(indent_stack) > 1:
                    indent_stack.pop()
                    current_indent = indent_stack[-1]

            # 应用当前缩进
            if any(stripped.startswith(keyword) for keyword in ['def ', 'class ', 'if ', 'for ', 'while ', 'with ', 'try ']):
                # 这些语句需要单独处理
                if stripped.startswith('class ') or stripped.startswith('def '):
                    fixed_lines.append('    ' * current_indent + stripped)
                    indent_stack.append(current_indent + 1)
                    current_indent += 1
                else:
                    fixed_lines.append('    ' * current_indent + stripped)
            else:
                fixed_lines.append('    ' * current_indent + stripped)

            # 增加缩进的情况
            if stripped.endswith(':') and not any(stripped.startswith(prefix) for prefix in ['class ', 'def ']):
                if not any(stripped.startswith(keyword) for keyword in ['elif ', 'else:', 'except ', 'finally:']):
                    indent_stack.append(current_indent + 1)
                    current_indent += 1

        fixed_content = '\n'.join(fixed_lines)

        # 确保文件以换行符结尾
        if fixed_content and not fixed_content.endswith('\n'):
            fixed_content += '\n'

        # 如果内容有变化，写回文件
        if fixed_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"Fixed comprehensive indentation: {file_path.name}")
            return True
        else:
            print(f"No indentation changes needed: {file_path.name}")
            return False

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """主函数"""
    print("COMPREHENSIVE INDENTATION FIX TOOL")
    print("="*50)

    # 需要修复的文件列表
    files_to_fix = [
        "app/services/medical_parser.py",
        "app/services/multimodal_processor.py",
        "app/services/knowledge_graph.py",
        "app/services/intelligent_agent.py",
        "app/services/medical_agents.py",
        "app/services/agent_orchestrator.py",
        "celery_worker/workflow_nodes/node1_medical_parser.py",
        "celery_worker/workflow_nodes/node2_multimodal_processor.py",
        "celery_worker/workflow_nodes/node3_knowledge_graph.py",
        "celery_worker/workflow_nodes/node4_intelligent_agents.py"
    ]

    fixed_count = 0

    for file_path_str in files_to_fix:
        file_path = project_root / file_path_str
        if file_path.exists():
            if fix_comprehensive_indentation(file_path):
                fixed_count += 1
        else:
            print(f"File not found: {file_path_str}")

    print(f"\nFixed indentation in {fixed_count} files")

if __name__ == "__main__":
    main()