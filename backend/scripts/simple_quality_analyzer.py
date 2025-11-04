#!/usr/bin/env python3
"""
Simple Code Quality Analyzer
"""

import ast
import os
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

project_root = Path(__file__).parent.parent

def analyze_python_file(file_path: Path) -> Dict:
    """Analyze a single Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        stats = {
            'lines': len(content.split('\n')),
            'functions': 0,
            'classes': 0,
            'docstrings': 0,
            'async_functions': 0,
            'imports': 0
        }

        # Count AST nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                stats['functions'] += 1
                if ast.get_docstring(node):
                    stats['docstrings'] += 1
            elif isinstance(node, ast.AsyncFunctionDef):
                stats['async_functions'] += 1
                if ast.get_docstring(node):
                    stats['docstrings'] += 1
            elif isinstance(node, ast.ClassDef):
                stats['classes'] += 1
                if ast.get_docstring(node):
                    stats['docstrings'] += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                stats['imports'] += 1

        # Check for issues
        issues = []

        # Long lines
        lines = content.split('\n')
        long_lines = [i+1 for i, line in enumerate(lines) if len(line) > 120]
        if long_lines:
            issues.append(f"Lines too long (>120 chars): {long_lines[:5]}...")  # Show first 5

        # Bare except
        if 'except:' in content:
            issues.append("Found bare except clauses")

        # TODO comments
        if 'TODO' in content or 'FIXME' in content:
            issues.append("Contains TODO/FIXME comments")

        return {
            'file': str(file_path.relative_to(project_root)),
            'stats': stats,
            'issues': issues
        }

    except Exception as e:
        return {
            'file': str(file_path.relative_to(project_root)),
            'error': str(e)
        }

def main():
    """Main analysis function"""
    print("CODE QUALITY ANALYSIS")
    print("=" * 50)

    # Find all Python files
    python_files = []
    for pattern in ["app/**/*.py", "celery_worker/**/*.py", "scripts/*.py"]:
        python_files.extend(project_root.glob(pattern))

    print(f"Analyzing {len(python_files)} Python files...")

    total_stats = defaultdict(int)
    all_issues = defaultdict(list)
    files_with_errors = 0

    for file_path in python_files:
        result = analyze_python_file(file_path)

        if 'error' in result:
            files_with_errors += 1
            all_issues['syntax_errors'].append(result['file'])
            continue

        # Aggregate stats
        stats = result['stats']
        for key, value in stats.items():
            total_stats[key] += value

        # Collect issues
        for issue in result['issues']:
            all_issues['general_issues'].append((result['file'], issue))

    # Print results
    print(f"\nSUMMARY:")
    print(f"Files analyzed: {len(python_files)}")
    print(f"Files with errors: {files_with_errors}")

    print(f"\nCODE METRICS:")
    print(f"Total lines: {total_stats['lines']:,}")
    print(f"Functions: {total_stats['functions']}")
    print(f"Async functions: {total_stats['async_functions']}")
    print(f"Classes: {total_stats['classes']}")
    print(f"Docstrings: {total_stats['docstrings']}")
    print(f"Import statements: {total_stats['imports']}")

    # Quality metrics
    docstring_coverage = 0
    if total_stats['functions'] + total_stats['classes'] > 0:
        docstring_coverage = (total_stats['docstrings'] /
                             (total_stats['functions'] + total_stats['classes'])) * 100

    print(f"\nQUALITY METRICS:")
    print(f"Docstring coverage: {docstring_coverage:.1f}%")
    print(f"Async functions ratio: {total_stats['async_functions']/max(1, total_stats['functions'])*100:.1f}%")

    print(f"\nISSUES FOUND:")
    for issue_type, issues in all_issues.items():
        if issues:
            print(f"{issue_type}: {len(issues)}")
            if issue_type == 'general_issues' and len(issues) <= 10:
                for file_path, issue in issues[:5]:  # Show first 5
                    print(f"  - {file_path}: {issue}")

    print(f"\nRECOMMENDATIONS:")
    if docstring_coverage < 70:
        print("- Add more docstrings to functions and classes")

    if len(all_issues['general_issues']) > 10:
        print("- Address code quality issues (long lines, TODOs, etc.)")

    if files_with_errors > 0:
        print(f"- Fix syntax errors in {files_with_errors} files")

    if total_stats['async_functions'] / max(1, total_stats['functions']) < 0.3:
        print("- Consider using async/await for I/O operations")

    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()