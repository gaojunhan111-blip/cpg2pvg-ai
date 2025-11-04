#!/usr/bin/env python3
"""
手动依赖关系分析器
Manual Dependency Analyzer
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

def analyze_imports_in_file(file_path: str) -> List[str]:
    """分析文件中的导入语句"""
    imports = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 匹配import语句
        import_patterns = [
            r'from\s+app\.([a-zA-Z0-9_\.]+)\s+import\s+([a-zA-Z0-9_,\s]+)',
            r'import\s+app\.([a-zA-Z0-9_\.]+)'
        ]

        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    # from app.xxx import yyy
                    imports.append(f"app.{match[0]}")
                else:
                    # import app.xxx
                    imports.append(f"app.{match}")

    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")

    return imports

def manual_dependency_analysis():
    """手动分析依赖关系"""
    project_root = Path(".")

    # 找到所有Python文件
    python_files = list(project_root.glob("**/*.py"))

    # 过滤掉__pycache__和其他不需要的文件
    python_files = [f for f in python_files if "__pycache__" not in str(f)]

    print(f"Found {len(python_files)} Python files")

    # 按模块分类
    modules = {
        'api': [],
        'services': [],
        'models': [],
        'core': [],
        'schemas': [],
        'workflows': [],
        'tasks': [],
        'utils': [],
        'enums': [],
        'other': []
    }

    for file_path in python_files:
        path_str = str(file_path)

        if 'api' in path_str:
            modules['api'].append(file_path)
        elif 'services' in path_str:
            modules['services'].append(file_path)
        elif 'models' in path_str:
            modules['models'].append(file_path)
        elif 'core' in path_str:
            modules['core'].append(file_path)
        elif 'schemas' in path_str:
            modules['schemas'].append(file_path)
        elif 'workflows' in path_str:
            modules['workflows'].append(file_path)
        elif 'tasks' in path_str:
            modules['tasks'].append(file_path)
        elif 'utils' in path_str:
            modules['utils'].append(file_path)
        elif 'enums' in path_str:
            modules['enums'].append(file_path)
        else:
            modules['other'].append(file_path)

    # 分析每个文件的导入
    all_imports = {}
    file_dependencies = defaultdict(set)

    for file_path in python_files:
        imports = analyze_imports_in_file(file_path)
        all_imports[str(file_path)] = imports

        # 分析依赖关系
        for import_stmt in imports:
            # 尝试匹配导入语句到具体的文件
            parts = import_stmt.split('.')
            if len(parts) >= 2:
                target_module = parts[1]

                # 查找对应的目标文件
                for category, files in modules.items():
                    if category == target_module:
                        for target_file in files:
                            file_dependencies[str(file_path)].add(str(target_file))

    # 打印分析结果
    print("\n=== 模块统计 ===")
    for category, files in modules.items():
        print(f"{category}: {len(files)} files")

    print("\n=== API层依赖分析 ===")
    for api_file in modules['api']:
        deps = file_dependencies.get(str(api_file), set())
        if deps:
            print(f"\n{api_file}:")
            for dep in deps:
                print(f"  -> {dep}")

    print("\n=== Services层依赖分析 ===")
    for service_file in modules['services']:
        deps = file_dependencies.get(str(service_file), set())
        if deps:
            print(f"\n{service_file}:")
            for dep in deps:
                print(f"  -> {dep}")

    print("\n=== 依赖矩阵 ===")
    categories = ['api', 'services', 'models', 'core', 'schemas', 'workflows', 'tasks', 'utils', 'enums']

    matrix = {}
    for from_cat in categories:
        matrix[from_cat] = {}
        for to_cat in categories:
            matrix[from_cat][to_cat] = 0

    # 计算依赖关系
    for file_path, deps in file_dependencies.items():
        from_cat = None
        for cat, files in modules.items():
            if Path(file_path) in files:
                from_cat = cat
                break

        if from_cat:
            for dep in deps:
                to_cat = None
                for cat, files in modules.items():
                    if Path(dep) in files:
                        to_cat = cat
                        break

                if to_cat and from_cat != to_cat and to_cat in matrix and from_cat in matrix:
                    matrix[from_cat][to_cat] += 1

    # 打印矩阵
    print("\n" + "".ljust(12), end="")
    for cat in categories:
        print(f"{cat[:8].ljust(8)}", end=" ")
    print()

    for from_cat in categories:
        print(f"{from_cat[:12].ljust(12)}", end="")
        for to_cat in categories:
            print(f"{str(matrix[from_cat][to_cat]).ljust(8)}", end=" ")
        print()

    # 检查关键接口问题
    print("\n=== 接口一致性检查 ===")

    # 检查API是否直接访问Models
    api_direct_models = []
    for api_file in modules['api']:
        deps = file_dependencies.get(str(api_file), set())
        for dep in deps:
            if 'models' in dep:
                api_direct_models.append(f"{api_file} -> {dep}")

    if api_direct_models:
        print("警告: API层直接访问Models层:")
        for issue in api_direct_models:
            print(f"  {issue}")
    else:
        print("✅ API层未直接访问Models层")

    # 检查Core层是否依赖上层模块
    core_violations = []
    for core_file in modules['core']:
        deps = file_dependencies.get(str(core_file), set())
        for dep in deps:
            if any(x in dep for x in ['api', 'services', 'workflows']):
                core_violations.append(f"{core_file} -> {dep}")

    if core_violations:
        print("警告: Core层依赖上层模块:")
        for issue in core_violations:
            print(f"  {issue}")
    else:
        print("✅ Core层未依赖上层模块")

    # 检查工作流编排器集成
    print("\n=== 工作流编排器集成检查 ===")
    workflow_files = [f for f in modules['services'] if 'workflow' in str(f)]
    print(f"找到工作流相关服务: {len(workflow_files)}")

    for wf_file in workflow_files:
        deps = file_dependencies.get(str(wf_file), set())
        print(f"\n{wf_file}:")
        print(f"  依赖数: {len(deps)}")
        for dep in list(deps)[:5]:  # 只显示前5个
            print(f"    -> {Path(dep).name}")
        if len(deps) > 5:
            print(f"    ... 还有 {len(deps) - 5} 个依赖")

if __name__ == "__main__":
    manual_dependency_analysis()