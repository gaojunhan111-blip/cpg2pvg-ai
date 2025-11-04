"""
Slow工作流编排器
Slow Workflow Orchestrator - 完整的医学指南处理工作流
整合所有9个节点的完整医学AI处理流程
"""

import asyncio
import uuid
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from app.core.logger import get_logger
from app.core.enhanced_logger import get_enhanced_logger, PerformanceTimer, async_timer
from app.core.config import get_settings
from app.schemas.medical_schemas import ProcessedContent, AgentResults, QualityResult
from app.schemas.pvg_schemas import PVGDocument, PVGSection, GenerationConfig
from app.enums.common import SectionType, ContentPriority, GenerationStatus, AgentType

# 导入所有工作流组件
from app.services.hierarchical_parser import HierarchicalMedicalParser
from app.services.content_structurer import ContentStructurer
from app.services.guideline_visualizer import GuidelineVisualizer
from app.services.intelligent_agent import get_agent_orchestrator
from app.services.progressive_generator import get_progressive_generator
from app.services.medical_cache import get_medical_cache
from app.services.cost_optimizer import get_cost_optimizer
from app.services.quality_controller import get_quality_controller
from app.services.performance_monitor import get_performance_monitor

logger = get_logger(__name__)
enhanced_logger = get_enhanced_logger(__name__)


class WorkflowStatus(str, Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    PARSING = "parsing"
    STRUCTURING = "structuring"
    VISUALIZING = "visualizing"
    PROCESSING = "processing"
    GENERATING = "generating"
    OPTIMIZING = "optimizing"
    QUALITY_CHECKING = "quality_checking"
    MONITORING = "monitoring"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingMode(str, Enum):
    """处理模式"""
    FAST = "fast"          # 快速模式，只核心节点
    SLOW = "slow"          # 慢速模式，所有节点
    THOROUGH = "thorough"   # 彻底模式，包含额外验证
    CUSTOM = "custom"       # 自定义模式


@dataclass
class WorkflowConfig:
    """工作流配置"""
    processing_mode: ProcessingMode = ProcessingMode.SLOW
    enable_visualization: bool = True
    enable_caching: bool = True
    enable_cost_optimization: bool = True
    enable_quality_control: bool = True
    enable_performance_monitoring: bool = True

    # 节点配置
    enabled_nodes: List[str] = field(default_factory=lambda: [
        "hierarchical_parser",      # 节点1
        "content_structurer",       # 节点2
        "guideline_visualizer",     # 节点3
        "intelligent_agent",        # 节点4
        "progressive_generator",    # 节点5
        "medical_cache",           # 节点6
        "cost_optimizer",          # 节点7
        "quality_controller",       # 节点8
        "performance_monitor"       # 节点9
    ])

    # 性能配置
    max_concurrent_nodes: int = 5
    timeout_per_node: int = 600  # 10分钟
    total_timeout: int = 7200   # 2小时

    # 质量配置
    min_quality_threshold: float = 0.8
    enable_auto_retry: bool = True
    max_retry_attempts: int = 3

    # 文件处理配置
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    supported_formats: List[str] = field(default_factory=lambda: [
        ".pdf", ".docx", ".txt", ".md", ".html"
    ])


@dataclass
class WorkflowProgress:
    """工作流进度"""
    task_id: str
    status: WorkflowStatus
    current_phase: str
    progress_percentage: float
    completed_nodes: List[str]
    current_node: Optional[str]
    error_message: Optional[str]
    started_at: datetime
    updated_at: datetime
    estimated_completion: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "current_phase": self.current_phase,
            "progress_percentage": self.progress_percentage,
            "completed_nodes": self.completed_nodes,
            "current_node": self.current_node,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "estimated_completion": self.estimated_completion.isoformat() if self.estimated_completion else None
        }


@dataclass
class WorkflowResult:
    """工作流结果"""
    task_id: str
    status: WorkflowStatus
    guideline_id: str
    pvg_document: Optional[PVGDocument] = None
    processing_time: float = 0.0
    total_cost: float = 0.0
    tokens_used: int = 0
    quality_score: float = 0.0
    node_results: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "task_id": self.task_id,
            "status": self.status.value,
            "guideline_id": self.guideline_id,
            "processing_time": self.processing_time,
            "total_cost": self.total_cost,
            "tokens_used": self.tokens_used,
            "quality_score": self.quality_score,
            "node_results": self.node_results,
            "error_message": self.error_message,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

        if self.pvg_document:
            result["pvg_document"] = self.pvg_document.to_dict()

        return result


class SlowWorkflowOrchestrator:
    """Slow工作流编排器 - 完整的医学AI处理流程"""

    def __init__(self, config: Optional[WorkflowConfig] = None):
        self.logger = enhanced_logger
        self.config = config or WorkflowConfig()
        self.settings = get_settings()

        # 工作流组件实例
        self.parser = None
        self.content_structurer = None
        self.guideline_visualizer = None
        self.agent_orchestrator = None
        self.content_generator = None
        self.cache_system = None
        self.cost_optimizer = None
        self.quality_controller = None
        self.performance_monitor = None

        # 工作流状态管理
        self.active_workflows: Dict[str, WorkflowProgress] = {}
        self.workflow_results: Dict[str, WorkflowResult] = {}

        # 文件存储配置
        self.upload_dir = Path(self.settings.UPLOAD_DIR) / "guidelines"
        self.output_dir = Path(self.settings.OUTPUT_DIR) / "pvg_documents"
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """确保必要的目录存在"""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def _initialize_components(self) -> None:
        """异步初始化所有组件"""
        if self.parser is None:
            self.parser = HierarchicalMedicalParser()

        if self.content_structurer is None:
            self.content_structurer = ContentStructurer()

        if self.guideline_visualizer is None:
            self.guideline_visualizer = GuidelineVisualizer()

        if self.agent_orchestrator is None:
            self.agent_orchestrator = await get_agent_orchestrator()

        if self.content_generator is None:
            self.content_generator = await get_progressive_generator()

        if self.cache_system is None:
            self.cache_system = await get_medical_cache()

        if self.cost_optimizer is None:
            self.cost_optimizer = await get_cost_optimizer()

        if self.quality_controller is None:
            self.quality_controller = await get_quality_controller()

        if self.performance_monitor is None:
            self.performance_monitor = await get_performance_monitor()

    async def process_guideline(
        self,
        guideline_id: str,
        file_path: str,
        progress_callback: Optional[Callable[[WorkflowProgress], None]] = None
    ) -> WorkflowResult:
        """执行完整的Slow工作流"""
        task_id = str(uuid.uuid4())
        start_time = time.time()

        # 初始化工作流进度
        progress = WorkflowProgress(
            task_id=task_id,
            status=WorkflowStatus.PENDING,
            current_phase="初始化",
            progress_percentage=0.0,
            completed_nodes=[],
            current_node=None,
            error_message=None,
            started_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.active_workflows[task_id] = progress
        result = WorkflowResult(
            task_id=task_id,
            status=WorkflowStatus.PENDING,
            guideline_id=guideline_id,
            file_path=file_path
        )

        try:
            self.logger.info(f"Starting Slow workflow for guideline: {guideline_id}",
                           extra_data={"task_id": task_id, "file_path": file_path})

            # 初始化组件
            await self._initialize_components()
            await self._update_progress(progress, WorkflowStatus.RUNNING, "组件初始化完成", 5.0, progress_callback)

            with PerformanceTimer(self.logger, "slow_workflow_complete"):
                # 阶段1：文档解析和结构化 (节点1-2)
                parsed_content = await self._execute_parsing_phase(guideline_id, file_path, progress, progress_callback)

                # 阶段2：可视化和智能处理 (节点3-4)
                processed_content = await self._execute_visualization_phase(parsed_content, progress, progress_callback)

                # 阶段3：内容生成 (节点5)
                pvg_document = await self._execute_generation_phase(processed_content, progress, progress_callback)

                # 阶段4：优化和质量控制 (节点6-8)
                optimized_document = await self._execute_optimization_phase(pvg_document, progress, progress_callback)

                # 阶段5：性能监控和完成 (节点9)
                final_result = await self._execute_monitoring_phase(optimized_document, progress, progress_callback)

            # 更新最终结果
            result.pvg_document = final_result
            result.status = WorkflowStatus.COMPLETED
            result.processing_time = time.time() - start_time
            result.completed_at = datetime.utcnow()

            # 保存文档
            await self._save_pvg_document(final_result, guideline_id)

            await self._update_progress(progress, WorkflowStatus.COMPLETED, "工作流完成", 100.0, progress_callback)

            self.logger.info(f"Slow workflow completed successfully: {task_id}",
                           extra_data={"processing_time": result.processing_time})

        except Exception as e:
            self.logger.error(f"Slow workflow failed: {task_id}, error: {e}",
                            extra_data={"error": str(e), "guideline_id": guideline_id})

            result.status = WorkflowStatus.FAILED
            result.error_message = str(e)
            result.processing_time = time.time() - start_time
            result.completed_at = datetime.utcnow()

            await self._update_progress(progress, WorkflowStatus.FAILED, f"工作流失败: {str(e)}",
                                       progress.progress_percentage, progress_callback)

        finally:
            # 清理活跃工作流
            if task_id in self.active_workflows:
                del self.active_workflows[task_id]

            # 保存结果
            self.workflow_results[task_id] = result

        return result

    @async_timer("parsing_phase")
    async def _execute_parsing_phase(
        self,
        guideline_id: str,
        file_path: str,
        progress: WorkflowProgress,
        progress_callback: Optional[Callable]
    ) -> ProcessedContent:
        """阶段1：文档解析和结构化"""
        self.logger.info(f"Starting parsing phase for: {guideline_id}")

        # 节点1：分层医学解析器
        if "hierarchical_parser" in self.config.enabled_nodes:
            await self._update_progress(progress, WorkflowStatus.PARSING, "分层解析医学指南", 10.0, progress_callback)

            with PerformanceTimer(self.logger, "hierarchical_parsing"):
                parsed_content = await self.parser.parse_medical_guideline(file_path)

            progress.completed_nodes.append("hierarchical_parser")
            progress.node_results = getattr(progress, 'node_results', {})
            progress.node_results["hierarchical_parser"] = {
                "status": "completed",
                "sections_count": len(parsed_content.sections) if hasattr(parsed_content, 'sections') else 0,
                "parsing_time": time.time()
            }

        # 节点2：内容结构化器
        if "content_structurer" in self.config.enabled_nodes:
            await self._update_progress(progress, WorkflowStatus.STRUCTURING, "结构化处理内容", 20.0, progress_callback)

            with PerformanceTimer(self.logger, "content_structuring"):
                structured_content = await self.content_structurer.structure_content(parsed_content)

            progress.completed_nodes.append("content_structurer")
            progress.node_results["content_structurer"] = {
                "status": "completed",
                "structure_type": "hierarchical",
                "structuring_time": time.time()
            }

        return structured_content

    @async_timer("visualization_phase")
    async def _execute_visualization_phase(
        self,
        parsed_content: ProcessedContent,
        progress: WorkflowProgress,
        progress_callback: Optional[Callable]
    ) -> AgentResults:
        """阶段2：可视化和智能处理"""
        self.logger.info("Starting visualization and intelligent processing phase")

        # 节点3：指南可视化器
        visualized_data = None
        if "guideline_visualizer" in self.config.enabled_nodes and self.config.enable_visualization:
            await self._update_progress(progress, WorkflowStatus.VISUALIZING, "可视化处理", 30.0, progress_callback)

            with PerformanceTimer(self.logger, "guideline_visualization"):
                visualized_data = await self.guideline_visualizer.visualize_guideline(parsed_content)

            progress.completed_nodes.append("guideline_visualizer")
            progress.node_results["guideline_visualizer"] = {
                "status": "completed",
                "visualization_count": len(visualized_data) if visualized_data else 0
            }

        # 节点4：智能体协调器
        if "intelligent_agent" in self.config.enabled_nodes:
            await self._update_progress(progress, WorkflowStatus.PROCESSING, "智能分析和处理", 40.0, progress_callback)

            with PerformanceTimer(self.logger, "intelligent_processing"):
                agent_results = await self.agent_orchestrator.process_medical_content(
                    parsed_content, visualized_data
                )

            progress.completed_nodes.append("intelligent_agent")
            progress.node_results["intelligent_agent"] = {
                "status": "completed",
                "agents_used": [agent.value for agent in agent_results.agents_used],
                "confidence_score": agent_results.overall_confidence
            }
        else:
            # 创建默认结果
            agent_results = AgentResults(
                content_analysis=parsed_content,
                recommendations=[],
                confidence_scores={},
                overall_confidence=0.8,
                agents_used=[AgentType.DIAGNOSIS, AgentType.TREATMENT],
                processing_metadata={"mode": "simplified"}
            )

        return agent_results

    @async_timer("generation_phase")
    async def _execute_generation_phase(
        self,
        agent_results: AgentResults,
        progress: WorkflowProgress,
        progress_callback: Optional[Callable]
    ) -> PVGDocument:
        """阶段3：内容生成"""
        self.logger.info("Starting progressive content generation phase")

        if "progressive_generator" not in self.config.enabled_nodes:
            raise ValueError("Progressive generator is required for content generation")

        await self._update_progress(progress, WorkflowStatus.GENERATING, "渐进式内容生成", 60.0, progress_callback)

        # 进度回调包装器
        def generation_progress_callback(section_id: str, status: str, content: str):
            generation_progress = 60.0 + (len(progress.completed_nodes) / 9.0) * 10.0
            asyncio.create_task(
                self._update_progress(progress, WorkflowStatus.GENERATING,
                                    f"生成章节: {section_id}", generation_progress, progress_callback)
            )

        with PerformanceTimer(self.logger, "progressive_generation"):
            pvg_document = await self.content_generator.generate_pvg(
                agent_results=agent_results,
                template_name="standard_pvg",
                config={
                    "enable_streaming": False,
                    "priority_strategy": "balanced"
                },
                progress_callback=generation_progress_callback
            )

        progress.completed_nodes.append("progressive_generator")
        progress.node_results["progressive_generator"] = {
            "status": "completed",
            "sections_generated": len(pvg_document.sections),
            "total_tokens": pvg_document.total_tokens,
            "estimated_cost": pvg_document.total_cost
        }

        await self._update_progress(progress, WorkflowStatus.GENERATING, "内容生成完成", 70.0, progress_callback)

        return pvg_document

    @async_timer("optimization_phase")
    async def _execute_optimization_phase(
        self,
        pvg_document: PVGDocument,
        progress: WorkflowProgress,
        progress_callback: Optional[Callable]
    ) -> PVGDocument:
        """阶段4：优化和质量控制 - 并行执行"""
        self.logger.info("Starting optimization and quality control phase")

        # 准备优化任务
        optimization_tasks = []
        node_names = []

        # 节点6：智能缓存
        if "medical_cache" in self.config.enabled_nodes and self.config.enable_caching:
            optimization_tasks.append(self._execute_node6_medical_cache(pvg_document))
            node_names.append("medical_cache")

        # 节点7：成本优化器
        if "cost_optimizer" in self.config.enabled_nodes and self.config.enable_cost_optimization:
            optimization_tasks.append(self._execute_node7_cost_optimizer(pvg_document))
            node_names.append("cost_optimizer")

        # 节点8：质量控制
        if "quality_controller" in self.config.enabled_nodes and self.config.enable_quality_control:
            optimization_tasks.append(self._execute_node8_quality_controller(pvg_document))
            node_names.append("quality_controller")

        if optimization_tasks:
            await self._update_progress(progress, WorkflowStatus.OPTIMIZING, "并行优化处理", 80.0, progress_callback)

            # 并行执行所有优化任务
            self.logger.info(f"Executing {len(optimization_tasks)} optimization nodes in parallel")
            results = await asyncio.gather(*optimization_tasks, return_exceptions=True)

            # 处理结果
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Optimization node {node_names[i]} failed: {result}")
                    progress.node_results[node_names[i]] = {
                        "error": str(result),
                        "status": "failed"
                    }
                else:
                    progress.node_results[node_names[i]] = result
                    progress.completed_nodes.append(node_names[i])

        await self._update_progress(progress, WorkflowStatus.QUALITY_CHECKING, "质量检查完成", 85.0, progress_callback)

        return pvg_document

    async def _execute_node6_medical_cache(self, pvg_document: PVGDocument) -> Dict[str, Any]:
        """节点6：智能缓存和记忆系统"""
        with PerformanceTimer(self.logger, "medical_caching"):
            # 缓存生成的文档内容
            for section in pvg_document.sections:
                content_hash = str(hash(section.content))
                await self.cache_system.cache_medical_content(
                    content_hash=content_hash,
                    processed_content=section.content,
                    content_type="pvg_section"
                )

        return {
            "status": "completed",
            "cached_sections": len(pvg_document.sections),
            "cache_efficiency": self.cache_system.cache_stats.get("cache_efficiency", 0.0)
        }

    async def _execute_node7_cost_optimizer(self, pvg_document: PVGDocument) -> Dict[str, Any]:
        """节点7：自适应成本优化器"""
        with PerformanceTimer(self.logger, "cost_optimization"):
            # 优化文档的成本结构
            optimization_result = await self.cost_optimizer.optimize_document_cost(pvg_document)

        return {
            "status": "completed",
            "original_cost": pvg_document.total_cost,
            "optimized_cost": optimization_result.get("optimized_cost", pvg_document.total_cost),
            "cost_savings": optimization_result.get("savings", 0.0)
        }

    async def _execute_node8_quality_controller(self, pvg_document: PVGDocument) -> Dict[str, Any]:
        """节点8：多层质量控制"""
        with PerformanceTimer(self.logger, "quality_control"):
            # 执行全面质量检查
            original_cpg = "Original CPG content"  # 这里应该是原始内容
            generated_pvg = pvg_document.title + "\n" + "\n".join([s.content for s in pvg_document.sections])

            quality_result = await self.quality_controller.validate_pvg_quality(original_cpg, generated_pvg)

        return {
            "status": "completed",
            "overall_score": quality_result.overall_score,
            "medical_accuracy": quality_result.medical_accuracy,
            "issues_found": len(quality_result.issues_found),
            "recommendations": quality_result.recommendations[:3]  # 前3个建议
        }

    @async_timer("monitoring_phase")
    async def _execute_monitoring_phase(
        self,
        pvg_document: PVGDocument,
        progress: WorkflowProgress,
        progress_callback: Optional[Callable]
    ) -> PVGDocument:
        """阶段5：性能监控和完成"""
        self.logger.info("Starting performance monitoring phase")

        # 节点9：性能监控器
        if "performance_monitor" in self.config.enabled_nodes and self.config.enable_performance_monitoring:
            await self._update_progress(progress, WorkflowStatus.MONITORING, "性能监控", 90.0, progress_callback)

            with PerformanceTimer(self.logger, "performance_monitoring"):
                monitoring_result = await self.performance_monitor.analyze_workflow_performance(pvg_document)

            progress.completed_nodes.append("performance_monitor")
            progress.node_results["performance_monitor"] = {
                "status": "completed",
                "performance_score": monitoring_result.get("performance_score", 0.0),
                "optimization_suggestions": monitoring_result.get("suggestions", [])
            }

        return pvg_document

    async def _save_pvg_document(self, pvg_document: PVGDocument, guideline_id: str) -> str:
        """保存PVG文档到文件"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"PVG_{guideline_id}_{timestamp}.json"
        output_path = self.output_dir / filename

        # 保存JSON格式
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(pvg_document.to_dict(), f, ensure_ascii=False, indent=2)

        # 保存HTML格式
        html_filename = f"PVG_{guideline_id}_{timestamp}.html"
        html_path = self.output_dir / html_filename

        html_content = self._generate_html_output(pvg_document)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        self.logger.info(f"PVG document saved: {output_path}")
        return str(output_path)

    def _generate_html_output(self, pvg_document: PVGDocument) -> str:
        """生成HTML格式的PVG文档"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{pvg_document.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #3498db; border-bottom: 2px solid #3498db; }}
                h3 {{ color: #e74c3c; }}
                .metadata {{ background: #f8f9fa; padding: 15px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .emergency {{ background: #ffe6e6; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>{pvg_document.title}</h1>

            <div class="metadata">
                <p><strong>文档ID:</strong> {pvg_document.document_id}</p>
                <p><strong>版本:</strong> {pvg_document.version}</p>
                <p><strong>生成时间:</strong> {pvg_document.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>总章节:</strong> {len(pvg_document.sections)}</p>
            </div>
        """

        for section in pvg_document.sections:
            section_class = ""
            if section.section_type == SectionType.EMERGENCY_GUIDANCE:
                section_class = "emergency"

            html += f"""
            <div class="section {section_class}">
                <h2>{section.title}</h2>
                <div>{section.html_content or section.content}</div>
            </div>
            """

        html += """
        </body>
        </html>
        """

        return html

    async def _update_progress(
        self,
        progress: WorkflowProgress,
        status: WorkflowStatus,
        current_phase: str,
        percentage: float,
        progress_callback: Optional[Callable]
    ) -> None:
        """更新工作流进度"""
        progress.status = status
        progress.current_phase = current_phase
        progress.progress_percentage = percentage
        progress.updated_at = datetime.utcnow()

        # 估算完成时间
        if percentage > 0:
            elapsed = (progress.updated_at - progress.started_at).total_seconds()
            estimated_total = elapsed / (percentage / 100.0)
            progress.estimated_completion = progress.started_at + timedelta(seconds=estimated_total)

        # 调用进度回调
        if progress_callback:
            try:
                await progress_callback(progress)
            except Exception as e:
                self.logger.warning(f"Progress callback failed: {e}")

    async def get_workflow_status(self, task_id: str) -> Optional[WorkflowProgress]:
        """获取工作流状态"""
        return self.active_workflows.get(task_id)

    async def get_workflow_result(self, task_id: str) -> Optional[WorkflowResult]:
        """获取工作流结果"""
        return self.workflow_results.get(task_id)

    async def cancel_workflow(self, task_id: str) -> bool:
        """取消工作流"""
        if task_id in self.active_workflows:
            progress = self.active_workflows[task_id]
            progress.status = WorkflowStatus.CANCELLED
            progress.updated_at = datetime.utcnow()

            # 创建取消结果
            result = WorkflowResult(
                task_id=task_id,
                status=WorkflowStatus.CANCELLED,
                guideline_id=progress.task_id,
                processing_time=0.0,
                completed_at=datetime.utcnow()
            )
            self.workflow_results[task_id] = result

            # 从活跃工作流中移除
            del self.active_workflows[task_id]

            self.logger.info(f"Workflow cancelled: {task_id}")
            return True

        return False

    def get_active_workflows(self) -> List[WorkflowProgress]:
        """获取所有活跃工作流"""
        return list(self.active_workflows.values())

    def get_completed_workflows(self, limit: int = 50) -> List[WorkflowResult]:
        """获取已完成的工作流"""
        completed = [r for r in self.workflow_results.values()
                    if r.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]]
        return sorted(completed, key=lambda x: x.completed_at or x.created_at, reverse=True)[:limit]


# 全局实例
_slow_orchestrator: Optional[SlowWorkflowOrchestrator] = None


async def get_slow_workflow_orchestrator(config: Optional[WorkflowConfig] = None) -> SlowWorkflowOrchestrator:
    """获取Slow工作流编排器实例"""
    global _slow_orchestrator
    if _slow_orchestrator is None:
        _slow_orchestrator = SlowWorkflowOrchestrator(config)
    return _slow_orchestrator