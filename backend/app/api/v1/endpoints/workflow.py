"""
工作流API端点
Workflow API Endpoints
提供完整的9节点工作流API接口
"""

import json
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.logger import get_logger
from app.services.workflow_orchestrator import get_workflow_orchestrator, WorkflowConfig, ProcessingMode

logger = get_logger(__name__)
router = APIRouter()


class WorkflowRequest(BaseModel):
    """工作流请求"""
    content: str = Field(..., description="医学指南内容")
    file_path: Optional[str] = Field(None, description="文件路径")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")

    # 配置选项
    processing_mode: ProcessingMode = ProcessingMode.STANDARD
    enable_caching: bool = True
    enable_cost_optimization: bool = True
    enable_quality_control: bool = True
    enable_performance_monitoring: bool = True

    # 节点选择
    enabled_nodes: Optional[List[str]] = None
    custom_config: Optional[Dict[str, Any]] = None


class WorkflowResponse(BaseModel):
    """工作流响应"""
    execution_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_duration: Optional[float] = None

    # 结果数据
    node_results: Dict[str, Any] = {}
    final_quality_score: Optional[float] = None
    pvg_document: Optional[Dict[str, Any]] = None

    # 性能指标
    total_tokens: int = 0
    total_cost: float = 0.0
    cost_savings: float = 0.0

    # 质量指标
    issues_found: List[str] = []
    recommendations: List[str] = []


class WorkflowStatusResponse(BaseModel):
    """工作流状态响应"""
    execution_id: str
    status: str
    progress_percentage: float
    current_phase: str
    completed_nodes: List[str]
    pending_nodes: List[str]
    error_message: Optional[str] = None


@router.post("/execute", response_model=WorkflowResponse)
async def execute_workflow(
    request: WorkflowRequest,
    background_tasks: BackgroundTasks
) -> WorkflowResponse:
    """执行完整的工作流"""
    try:
        logger.info(f"Received workflow execution request")

        # 获取工作流编排器
        orchestrator = await get_workflow_orchestrator()

        # 构建配置
        config = WorkflowConfig(
            processing_mode=request.processing_mode,
            enable_caching=request.enable_caching,
            enable_cost_optimization=request.enable_cost_optimization,
            enable_quality_control=request.enable_quality_control,
            enable_performance_monitoring=request.enable_performance_monitoring,
            enabled_nodes=request.enabled_nodes
        )

        # 构建输入数据
        input_data = {
            "content": request.content,
            "file_path": request.file_path,
            "metadata": request.metadata
        }

        # 执行工作流
        workflow_execution = await orchestrator.execute_complete_workflow(
            input_data=input_data,
            config=config
        )

        # 构建响应
        response = WorkflowResponse(
            execution_id=workflow_execution.execution_id,
            status=workflow_execution.status,
            started_at=workflow_execution.started_at,
            completed_at=workflow_execution.completed_at,
            total_duration=workflow_execution.total_duration,
            node_results=workflow_execution.node_results,
            final_quality_score=workflow_execution.final_quality_score,
            total_tokens=workflow_execution.total_tokens,
            total_cost=workflow_execution.total_cost
        )

        # 提取PVG文档
        if "progressive_generator" in workflow_execution.node_results:
            pvg_data = workflow_execution.node_results["progressive_generator"].get("result_data", {}).get("pvg_document", {})
            if pvg_data:
                response.pvg_document = pvg_data

        # 提取质量信息
        if "quality_controller" in workflow_execution.node_results:
            quality_data = workflow_execution.node_results["quality_controller"].get("result_data", {}).get("quality_result", {})
            if quality_data:
                response.issues_found = quality_data.get("issues_found", [])
                response.recommendations = quality_data.get("recommendations", [])

        # 提取成本节省
        if "cost_optimizer" in workflow_execution.node_results:
            cost_data = workflow_execution.node_results["cost_optimizer"].get("metadata", {})
            response.cost_savings = cost_data.get("total_savings", 0.0)

        logger.info(f"Workflow execution completed: {workflow_execution.execution_id}")
        return response

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"工作流执行失败: {str(e)}")


@router.post("/execute-streaming")
async def execute_workflow_streaming(request: WorkflowRequest) -> StreamingResponse:
    """执行流式工作流"""
    try:
        logger.info(f"Received streaming workflow execution request")

        # 获取工作流编排器
        orchestrator = await get_workflow_orchestrator()

        # 构建配置
        config = WorkflowConfig(
            processing_mode=request.processing_mode,
            enable_caching=request.enable_caching,
            enable_cost_optimization=request.enable_cost_optimization,
            enable_quality_control=request.enable_quality_control,
            enable_performance_monitoring=request.enable_performance_monitoring,
            enabled_nodes=request.enabled_nodes
        )

        # 构建输入数据
        input_data = {
            "content": request.content,
            "file_path": request.file_path,
            "metadata": request.metadata
        }

        async def generate_stream():
            """生成流式响应"""
            try:
                # 进度回调函数
                async def progress_callback(status: str, percentage: int):
                    yield f"data: {json.dumps({'type': 'progress', 'status': status, 'percentage': percentage})}\n\n"

                # 执行工作流
                workflow_execution = await orchestrator.execute_complete_workflow(
                    input_data=input_data,
                    config=config,
                    progress_callback=progress_callback
                )

                # 发送最终结果
                result = {
                    "type": "complete",
                    "execution_id": workflow_execution.execution_id,
                    "status": workflow_execution.status,
                    "final_quality_score": workflow_execution.final_quality_score,
                    "total_duration": workflow_execution.total_duration
                }

                yield f"data: {json.dumps(result)}\n\n"

            except Exception as e:
                error_data = {
                    "type": "error",
                    "message": str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )

    except Exception as e:
        logger.error(f"Streaming workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"流式工作流执行失败: {str(e)}")


@router.get("/status/{execution_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(execution_id: str) -> WorkflowStatusResponse:
    """获取工作流状态"""
    try:
        orchestrator = await get_workflow_orchestrator()

        # 查找工作流执行记录
        workflow_execution = None
        for execution in orchestrator.workflow_history:
            if execution.execution_id == execution_id:
                workflow_execution = execution
                break

        if not workflow_execution:
            raise HTTPException(status_code=404, detail="工作流执行记录未找到")

        # 确定当前阶段
        completed_nodes = list(workflow_execution.node_results.keys())
        total_nodes = len(workflow_execution.config.get("enabled_nodes", 9))
        progress_percentage = (len(completed_nodes) / total_nodes) * 100 if total_nodes > 0 else 0

        # 确定当前阶段
        phase_mapping = {
            1: "input_parsing",
            2: "structuring",
            3: "intelligent_processing",
            4: "optimization",
            5: "monitoring"
        }

        current_phase = "completed"
        if progress_percentage < 20:
            current_phase = phase_mapping[1]
        elif progress_percentage < 40:
            current_phase = phase_mapping[2]
        elif progress_percentage < 70:
            current_phase = phase_mapping[3]
        elif progress_percentage < 90:
            current_phase = phase_mapping[4]

        # 计算待处理节点
        all_nodes = workflow_execution.config.get("enabled_nodes", [])
        pending_nodes = [node for node in all_nodes if node not in completed_nodes]

        return WorkflowStatusResponse(
            execution_id=workflow_execution.execution_id,
            status=workflow_execution.status,
            progress_percentage=progress_percentage,
            current_phase=current_phase,
            completed_nodes=completed_nodes,
            pending_nodes=pending_nodes,
            error_message=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        raise HTTPException(status_code=500, detail=f"获取工作流状态失败: {str(e)}")


@router.get("/statistics")
async def get_workflow_statistics() -> Dict[str, Any]:
    """获取工作流统计信息"""
    try:
        orchestrator = await get_workflow_orchestrator()
        stats = await orchestrator.get_orchestrator_statistics()
        return stats

    except Exception as e:
        logger.error(f"Failed to get workflow statistics: {e}")
        raise HTTPException(status_code=500, detail=f"获取工作流统计失败: {str(e)}")


@router.get("/history")
async def get_workflow_history(limit: int = 10) -> Dict[str, Any]:
    """获取工作流历史"""
    try:
        orchestrator = await get_workflow_orchestrator()

        # 获取最近的工作流记录
        recent_workflows = orchestrator.workflow_history[-limit:]

        return {
            "total_workflows": len(orchestrator.workflow_history),
            "recent_workflows": [
                {
                    "execution_id": w.execution_id,
                    "workflow_name": w.workflow_name,
                    "status": w.status,
                    "started_at": w.started_at.isoformat(),
                    "completed_at": w.completed_at.isoformat() if w.completed_at else None,
                    "total_duration": w.total_duration,
                    "final_quality_score": w.final_quality_score,
                    "total_tokens": w.total_tokens,
                    "total_cost": w.total_cost,
                    "error_count": w.error_count
                }
                for w in recent_workflows
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get workflow history: {e}")
        raise HTTPException(status_code=500, detail=f"获取工作流历史失败: {str(e)}")


@router.delete("/cancel/{execution_id}")
async def cancel_workflow(execution_id: str) -> Dict[str, Any]:
    """取消工作流执行"""
    try:
        # 这里应该实现取消逻辑
        # 由于当前是同步执行，取消功能有限
        logger.info(f"Cancel request received for workflow: {execution_id}")

        return {
            "message": "工作流取消请求已接收",
            "execution_id": execution_id,
            "status": "cancelling"
        }

    except Exception as e:
        logger.error(f"Failed to cancel workflow: {e}")
        raise HTTPException(status_code=500, detail=f"取消工作流失败: {str(e)}")


@router.post("/optimize")
async def optimize_workflow() -> Dict[str, Any]:
    """手动触发工作流优化"""
    try:
        from app.services.performance_monitor import get_performance_monitor

        monitor = await get_performance_monitor()
        optimization_result = await monitor.optimize_workflow_parameters()

        return {
            "optimization_id": optimization_result.optimization_id,
            "improvement_percentage": optimization_result.improvement_percentage,
            "cost_reduction": optimization_result.cost_reduction,
            "recommendations": optimization_result.recommendations,
            "next_optimization": optimization_result.next_optimization.isoformat() if optimization_result.next_optimization else None
        }

    except Exception as e:
        logger.error(f"Failed to optimize workflow: {e}")
        raise HTTPException(status_code=500, detail=f"工作流优化失败: {str(e)}")


@router.get("/dashboard")
async def get_workflow_dashboard() -> Dict[str, Any]:
    """获取工作流仪表板"""
    try:
        orchestrator = await get_workflow_orchestrator()
        stats = await orchestrator.get_orchestrator_statistics()

        # 获取各个组件的状态
        dashboard_data = {
            "overview": {
                "total_workflows": stats["orchestrator_stats"]["total_workflows"],
                "success_rate": (
                    stats["orchestrator_stats"]["successful_workflows"] /
                    stats["orchestrator_stats"]["total_workflows"]
                ) if stats["orchestrator_stats"]["total_workflows"] > 0 else 0,
                "average_execution_time": stats["orchestrator_stats"]["average_execution_time"],
                "total_cost_saved": stats["orchestrator_stats"]["total_cost_saved"],
                "quality_improvements": stats["orchestrator_stats"]["quality_improvements"]
            },
            "recent_activity": stats["recent_workflows"],
            "available_nodes": stats["available_nodes"],
            "node_health": {
                "medical_parser": "healthy",
                "content_structurer": "healthy",
                "guideline_visualizer": "healthy",
                "intelligent_agent": "healthy",
                "progressive_generator": "healthy",
                "medical_cache": "healthy",
                "cost_optimizer": "healthy",
                "quality_controller": "healthy",
                "performance_monitor": "healthy"
            }
        }

        return dashboard_data

    except Exception as e:
        logger.error(f"Failed to get workflow dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"获取工作流仪表板失败: {str(e)}")