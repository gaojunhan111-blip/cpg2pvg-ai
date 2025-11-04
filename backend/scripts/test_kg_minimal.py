#!/usr/bin/env python3
"""
Knowledge Graph Minimal Test Script
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


def test_knowledge_graph_imports():
    """测试知识图谱模块导入"""
    print_colored("Testing Knowledge Graph Module Imports", "cyan")
    print("-" * 40)

    try:
        # 测试基础模型导入
        from app.models.knowledge_graph import (
            MedicalEntityModel, ClinicalRelationshipModel,
            ClinicalContextModel, EnhancedContentModel,
            OntologyConceptModel, KnowledgeGraphJobModel
        )
        print_colored("✓ Database models import successful", "green")

        # 测试服务类导入（不包含依赖项的部分）
        from app.services.knowledge_graph import (
            MedicalEntity, EntityType, LinkedEntity,
            ClinicalRelationship, ClinicalContext,
            EnhancedContent, MedicalOntology, OntologySource
        )
        print_colored("✓ Service classes import successful", "green")

        # 测试工作流节点导入
        from celery_worker.workflow_nodes.node3_knowledge_graph import KnowledgeGraphNode
        print_colored("✓ Workflow node import successful", "green")

        return True

    except Exception as e:
        print_colored(f"Import failed: {str(e)}", "red")
        import traceback
        traceback.print_exc()
        return False


def test_data_models():
    """测试数据模型创建"""
    print_colored("Testing Data Model Creation", "blue")
    print("-" * 40)

    try:
        from app.services.knowledge_graph import (
            MedicalEntity, EntityType, LinkedEntity,
            ClinicalRelationship, ClinicalContext,
            EnhancedContent, MedicalOntology, OntologySource
        )

        # 测试医学实体创建
        entity = MedicalEntity(
            text="Type 2 Diabetes",
            entity_type=EntityType.DISEASE,
            extraction_confidence=0.9,
            source="test",
            start_position=0,
            end_position=15
        )
        print_colored(f"✓ MedicalEntity created: {entity.text} ({entity.entity_type.value})", "green")

        # 测试链接实体创建
        linked_entity = LinkedEntity(
            entity=entity,
            best_match={"preferred_name": "Diabetes Mellitus Type 2", "ontology_id": "DM2_001"},
            link_confidence=0.85
        )
        print_colored(f"✓ LinkedEntity created with confidence: {linked_entity.link_confidence:.2f}", "green")

        # 测试临床关系创建
        source_entity = MedicalEntity("Metformin", EntityType.MEDICATION, 0.95)
        target_entity = MedicalEntity("Type 2 Diabetes", EntityType.DISEASE, 0.9)

        relationship = ClinicalRelationship(
            source_entity=linked_entity,
            target_entity=LinkedEntity(source_entity),
            relationship_type="treats",
            confidence="high",
            strength=0.8
        )
        print_colored(f"✓ ClinicalRelationship created: {relationship.relationship_type}", "green")

        # 测试临床上下文创建
        context = ClinicalContext(
            primary_condition=LinkedEntity(target_entity),
            risk_factors=[],
            recommendations=[],
            warnings=[],
            completeness_score=0.9,
            confidence_score=0.85
        )
        print_colored(f"✓ ClinicalContext created with completeness: {context.completeness_score:.2f}", "green")

        # 测试增强内容创建
        enhanced_content = EnhancedContent(
            content_id="test_001",
            entities=[linked_entity],
            relationships=[relationship],
            clinical_context=context,
            processing_time=1.5,
            overall_quality=0.88
        )
        print_colored(f"✓ EnhancedContent created with quality: {enhanced_content.overall_quality:.2f}", "green")

        # 测试本体创建
        ontology = MedicalOntology(
            name="Test_Ontology",
            source=OntologySource.CUSTOM
        )
        print_colored(f"✓ MedicalOntology created: {ontology.name}", "green")

        return True

    except Exception as e:
        print_colored(f"Data model test failed: {str(e)}", "red")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_node():
    """测试工作流节点"""
    print_colored("Testing Workflow Node", "purple")
    print("-" * 40)

    try:
        from celery_worker.workflow_nodes.node3_knowledge_graph import KnowledgeGraphNode

        # 创建工作流节点实例
        node = KnowledgeGraphNode()
        print_colored("✓ KnowledgeGraphNode instance created", "green")

        # 测试节点属性
        print(f"Node ID: {node.node_id}")
        print(f"Node Name: {node.node_name}")
        print(f"Node Version: {node.node_version}")

        return True

    except Exception as e:
        print_colored(f"Workflow node test failed: {str(e)}", "red")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print_colored("Knowledge Graph Minimal Integration Test", "cyan")
    print("=" * 60)

    success_count = 0
    total_tests = 3

    # 测试1: 模块导入测试
    print_colored("\nTest 1: Module Import Test", "blue")
    if test_knowledge_graph_imports():
        success_count += 1

    # 测试2: 数据模型测试
    print_colored("\nTest 2: Data Model Test", "blue")
    if test_data_models():
        success_count += 1

    # 测试3: 工作流节点测试
    print_colored("\nTest 3: Workflow Node Test", "blue")
    if test_workflow_node():
        success_count += 1

    # 总结
    print_colored("\n" + "=" * 60, "cyan")
    print_colored("Test Summary", "cyan")
    print(f"  Passed: {success_count}/{total_tests}")

    if success_count == total_tests:
        print_colored("All tests passed! Knowledge graph core functionality is working", "green")
        print_colored("\nNext steps:", "cyan")
        print("  1. Install spaCy and transformers for full functionality")
        print("  2. Run complete end-to-end tests with real data")
        print("  3. Integrate into workflow system")
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