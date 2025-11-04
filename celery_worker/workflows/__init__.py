"""
Celery Worker工作流模块
CPG2PVG-AI System Celery Worker Workflows
"""

from .slow_workflow import SlowWorkflowProcessor
from .fast_workflow import FastWorkflowProcessor

__all__ = ["SlowWorkflowProcessor", "FastWorkflowProcessor"]