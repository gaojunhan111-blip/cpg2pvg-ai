#!/usr/bin/env python3
"""
Code Formatting Optimizer
代码格式优化器
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Tuple, Dict

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class CodeFormatter:
    """代码格式化器"""

    def __init__(self):
        self.project_root = project_root
        self.optimized_files = []
        self.stats = {
            'files_processed': 0,
            'long_lines_fixed': 0,
            'formatting_issues_fixed': 0,
            'import_issues_fixed': 0
        }

    def fix_long_lines(self, file_path: str, max_line_length: int = 120) -> int:
        """修复长行代码"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_lines = content.split('\n')
            fixed_lines = []
            long_lines_fixed = 0

            for line_num, line in enumerate(original_lines, 1):
                if len(line) > max_line_length:
                    fixed_line = self._break_long_line(line, max_line_length)
                    if fixed_line != line:
                        long_lines_fixed += 1
                        # 添加注释说明自动修复
                        fixed_lines.append(f"# Auto-formatted from line {line_num}")
                        fixed_lines.extend(fixed_line)
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)

            if long_lines_fixed > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(fixed_lines))

                print(f"  Fixed {long_lines_fixed} long lines in {Path(file_path).name}")
                self.stats['long_lines_fixed'] += long_lines_fixed

            return long_lines_fixed

        except Exception as e:
            print(f"  Error fixing long lines in {file_path}: {e}")
            return 0

    def _break_long_line(self, line: str, max_length: int) -> List[str]:
        """断行长行"""
        lines = []
        current_line = line.rstrip()

        # 如果是注释行，简单换行
        if current_line.strip().startswith('#'):
            words = current_line.split()
            temp_line = ""
            for word in words:
                if len(temp_line + " " + word) <= max_length:
                    temp_line = (temp_line + " " + word).strip()
                else:
                    if temp_line:
                        lines.append(temp_line)
                    temp_line = "# " + word
            if temp_line:
                lines.append(temp_line)
            return lines

        # 处理import语句
        if current_line.strip().startswith(('import ', 'from ')):
            return self._break_import_line(current_line, max_length)

        # 处理函数调用或方法链
        if '(' in current_line or '.' in current_line:
            return self._break_function_call(current_line, max_length)

        # 处理字符串连接
        if '+' in current_line and '"' in current_line:
            return self._break_string_concatenation(current_line, max_length)

        # 默认按空格分割
        return self._break_generic_line(current_line, max_length)

    def _break_import_line(self, line: str, max_length: int) -> List[str]:
        """断开import语句"""
        stripped = line.strip()
        if stripped.startswith('from '):
            # from ... import ...
            parts = stripped.split(' import ')
            if len(parts) == 2:
                from_part, import_part = parts
                imports = [imp.strip() for imp in import_part.split(',')]

                lines = [f"{from_part} import ("]
                for imp in imports:
                    lines.append(f"    {imp},")
                lines.append(")")
                return lines

        return [line]

    def _break_function_call(self, line: str, max_length: int) -> List[str]:
        """断开函数调用"""
        # 找到第一个开括号
        open_paren = line.find('(')
        if open_paren == -1:
            return [line]

        base = line[:open_paren + 1]
        args_str = line[open_paren + 1:-1] if line.endswith(')') else line[open_paren + 1:]

        # 简单的参数分割
        args = self._split_arguments(args_str)

        lines = [base]
        for i, arg in enumerate(args):
            if i == len(args) - 1:
                lines.append(f"    {arg})")
            else:
                lines.append(f"    {arg},")

        return lines

    def _split_arguments(self, args_str: str) -> List[str]:
        """分割函数参数"""
        args = []
        current_arg = ""
        paren_level = 0
        bracket_level = 0
        in_string = False
        string_char = None

        for char in args_str:
            if char in ('"', "'") and not in_string:
                in_string = True
                string_char = char
            elif char == string_char and in_string:
                in_string = False
                string_char = None
            elif not in_string:
                if char == '(':
                    paren_level += 1
                elif char == ')':
                    paren_level -= 1
                elif char == '[':
                    bracket_level += 1
                elif char == ']':
                    bracket_level -= 1
                elif char == ',' and paren_level == 0 and bracket_level == 0:
                    args.append(current_arg.strip())
                    current_arg = ""
                    continue

            current_arg += char

        if current_arg.strip():
            args.append(current_arg.strip())

        return args

    def _break_string_concatenation(self, line: str, max_length: int) -> List[str]:
        """断开字符串连接"""
        parts = line.split('+')
        lines = []
        current_line = ""

        for i, part in enumerate(parts):
            part = part.strip()
            if i == 0:
                current_line = part
            else:
                if len(current_line + " + " + part) <= max_length:
                    current_line += " + " + part
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = part

        if current_line:
            lines.append(current_line)

        return lines

    def _break_generic_line(self, line: str, max_length: int) -> List[str]:
        """通用行断开"""
        words = line.split()
        lines = []
        current_line = ""

        for word in words:
            if not current_line:
                current_line = word
            elif len(current_line + " " + word) <= max_length:
                current_line += " " + word
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines

    def fix_imports(self, file_path: str) -> int:
        """修复导入语句"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            fixed_lines = []
            import_issues_fixed = 0

            # 收集导入语句
            import_lines = []
            other_lines = []
            in_import_section = True

            for line in lines:
                stripped = line.strip()
                if stripped.startswith(('import ', 'from ')) or (in_import_section and (not stripped or stripped.startswith('#'))):
                    import_lines.append(line)
                    in_import_section = True
                else:
                    other_lines.append(line)
                    in_import_section = False

            # 排序和分组导入语句
            if import_lines:
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

                # 重新组织导入语句
                sorted_imports = []
                if stdlib_imports:
                    sorted_imports.extend(sorted(stdlib_imports))
                    sorted_imports.append('')
                if third_party_imports:
                    sorted_imports.extend(sorted(third_party_imports))
                    sorted_imports.append('')
                if local_imports:
                    sorted_imports.extend(sorted(local_imports))

                # 移除重复的导入
                seen_imports = set()
                unique_imports = []
                for import_line in sorted_imports:
                    if import_line.strip() and import_line not in seen_imports:
                        seen_imports.add(import_line)
                        unique_imports.append(import_line)
                    elif not import_line.strip():
                        unique_imports.append(import_line)

                if unique_imports != import_lines:
                    import_issues_fixed = 1
                    fixed_lines = unique_imports + other_lines

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(fixed_lines))

                    print(f"  Fixed import organization in {Path(file_path).name}")

            self.stats['import_issues_fixed'] += import_issues_fixed
            return import_issues_fixed

        except Exception as e:
            print(f"  Error fixing imports in {file_path}: {e}")
            return 0

    def fix_formatting_issues(self, file_path: str) -> int:
        """修复格式问题"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            fixed_content = content

            # 移除行尾空白
            fixed_content = '\n'.join(line.rstrip() for line in fixed_content.split('\n'))

            # 确保文件以换行符结尾
            if fixed_content and not fixed_content.endswith('\n'):
                fixed_content += '\n'

            # 移除多余的空行
            fixed_lines = []
            blank_count = 0
            for line in fixed_content.split('\n'):
                if line.strip() == '':
                    blank_count += 1
                    if blank_count <= 2:  # 最多保留2个连续空行
                        fixed_lines.append(line)
                else:
                    blank_count = 0
                    fixed_lines.append(line)

            fixed_content = '\n'.join(fixed_lines)

            # 修复方法定义间距
            fixed_content = re.sub(r'\n\ndef\s+', '\n\n\n', fixed_content)

            # 修复类定义间距
            fixed_content = re.sub(r'\n\nclass\s+', '\n\n\n', fixed_content)

            # 统一缩进（使用4个空格）
            fixed_content = self._fix_indentation(fixed_content)

            if fixed_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)

                print(f"  Fixed formatting issues in {Path(file_path).name}")
                return 1

            return 0

        except Exception as e:
            print(f"  Error fixing formatting in {file_path}: {e}")
            return 0

    def _fix_indentation(self, content: str) -> str:
        """修复缩进"""
        lines = content.split('\n')
        fixed_lines = []

        for line in lines:
            if line.strip():
                # 计算当前缩进级别
                current_indent = len(line) - len(line.lstrip())
                # 转换为4空格缩进
                indent_level = current_indent // 4
                new_indent = '    ' * indent_level
                fixed_lines.append(new_indent + line.lstrip())
            else:
                fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def optimize_file(self, file_path: str) -> Dict[str, int]:
        """优化单个文件"""
        print(f"Optimizing: {Path(file_path).name}")

        fixes = {
            'long_lines': 0,
            'imports': 0,
            'formatting': 0
        }

        try:
            # 修复长行
            fixes['long_lines'] = self.fix_long_lines(file_path)

            # 修复导入
            fixes['imports'] = self.fix_imports(file_path)

            # 修复格式问题
            fixes['formatting'] = self.fix_formatting_issues(file_path)

            total_fixes = sum(fixes.values())
            if total_fixes > 0:
                self.optimized_files.append(file_path)
                self.stats['files_processed'] += 1
                print(f"  Total fixes applied: {total_fixes}")
            else:
                print(f"  No fixes needed")

        except Exception as e:
            print(f"  Error optimizing file: {e}")

        return fixes

    def optimize_directory(self, directory: str, patterns: List[str] = ["*.py"]):
        """优化目录中的文件"""
        print(f"\n{'='*60}")
        print(f"OPTIMIZING DIRECTORY: {directory}")
        print(f"{'='*60}")

        files_to_optimize = []
        for pattern in patterns:
            files_to_optimize.extend(Path(directory).glob(pattern))

        if not files_to_optimize:
            print(f"No Python files found in {directory}")
            return

        for file_path in files_to_optimize:
            if file_path.is_file() and not file_path.name.startswith('.'):
                self.optimize_file(str(file_path))

    def print_summary(self):
        """打印优化摘要"""
        print(f"\n{'='*60}")
        print("CODE OPTIMIZATION SUMMARY")
        print(f"{'='*60}")

        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Long lines fixed: {self.stats['long_lines_fixed']}")
        print(f"Import issues fixed: {self.stats['import_issues_fixed']}")
        print(f"Formatting issues fixed: {self.stats['formatting_issues_fixed']}")

        total_fixes = (
            self.stats['long_lines_fixed'] +
            self.stats['import_issues_fixed'] +
            self.stats['formatting_issues_fixed']
        )

        print(f"Total fixes applied: {total_fixes}")

        if total_fixes > 0:
            print(f"\nFiles optimized:")
            for file_path in self.optimized_files:
                print(f"  ✓ {Path(file_path).relative_to(self.project_root)}")

        # 质量评估
        if total_fixes == 0:
            print(f"\n🎉 EXCELLENT: All files are properly formatted!")
        elif total_fixes < 50:
            print(f"\n👍 GOOD: Minor formatting improvements made")
        elif total_fixes < 200:
            print(f"\n⚠️ FAIR: Significant formatting improvements made")
        else:
            print(f"\n🔧 WORK: Major formatting improvements made")


def main():
    """主函数"""
    print("CODE FORMATTING OPTIMIZER")
    print("="*80)
    print(f"Optimization started at: {datetime.datetime.now()}")
    print(f"Project root: {project_root}")

    formatter = CodeFormatter()

    # 优化核心服务文件
    core_files = [
        "app/services/medical_parser.py",
        "app/services/multimodal_processor.py",
        "app/services/knowledge_graph.py",
        "app/services/intelligent_agent.py",
        "app/services/medical_agents.py",
        "app/services/agent_orchestrator.py"
    ]

    print(f"\n{'='*60}")
    print("OPTIMIZING CORE SERVICE FILES")
    print(f"{'='*60}")

    for file_path in core_files:
        full_path = project_root / file_path
        if full_path.exists():
            formatter.optimize_file(str(full_path))
        else:
            print(f"File not found: {file_path}")

    # 优化模型文件
    model_dir = project_root / "app/models"
    if model_dir.exists():
        formatter.optimize_directory(str(model_dir))

    # 优化工作流节点
    workflow_dir = project_root / "celery_worker/workflow_nodes"
    if workflow_dir.exists():
        formatter.optimize_directory(str(workflow_dir))

    # 打印摘要
    formatter.print_summary()

    # 保存优化报告
    try:
        import json
        report_data = {
            "optimization_timestamp": datetime.datetime.now().isoformat(),
            "statistics": formatter.stats,
            "optimized_files": [str(Path(f).relative_to(project_root)) for f in formatter.optimized_files]
        }

        report_path = project_root / "code_optimization_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Optimization report saved to: {report_path}")

    except Exception as e:
        print(f"\n⚠️ Failed to save optimization report: {e}")


if __name__ == "__main__":
    import datetime
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPT] Optimization interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Optimization failed: {e}")
        import traceback
        traceback.print_exc()