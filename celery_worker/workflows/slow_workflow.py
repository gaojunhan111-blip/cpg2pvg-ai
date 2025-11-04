"""
Slow工作流处理器
CPG2PVG-AI System Slow Workflow Processor
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.workflows.slow_mode.orchestrator import SlowWorkflowOrchestrator
from app.workflows.types import ProcessingContext, ProcessingMode, CostLevel, QualityLevel

logger = logging.getLogger(__name__)


class SlowWorkflowProcessor:
    """Slow工作流处理器"""

    def __init__(self):
        self.orchestrator = None

    async def process(self, guideline: Any, task_id: str) -> Dict[str, Any]:
        """处理指南"""
        try:
            logger.info(f"开始Slow工作流处理，指南ID: {guideline.id}, 任务ID: {task_id}")

            # 初始化编排器
            self.orchestrator = SlowWorkflowOrchestrator()

            # 创建处理上下文
            context = ProcessingContext(
                guideline_id=guideline.id,
                user_id=guideline.user_id,
                processing_mode=ProcessingMode.SLOW,
                cost_level=CostLevel.MEDIUM,
                quality_requirement=QualityLevel.HIGH,
                task_id=task_id
            )

            # 准备输入数据
            input_data = {
                "document_content": guideline.content,
                "document_type": guideline.document_type,
                "file_metadata": guideline.file_metadata or {}
            }

            # 执行工作流
            workflow_state = await self.orchestrator.execute_workflow(context, input_data)

            # 生成处理结果
            result = {
                "task_id": task_id,
                "guideline_id": guideline.id,
                "status": workflow_state.status.value,
                "progress": workflow_state.progress,
                "results": [],
                "metadata": {
                    "workflow_name": "SlowWorkflow",
                    "execution_time": workflow_state.metrics.total_execution_time,
                    "total_cost": workflow_state.metrics.total_cost,
                    "total_tokens": workflow_state.metrics.total_tokens,
                    "quality_score": workflow_state.metrics.average_quality_score,
                    "started_at": workflow_state.started_at.isoformat() if workflow_state.started_at else None,
                    "completed_at": workflow_state.completed_at.isoformat() if workflow_state.completed_at else None
                }
            }

            # 提取处理结果
            for step_result in workflow_state.results:
                if step_result.success and step_result.data:
                    result["results"].append({
                        "step_name": step_result.step_name,
                        "data": step_result.data,
                        "execution_time": step_result.execution_time
                    })

            logger.info(f"Slow工作流处理完成，状态: {workflow_state.status.value}")
            return result

        except Exception as e:
            logger.error(f"Slow工作流处理失败: {str(e)}")
            return {
                "task_id": task_id,
                "guideline_id": guideline.id,
                "status": "FAILED",
                "error": str(e),
                "metadata": {
                    "workflow_name": "SlowWorkflow",
                    "failed_at": datetime.utcnow().isoformat()
                }
            }