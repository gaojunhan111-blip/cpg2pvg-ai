"""
工作流数据类型定义
CPG2PVG-AI System Workflow Types
"""

from typing import Dict, List, Any, Optional, Union, Callable, AsyncGenerator
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
import uuid


class ProcessingStatus(str, Enum):
    """处理状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class ContentType(str, Enum):
    """内容类型枚举"""
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
    CHART = "chart"
    ALGORITHM = "algorithm"
    REFERENCE = "reference"
    FOOTNOTE = "footnote"
    METADATA = "metadata"


class ProcessingMode(str, Enum):
    """处理模式枚举"""
    SLOW = "slow"
    FAST = "fast"
    CUSTOM = "custom"


class QualityLevel(str, Enum):
    """质量等级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXCELLENT = "excellent"


class CostLevel(str, Enum):
    """成本等级枚举"""
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNLIMITED = "unlimited"


@dataclass
class DocumentSection:
    """文档片段"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content: str = ""
    content_type: ContentType = ContentType.TEXT
    level: int = 0  # 标题级别
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "content_type": self.content_type.value,
            "level": self.level,
            "start_page": self.start_page,
            "end_page": self.end_page,
            "metadata": self.metadata,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
        }


@dataclass
class ProcessingContext:
    """处理上下文"""
    guideline_id: int
    user_id: int
    processing_mode: ProcessingMode
    cost_level: CostLevel
    quality_requirement: QualityLevel
    max_tokens: int = 4000
    temperature: float = 0.7
    language: str = "zh"
    target_audience: str = "general"
    medical_specialties: List[str] = field(default_factory=list)
    evidence_level: str = "standard"

    # 配置参数
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "guideline_id": self.guideline_id,
            "user_id": self.user_id,
            "processing_mode": self.processing_mode.value,
            "cost_level": self.cost_level.value,
            "quality_requirement": self.quality_requirement.value,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "language": self.language,
            "target_audience": self.target_audience,
            "medical_specialties": self.medical_specialties,
            "evidence_level": self.evidence_level,
            "config": self.config,
            "metadata": self.metadata,
        }


@dataclass
class ProcessingResult:
    """处理结果"""
    step_name: str
    status: ProcessingStatus
    success: bool = False
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    token_usage: int = 0
    cost: float = 0.0
    quality_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "step_name": self.step_name,
            "status": self.status.value,
            "success": self.success,
            "data": self.data,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "token_usage": self.token_usage,
            "cost": self.cost,
            "quality_score": self.quality_score,
            "metadata": self.metadata,
        }


@dataclass
class WorkflowMetrics:
    """工作流指标"""
    total_execution_time: float = 0.0
    total_cost: float = 0.0
    total_tokens: int = 0
    step_count: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    average_quality_score: Optional[float] = None
    peak_memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None

    def calculate_completion_rate(self) -> float:
        """计算完成率"""
        if self.step_count == 0:
            return 0.0
        return self.completed_steps / self.step_count

    def calculate_average_step_time(self) -> float:
        """计算平均步骤时间"""
        if self.completed_steps == 0:
            return 0.0
        return self.total_execution_time / self.completed_steps


@dataclass
class WorkflowState:
    """工作流状态"""
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: ProcessingStatus = ProcessingStatus.PENDING
    current_step: Optional[str] = None
    progress: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: List[ProcessingResult] = field(default_factory=list)
    metrics: WorkflowMetrics = field(default_factory=WorkflowMetrics)
    context: Optional[ProcessingContext] = None

    def add_result(self, result: ProcessingResult) -> None:
        """添加处理结果"""
        self.results.append(result)
        self.metrics.total_execution_time += result.execution_time
        self.metrics.total_cost += result.cost
        self.metrics.total_tokens += result.token_usage
        self.metrics.completed_steps += 1

        # 更新平均质量分数
        if result.quality_score is not None:
            if self.metrics.average_quality_score is None:
                self.metrics.average_quality_score = result.quality_score
            else:
                total_score = self.metrics.average_quality_score * (self.metrics.completed_steps - 1) + result.quality_score
                self.metrics.average_quality_score = total_score / self.metrics.completed_steps

    def add_failed_step(self) -> None:
        """添加失败步骤"""
        self.metrics.failed_steps += 1

    def calculate_progress(self) -> None:
        """计算总体进度"""
        total_steps = self.metrics.completed_steps + self.metrics.failed_steps
        if self.metrics.step_count > 0:
            self.progress = total_steps / self.metrics.step_count

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "current_step": self.current_step,
            "progress": self.progress,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "results": [result.to_dict() for result in self.results],
            "metrics": {
                "total_execution_time": self.metrics.total_execution_time,
                "total_cost": self.metrics.total_cost,
                "total_tokens": self.metrics.total_tokens,
                "step_count": self.metrics.step_count,
                "completed_steps": self.metrics.completed_steps,
                "failed_steps": self.metrics.failed_steps,
                "average_quality_score": self.metrics.average_quality_score,
                "completion_rate": self.metrics.calculate_completion_rate(),
                "average_step_time": self.metrics.calculate_average_step_time(),
            }
        }


# 类型别名
ProcessingStep = Callable[[ProcessingContext, Any], AsyncGenerator[ProcessingResult, None]]
StepCallback = Callable[[ProcessingResult], None]