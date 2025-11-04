#!/usr/bin/env python3
"""
代码质量分析器
Code Quality Analyzer
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict

# 项目根目录
project_root = Path(__file__).parent.parent

class CodeQualityAnalyzer:
    """代码质量分析器"""

    def __init__(self):
        self.results = {
            'total_files': 0,
            'python_files': 0,
            'issues': defaultdict(list),
            'metrics': defaultdict(int),
            'complexity_scores': {},
            'type_annotation_coverage': 0,
            'docstring_coverage': 0
        }

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """分析单个Python文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 基本统计
            lines = content.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]
            comment_lines = [line for line in lines if line.strip().startswith('#')]

            file_metrics = {
                'total_lines': len(lines),
                'code_lines': len(non_empty_lines),
                'comment_lines': len(comment_lines),
                'functions': 0,
                'classes': 0,
                'docstrings': 0,
                'type_annotations': 0
            }

            # AST分析
            try:
                tree = ast.parse(content)
                file_metrics.update(self._analyze_ast(tree))
            except SyntaxError as e:
                self.results['issues']['syntax_errors'].append(f"{file_path}: {e}")

            # 代码质量检查
            issues = self._check_code_quality(content, file_path)

            return {
                'file_path': str(file_path),
                'metrics': file_metrics,
                'issues': issues,
                'quality_score': self._calculate_quality_score(file_metrics, issues)
            }

        except Exception as e:
            self.results['issues']['analysis_errors'].append(f"{file_path}: {e}")
            return {}

    def _analyze_ast(self, tree: ast.AST) -> Dict[str, int]:
        """分析AST树"""
        metrics = {
            'functions': 0,
            'classes': 0,
            'docstrings': 0,
            'type_annotations': 0
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                metrics['functions'] += 1
                if ast.get_docstring(node):
                    metrics['docstrings'] += 1
                if node.returns:
                    metrics['type_annotations'] += 1

                # 检查参数类型注解
                for arg in node.args.args:
                    if arg.annotation:
                        metrics['type_annotations'] += 1

            elif isinstance(node, ast.AsyncFunctionDef):
                metrics['functions'] += 1
                if ast.get_docstring(node):
                    metrics['docstrings'] += 1
                if node.returns:
                    metrics['type_annotations'] += 1

            elif isinstance(node, ast.ClassDef):
                metrics['classes'] += 1
                if ast.get_docstring(node):
                    metrics['docstrings'] += 1

        return metrics

    def _check_code_quality(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """检查代码质量问题"""
        issues = []
        lines = content.split('\n')

        # 1. 检查行长度
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append({
                    'type': 'long_line',
                    'line': i,
                    'message': f'Line too long ({len(line)} > 120 characters)'
                })

        # 2. 检查TODO/FIXME
        for i, line in enumerate(lines, 1):
            if re.search(r'\b(TODO|FIXME|XXX|HACK)\b', line, re.IGNORECASE):
                issues.append({
                    'type': 'todo_comment',
                    'line': i,
                    'message': f'TODO/FIXME found: {line.strip()}'
                })

        # 3. 检查导入语句顺序
        import_issues = self._check_imports(content)
        issues.extend(import_issues)

        # 4. 检查空函数/类
        if 'pass' in content and content.count('pass') > 5:
            issues.append({
                'type': 'many_passes',
                'message': f'Many pass statements ({content.count("pass")}) found'
            })

        # 5. 检查异常处理
        bare_except_count = len(re.findall(r'except\s*:', content))
        if bare_except_count > 0:
            issues.append({
                'type': 'bare_except',
                'message': f'Found {bare_except_count} bare except clauses'
            })

        return issues

    def _check_imports(self, content: str) -> List[Dict[str, Any]]:
        """检查导入语句"""
        issues = []
        lines = content.split('\n')
        imports = []

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith(('import ', 'from ')):
                imports.append({'line': i, 'content': stripped})

        # 检查导入顺序 (stdlib, third-party, local)
        if len(imports) > 3:
            stdlib_pattern = r'^(import (os|sys|json|re|time|datetime|uuid|pathlib|typing|collections|asyncio|logging|hashlib|enum|dataclasses|io|math|random|string|copy|itertools|functools|decimal|fractions|statistics|textwrap|unicodedata|email|http|urllib|xml|sqlite3|csv|configparser|html|zoneinfo|threading|multiprocessing|queue|socket|ssl|select|subprocess|tempfile|shutil|glob|fnmatch|pickle|gzip|zipfile|tarfile|weakref|types|inspect|pkgutil|importlib|warnings|traceback|gc|sysconfig|platform|unittest|doctest|pdb|profile|pstats|timeit|resource|tracemalloc|dis|compile|ast|parser|symbol|token|keyword|tokenize|tabnanny|py_compile|importlib|site|user|builtins))\b'

            has_issue = False
            for i in range(1, len(imports)):
                curr = imports[i]['content']
                prev = imports[i-1]['content']

                # 检查是否应该分组
                if (curr.startswith('from app.') and not prev.startswith(('from app.', 'import app.'))) or \
                   (prev.startswith('from app.') and not curr.startswith(('from app.', 'import app.'))):
                    has_issue = True
                    break

            if has_issue:
                issues.append({
                    'type': 'import_order',
                    'message': 'Import statements should be grouped (stdlib, third-party, local)'
                })

        return issues

    def _calculate_quality_score(self, metrics: Dict[str, int], issues: List[Dict]) -> float:
        """计算代码质量分数"""
        score = 100.0

        # 扣分项
        if metrics['functions'] > 0:
            docstring_ratio = metrics['docstrings'] / metrics['functions']
            score -= (1 - docstring_ratio) * 20  # 文档字符串覆盖率

        if metrics['functions'] > 0:
            type_annotation_ratio = metrics['type_annotations'] / (metrics['functions'] * 2)  # 假设每个函数平均2个注解
            score -= (1 - min(type_annotation_ratio, 1.0)) * 15  # 类型注解覆盖率

        # 问题扣分
        score -= len(issues) * 2  # 每个问题扣2分

        return max(0, score)

    def analyze_project(self, paths: List[Path]) -> Dict[str, Any]:
        """分析整个项目"""
        all_files = []

        for path in paths:
            if path.is_file() and path.suffix == '.py':
                all_files.append(path)
            elif path.is_dir():
                all_files.extend(path.rglob('*.py'))

        self.results['total_files'] = len(all_files)
        self.results['python_files'] = len(all_files)

        print(f"Analyzing {len(all_files)} Python files...")

        for file_path in all_files:
            file_result = self.analyze_file(file_path)
            if file_result:
                all_files.append(file_result)

                # 累计指标
                metrics = file_result['metrics']
                for key, value in metrics.items():
                    self.results['metrics'][key] += value

                # 累计问题
                for issue in file_result['issues']:
                    self.results['issues'][issue['type']].append(issue)

        # 计算覆盖率
        if self.results['metrics']['functions'] > 0:
            self.results['docstring_coverage'] = (self.results['metrics']['docstrings'] /
                                                self.results['metrics']['functions']) * 100

        return self.results

    def generate_report(self) -> str:
        """生成质量报告"""
        report = []
        report.append("=" * 60)
        report.append("代码质量分析报告")
        report.append("Code Quality Analysis Report")
        report.append("=" * 60)

        # 基本统计
        report.append(f"\n📊 基本统计:")
        report.append(f"   Python文件数: {self.results['python_files']}")
        report.append(f"   总代码行数: {self.results['metrics']['code_lines']:,}")
        report.append(f"   函数数量: {self.results['metrics']['functions']}")
        report.append(f"   类数量: {self.results['metrics']['classes']}")
        report.append(f"   文档字符串覆盖率: {self.results['docstring_coverage']:.1f}%")

        # 问题统计
        report.append(f"\n⚠️  发现的问题:")
        total_issues = sum(len(issues) for issues in self.results['issues'].values())
        report.append(f"   总问题数: {total_issues}")

        for issue_type, issues in self.results['issues'].items():
            if issues:
                report.append(f"   {issue_type}: {len(issues)}")

        # 建议
        report.append(f"\n💡 改进建议:")

        if self.results['docstring_coverage'] < 80:
            report.append("   - 增加函数和类的文档字符串")

        if any('type' in issue_type for issue_type in self.results['issues'].keys()):
            report.append("   - 添加类型注解以提高代码可读性")

        if 'import_order' in self.results['issues']:
            report.append("   - 整理导入语句的顺序")

        if 'long_line' in self.results['issues']:
            report.append("   - 将过长的代码行拆分为多行")

        report.append("=" * 60)

        return '\n'.join(report)


def main():
    """主函数"""
    analyzer = CodeQualityAnalyzer()

    # 分析主要目录
    paths_to_analyze = [
        project_root / "app",
        project_root / "celery_worker",
        project_root / "scripts"
    ]

    results = analyzer.analyze_project(paths_to_analyze)

    # 生成报告
    report = analyzer.generate_report()
    print(report)

    # 保存详细报告到文件
    report_path = project_root / "code_quality_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n详细报告已保存到: {report_path}")


if __name__ == "__main__":
    main()