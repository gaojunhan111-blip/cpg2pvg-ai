"""
Celery任务模块
CPG2PVG-AI System Celery Tasks
"""

from .guideline_tasks import process_guideline_task
from .document_processing_tasks import parse_document_task, process_multimodal_content_task
from .quality_control_tasks import quality_control_task

__all__ = [
    "process_guideline_task",
    "parse_document_task",
    "process_multimodal_content_task",
    "quality_control_task",
]