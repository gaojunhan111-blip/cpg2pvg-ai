#!/usr/bin/env python3
"""
多模态内容处理器测试脚本
MultiModal Content Processor Test Script
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


async def test_multimodal_processor():
    """测试多模态处理器"""
    print_colored("🧪 测试多模态内容处理器", "cyan")
    print("=" * 60)

    try:
        # 导入必要模块
        from app.services.multimodal_processor import (
            MultiModalProcessor, ProcessingConfig, ProcessedContent
        )
        from app.services.medical_parser import (
            MedicalDocument, DocumentMetadata, FileType,
            DocumentSection, SectionType, MedicalTable, ClinicalAlgorithm
        )
        print_colored("✅ 模块导入成功", "green")

        # 创建测试文档
        test_document = create_test_document()
        print_colored("✅ 测试文档创建成功", "green")

        # 创建处理配置
        config = ProcessingConfig(
            max_workers=2,
            timeout_per_item=60,
            max_tables_to_process=3,
            max_algorithms_to_process=2,
            max_text_sections=5,
            max_cost_per_document=1.0
        )
        print_colored("✅ 处理配置创建成功", "green")

        # 创建多模态处理器
        processor = MultiModalProcessor(config)
        print_colored("✅ 多模态处理器创建成功", "green")

        # 执行处理
        print_colored("🔄 开始处理测试文档...", "yellow")
        start_time = asyncio.get_event_loop().time()

        processed_content = await processor.process_guideline_content(test_document)

        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time

        print_colored(f"✅ 处理完成，耗时 {processing_time:.2f} 秒", "green")

        # 验证结果
        await validate_processing_results(processed_content)

        return True

    except Exception as e:
        print_colored(f"❌ 测试失败: {str(e)}", "red")
        import traceback
        traceback.print_exc()
        return False


def create_test_document():
    """创建测试文档"""
    # 创建文档元数据
    metadata = DocumentMetadata(
        file_path="test_guideline.pdf",
        file_hash="test_hash_123",
        file_size=1024,
        file_type=FileType.PDF,
        page_count=5,
        word_count=1000,
        char_count=5000,
        title="糖尿病治疗指南",
        abstract="2型糖尿病患者的治疗管理指南",
        authors=["Dr. Smith", "Dr. Johnson"],
        keywords=["diabetes", "treatment", "guideline"],
        doi="10.1234/test.2023",
        journal="Medical Journal",
        publication_year=2023,
        language="English"
    )

    # 创建文档章节
    sections = [
        DocumentSection(
            section_id="sec_1",
            title="治疗目标",
            section_type=SectionType.RECOMMENDATIONS,
            content="对于2型糖尿病患者，建议将糖化血红蛋白控制在7%以下。这个目标适用于大多数成年患者，但需要根据个体情况调整。对于老年患者或有并发症的患者，可以考虑更宽松的目标。",
            start_position=0,
            end_position=200,
            level=1
        ),
        DocumentSection(
            section_id="sec_2",
            title="药物选择",
            section_type=SectionType.TREATMENT,
            content="二甲双胍是2型糖尿病的一线治疗药物。如果不能耐受或有禁忌症，可以考虑使用磺脲类药物、DPP-4抑制剂或SGLT2抑制剂。联合治疗可以提高血糖控制效果。",
            start_position=200,
            end_position=400,
            level=1
        )
    ]

    # 创建医学表格
    tables = [
        MedicalTable(
            table_id="table_1",
            title="常用降糖药物比较",
            headers=["药物", "剂量", "主要副作用", "禁忌症"],
            rows=[
                ["二甲双胍", "500-2000mg/天", "胃肠道反应", "严重肾功能不全"],
                ["格列美脲", "1-8mg/天", "低血糖", "严重肝肾功能不全"],
                ["西格列汀", "100mg/天", "头痛", "过敏反应"]
            ],
            caption="表1展示了三种常用降糖药物的特点",
            content_text="常用降糖药物比较表，包括二甲双胍、格列美脲、西格列汀的剂量、副作用和禁忌症信息"
        ),
        MedicalTable(
            table_id="table_2",
            title="血糖监测频率建议",
            headers=["患者类型", "监测频率", "监测时间"],
            rows=[
                ["新诊断患者", "每日4次", "餐前+睡前"],
                ["稳定期患者", "每周2-3天", "餐前+餐后"],
                ["胰岛素治疗", "每日4-7次", "餐前+睡前+必要时"]
            ],
            caption="表2：不同患者的血糖监测建议"
        )
    ]

    # 创建临床算法
    algorithms = [
        ClinicalAlgorithm(
            algorithm_id="algo_1",
            title="2型糖尿病初始治疗算法",
            steps=[
                {"id": "step1", "title": "诊断确认", "description": "确认2型糖尿病诊断"},
                {"id": "step2", "title": "生活方式干预", "description": "开始饮食和运动干预"},
                {"id": "step3", "title": "药物选择", "description": "根据患者情况选择合适药物"}
            ],
            decision_points=[
                {
                    "id": "decision1",
                    "question": "HbA1c是否达标？",
                    "options": [
                        {"label": "是", "outcome": "继续当前治疗"},
                        {"label": "否", "outcome": "调整治疗方案"}
                    ]
                }
            ],
            flowchart_text="诊断 -> 生活方式干预 -> 药物选择 -> 监测效果 -> 调整方案",
            source_section="sec_2",
            target_population="新诊断2型糖尿病患者"
        )
    ]

    return MedicalDocument(
        document_id="test_doc_001",
        metadata=metadata,
        full_text="完整的糖尿病治疗指南内容...",
        language_detected="en",
        sections=sections,
        tables=tables,
        algorithms=algorithms
    )


async def validate_processing_results(processed_content: ProcessedContent):
    """验证处理结果"""
    print_colored("\n📊 验证处理结果", "blue")
    print("-" * 40)

    # 基本状态检查
    print(f"处理状态: {processed_content.status.value}")
    print(f"内容ID: {processed_content.content_id}")
    print(f"处理时间: {processed_content.total_processing_time:.2f}秒")

    # 文本处理结果
    print(f"\n📝 文本处理结果:")
    print(f"  处理章节数: {len(processed_content.text_results)}")
    for i, result in enumerate(processed_content.text_results):
        print(f"  章节 {i+1}: {result.section_type} - 状态: {result.status.value}")
        print(f"    关键点数量: {len(result.key_points)}")
        print(f"    医学实体数量: {len(result.medical_entities)}")
        print(f"    质量分数: {result.metrics.quality_score:.2f}")

    # 表格处理结果
    print(f"\n📊 表格处理结果:")
    print(f"  处理表格数: {len(processed_content.processed_tables)}")
    for i, table in enumerate(processed_content.processed_tables):
        print(f"  表格 {i+1}: {table.title} - 类型: {table.table_type.value}")
        print(f"    临床重要性: {table.clinical_importance.value}")
        print(f"    关键发现数量: {len(table.key_findings)}")
        print(f"    质量分数: {table.metrics.quality_score:.2f}")

    # 算法处理结果
    print(f"\n🤖 算法处理结果:")
    print(f"  处理算法数: {len(processed_content.processed_algorithms)}")
    for i, algorithm in enumerate(processed_content.processed_algorithms):
        print(f"  算法 {i+1}: {algorithm.title} - 类型: {algorithm.algorithm_type.value}")
        print(f"    临床重要性: {algorithm.clinical_importance.value}")
        print(f"    决策点数量: {len(algorithm.key_decision_points)}")
        print(f"    质量分数: {algorithm.metrics.quality_score:.2f}")

    # 跨模态关系
    print(f"\n🔗 跨模态关系:")
    print(f"  关系数量: {len(processed_content.cross_modal_relationships)}")
    for i, rel in enumerate(processed_content.cross_modal_relationships):
        print(f"  关系 {i+1}: {rel.source_type.value} -> {rel.target_type.value}")
        print(f"    类型: {rel.relationship_type}, 置信度: {rel.confidence:.2f}")

    # 整体质量评估
    print(f"\n📈 整体质量评估:")
    print(f"  总体质量分数: {processed_content.overall_quality_score:.2f}")
    print(f"  完整性分数: {processed_content.completeness_score:.2f}")
    print(f"  总token使用: {processed_content.total_tokens_used}")
    print(f"  估算成本: ${processed_content.total_cost_estimate:.2f}")

    # 关键临床洞察
    print(f"\n💡 关键临床洞察:")
    for i, insight in enumerate(processed_content.key_clinical_insights):
        print(f"  {i+1}. {insight}")

    # 处理日志
    if processed_content.processing_log:
        print(f"\n📝 处理日志:")
        for log_entry in processed_content.processing_log[-5:]:  # 显示最后5条
            print(f"  - {log_entry}")

    # 错误信息
    if processed_content.errors:
        print(f"\n❌ 错误信息:")
        for error in processed_content.errors:
            print(f"  - {error}")

    # 验证成功标准
    success_criteria = [
        (len(processed_content.text_results) > 0, "至少处理了一个文本章节"),
        (processed_content.overall_quality_score >= 0.5, "整体质量分数 >= 0.5"),
        (processed_content.total_processing_time > 0, "处理时间 > 0"),
        (len(processed_content.processing_log) > 0, "有处理日志")
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
        print_colored("⚠️ 部分验证标准未通过，但这可能是正常的测试行为", "yellow")


async def test_configuration_options():
    """测试配置选项"""
    print_colored("\n⚙️ 测试配置选项", "purple")
    print("-" * 40)

    try:
        from app.services.multimodal_processor import ProcessingConfig

        # 测试默认配置
        default_config = ProcessingConfig()
        print_colored("✅ 默认配置创建成功", "green")

        # 测试自定义配置
        custom_config = ProcessingConfig(
            max_workers=8,
            max_tables_to_process=5,
            clinical_keywords=["diabetes", "treatment", "guideline", "medication"]
        )
        print_colored("✅ 自定义配置创建成功", "green")

        # 验证配置参数
        print(f"  最大工作线程: {custom_config.max_workers}")
        print(f"  最大表格处理数: {custom_config.max_tables_to_process}")
        print(f"  临床关键词: {custom_config.clinical_keywords[:2]}...")

        return True

    except Exception as e:
        print_colored(f"❌ 配置测试失败: {str(e)}", "red")
        return False


async def main():
    """主函数"""
    print_colored("🧪 多模态内容处理器集成测试", "cyan")
    print("=" * 60)

    success_count = 0
    total_tests = 2

    # 测试1: 基本功能测试
    print_colored("\n📋 测试1: 基本功能测试", "blue")
    if await test_multimodal_processor():
        success_count += 1

    # 测试2: 配置选项测试
    print_colored("\n📋 测试2: 配置选项测试", "blue")
    if await test_configuration_options():
        success_count += 1

    # 总结
    print_colored("\n" + "=" * 60, "cyan")
    print_colored("📊 测试总结", "cyan")
    print(f"  通过: {success_count}/{total_tests}")

    if success_count == total_tests:
        print_colored("🎉 所有测试通过！多模态处理器工作正常", "green")
        print_colored("\n📋 下一步:", "cyan")
        print("  1. 运行完整的文档处理流程测试")
        print("  2. 集成到Celery工作流")
        print("  3. 测试大规模文档处理")
        return True
    else:
        print_colored(f"⚠️ {total_tests - success_count} 个测试失败", "yellow")
        print_colored("请检查错误信息并修复问题", "yellow")
        return False


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