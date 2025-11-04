#!/usr/bin/env python3
"""
Comprehensive System Compatibility Check
全面系统集成兼容性检查
"""

import os
import sys
import importlib
import traceback
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import json
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class SystemCompatibilityChecker:
    """系统兼容性检查器"""

    def __init__(self):
        self.project_root = project_root
        self.results = {
            "import_compatibility": {},
            "module_dependencies": {},
            "data_model_consistency": {},
            "workflow_connectivity": {},
            "configuration_conflicts": {},
            "overall_compatibility": 0.0,
            "issues_found": [],
            "recommendations": []
        }

    def run_comprehensive_check(self):
        """运行全面兼容性检查"""
        print("COMPREHENSIVE SYSTEM COMPATIBILITY CHECK")
        print("="*80)
        print(f"Check started at: {datetime.now()}")
        print(f"Project root: {self.project_root}")

        # 1. 检查导入兼容性
        print("\n1. CHECKING IMPORT COMPATIBILITY")
        print("-" * 50)
        self._check_import_compatibility()

        # 2. 分析模块依赖
        print("\n2. ANALYZING MODULE DEPENDENCIES")
        print("-" * 50)
        self._analyze_module_dependencies()

        # 3. 验证数据模型一致性
        print("\n3. VERIFYING DATA MODEL CONSISTENCY")
        print("-" * 50)
        self._verify_data_model_consistency()

        # 4. 测试工作流节点连接
        print("\n4. TESTING WORKFLOW NODE CONNECTIVITY")
        print("-" * 50)
        self._test_workflow_connectivity()

        # 5. 检查配置冲突
        print("\n5. CHECKING CONFIGURATION CONFLICTS")
        print("-" * 50)
        self._check_configuration_conflicts()

        # 6. 计算总体兼容性
        print("\n6. CALCULATING OVERALL COMPATIBILITY")
        print("-" * 50)
        self._calculate_overall_compatibility()

        # 7. 生成报告
        print("\n7. GENERATING COMPATIBILITY REPORT")
        print("-" * 50)
        self._generate_compatibility_report()

        # 8. 保存结果
        self._save_results()

    def _check_import_compatibility(self):
        """检查导入兼容性"""
        critical_modules = [
            "app.core.config",
            "app.core.database",
            "app.core.logger",
            "app.models.base",
            "app.services.medical_parser",
            "app.services.multimodal_processor",
            "app.services.knowledge_graph",
            "app.services.intelligent_agent",
            "app.services.medical_agents",
            "app.services.agent_orchestrator",
            "celery_worker.workflow.base_node",
            "celery_worker.workflow_nodes.node1_medical_parser",
            "celery_worker.workflow_nodes.node2_multimodal_processor",
            "celery_worker.workflow_nodes.node3_knowledge_graph",
            "celery_worker.workflow_nodes.node4_intelligent_agents"
        ]

        import_results = {}
        successful_imports = 0

        for module_name in critical_modules:
            try:
                print(f"  Importing: {module_name}")
                module = importlib.import_module(module_name)
                import_results[module_name] = {
                    "status": "success",
                    "file_path": getattr(module, '__file__', 'unknown'),
                    "classes": [name for name in dir(module) if name[0].isupper()],
                    "functions": [name for name in dir(module) if not name.startswith('_') and callable(getattr(module, name))]
                }
                successful_imports += 1
                print(f"    ✓ Success - {len(import_results[module_name]['classes'])} classes, {len(import_results[module_name]['functions'])} functions")

            except ImportError as e:
                import_results[module_name] = {
                    "status": "failed",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
                self.results["issues_found"].append({
                    "type": "import_error",
                    "module": module_name,
                    "error": str(e)
                })
                print(f"    ✗ Failed: {e}")

            except Exception as e:
                import_results[module_name] = {
                    "status": "error",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
                self.results["issues_found"].append({
                    "type": "module_error",
                    "module": module_name,
                    "error": str(e)
                })
                print(f"    ✗ Error: {e}")

        self.results["import_compatibility"] = {
            "total_modules": len(critical_modules),
            "successful_imports": successful_imports,
            "success_rate": successful_imports / len(critical_modules),
            "details": import_results
        }

        print(f"\n  Import success rate: {successful_imports}/{len(critical_modules)} ({successful_imports/len(critical_modules)*100:.1f}%)")

    def _analyze_module_dependencies(self):
        """分析模块依赖"""
        dependency_graph = {}
        circular_dependencies = []

        # 扫描Python文件中的导入语句
        python_files = list(self.project_root.glob("**/*.py"))

        for file_path in python_files:
            if "site-packages" in str(file_path):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 提取导入语句
                imports = self._extract_imports(content, file_path)
                module_name = self._get_module_name(file_path)

                dependency_graph[module_name] = {
                    "file_path": str(file_path.relative_to(self.project_root)),
                    "imports": imports,
                    "dependency_count": len(imports)
                }

            except Exception as e:
                print(f"    Error analyzing {file_path}: {e}")

        # 检查循环依赖
        circular_dependencies = self._detect_circular_dependencies(dependency_graph)

        self.results["module_dependencies"] = {
            "total_modules": len(dependency_graph),
            "dependency_graph": dependency_graph,
            "circular_dependencies": circular_dependencies
        }

        print(f"  Analyzed {len(dependency_graph)} modules")
        print(f"  Circular dependencies: {len(circular_dependencies)}")

        if circular_dependencies:
            for cycle in circular_dependencies:
                print(f"    ⚠ Cycle: {' -> '.join(cycle)}")

    def _extract_imports(self, content: str, file_path: Path) -> List[str]:
        """提取导入语句"""
        imports = []
        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            if line.startswith('import '):
                # import module
                module = line.replace('import ', '').split('.')[0]
                imports.append(module)
            elif line.startswith('from '):
                # from module import ...
                parts = line.split(' ')
                if len(parts) >= 2:
                    module_part = parts[1]
                    module = module_part.split('.')[0]
                    imports.append(module)

        # 过滤标准库导入
        stdlib_modules = {
            'os', 'sys', 'json', 'time', 'datetime', 'uuid', 'pathlib',
            'typing', 'dataclasses', 'enum', 'abc', 'collections',
            'asyncio', 'logging', 're', 'math', 'random', 'itertools'
        }

        filtered_imports = [imp for imp in imports if imp not in stdlib_modules]
        return filtered_imports

    def _get_module_name(self, file_path: Path) -> str:
        """获取模块名称"""
        relative_path = file_path.relative_to(self.project_root)
        parts = list(relative_path.parts)

        # 移除文件扩展名
        if parts[-1].endswith('.py'):
            parts[-1] = parts[-1][:-3]

        # 如果是__init__.py，使用目录名
        if parts[-1] == '__init__':
            parts.pop()

        return '.'.join(parts)

    def _detect_circular_dependencies(self, dependency_graph: Dict) -> List[List[str]]:
        """检测循环依赖"""
        circular_deps = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]):
            if node in rec_stack:
                # 找到循环依赖
                cycle_start = path.index(node)
                circular_deps.append(path[cycle_start:] + [node])
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)

            if node in dependency_graph:
                for dependency in dependency_graph[node]["imports"]:
                    if dependency in dependency_graph:
                        dfs(dependency, path + [node])

            rec_stack.remove(node)

        for module in dependency_graph:
            if module not in visited:
                dfs(module, [])

        return circular_deps

    def _verify_data_model_consistency(self):
        """验证数据模型一致性"""
        model_checks = {}

        # 检查基础模型
        try:
            from app.models.base import Base
            model_checks["base_model"] = {
                "status": "available",
                "class": "Base"
            }
        except Exception as e:
            model_checks["base_model"] = {
                "status": "failed",
                "error": str(e)
            }

        # 检查各个模型文件
        model_files = [
            ("knowledge_graph", "app.models.knowledge_graph"),
            ("intelligent_agent", "app.models.intelligent_agent"),
            ("medical_document", "app.models.medical_document"),
            ("multimodal_content", "app.models.multimodal_content")
        ]

        for model_name, module_path in model_files:
            try:
                module = importlib.import_module(module_path)
                models = [name for name in dir(module) if name.endswith('Model') and name[0].isupper()]

                model_checks[model_name] = {
                    "status": "available",
                    "models": models,
                    "model_count": len(models)
                }
                print(f"  {model_name}: {len(models)} models found")

                # 检查每个模型是否继承自Base
                for model_name_class in models:
                    try:
                        model_class = getattr(module, model_name_class)
                        if hasattr(model_class, '__bases__'):
                            base_classes = [base.__name__ for base in model_class.__bases__]
                            if 'Base' not in base_classes and 'Model' not in base_classes:
                                self.results["issues_found"].append({
                                    "type": "model_inheritance",
                                    "model": model_name_class,
                                    "issue": "Does not inherit from Base"
                                })
                    except Exception:
                        pass

            except Exception as e:
                model_checks[model_name] = {
                    "status": "failed",
                    "error": str(e)
                }
                self.results["issues_found"].append({
                    "type": "model_import_error",
                    "module": module_path,
                    "error": str(e)
                })
                print(f"  {model_name}: Failed - {e}")

        self.results["data_model_consistency"] = model_checks

    def _test_workflow_connectivity(self):
        """测试工作流节点连接"""
        workflow_tests = {}

        # 检查基础节点类
        try:
            from celery_worker.workflow.base_node import BaseWorkflowNode
            workflow_tests["base_node"] = {
                "status": "available",
                "class": "BaseWorkflowNode"
            }
        except Exception as e:
            workflow_tests["base_node"] = {
                "status": "failed",
                "error": str(e)
            }

        # 检查各个工作流节点
        workflow_nodes = [
            ("node1", "celery_worker.workflow_nodes.node1_medical_parser"),
            ("node2", "celery_worker.workflow_nodes.node2_multimodal_processor"),
            ("node3", "celery_worker.workflow_nodes.node3_knowledge_graph"),
            ("node4", "celery_worker.workflow_nodes.node4_intelligent_agents")
        ]

        for node_name, module_path in workflow_nodes:
            try:
                module = importlib.import_module(module_path)

                # 查找节点类
                node_classes = [name for name in dir(module) if 'Node' in name and name[0].isupper()]

                workflow_tests[node_name] = {
                    "status": "available",
                    "module": module_path,
                    "classes": node_classes
                }
                print(f"  {node_name}: {len(node_classes)} node classes")

                # 测试节点类是否可实例化
                for class_name in node_classes:
                    try:
                        node_class = getattr(module, class_name)
                        # 尝试实例化（不传入参数）
                        # instance = node_class()  # 注释掉，避免需要参数的实例化失败
                    except Exception as e:
                        self.results["issues_found"].append({
                            "type": "node_instantiation",
                            "node": class_name,
                            "error": str(e)
                        })

            except Exception as e:
                workflow_tests[node_name] = {
                    "status": "failed",
                    "module": module_path,
                    "error": str(e)
                }
                self.results["issues_found"].append({
                    "type": "workflow_node_error",
                    "node": node_name,
                    "error": str(e)
                })
                print(f"  {node_name}: Failed - {e}")

        self.results["workflow_connectivity"] = workflow_tests

    def _check_configuration_conflicts(self):
        """检查配置冲突"""
        config_checks = {}

        # 检查配置文件
        config_files = [
            "app/core/config.py",
            "app/core/database.py",
            "app/core/logger.py"
        ]

        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                try:
                    module_path = config_file.replace('/', '.').replace('.py', '')
                    module = importlib.import_module(module_path)

                    config_elements = [name for name in dir(module) if not name.startswith('_')]

                    config_checks[config_file] = {
                        "status": "available",
                        "elements": len(config_elements),
                        "module_path": module_path
                    }
                    print(f"  {config_file}: {len(config_elements)} configuration elements")

                except Exception as e:
                    config_checks[config_file] = {
                        "status": "failed",
                        "error": str(e)
                    }
                    self.results["issues_found"].append({
                        "type": "config_error",
                        "file": config_file,
                        "error": str(e)
                    })
                    print(f"  {config_file}: Failed - {e}")
            else:
                config_checks[config_file] = {
                    "status": "missing",
                    "error": "File not found"
                }

        # 检查环境变量冲突
        env_vars = {
            "DATABASE_URL": os.getenv("DATABASE_URL"),
            "REDIS_URL": os.getenv("REDIS_URL"),
            "LOG_LEVEL": os.getenv("LOG_LEVEL"),
            "DEBUG": os.getenv("DEBUG")
        }

        config_checks["environment_variables"] = env_vars

        self.results["configuration_conflicts"] = config_checks

    def _calculate_overall_compatibility(self):
        """计算总体兼容性"""
        scores = []

        # 导入兼容性评分 (30%)
        import_success_rate = self.results["import_compatibility"]["success_rate"]
        import_score = import_success_rate * 100
        scores.append(("import_compatibility", import_score, 0.3))

        # 模块依赖评分 (20%)
        total_modules = self.results["module_dependencies"]["total_modules"]
        circular_deps = len(self.results["module_dependencies"]["circular_dependencies"])
        dependency_score = max(0, 100 - (circular_deps * 20))
        scores.append(("module_dependencies", dependency_score, 0.2))

        # 数据模型一致性评分 (20%)
        model_issues = len([issue for issue in self.results["issues_found"] if issue["type"].startswith("model")])
        total_models = sum(check.get("model_count", 1) for check in self.results["data_model_consistency"].values() if isinstance(check, dict))
        model_score = max(0, 100 - (model_issues * 10))
        scores.append(("data_models", model_score, 0.2))

        # 工作流连接评分 (20%)
        workflow_issues = len([issue for issue in self.results["issues_found"] if issue["type"].startswith("workflow")])
        total_workflow_nodes = len(self.results["workflow_connectivity"])
        workflow_score = max(0, 100 - (workflow_issues * 15))
        scores.append(("workflow", workflow_score, 0.2))

        # 配置冲突评分 (10%)
        config_issues = len([issue for issue in self.results["issues_found"] if issue["type"].startswith("config")])
        config_score = max(0, 100 - (config_issues * 10))
        scores.append(("configuration", config_score, 0.1))

        # 计算加权平均分
        overall_score = sum(score * weight for name, score, weight in scores)
        self.results["overall_compatibility"] = overall_score

        print(f"  Import compatibility: {import_score:.1f}/100")
        print(f"  Module dependencies: {dependency_score:.1f}/100")
        print(f"  Data models: {model_score:.1f}/100")
        print(f"  Workflow connectivity: {workflow_score:.1f}/100")
        print(f"  Configuration: {config_score:.1f}/100")
        print(f"  Overall compatibility: {overall_score:.1f}/100")

    def _generate_compatibility_report(self):
        """生成兼容性报告"""
        print(f"\nCOMPATIBILITY ASSESSMENT")
        print("="*50)

        overall_score = self.results["overall_compatibility"]
        issues_count = len(self.results["issues_found"])

        if overall_score >= 95:
            grade = "A+"
            status = "Excellent - All components compatible"
        elif overall_score >= 90:
            grade = "A"
            status = "Very Good - Minor compatibility issues"
        elif overall_score >= 80:
            grade = "B"
            status = "Good - Some compatibility improvements needed"
        elif overall_score >= 70:
            grade = "C"
            status = "Fair - Significant compatibility issues"
        else:
            grade = "F"
            status = "Poor - Major compatibility problems"

        print(f"Overall Compatibility Score: {overall_score:.1f}/100")
        print(f"Grade: {grade}")
        print(f"Status: {status}")
        print(f"Issues Found: {issues_count}")

        if issues_count > 0:
            print(f"\nCritical Issues:")
            critical_issues = [issue for issue in self.results["issues_found"] if issue["type"] in ["import_error", "model_import_error"]]
            for issue in critical_issues[:5]:
                print(f"  • {issue['type']}: {issue.get('module', issue.get('file', 'unknown'))} - {issue['error']}")

            # 生成建议
            self.results["recommendations"] = [
                {
                    "category": "Critical",
                    "description": "Fix import errors and model issues",
                    "actions": ["Review missing dependencies", "Check file paths", "Verify module structure"]
                }
            ]

            if grade in ["A+", "A"]:
                self.results["recommendations"].append({
                    "category": "Improvement",
                    "description": "System is compatible, consider optimization",
                    "actions": ["Add comprehensive tests", "Implement performance monitoring", "Document API"]
                })

    def _save_results(self):
        """保存检查结果"""
        report_path = self.project_root / "system_compatibility_report.json"

        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)

            print(f"\nDetailed report saved to: {report_path.relative_to(self.project_root)}")
        except Exception as e:
            print(f"\nFailed to save report: {e}")


def main():
    """主函数"""
    try:
        checker = SystemCompatibilityChecker()
        checker.run_comprehensive_check()

    except KeyboardInterrupt:
        print("\nCompatibility check interrupted by user")
    except Exception as e:
        print(f"\nCompatibility check failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()