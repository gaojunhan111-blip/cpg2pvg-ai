"""
指南处理任务
CPG2PVG-AI System Guideline Processing Tasks
"""

import asyncio
import logging
from typing import Dict, Any
from celery import Task

from celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.task import Task as TaskModel, TaskStatus
from app.models.guideline import Guideline, GuidelineStatus

logger = logging.getLogger(__name__)


class ProcessGuidelineTask(Task):
    """指南处理任务基类"""

    def on_success(self, retval, task_id, args, kwargs):
        """任务成功回调"""
        logger.info(f"Guideline processing task {task_id} completed successfully")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败回调"""
        logger.error(f"Guideline processing task {task_id} failed: {exc}")


@celery_app.task(
    bind=True,
    base=ProcessGuidelineTask,
    name="process_guideline_task",
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=1800,  # 30分钟
    time_limit=2100,       # 35分钟
)
def process_guideline_task(self, guideline_id: int, processing_mode: str = "slow") -> Dict[str, Any]:
    """
    处理指南的主要任务
    启动Slow工作流的所有技术节点
    """
    try:
        # 使用asyncio运行异步代码
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                _process_guideline_async(guideline_id, processing_mode, self.request.id)
            )
            return result
        finally:
            loop.close()

    except Exception as exc:
        logger.error(f"Guideline processing failed: {exc}")

        # 更新任务状态为失败
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                _update_task_status(self.request.id, TaskStatus.FAILED, str(exc))
            )
        finally:
            loop.close()

        # 重试任务
        raise self.retry(exc=exc)


async def _process_guideline_async(
    guideline_id: int,
    processing_mode: str,
    task_id: str
) -> Dict[str, Any]:
    """异步处理指南"""

    async with AsyncSessionLocal() as session:
        # 获取指南信息
        guideline = await session.get(Guideline, guideline_id)
        if not guideline:
            raise ValueError(f"Guideline {guideline_id} not found")

        # 更新指南状态
        guideline.status = GuidelineStatus.PROCESSING
        await session.commit()

        logger.info(f"Starting guideline processing: {guideline.title} (ID: {guideline_id})")

        try:
            if processing_mode == "slow":
                # Slow工作流 - 完整的9个技术节点
                result = await _run_slow_workflow(guideline, task_id)
            else:
                # Fast工作流 - 简化版本
                result = await _run_fast_workflow(guideline, task_id)

            # 更新指南状态和结果
            guideline.status = GuidelineStatus.COMPLETED
            guideline.processed_content = result.get("processed_content")
            guideline.quality_score = result.get("quality_score", 0)
            guideline.accuracy_score = result.get("accuracy_score", 0)

            await session.commit()

            # 更新任务状态
            await _update_task_status(task_id, TaskStatus.COMPLETED)

            logger.info(f"Guideline processing completed: {guideline.title}")

            return {
                "success": True,
                "guideline_id": guideline_id,
                "processed_content": result.get("processed_content"),
                "quality_score": result.get("quality_score"),
                "accuracy_score": result.get("accuracy_score"),
                "processing_time": result.get("processing_time"),
                "total_cost": result.get("total_cost"),
            }

        except Exception as e:
            # 更新指南状态为失败
            guideline.status = GuidelineStatus.FAILED
            await session.commit()

            # 更新任务状态
            await _update_task_status(task_id, TaskStatus.FAILED, str(e))

            raise e


async def _run_slow_workflow(guideline: Guideline, task_id: str) -> Dict[str, Any]:
    """
    运行Slow工作流
    完整保留所有9个技术节点
    """
    from celery_worker.workflows.slow_workflow import SlowWorkflowProcessor

    processor = SlowWorkflowProcessor()
    return await processor.process(guideline, task_id)


async def _run_fast_workflow(guideline: Guideline, task_id: str) -> Dict[str, Any]:
    """
    运行Fast工作流
    简化版本，只包含核心处理节点
    """
    from celery_worker.workflows.fast_workflow import FastWorkflowProcessor

    processor = FastWorkflowProcessor()
    return await processor.process(guideline, task_id)


async def _update_task_status(
    task_id: str,
    status: TaskStatus,
    error_message: str = None
):
    """更新任务状态"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        # 查找任务
        stmt = select(TaskModel).where(TaskModel.task_id == task_id)
        result = await session.execute(stmt)
        task = result.scalar_one_or_none()

        if task:
            task.status = status
            if error_message:
                task.error_message = error_message

            if status == TaskStatus.COMPLETED:
                task.completed_at = str(asyncio.get_event_loop().time())

            await session.commit()