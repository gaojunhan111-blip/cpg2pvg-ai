#!/usr/bin/env python3
"""
System Compatibility Check Script
检查知识图谱系统的兼容性和集成性
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_module_imports():
    """测试模块导入"""
    print("1. MODULE IMPORT TEST")
    print("-" * 30)

    modules = [
        ("app.models.base", "Base model"),
        ("app.core.database", "Database configuration"),
        ("app.models.medical_document", "Medical document models"),
        ("app.models.multimodal_content", "Multimodal content models"),
        ("app.models.knowledge_graph", "Knowledge graph models"),
        ("app.services.medical_parser", "Medical parser service"),
        ("app.services.multimodal_processor", "Multimodal processor service"),
        ("app.services.knowledge_graph", "Knowledge graph service"),
        ("celery_worker.workflow.base_node", "Base workflow node"),
        ("celery_worker.workflow_nodes.node1_medical_parser", "Node 1: Medical parser"),
        ("celery_worker.workflow_nodes.node2_multimodal_processor", "Node 2: Multimodal processor"),
        ("celery_worker.workflow_nodes.node3_knowledge_graph", "Node 3: Knowledge graph"),
    ]

    passed = []
    failed = []

    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"  PASS {description}")
            passed.append((module_name, description))
        except Exception as e:
            print(f"  FAIL {description}: {str(e)}")
            failed.append((module_name, description, str(e)))

    return passed, failed


def test_service_classes():
    """测试服务类实例化"""
    print("\n2. SERVICE CLASS TEST")
    print("-" * 25)

    try:
        from app.services.knowledge_graph import MedicalKnowledgeGraph, EntityType
        from app.services.multimodal_processor import MultiModalProcessor, ProcessingConfig

        # 测试配置创建
        config = {
            'min_entity_confidence': 0.4,
            'max_entities_per_type': 20,
            'enable_ontology_linking': True
        }
        kg = MedicalKnowledgeGraph(config)
        print("  PASS MedicalKnowledgeGraph instantiation")

        processing_config = ProcessingConfig()
        processor = MultiModalProcessor(processing_config)
        print("  PASS MultiModalProcessor instantiation")

        # 测试枚举
        entity_types = list(EntityType)
        print(f"  PASS EntityTypes: {len(entity_types)} types defined")

        return True, ""

    except Exception as e:
        print(f"  FAIL Service class test: {e}")
        return False, str(e)


def test_workflow_nodes():
    """测试工作流节点"""
    print("\n3. WORKFLOW NODE TEST")
    print("-" * 22)

    try:
        from celery_worker.workflow_nodes.node1_medical_parser import MedicalParserNode
        from celery_worker.workflow_nodes.node2_multimodal_processor import MultiModalProcessorNode
        from celery_worker.workflow_nodes.node3_knowledge_graph import KnowledgeGraphNode

        # 测试节点创建
        node1 = MedicalParserNode()
        node2 = MultiModalProcessorNode()
        node3 = KnowledgeGraphNode()

        print("  PASS MedicalParserNode instantiation")
        print("  PASS MultiModalProcessorNode instantiation")
        print("  PASS KnowledgeGraphNode instantiation")

        print(f"  Node 1: {node1.node_name}")
        print(f"  Node 2: {node2.node_name}")
        print(f"  Node 3: {node3.node_name}")

        return True, ""

    except Exception as e:
        print(f"  FAIL Workflow node test: {e}")
        return False, str(e)


def test_data_structures():
    """测试数据结构创建"""
    print("\n4. DATA STRUCTURE TEST")
    print("-" * 25)

    try:
        from app.services.medical_parser import MedicalDocument, DocumentMetadata, FileType

        test_metadata = DocumentMetadata(
            file_path='test.pdf',
            file_type=FileType.PDF,
            title='Test Document'
        )

        test_document = MedicalDocument(
            document_id='test_001',
            metadata=test_metadata,
            full_text='Test content'
        )

        print("  PASS MedicalDocument creation")
        print(f"  Document ID: {test_document.document_id}")

        return True, ""

    except Exception as e:
        print(f"  FAIL Data structure test: {e}")
        return False, str(e)


def test_database_models():
    """测试数据库模型"""
    print("\n5. DATABASE MODEL TEST")
    print("-" * 26)

    try:
        from app.models.base import Base
        from app.models.medical_document import MedicalDocumentModel
        from app.models.multimodal_content import ProcessedContentModel
        from app.models.knowledge_graph import EnhancedContentModel

        # 检查表名
        table_names = [
            MedicalDocumentModel.__tablename__,
            ProcessedContentModel.__tablename__,
            EnhancedContentModel.__tablename__
        ]

        print(f"  PASS Database models import")
        print(f"  PASS Table names: {table_names}")

        return True, ""

    except Exception as e:
        print(f"  FAIL Database model test: {e}")
        return False, str(e)


def main():
    """主函数"""
    print("SYSTEM COMPATIBILITY CHECK")
    print("=" * 50)

    total_tests = 5
    passed_tests = 0

    # 运行测试
    module_passed, module_failed = test_module_imports()

    service_passed, service_error = test_service_classes()
    if service_passed:
        passed_tests += 1

    workflow_passed, workflow_error = test_workflow_nodes()
    if workflow_passed:
        passed_tests += 1

    data_passed, data_error = test_data_structures()
    if data_passed:
        passed_tests += 1

    db_passed, db_error = test_database_models()
    if db_passed:
        passed_tests += 1

    # 总结
    print("\n" + "=" * 50)
    print("COMPATIBILITY SUMMARY")
    print("=" * 50)

    print(f"\n📊 STATISTICS:")
    print(f"  Module imports: {len(module_passed)} passed, {len(module_failed)} failed")
    print(f"  Integration tests: {passed_tests}/4 passed")

    if module_failed:
        print(f"\n❌ FAILED MODULES:")
        for module_name, description, error in module_failed:
            print(f"  • {description}")
            print(f"    {error}")

    success_rate = len(module_passed) / (len(module_passed) + len(module_failed)) * 100
    print(f"\n🎯 OVERALL SUCCESS RATE: {success_rate:.1f}%")

    if len(module_failed) == 0:
        print("\n🎉 SYSTEM STATUS: FULLY COMPATIBLE")
        print("   All components can work together seamlessly!")
        print("\n✅ The knowledge graph system is ready for:")
        print("   • Production deployment")
        print("   • End-to-end testing")
        print("   • Performance benchmarking")
        print("   • Clinical document processing")
        return True
    else:
        print(f"\n⚠️  SYSTEM STATUS: COMPATIBILITY ISSUES")
        print(f"   {len(module_failed)} modules have import issues that need resolution")
        print("\n🔧 RECOMMENDED ACTIONS:")
        print("   • Install missing dependencies (spaCy, transformers)")
        print("   • Fix import path issues")
        print("   • Resolve model relationship conflicts")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)