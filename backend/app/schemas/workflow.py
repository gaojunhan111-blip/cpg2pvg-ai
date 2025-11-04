"""
工作流相关的Pydantic模型
Workflow Related Pydantic Models
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class WorkflowUploadRequest(BaseModel):
    """工作流上传请求"""
    title: str = Field(..., description="文档标题")
    description: Optional[str] = Field(None, description="文档描述")
    processing_mode: str = Field("slow", description="处理模式: slow/fast/thorough")
    priority: str = Field("normal", description="任务优先级: low/normal/high/urgent")
    enable_visualization: bool = Field(True, description="启用可视化")
    enable_caching: bool = Field(True, description="启用缓存")
    enable_cost_optimization: bool = Field(True, description="启用成本优化")
    enable_quality_control: bool = Field(True, description="启用质量控制")
    custom_config: Optional[Dict[str, Any]] = Field(None, description="自定义配置")
    tags: Optional[List[str]] = Field(None, description="标签")


class WorkflowUploadResponse(BaseModel):
    """工作流上传响应"""
    task_id: str
    guideline_id: str
    celery_task_id: str
    status: str
    message: str
    upload_time: datetime
    estimated_processing_time: int


class WorkflowStatusResponse(BaseModel):
    """工作流状态响应"""
    task_id: str
    guideline_id: str
    status: str
    current_phase: str
    progress_percentage: float
    current_node: Optional[str]
    completed_nodes: List[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_completion: Optional[datetime]
    processing_time: float
    total_cost: float
    tokens_used: int
    quality_score: Optional[float]
    error_message: Optional[str]
    retry_count: int
    output_files: List[str]
    worker_hostname: Optional[str]
    node_results: Dict[str, Any]


class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: List[Dict[str, Any]]
    total_count: int
    limit: int
    offset: int


class UploadResponse(BaseModel):
    """上传响应"""
    task_id: str
    guideline_id: str
    celery_task_id: str
    status: str
    message: str
    upload_time: datetime
    estimated_processing_time: int


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    celery_task_id: str
    guideline_id: str
    status: str
    progress_percentage: float
    current_phase: str
    current_node: Optional[str]
    completed_nodes: List[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_completion: Optional[datetime]
    processing_time: float
    total_cost: float
    quality_score: Optional[float]
    error_message: Optional[str]
    retry_count: int
    output_files: List[str]
    worker_hostname: Optional[str]


class PVGDownloadResponse(BaseModel):
    """PVG下载响应"""
    file_path: str
    filename: str
    content_type: str
    size: int
    download_url: str