#!/usr/bin/env python3
"""
Workflow Nodes Fix Tool
工作流节点修复工具
"""

import re
from pathlib import Path

# 项目根目录
project_root = Path(__file__).parent.parent

def fix_workflow_node(file_path: Path) -> bool:
    """修复工作流节点文件的语法和结构"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 基本修复策略
        fixed_content = content

        # 1. 修复重复的文档字符串
        fixed_content = re.sub(r'"""\s*节点\d+：[^\n]*\s*Node\s*\d+: [^\n]*\s*"""\s*"""\s*节点\d+：[^\n]*\s*Node\s*\d+: [^\n]*\s*"""',
                              '"""\n节点1：智能文档解析层\nNode 1: Intelligent Document Parsing Layer\n"""', fixed_content)

        # 2. 修复断裂的导入语句
        fixed_content = re.sub(r'from\s+([^\s]+)\s*\(\s*\n\s*from\s+', r'from \1 import (\nfrom ', fixed_content)

        # 3. 修复缺失的缩进 - 确保类和函数有正确的缩进
        lines = fixed_content.split('\n')
        fixed_lines = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 跳过空行
            if not stripped:
                fixed_lines.append('')
                continue

            # 如果是类定义或函数定义，确保没有缩进
            if stripped.startswith('class ') or stripped.startswith('def ') or stripped.startswith('async def '):
                fixed_lines.append(stripped)
            # 如果是导入语句，确保没有缩进
            elif stripped.startswith(('from ', 'import ')):
                fixed_lines.append(stripped)
            # 如果是装饰器，确保没有缩进
            elif stripped.startswith('@'):
                fixed_lines.append(stripped)
            # 如果是文档字符串，保持原有缩进
            elif stripped.startswith('"""') or stripped.startswith("'''"):
                fixed_lines.append(line)
            # 其他代码行，如果有内容则添加4空格缩进
            elif stripped and not stripped.startswith('#'):
                fixed_lines.append('    ' + stripped)
            # 注释行保持原样但添加适当缩进
            elif stripped.startswith('#'):
                fixed_lines.append('    ' + stripped)
            else:
                fixed_lines.append(line)

        fixed_content = '\n'.join(fixed_lines)

        # 如果内容有变化，写回文件
        if fixed_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"Fixed workflow node: {file_path.name}")
            return True
        else:
            print(f"No changes needed: {file_path.name}")
            return False

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """主函数"""
    print("WORKFLOW NODES FIX TOOL")
    print("="*40)

    # 需要修复的工作流节点文件列表
    files_to_fix = [
        "celery_worker/workflow_nodes/node1_medical_parser.py",
        "celery_worker/workflow_nodes/node2_multimodal_processor.py",
        "celery_worker/workflow_nodes/node3_knowledge_graph.py",
        "celery_worker/workflow_nodes/node4_intelligent_agents.py"
    ]

    fixed_count = 0

    for file_path_str in files_to_fix:
        file_path = project_root / file_path_str
        if file_path.exists():
            if fix_workflow_node(file_path):
                fixed_count += 1
        else:
            print(f"File not found: {file_path_str}")

    print(f"\nFixed {fixed_count} workflow node files")

if __name__ == "__main__":
    main()