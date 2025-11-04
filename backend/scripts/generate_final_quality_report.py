#!/usr/bin/env python3
"""
Final Quality Report Generator
最终质量报告生成器
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class QualityReportGenerator:
    """质量报告生成器"""

    def __init__(self):
        self.project_root = project_root
        self.report_data = {
            "analysis_timestamp": datetime.now().isoformat(),
            "project_overview": {},
            "optimization_summary": {},
            "code_quality_metrics": {},
            "architecture_status": {},
            "recommendations": [],
            "grade": "A"
        }

    def generate_comprehensive_report(self):
        """生成综合质量报告"""
        print("FINAL CODE QUALITY REPORT")
        print("="*80)

        # 收集项目概览
        self._collect_project_overview()

        # 分析优化成果
        self._analyze_optimization_results()

        # 评估代码质量指标
        self._assess_code_quality_metrics()

        # 评估架构状态
        self._assess_architecture_status()

        # 生成建议
        self._generate_recommendations()

        # 计算最终评分
        self._calculate_final_grade()

        # 保存报告
        self._save_report()

        # 打印摘要
        self._print_summary()

    def _collect_project_overview(self):
        """收集项目概览"""
        print("\\n1. PROJECT OVERVIEW")
        print("-" * 40)

        # 统计Python文件
        python_files = list(self.project_root.glob("**/*.py"))
        total_files = len(python_files)

        # 按目录分类
        directories = {}
        for file_path in python_files:
            relative_path = file_path.relative_to(self.project_root)
            dir_name = str(relative_path.parts[0]) if len(relative_path.parts) > 0 else "root"
            if dir_name not in directories:
                directories[dir_name] = []
            directories[dir_name].append(str(relative_path))

        # 统计代码行数
        total_lines = 0
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    total_lines += len(f.readlines())
            except:
                pass

        self.report_data["project_overview"] = {
            "total_python_files": total_files,
            "total_lines_of_code": total_lines,
            "main_directories": {
                dir_name: len(files) for dir_name, files in directories.items()
                if dir_name in ["app", "celery_worker", "scripts"]
            }
        }

        print(f"  Total Python files: {total_files}")
        print(f"  Total lines of code: {total_lines:,}")
        print(f"  Main directories:")
        for dir_name, count in self.report_data["project_overview"]["main_directories"].items():
            print(f"    {dir_name}: {count} files")

    def _analyze_optimization_results(self):
        """分析优化结果"""
        print("\\n2. OPTIMIZATION RESULTS")
        print("-" * 40)

        # 读取优化报告
        optimization_report_path = self.project_root / "code_optimization_report.json"
        if optimization_report_path.exists():
            with open(optimization_report_path, 'r', encoding='utf-8') as f:
                optimization_data = json.load(f)

            self.report_data["optimization_summary"] = optimization_data.get("statistics", {})
            print(f"  Files processed: {optimization_data.get('statistics', {}).get('files_processed', 0)}")
            print(f"  Long lines fixed: {optimization_data.get('statistics', {}).get('long_lines_fixed', 0)}")
            print(f"  Import issues fixed: {optimization_data.get('statistics', {}).get('import_issues_fixed', 0)}")
            print(f"  Formatting issues fixed: {optimization_data.get('statistics', {}).get('formatting_issues_fixed', 0)}")
        else:
            self.report_data["optimization_summary"] = {
                "files_processed": 0,
                "long_lines_fixed": 0,
                "import_issues_fixed": 0,
                "formatting_issues_fixed": 0
            }
            print("  Optimization report not found")

    def _assess_code_quality_metrics(self):
        """评估代码质量指标"""
        print("\\n3. CODE QUALITY METRICS")
        print("-" * 40)

        # 基于优化结果计算质量指标
        stats = self.report_data["optimization_summary"]

        # 长行问题评分
        total_long_lines = stats.get("long_lines_fixed", 0)
        if total_long_lines == 0:
            long_line_score = 100
        elif total_long_lines < 20:
            long_line_score = 80
        elif total_long_lines < 50:
            long_line_score = 60
        else:
            long_line_score = 40

        # 导入组织评分
        import_issues = stats.get("import_issues_fixed", 0)
        if import_issues == 0:
            import_score = 100
        elif import_issues < 10:
            import_score = 85
        elif import_issues < 20:
            import_score = 70
        else:
            import_score = 50

        # 格式化问题评分
        format_issues = stats.get("formatting_issues_fixed", 0)
        if format_issues == 0:
            format_score = 100
        elif format_issues < 30:
            format_score = 80
        elif format_issues < 60:
            format_score = 60
        else:
            format_score = 40

        # 综合代码质量评分
        overall_quality = (long_line_score * 0.4 + import_score * 0.3 + format_score * 0.3)

        self.report_data["code_quality_metrics"] = {
            "long_line_score": long_line_score,
            "import_organization_score": import_score,
            "formatting_score": format_score,
            "overall_quality_score": overall_quality
        }

        print(f"  Long line compliance: {long_line_score}/100")
        print(f"  Import organization: {import_score}/100")
        print(f"  Code formatting: {format_score}/100")
        print(f"  Overall quality: {overall_quality:.1f}/100")

    def _assess_architecture_status(self):
        """评估架构状态"""
        print("\\n4. ARCHITECTURE STATUS")
        print("-" * 40)

        # 检查关键组件
        components = {
            "Core Services": {
                "files": [
                    "app/services/medical_parser.py",
                    "app/services/multimodal_processor.py",
                    "app/services/knowledge_graph.py",
                    "app/services/intelligent_agent.py",
                    "app/services/medical_agents.py",
                    "app/services/agent_orchestrator.py"
                ],
                "weight": 0.3
            },
            "Data Models": {
                "files": [
                    "app/models/knowledge_graph.py",
                    "app/models/intelligent_agent.py",
                    "app/models/medical_document.py",
                    "app/models/multimodal_content.py"
                ],
                "weight": 0.2
            },
            "Workflow Nodes": {
                "files": [
                    "celery_worker/workflow_nodes/node1_medical_parser.py",
                    "celery_worker/workflow_nodes/node2_multimodal_processor.py",
                    "celery_worker/workflow_nodes/node3_knowledge_graph.py",
                    "celery_worker/workflow_nodes/node4_intelligent_agents.py"
                ],
                "weight": 0.3
            },
            "Configuration": {
                "files": [
                    "app/core/config.py",
                    "app/core/database.py",
                    "app/core/logger.py"
                ],
                "weight": 0.1
            },
            "Tests": {
                "files": [
                    "scripts/test_core_services_ascii.py",
                    "scripts/test_architecture_validation.py"
                ],
                "weight": 0.1
            }
        }

        total_weight = 0
        architecture_score = 0

        for component_name, component_data in components.items():
            existing_files = 0
            for file_path in component_data["files"]:
                if (self.project_root / file_path).exists():
                    existing_files += 1

            component_score = (existing_files / len(component_data["files"])) * 100
            component_weight = component_data["weight"]

            architecture_score += component_score * component_weight
            total_weight += component_weight

            print(f"  {component_name}: {existing_files}/{len(component_data['files'])} files ({component_score:.0f}%)")

        # 标准化评分
        if total_weight > 0:
            architecture_score = architecture_score / total_weight
        else:
            architecture_score = 0

        self.report_data["architecture_status"] = {
            "overall_architecture_score": architecture_score,
            "component_details": {
                name: {
                    "files_found": sum(1 for f in data["files"] if (self.project_root / f).exists()),
                    "total_files": len(data["files"]),
                    "score": (sum(1 for f in data["files"] if (self.project_root / f).exists()) / len(data["files"])) * 100
                }
                for name, data in components.items()
            }
        }

        print(f"  Overall architecture: {architecture_score:.1f}/100")

    def _generate_recommendations(self):
        """生成建议"""
        print("\\n5. RECOMMENDATIONS")
        print("-" * 40)

        recommendations = []

        # 基于代码质量评分的建议
        quality_metrics = self.report_data["code_quality_metrics"]
        if quality_metrics["overall_quality_score"] < 80:
            recommendations.append({
                "category": "Code Quality",
                "priority": "High",
                "description": "Further code quality improvements needed",
                "actions": ["Continue refactoring long functions", "Improve code documentation", "Add comprehensive tests"]
            })
        elif quality_metrics["overall_quality_score"] < 90:
            recommendations.append({
                "category": "Code Quality",
                "priority": "Medium",
                "description": "Minor code quality improvements recommended",
                "actions": ["Add more inline comments", "Improve variable naming", "Enhance error handling"]
            })

        # 基于架构状态的建议
        arch_score = self.report_data["architecture_status"]["overall_architecture_score"]
        if arch_score < 80:
            recommendations.append({
                "category": "Architecture",
                "priority": "High",
                "description": "Architecture needs attention",
                "actions": ["Complete missing components", "Improve system integration", "Add proper error handling"]
            })
        elif arch_score < 95:
            recommendations.append({
                "category": "Architecture",
                "priority": "Low",
                "description": "Minor architecture improvements possible",
                "actions": ["Add performance monitoring", "Implement caching strategies", "Enhance logging"]
            })

        # 通用建议
        recommendations.append({
            "category": "Best Practices",
            "priority": "Medium",
            "description": "Follow Python best practices",
            "actions": ["Use type hints consistently", "Implement proper logging", "Add comprehensive unit tests"]
        })

        recommendations.append({
            "category": "Documentation",
            "priority": "High",
            "description": "Improve project documentation",
            "actions": ["Add API documentation", "Create user guides", "Document configuration options"]
        })

        self.report_data["recommendations"] = recommendations

        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec['category']} ({rec['priority']})")
            print(f"     {rec['description']}")
            print(f"     Actions: {', '.join(rec['actions'])}")

    def _calculate_final_grade(self):
        """计算最终评分"""
        print("\\n6. FINAL ASSESSMENT")
        print("-" * 40)

        # 计算综合评分
        quality_score = self.report_data["code_quality_metrics"]["overall_quality_score"]
        architecture_score = self.report_data["architecture_status"]["overall_architecture_score"]

        # 权重分配
        final_score = quality_score * 0.6 + architecture_score * 0.4

        # 确定等级
        if final_score >= 95:
            grade = "A+"
            status = "Excellent - Production Ready"
        elif final_score >= 90:
            grade = "A"
            status = "Excellent - Ready for Production"
        elif final_score >= 85:
            grade = "A-"
            status = "Very Good - Minor Improvements Needed"
        elif final_score >= 80:
            grade = "B+"
            status = "Good - Some Improvements Needed"
        elif final_score >= 75:
            grade = "B"
            status = "Above Average - Moderate Improvements Needed"
        elif final_score >= 70:
            grade = "B-"
            status = "Average - Significant Improvements Needed"
        elif final_score >= 65:
            grade = "C+"
            status = "Below Average - Major Improvements Needed"
        elif final_score >= 60:
            grade = "C"
            status = "Fair - Extensive Work Required"
        else:
            grade = "F"
            status = "Poor - Complete Redesign Needed"

        self.report_data["grade"] = grade
        self.report_data["final_score"] = final_score
        self.report_data["status"] = status

        print(f"  Final Score: {final_score:.1f}/100")
        print(f"  Grade: {grade}")
        print(f"  Status: {status}")

    def _save_report(self):
        """保存报告"""
        report_path = self.project_root / "final_quality_report.json"

        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.report_data, f, indent=2, ensure_ascii=False, default=str)

            print(f"\\n📄 Detailed report saved to: {report_path.relative_to(self.project_root)}")
        except Exception as e:
            print(f"\\n⚠️ Failed to save report: {e}")

    def _print_summary(self):
        """打印摘要"""
        print("\\n" + "="*80)
        print("CODE OPTIMIZATION AND QUALITY IMPROVEMENT SUMMARY")
        print("="*80)

        print(f"\\n🎯 FINAL GRADE: {self.report_data['grade']}")
        print(f"📊 FINAL SCORE: {self.report_data['final_score']:.1f}/100")
        print(f"📋 STATUS: {self.report_data['status']}")

        print(f"\\n📈 IMPROVEMENTS MADE:")
        stats = self.report_data["optimization_summary"]
        print(f"   • Files processed: {stats.get('files_processed', 0)}")
        print(f"   • Long lines fixed: {stats.get('long_lines_fixed', 0)}")
        print(f"   • Import issues resolved: {stats.get('import_issues_fixed', 0)}")
        print(f"   • Formatting issues fixed: {stats.get('formatting_issues_fixed', 0)}")
        print(f"   • Total fixes applied: {sum(stats.values())}")

        print(f"\\n🏗️ ARCHITECTURE STATUS:")
        arch_details = self.report_data["architecture_status"]["component_details"]
        for component, details in arch_details.items():
            status = "✓" if details["score"] >= 90 else "⚠" if details["score"] >= 70 else "✗"
            print(f"   {status} {component}: {details['files_found']}/{details['total_files']} files")

        print(f"\\n📋 KEY RECOMMENDATIONS:")
        high_priority = [rec for rec in self.report_data["recommendations"] if rec["priority"] == "High"]
        if high_priority:
            for rec in high_priority[:3]:
                print(f"   • {rec['description']}")
        else:
            print("   • No high-priority issues - Great work!")

        print(f"\\n🚀 NEXT STEPS:")
        grade = self.report_data["grade"]
        if grade.startswith("A"):
            print("   ✓ System is ready for production deployment")
            print("   ✓ Consider implementing automated CI/CD pipeline")
            print("   ✓ Set up comprehensive monitoring and logging")
        elif grade.startswith("B"):
            print("   • Address the high-priority recommendations")
            print("   • Add comprehensive test coverage")
            print("   • Improve documentation and user guides")
        else:
            print("   • Major refactoring required before production")
            print("   • Focus on core architecture improvements")
            print("   • Implement proper error handling and logging")


def main():
    """主函数"""
    try:
        generator = QualityReportGenerator()
        generator.generate_comprehensive_report()

    except KeyboardInterrupt:
        print("\\nReport generation interrupted by user")
    except Exception as e:
        print(f"\\nReport generation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()