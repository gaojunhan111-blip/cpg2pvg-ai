#!/usr/bin/env python3
"""
Comprehensive Code Quality Check
全面代码质量检查
"""

import os
import re
import ast
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class CodeQualityAnalyzer:
    """代码质量分析器"""

    def __init__(self):
        self.issues = defaultdict(list)
        self.stats = defaultdict(int)

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """分析单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            file_stats = {
                'path': file_path,
                'lines': len(content.splitlines()),
                'characters': len(content),
                'issues': []
            }

            # 语法检查
            try:
                ast.parse(content)
                file_stats['syntax_valid'] = True
            except SyntaxError as e:
                file_stats['syntax_valid'] = False
                file_stats['issues'].append({
                    'type': 'syntax_error',
                    'line': e.lineno,
                    'message': str(e)
                })

            # 长行检查 (>120字符)
            lines = content.splitlines()
            long_lines = []
            for i, line in enumerate(lines, 1):
                if len(line) > 120:
                    long_lines.append({
                        'line': i,
                        'length': len(line),
                        'content': line[:100] + '...' if len(line) > 100 else line
                    })

            if long_lines:
                file_stats['issues'].append({
                    'type': 'long_lines',
                    'count': len(long_lines),
                    'details': long_lines[:5]  # 只显示前5个
                })

            # 安全检查
            security_issues = self._check_security(content)
            if security_issues:
                file_stats['issues'].extend(security_issues)

            # 代码结构检查
            structure_issues = self._check_structure(content)
            if structure_issues:
                file_stats['issues'].extend(structure_issues)

            # 文档检查
            doc_issues = self._check_documentation(content, file_path)
            if doc_issues:
                file_stats['issues'].extend(doc_issues)

            # 复杂度检查
            complexity_issues = self._check_complexity(content)
            if complexity_issues:
                file_stats['issues'].extend(complexity_issues)

            return file_stats

        except Exception as e:
            return {
                'path': file_path,
                'error': str(e),
                'issues': [{
                    'type': 'file_error',
                    'message': f'Cannot read file: {e}'
                }]
            }

    def _check_security(self, content: str) -> List[Dict[str, Any]]:
        """安全检查"""
        issues = []
        lines = content.splitlines()

        security_patterns = [
            (r'eval\s*\(', 'Use of eval() function - potential security risk'),
            (r'exec\s*\(', 'Use of exec() function - potential security risk'),
            (r'os\.system\s*\(', 'Use of os.system() - potential security risk'),
            (r'subprocess\.call\s*\(', 'Use of subprocess.call() - verify input sanitization'),
            (r'shell=True', 'shell=True detected - ensure input sanitization'),
            (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password detected'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key detected'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret detected'),
        ]

        for i, line in enumerate(lines, 1):
            # 跳过注释和文档字符串
            if line.strip().startswith('#') or '"""' in line or "'''" in line:
                continue

            for pattern, message in security_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        'type': 'security',
                        'line': i,
                        'message': message,
                        'content': line.strip()[:100]
                    })

        return issues

    def _check_structure(self, content: str) -> List[Dict[str, Any]]:
        """代码结构检查"""
        issues = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # 函数长度检查
                    if hasattr(node, 'end_lineno') and node.end_lineno:
                        func_lines = node.end_lineno - node.lineno + 1
                        if func_lines > 50:
                            issues.append({
                                'type': 'structure',
                                'severity': 'medium',
                                'message': f'Function {node.name} is too long ({func_lines} lines)',
                                'line': node.lineno
                            })

                    # 参数数量检查
                    if len(node.args.args) > 8:
                        issues.append({
                            'type': 'structure',
                            'severity': 'medium',
                            'message': f'Function {node.name} has too many parameters ({len(node.args.args)})',
                            'line': node.lineno
                        })

                elif isinstance(node, ast.ClassDef):
                    # 类方法数量检查
                    methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                    if len(methods) > 20:
                        issues.append({
                            'type': 'structure',
                            'severity': 'low',
                            'message': f'Class {node.name} has many methods ({len(methods)})',
                            'line': node.lineno
                        })

        except Exception:
            # 如果AST解析失败，跳过结构检查
            pass

        return issues

    def _check_documentation(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """文档检查"""
        issues = []

        # 检查是否有模块级文档字符串
        if not content.strip().startswith('"""') and not content.strip().startswith("'''"):
            if not content.strip().startswith('#') or 'test_' not in file_path:
                issues.append({
                    'type': 'documentation',
                    'severity': 'low',
                    'message': 'Missing module-level docstring',
                    'line': 1
                })

        # 检查TODO/FIXME注释
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if 'TODO' in line.upper() and not line.strip().startswith('#'):
                issues.append({
                    'type': 'documentation',
                    'severity': 'low',
                    'message': f'TODO comment found: {line.strip()}',
                    'line': i
                })
            elif 'FIXME' in line.upper():
                issues.append({
                    'type': 'documentation',
                    'severity': 'medium',
                    'message': f'FIXME comment found: {line.strip()}',
                    'line': i
                })

        return issues

    def _check_complexity(self, content: str) -> List[Dict[str, Any]]:
        """复杂度检查"""
        issues = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # 计算圈复杂度（简化版）
                    complexity = 1  # 基础复杂度

                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.While, ast.For, ast.Try)):
                            complexity += 1
                        elif isinstance(child, ast.ExceptHandler):
                            complexity += 1
                        elif isinstance(child, ast.With):
                            complexity += 1

                    if complexity > 10:
                        issues.append({
                            'type': 'complexity',
                            'severity': 'medium',
                            'message': f'Function {node.name} has high complexity ({complexity})',
                            'line': node.lineno,
                            'complexity': complexity
                        })

        except Exception:
            pass

        return issues

    def analyze_directory(self, directory: str, pattern: str = "*.py") -> Dict[str, Any]:
        """分析目录中的所有Python文件"""
        results = {
            'total_files': 0,
            'total_issues': 0,
            'files': [],
            'summary': {
                'by_type': defaultdict(int),
                'by_severity': defaultdict(int),
                'by_file': defaultdict(int)
            }
        }

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    file_stats = self.analyze_file(file_path)

                    results['files'].append(file_stats)
                    results['total_files'] += 1

                    if 'error' not in file_stats:
                        # 统计问题
                        for issue in file_stats['issues']:
                            issue_type = issue['type']
                            severity = issue.get('severity', 'medium')

                            results['total_issues'] += 1
                            results['summary']['by_type'][issue_type] += 1
                            results['summary']['by_severity'][severity] += 1
                            results['summary']['by_file'][file_path] += 1

        return results


def main():
    """主函数"""
    print("COMPREHENSIVE CODE QUALITY CHECK")
    print("=" * 60)

    analyzer = CodeQualityAnalyzer()

    # 要检查的目录
    directories = [
        ('app/services', 'Services Layer'),
        ('app/models', 'Models Layer'),
        ('celery_worker/workflow_nodes', 'Workflow Nodes Layer'),
        ('celery_worker/workflow', 'Workflow Base Layer'),
    ]

    total_results = {
        'directories': {},
        'overall_stats': {
            'total_files': 0,
            'total_issues': 0,
            'files_with_issues': 0,
            'critical_issues': 0
        }
    }

    print("\n1. CODE STRUCTURE ANALYSIS")
    print("-" * 30)

    for directory, name in directories:
        if os.path.exists(directory):
            print(f"\nAnalyzing {name}...")
            results = analyzer.analyze_directory(directory)

            total_results['directories'][name] = results

            # 更新总体统计
            total_results['overall_stats']['total_files'] += results['total_files']
            total_results['overall_stats']['total_issues'] += results['total_issues']

            files_with_issues = len([f for f in results['files'] if f.get('issues')])
            total_results['overall_stats']['files_with_issues'] += files_with_issues

            # 统计严重问题
            critical_count = sum(1 for f in results['files']
                               for issue in f.get('issues', [])
                               if issue.get('severity') == 'high')
            total_results['overall_stats']['critical_issues'] += critical_count

            print(f"  Files: {results['total_files']}")
            print(f"  Issues: {results['total_issues']}")
            print(f"  Files with issues: {files_with_issues}")

            if results['summary']['by_severity']:
                print("  Severity breakdown:")
                for severity, count in results['summary']['by_severity'].items():
                    print(f"    {severity}: {count}")

    print("\n2. DETAILED ISSUE ANALYSIS")
    print("-" * 30)

    # 按类型显示问题
    all_issues_by_type = defaultdict(list)

    for name, results in total_results['directories'].items():
        for file_stats in results['files']:
            for issue in file_stats.get('issues', []):
                issue['file'] = file_stats['path']
                issue['directory'] = name
                all_issues_by_type[issue['type']].append(issue)

    # 显示最常见的问题类型
    issue_types_sorted = sorted(all_issues_by_type.items(),
                               key=lambda x: len(x[1]), reverse=True)

    print("\nMost Common Issue Types:")
    for issue_type, issues in issue_types_sorted[:10]:
        print(f"  {issue_type}: {len(issues)} occurrences")

        # 显示前几个例子
        for issue in issues[:3]:
            location = f"Line {issue.get('line', '?')}" if 'line' in issue else "Unknown"
            print(f"    - {location}: {issue.get('message', 'No message')}")

        if len(issues) > 3:
            print(f"    ... and {len(issues) - 3} more")

    print("\n3. SECURITY ISSUES")
    print("-" * 20)

    security_issues = all_issues_by_type.get('security', [])
    if security_issues:
        print(f"⚠️  Found {len(security_issues)} security issues:")
        for issue in security_issues:
            print(f"  📍 {issue['directory']} - {os.path.basename(issue['file'])}")
            print(f"     Line {issue.get('line', '?')}: {issue['message']}")
    else:
        print("✅ No security issues found")

    print("\n4. QUALITY METRICS")
    print("-" * 18)

    overall = total_results['overall_stats']
    if overall['total_files'] > 0:
        issues_per_file = overall['total_issues'] / overall['total_files']
        files_with_issues_percent = (overall['files_with_issues'] / overall['total_files']) * 100

        print(f"Total files analyzed: {overall['total_files']}")
        print(f"Total issues found: {overall['total_issues']}")
        print(f"Average issues per file: {issues_per_file:.1f}")
        print(f"Files with issues: {overall['files_with_issues']} ({files_with_issues_percent:.1f}%)")
        print(f"Critical issues: {overall['critical_issues']}")

    # 5. 质量评级
    print("\n5. QUALITY RATING")
    print("-" * 18)

    quality_score = calculate_quality_score(overall)

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

    print(f"Quality Score: {quality_score}/100")
    print(f"Grade: {grade}")
    print(f"Status: {status}")

    # 6. 推荐改进建议
    print("\n6. RECOMMENDATIONS")
    print("-" * 20)

    recommendations = generate_recommendations(all_issues_by_type, overall)
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")

    return quality_score >= 70


def calculate_quality_score(stats: Dict[str, Any]) -> int:
    """计算质量分数"""
    base_score = 100

    # 根据问题数量扣分
    total_issues = stats['total_issues']
    total_files = stats['total_files']

    if total_files > 0:
        issues_per_file = total_issues / total_files

        # 每1个问题每文件扣1分
        base_score -= min(issues_per_file, 50)

        # 严重问题额外扣分
        critical_penalty = stats['critical_issues'] * 5
        base_score -= critical_penalty

    return max(0, int(base_score))


def generate_recommendations(issues_by_type: Dict, stats: Dict) -> List[str]:
    """生成改进建议"""
    recommendations = []

    # 基于问题类型生成建议
    if 'long_lines' in issues_by_type:
        count = len(issues_by_type['long_lines'])
        recommendations.append(f"Fix {count} long lines (>120 chars) to improve readability")

    if 'documentation' in issues_by_type:
        count = len(issues_by_type['documentation'])
        recommendations.append(f"Add proper documentation for {count} undocumented components")

    if 'complexity' in issues_by_type:
        count = len(issues_by_type['complexity'])
        recommendations.append(f"Refactor {count} complex functions to reduce maintainability issues")

    if 'security' in issues_by_type:
        recommendations.append("Address security issues immediately before production deployment")

    if 'structure' in issues_by_type:
        recommendations.append("Improve code structure by breaking down large functions and classes")

    # 通用建议
    if stats['files_with_issues'] > 0:
        recommendations.append("Set up pre-commit hooks to catch issues automatically")

    recommendations.append("Consider adding unit tests to ensure code quality")
    recommendations.append("Implement code review process for future changes")

    return recommendations[:10]  # 最多显示10个建议


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nCode quality check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)