"""
指南处理任务
Guideline Processing Tasks for Celery
"""

import asyncio
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from celery import current_task
from celery.app.task import Task

from app.core.celery_app import celery_app
from app.core.logger import get_logger
from app.core.enhanced_logger import get_enhanced_logger
from app.services.slow_workflow_orchestrator import get_slow_workflow_orchestrator, WorkflowConfig
from app.core.config import get_settings

logger = get_logger(__name__)
enhanced_logger = get_enhanced_logger(__name__)
settings = get_settings()


class ProgressUpdater:
    """进度更新器"""

    def __init__(self, task: Task):
        self.task = task
        self.logger = get_enhanced_logger(f"task_{task.request.id}")

    async def update_progress(self, progress) -> None:
        """更新任务进度到Celery后端"""
        try:
            # 更新Celery任务状态
            self.task.update_state(
                state='PROGRESS',
                meta={
                    'current': progress.progress_percentage,
                    'total': 100,
                    'status': progress.status.value,
                    'phase': progress.current_phase,
                    'current_node': progress.current_node,
                    'completed_nodes': progress.completed_nodes,
                    'error_message': progress.error_message,
                    'estimated_completion': progress.estimated_completion.isoformat() if progress.estimated_completion else None
                }
            )

            # 记录详细日志
            self.logger.info(f"Progress updated: {progress.progress_percentage}% - {progress.current_phase}",
                           extra_data={
                               "task_id": self.task.request.id,
                               "progress": progress.to_dict()
                           })

        except Exception as e:
            self.logger.error(f"Failed to update progress: {e}")

    def update_progress_sync(self, progress) -> None:
        """同步更新进度（用于从同步上下文调用）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.update_progress(progress))
            loop.close()
        except Exception as e:
            logger.error(f"Failed to update progress synchronously: {e}")


@celery_app.task(bind=True, name="app.tasks.guideline_tasks.process_guideline_task")
def process_guideline_task(self, guideline_id: str, file_path: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    异步处理指南的Celery任务

    Args:
        guideline_id: 指南ID
        file_path: 文件路径
        config: 工作流配置

    Returns:
        Dict[str, Any]: 处理结果
    """
    task_id = self.request.id
    start_time = datetime.utcnow()

    logger.info(f"Starting guideline processing task: {task_id} for guideline: {guideline_id}")
    enhanced_logger.info(f"Task started", extra_data={
        "task_id": task_id,
        "guideline_id": guideline_id,
        "file_path": file_path
    })

    try:
        # 更新任务状态为处理中
        self.update_state(
            state='PROCESSING',
            meta={'stage': 'initialization', 'message': '正在初始化工作流...'}
        )

        # 创建工作流配置
        workflow_config = WorkflowConfig()
        if config:
            for key, value in config.items():
                if hasattr(workflow_config, key):
                    setattr(workflow_config, key, value)

        # 获取工作流编排器
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            orchestrator = loop.run_until_complete(get_slow_workflow_orchestrator(workflow_config))
            progress_updater = ProgressUpdater(self)

            # 执行工作流
            result = loop.run_until_complete(
                orchestrator.process_guideline(
                    guideline_id=guideline_id,
                    file_path=file_path,
                    progress_callback=progress_updater.update_progress
                )
            )

            # 准备返回结果
            result_dict = result.to_dict()

            # 添加任务相关信息
            result_dict.update({
                "celery_task_id": task_id,
                "processing_start_time": start_time.isoformat(),
                "processing_end_time": datetime.utcnow().isoformat(),
                "worker_hostname": self.request.hostname,
            })

            # 更新最终状态
            self.update_state(
                state='SUCCESS',
                meta=result_dict
            )

            logger.info(f"Guideline processing task completed successfully: {task_id}")
            enhanced_logger.info(f"Task completed successfully", extra_data={
                "task_id": task_id,
                "processing_time": result.processing_time,
                "quality_score": result.quality_score,
                "total_cost": result.total_cost
            })

            return result_dict

        finally:
            loop.close()

    except Exception as e:
        error_msg = str(e)
        error_traceback = f"Task failed with error: {error_msg}"

        logger.error(f"Guideline processing task failed: {task_id}, error: {e}")
        enhanced_logger.error(f"Task failed", extra_data={
            "task_id": task_id,
            "error": error_msg,
            "guideline_id": guideline_id
        })

        # 更新任务状态为失败
        self.update_state(
            state='FAILURE',
            meta={
                'error': error_msg,
                'error_type': type(e).__name__,
                'stage': 'workflow_execution',
                'guideline_id': guideline_id,
                'processing_start_time': start_time.isoformat(),
                'failure_time': datetime.utcnow().isoformat()
            }
        )

        # 重新抛出异常以触发Celery的重试机制
        raise


@celery_app.task(bind=True, name="app.tasks.guideline_tasks.batch_process_guidelines")
def batch_process_guidelines(self, guideline_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    批量处理多个指南

    Args:
        guideline_configs: 指南配置列表，每个配置包含guideline_id和file_path

    Returns:
        List[Dict[str, Any]]: 批量处理结果
    """
    batch_id = str(uuid.uuid4())
    task_id = self.request.id

    logger.info(f"Starting batch processing task: {task_id}, batch_id: {batch_id}")
    logger.info(f"Batch size: {len(guideline_configs)} guidelines")

    try:
        # 更新批量处理状态
        self.update_state(
            state='BATCH_PROCESSING',
            meta={
                'batch_id': batch_id,
                'total_guidelines': len(guideline_configs),
                'completed_guidelines': 0,
                'failed_guidelines': 0,
                'current_guideline': None
            }
        )

        results = []
        completed_count = 0
        failed_count = 0

        # 处理每个指南
        for i, config in enumerate(guideline_configs):
            guideline_id = config.get('guideline_id')
            file_path = config.get('file_path')

            if not guideline_id or not file_path:
                error_result = {
                    'guideline_id': guideline_id or 'unknown',
                    'status': 'FAILED',
                    'error': 'Missing guideline_id or file_path',
                    'processing_time': 0.0
                }
                results.append(error_result)
                failed_count += 1
                continue

            try:
                # 更新当前处理状态
                self.update_state(
                    state='BATCH_PROCESSING',
                    meta={
                        'batch_id': batch_id,
                        'total_guidelines': len(guideline_configs),
                        'completed_guidelines': completed_count,
                        'failed_guidelines': failed_count,
                        'current_guideline': guideline_id,
                        'progress_percentage': (i / len(guideline_configs)) * 100
                    }
                )

                logger.info(f"Processing guideline {i+1}/{len(guideline_configs)}: {guideline_id}")

                # 创建子任务处理单个指南
                from celery import group
                from . import process_guideline_task

                # 使用group并行处理（可选：串行处理以控制资源使用）
                task_result = process_guideline_task.delay(
                    guideline_id=guideline_id,
                    file_path=file_path,
                    config=config.get('config')
                )

                # 等待任务完成
                result = task_result.get(timeout=3600)  # 1小时超时

                results.append(result)
                completed_count += 1

                logger.info(f"Completed guideline {i+1}/{len(guideline_configs)}: {guideline_id}")

            except Exception as e:
                error_result = {
                    'guideline_id': guideline_id,
                    'status': 'FAILED',
                    'error': str(e),
                    'processing_time': 0.0,
                    'celery_task_id': task_result.id if 'task_result' in locals() else None
                }
                results.append(error_result)
                failed_count += 1

                logger.error(f"Failed to process guideline: {guideline_id}, error: {e}")

        # 计算批量处理统计
        total_processing_time = sum(r.get('processing_time', 0.0) for r in results)
        total_cost = sum(r.get('total_cost', 0.0) for r in results if r.get('total_cost'))
        total_tokens = sum(r.get('tokens_used', 0) for r in results if r.get('tokens_used'))

        batch_result = {
            'batch_id': batch_id,
            'celery_task_id': task_id,
            'total_guidelines': len(guideline_configs),
            'completed_guidelines': completed_count,
            'failed_guidelines': failed_count,
            'success_rate': completed_count / len(guideline_configs) if guideline_configs else 0,
            'total_processing_time': total_processing_time,
            'total_cost': total_cost,
            'total_tokens': total_tokens,
            'results': results,
            'worker_hostname': self.request.hostname,
            'start_time': start_time.isoformat() if 'start_time' in locals() else datetime.utcnow().isoformat(),
            'end_time': datetime.utcnow().isoformat()
        }

        # 更新最终状态
        final_state = 'SUCCESS' if failed_count == 0 else 'PARTIAL_SUCCESS' if completed_count > 0 else 'FAILURE'
        self.update_state(
            state=final_state,
            meta=batch_result
        )

        logger.info(f"Batch processing completed: {task_id}")
        logger.info(f"Success rate: {batch_result['success_rate']:.2%} ({completed_count}/{len(guideline_configs)})")

        return batch_result

    except Exception as e:
        error_msg = f"Batch processing failed: {str(e)}"
        logger.error(f"Batch processing task failed: {task_id}, error: {e}")

        self.update_state(
            state='FAILURE',
            meta={
                'batch_id': batch_id,
                'error': error_msg,
                'total_guidelines': len(guideline_configs),
                'completed_guidelines': completed_count if 'completed_count' in locals() else 0,
                'failed_guidelines': failed_count if 'failed_count' in locals() else 0
            }
        )

        raise


@celery_app.task(bind=True, name="app.tasks.guideline_tasks.retry_failed_task")
def retry_failed_task(self, task_id: str, original_guideline_id: str, original_file_path: str) -> Dict[str, Any]:
    """
    重试失败的任务

    Args:
        task_id: 原始任务ID
        original_guideline_id: 原始指南ID
        original_file_path: 原始文件路径

    Returns:
        Dict[str, Any]: 重试结果
    """
    retry_id = self.request.id

    logger.info(f"Starting retry task: {retry_id} for original task: {task_id}")
    logger.info(f"Retrying processing of guideline: {original_guideline_id}")

    try:
        # 检查原始文件是否仍然存在
        if not os.path.exists(original_file_path):
            raise FileNotFoundError(f"Original file not found: {original_file_path}")

        # 重新执行处理任务
        result = process_guideline_task.apply_async(
            args=[original_guideline_id, original_file_path],
            kwargs={'config': {'enable_auto_retry': True, 'max_retry_attempts': 2}},
            queue='high_priority'
        ).get()

        # 添加重试信息
        result['retry_info'] = {
            'original_task_id': task_id,
            'retry_task_id': retry_id,
            'retry_timestamp': datetime.utcnow().isoformat(),
            'worker_hostname': self.request.hostname
        }

        logger.info(f"Retry task completed successfully: {retry_id}")
        return result

    except Exception as e:
        logger.error(f"Retry task failed: {retry_id}, error: {e}")

        self.update_state(
            state='FAILURE',
            meta={
                'original_task_id': task_id,
                'retry_task_id': retry_id,
                'error': str(e),
                'guideline_id': original_guideline_id
            }
        )

        raise


@celery_app.task(bind=True, name="app.tasks.guideline_task.process_guideline_with_priority")
def process_guideline_with_priority(self, guideline_id: str, file_path: str, priority: int = 5, **kwargs) -> Dict[str, Any]:
    """
    带优先级的指南处理任务

    Args:
        guideline_id: 指南ID
        file_path: 文件路径
        priority: 任务优先级（1-10，1为最高）
        **kwargs: 其他配置参数

    Returns:
        Dict[str, Any]: 处理结果
    """
    # 设置任务优先级
    self.request.delivery_info['priority'] = priority

    logger.info(f"Starting high priority guideline processing: {guideline_id}, priority: {priority}")

    # 调用标准处理任务
    return process_guideline_task.apply_async(
        args=[guideline_id, file_path],
        kwargs=kwargs,
        queue='high_priority',
        priority=priority
    ).get()