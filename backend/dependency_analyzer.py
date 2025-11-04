#!/usr/bin/env python3
"""
模块依赖关系分析器
Module Dependency Analyzer
"""

import ast
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque
import re


class DependencyAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.modules = {}
        self.dependencies = defaultdict(set)
        self.import_graph = defaultdict(set)
        self.module_hierarchy = {}

    def analyze_project(self):
        """分析整个项目的依赖关系"""
        print("开始分析项目依赖关系...")

        # 扫描所有Python文件
        python_files = list(self.project_root.glob("**/*.py"))
        print(f"发现 {len(python_files)} 个Python文件")

        # 分析每个文件
        for file_path in python_files:
            if "__pycache__" in str(file_path):
                continue

            module_info = self._analyze_file(file_path)
            if module_info:
                self.modules[str(file_path.relative_to(self.project_root))] = module_info

        # 构建依赖图
        self._build_dependency_graph()

        # 分析模块层次结构
        self._analyze_module_hierarchy()

        return self.generate_report()

    def _analyze_file(self, file_path: Path) -> Optional[Dict]:
        """分析单个Python文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 解析AST
            tree = ast.parse(content)

            # 提取模块信息
            imports = []
            functions = []
            classes = []
            constants = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}")
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            constants.append(target.id)

            return {
                'imports': imports,
                'functions': functions,
                'classes': classes,
                'constants': constants,
                'ast_tree': tree,
                'content': content
            }

        except Exception as e:
            print(f"分析文件失败 {file_path}: {e}")
            return None

    def _build_dependency_graph(self):
        """构建依赖关系图"""
        for file_path, module_info in self.modules.items():
            # 确定模块类型
            module_type = self._get_module_type(file_path)

            # 分析导入依赖
            for import_stmt in module_info['imports']:
                target_module = self._resolve_import(import_stmt, file_path)
                if target_module and target_module in self.modules:
                    self.dependencies[file_path].add(target_module)
                    self.import_graph[module_type].add(self._get_module_type(target_module))

    def _get_module_type(self, file_path: str) -> str:
        """获取模块类型"""
        if 'api' in file_path:
            return 'api'
        elif 'services' in file_path:
            return 'services'
        elif 'models' in file_path:
            return 'models'
        elif 'core' in file_path:
            return 'core'
        elif 'schemas' in file_path:
            return 'schemas'
        elif 'workflows' in file_path:
            return 'workflows'
        elif 'tasks' in file_path:
            return 'tasks'
        elif 'utils' in file_path:
            return 'utils'
        elif 'enums' in file_path:
            return 'enums'
        else:
            return 'other'

    def _resolve_import(self, import_stmt: str, current_file: str) -> Optional[str]:
        """解析导入语句，返回目标文件路径"""
        # 处理相对导入
        if import_stmt.startswith('.'):
            return None  # 暂时跳过相对导入

        # 处理项目内部导入
        if import_stmt.startswith('app.'):
            # 将 app.xxx.yyy 转换为文件路径
            parts = import_stmt.split('.')

            # 处理特殊情况
            if len(parts) >= 3:
                # app.xxx.zzz -> xxx/zzz.py 或 xxx/zzz/__init__.py
                module_path = '/'.join(parts[1:-1])
                module_name = parts[-1]

                # 尝试多种可能的文件路径
                possible_paths = [
                    f"{module_path}/{module_name}.py",
                    f"{module_path}/{module_name}/__init__.py",
                    f"{module_path}.py" if len(parts) == 2 else None
                ]

                for path in possible_paths:
                    if path and path in self.modules:
                        return path

        return None

    def _analyze_module_hierarchy(self):
        """分析模块层次结构"""
        hierarchy = {
            'api': set(),
            'services': set(),
            'models': set(),
            'core': set(),
            'schemas': set(),
            'workflows': set(),
            'tasks': set(),
            'utils': set(),
            'enums': set(),
            'other': set()
        }

        for file_path in self.modules.keys():
            module_type = self._get_module_type(file_path)
            hierarchy[module_type].add(file_path)

        self.module_hierarchy = hierarchy

    def detect_circular_dependencies(self) -> List[List[str]]:
        """检测循环依赖"""
        def dfs(node: str, visited: Set[str], rec_stack: Set[str], path: List[str]) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.dependencies.get(node, []):
                if neighbor not in visited:
                    result = dfs(neighbor, visited, rec_stack, path.copy())
                    if result:
                        return result
                elif neighbor in rec_stack:
                    # 找到循环
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]

            rec_stack.remove(node)
            return None

        visited = set()
        cycles = []

        for node in self.modules.keys():
            if node not in visited:
                cycle = dfs(node, visited, set(), [])
                if cycle:
                    cycles.append(cycle)

        return cycles

    def analyze_coupling(self) -> Dict:
        """分析模块间耦合度"""
        coupling_analysis = {}

        # 计算各模块的耦合度
        for module_type, modules in self.module_hierarchy.items():
            if not modules:
                continue

            # 出度耦合（该模块依赖其他模块）
            outbound_deps = set()
            # 入度耦合（其他模块依赖该模块）
            inbound_deps = set()

            for module in modules:
                outbound_deps.update(self.dependencies.get(module, []))

                # 查找依赖该模块的其他模块
                for other_module, deps in self.dependencies.items():
                    if module in deps:
                        inbound_deps.add(other_module)

            # 计算耦合度指标
            coupling_analysis[module_type] = {
                'module_count': len(modules),
                'outbound_coupling': len(outbound_deps),
                'inbound_coupling': len(inbound_deps),
                'total_coupling': len(outbound_deps) + len(inbound_deps),
                'instability': len(outbound_deps) / (len(outbound_deps) + len(inbound_deps)) if (len(outbound_deps) + len(inbound_deps)) > 0 else 0,
                'outbound_modules': list(outbound_deps),
                'inbound_modules': list(inbound_deps)
            }

        return coupling_analysis

    def check_interface_consistency(self) -> Dict:
        """检查接口一致性"""
        interface_issues = []

        # 检查API层与服务层的接口契约
        api_modules = self.module_hierarchy.get('api', set())
        service_modules = self.module_hierarchy.get('services', set())

        for api_file in api_modules:
            api_info = self.modules[api_file]

            # 检查API是否正确导入和使用了服务
            for import_stmt in api_info['imports']:
                if 'services' in import_stmt:
                    service_name = import_stmt.split('.')[-1]
                    # 检查对应的服务是否存在
                    service_found = False
                    for service_file in service_modules:
                        if service_name in service_file or service_name.replace('_', '') in service_file:
                            service_found = True
                            break

                    if not service_found:
                        interface_issues.append({
                            'type': 'missing_service',
                            'api_file': api_file,
                            'service_name': service_name,
                            'import_stmt': import_stmt
                        })

        # 检查Models层一致性
        model_modules = self.module_hierarchy.get('models', set())
        schema_modules = self.module_hierarchy.get('schemas', set())

        # 检查模型与模式的一致性
        for model_file in model_modules:
            model_info = self.modules[model_file]
            model_name = Path(model_file).stem

            # 查找对应的schema
            schema_found = False
            for schema_file in schema_modules:
                if model_name in schema_file:
                    schema_found = True
                    break

            if not schema_found and model_name != 'base':
                interface_issues.append({
                    'type': 'missing_schema',
                    'model_file': model_file,
                    'model_name': model_name
                })

        return {
            'issues': interface_issues,
            'api_service_alignment': len([i for i in interface_issues if i['type'] == 'missing_service']) == 0,
            'model_schema_alignment': len([i for i in interface_issues if i['type'] == 'missing_schema']) == 0
        }

    def generate_dependency_matrix(self) -> Dict:
        """生成依赖矩阵"""
        matrix = {}
        module_types = list(self.module_hierarchy.keys())

        for from_type in module_types:
            matrix[from_type] = {}
            for to_type in module_types:
                if from_type == to_type:
                    matrix[from_type][to_type] = 0
                else:
                    count = len(self.import_graph.get(from_type, set()) & set([to_type]))
                    matrix[from_type][to_type] = count

        return matrix

    def generate_report(self) -> Dict:
        """生成完整的依赖分析报告"""
        print("生成依赖分析报告...")

        # 检测循环依赖
        circular_deps = self.detect_circular_dependencies()

        # 分析耦合度
        coupling_analysis = self.analyze_coupling()

        # 检查接口一致性
        interface_consistency = self.check_interface_consistency()

        # 生成依赖矩阵
        dependency_matrix = self.generate_dependency_matrix()

        # 分析架构层次
        architecture_analysis = self._analyze_architecture_layers()

        return {
            'project_summary': {
                'total_modules': len(self.modules),
                'module_types': {k: len(v) for k, v in self.module_hierarchy.items()},
                'total_dependencies': sum(len(deps) for deps in self.dependencies.values())
            },
            'dependency_matrix': dependency_matrix,
            'circular_dependencies': circular_deps,
            'coupling_analysis': coupling_analysis,
            'interface_consistency': interface_consistency,
            'architecture_analysis': architecture_analysis,
            'detailed_dependencies': {
                module: list(deps) for module, deps in self.dependencies.items()
            },
            'module_hierarchy': {k: list(v) for k, v in self.module_hierarchy.items()}
        }

    def _analyze_architecture_layers(self) -> Dict:
        """分析架构层次是否合理"""
        violations = []

        # 检查架构违规
        # 1. API层不应该直接依赖Models层（应该通过Services层）
        api_modules = self.module_hierarchy.get('api', set())
        model_modules = self.module_hierarchy.get('models', set())

        for api_file in api_modules:
            direct_model_deps = []
            for dep in self.dependencies.get(api_file, []):
                if dep in model_modules:
                    direct_model_deps.append(dep)

            if direct_model_deps:
                violations.append({
                    'type': 'api_direct_model_access',
                    'api_file': api_file,
                    'violations': direct_model_deps,
                    'severity': 'high'
                })

        # 2. Core层不应该依赖上层的Services或API
        core_modules = self.module_hierarchy.get('core', set())

        for core_file in core_modules:
            upper_layer_deps = []
            for dep in self.dependencies.get(core_file, []):
                dep_type = self._get_module_type(dep)
                if dep_type in ['api', 'services', 'workflows']:
                    upper_layer_deps.append(dep)

            if upper_layer_deps:
                violations.append({
                    'type': 'core_depends_on_upper_layer',
                    'core_file': core_file,
                    'violations': upper_layer_deps,
                    'severity': 'high'
                })

        return {
            'violations': violations,
            'compliance_score': max(0, 100 - len(violations) * 10),
            'recommendations': self._generate_architecture_recommendations(violations)
        }

    def _generate_architecture_recommendations(self, violations: List[Dict]) -> List[str]:
        """生成架构改进建议"""
        recommendations = []

        violation_types = set(v['type'] for v in violations)

        if 'api_direct_model_access' in violation_types:
            recommendations.append("API层应该通过Services层访问数据，避免直接依赖Models层")

        if 'core_depends_on_upper_layer' in violation_types:
            recommendations.append("Core基础设施层不应该依赖上层的业务逻辑模块")

        # 检查耦合度过高的模块
        coupling_analysis = self.analyze_coupling()
        high_coupling_modules = [
            module for module, analysis in coupling_analysis.items()
            if analysis['total_coupling'] > 10
        ]

        if high_coupling_modules:
            recommendations.append(f"以下模块耦合度过高，建议重构: {', '.join(high_coupling_modules)}")

        return recommendations


def main():
    if len(sys.argv) != 2:
        print("用法: python dependency_analyzer.py <project_root>")
        sys.exit(1)

    project_root = sys.argv[1]
    analyzer = DependencyAnalyzer(project_root)

    print("开始分析项目依赖关系...")
    report = analyzer.analyze_project()

    # 保存报告
    report_path = os.path.join(project_root, "dependency_analysis_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n依赖分析报告已保存到: {report_path}")

    # 打印摘要
    print("\n=== 依赖分析摘要 ===")
    summary = report['project_summary']
    print(f"总模块数: {summary['total_modules']}")
    print(f"模块类型分布: {summary['module_types']}")
    print(f"总依赖关系数: {summary['total_dependencies']}")

    # 打印循环依赖
    if report['circular_dependencies']:
        print(f"\n警告: 发现 {len(report['circular_dependencies'])} 个循环依赖:")
        for i, cycle in enumerate(report['circular_dependencies'], 1):
            print(f"  {i}. {' -> '.join(cycle)}")
    else:
        print("\n[OK] 未发现循环依赖")

    # 打印接口一致性
    interface = report['interface_consistency']
    print(f"\n接口一致性检查:")
    print(f"  API-Service对齐: {'[OK]' if interface['api_service_alignment'] else '[FAIL]'}")
    print(f"  Model-Schema对齐: {'[OK]' if interface['model_schema_alignment'] else '[FAIL]'}")
    print(f"  问题数量: {len(interface['issues'])}")

    # 打印架构分析
    arch = report['architecture_analysis']
    print(f"\n架构合规性评分: {arch['compliance_score']}/100")
    if arch['violations']:
        print(f"架构违规数量: {len(arch['violations'])}")

    # 打印高耦合模块
    high_coupling = [
        module for module, analysis in report['coupling_analysis'].items()
        if analysis['total_coupling'] > 10
    ]
    if high_coupling:
        print(f"\n警告: 高耦合模块: {', '.join(high_coupling)}")


if __name__ == "__main__":
    main()