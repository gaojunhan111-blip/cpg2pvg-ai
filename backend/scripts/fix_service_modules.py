#!/usr/bin/env python3
"""
Service Modules Fix Tool
服务模块修复工具
"""

import re
from pathlib import Path

# 项目根目录
project_root = Path(__file__).parent.parent

def fix_service_module(file_path: Path) -> bool:
    """修复服务模块文件的缩进问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 分析和修复缩进问题
        lines = content.split('\n')
        fixed_lines = []
        in_class_or_function = False
        indent_level = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 跳过空行
            if not stripped:
                fixed_lines.append('')
                continue

            # 文档字符串处理
            if '"""' in line or "'''" in line:
                # 如果是多行字符串的开始或结束，保持原样
                fixed_lines.append(line)
                continue

            # 检查是否是类、函数或装饰器定义
            if (stripped.startswith('class ') or
                stripped.startswith('def ') or
                stripped.startswith('async def ') or
                stripped.startswith('@')):
                # 顶级定义不应该有缩进
                fixed_lines.append(stripped)
                in_class_or_function = True
                if stripped.endswith(':'):
                    indent_level = 1
                continue

            # 导入语句
            if stripped.startswith(('from ', 'import ')) or stripped.startswith('#'):
                fixed_lines.append(stripped)
                continue

            # 在类或函数内部的代码需要缩进
            if in_class_or_function:
                if stripped:
                    fixed_lines.append('    ' * indent_level + stripped)
                else:
                    fixed_lines.append('')
            else:
                # 顶级代码
                fixed_lines.append(stripped)

            # 检查是否需要调整缩进级别
            if stripped.endswith(':') and not any(keyword in stripped for keyword in ['class ', 'def ', 'async def ']):
                indent_level += 1
            elif (stripped.startswith(('return ', 'pass ', 'break ', 'continue ', 'raise ', 'elif ', 'else:', 'except ', 'finally:'))
                  and indent_level > 0):
                indent_level -= 1

        fixed_content = '\n'.join(fixed_lines)

        # 确保文件以换行符结尾
        if fixed_content and not fixed_content.endswith('\n'):
            fixed_content += '\n'

        # 如果内容有变化，写回文件
        if fixed_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"Fixed service module: {file_path.name}")
            return True
        else:
            print(f"No changes needed: {file_path.name}")
            return False

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """主函数"""
    print("SERVICE MODULES FIX TOOL")
    print("="*40)

    # 需要修复的服务模块文件列表（基于兼容性检查结果）
    files_to_fix = [
        "app/services/multimodal_processor.py",
        "app/services/knowledge_graph.py",
        "app/services/medical_agents.py",
        "app/services/agent_orchestrator.py"
    ]

    fixed_count = 0

    for file_path_str in files_to_fix:
        file_path = project_root / file_path_str
        if file_path.exists():
            if fix_service_module(file_path):
                fixed_count += 1
        else:
            print(f"File not found: {file_path_str}")

    print(f"\nFixed {fixed_count} service module files")

if __name__ == "__main__":
    main()