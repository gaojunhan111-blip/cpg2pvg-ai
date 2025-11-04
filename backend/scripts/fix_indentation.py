#!/usr/bin/env python3
"""
Proper Indentation Fix Tool
正确缩进修复工具
"""

import os
import re
from pathlib import Path
from typing import List, Dict

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent

def fix_file_indentation(file_path: Path) -> bool:
    """修复单个文件的缩进问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        lines = content.split('\n')
        fixed_lines = []
        current_indent = 0
        in_multiline_string = False
        multiline_start = 0

        for i, line in enumerate(lines):
            # 检查多行字符串
            if '"""' in line or "'''" in line:
                if not in_multiline_string:
                    in_multiline_string = True
                    multiline_start = i
                    fixed_lines.append(line)
                else:
                    in_multiline_string = False
                    fixed_lines.append(line)
                continue

            if in_multiline_string:
                fixed_lines.append(line)
                continue

            # 处理代码行
            stripped = line.strip()

            # 空行保持原样
            if not stripped:
                fixed_lines.append('')
                continue

            # 注释行保持原样但调整到当前缩进级别
            if stripped.startswith('#'):
                fixed_lines.append('    ' * current_indent + stripped)
                continue

            # 计算当前行的缩进需求
            # 减少缩进的情况
            if stripped.startswith(('return ', 'pass', 'break', 'continue', 'raise ')):
                if current_indent > 0:
                    current_indent -= 1
            elif stripped.startswith(('elif ', 'else:', 'except ', 'finally:')):
                if current_indent > 0:
                    current_indent -= 1
            elif stripped == ')':
                # 函数/类定义结束
                pass

            # 应用当前缩进
            fixed_lines.append('    ' * current_indent + stripped)

            # 增加缩进的情况
            if stripped.endswith(':'):
                current_indent += 1
            elif stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'with ', 'try ')):
                # 这些通常会在下一行开始新块
                pass

        fixed_content = '\n'.join(fixed_lines)

        # 确保文件以换行符结尾
        if fixed_content and not fixed_content.endswith('\n'):
            fixed_content += '\n'

        # 如果内容有变化，写回文件
        if fixed_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"Fixed indentation: {file_path.name}")
            return True
        else:
            print(f"No indentation changes needed: {file_path.name}")
            return False

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """主函数"""
    print("PROPER INDENTATION FIX TOOL")
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
            if fix_file_indentation(file_path):
                fixed_count += 1
        else:
            print(f"File not found: {file_path_str}")

    print(f"\nFixed indentation in {fixed_count} files")

if __name__ == "__main__":
    main()