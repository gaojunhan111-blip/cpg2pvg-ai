#!/usr/bin/env python3
"""
修复文件编码问题
Fix file encoding issues
"""

import os
import re
from pathlib import Path

# Emoji替换映射
emoji_replacements = {
    "[OK]": "[OK]",
    "[FAIL]": "[FAIL]",
    "[WARN]": "[WARN]",
    "[SEARCH]": "[SEARCH]",
    "[PACKAGE]": "[PACKAGE]",
    "[DB]": "[DB]",
    "[REDIS]": "[REDIS]",
    "[FILE]": "[FILE]",
    "[AI]": "[AI]",
    "[SECURITY]": "[SECURITY]",
    "[LIST]": "[LIST]",
    "[START]": "[START]",
    "[HEALTH]": "[HEALTH]",
    "[BUILD]": "[BUILD]",
    "[CONFIG]": "[CONFIG]",
    "[TARGET]": "[TARGET]",
    "[METRICS]": "[METRICS]",
    "[SUCCESS]": "[SUCCESS]",
    "[GREEN]": "[GREEN]",
    "[WEB]": "[WEB]",
    "[SHIELD]": "[SHIELD]",
    "[LOCK]": "[LOCK]"
}

def fix_file_encoding(file_path):
    """修复单个文件的编码问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 替换emoji
        for emoji, replacement in emoji_replacements.items():
            content = content.replace(emoji, replacement)

        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  修复: {file_path}")
            return True
        else:
            return False

    except Exception as e:
        print(f"  错误: {file_path} - {e}")
        return False

def fix_directory_encoding(directory):
    """修复目录中所有Python文件的编码问题"""
    print(f"扫描目录: {directory}")

    fixed_count = 0
    total_count = 0

    for file_path in Path(directory).rglob("*.py"):
        total_count += 1
        if fix_file_encoding(file_path):
            fixed_count += 1

    print(f"\n扫描完成:")
    print(f"  总文件数: {total_count}")
    print(f"  修复文件数: {fixed_count}")

    return fixed_count > 0

def main():
    """主函数"""
    print("修复文件编码问题...")
    print("=" * 50)

    # 修复当前目录
    current_dir = Path(__file__).parent
    fixed_count = 0

    # 修复scripts目录
    scripts_dir = current_dir
    if fix_directory_encoding(scripts_dir):
        fixed_count += 1

    # 修复app目录
    app_dir = current_dir.parent / "app"
    if app_dir.exists():
        if fix_directory_encoding(app_dir):
            fixed_count += 1

    # 修复README.md
    readme_path = current_dir.parent / "README.md"
    if readme_path.exists():
        if fix_file_encoding(readme_path):
            fixed_count += 1

    print(f"\n总计修复目录数: {fixed_count}")
    print("编码问题修复完成!")

if __name__ == "__main__":
    main()