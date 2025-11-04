#!/usr/bin/env python3
"""
知识图谱测试脚本
Knowledge Graph Test Script
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
    print_colored("🧠 测试基于知识图谱的语义理解", "cyan")
    print("=" * 60)

    try:
        # 导入必要模块
        from app.services.knowledge_graph import (
            MedicalKnowledgeGraph, EnhancedContent, ProcessingConfig,
            MedicalEntity, EntityType, LinkedEntity, ClinicalRelationship,
            ClinicalContext, MedicalOntology
        )
        from app.services.multimodal_processor import ProcessedContent, TextProcessingResult, ProcessingStatus
        print_colored("✅ 模块导入成功", "green")

        # 创建测试的ProcessedContent
        test_processed_content = create_test_processed_content()
        print_colored("✅ 测试内容创建成功", "green")

        # 创建知识图谱配置
        config = {
            "min_entity_confidence": 0.4,
            "max_entities_per_type": 20,
            "enable_ontology_linking": True,
            "enable_relationship_inference": True,
            "enable_context_building": True
        }
        print_colored("✅ 知识图谱配置创建成功", "green")

        # 创建知识图谱处理器
        kg = MedicalKnowledgeGraph(config)
        print_colored("✅ 知识图谱处理器创建成功", "green")

        # 验证本体加载
        if kg.ontology and kg.ontology.total_concepts > 0:
            print_colored(f"✅ 本体加载成功: {kg.ontology.total_concepts}个概念", "green")
        else:
            print_colored("⚠️ 本体加载可能失败", "yellow")

        # 执行语义理解增强
        print_colored("🔄 开始语义理解增强测试...", "yellow")
        start_time = asyncio.get_event_loop().time()

        enhanced_content = await kg.enhance_semantic_understanding(test_processed_content)

        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time

        print_colored(f"✅ 语义理解增强完成，耗时 {processing_time:.2f} 秒", "green")

        # 验证结果
        await validate_knowledge_graph_results(enhanced_content)

        return True

    except Exception as e:
        print_colored(f"❌ 测试失败: {str(e)}", "red")
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
    from app.services.multimodal_processor import ProcessedContent

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
    print_colored("\n📊 验证知识图谱结果", "blue")
    print("-" * 40)

    # 基本信息
    print(f"内容ID: {enhanced_content.content_id}")
    print(f"处理时间: {enhanced_content.processing_time:.2f}秒")
    print(f"总体质量: {enhanced_content.overall_quality:.2f}")

    # 实体分析
    print(f"\n🏷️ 医学实体分析:")
    print(f"  提取实体数: {len(enhanced_content.entities)}")
    print(f"  链接实体数: {len([e for e in enhanced_content.entities if e.link_confidence > 0])}")
    print(f"  实体类型分布: {enhanced_content.entity_counts}")

    # 实体质量检查
    high_confidence_entities = [e for e in enhanced_content.entities if e.link_confidence > 0.8]
    print(f"  高置信度实体: {len(high_confidence_entities)}")

    # 显示前几个实体详情
    if enhanced_content.entities:
        print(f"\n  前5个实体详情:")
        for i, linked_entity in enumerate(enhanced_content.entities[:5]):
            entity = linked_entity.entity
            print(f"    {i+1}. {entity.text} ({entity.entity_type.value})")
            print(f"       置信度: {entity.extraction_confidence:.2f}")
            print(f"       链接置信度: {linked_entity.link_confidence:.2f}")
            if linked_entity.best_match:
                print(f"       本体匹配: {linked_entity.best_match.get('preferred_name', 'N/A')}")

    # 关系分析
    print(f"\n🔗 临床关系分析:")
    print(f"  关系数: {len(enhanced_content.relationships)}")
    print(f"  关系类型分布: {enhanced_content.relationship_counts}")

    # 显示前几个关系
    if enhanced_content.relationships:
        print(f"\n  前5个关系:")
        for i, rel in enumerate(enhanced_content.relationships[:5]):
            print(f"    {i+1}. {rel.source_entity.entity.text} --{rel.relationship_type.value}--> {rel.target_entity.entity.text}")
            print(f"       置信度: {rel.confidence.value}")
            print(f"       强度: {rel.strength:.2f}")

    # 临床上下文分析
    if enhanced_content.clinical_context:
        context = enhanced_content.clinical_context
        print(f"\n🏥 临床上下文分析:")
        print(f"  上下文已构建: 是")
        if context.primary_condition:
            print(f"  主要疾病: {context.primary_condition.entity.text}")
        print(f"  风险因素数: {len(context.risk_factors)}")
        print(f"  推荐数: {len(context.recommendations)}")
        print(f"  安全警报数: {len(context.warnings)}")
        print(f"  完整性分数: {context.completeness_score:.2f}")
        print(f"  置信度分数: {context.confidence_score:.2f}")
    else:
        print(f"\n🏥 临床上下文分析:")
        print(f"  上下文已构建: 否")

    # 质量指标
    print(f"\n📈 质量指标:")
    print(f"  提取质量: {enhanced_content.extraction_quality:.2f}")
    print(f"  链接质量: {enhanced_content.linking_quality:.2f}")
    print(f"  推理质量: {enhanced_content.inference_quality:.2f}")

    # 增强功能
    print(f"\n🚀 增强功能:")
    print(f"  语义摘要: {'✓' if enhanced_content.semantic_summary else '✗'}")
    print(f"  关键洞察: {len(enhanced_content.key_insights)}")
    print(f"  临床推荐: {len(enhanced_content.clinical_recommendations)}")
    print(f"  安全警报: {len(enhanced_content.safety_alerts)}")

    # 显示关键内容
    if enhanced_content.semantic_summary:
        print(f"\n📝 语义摘要:")
        print(f"  {enhanced_content.semantic_summary}")

    if enhanced_content.key_insights:
        print(f"\n💡 关键洞察:")
        for i, insight in enumerate(enhanced_content.key_insights):
            print(f"  {i+1}. {insight}")

    if enhanced_content.clinical_recommendations:
        print(f"\n💊 临床推荐:")
        for i, rec in enumerate(enhanced_content.clinical_recommendations):
            print(f"  {i+1}. {rec}")

    if enhanced_content.safety_alerts:
        print(f"\n⚠️ 安全警报:")
        for i, alert in enumerate(enhanced_content.safety_alerts):
            print(f"  {i+1}. {alert}")

    # 验证成功标准
    success_criteria = [
        len(enhanced_content.entities) > 0,
        len(enhanced_content.entities) == len(enhanced_content.entity_counts),
        enhanced_content.overall_quality > 0.5,
        enhanced_content.processing_time > 0
    ]

    print(f"\n✅ 验证标准检查:")
    passed = 0
    total = len(success_criteria)

    for criterion, description in success_criteria:
        status = "PASS" if criterion else "FAIL"
        color = "green" if criterion else "red"
        print_colored(f"  [{status}] {description}", color)
        if criterion:
            passed += 1

    print(f"\n📊 总体验证结果: {passed}/{total} 通过")

    if passed == total:
        print_colored("🎉 所有验证标准都通过！", "green")
    else:
        print_colored(f"⚠️ {total - passed} 项验证标准未通过", "yellow")


async def test_ontology_components():
    """测试本体组件"""
    print_colored("\n🧪 测试本体组件", "purple")
    print("-" * 40)

    try:
        from app.services.knowledge_graph import MedicalKnowledgeGraph, MedicalOntology, OntologySource

        # 创建知识图谱实例
        kg = MedicalKnowledgeGraph()
        print_colored("✅ 知识图谱实例创建成功", "green")

        # 验证本体
        if kg.ontology:
            print_colored(f"✅ 本体加载成功: {kg.ontology.name}", "green")
            print_colored(f"   概念数量: {kg.ontology.total_concepts}", "green")
            print_colored(f"   关系数量: {kg.ontology.total_relationships}", "green")
            print_colored(f"   本体来源: {kg.ontology.source.value}", "green")

            # 验证概念查找
            test_concepts = ["diabetes", "metformin", "hypertension"]
            for concept in test_concepts:
                concept_id = kg.ontology.find_concept(concept)
                if concept_id:
                    concept_data = kg.ontology.get_concept_data(concept_id)
                    print_colored(f"   ✅ 找到概念 '{concept}': {concept_data.get('preferred_name', 'N/A')}", "green")
                else:
                    print_colored(f"   ⚠️ 未找到概念: {concept}", "yellow")

        return True

    except Exception as e:
        print_colored(f"❌ 本体组件测试失败: {str(e)}", "red")
        return False


async def test_entity_extraction():
    """测试实体提取"""
    print_colored("\n🔍 测试实体提取", "purple")
    print("-" * 40)

    try:
        from app.services.knowledge_graph import MedicalKnowledgeGraph, MedicalEntity, EntityType

        # 创建知识图谱实例
        kg = MedicalKnowledgeGraph()
        print_colored("✅ 知识图谱实例创建成功", "green")

        # 测试规则提取
        test_text = "Patient with Type 2 Diabetes mellitus treated with metformin and insulin."
        print(f"测试文本: {test_text}")

        # 模拟内容段
        content_segments = [(test_text, "test_segment", "test")]

        # 提取实体
        rule_entities = await kg._extract_entities_with_rules(content_segments)
        print_colored(f"  规则提取: {len(rule_entities)} 个实体")

        # 模型提取
        model_entities = await kg._extract_entities_with_model(content_segments)
        print_colored(f"  模型提取: {len(model_entities)} 个实体")

        # 融合实体
        merged_entities = kg._merge_entities(rule_entities, model_entities)
        print_colored(f"  融合后: {len(merged_entities)} 个实体")

        # 显示提取的实体
        if merged_entities:
            print_colored("  提取的实体:")
            for entity in merged_entities:
                print(f"    - {entity.text} ({entity.entity_type.value}) - 置信度: {entity.extraction_confidence:.2f}")

        return len(merged_entities) > 0

    except Exception as e:
        print_colored(f"❌ 实体提取测试失败: {str(e)}", "red")
        return False


async def test_ontology_linking():
    """测试本体链接"""
    print_colored("\n🔗 测试本体链接", "purple")
    print("-" - 40)

    try:
        from app.services.knowledge_graph import MedicalKnowledgeGraph, MedicalEntity, EntityType

        # 创建知识图谱实例
        kg = MedicalKnowledgeGraph()
        print_colored("✅ 知识图谱实例创建成功", "green")

        # 创建测试实体
        test_entities = [
            MedicalEntity(
                text="Type 2 Diabetes",
                entity_type=EntityType.DISEASE,
                extraction_confidence=0.8
            ),
            MedicalEntity(
                text="Metformin",
                entity_type=EntityType.MEDICATION,
                extraction_confidence=0.9
            ),
            MedicalEntity(
                text="Hypertension",
                entity_type=EntityType.DISEASE,
                extraction_confidence=0.7
            )
        ]
        print_colored(f"  创建测试实体: {len(test_entities)} 个", "green")

        # 链接到本体
        linked_entities = await kg._link_to_ontology(test_entities)
        print_colored(f"  本体链接完成: {len(linked_entities)} 个实体")

        # 分析链接结果
        linked_count = 0
        high_confidence_count = 0

        for linked_entity in linked_entities:
            if linked_entity.best_match:
                linked_count += 1
                if linked_entity.link_confidence > 0.7:
                    high_confidence_count += 1

                entity = linked_entity.entity
                match = linked_entity.best_match
                print(f"    - {entity.text} -> {match.get('preferred_name', 'N/A')} (置信度: {linked_entity.link_confidence:.2f})")

        print_colored(f"  成功链接: {linked_count}/{len(test_entities)}")
        print_colored(f"  高置信度链接: {high_confidence_count}/{len(test_entities)}")

        return linked_count > 0

    except Exception as e:
        print_colored(f"❌ 本体链接测试失败: {str(e)}", "red")
        return False


async def main():
    """主函数"""
    print_colored("🧠 知识图谱集成测试", "cyan")
    print("=" * 60)

    success_count = 0
    total_tests = 4

    # 测试1: 基本功能测试
    print_colored("\n📋 测试1: 基本功能测试", "blue")
    if await test_knowledge_graph():
        success_count += 1

    # 测试2: 本体组件测试
    print_colored("\n📋 测试2: 本体组件测试", "blue")
    if await test_ontology_components():
        success_count += 1

    # 测试3: 实体提取测试
    print_colored("\n📋 测试3: 实体提取测试", "blue")
    if await test_entity_extraction():
        success_count += 1

    # 测试4: 本体链接测试
    print_colored("\n📋 测试4: 本体链接测试", "blue")
    if await test_ontology_linking():
        success_count += 1

    # 总结
    print_colored("\n" + "=" * 60, "cyan")
    print_colored("📊 测试总结", "cyan")
    print(f"  通过: {success_count}/{total_tests}")

    if success_count == total_tests:
        print_colored("🎉 所有测试通过！知识图谱系统工作正常", "green")
        print_colored("\n📋 下一步:", "cyan")
        print("  1. 运行完整的端到端测试")
        print("  2. 集成到工作流系统")
        print("  3. 开始临床文档语义理解")
    else:
        print_colored(f"⚠️ {total_tests - success_count} 个测试失败", "yellow")
        print_colored("请检查错误信息并修复问题", "yellow")

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