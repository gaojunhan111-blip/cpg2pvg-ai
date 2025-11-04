#!/usr/bin/env python3
"""
Comprehensive Code Analysis and Optimization
全面代码分析和优化
"""

import os
import sys
import ast
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any
from collections import defaultdict

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class CodeAnalyzer:
    """代码分析器"""

    def __init__(self):
        self.results = {
            "files_analyzed": 0,
            "total_lines": 0,
            "issues": defaultdict(list),
            "metrics": defaultdict(dict),
            "recommendations": []
        }
        self.project_root = project_root

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """分析单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            analyzer = FileAnalyzer(file_path, content)
            analyzer.visit(tree)

            return analyzer.get_results()

        except Exception as e:
            return {"error": str(e), "file": file_path}

    def analyze_directory(self, directory: str, patterns: List[str]) -> Dict[str, Any]:
        """分析目录中的文件"""
        print(f"\n{'='*60}")
        print(f"ANALYZING DIRECTORY: {directory}")
        print(f"{'='*60}")

        files_to_analyze = []
        for pattern in patterns:
            files_to_analyze.extend(Path(directory).glob(pattern))

        for file_path in files_to_analyze:
            if file_path.is_file():
                print(f"Analyzing: {file_path.relative_to(self.project_root)}")
                result = self.analyze_file(str(file_path))

                if "error" not in result:
                    self.results["files_analyzed"] += 1
                    self.results["total_lines"] += result.get("total_lines", 0)

                    # 收集问题
                    for issue_type, issues in result.get("issues", {}).items():
                        self.results["issues"][issue_type].extend(issues)

                    # 收集指标
                    file_name = str(file_path.relative_to(self.project_root))
                    self.results["metrics"][file_name] = result.get("metrics", {})
                else:
                    print(f"  ERROR: {result['error']}")

        return self.results

    def generate_optimization_recommendations(self):
        """生成优化建议"""
        recommendations = []

        # 分析复杂度问题
        complexity_issues = len(self.results["issues"]["complexity"])
        if complexity_issues > 0:
            recommendations.append({
                "category": "Complexity",
                "priority": "High",
                "count": complexity_issues,
                "description": f"发现 {complexity_issues} 个复杂度过高的函数，需要重构"
            })

        # 分析长度问题
        length_issues = len(self.results["issues"]["length"])
        if length_issues > 0:
            recommendations.append({
                "category": "Code Length",
                "priority": "Medium",
                "count": length_issues,
                "description": f"发现 {length_issues} 行过长的代码，需要格式化"
            })

        # 分析命名问题
        naming_issues = len(self.results["issues"]["naming"])
        if naming_issues > 0:
            recommendations.append({
                "category": "Naming",
                "priority": "Low",
                "count": naming_issues,
                "description": f"发现 {naming_issues} 个命名不规范的地方"
            })

        # 分析导入问题
        import_issues = len(self.results["issues"]["imports"])
        if import_issues > 0:
            recommendations.append({
                "category": "Imports",
                "priority": "Medium",
                "count": import_issues,
                "description": f"发现 {import_issues} 个导入问题，需要优化"
            })

        self.results["recommendations"] = recommendations
        return recommendations


class FileAnalyzer(ast.NodeVisitor):
    """文件分析器"""

    def __init__(self, file_path: str, content: str):
        self.file_path = file_path
        self.content = content
        self.lines = content.split('\n')
        self.issues = defaultdict(list)
        self.metrics = {
            "total_lines": len(self.lines),
            "classes": 0,
            "functions": 0,
            "complex_functions": 0,
            "long_lines": 0,
            "imports": 0,
            "docstrings": 0
        }
        self.current_class = None
        self.imports = set()

    def get_results(self) -> Dict[str, Any]:
        """获取分析结果"""
        return {
            "file": self.file_path,
            "issues": dict(self.issues),
            "metrics": self.metrics,
            "imports": list(self.imports)
        }

    def visit_ClassDef(self, node: ast.ClassDef):
        """分析类定义"""
        self.current_class = node.name
        self.metrics["classes"] += 1

        # 检查类名
        if not node.name[0].isupper():
            self.issues["naming"].append({
                "type": "class_name",
                "line": node.lineno,
                "message": f"Class name '{node.name}' should follow PascalCase"
            })

        # 检查类长度
        if hasattr(node, 'end_lineno') and node.end_lineno:
            class_length = node.end_lineno - node.lineno + 1
            if class_length > 200:
                self.issues["complexity"].append({
                    "type": "large_class",
                    "line": node.lineno,
                    "message": f"Class '{node.name}' is too long ({class_length} lines)"
                })

        # 检查文档字符串
        docstring = ast.get_docstring(node)
        if docstring:
            self.metrics["docstrings"] += 1
        else:
            self.issues["documentation"].append({
                "type": "missing_docstring",
                "line": node.lineno,
                "message": f"Class '{node.name}' is missing docstring"
            })

        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """分析函数定义"""
        self.metrics["functions"] += 1

        # 检查函数名
        if not self._is_snake_case(node.name):
            self.issues["naming"].append({
                "type": "function_name",
                "line": node.lineno,
                "message": f"Function name '{node.name}' should follow snake_case"
            })

        # 检查函数长度
        if hasattr(node, 'end_lineno') and node.end_lineno:
            func_length = node.end_lineno - node.lineno + 1
            if func_length > 50:
                self.metrics["complex_functions"] += 1
                self.issues["complexity"].append({
                    "type": "long_function",
                    "line": node.lineno,
                    "message": f"Function '{node.name}' is too long ({func_length} lines)"
                })

        # 检查复杂度（简化版）
        complexity = self._calculate_complexity(node)
        if complexity > 10:
            self.issues["complexity"].append({
                "type": "high_complexity",
                "line": node.lineno,
                "message": f"Function '{node.name}' has high complexity ({complexity})"
            })

        # 检查文档字符串
        docstring = ast.get_docstring(node)
        if docstring:
            self.metrics["docstrings"] += 1
        elif node.name.startswith('_') or self.current_class is None:
            # 公共函数应该有文档字符串
            if not node.name.startswith('_'):
                self.issues["documentation"].append({
                    "type": "missing_docstring",
                    "line": node.lineno,
                    "message": f"Function '{node.name}' is missing docstring"
                })

        # 检查参数数量
        if len(node.args.args) > 7:
            self.issues["complexity"].append({
                "type": "too_many_parameters",
                "line": node.lineno,
                "message": f"Function '{node.name}' has too many parameters ({len(node.args.args)})"
            })

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        """分析导入语句"""
        self.metrics["imports"] += 1
        for alias in node.names:
            self.imports.add(alias.name)

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """分析 from 导入语句"""
        self.metrics["imports"] += 1
        if node.module:
            self.imports.add(node.module)

        # 检查是否使用通配符导入
        for alias in node.names:
            if alias.name == '*':
                self.issues["imports"].append({
                    "type": "wildcard_import",
                    "line": node.lineno,
                    "message": "Avoid using wildcard imports"
                })
            self.imports.add(f"{node.module}.{alias.name}" if node.module else alias.name)

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """分析异步函数定义"""
        # 复用普通函数的分析逻辑
        self.visit_FunctionDef(node)

    def _calculate_complexity(self, node: ast.AST) -> int:
        """计算圈复杂度（简化版）"""
        complexity = 1  # 基础复杂度

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _is_snake_case(self, name: str) -> bool:
        """检查是否为 snake_case 命名"""
        return name.replace('_', '').isalnum() and name != name.upper()

    def generic_visit(self, node: ast.AST):
        """通用访问方法，同时检查长行"""
        # 检查长行
        if hasattr(node, 'lineno'):
            line_num = node.lineno
            if line_num <= len(self.lines):
                line_content = self.lines[line_num - 1]
                if len(line_content) > 120:
                    self.metrics["long_lines"] += 1
                    if self.metrics["long_lines"] <= 5:  # 只报告前5个长行
                        self.issues["length"].append({
                            "type": "long_line",
                            "line": line_num,
                            "message": f"Line {line_num} is too long ({len(line_content)} chars)"
                        })

        super().generic_visit(node)


class CodeOptimizer:
    """代码优化器"""

    def __init__(self):
        self.optimizations = []
        self.project_root = project_root

    def optimize_file(self, file_path: str) -> bool:
        """优化单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # 应用各种优化
            content = self._optimize_imports(content)
            content = self._optimize_formatting(content)
            content = self._remove_unused_imports(content, file_path)
            content = self._optimize_blank_lines(content)

            # 如果有变化，写回文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True

        except Exception as e:
            print(f"Error optimizing {file_path}: {e}")

        return False

    def _optimize_imports(self, content: str) -> str:
        """优化导入语句"""
        lines = content.split('\n')
        import_lines = []
        other_lines = []
        in_imports = True

        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('import ', 'from ')) or (in_imports and (not stripped or stripped.startswith('#'))):
                import_lines.append(line)
                in_imports = True
            else:
                other_lines.append(line)
                in_imports = False

        # 排序导入语句（简单的字母排序）
        if import_lines:
            # 分组标准库导入和第三方导入
            stdlib_imports = []
            third_party_imports = []
            local_imports = []

            for line in import_lines:
                stripped = line.strip()
                if stripped.startswith(('import os', 'import sys', 'import json', 'import time', 'import uuid',
                                     'import asyncio', 'import logging', 'import re', 'from datetime',
                                     'from typing', 'from pathlib', 'from collections', 'from dataclasses',
                                     'from enum', 'from abc')):
                    stdlib_imports.append(line)
                elif stripped.startswith(('from app', 'from celery_worker')):
                    local_imports.append(line)
                else:
                    third_party_imports.append(line)

            # 重新组合
            sorted_imports = []
            if stdlib_imports:
                sorted_imports.extend(sorted(stdlib_imports))
                sorted_imports.append('')  # 空行分隔
            if third_party_imports:
                sorted_imports.extend(sorted(third_party_imports))
                sorted_imports.append('')  # 空行分隔
            if local_imports:
                sorted_imports.extend(sorted(local_imports))

            return '\n'.join(sorted_imports + other_lines)

        return content

    def _optimize_formatting(self, content: str) -> str:
        """优化格式化"""
        lines = content.split('\n')
        optimized_lines = []

        for line in lines:
            # 移除行尾空白
            line = line.rstrip()

            # 确保文件以换行符结尾
            if line or (optimized_lines and optimized_lines[-1] != ''):
                optimized_lines.append(line)

        return '\n'.join(optimized_lines) + '\n'

    def _remove_unused_imports(self, content: str, file_path: str) -> str:
        """移除未使用的导入（简化版）"""
        # 这是一个简化的实现，实际项目中可以使用 isort 或 autoflake
        try:
            tree = ast.parse(content)
            used_names = set()

            # 收集使用的名称
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    used_names.add(node.attr)

            # 简单的未使用导入检测
            lines = content.split('\n')
            filtered_lines = []

            for line in lines:
                stripped = line.strip()
                keep_line = True

                if stripped.startswith('from ') and ' import ' in stripped:
                    # 检查 from...import 语句
                    imports_part = stripped.split(' import ')[1]
                    imported_names = [name.strip().split(' as ')[0] for name in imports_part.split(',')]

                    unused_imports = []
                    for name in imported_names:
                        if name not in used_names and name != '*':
                            unused_imports.append(name)

                    if unused_imports and len(imported_names) == len(unused_imports):
                        # 所有导入都未使用
                        keep_line = False
                    elif unused_imports:
                        # 部分导入未使用，需要移除
                        active_imports = [name for name in imported_names if name not in unused_imports]
                        if active_imports:
                            module_part = stripped.split(' import ')[0]
                            line = f"{module_part} import {', '.join(active_imports)}"

                if keep_line:
                    filtered_lines.append(line)

            return '\n'.join(filtered_lines)

        except:
            return content

    def _optimize_blank_lines(self, content: str) -> str:
        """优化空行"""
        lines = content.split('\n')
        optimized_lines = []
        blank_count = 0

        for line in lines:
            if line.strip() == '':
                blank_count += 1
                if blank_count <= 2:  # 最多保留2个连续空行
                    optimized_lines.append(line)
            else:
                blank_count = 0
                optimized_lines.append(line)

        return '\n'.join(optimized_lines)


def analyze_project_structure():
    """分析项目结构"""
    print("\n" + "="*80)
    print("PROJECT STRUCTURE ANALYSIS")
    print("="*80)

    directories = [
        "app/services",
        "app/models",
        "celery_worker/workflow_nodes",
        "scripts"
    ]

    patterns = ["*.py"]

    total_files = 0
    total_lines = 0
    directory_stats = {}

    for directory in directories:
        if os.path.exists(project_root / directory):
            analyzer = CodeAnalyzer()
            results = analyzer.analyze_directory(str(project_root / directory), patterns)

            directory_stats[directory] = {
                "files": results["files_analyzed"],
                "lines": results["total_lines"],
                "issues": len(results["issues"])
            }

            total_files += results["files_analyzed"]
            total_lines += results["total_lines"]

    print(f"\nPROJECT OVERVIEW:")
    print(f"  Total Python files: {total_files}")
    print(f"  Total lines of code: {total_lines:,}")
    print(f"  Directories analyzed: {len(directory_stats)}")

    print(f"\nDIRECTORY BREAKDOWN:")
    for directory, stats in directory_stats.items():
        print(f"  {directory}:")
        print(f"    Files: {stats['files']}")
        print(f"    Lines: {stats['lines']:,}")
        print(f"    Issues: {stats['issues']}")

    return directory_stats


def main():
    """主函数"""
    print("COMPREHENSIVE CODE ANALYSIS AND OPTIMIZATION")
    print("="*80)
    print(f"Analysis started at: {datetime.now()}")
    print(f"Project root: {project_root}")

    # 1. 分析项目结构
    structure_stats = analyze_project_structure()

    # 2. 详细代码分析
    print(f"\n{'='*80}")
    print("DETAILED CODE QUALITY ANALYSIS")
    print(f"{'='*80}")

    analyzer = CodeAnalyzer()

    # 分析核心服务文件
    core_files = [
        "app/services/medical_parser.py",
        "app/services/multimodal_processor.py",
        "app/services/knowledge_graph.py",
        "app/services/intelligent_agent.py",
        "app/services/medical_agents.py",
        "app/services/agent_orchestrator.py"
    ]

    print(f"\nAnalyzing Core Service Files:")
    for file_path in core_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"  {file_path}")
            result = analyzer.analyze_file(str(full_path))

            if "error" not in result:
                analyzer.results["files_analyzed"] += 1
                analyzer.results["total_lines"] += result.get("total_lines", 0)

                for issue_type, issues in result.get("issues", {}).items():
                    analyzer.results["issues"][issue_type].extend(issues)

                analyzer.results["metrics"][file_path] = result.get("metrics", {})
            else:
                print(f"    ERROR: {result['error']}")
        else:
            print(f"  {file_path} - File not found")

    # 3. 生成优化建议
    recommendations = analyzer.generate_optimization_recommendations()

    # 4. 显示分析结果
    print(f"\n{'='*80}")
    print("ANALYSIS RESULTS")
    print(f"{'='*80}")

    print(f"\nSUMMARY:")
    print(f"  Files analyzed: {analyzer.results['files_analyzed']}")
    print(f"  Total lines: {analyzer.results['total_lines']:,}")

    total_issues = sum(len(issues) for issues in analyzer.results["issues"].values())
    print(f"  Total issues found: {total_issues}")

    print(f"\nISSUE BREAKDOWN:")
    for issue_type, issues in analyzer.results["issues"].items():
        if issues:
            print(f"  {issue_type.capitalize()}: {len(issues)}")
            # 显示前几个例子
            for issue in issues[:3]:
                print(f"    Line {issue['line']}: {issue['message']}")
            if len(issues) > 3:
                print(f"    ... and {len(issues) - 3} more")

    print(f"\nOPTIMIZATION RECOMMENDATIONS:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec['category']} (Priority: {rec['priority']})")
        print(f"     {rec['description']}")

    # 5. 代码质量评分
    quality_score = calculate_quality_score(analyzer.results, structure_stats)
    print(f"\nCODE QUALITY SCORE: {quality_score}/100")

    if quality_score >= 90:
        grade = "A (Excellent)"
        status = "Production Ready"
    elif quality_score >= 80:
        grade = "B (Good)"
        status = "Ready with Minor Improvements"
    elif quality_score >= 70:
        grade = "C (Average)"
        status = "Needs Improvements"
    elif quality_score >= 60:
        grade = "D (Poor)"
        status = "Significant Improvements Needed"
    else:
        grade = "F (Fail)"
        status = "Major Refactoring Required"

    print(f"GRADE: {grade}")
    print(f"STATUS: {status}")

    # 6. 保存分析报告
    save_analysis_report(analyzer.results, recommendations, quality_score, grade)

    # 7. 询问是否应用优化
    print(f"\n{'='*80}")
    print("OPTIMIZATION OPTIONS")
    print(f"{'='*80}")
    print("The following optimizations can be applied:")
    print("1. Organize imports (sort and group)")
    print("2. Remove unused imports")
    print("3. Fix formatting issues")
    print("4. Optimize blank lines")
    print("5. Generate code improvement suggestions")

    # 自动应用安全的优化
    print(f"\nApplying safe optimizations...")
    optimizer = CodeOptimizer()

    files_optimized = 0
    for file_path in core_files:
        full_path = project_root / file_path
        if full_path.exists():
            if optimizer.optimize_file(str(full_path)):
                files_optimized += 1
                print(f"  Optimized: {file_path}")

    print(f"\nOptimization complete: {files_optimized} files optimized")


def calculate_quality_score(results: Dict, structure_stats: Dict) -> int:
    """计算代码质量评分"""
    base_score = 100

    # 扣分项
    total_issues = sum(len(issues) for issues in results["issues"].values())
    complexity_penalty = min(len(results["issues"]["complexity"]) * 2, 20)
    length_penalty = min(len(results["issues"]["length"]) * 1, 10)
    import_penalty = min(len(results["issues"]["imports"]) * 3, 15)
    naming_penalty = min(len(results["issues"]["naming"]) * 1, 10)

    # 奖励项
    docstring_bonus = min(sum(
        metrics.get("docstrings", 0)
        for metrics in results["metrics"].values()
    ) * 0.5, 10)

    # 计算最终分数
    final_score = base_score - complexity_penalty - length_penalty - import_penalty - naming_penalty + docstring_bonus

    return max(0, min(100, int(final_score)))


def save_analysis_report(results: Dict, recommendations: List[Dict], quality_score: int, grade: str):
    """保存分析报告"""
    report_data = {
        "analysis_timestamp": datetime.now().isoformat(),
        "quality_score": quality_score,
        "grade": grade,
        "summary": {
            "files_analyzed": results["files_analyzed"],
            "total_lines": results["total_lines"],
            "total_issues": sum(len(issues) for issues in results["issues"].values())
        },
        "issues": {
            category: [
                {
                    "type": issue["type"],
                    "line": issue["line"],
                    "message": issue["message"]
                }
                for issue in issues
            ]
            for category, issues in results["issues"].items()
        },
        "recommendations": recommendations,
        "file_metrics": results["metrics"]
    }

    report_path = project_root / "code_analysis_report.json"
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n[REPORT] Analysis report saved to: {report_path}")
    except Exception as e:
        print(f"\n[ERROR] Failed to save analysis report: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPT] Analysis interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Analysis failed: {e}")
        import traceback
        traceback.print_exc()