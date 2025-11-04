#!/usr/bin/env python3
"""
Final Quality Check After Fixes
修复后的最终质量检查
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_long_lines():
    """检查长行问题"""
    print("LONG LINES CHECK")
    print("-" * 20)

    files_to_check = [
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

    total_long_lines = 0
    files_with_long_lines = 0

    for file_path in files_to_check:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                long_lines = []
                for i, line in enumerate(lines, 1):
                    if len(line.rstrip()) > 120:
                        long_lines.append((i, len(line.rstrip())))

                if long_lines:
                    files_with_long_lines += 1
                    total_long_lines += len(long_lines)
                    print(f"  {os.path.basename(file_path)}: {len(long_lines)} long lines")
                    # 显示前几个
                    for line_num, length in long_lines[:3]:
                        print(f"    Line {line_num}: {length} chars")
                    if len(long_lines) > 3:
                        print(f"    ... and {len(long_lines) - 3} more")
                else:
                    print(f"  {os.path.basename(file_path)}: No long lines ✓")

            except Exception as e:
                print(f"  {os.path.basename(file_path)}: Error - {e}")
        else:
            print(f"  {os.path.basename(file_path)}: File not found")

    return total_long_lines, files_with_long_lines


def check_function_lengths():
    """检查函数长度"""
    print("\nFUNCTION LENGTHS CHECK")
    print("-" * 26)

    key_files = [
        'app/services/knowledge_graph.py',
        'app/services/multimodal_processor.py',
        'app/services/medical_parser.py',
    ]

    long_functions = []

    try:
        import ast

        for file_path in key_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                try:
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            if hasattr(node, 'end_lineno') and node.end_lineno:
                                func_length = node.end_lineno - node.lineno + 1
                                if func_length > 50:
                                    long_functions.append({
                                        'file': os.path.basename(file_path),
                                        'function': node.name,
                                        'line': node.lineno,
                                        'length': func_length
                                    })
                except SyntaxError:
                    print(f"  {os.path.basename(file_path)}: Syntax error, skipping")

    except ImportError:
        print("  AST module not available, skipping function analysis")

    if long_functions:
        print(f"  Found {len(long_functions)} long functions (>50 lines):")
        for func in long_functions:
            print(f"    {func['file']}.{func['function']}: {func['length']} lines (line {func['line']})")
    else:
        print("  No long functions found ✓")

    return len(long_functions)


def check_import_cleanup():
    """检查导入清理"""
    print("\nIMPORT CLEANUP CHECK")
    print("-" * 22)

    files_to_check = [
        'app/services/knowledge_graph.py',
        'app/services/multimodal_processor.py',
        'celery_worker/workflow_nodes/node3_knowledge_graph.py',
    ]

    duplicate_imports = []

    for file_path in files_to_check:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查重复导入
                import_lines = []
                for line in content.splitlines():
                    if line.strip().startswith('from ') and ' import ' in line:
                        import_lines.append(line.strip())

                # 简单重复检测
                seen_imports = set()
                duplicates = []
                for import_line in import_lines:
                    if import_line in seen_imports:
                        duplicates.append(import_line)
                    seen_imports.add(import_line)

                if duplicates:
                    duplicate_imports.extend([
                        {'file': os.path.basename(file_path), 'import': dup}
                        for dup in duplicates
                    ])
                    print(f"  {os.path.basename(file_path)}: {len(duplicates)} duplicate imports")
                    for dup in duplicates:
                        print(f"    {dup}")
                else:
                    print(f"  {os.path.basename(file_path)}: No duplicate imports ✓")

            except Exception as e:
                print(f"  {os.path.basename(file_path)}: Error - {e}")
        else:
            print(f"  {os.path.basename(file_path)}: File not found")

    return len(duplicate_imports)


def main():
    """主函数"""
    print("FINAL CODE QUALITY CHECK")
    print("=" * 50)
    print("Checking improvements after fixes...")
    print()

    # 1. 检查长行问题
    total_long_lines, files_with_long_lines = check_long_lines()

    # 2. 检查函数长度
    long_function_count = check_function_lengths()

    # 3. 检查导入清理
    duplicate_import_count = check_import_cleanup()

    # 4. 总体评估
    print("\n" + "=" * 50)
    print("IMPROVEMENT SUMMARY")
    print("=" * 50)

    print(f"\nResults:")
    print(f"  Long lines: {total_long_lines} (previously 68)")
    print(f"  Files with long lines: {files_with_long_lines}")
    print(f"  Long functions: {long_function_count} (previously 5)")
    print(f"  Duplicate imports: {duplicate_import_count}")

    # 计算改进
    long_lines_improvement = max(0, 68 - total_long_lines)
    functions_improvement = max(0, 5 - long_function_count)

    print(f"\nImprovements:")
    print(f"  Long lines fixed: {long_lines_improvement}/68 ({long_lines_improvement/68*100:.1f}%)")
    print(f"  Long functions refactored: {functions_improvement}/5 ({functions_improvement/5*100:.1f}%)")

    # 质量评分
    base_score = 81  # 之前的分数
    improvement_score = (long_lines_improvement / 68) * 10 + (functions_improvement / 5) * 5
    new_score = min(100, base_score + improvement_score)

    print(f"\nQuality Score:")
    print(f"  Previous: 81/100")
    print(f"  Current: {int(new_score)}/100")
    print(f"  Improvement: +{int(new_score - 81)} points")

    # 等级评估
    if new_score >= 90:
        grade = "A (Excellent)"
        status = "Production Ready"
    elif new_score >= 80:
        grade = "B (Good)"
        status = "Ready with Minor Improvements"
    elif new_score >= 70:
        grade = "C (Average)"
        status = "Needs Improvements"
    else:
        grade = "D (Poor)"
        status = "Significant Improvements Needed"

    print(f"\nGrade: {grade}")
    print(f"Status: {status}")

    # 下一步建议
    print(f"\nNext Steps:")
    if total_long_lines > 0:
        print(f"1. Continue fixing remaining {total_long_lines} long lines")
    if long_function_count > 0:
        print(f"2. Refactor remaining {long_function_count} long functions")
    if duplicate_import_count > 0:
        print(f"3. Clean up {duplicate_import_count} duplicate imports")
    if total_long_lines == 0 and long_function_count == 0 and duplicate_import_count == 0:
        print("✅ All major issues resolved!")
        print("1. Set up automated code quality checks")
        print("2. Add comprehensive unit tests")
        print("3. Deploy to production environment")

    return new_score >= 85


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nCheck interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)