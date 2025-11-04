#!/usr/bin/env python3
"""
Core Services Test Script
核心服务测试脚本
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.logger import get_logger

logger = get_logger(__name__)


class CoreServicesTestSuite:
    """核心服务测试套件"""

    def __init__(self):
        self.test_results = {}
        self.test_document_path = None

    def setup_test_document(self):
        """设置测试文档"""
        print("\n" + "="*60)
        print("SETTING UP TEST DOCUMENT")
        print("="*60)

        # 创建测试文档目录
        test_docs_dir = project_root / "test_documents"
        test_docs_dir.mkdir(exist_ok=True)

        # 创建测试医学文档
        test_content = """# 糖尿病临床诊疗指南

## 概述
糖尿病是一种常见的代谢性疾病，以血糖水平升高为特征。根据世界卫生组织统计，全球约有4.22亿成年人患有糖尿病。

## 病理生理学
糖尿病主要分为1型和2型两种类型：
1. 1型糖尿病：自身免疫破坏胰岛β细胞，导致胰岛素绝对缺乏
2. 2型糖尿病：胰岛素抵抗和胰岛素分泌不足

## 临床表现
### 常见症状
- 多饮、多尿、多食（三多症状）
- 体重减轻
- 视力模糊
- 疲劳乏力

### 并发症
- 微血管并发症：视网膜病变、肾病、神经病变
- 大血管并发症：冠心病、脑卒中、外周血管疾病

## 诊断标准
根据美国糖尿病协会标准，满足以下任一条件即可诊断：
1. 空腹血糖≥7.0 mmol/L
2. 餐后2小时血糖≥11.1 mmol/L
3. 糖化血红蛋白≥6.5%
4. 典型症状+随机血糖≥11.1 mmol/L

## 治疗方案

### 1型糖尿病治疗
- 胰岛素替代治疗
- 血糖监测
- 饮食管理

### 2型糖尿病治疗
#### 生活方式干预
- 控制饮食
- 规律运动
- 减轻体重

#### 药物治疗
一线用药：二甲双胍
二线用药：磺脲类、DPP-4抑制剂、SGLT2抑制剂

## 预防措施
### 一级预防
- 健康饮食
- 规律运动
- 控制体重
- 戒烟限酒

### 筛查建议
- 年龄≥45岁的人群应定期筛查
- 肥胖、高血压、高血脂等高危人群应更早开始筛查

## 监测随访

### 自我监测
- 血糖监测频率根据治疗方案调整
- 记录血糖值和相关因素

### 定期随访
- 每3-6个月随访一次
- 检查糖化血红蛋白
- 评估并发症
"""

        self.test_document_path = test_docs_dir / "diabetes_guideline.txt"
        with open(self.test_document_path, 'w', encoding='utf-8') as f:
            f.write(test_content)

        print(f"Created test document: {self.test_document_path}")
        return str(self.test_document_path)

    async def test_medical_parser_service(self):
        """测试医学解析服务"""
        print("\n" + "="*60)
        print("TESTING MEDICAL PARSER SERVICE")
        print("="*60)

        try:
            from app.services.medical_parser import parse_medical_document

            result = await parse_medical_document(
                document_path=str(self.test_document_path),
                document_type="clinical_guideline"
            )

            print(f"SUCCESS: Medical parsing completed")
            print(f"   Document ID: {result.document_id}")
            print(f"   Sections: {len(result.structured_sections)}")
            print(f"   Tables: {len(result.extracted_tables)}")
            print(f"   Processing time: {result.processing_time:.2f}s")

            self.test_results['medical_parser'] = {
                'success': True,
                'document_id': result.document_id,
                'sections_count': len(result.structured_sections),
                'tables_count': len(result.extracted_tables),
                'processing_time': result.processing_time
            }

            return result

        except Exception as e:
            print(f"FAILED: Medical parsing failed - {e}")
            self.test_results['medical_parser'] = {
                'success': False,
                'error': str(e)
            }
            return None

    async def test_knowledge_graph_service(self):
        """测试知识图谱服务"""
        print("\n" + "="*60)
        print("TESTING KNOWLEDGE GRAPH SERVICE")
        print("="*60)

        try:
            from app.services.knowledge_graph import MedicalKnowledgeGraph

            # 创建知识图谱实例
            kg_service = MedicalKnowledgeGraph()

            # 模拟增强内容数据
            enhanced_content = {
                "content_id": "test_content_001",
                "original_content_id": "test_doc_001",
                "processed_text": """
                患者诊断为2型糖尿病，空腹血糖8.5mmol/L，餐后2小时血糖14.2mmol/L。
                建议使用二甲双胍治疗，起始剂量500mg每日两次。
                需要定期监测血糖和糖化血红蛋白。
                """,
                "entities": {
                    "diseases": ["2型糖尿病"],
                    "symptoms": ["血糖升高"],
                    "treatments": ["二甲双胍"],
                    "medications": ["二甲双胍"]
                },
                "relationships": {
                    "treatment_relationships": [
                        {
                            "source": "二甲双胍",
                            "target": "2型糖尿病",
                            "relationship_type": "treats",
                            "confidence": 0.9
                        }
                    ]
                }
            }

            # 执行语义理解
            result = await kg_service.process_semantic_understanding(
                enhanced_content=enhanced_content,
                options={
                    "extract_entities": True,
                    "build_relationships": True,
                    "enable_clinical_context": True
                }
            )

            print(f"SUCCESS: Knowledge graph processing completed")
            print(f"   Enhanced Content ID: {result.enhanced_content_id}")
            print(f"   Medical Entities: {len(result.medical_entities)}")
            print(f"   Clinical Relationships: {len(result.clinical_relationships)}")
            print(f"   Quality Score: {result.quality_metrics.overall_quality:.2f}")
            print(f"   Processing time: {result.processing_time:.2f}s")

            self.test_results['knowledge_graph'] = {
                'success': True,
                'enhanced_content_id': result.enhanced_content_id,
                'entities_count': len(result.medical_entities),
                'relationships_count': len(result.clinical_relationships),
                'quality_score': result.quality_metrics.overall_quality,
                'processing_time': result.processing_time
            }

            return result

        except Exception as e:
            print(f"FAILED: Knowledge graph processing failed - {e}")
            self.test_results['knowledge_graph'] = {
                'success': False,
                'error': str(e)
            }
            return None

    async def test_intelligent_agent_service(self):
        """测试智能体服务"""
        print("\n" + "="*60)
        print("TESTING INTELLIGENT AGENT SERVICE")
        print("="*60)

        try:
            from app.services.agent_orchestrator import IntelligentAgentOrchestrator, AgentType, ProcessingStrategy
            from app.services.intelligent_agent import RelevantContent

            # 创建智能体协调器
            orchestrator = IntelligentAgentOrchestrator()

            # 模拟相关内容
            relevant_contents = [
                RelevantContent(
                    content_id="test_content_001",
                    agent_type=AgentType.DIAGNOSIS,
                    text_segments=[
                        ("患者诊断为2型糖尿病，空腹血糖8.5mmol/L，餐后2小时血糖14.2mmol/L。", "section_1", "clinical_finding"),
                        ("患者有多饮、多尿、体重减轻等症状。", "section_2", "symptom")
                    ],
                    metadata={"content_type": "clinical_case"},
                    relevance_score=0.9,
                    priority=9
                ),
                RelevantContent(
                    content_id="test_content_001",
                    agent_type=AgentType.TREATMENT,
                    text_segments=[
                        ("建议使用二甲双胍治疗，起始剂量500mg每日两次。", "section_3", "treatment"),
                        ("需要配合饮食控制和运动治疗。", "section_4", "lifestyle")
                    ],
                    metadata={"content_type": "clinical_case"},
                    relevance_score=0.85,
                    priority=8
                )
            ]

            # 执行智能体协调
            agent_types = [AgentType.DIAGNOSIS, AgentType.TREATMENT]
            result = await orchestrator.coordinate_agents(
                relevant_content=relevant_contents,
                agent_types=agent_types,
                strategy=ProcessingStrategy.PARALLEL,
                fallback_strategy=None
            )

            print(f"SUCCESS: Intelligent agent processing completed")
            print(f"   Coordination ID: {result.coordination_id}")
            print(f"   Total Agents: {result.total_agents}")
            print(f"   Successful Agents: {result.successful_agents}")
            print(f"   Overall Confidence: {result.overall_confidence:.2f}")
            print(f"   Consensus Score: {result.consensus_score:.2f}")
            print(f"   Processing time: {result.total_processing_time:.2f}s")

            self.test_results['intelligent_agents'] = {
                'success': True,
                'coordination_id': result.coordination_id,
                'total_agents': result.total_agents,
                'successful_agents': result.successful_agents,
                'overall_confidence': result.overall_confidence,
                'consensus_score': result.consensus_score,
                'processing_time': result.total_processing_time
            }

            return result

        except Exception as e:
            print(f"FAILED: Intelligent agent processing failed - {e}")
            self.test_results['intelligent_agents'] = {
                'success': False,
                'error': str(e)
            }
            return None

    async def test_database_models(self):
        """测试数据库模型"""
        print("\n" + "="*60)
        print("TESTING DATABASE MODELS")
        print("="*60)

        try:
            from app.models.knowledge_graph import (
                MedicalEntityModel,
                LinkedEntityModel,
                ClinicalRelationshipModel
            )
            from app.models.intelligent_agent import (
                AgentJobModel,
                AgentCoordinationModel
            )

            print("SUCCESS: Database models imported successfully")

            # 测试模型创建
            test_entity = MedicalEntityModel(
                entity_id="test_entity_001",
                entity_type="disease",
                entity_name="2型糖尿病",
                entity_code="E11",
                coding_system="ICD-10",
                entity_description="2型糖尿病 mellitus"
            )

            test_coordination = AgentCoordinationModel(
                coordination_id="test_coordination_001",
                enhanced_content_id="test_content_001",
                coordination_strategy="parallel",
                total_agents=2,
                successful_agents=2,
                failed_agents=0,
                integrated_summary="Test summary"
            )

            print(f"SUCCESS: Database models created successfully")
            print(f"   Entity model: {test_entity.entity_name}")
            print(f"   Coordination model: {test_coordination.coordination_id}")

            self.test_results['database_models'] = {
                'success': True,
                'entity_model': str(test_entity.entity_name),
                'coordination_model': str(test_coordination.coordination_id)
            }

            return True

        except Exception as e:
            print(f"FAILED: Database models test failed - {e}")
            self.test_results['database_models'] = {
                'success': False,
                'error': str(e)
            }
            return False

    async def run_all_tests(self):
        """运行所有测试"""
        print("CORE SERVICES TEST SUITE")
        print("="*80)
        print(f"Test started at: {datetime.now()}")
        print(f"Project root: {project_root}")

        # 设置测试文档
        self.setup_test_document()

        # 记录开始时间
        start_time = datetime.now()

        # 运行各项测试
        test_functions = [
            ("Database Models", self.test_database_models),
            ("Medical Parser", self.test_medical_parser_service),
            ("Knowledge Graph", self.test_knowledge_graph_service),
            ("Intelligent Agents", self.test_intelligent_agent_service)
        ]

        for test_name, test_func in test_functions:
            try:
                print(f"\n🧪 Running {test_name} test...")
                await test_func()
                print(f"✅ {test_name} test completed")
            except Exception as e:
                print(f"❌ {test_name} test failed: {e}")
                self.test_results[test_name.lower().replace(' ', '_')] = {
                    'success': False,
                    'error': str(e)
                }

        # 计算总处理时间
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        # 生成测试报告
        self.generate_test_report(total_time)

    def generate_test_report(self, total_time: float):
        """生成测试报告"""
        print("\n" + "="*80)
        print("CORE SERVICES TEST REPORT")
        print("="*80)

        successful_tests = sum(1 for result in self.test_results.values() if result.get('success', False))
        total_tests = len(self.test_results)

        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total tests: {total_tests}")
        print(f"   Successful tests: {successful_tests}")
        print(f"   Success rate: {successful_tests/total_tests*100:.1f}%")
        print(f"   Total processing time: {total_time:.2f}s")

        print(f"\n📋 TEST DETAILS:")
        for test_name, result in self.test_results.items():
            status = "PASS" if result.get('success', False) else "FAIL"
            print(f"   {test_name.replace('_', ' ').title()}: {status}")
            if not result.get('success', False):
                print(f"      Error: {result.get('error', 'Unknown error')}")

        # 系统架构验证
        print(f"\n🏗️ ARCHITECTURE VERIFICATION:")
        core_components = ['database_models', 'medical_parser', 'knowledge_graph', 'intelligent_agents']
        working_components = [comp for comp in core_components if self.test_results.get(comp, {}).get('success', False)]

        print(f"   Core components working: {len(working_components)}/{len(core_components)}")
        for comp in working_components:
            print(f"   ✅ {comp.replace('_', ' ').title()}")

        # 最终评估
        print(f"\n🎯 SYSTEM ASSESSMENT:")
        if successful_tests == total_tests:
            print("   🏆 EXCELLENT: All core services working perfectly")
            print("   ✅ System architecture validated and ready")
            grade = "A"
        elif successful_tests >= total_tests * 0.75:
            print("   👍 GOOD: Most core services working")
            print("   🔧 Minor adjustments needed")
            grade = "B"
        elif successful_tests >= total_tests * 0.5:
            print("   ⚠️ FAIR: Half of core services functional")
            print("   🔨 Some debugging required")
            grade = "C"
        else:
            print("   ❌ POOR: Major issues detected")
            print("   🚨 Extensive troubleshooting needed")
            grade = "D"

        print(f"   Grade: {grade}")

        # 保存测试报告
        report_data = {
            "test_timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests * 100,
            "total_processing_time": total_time,
            "grade": grade,
            "test_results": self.test_results,
            "working_components": working_components
        }

        report_path = project_root / "core_services_test_report.json"
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
            print(f"\n📄 Test report saved to: {report_path}")
        except Exception as e:
            print(f"\n⚠️ Failed to save test report: {e}")


async def main():
    """主函数"""
    print("MEDICAL DOCUMENT PROCESSING CORE SERVICES TEST")
    print("="*80)

    try:
        test_suite = CoreServicesTestSuite()
        await test_suite.run_all_tests()

    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        logger.exception("Test suite error")


if __name__ == "__main__":
    asyncio.run(main())