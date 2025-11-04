"""
指南相关Pydantic模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class GuidelineStatusEnum(str, Enum):
    uploaded = "uploaded"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class GuidelineBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    processing_mode: str = Field(default="slow", pattern="^(slow|fast)$")
    is_public: bool = Field(default=False)


class GuidelineCreate(GuidelineBase):
    original_filename: str
    file_size: int
    file_type: str
    file_hash: str
    uploaded_by: str


class GuidelineUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    is_public: Optional[bool] = None


class GuidelineResponse(GuidelineBase):
    id: int
    original_filename: str
    file_size: int
    file_type: str
    file_hash: str
    status: GuidelineStatusEnum
    processed_content: Optional[str]
    processing_metadata: Optional[Dict[str, Any]]
    quality_score: Optional[int]
    accuracy_score: Optional[int]
    uploaded_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GuidelineListResponse(BaseModel):
    items: List[GuidelineResponse]
    total: int
    page: int
    size: int
    pages: int


class UploadResponse(BaseModel):
    task_id: str
    guideline_id: int
    status: str
    message: str