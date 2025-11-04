"""
医学文档解析器使用示例
Medical Parser Usage Examples
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.medical_parser import (
    parse_medical_document,
    create_document_chunks,
    HierarchicalMedicalParser
)
from app.core.logger import get_logger

logger = get_logger(__name__)


async def basic_usage_example():
    """基础使用示例"""
    print("=" * 60)
    print("基础使用示例")
    print("=" * 60)

    # 假设有一个医学文档文件
    file_path = "examples/hypertension_guideline.pdf"

    # 1. 解析医学文档
    try:
        print(f"正在解析文档: {file_path}")
        document = await parse_medical_document(file_path)

        print(f"✅ 解析成功!")
        print(f"文档ID: {document.document_id}")
        print(f"文档类型: {document.metadata.file_type}")
        print(f"字符数: {document.metadata.char_count:,}")
        print(f"章节数: {len(document.sections)}")
        print(f"表格数: {len(document.tables)}")
        print(f"算法数: {len(document.algorithms)}")

    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return

    # 2. 查看文档章节
    print("\n📚 文档章节:")
    for i, section in enumerate(document.sections[:5]):  # 只显示前5个
        print(f"  {i+1}. {section.title} ({section.section_type.value})")
        print(f"     长度: {len(section.content)} 字符")
        print(f"     实体数: {len(section.entities)}")

    # 3. 查看表格信息
    if document.tables:
        print("\n📊 表格信息:")
        for i, table in enumerate(document.tables[:3]):  # 只显示前3个
            print(f"  表格 {i+1}:")
            print(f"    列数: {len(table.headers)}")
            print(f"    行数: {len(table.rows)}")
            if table.interpretation:
                print(f"    AI解读: {table.interpretation[:100]}...")

    # 4. 查看算法信息
    if document.algorithms:
        print("\n🔄 临床算法:")
        for i, algorithm in enumerate(document.algorithms):
            print(f"  算法 {i+1}: {algorithm.title}")
            print(f"    步骤数: {len(algorithm.steps)}")
            print(f"    证据等级: {algorithm.evidence_level}")


async def advanced_usage_example():
    """高级使用示例"""
    print("\n" + "=" * 60)
    print("高级使用示例")
    print("=" * 60)

    # 获取解析器实例
    parser = HierarchicalMedicalParser()

    # 自定义解析配置
    max_chunk_size = 600  # 自定义分块大小

    file_path = "examples/diabetes_guideline.docx"

    try:
        # 1. 解析文档
        document = await parse_medical_document(file_path)

        # 2. 自适应分块
        print("🔧 创建自适应分块...")
        chunks = await create_document_chunks(document, max_chunk_size)

        print(f"✅ 分块创建成功: {len(chunks)} 个块")
        print(f"平均块大小: {sum(chunk.word_count for chunk in chunks) / len(chunks):.1f} 词")

        # 3. 分析分块质量
        semantic_blocks = sum(1 for chunk in chunks if chunk.semantic_boundary)
        print(f"语义边界块: {semantic_blocks}/{len(chunks)} ({semantic_blocks/len(chunks)*100:.1f}%)")

        # 4. 查看不同类型的分块
        chunk_types = {}
        for chunk in chunks:
            chunk_type = chunk.chunk_type.value
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1

        print("\n📋 分块类型分布:")
        for chunk_type, count in chunk_types.items():
            print(f"  {chunk_type}: {count} 个块")

        # 5. 查看实体提取结果
        all_entities = []
        for section in document.sections:
            all_entities.extend(section.entities)

        if all_entities:
            print(f"\n🏥 医学实体 (共 {len(all_entities)} 个):")

            # 按类型统计
            entity_types = {}
            for entity in all_entities:
                entity_type = entity.label
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

            for entity_type, count in entity_types.items():
                print(f"  {entity_type}: {count} 个")

            # 显示一些示例实体
            print("\n实体示例:")
            for entity in all_entities[:5]:
                print(f"  - {entity.text} ({entity.label}, 置信度: {entity.confidence:.2f})")

    except Exception as e:
        print(f"❌ 高级解析失败: {e}")


async def evidence_analysis_example():
    """证据分析示例"""
    print("\n" + "=" * 60)
    print("证据分析示例")
    print("=" * 60)

    file_path = "examples/evidence_based_medicine.pdf"

    try:
        document = await parse_medical_document(file_path)

        # 1. 证据等级体系分析
        hierarchy = document.evidence_hierarchy
        print(f"📚 证据分级系统: {hierarchy.grading_system}")
        print(f"制定依据: {hierarchy.guideline_basis}")

        print(f"\n📊 证据分布:")
        print(f"  高质量证据 (A级): {len(hierarchy.primary_evidence)} 项")
        print(f"  中等质量证据 (B级): {len(hierarchy.secondary_evidence)} 项")
        print(f"  专家意见 (D级): {len(hierarchy.expert_opinion)} 项")

        # 2. 查看具体证据引用
        if hierarchy.primary_evidence:
            print(f"\n🔍 高质量证据示例:")
            for i, ref in enumerate(hierarchy.primary_evidence[:3]):
                print(f"  {i+1}. {ref.citation_text}")
                print(f"     研究类型: {ref.study_type}")
                print(f"     证据等级: {ref.evidence_level.value}")

        # 3. 章节证据等级分析
        print(f"\n📖 章节证据等级:")
        evidence_sections = [
            section for section in document.sections
            if section.evidence_level
        ]

        for section in evidence_sections:
            print(f"  {section.title}: {section.evidence_level.value}")

    except Exception as e:
        print(f"❌ 证据分析失败: {e}")


async def performance_analysis_example():
    """性能分析示例"""
    print("\n" + "=" * 60)
    print("性能分析示例")
    print("=" * 60)

    import time

    test_sizes = [1000, 5000, 10000, 50000]  # 字符数

    for size in test_sizes:
        # 生成测试内容
        test_content = f"""
# 高血压临床指南测试文档 ({size} 字符)

## 摘要
本指南为成人高血压的诊断和管理提供循证医学推荐。
{'测试医学文档内容。' * (size // 20)}

## 推荐意见

### 1. 诊断标准
- 诊室血压 ≥ 140/90 mmHg
- 家庭血压 ≥ 135/85 mmHg
- 24小时动态血压 ≥ 130/80 mmHg

### 2. 治疗目标
- 一般患者: < 140/90 mmHg
- 高危患者: < 130/80 mmHg

### 3. 药物治疗
一线药物: ACEI、ARB、CCB、利尿剂
联合用药: 两种或以上不同机制的药物
"""

        print(f"🚀 测试文档大小: {size:,} 字符")

        start_time = time.time()

        # 模拟解析过程
        document = await parse_medical_document_string(test_content)

        end_time = time.time()
        duration = end_time - start_time

        print(f"  ⏱️  解析时间: {duration:.3f} 秒")
        print(f"  📄 章节数: {len(document.sections)}")
        print(f"  🔤 分块数: {len(await create_document_chunks(document))}")
        print(f"  🏥 实体数: {sum(len(section.entities) for section in document.sections)}")

        # 计算处理速度
        chars_per_second = size / duration
        print(f"  ⚡ 处理速度: {chars_per_second:,.0f} 字符/秒")

        print()


async def parse_medical_document_string(content: str) -> 'MedicalDocument':
    """从字符串解析医学文档（辅助函数）"""
    from app.services.medical_parser import MedicalDocument, DocumentMetadata, DocumentType, SectionType
    from dataclasses import field

    # 创建临时文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name

    try:
        # 解析文档
        document = await parse_medical_document(temp_path)
        return document
    finally:
        # 清理临时文件
        import os
        os.unlink(temp_path)


async def integration_example():
    """集成使用示例"""
    print("\n" + "=" * 60)
    print("工作流集成示例")
    print("=" * 60)

    from celery_worker.workflow_nodes.node1_medical_parser import parse_medical_guideline

    # 模拟工作流上下文
    workflow_context = {
        "file_path": "examples/comprehensive_medical_guideline.pdf",
        "guideline_id": "guideline_001",
        "max_chunk_size": 800,
        "workflow_id": "workflow_001",
        "user_id": "user_001"
    }

    try:
        print("🔄 执行工作流节点...")
        result = await parse_medical_guideline(
            file_path=workflow_context["file_path"],
            guideline_id=workflow_context["guideline_id"],
            max_chunk_size=workflow_context["max_chunk_size"]
        )

        if result["success"]:
            print("✅ 节点执行成功!")
            print(f"文档ID: {result['document_id']}")
            print(f"总词数: {result['total_words']:,}")
            print(f"章节数: {result['sections_count']}")
            print(f"表格数: {result['tables_count']}")
            print(f"算法数: {result['algorithms_count']}")
            print(f"分块数: {result['chunks_count']}")

            # 显示处理摘要
            summary = result.get("summary", {})
            if summary and "quality_metrics" in summary:
                metrics = summary["quality_metrics"]
                print(f"\n📊 质量指标:")
                print(f"  语义边界比例: {metrics['semantic_boundary_ratio']:.2f}")
                print(f"  平均块大小: {metrics['avg_chunk_size']:.1f} 词")
                print(f"  有证据分级: {metrics['has_evidence_grading']}")
                print(f"  包含表格: {metrics['has_tables']}")
                print(f"  包含算法: {metrics['has_algorithms']}")
        else:
            print(f"❌ 节点执行失败: {result.get('error', '未知错误')}")

    except Exception as e:
        print(f"❌ 集成测试失败: {e}")


async def main():
    """主函数"""
    print("🏥 医学文档解析器使用示例")
    print("=" * 60)

    try:
        # 基础使用示例
        await basic_usage_example()

        # 高级使用示例
        await advanced_usage_example()

        # 证据分析示例
        await evidence_analysis_example()

        # 性能分析示例
        await performance_analysis_example()

        # 集成使用示例
        await integration_example()

        print("\n🎉 所有示例执行完成!")

    except Exception as e:
        print(f"❌ 示例执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())