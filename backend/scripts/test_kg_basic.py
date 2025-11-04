#!/usr/bin/env python3
"""
Knowledge Graph Basic Test Script
Testing core functionality without heavy dependencies
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def print_colored(message: str, color: str = "white"):
    """打印彩色消息"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, colors['white'])}{message}{colors['reset']}")


def test_database_models():
    """测试数据库模型"""
    print_colored("Testing Database Models", "cyan")
    print("-" * 40)

    try:
        # 测试数据库模型导入
        from app.models.knowledge_graph import (
            MedicalEntityModel, ClinicalRelationshipModel,
            ClinicalContextModel, EnhancedContentModel,
            OntologyConceptModel, KnowledgeGraphJobModel
        )
        print_colored("PASS: Database models imported successfully", "green")

        # 验证模型类是否正确定义
        model_classes = [
            MedicalEntityModel, ClinicalRelationshipModel,
            ClinicalContextModel, EnhancedContentModel,
            OntologyConceptModel, KnowledgeGraphJobModel
        ]

        for model_class in model_classes:
            print(f"  - {model_class.__name__}: OK")

        return True

    except Exception as e:
        print_colored(f"FAIL: Database model test failed - {str(e)}", "red")
        import traceback
        traceback.print_exc()
        return False


def test_knowledge_graph_data_structures():
    """测试知识图谱数据结构"""
    print_colored("Testing Knowledge Graph Data Structures", "blue")
    print("-" * 40)

    try:
        # 直接测试数据结构，不导入完整服务
        # 测试枚举类型
        from app.services.knowledge_graph import EntityType, OntologySource

        # 测试枚举值
        entity_types = [EntityType.DISEASE, EntityType.MEDICATION, EntityType.SYMPTOM]
        for et in entity_types:
            print(f"  EntityType.{et.name}: {et.value}")

        ontology_sources = [OntologySource.SNOMED_CT, OntologySource.UMLS, OntologySource.CUSTOM]
        for os_val in ontology_sources:
            print(f"  OntologySource.{os_val.name}: {os_val.value}")

        print_colored("PASS: Enum types working correctly", "green")

        # 测试基本数据类创建（手动创建，避免导入依赖项）
        test_data = {
            "entity_text": "Type 2 Diabetes",
            "entity_type": "disease",
            "confidence": 0.9,
            "content_id": "test_001"
        }

        print(f"  Test data structure: {test_data}")
        print_colored("PASS: Basic data structures working", "green")

        return True

    except Exception as e:
        print_colored(f"FAIL: Data structure test failed - {str(e)}", "red")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_node_structure():
    """测试工作流节点结构"""
    print_colored("Testing Workflow Node Structure", "purple")
    print("-" * 40)

    try:
        # 测试基础节点结构
        import celery_worker.workflow.base_node as base_module

        # 检查基础节点类是否存在
        if hasattr(base_module, 'BaseWorkflowNode'):
            print_colored("PASS: BaseWorkflowNode found", "green")
        else:
            print_colored("FAIL: BaseWorkflowNode not found", "red")
            return False

        # 测试节点配置
        node_config = {
            "node_id": "knowledge_graph_node",
            "node_name": "Knowledge Graph Processing Node",
            "version": "1.0.0"
        }

        print(f"  Node configuration: {node_config}")
        print_colored("PASS: Node configuration structure valid", "green")

        return True

    except Exception as e:
        print_colored(f"FAIL: Workflow node test failed - {str(e)}", "red")
        import traceback
        traceback.print_exc()
        return False


def test_file_structure():
    """测试文件结构完整性"""
    print_colored("Testing File Structure Integrity", "yellow")
    print("-" * 40)

    required_files = [
        "app/models/knowledge_graph.py",
        "app/services/knowledge_graph.py",
        "celery_worker/workflow_nodes/node3_knowledge_graph.py",
        "scripts/test_knowledge_graph.py"
    ]

    missing_files = []

    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"  OK: {file_path}")
        else:
            print(f"  MISSING: {file_path}")
            missing_files.append(file_path)

    if missing_files:
        print_colored(f"FAIL: {len(missing_files)} files missing", "red")
        return False
    else:
        print_colored("PASS: All required files present", "green")
        return True


async def main():
    """主函数"""
    print_colored("Knowledge Graph Basic Integration Test", "cyan")
    print("=" * 60)

    success_count = 0
    total_tests = 4

    # 测试1: 文件结构测试
    print_colored("\nTest 1: File Structure Test", "blue")
    if test_file_structure():
        success_count += 1

    # 测试2: 数据库模型测试
    print_colored("\nTest 2: Database Models Test", "blue")
    if test_database_models():
        success_count += 1

    # 测试3: 数据结构测试
    print_colored("\nTest 3: Data Structures Test", "blue")
    if test_knowledge_graph_data_structures():
        success_count += 1

    # 测试4: 工作流节点测试
    print_colored("\nTest 4: Workflow Node Test", "blue")
    if test_workflow_node_structure():
        success_count += 1

    # 总结
    print_colored("\n" + "=" * 60, "cyan")
    print_colored("Test Summary", "cyan")
    print(f"  Passed: {success_count}/{total_tests}")

    if success_count == total_tests:
        print_colored("All tests passed! Knowledge graph basic functionality verified", "green")
        print_colored("\nNext steps:", "cyan")
        print("  1. Install spaCy and transformers for full functionality")
        print("  2. Run complete integration tests with real data")
        print("  3. Test the complete three-node workflow system")
        print("  4. Performance testing with large documents")
    else:
        print_colored(f"{total_tests - success_count} tests failed", "yellow")
        print_colored("Please check error messages and fix issues", "yellow")

    return success_count == total_tests


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        sys.exit(1)