"""
Celery应用配置
CPG2PVG-AI System Celery Application
"""

import os
from celery import Celery
from celery.signals import worker_ready, task_failure, task_success
import logging

from app.core.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Celery应用实例
celery_app = Celery(
    "cpg2pvg_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "celery_worker.tasks.guideline_tasks",
        "celery_worker.tasks.document_processing_tasks",
        "celery_worker.tasks.quality_control_tasks",
    ]
)

# Celery配置
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,

    # 任务路由
    task_routes={
        "celery_worker.tasks.guideline_tasks.*": {"queue": "guideline_processing"},
        "celery_worker.tasks.document_processing_tasks.*": {"queue": "document_processing"},
        "celery_worker.tasks.quality_control_tasks.*": {"queue": "quality_control"},
    },

    # 任务优先级
    task_inherit_parent_priority=True,
    task_default_priority=5,
    worker_prefetch_multiplier=1,

    # 任务重试配置
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_max_retries=3,
    task_default_retry_delay=60,  # 60秒

    # 结果过期时间
    result_expires=3600,  # 1小时

    # 工作进程配置
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,

    # 监控
    worker_send_task_events=True,
    task_send_sent_event=True,

    # 任务时间限制
    task_soft_time_limit=1800,  # 30分钟软限制
    task_time_limit=2100,       # 35分钟硬限制
)

# 任务失败处理
@task_failure.connect
def task_failure_handler(sender, task_id, exception, args, kwargs, traceback, einfo, **kwds):
    """任务失败处理"""
    logger.error(
        f"Task {sender.name} failed: {task_id} - {exception}"
    )
    logger.error(f"Traceback: {traceback}")

# 任务成功处理
@task_success.connect
def task_success_handler(sender, result, args, kwargs, **kwds):
    """任务成功处理"""
    logger.info(
        f"Task {sender.name} completed successfully"
    )

# 工作进程启动处理
@worker_ready.connect
def worker_ready_handler(sender=None, **kwds):
    """工作进程启动处理"""
    logger.info("Celery worker is ready to process tasks")

# 健康检查任务
@celery_app.task(bind=True, name="health_check")
def health_check(self):
    """健康检查任务"""
    return {"status": "healthy", "worker": os.getpid()}

# 定期任务配置
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # 清理过期任务结果
    'cleanup-expired-results': {
        'task': 'celery_worker.tasks.cleanup_tasks.cleanup_expired_results',
        'schedule': crontab(minute=0, hour='*/6'),  # 每6小时执行一次
    },
    # 系统性能监控
    'system-performance-monitor': {
        'task': 'celery_worker.tasks.monitoring_tasks.system_performance_check',
        'schedule': crontab(minute='*/5'),  # 每5分钟执行一次
    },
}

if __name__ == "__main__":
    celery_app.start()