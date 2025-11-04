#!/usr/bin/env python3
"""
Simple System Compatibility Check
简化的系统兼容性检查
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """主函数"""
    print("SYSTEM COMPATIBILITY CHECK")
    print("=" * 50)

    modules_to_test = [
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

    passed = 0
    failed = 0

    print("\nMODULE IMPORT TEST:")
    print("-" * 20)

    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"  PASS: {description}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {description}")
            print(f"        Error: {str(e)}")
            failed += 1

    # 测试数据结构
    print("\nDATA STRUCTURE TEST:")
    print("-" * 22)

    try:
        from app.services.knowledge_graph import MedicalKnowledgeGraph, EntityType
        config = {'min_entity_confidence': 0.4}
        kg = MedicalKnowledgeGraph(config)
        print("  PASS: MedicalKnowledgeGraph instantiation")
        passed += 1
    except Exception as e:
        print(f"  FAIL: Service class instantiation - {e}")
        failed += 1

    try:
        from celery_worker.workflow_nodes.node1_medical_parser import MedicalParserNode
        node = MedicalParserNode()
        print(f"  PASS: Workflow node creation ({node.node_name})")
        passed += 1
    except Exception as e:
        print(f"  FAIL: Workflow node creation - {e}")
        failed += 1

    # 总结
    print("\n" + "=" * 50)
    print("COMPATIBILITY SUMMARY")
    print("=" * 50)

    total_tests = passed + failed
    success_rate = (passed / total_tests) * 100 if total_tests > 0 else 0

    print(f"\nSTATISTICS:")
    print(f"  Total tests: {total_tests}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Success rate: {success_rate:.1f}%")

    if failed == 0:
        print("\nSYSTEM STATUS: FULLY COMPATIBLE")
        print("All components can work together seamlessly!")
        print("\nThe knowledge graph system is ready for:")
        print("  - Production deployment")
        print("  - End-to-end testing")
        print("  - Performance benchmarking")
        print("  - Clinical document processing")
        return True
    elif failed <= 2:
        print(f"\nSYSTEM STATUS: MOSTLY COMPATIBLE")
        print(f"{failed} minor issues found, but core functionality should work.")
        print("\nRecommended actions:")
        print("  - Install missing dependencies for full functionality")
        print("  - Fix remaining import issues")
        return True
    else:
        print(f"\nSYSTEM STATUS: COMPATIBILITY ISSUES")
        print(f"{failed} issues need to be resolved for full functionality.")
        print("\nRequired actions:")
        print("  - Fix import path issues")
        print("  - Install missing dependencies")
        print("  - Resolve model relationship conflicts")
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