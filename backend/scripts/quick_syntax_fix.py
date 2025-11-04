#!/usr/bin/env python3
"""
Quick Syntax Fix Tool
快速语法修复工具
"""

import re
from pathlib import Path

project_root = Path(__file__).parent.parent

def fix_agent_orchestrator():
    """修复agent_orchestrator.py的缩进问题"""
    file_path = project_root / "app/services/agent_orchestrator.py"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 修复第26行的缩进问题
        lines = content.split('\n')
        if len(lines) > 25 and not lines[25].startswith('    '):
            lines[25] = '    ' + lines[25].lstrip()

        fixed_content = '\n'.join(lines)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)

        print("Fixed agent_orchestrator.py")
        return True
    except Exception as e:
        print(f"Error fixing agent_orchestrator.py: {e}")
        return False

def fix_knowledge_graph():
    """修复knowledge_graph.py的缩进问题"""
    file_path = project_root / "app/services/knowledge_graph.py"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 修复第18行的缩进问题
        lines = content.split('\n')
        if len(lines) > 17 and not lines[17].startswith('    '):
            lines[17] = '    ' + lines[17].lstrip()

        fixed_content = '\n'.join(lines)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)

        print("Fixed knowledge_graph.py")
        return True
    except Exception as e:
        print(f"Error fixing knowledge_graph.py: {e}")
        return False

def fix_minio_setup():
    """修复minio_setup.py的ASCII字符问题"""
    file_path = project_root / "app/services/minio_setup.py"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 替换非ASCII字符
        content = re.sub(r'[^\x00-\x7F]+', '', content)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("Fixed minio_setup.py")
        return True
    except Exception as e:
        print(f"Error fixing minio_setup.py: {e}")
        return False

def fix_fix_long_lines():
    """修复fix_long_lines.py的字符串问题"""
    file_path = project_root / "scripts/fix_long_lines.py"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 修复第138行的字符串问题
        lines = content.split('\n')
        if len(lines) > 137:
            # 确保字符串正确关闭
            if not lines[137].rstrip().endswith('"') and not lines[137].rstrip().endswith("'"):
                lines[137] = lines[137].rstrip() + '"'

        fixed_content = '\n'.join(lines)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)

        print("Fixed fix_long_lines.py")
        return True
    except Exception as e:
        print(f"Error fixing fix_long_lines.py: {e}")
        return False

def main():
    """主函数"""
    print("QUICK SYNTAX FIX")
    print("=" * 30)

    fixes = [
        fix_agent_orchestrator,
        fix_knowledge_graph,
        fix_minio_setup,
        fix_fix_long_lines
    ]

    fixed_count = 0
    for fix_func in fixes:
        if fix_func():
            fixed_count += 1

    print(f"\nFixed {fixed_count} files")

if __name__ == "__main__":
    main()