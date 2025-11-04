#!/usr/bin/env python3
"""
Simple Long Line Fix
简单的长行修复脚本
"""

import os

def fix_specific_long_lines():
    """修复特定的长行问题"""

    fixes = [
        # Knowledge Graph Service
        {
            'file': 'app/services/knowledge_graph.py',
            'fixes': [
                {
                    'old': '                        if len(term.split()) <= len(entity.canonical_form.split()) + 2:  # 避免过长的匹配',
                    'new': '                        # 避免过长的匹配\n                        if len(term.split()) <= len(entity.canonical_form.split()) + 2:'
                }
            ]
        },
        # Multimodal Processor Service
        {
            'file': 'app/services/multimodal_processor.py',
            'fixes': [
                {
                    'old': '                "completed": len([t for t in processed_content.processed_tables if t.status == ProcessingStatus.COMPLETED]),',
                    'new': '                "completed": len([\n                    t for t in processed_content.processed_tables\n                    if t.status == ProcessingStatus.COMPLETED\n                ]),'
                },
                {
                    'old': '                "failed": len([t for t in processed_content.processed_tables if t.status == ProcessingStatus.FAILED]),',
                    'new': '                "failed": len([\n                    t for t in processed_content.processed_tables\n                    if t.status == ProcessingStatus.FAILED\n                ]),'
                }
            ]
        }
    ]

    total_fixed = 0

    for file_fix in fixes:
        file_path = file_fix['file']
        if os.path.exists(file_path):
            print(f"Fixing {file_path}:")

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            for fix in file_fix['fixes']:
                if fix['old'] in content:
                    content = content.replace(fix['old'], fix['new'])
                    print(f"  - Fixed: {fix['old'][:50]}...")
                    total_fixed += 1
                else:
                    print(f"  - Not found: {fix['old'][:50]}...")

            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        else:
            print(f"File not found: {file_path}")

    return total_fixed

def main():
    """主函数"""
    print("SIMPLE LONG LINE FIX")
    print("=" * 40)

    fixed_count = fix_specific_long_lines()

    print(f"\n{'='*40}")
    print(f"Fixed {fixed_count} lines")
    print("Fix completed!")

if __name__ == "__main__":
    main()