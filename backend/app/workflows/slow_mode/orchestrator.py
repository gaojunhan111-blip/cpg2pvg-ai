"""
Slow工作流编排器
CPG2PVG-AI System Slow Workflow Orchestrator
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.workflows.base import BaseWorkflowOrchestrator
from app.workflows.slow_mode.document_parser import HierarchicalMedicalParser
from app.workflows.slow_mode.multimodal_processor import MultiModalProcessor
from app.workflows.slow_mode.knowledge_graph import MedicalKnowledgeGraph
from app.workflows.slow_mode.agent_system import IntelligentAgentOrchestrator
from app.workflows.slow_mode.content_generator import ProgressiveContentGenerator
from app.workflows.slow_mode.cache_system import MedicalContentCache
from app.workflows.slow_mode.cost_optimizer import AdaptiveCostOptimizer
from app.workflows.slow_mode.quality_controller import MultiLayerQualityController
from app.workflows.slow_mode.performance_monitor import PerformanceMonitor

from app.workflows.types import (
    ProcessingContext,
    ProcessingResult,
    WorkflowState,
    ProcessingStatus,
)

logger = logging.getLogger(__name__)


class SlowWorkflowOrchestrator(BaseWorkflowOrchestrator):
    """Slow工作流编排器 - 完整保留9个技术节点"""

    def __init__(self):
        super().__init__(
            name="SlowWorkflow",
            description="完整的Slow工作流，包含9个核心技术节点"
        )

        # 初始化所有工作流节点
        self._initialize_nodes()

        # 定义工作流步骤顺序
        self._define_workflow_steps()

    def _initialize_nodes(self):
        """初始化所有工作流节点"""
        try:
            # 节点1: 智能文档解析层
            self.add_node(HierarchicalMedicalParser())

            # 节点2: 多模态内容处理管道
            self.add_node(MultiModalProcessor())

            # 节点3: 基于知识图谱的语义理解
            self.add_node(MedicalKnowledgeGraph())

            # 节点4: 分层智能体系统
            self.add_node(IntelligentAgentOrchestrator())

            # 节点5: 渐进式内容生成
            self.add_node(ProgressiveContentGenerator())

            # 节点6: 智能缓存和记忆系统
            self.add_node(MedicalContentCache())

            # 节点7: 成本优化策略
            self.add_node(AdaptiveCostOptimizer())

            # 节点8: 质量控制和验证系统
            self.add_node(MultiLayerQualityController())

            # 节点9: 性能监控和自适应调整
            self.add_node(PerformanceMonitor())

            logger.info("Slow工作流所有节点初始化完成")

        except Exception as e:
            logger.error(f"初始化工作流节点失败: {str(e)}")
            raise

    def _define_workflow_steps(self):
        """定义工作流步骤顺序"""
        # 按照Slow工作流的9个技术节点顺序
        workflow_steps = [
            "HierarchicalMedicalParser",      # 节点1: 智能文档解析
            "MultiModalProcessor",           # 节点2: 多模态处理
            "MedicalKnowledgeGraph",        # 节点3: 知识图谱
            "IntelligentAgentOrchestrator",   # 节点4: 智能体系统
            "ProgressiveContentGenerator",   # 节点5: 内容生成
            "MedicalContentCache",           # 节点6: 缓存系统
            "AdaptiveCostOptimizer",         # 节点7: 成本优化
            "MultiLayerQualityController",    # 节点8: 质量控制
            "PerformanceMonitor",            # 节点9: 性能监控
        ]

        for step in workflow_steps:
            self.add_step(step)

        logger.info(f"Slow工作流步骤定义完成，共{len(workflow_steps)}个步骤")

    async def execute_workflow(
        self,
        context: ProcessingContext,
        input_data: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """执行完整的Slow工作流"""
        # 创建工作流状态
        state = WorkflowState()
        state.status = ProcessingStatus.RUNNING
        state.context = context
        state.metrics.step_count = len(self.workflow_steps)
        state.started_at = datetime.utcnow()
        state.current_step = None

        try:
            logger.info(f"开始执行Slow工作流，指南ID: {context.guideline_id}")

            # 逐步执行所有工作流节点
            for i, step_name in enumerate(self.workflow_steps):
                state.current_step = step_name
                state.calculate_progress()

                logger.info(f"执行第{i+1}/{len(self.workflow_steps)}个步骤: {step_name}")

                # 执行单个步骤
                step_results = await self.execute_workflow_step(
                    step_name, context, input_data
                )

                # 将结果添加到状态中
                for result in step_results:
                    state.add_result(result)

                    # 如果步骤失败，记录失败信息
                    if not result.success:
                        state.add_failed_step()
                        logger.error(f"步骤 {step_name} 执行失败: {result.error_message}")

                # 更新进度
                state.calculate_progress()

                # 实时更新进度到数据库
                await self._update_progress_to_database(state)

                # 检查是否需要提前终止
                if self._should_terminate_early(state):
                    logger.warning(f"工作流提前终止在步骤: {step_name}")
                    break

            # 工作流完成
            state.status = ProcessingStatus.COMPLETED
            state.completed_at = datetime.utcnow()
            state.current_step = None
            state.calculate_progress()

            logger.info(f"Slow工作流执行完成，总耗时: {format_time(state.metrics.total_execution_time)}")
            logger.info(f"总成本: {format_cost(state.metrics.total_cost)}, 总token: {state.metrics.total_tokens}")

            # 生成处理结果报告
            await self._generate_processing_report(state)

            return state

        except Exception as e:
            logger.error(f"Slow工作流执行失败: {str(e)}")
            state.status = ProcessingStatus.FAILED
            state.completed_at = datetime.utcnow()

            # 添加错误结果
            error_result = ProcessingResult(
                step_name="WorkflowOrchestrator",
                status=ProcessingStatus.FAILED,
                success=False,
                error_message=str(e),
                execution_time=0.0
            )
            state.add_result(error_result)

            return state

    async def _update_progress_to_database(self, state: WorkflowState):
        """更新进度到数据库"""
        try:
            from app.core.database import get_db_session
            from app.models import Task, TaskStatus

            async with get_db_session() as session:
                # 这里应该根据context中的guideline_id查找对应的Task记录
                # 并更新其状态和进度
                # 简化实现，实际应该有完整的Task查找逻辑
                pass

        except Exception as e:
            logger.error(f"更新进度到数据库失败: {str(e)}")

    def _should_terminate_early(self, state: WorkflowState) -> bool:
        """判断是否应该提前终止工作流"""
        # 如果失败步骤过多，提前终止
        failure_rate = state.metrics.failed_steps / max(1, state.metrics.completed_steps)
        if failure_rate > 0.3:  # 失败率超过30%
            return True

        # 如果累计成本过高，提前终止
        if hasattr(state.context, 'max_cost') and state.metrics.total_cost > state.context.max_cost:
            return True

        return False

    async def _generate_processing_report(self, state: WorkflowState):
        """生成处理报告"""
        try:
            # 这里可以生成详细的处理报告
            # 包括每个步骤的详细信息、质量评估、成本分析等
            logger.info("生成处理报告")

        except Exception as e:
            logger.error(f"生成处理报告失败: {str(e)}")

    def get_workflow_status(self, state: WorkflowState) -> Dict[str, Any]:
        """获取工作流状态"""
        return {
            "workflow_id": state.workflow_id,
            "status": state.status.value,
            "progress": state.progress,
            "current_step": state.current_step,
            "total_steps": state.metrics.step_count,
            "completed_steps": state.metrics.completed_steps,
            "failed_steps": state.metrics.failed_steps,
            "execution_time": state.metrics.total_execution_time,
            "total_cost": state.metrics.total_cost,
            "total_tokens": state.metrics.total_tokens,
            "quality_score": state.metrics.average_quality_score,
            "started_at": state.started_at.isoformat() if state.started_at else None,
            "completed_at": state.completed_at.isoformat() if state.completed_at else None,
            "step_results": [result.to_dict() for result in state.results],
        }

    async def get_step_estimates(self) -> Dict[str, Dict[str, Any]]:
        """获取各步骤的预估信息"""
        estimates = {
            "HierarchicalMedicalParser": {
                "estimated_time": 120,  # 2分钟
                "estimated_cost": 0.02,
                "description": "智能文档解析，识别结构和内容"
            },
            "MultiModalProcessor": {
                "estimated_time": 180,  # 3分钟
                "estimated_cost": 0.03,
                "description": "多模态内容处理，处理文本、表格、图像"
            },
            "MedicalKnowledgeGraph": {
                "estimated_time": 240,  # 4分钟
                "estimated_cost": 0.05,
                "description": "知识图谱语义理解和增强"
            },
            "IntelligentAgentOrchestrator": {
                "estimated_time": 480,  # 8分钟
                "estimated_cost": 0.10,
                "description": "多智能体协作处理"
            },
            "ProgressiveContentGenerator": {
                "estimated_time": 360,  # 6分钟
                "estimated_cost": 0.08,
                "description": "渐进式内容生成，关键部分优先"
            },
            "MedicalContentCache": {
                "estimated_time": 30,   # 30秒
                "estimated_cost": 0.00,
                "description": "智能缓存和记忆系统"
            },
            "AdaptiveCostOptimizer": {
                "estimated_time": 60,   # 1分钟
                "estimated_cost": 0.01,
                "description": "成本优化策略"
            },
            "MultiLayerQualityController": {
                "estimated_time": 180,  # 3分钟
                "estimated_cost": 0.04,
                "description": "多层质量控制和验证"
            },
            "PerformanceMonitor": {
                "estimated_time": 30,   # 30秒
                "estimated_cost": 0.00,
                "description": "性能监控和自适应调整"
            },
        }

        return estimates

    def get_workflow_statistics(self) -> Dict[str, Any]:
        """获取工作流统计信息"""
        return {
            "total_nodes": len(self.nodes),
            "total_steps": len(self.workflow_steps),
            "estimated_total_time": sum(estimate["estimated_time"] for estimate in self.get_step_estimates().values()),
            "estimated_total_cost": sum(estimate["estimated_cost"] for estimate in self.get_step_estimates().values()),
            "workflow_name": self.name,
            "workflow_description": self.description,
        }


# 便捷函数
async def create_slow_workflow() -> SlowWorkflowOrchestrator:
    """创建Slow工作流实例"""
    orchestrator = SlowWorkflowOrchestrator()
    return orchestrator


# 工作流执行函数
async def process_guideline_with_slow_workflow(
    guideline_id: int,
    user_id: int,
    processing_mode: str = "slow",
    **kwargs
) -> WorkflowState:
    """使用Slow工作流处理指南的便捷函数"""
    from app.workflows.types import ProcessingContext, ProcessingMode, CostLevel, QualityLevel

    # 创建处理上下文
    context = ProcessingContext(
        guideline_id=guideline_id,
        user_id=user_id,
        processing_mode=ProcessingMode(processing_mode),
        cost_level=CostLevel.MEDIUM,
        quality_requirement=QualityLevel.HIGH,
        **kwargs
    )

    # 创建并执行工作流
    orchestrator = await create_slow_workflow()
    state = await orchestrator.execute_workflow(context)

    return state


# 格式化函数
def format_time(seconds: float) -> str:
    """格式化时间显示"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        return f"{seconds/60:.1f}分钟"
    else:
        return f"{seconds/3600:.1f}小时"


def format_cost(cost: float) -> str:
    """格式化成本显示"""
    if cost < 1:
        return f"${cost*1000:.1f}c"
    else:
        return f"${cost:.2f}"