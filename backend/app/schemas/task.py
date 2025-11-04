"""
任务相关Pydantic模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TaskStatusEnum(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class TaskBase(BaseModel):
    task_type: str = Field(..., min_length=1, max_length=50)
    priority: int = Field(default=0, ge=0, le=10)


class TaskCreate(TaskBase):
    guideline_id: int
    input_data: Optional[Dict[str, Any]] = None
    notify_on_completion: bool = Field(default=True)


class TaskUpdate(BaseModel):
    status: Optional[TaskStatusEnum] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class TaskResponse(TaskBase):
    id: int
    task_id: str
    status: TaskStatusEnum
    guideline_id: int
    input_data: Optional[Dict[str, Any]]
    result_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    execution_time: Optional[float]
    total_tokens_used: int
    total_cost: float
    quality_score: Optional[float]
    accuracy_score: Optional[float]
    retry_count: int
    max_retries: int
    notify_on_completion: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    items: List[TaskResponse]
    total: int
    page: int
    size: int
    pages: int


class TaskProgressBase(BaseModel):
    step_name: str = Field(..., min_length=1, max_length=100)
    status: str = Field(..., pattern="^(running|completed|failed)$")
    progress_percentage: int = Field(default=0, ge=0, le=100)
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TaskProgressResponse(TaskProgressBase):
    id: int
    task_id: str
    execution_time: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskProgressUpdate(BaseModel):
    task_id: str
    status: TaskStatusEnum
    progress_percentage: int
    current_step: Optional[str] = None
    message: Optional[str] = None
    recent_updates: List[TaskProgressResponse] = []
    estimated_completion: Optional[str] = None