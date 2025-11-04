#!/usr/bin/env python3
"""
Complete Four-Node Workflow System Test
完整四节点工作流系统测试
"""

import os
import sys
import asyncio
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入工作流节点
try:
    from celery_worker.workflow_nodes.node1_medical_parser import process_medical_document
    from celery_worker.workflow_nodes.node2_multimodal_processor import process_multimodal_content
    from celery_worker.workflow_nodes.node3_knowledge_graph import process_semantic_understanding
    from celery_worker.workflow_nodes.node4_intelligent_agents import process_medical_intelligent_analysis
    print("✅ Successfully imported all workflow nodes")
except ImportError as e:
    print(f"❌ Failed to import workflow nodes: {e}")
    sys.exit(1)

from app.core.logger import get_logger

logger = get_logger(__name__)


class WorkflowTestSuite:
    """工作流测试套件"""

    def __init__(self):
        self.test_results = []
        self.test_document_path = None
        self.workflow_outputs = {}

    async def setup_test_document(self):
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
三线用药：GLP-1受体激动剂、胰岛素

## 预防措施
### 一级预防
- 健康饮食
- 规律运动
- 控制体重
- 戒烟限酒

### 筛查建议
- 年龄≥45岁的人群应定期筛查
- 肥胖、高血压、高血脂等高危人群应更早开始筛查

## 特殊人群管理

### 儿童糖尿病
- 以1型糖尿病为主
- 需要特别注意生长发育
- 家长教育非常重要

### 老年糖尿病
- 心血管风险较高
- 需要个体化治疗目标
- 注意低血糖风险

### 妊娠期糖尿病
- 通常在妊娠24-28周筛查
- 饮食控制为首选治疗
- 胰岛素治疗指征：血糖控制不佳

## 监测随访

### 自我监测
- 血糖监测频率根据治疗方案调整
- 记录血糖值和相关因素

### 定期随访
- 每3-6个月随访一次
- 检查糖化血红蛋白
- 评估并发症

## 结语
糖尿病是一种需要长期管理的慢性疾病，通过规范的治疗和监测，可以有效控制血糖，预防并发症，提高患者生活质量。
"""

        self.test_document_path = test_docs_dir / "diabetes_guideline.txt"
        with open(self.test_document_path, 'w', encoding='utf-8') as f:
            f.write(test_content)

        print(f"✅ Created test document: {self.test_document_path}")
        return str(self.test_document_path)

    async def test_node1_medical_parsing(self) -> Dict[str, Any]:
        """测试节点1：医学解析"""
        print("\n" + "="*60)
        print("TESTING NODE 1: MEDICAL DOCUMENT PARSING")
        print("="*60)

        try:
            result = await process_medical_document(
                document_path=str(self.test_document_path),
                document_type="clinical_guideline"
            )

            print(f"✅ Node 1 completed successfully")
            print(f"   Document ID: {result.get('document_id')}")
            print(f"   Sections extracted: {len(result.get('structured_sections', []))}")
            print(f"   Processing time: {result.get('statistics', {}).get('parsing_time', 0):.2f}s")

            self.workflow_outputs['node1'] = result
            return result

        except Exception as e:
            print(f"❌ Node 1 failed: {e}")
            return {"success": False, "error": str(e)}

    async def test_node2_multimodal_processing(self) -> Dict[str, Any]:
        """测试节点2：多模态处理"""
        print("\n" + "="*60)
        print("TESTING NODE 2: MULTIMODAL CONTENT PROCESSING")
        print("="*60)

        if 'node1' not in self.workflow_outputs:
            print("❌ Node 1 output not available")
            return {"success": False, "error": "Node 1 output not available"}

        try:
            node1_output = self.workflow_outputs['node1']
            document_id = node1_output.get('document_id')

            result = await process_multimodal_content(
                document_id=document_id,
                processing_options={
                    "extract_tables": True,
                    "analyze_images": False,  # 文本测试，不包含图像
                    "min_confidence": 0.7
                }
            )

            print(f"✅ Node 2 completed successfully")
            print(f"   Content ID: {result.get('content_id')}")
            print(f"   Features extracted: {len(result.get('extracted_features', {}))}")
            print(f"   Processing time: {result.get('processing_time', 0):.2f}s")

            self.workflow_outputs['node2'] = result
            return result

        except Exception as e:
            print(f"❌ Node 2 failed: {e}")
            return {"success": False, "error": str(e)}

    async def test_node3_knowledge_graph(self) -> Dict[str, Any]:
        """测试节点3：知识图谱"""
        print("\n" + "="*60)
        print("TESTING NODE 3: KNOWLEDGE GRAPH SEMANTIC UNDERSTANDING")
        print("="*60)

        if 'node2' not in self.workflow_outputs:
            print("❌ Node 2 output not available")
            return {"success": False, "error": "Node 2 output not available"}

        try:
            node2_output = self.workflow_outputs['node2']
            content_id = node2_output.get('content_id')

            result = await process_semantic_understanding(
                enhanced_content_id=content_id,
                processing_options={
                    "extract_entities": True,
                    "build_relationships": True,
                    "enable_clinical_context": True
                }
            )

            print(f"✅ Node 3 completed successfully")
            print(f"   Enhanced Content ID: {result.get('enhanced_content_id')}")
            print(f"   Entities extracted: {len(result.get('entities', {}))}")
            print(f"   Relationships: {len(result.get('relationships', {}))}")
            print(f"   Processing time: {result.get('processing_time', 0):.2f}s")

            self.workflow_outputs['node3'] = result
            return result

        except Exception as e:
            print(f"❌ Node 3 failed: {e}")
            return {"success": False, "error": str(e)}

    async def test_node4_intelligent_agents(self) -> Dict[str, Any]:
        """测试节点4：智能体系统"""
        print("\n" + "="*60)
        print("TESTING NODE 4: INTELLIGENT AGENT SYSTEM")
        print("="*60)

        if 'node3' not in self.workflow_outputs:
            print("❌ Node 3 output not available")
            return {"success": False, "error": "Node 3 output not available"}

        try:
            node3_output = self.workflow_outputs['node3']
            enhanced_content_id = node3_output.get('enhanced_content_id')

            result = await process_medical_intelligent_analysis(
                enhanced_content_id=enhanced_content_id,
                processing_options={
                    "enabled_agents": ["diagnosis", "treatment", "prevention", "monitoring"],
                    "processing_strategy": "parallel",
                    "min_confidence_score": 0.6
                }
            )

            print(f"✅ Node 4 completed successfully")
            print(f"   Coordination ID: {result.get('coordination_id')}")
            print(f"   Agents successful: {result.get('statistics', {}).get('successful_agents', 0)}/{result.get('statistics', {}).get('total_agents', 0)}")
            print(f"   Overall confidence: {result.get('quality_metrics', {}).get('overall_confidence', 0):.2f}")
            print(f"   Processing time: {result.get('statistics', {}).get('total_processing_time', 0):.2f}s")

            self.workflow_outputs['node4'] = result
            return result

        except Exception as e:
            print(f"❌ Node 4 failed: {e}")
            return {"success": False, "error": str(e)}

    async def run_complete_workflow(self):
        """运行完整工作流测试"""
        print("🚀 STARTING COMPLETE FOUR-NODE WORKFLOW TEST")
        print("="*60)
        print(f"Test started at: {datetime.now()}")
        print(f"Project root: {project_root}")

        # 设置测试文档
        await self.setup_test_document()

        # 记录开始时间
        start_time = datetime.now()

        # 依次测试各个节点
        node_results = []

        # 节点1：医学文档解析
        result = await self.test_node1_medical_parsing()
        node_results.append(("Node 1 - Medical Parsing", result))

        # 节点2：多模态内容处理
        result = await self.test_node2_multimodal_processing()
        node_results.append(("Node 2 - Multimodal Processing", result))

        # 节点3：知识图谱语义理解
        result = await self.test_node3_knowledge_graph()
        node_results.append(("Node 3 - Knowledge Graph", result))

        # 节点4：智能体系统
        result = await self.test_node4_intelligent_agents()
        node_results.append(("Node 4 - Intelligent Agents", result))

        # 计算总处理时间
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        # 生成测试报告
        self.generate_test_report(node_results, total_time)

        return node_results

    def generate_test_report(self, node_results: List, total_time: float):
        """生成测试报告"""
        print("\n" + "="*80)
        print("COMPLETE WORKFLOW TEST REPORT")
        print("="*80)

        successful_nodes = sum(1 for _, result in node_results if result.get('success', False))
        total_nodes = len(node_results)

        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total nodes: {total_nodes}")
        print(f"   Successful nodes: {successful_nodes}")
        print(f"   Success rate: {successful_nodes/total_nodes*100:.1f}%")
        print(f"   Total processing time: {total_time:.2f}s")

        print(f"\n📋 NODE DETAILS:")
        for i, (node_name, result) in enumerate(node_results, 1):
            status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
            print(f"   {i}. {node_name}: {status}")
            if not result.get('success', False):
                print(f"      Error: {result.get('error', 'Unknown error')}")

        print(f"\n🔗 WORKFLOW CHAIN:")
        if successful_nodes == total_nodes:
            print("   ✅ Complete workflow chain successful")
            print("   📄 Document → 🧠 Multimodal → 🕸️ Knowledge Graph → 🤖 Intelligent Agents")
        else:
            print("   ⚠️ Workflow chain broken at some nodes")

        # 数据流验证
        print(f"\n📊 DATA FLOW VALIDATION:")
        data_flow_valid = True

        if 'node1' in self.workflow_outputs and self.workflow_outputs['node1'].get('success'):
            doc_id = self.workflow_outputs['node1'].get('document_id')
            print(f"   Node 1 → Node 2: ✅ Document ID {doc_id}")
        else:
            print("   Node 1 → Node 2: ❌ No valid document ID")
            data_flow_valid = False

        if 'node2' in self.workflow_outputs and self.workflow_outputs['node2'].get('success'):
            content_id = self.workflow_outputs['node2'].get('content_id')
            print(f"   Node 2 → Node 3: ✅ Content ID {content_id}")
        else:
            print("   Node 2 → Node 3: ❌ No valid content ID")
            data_flow_valid = False

        if 'node3' in self.workflow_outputs and self.workflow_outputs['node3'].get('success'):
            enhanced_id = self.workflow_outputs['node3'].get('enhanced_content_id')
            print(f"   Node 3 → Node 4: ✅ Enhanced Content ID {enhanced_id}")
        else:
            print("   Node 3 → Node 4: ❌ No valid enhanced content ID")
            data_flow_valid = False

        # 最终评估
        print(f"\n🎯 FINAL ASSESSMENT:")
        if successful_nodes == total_nodes and data_flow_valid:
            print("   🏆 EXCELLENT: All nodes working perfectly")
            print("   ✅ System ready for production deployment")
            grade = "A"
        elif successful_nodes >= total_nodes * 0.75:
            print("   👍 GOOD: Most nodes working correctly")
            print("   🔧 Minor fixes needed before production")
            grade = "B"
        elif successful_nodes >= total_nodes * 0.5:
            print("   ⚠️ FAIR: Half of the nodes working")
            print("   🔨 Significant work required")
            grade = "C"
        else:
            print("   ❌ POOR: Major issues detected")
            print("   🚨 Extensive debugging and fixes required")
            grade = "D"

        print(f"   Grade: {grade}")

        # 保存测试报告
        report_data = {
            "test_timestamp": datetime.now().isoformat(),
            "total_nodes": total_nodes,
            "successful_nodes": successful_nodes,
            "success_rate": successful_nodes / total_nodes * 100,
            "total_processing_time": total_time,
            "data_flow_valid": data_flow_valid,
            "grade": grade,
            "node_results": [
                {
                    "name": name,
                    "success": result.get('success', False),
                    "error": result.get('error')
                }
                for name, result in node_results
            ],
            "workflow_outputs": self.workflow_outputs
        }

        report_path = project_root / "test_workflow_report.json"
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
            print(f"\n📄 Test report saved to: {report_path}")
        except Exception as e:
            print(f"\n⚠️ Failed to save test report: {e}")


async def main():
    """主函数"""
    print("MEDICAL DOCUMENT PROCESSING WORKFLOW TEST SUITE")
    print("="*80)

    try:
        test_suite = WorkflowTestSuite()
        await test_suite.run_complete_workflow()

    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        logger.exception("Test suite error")


if __name__ == "__main__":
    asyncio.run(main())