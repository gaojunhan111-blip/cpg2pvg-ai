"""
医学相关数据模式定义
Medical Data Schemas
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

from app.enums.common import AgentType


@dataclass
class MedicalPattern:
    """医学模式"""
    pattern_id: str
    pattern_name: str
    pattern_type: str
    description: str
    keywords: List[str] = field(default_factory=list)

    # 模式属性
    confidence_score: float = 0.0
    relevance_score: float = 0.0
    frequency: int = 0

    # 医学属性
    medical_domain: str = ""
    severity_level: str = ""
    evidence_level: str = ""

    # 元数据
    source_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_validated: Optional[datetime] = None


@dataclass
class ProcessedContent:
    """处理后的内容"""
    content_id: str
    original_hash: str
    content_type: str
    title: str
    summary: str

    # 处理结果
    sections: List[Dict[str, Any]] = field(default_factory=list)
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)

    # 质量指标
    confidence_score: float = 0.0
    completeness_score: float = 0.0
    medical_accuracy: Optional[float] = None
    readability_score: float = 0.0

    # 处理信息
    processing_time: float = 0.0
    token_usage: int = 0
    processing_cost: float = 0.0

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    agent_type: Optional[AgentType] = None


class QualityResult(BaseModel):
    """质量检查结果"""
    overall_score: float
    medical_accuracy: float
    readability_score: float
    completeness_score: float
    coherence_score: float

    # 详细评估
    issues_found: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    # 对比分析
    similarity_score: float
    content_preservation: float
    information_loss: List[str] = Field(default_factory=list)

    # 时间戳
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    evaluation_time: float = 0.0


class WorkflowExecution(BaseModel):
    """工作流执行记录"""
    execution_id: str
    workflow_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"

    # 性能指标
    total_duration: Optional[float] = None
    node_durations: Dict[str, float] = Field(default_factory=dict)

    # 资源使用
    total_tokens: int = 0
    total_cost: float = 0.0
    memory_usage: Optional[float] = None

    # 质量指标
    final_quality_score: Optional[float] = None
    error_count: int = 0
    warning_count: int = 0

    # 节点结果
    node_results: Dict[str, Any] = Field(default_factory=dict)

    # 配置信息
    config: Dict[str, Any] = Field(default_factory=dict)


class PerformanceMetrics(BaseModel):
    """性能指标"""
    timestamp: datetime
    node_name: str
    execution_time: float

    # 资源指标
    cpu_usage: float
    memory_usage: float
    disk_io: float
    network_io: float

    # LLM指标
    tokens_generated: int
    tokens_input: int
    model_cost: float
    api_latency: float

    # 质量指标
    accuracy_score: float
    user_satisfaction: Optional[float] = None


class OptimizationResult(BaseModel):
    """优化结果"""
    optimization_id: str
    timestamp: datetime

    # 优化参数
    parameter_changes: Dict[str, Any]
    old_parameters: Dict[str, Any]

    # 性能对比
    performance_before: float
    performance_after: float
    improvement_percentage: float

    # 成本对比
    cost_before: float
    cost_after: float
    cost_reduction: float

    # 质量对比
    quality_before: float
    quality_after: float

    # 建议
    recommendations: List[str] = Field(default_factory=list)
    next_optimization: Optional[datetime] = None


class CostOptimizationConfig(BaseModel):
    """成本优化配置"""
    target_cost_reduction: float = 0.3
    quality_threshold: float = 0.8
    complexity_threshold: float = 0.7

    # 模型选择策略
    high_quality_models: List[str] = ["gpt-4", "claude-3"]
    medium_quality_models: List[str] = ["gpt-3.5-turbo", "claude-instant"]
    low_quality_models: List[str] = ["gpt-3.5-turbo-instruct"]

    # 优化策略
    enable_token_optimization: bool = True
    enable_model_switching: bool = True
    enable_caching: bool = True

    # 限制条件
    min_quality_requirement: float = 0.7
    max_token_reduction: float = 0.5


class QualityControlConfig(BaseModel):
    """质量控制配置"""
    medical_accuracy_threshold: float = 0.85
    readability_threshold: float = 0.7
    completeness_threshold: float = 0.8

    # 检查项目
    check_medical_accuracy: bool = True
    check_readability: bool = True
    check_completeness: bool = True
    check_coherence: bool = True

    # 自动修复
    enable_auto_correction: bool = False
    max_correction_attempts: int = 2