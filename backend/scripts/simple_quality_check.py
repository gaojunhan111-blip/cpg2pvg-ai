#!/usr/bin/env python3
"""
Simple Code Quality Check
简化代码质量检查
"""

import os
import re
import ast
import sys
from pathlib import Path
from collections import defaultdict

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def analyze_file_issues(file_path: str) -> dict:
    """分析单个文件的问题"""
    issues = {
        'file': file_path,
        'long_lines': [],
        'complexity': [],
        'structure': [],
        'documentation': [],
        'security': []
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()

        # 语法检查
        try:
            ast.parse(content)
            syntax_ok = True
        except SyntaxError as e:
            issues['syntax_error'] = {
                'line': e.lineno,
                'message': str(e)
            }
            syntax_ok = False

        if not syntax_ok:
            return issues

        # 长行检查 (>120字符)
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues['long_lines'].append({
                    'line': i,
                    'length': len(line)
                })

        # 复杂度检查（简化版）
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                        complexity += 1

                if complexity > 10:
                    issues['complexity'].append({
                        'function': node.name,
                        'line': node.lineno,
                        'complexity': complexity
                    })

                # 函数长度检查
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    func_length = node.end_lineno - node.lineno + 1
                    if func_length > 50:
                        issues['structure'].append({
                            'type': 'long_function',
                            'function': node.name,
                            'line': node.lineno,
                            'length': func_length
                        })

                # 参数数量检查
                if len(node.args.args) > 8:
                    issues['structure'].append({
                        'type': 'too_many_params',
                        'function': node.name,
                        'line': node.lineno,
                        'param_count': len(node.args.args)
                    })

            elif isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if len(methods) > 20:
                    issues['structure'].append({
                        'type': 'large_class',
                        'class': node.name,
                        'line': node.lineno,
                        'method_count': len(methods)
                    })

        # 文档检查
        if not content.strip().startswith('"""') and not content.strip().startswith("'''"):
            if 'test_' not in file_path.lower():
                issues['documentation'].append({
                    'type': 'missing_module_docstring'
                })

        # TODO/FIXME检查
        for i, line in enumerate(lines, 1):
            if 'TODO' in line.upper() and not line.strip().startswith('#'):
                issues['documentation'].append({
                    'type': 'todo_comment',
                    'line': i,
                    'content': line.strip()
                })

        # 安全检查（基础版）
        security_patterns = [
            (r'eval\s*\(', 'eval() usage'),
            (r'exec\s*\(', 'exec() usage'),
            (r'os\.system\s*\(', 'os.system() usage'),
        ]

        for i, line in enumerate(lines, 1):
            if line.strip().startswith('#'):
                continue

            for pattern, message in security_patterns:
                if re.search(pattern, line):
                    issues['security'].append({
                        'line': i,
                        'message': message,
                        'content': line.strip()[:50]
                    })

    except Exception as e:
        issues['error'] = str(e)

    return issues


def main():
    """主函数"""
    print("CODE QUALITY CHECK")
    print("=" * 50)

    # 检查的目录和文件
    targets = [
        ('app/services/knowledge_graph.py', 'Knowledge Graph Service'),
        ('app/services/multimodal_processor.py', 'Multimodal Processor Service'),
        ('app/services/medical_parser.py', 'Medical Parser Service'),
        ('app/models/knowledge_graph.py', 'Knowledge Graph Models'),
        ('app/models/multimodal_content.py', 'Multimodal Content Models'),
        ('app/models/medical_document.py', 'Medical Document Models'),
        ('celery_worker/workflow_nodes/node3_knowledge_graph.py', 'Knowledge Graph Node'),
        ('celery_worker/workflow_nodes/node2_multimodal_processor.py', 'Multimodal Processor Node'),
        ('celery_worker/workflow_nodes/node1_medical_parser.py', 'Medical Parser Node'),
        ('celery_worker/workflow/base_node.py', 'Base Workflow Node'),
    ]

    all_issues = defaultdict(list)
    total_stats = {
        'files_checked': 0,
        'files_with_issues': 0,
        'total_issues': 0,
        'by_type': defaultdict(int)
    }

    print("\n1. INDIVIDUAL FILE ANALYSIS")
    print("-" * 35)

    for file_path, name in targets:
        if os.path.exists(file_path):
            print(f"\n{name}:")
            issues = analyze_file_issues(file_path)
            total_stats['files_checked'] += 1

            has_issues = False
            for issue_type, issue_list in issues.items():
                if issue_type == 'file':
                    continue
                if issue_list:
                    has_issues = True
                    print(f"  {issue_type.replace('_', ' ').title()}: {len(issue_list)}")
                    total_stats['by_type'][issue_type] += len(issue_list)

                    # 显示前几个问题
                    for issue in issue_list[:2]:
                        if issue_type == 'long_lines':
                            print(f"    Line {issue['line']}: {issue['length']} chars")
                        elif issue_type == 'complexity':
                            print(f"    Function {issue['function']} (complexity: {issue['complexity']})")
                        elif issue_type == 'structure':
                            if issue['type'] == 'long_function':
                                print(f"    Function {issue['function']}: {issue['length']} lines")
                            else:
                                print(f"    {issue['type'].replace('_', ' ').title()}")
                        else:
                            print(f"    Issue found")

                    if len(issue_list) > 2:
                        print(f"    ... and {len(issue_list) - 2} more")

            if not has_issues:
                print("  No issues found")
            else:
                total_stats['files_with_issues'] += 1

        else:
            print(f"\n{name}: FILE NOT FOUND")

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    print(f"\nStatistics:")
    print(f"  Files checked: {total_stats['files_checked']}")
    print(f"  Files with issues: {total_stats['files_with_issues']}")

    if total_stats['files_checked'] > 0:
        for issue_type, count in total_stats['by_type'].items():
            print(f"  {issue_type.replace('_', ' ').title()}: {count}")

    print("\n2. QUALITY ASSESSMENT")
    print("-" * 22)

    # 计算质量分数
    base_score = 100
    total_issues = sum(total_stats['by_type'].values())

    if total_stats['files_checked'] > 0:
        issues_per_file = total_issues / total_stats['files_checked']
        base_score -= min(issues_per_file * 2, 50)  # 每个问题扣2分，最多扣50分

        # 严重问题额外扣分
        security_issues = total_stats['by_type'].get('security', 0)
        base_score -= security_issues * 10

        complexity_issues = total_stats['by_type'].get('complexity', 0)
        base_score -= complexity_issues * 3

    quality_score = max(0, int(base_score))

    print(f"Quality Score: {quality_score}/100")

    if quality_score >= 90:
        grade = "A (Excellent)"
        status = "Production Ready"
    elif quality_score >= 80:
        grade = "B (Good)"
        status = "Ready with Minor Improvements"
    elif quality_score >= 70:
        grade = "C (Average)"
        status = "Needs Improvements"
    else:
        grade = "D (Poor)"
        status = "Significant Improvements Needed"

    print(f"Grade: {grade}")
    print(f"Status: {status}")

    print("\n3. TOP RECOMMENDATIONS")
    print("-" * 24)

    recommendations = []

    if total_stats['by_type'].get('long_lines', 0) > 0:
        recommendations.append(f"Fix {total_stats['by_type']['long_lines']} long lines (>120 chars)")

    if total_stats['by_type'].get('complexity', 0) > 0:
        recommendations.append(f"Refactor {total_stats['by_type']['complexity']} complex functions")

    if total_stats['by_type'].get('structure', 0) > 0:
        recommendations.append("Improve code structure by breaking down large components")

    if total_stats['by_type'].get('documentation', 0) > 0:
        recommendations.append("Add proper documentation and remove TODO comments")

    if total_stats['by_type'].get('security', 0) > 0:
        recommendations.append("Address security issues before production")

    if quality_score < 80:
        recommendations.append("Consider code review and refactoring for better maintainability")

    recommendations.append("Set up automated code quality checks")

    for i, rec in enumerate(recommendations[:5], 1):
        print(f"{i}. {rec}")

    return quality_score >= 70


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