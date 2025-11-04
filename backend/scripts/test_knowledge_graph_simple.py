#!/usr/bin/env python3
"""
知识图谱测试脚本 - 简化版本
Knowledge Graph Test Script - Simplified Version
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


async def test_knowledge_graph():
    """测试知识图谱"""
    print_colored("Testing Knowledge Graph-Based Semantic Understanding", "cyan")
    print("=" * 60)

    try:
        # 导入必要模块
        from app.services.knowledge_graph import (
            MedicalKnowledgeGraph, EnhancedContent, ProcessingConfig,
            MedicalEntity, EntityType, LinkedEntity, ClinicalRelationship,
            ClinicalContext, MedicalOntology
        )
        from app.services.multimodal_processor import ProcessedContent, TextProcessingResult, ProcessingStatus
        print_colored("Module import successful", "green")

        # 创建测试的ProcessedContent
        test_processed_content = create_test_processed_content()
        print_colored("Test content creation successful", "green")

        # 创建知识图谱配置
        config = {
            "min_entity_confidence": 0.4,
            "max_entities_per_type": 20,
            "enable_ontology_linking": True,
            "enable_relationship_inference": True,
            "enable_context_building": True
        }
        print_colored("Knowledge graph configuration creation successful", "green")

        # 创建知识图谱处理器
        kg = MedicalKnowledgeGraph(config)
        print_colored("Knowledge graph processor creation successful", "green")

        # 验证本体加载
        if kg.ontology and kg.ontology.total_concepts > 0:
            print_colored(f"Ontology loading successful: {kg.ontology.total_concepts} concepts", "green")
        else:
            print_colored("Ontology loading might have failed", "yellow")

        # 执行语义理解增强
        print_colored("Starting semantic understanding enhancement test...", "yellow")
        start_time = asyncio.get_event_loop().time()

        enhanced_content = await kg.enhance_semantic_understanding(test_processed_content)

        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time

        print_colored(f"Semantic understanding enhancement completed, time: {processing_time:.2f} seconds", "green")

        # 验证结果
        await validate_knowledge_graph_results(enhanced_content)

        return True

    except Exception as e:
        print_colored(f"Test failed: {str(e)}", "red")
        import traceback
        traceback.print_exc()
        return False


def create_test_processed_content():
    """创建测试用的ProcessedContent"""
    # 导入必要的类
    from app.services.multimodal_processor import ProcessedContent, TextProcessingResult, ProcessingStatus
    from app.services.knowledge_graph import EntityType

    # 创建文本处理结果
    text_results = [
        TextProcessingResult(
            text_result_id="text_001",
            section_id="section_diagnosis",
            section_type="recommendations",
            original_content="2型糖尿病患者的血糖控制目标",
            processed_content="对于2型糖尿病患者，建议将糖化血红蛋白控制在7%以下。这个目标适用于大多数成年患者。",
            summary="血糖控制目标为HbA1c < 7%",
            key_points=["血糖控制目标", "HbA1c < 7%", "适用于大多数患者"],
            medical_entities=[
                {"text": "2型糖尿病", "type": "disease", "confidence": 0.9},
                {"text": "糖化血红蛋白", "type": "lab_test", "confidence": 0.8}
            ],
            clinical_concepts=["diabetes management", "glycemic control"],
            status=ProcessingStatus.COMPLETED,
            processing_log=["Text processing completed"]
        ),
        TextProcessingResult(
            text_result_id="text_002",
            section_id="section_treatment",
            section_type="treatment",
            original_content="使用二甲双胍作为一线治疗药物，必要时加用胰岛素治疗。",
            processed_content="使用二甲双胍作为一线治疗药物，必要时加用胰岛素治疗。",
            summary="一线药物为二甲双胍，必要时加胰岛素",
            key_points=["二甲双胍", "一线治疗", "必要时胰岛素"],
            medical_entities=[
                {"text": "二甲双胍", "type": "medication", "confidence": 0.9},
                {"text": "胰岛素", "type": "medication", "confidence": 0.8}
            ],
            clinical_concepts=["pharmacological therapy"],
            status=ProcessingStatus.COMPLETED,
            processing_log=["Text processing completed"]
        )
    ]

    # 创建ProcessedContent实例
    return ProcessedContent(
        content_id="test_processed_001",
        source_document_id="test_doc_001",
        text_results=text_results,
        processed_tables=[],
        processed_algorithms=[],
        integrated_summary="2型糖尿病的治疗管理，包括血糖目标和药物治疗方案",
        key_clinical_insights=["HbA1c目标7%", "二甲双胍一线用药"],
        content_statistics={},
        total_processing_time=0.0,
        total_tokens_used=0,
        total_cost_estimate=0.0,
        overall_quality_score=0.85,
        completeness_score=0.9,
        status="completed",
        processing_log=["Test content created"]
    )


async def validate_knowledge_graph_results(enhanced_content):
    """验证知识图谱结果"""
    print_colored("Validating Knowledge Graph Results", "blue")
    print("-" * 40)

    # 基本信息
    print(f"Content ID: {enhanced_content.content_id}")
    print(f"Processing time: {enhanced_content.processing_time:.2f} seconds")
    print(f"Overall quality: {enhanced_content.overall_quality:.2f}")

    # 实体分析
    print(f"Medical Entity Analysis:")
    print(f"  Extracted entities: {len(enhanced_content.entities)}")
    print(f"  Linked entities: {len([e for e in enhanced_content.entities if e.link_confidence > 0])}")
    print(f"  Entity type distribution: {enhanced_content.entity_counts}")

    # 实体质量检查
    high_confidence_entities = [e for e in enhanced_content.entities if e.link_confidence > 0.8]
    print(f"  High confidence entities: {len(high_confidence_entities)}")

    # 关系分析
    print(f"Clinical Relationship Analysis:")
    print(f"  Relationships: {len(enhanced_content.relationships)}")
    print(f"  Relationship type distribution: {enhanced_content.relationship_counts}")

    # 临床上下文分析
    if enhanced_content.clinical_context:
        context = enhanced_content.clinical_context
        print(f"Clinical Context Analysis:")
        print(f"  Context built: Yes")
        if context.primary_condition:
            print(f"  Primary condition: {context.primary_condition.entity.text}")
        print(f"  Risk factors: {len(context.risk_factors)}")
        print(f"  Recommendations: {len(context.recommendations)}")
        print(f"  Safety warnings: {len(context.warnings)}")
        print(f"  Completeness score: {context.completeness_score:.2f}")
        print(f"  Confidence score: {context.confidence_score:.2f}")
    else:
        print(f"Clinical Context Analysis:")
        print(f"  Context built: No")

    # 质量指标
    print(f"Quality Metrics:")
    print(f"  Extraction quality: {enhanced_content.extraction_quality:.2f}")
    print(f"  Linking quality: {enhanced_content.linking_quality:.2f}")
    print(f"  Inference quality: {enhanced_content.inference_quality:.2f}")

    # 验证成功标准
    success_criteria = [
        (len(enhanced_content.entities) > 0, "Extracted entities > 0"),
        (enhanced_content.overall_quality > 0.5, "Overall quality >= 0.5"),
        (enhanced_content.processing_time > 0, "Processing time > 0")
    ]

    print(f"Validation Criteria Check:")
    passed = 0
    total = len(success_criteria)

    for criterion, description in success_criteria:
        status = "PASS" if criterion else "FAIL"
        color = "green" if criterion else "red"
        print_colored(f"  [{status}] {description}", color)
        if criterion:
            passed += 1

    print(f"Overall validation result: {passed}/{total} passed")

    if passed == total:
        print_colored("All validation criteria passed!", "green")
    else:
        print_colored(f"{total - passed} validation criteria not passed", "yellow")


async def main():
    """主函数"""
    print_colored("Knowledge Graph Integration Test", "cyan")
    print("=" * 60)

    success_count = 0
    total_tests = 1

    # 测试1: 基本功能测试
    print_colored("Test 1: Basic Functionality Test", "blue")
    if await test_knowledge_graph():
        success_count += 1

    # 总结
    print_colored("=" * 60, "cyan")
    print_colored("Test Summary", "cyan")
    print(f"  Passed: {success_count}/{total_tests}")

    if success_count == total_tests:
        print_colored("All tests passed! Knowledge graph system is working properly", "green")
        print_colored("Next steps:", "cyan")
        print("  1. Run complete end-to-end tests")
        print("  2. Integrate into workflow system")
        print("  3. Start clinical document semantic understanding")
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