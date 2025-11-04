"""
节点5：渐进式内容生成层
Node 5: Progressive Content Generation Layer
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import asyncio
import json
from dataclasses import asdict

from app.core.database import get_db
from app.core.logger import get_logger
from app.services.intelligent_agent import AgentResults
from app.services.progressive_generator import get_progressive_generator, PVGDocument
from celery_worker.workflow.base_node import BaseWorkflowNode
from app.enums.common import ContentPriority

logger = get_logger(__name__)


class ProgressiveGeneratorNode(BaseWorkflowNode):
    """渐进式内容生成节点"""

    def __init__(self) -> None:
        super().__init__()
        self.logger = get_logger(__name__)
        self.node_name = "progressive_generator"
        self.node_description = "渐进式内容生成层"

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理渐进式内容生成任务"""
        try:
            self.logger.info(f"开始处理渐进式内容生成任务: {input_data.get('task_id', 'unknown')}")

            # 获取输入参数
            agent_results_data = input_data.get('agent_results')
            guideline_id = input_data.get('guideline_id')
            task_id = input_data.get('task_id')
            template_name = input_data.get('template_name', 'standard_clinical')
            enable_streaming = input_data.get('enable_streaming', False)

            if not agent_results_data:
                raise ValueError("缺少智能体结果数据")

            if not guideline_id:
                raise ValueError("缺少指南ID参数")

            # 重建AgentResults对象
            agent_results = self._rebuild_agent_results(agent_results_data)

            # 创建进度回调
            progress_updates = []
            if enable_streaming:
                async def progress_callback(section_id: str, status: str, content: str):
                    progress_updates.append({
                        "section_id": section_id,
                        "status": status,
                        "content_preview": content[:100] if content else ""
                    })
                    self.logger.info(f"Section {section_id} status: {status}")

            # 执行渐进式生成
            pvg_document = await self._generate_pvg_document(
                agent_results=agent_results,
                guideline_id=guideline_id,
                template_name=template_name,
                task_id=task_id,
                progress_callback=progress_callback if enable_streaming else None
            )

            # 保存到数据库
            result_data = await self._save_to_database(pvg_document, guideline_id, task_id)

            self.logger.info(f"渐进式内容生成完成: {len(pvg_document.sections)} 个章节")

            return {
                "status": "success",
                "document_id": pvg_document.document_id,
                "sections_count": len(pvg_document.sections),
                "total_tokens": pvg_document.total_tokens,
                "total_cost": pvg_document.total_cost,
                "generation_time": pvg_document.generation_time,
                "progress_updates": progress_updates,
                "result_data": result_data
            }

        except Exception as e:
            self.logger.error(f"渐进式内容生成失败: {e}")
            return {
                "status": "error",
                "error_message": str(e)
            }

    def _rebuild_agent_results(self, agent_results_data: Dict[str, Any]) -> AgentResults:
        """重建AgentResults对象"""
        # 创建一个模拟的AgentResults对象
        return AgentResults(
            coordination_id=agent_results_data.get("coordination_id", ""),
            enhanced_content_id=agent_results_data.get("enhanced_content_id", ""),
            strategy=agent_results_data.get("strategy", "parallel"),
            results=[],
            integrated_summary=agent_results_data.get("integrated_summary", ""),
            overall_confidence=agent_results_data.get("overall_confidence", 0.0),
            total_processing_time=agent_results_data.get("total_processing_time", 0.0)
        )

    async def _generate_pvg_document(
        self,
        agent_results: AgentResults,
        guideline_id: str,
        template_name: str,
        task_id: str,
        progress_callback: Optional[callable] = None
    ) -> PVGDocument:
        """生成PVG文档"""
        generator = await get_progressive_generator()

        return await generator.generate_pvg(
            agent_results=agent_results,
            template_name=template_name,
            config={
                "enable_streaming": progress_callback is not None
            },
            progress_callback=progress_callback
        )

    async def _save_to_database(
        self,
        pvg_document: PVGDocument,
        guideline_id: str,
        task_id: str
    ) -> Dict[str, Any]:
        """保存到数据库"""
        try:
            async with get_db() as db:
                # 保存PVG文档主记录（简化版本，实际应用中应该有对应的模型类）
                document_record = {
                    "document_id": pvg_document.document_id,
                    "guideline_id": guideline_id,
                    "title": pvg_document.title,
                    "subtitle": pvg_document.subtitle,
                    "version": pvg_document.version,
                    "status": pvg_document.status,
                    "progress": pvg_document.progress,
                    "total_tokens": pvg_document.total_tokens,
                    "total_cost": pvg_document.total_cost,
                    "sections_count": len(pvg_document.sections),
                    "completed_sections": len(pvg_document.get_completed_sections()),
                    "task_id": task_id,
                    "metadata": pvg_document.metadata,
                    "template_config": asdict(pvg_document.template_structure) if pvg_document.template_structure else None,
                    "created_at": pvg_document.created_at,
                    "completed_at": pvg_document.completed_at
                }

                # 模拟保存到数据库
                await db.execute(
                    "INSERT INTO pvg_documents (document_id, guideline_id, title, subtitle, version, status, progress, total_tokens, total_cost, sections_count, completed_sections, task_id, metadata, created_at, completed_at) VALUES "
                    "(:document_id, :guideline_id, :title, :subtitle, :version, :status, :progress, :total_tokens, :total_cost, :sections_count, :completed_sections, :task_id, :metadata, :created_at, :completed_at)",
                    document_record
                )

                # 保存章节记录
                for section in pvg_document.sections:
                    section_record = {
                        "section_id": section.section_id,
                        "document_id": pvg_document.document_id,
                        "section_type": section.section_type.value,
                        "title": section.title,
                        "content": section.content,
                        "html_content": section.html_content,
                        "priority": section.priority.value,
                        "order": section.order,
                        "status": section.status.value,
                        "model_used": section.model_used,
                        "generation_time": section.generation_time,
                        "tokens_used": section.tokens_used,
                        "cost_estimate": section.cost_estimate,
                        "metadata": section.metadata,
                        "created_at": section.created_at,
                        "completed_at": section.completed_at
                    }

                    await db.execute(
                        "INSERT INTO pvg_sections (section_id, document_id, section_type, title, content, html_content, priority, order, status, model_used, generation_time, tokens_used, cost_estimate, metadata, created_at, completed_at) VALUES "
                        "(:section_id, :document_id, :section_type, :title, :content, :html_content, :priority, :order, :status, :model_used, :generation_time, :tokens_used, :cost_estimate, :metadata, :created_at, :completed_at)",
                        section_record
                    )

                await db.commit()

                return {
                    "document_id": pvg_document.document_id,
                    "sections_saved": len(pvg_document.sections),
                    "database_records": len(pvg_document.sections) + 1
                }

        except Exception as e:
            self.logger.error(f"保存到数据库失败: {e}")
            raise

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        required_fields = ['agent_results', 'guideline_id', 'task_id']

        for field in required_fields:
            if field not in input_data or not input_data[field]:
                self.logger.error(f"缺少必需字段: {field}")
                return False

        return True

    async def _stream_progress_update(self, section_id: str, update_data: Dict[str, Any]) -> None:
        """流式输出进度更新"""
        # 这里可以连接到WebSocket或其他实时通信机制
        try:
            # 模拟流式输出
            update_json = json.dumps(update_data, ensure_ascii=False)
            logger.info(f"Stream update for {section_id}: {update_json}")

            # 实际应用中，这里可能会：
            # 1. 通过WebSocket发送给客户端
            # 2. 写入到消息队列
            # 3. 发送到事件流
            pass

        except Exception as e:
            self.logger.error(f"流式输出失败: {e}")

    def get_node_info(self) -> Dict[str, Any]:
        """获取节点信息"""
        return {
            "node_name": self.node_name,
            "node_description": self.node_description,
            "node_type": "progressive_generator",
            "capabilities": [
                "渐进式内容生成",
                "多模型策略",
                "实时流式输出",
                "PVG模板系统",
                "成本优化",
                "质量控制",
                "进度跟踪"
            ],
            "supported_templates": [
                "standard_clinical",
                "emergency_guideline",
                "special_population",
                "chronic_disease"
            ],
            "model_assignments": {
                "high_priority": "gpt-4",
                "medium_priority": "gpt-3.5-turbo",
                "low_priority": "gpt-3.5-turbo-instruct"
            }
        }

    async def get_generation_statistics(self) -> Dict[str, Any]:
        """获取生成统计信息"""
        generator = await get_progressive_generator()
        return generator.get_generation_stats()

    async def estimate_generation_cost(
        self,
        agent_results: AgentResults,
        template_name: str = "standard_clinical",
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """估算生成成本"""
        generator = await get_progressive_generator()

        # 创建临时文档进行成本估算
        temp_document = PVGDocument(
            document_id="estimate_test",
            guideline_id="test",
            title="成本估算测试"
        )

        # 从模板结构估算章节数量和token需求
        template_manager = generator.template_manager
        template_structure = template_manager.get_template(template_name)

        total_estimated_tokens = sum(
            section.get("estimated_tokens", 500)
            for section in template_structure.sections
        )

        # 简化成本计算
        high_priority_sections = template_structure.get_high_priority_sections()
        medium_priority_sections = [s for s in template_structure.sections
                                     if s.get("priority") == ContentPriority.MEDIUM.value]
        low_priority_sections = [s for s in template_structure.sections
                                   if s.get("priority") == ContentPriority.LOW.value]

        estimated_cost = (
            len(high_priority_sections) * 0.03 +  # GPT-4 高质量章节
            len(medium_priority_sections) * 0.002 +  # GPT-3.5-turbo 中等章节
            len(low_priority_sections) * 0.0015  # GPT-3.5-turbo-instruct 低成本章节
        ) * (total_estimated_tokens / 1000)

        return {
            "estimated_tokens": total_estimated_tokens,
            "estimated_cost": estimated_cost,
            "high_priority_sections": len(high_priority_sections),
            "medium_priority_sections": len(medium_priority_sections),
            "low_priority_sections": len(low_priority_sections),
            "template_type": template_name
        }


# 节点工厂函数
def create_node() -> ProgressiveGeneratorNode:
    """创建渐进式内容生成节点实例"""
    return ProgressiveGeneratorNode()


# 导出节点
__all__ = ['ProgressiveGeneratorNode', 'create_node']