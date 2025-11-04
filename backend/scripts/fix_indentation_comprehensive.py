#!/usr/bin/env python3
"""
Comprehensive Indentation Fix Tool
全面缩进修复工具
"""

import re
from pathlib import Path

project_root = Path(__file__).parent.parent

def fix_file_indentation(file_path: Path):
    """修复单个文件的缩进问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        fixed_lines = []
        indent_level = 0
        in_multiline_string = False
        multiline_delimiter = None

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 处理多行字符串
            if not in_multiline_string:
                if ('"""' in line and line.count('"""') == 1) or ("'''" in line and line.count("'''") == 1):
                    in_multiline_string = True
                    multiline_delimiter = '"""' if '"""' in line else "'''"
                    fixed_lines.append(line)
                    continue
            else:
                if multiline_delimiter in line:
                    in_multiline_string = False
                    multiline_delimiter = None
                fixed_lines.append(line)
                continue

            # 空行
            if not stripped:
                fixed_lines.append('')
                continue

            # 注释行
            if stripped.startswith('#'):
                fixed_lines.append('    ' * indent_level + stripped)
                continue

            # 类和函数定义
            if stripped.startswith(('class ', 'def ', 'async def ')):
                fixed_lines.append('    ' * indent_level + stripped)
                if stripped.endswith(':'):
                    indent_level += 1
                continue

            # 导入语句
            if stripped.startswith(('from ', 'import ')):
                fixed_lines.append(stripped)
                continue

            # 装饰器
            if stripped.startswith('@'):
                fixed_lines.append('    ' * indent_level + stripped)
                continue

            # 减少缩进的情况
            if (stripped.startswith(('return ', 'pass ', 'break ', 'continue ', 'raise ')) and
                indent_level > 0):
                if any(keyword in stripped for keyword in ['return', 'pass', 'break', 'continue', 'raise']):
                    pass  # 不调整缩进，保持原样

            # 应用缩进
            fixed_lines.append('    ' * indent_level + stripped)

            # 增加缩进的情况
            if stripped.endswith(':'):
                indent_level += 1

        fixed_content = '\n'.join(fixed_lines)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)

        return True

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """主函数"""
    print("COMPREHENSIVE INDENTATION FIX")
    print("=" * 40)

    # 需要修复的文件
    files_to_fix = [
        "app/services/agent_orchestrator.py",
        "app/services/knowledge_graph.py",
        "app/services/medical_agents.py",
        "app/services/multimodal_processor.py"
    ]

    fixed_count = 0
    for file_path_str in files_to_fix:
        file_path = project_root / file_path_str
        if file_path.exists():
            if fix_file_indentation(file_path):
                print(f"Fixed: {file_path_str}")
                fixed_count += 1
        else:
            print(f"File not found: {file_path_str}")

    print(f"\nFixed {fixed_count} files")

if __name__ == "__main__":
    main()