#!/usr/bin/env python3
"""
Architecture Validation Test
架构验证测试
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ArchitectureValidationTest:
    """架构验证测试"""

    def __init__(self):
        self.test_results = {}
        print("ARCHITECTURE VALIDATION TEST")
        print("="*60)

    def test_imports(self):
        """测试核心模块导入"""
        print("\n[TEST] Testing Core Module Imports...")

        try:
            # 测试医学解析器
            from app.services.medical_parser import HierarchicalMedicalParser
            print("[OK] Medical Parser imported")

            # 测试多模态处理器
            from app.services.multimodal_processor import MultiModalProcessor
            print("[OK] Multimodal Processor imported")

            # 测试知识图谱
            from app.services.knowledge_graph import MedicalKnowledgeGraph
            print("[OK] Knowledge Graph imported")

            # 测试智能体系统
            from app.services.agent_orchestrator import IntelligentAgentOrchestrator
            print("[OK] Agent Orchestrator imported")

            # 测试智能体
            from app.services.medical_agents import DiagnosisAgent, TreatmentAgent
            print("[OK] Medical Agents imported")

            # 测试基础智能体
            from app.services.intelligent_agent import BaseMedicalAgent
            print("[OK] Base Medical Agent imported")

            self.test_results['imports'] = {
                'success': True,
                'modules': ['medical_parser', 'multimodal_processor', 'knowledge_graph', 'agent_orchestrator', 'medical_agents', 'intelligent_agent']
            }

            return True

        except Exception as e:
            print(f"[FAIL] Import test failed: {e}")
            self.test_results['imports'] = {
                'success': False,
                'error': str(e)
            }
            return False

    def test_database_models(self):
        """测试数据库模型"""
        print("\n[TEST] Testing Database Models...")

        try:
            # 知识图谱模型
            from app.models.knowledge_graph import (
                MedicalEntityModel,
                ClinicalRelationshipModel,
                EnhancedContentModel
            )
            print("[OK] Knowledge Graph models imported")

            # 智能体模型
            from app.models.intelligent_agent import (
                AgentJobModel,
                AgentCoordinationModel,
                AgentResultModel
            )
            print("[OK] Intelligent Agent models imported")

            # 医学文档模型
            from app.models.medical_document import (
                MedicalDocumentModel,
                DocumentSectionModel
            )
            print("[OK] Medical Document models imported")

            # 多模态内容模型
            from app.models.multimodal_content import (
                ProcessedContentModel,
                TextProcessingResultModel
            )
            print("[OK] Multimodal Content models imported")

            self.test_results['database_models'] = {
                'success': True,
                'model_groups': ['knowledge_graph', 'intelligent_agent', 'medical_document', 'multimodal_content']
            }

            return True

        except Exception as e:
            print(f"[FAIL] Database models test failed: {e}")
            self.test_results['database_models'] = {
                'success': False,
                'error': str(e)
            }
            return False

    def test_workflow_nodes(self):
        """测试工作流节点"""
        print("\n[TEST] Testing Workflow Nodes...")

        try:
            # 检查工作流节点文件是否存在
            node_files = [
                'celery_worker/workflow_nodes/node1_medical_parser.py',
                'celery_worker/workflow_nodes/node2_multimodal_processor.py',
                'celery_worker/workflow_nodes/node3_knowledge_graph.py',
                'celery_worker/workflow_nodes/node4_intelligent_agents.py'
            ]

            existing_nodes = []
            for node_file in node_files:
                if os.path.exists(project_root / node_file):
                    print(f"[OK] {node_file} exists")
                    existing_nodes.append(node_file)
                else:
                    print(f"[MISSING] {node_file}")

            # 测试基础节点类
            from celery_worker.workflow.base_node import BaseWorkflowNode
            print("[OK] Base Workflow Node imported")

            self.test_results['workflow_nodes'] = {
                'success': True,
                'existing_nodes': existing_nodes,
                'total_nodes': len(node_files),
                'base_node': True
            }

            return len(existing_nodes) >= 3  # 至少3个节点存在

        except Exception as e:
            print(f"[FAIL] Workflow nodes test failed: {e}")
            self.test_results['workflow_nodes'] = {
                'success': False,
                'error': str(e)
            }
            return False

    def test_data_structures(self):
        """测试数据结构"""
        print("\n[TEST] Testing Data Structures...")

        try:
            # 智能体数据结构
            from app.services.intelligent_agent import (
                AgentType,
                AgentStatus,
                ProcessingStrategy,
                RelevantContent,
                AgentResult,
                AgentResults
            )
            print("[OK] Agent data structures imported")

            # 测试枚举值
            agent_types = list(AgentType)
            print(f"[OK] Agent types: {[t.value for t in agent_types]}")

            processing_strategies = list(ProcessingStrategy)
            print(f"[OK] Processing strategies: {[s.value for s in processing_strategies]}")

            # 知识图谱数据结构
            from app.services.knowledge_graph import (
                MedicalEntity,
                ClinicalRelationship,
                ClinicalContext
            )
            print("[OK] Knowledge graph data structures imported")

            self.test_results['data_structures'] = {
                'success': True,
                'agent_types': len(agent_types),
                'processing_strategies': len(processing_strategies),
                'structures': ['RelevantContent', 'AgentResult', 'AgentResults', 'MedicalEntity', 'ClinicalRelationship']
            }

            return True

        except Exception as e:
            print(f"[FAIL] Data structures test failed: {e}")
            self.test_results['data_structures'] = {
                'success': False,
                'error': str(e)
            }
            return False

    def test_service_instantiation(self):
        """测试服务实例化"""
        print("\n[TEST] Testing Service Instantiation...")

        try:
            # 医学处理器
            from app.services.medical_parser import HierarchicalMedicalParser
            medical_processor = HierarchicalMedicalParser()
            print("[OK] Medical Document Parser instantiated")

            # 多模态处理器
            from app.services.multimodal_processor import MultiModalProcessor
            multimodal_processor = MultiModalProcessor()
            print("[OK] MultiModal Processor instantiated")

            # 知识图谱服务
            from app.services.knowledge_graph import MedicalKnowledgeGraph
            knowledge_graph = MedicalKnowledgeGraph()
            print("[OK] Medical Knowledge Graph instantiated")

            # 智能体协调器
            from app.services.agent_orchestrator import IntelligentAgentOrchestrator
            agent_orchestrator = IntelligentAgentOrchestrator()
            print("[OK] Intelligent Agent Orchestrator instantiated")

            self.test_results['service_instantiation'] = {
                'success': True,
                'services': ['HierarchicalMedicalParser', 'MultiModalProcessor', 'MedicalKnowledgeGraph', 'IntelligentAgentOrchestrator']
            }

            return True

        except Exception as e:
            print(f"[FAIL] Service instantiation test failed: {e}")
            self.test_results['service_instantiation'] = {
                'success': False,
                'error': str(e)
            }
            return False

    def test_architecture_integrity(self):
        """测试架构完整性"""
        print("\n[TEST] Testing Architecture Integrity...")

        try:
            # 检查关键组件
            integrity_checks = {
                'medical_parser_service': False,
                'multimodal_processor_service': False,
                'knowledge_graph_service': False,
                'agent_orchestrator_service': False,
                'medical_agents': False,
                'database_models': False,
                'workflow_nodes': False
            }

            # 执行检查
            try:
                from app.services.medical_parser import HierarchicalMedicalParser
                integrity_checks['medical_parser_service'] = True
            except:
                pass

            try:
                from app.services.multimodal_processor import MultiModalProcessor
                integrity_checks['multimodal_processor_service'] = True
            except:
                pass

            try:
                from app.services.knowledge_graph import MedicalKnowledgeGraph
                integrity_checks['knowledge_graph_service'] = True
            except:
                pass

            try:
                from app.services.agent_orchestrator import IntelligentAgentOrchestrator
                integrity_checks['agent_orchestrator_service'] = True
            except:
                pass

            try:
                from app.services.medical_agents import DiagnosisAgent, TreatmentAgent
                integrity_checks['medical_agents'] = True
            except:
                pass

            try:
                from app.models.knowledge_graph import MedicalEntityModel
                integrity_checks['database_models'] = True
            except:
                pass

            # 检查工作流节点文件
            node_files = [
                'celery_worker/workflow_nodes/node1_medical_parser.py',
                'celery_worker/workflow_nodes/node2_multimodal_processor.py',
                'celery_worker/workflow_nodes/node3_knowledge_graph.py',
                'celery_worker/workflow_nodes/node4_intelligent_agents.py'
            ]

            existing_nodes = sum(1 for node in node_files if os.path.exists(project_root / node))
            if existing_nodes >= 3:
                integrity_checks['workflow_nodes'] = True

            passed_checks = sum(integrity_checks.values())
            total_checks = len(integrity_checks)

            print(f"[RESULT] Architecture integrity: {passed_checks}/{total_checks} components working")
            for component, status in integrity_checks.items():
                status_str = "[OK]" if status else "[FAIL]"
                print(f"   {status_str} {component}")

            success_rate = passed_checks / total_checks

            self.test_results['architecture_integrity'] = {
                'success': success_rate >= 0.7,  # 至少70%组件正常
                'passed_checks': passed_checks,
                'total_checks': total_checks,
                'success_rate': success_rate,
                'component_status': integrity_checks
            }

            return success_rate >= 0.7

        except Exception as e:
            print(f"[FAIL] Architecture integrity test failed: {e}")
            self.test_results['architecture_integrity'] = {
                'success': False,
                'error': str(e)
            }
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print(f"\nStarting architecture validation at: {datetime.now()}")
        print(f"Project root: {project_root}")

        test_functions = [
            ("Core Module Imports", self.test_imports),
            ("Database Models", self.test_database_models),
            ("Workflow Nodes", self.test_workflow_nodes),
            ("Data Structures", self.test_data_structures),
            ("Service Instantiation", self.test_service_instantiation),
            ("Architecture Integrity", self.test_architecture_integrity)
        ]

        passed_tests = 0

        for test_name, test_func in test_functions:
            try:
                print(f"\n{'='*60}")
                print(f"TESTING: {test_name}")
                print('='*60)

                if test_func():
                    passed_tests += 1
                    print(f"[PASS] {test_name} completed successfully")
                else:
                    print(f"[FAIL] {test_name} failed")

            except Exception as e:
                print(f"[ERROR] {test_name} encountered exception: {e}")

        self.generate_final_report(passed_tests, len(test_functions))

    def generate_final_report(self, passed_tests, total_tests):
        """生成最终报告"""
        print("\n" + "="*80)
        print("ARCHITECTURE VALIDATION REPORT")
        print("="*80)

        success_rate = passed_tests / total_tests

        print(f"\nSUMMARY:")
        print(f"   Total tests: {total_tests}")
        print(f"   Passed tests: {passed_tests}")
        print(f"   Success rate: {success_rate*100:.1f}%")

        print(f"\nDETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            status = "[PASS]" if result.get('success', False) else "[FAIL]"
            print(f"   {status} {test_name.replace('_', ' ').title()}")

        print(f"\nARCHITECTURE ASSESSMENT:")
        if success_rate >= 0.9:
            print("   [EXCELLENT] Architecture is robust and well-structured")
            print("   [READY] System is ready for advanced testing and deployment")
            grade = "A"
        elif success_rate >= 0.7:
            print("   [GOOD] Architecture is mostly functional")
            print("   [MINOR] Some components need attention")
            grade = "B"
        elif success_rate >= 0.5:
            print("   [FAIR] Architecture has significant issues")
            print("   [WORK] Requires substantial debugging")
            grade = "C"
        else:
            print("   [POOR] Architecture has major problems")
            print("   [URGENT] Requires extensive rework")
            grade = "D"

        print(f"   Overall Grade: {grade}")

        # 保存测试报告
        report_data = {
            "test_timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate * 100,
            "grade": grade,
            "test_results": self.test_results
        }

        report_path = project_root / "architecture_validation_report.json"
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
            print(f"\n[SAVE] Validation report saved to: {report_path}")
        except Exception as e:
            print(f"\n[ERROR] Failed to save validation report: {e}")


def main():
    """主函数"""
    try:
        validator = ArchitectureValidationTest()
        validator.run_all_tests()

    except KeyboardInterrupt:
        print("\n\n[INTERRUPT] Validation interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Validation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()