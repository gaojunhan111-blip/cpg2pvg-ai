#!/usr/bin/env python3
"""
Fix Missing Class Keywords Tool
修复缺失类关键字工具
"""

import re
from pathlib import Path

# 项目根目录
project_root = Path(__file__).parent.parent

def fix_missing_class_keywords(file_path: Path) -> bool:
    """修复文件中缺失的class关键字"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 修复模式：查找形如 "ClassName(str, enum.Enum):" 的模式并添加 class 关键字
        # 同时也要修复 "ClassName(BaseModel):" 等模式
        patterns = [
            # 枚举类模式
            (r'^([A-Z][a-zA-Z0-9_]*)\s*\(\s*str\s*,\s*enum\s*\.\s*Enum\s*\):', r'class \1(str, enum.Enum):'),
            (r'^([A-Z][a-zA-Z0-9_]*)\s*\(\s*str\s*,\s*Enum\s*\):', r'class \1(str, Enum):'),
            # 继承类模式
            (r'^([A-Z][a-zA-Z0-9_]*)\s*\(\s*BaseModel\s*\):', r'class \1(BaseModel):'),
        ]

        lines = content.split('\n')
        fixed_lines = []

        for line in lines:
            fixed_line = line

            # 检查是否是需要修复的行
            stripped = line.strip()

            # 跳过注释行、空行、已经包含class关键字的行
            if (not stripped or
                stripped.startswith('#') or
                stripped.startswith('"""') or
                stripped.startswith("'''") or
                stripped.startswith('class ') or
                'def ' in stripped or
                '@' in stripped):
                fixed_lines.append(line)
                continue

            # 应用修复模式
            for pattern, replacement in patterns:
                if re.match(pattern, line):
                    fixed_line = re.sub(pattern, replacement, line)
                    break

            # 额外的修复：处理简单的枚举模式
            if re.match(r'^([A-Z][a-zA-Z0-9_]*)\s*\(\s*str\s*,\s*enum\s*\.\s*Enum\s*\):', line):
                fixed_line = re.sub(r'^([A-Z][a-zA-Z0-9_]*)\s*\(\s*str\s*,\s*enum\s*\.\s*Enum\s*\):', r'class \1(str, enum.Enum):', line)
            elif re.match(r'^([A-Z][a-zA-Z0-9_]*)\s*\(\s*[A-Z][a-zA-Z0-9_]*\s*\):', line):
                fixed_line = re.sub(r'^([A-Z][a-zA-Z0-9_]*)\s*\(\s*([A-Z][a-zA-Z0-9_]*)\s*\):', r'class \1(\2):', line)

            fixed_lines.append(fixed_line)

        fixed_content = '\n'.join(fixed_lines)

        # 如果内容有变化，写回文件
        if fixed_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"Fixed class keywords: {file_path.name}")
            return True
        else:
            print(f"No class keyword fixes needed: {file_path.name}")
            return False

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """主函数"""
    print("FIX MISSING CLASS KEYWORDS TOOL")
    print("="*40)

    # 需要修复的文件列表
    files_to_fix = [
        "app/models/task_progress.py",
        "app/models/workflow.py",
        "app/models/async_task.py",
    ]

    fixed_count = 0

    for file_path_str in files_to_fix:
        file_path = project_root / file_path_str
        if file_path.exists():
            if fix_missing_class_keywords(file_path):
                fixed_count += 1
        else:
            print(f"File not found: {file_path_str}")

    print(f"\nFixed class keywords in {fixed_count} files")

if __name__ == "__main__":
    main()