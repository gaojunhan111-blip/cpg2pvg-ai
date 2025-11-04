"""
Celery应用配置
CPG2PVG-AI System Celery Application
"""

import os
from celery import Celery
from celery.signals import worker_ready, worker_failure, task_success, task_failure
from kombu import Queue
import logging

from app.core.config import settings

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
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
        "celery_worker.tasks.cleanup_tasks",
        "celery_worker.tasks.monitoring_tasks",
        # "celery_worker.tasks.notification_tasks",  # 注释掉不存在的模块
    ]
)

# Celery配置
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_expires=settings.REDIS_CACHE_TTL,  # 结果过期时间
    timezone="Asia/Shanghai",
    enable_utc=True,

    # 任务路由配置
    task_routes={
        "celery_worker.tasks.guideline_tasks.*": {"queue": "guideline_processing"},
        "celery_worker.tasks.document_processing_tasks.*": {"queue": "document_processing"},
        "celery_worker.tasks.quality_control_tasks.*": {"queue": "quality_control"},
        "celery_worker.tasks.cleanup_tasks.*": {"queue": "maintenance"},
        "celery_worker.tasks.monitoring_tasks.*": {"queue": "monitoring"},
        # "celery_worker.tasks.notification_tasks.*": {"queue": "notifications"},  # 注释掉不存在的模块
    },

    # 队列定义
    task_queues=(
        Queue('guideline_processing', routing_key='guideline_processing'),
        Queue('document_processing', routing_key='document_processing'),
        Queue('quality_control', routing_key='quality_control'),
        Queue('maintenance', routing_key='maintenance'),
        Queue('monitoring', routing_key='monitoring'),
        Queue('notifications', routing_key='notifications'),
        Queue('default', routing_key='default'),
    ),

    # 任务优先级配置
    task_inherit_parent_priority=True,
    task_default_priority=5,
    worker_prefetch_multiplier=1,

    # 任务重试配置
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_max_retries=3,
    task_default_retry_delay=60,
    task_retry_backoff=True,
    task_retry_backoff_max=700,
    task_retry_jitter=True,

    # 工作进程配置
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    worker_log_color=False,

    # 监控配置
    worker_send_task_events=True,
    task_send_sent_event=True,
    task_send_started_event=True,

    # 结果后端配置
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 3600,
    },

    # 任务时间限制
    task_soft_time_limit=settings.DEFAULT_TASK_TIMEOUT - 60,  # 软限制比硬限制少60秒
    task_time_limit=settings.DEFAULT_TASK_TIMEOUT,
    task_ignore_result=False,

    # Beat调度器配置
    beat_schedule={
        # 清理过期任务结果
        'cleanup-expired-results': {
            'task': 'celery_worker.tasks.cleanup_tasks.cleanup_expired_results',
            'schedule': 3600.0,  # 每小时执行一次
        },
        # 系统性能监控
        'system-performance-monitor': {
            'task': 'celery_worker.tasks.monitoring_tasks.system_performance_check',
            'schedule': 300.0,  # 每5分钟执行一次
        },
        # 数据库统计更新
        'update-database-stats': {
            'task': 'celery_worker.tasks.monitoring_tasks.update_database_stats',
            'schedule': 600.0,  # 每10分钟执行一次
        },
        # 用户使用统计
        'update-user-usage-stats': {
            'task': 'celery_worker.tasks.monitoring_tasks.update_user_stats',
            'schedule': 86400.0,  # 每天执行一次
        },
        # 健康检查
        'health-check': {
            'task': 'celery_worker.tasks.monitoring_tasks.health_check_task',
            'schedule': 60.0,  # 每分钟执行一次
        },
    },

    # 安全配置
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,

    # 性能优化
    worker_proc_alive_timeout=60,
    worker_max_memory_per_child=200000,  # 200MB

)

# 环境特定配置
if settings.DEBUG:
    celery_app.conf.update(
        worker_log_level="DEBUG",
        task_always_eager=False,
    )

# 任务失败处理
@worker_failure.connect
def worker_failure_handler(sender, **kwargs):
    """Worker失败处理"""
    logger.error(f"Worker failed: {sender}")


@task_failure.connect
def task_failure_handler(sender, task_id, exception, args, kwargs, traceback, einfo, **kwds):
    """任务失败处理"""
    logger.error(
        f"Task {sender.name} failed: {task_id} - {exception}"
    )
    logger.error(f"Traceback: {traceback}")

    # 记录失败任务到数据库（可选）
    try:
        import asyncio
        from app.core.database import get_db_session
        from app.models import Task, TaskStatus
        from datetime import datetime

        async def update_task_status():
            async with get_db_session() as session:
                result = await session.execute(
                    "SELECT id FROM tasks WHERE task_id = :task_id",
                    {"task_id": task_id}
                )
                task_db_id = result.scalar_one_or_none()

                if task_db_id:
                    task = await session.get(Task, task_db_id)
                    if task:
                        task.fail_task(str(exception))
                        await session.commit()

        # 在新的事件循环中运行异步函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(update_task_status())
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Failed to update task status in database: {e}")


@task_success.connect
def task_success_handler(sender, result, args, kwargs, **kwds):
    """任务成功处理"""
    logger.info(f"Task {sender.name} completed successfully")


@worker_ready.connect
def worker_ready_handler(sender=None, **kwds):
    """Worker启动处理"""
    logger.info(f"Celery worker {sender.hostname} is ready to process tasks")

    # 记录worker启动事件
    try:
        import asyncio
        from app.core.database import get_db_session

        async def log_worker_start():
            # 这里可以记录worker启动到数据库或日志系统
            pass

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(log_worker_start())
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Failed to log worker start: {e}")


# 健康检查任务
@celery_app.task(name="health_check", bind=True)
def health_check_task(self):
    """健康检查任务"""
    try:
        # 检查各个服务的健康状态
        checks = {
            "worker_id": self.request.id,
            "hostname": self.request.hostname,
            "status": "healthy",
            "timestamp": self.request.now_iso,
        }

        # 检查数据库连接（如果需要）
        # 检查Redis连接
        # 检查其他依赖服务

        return checks
    except Exception as e:
        return {
            "worker_id": self.request.id,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": self.request.now_iso,
        }


# 延迟任务包装器
def create_delayed_task(task_name: str, countdown: int = None, eta=None, **kwargs):
    """创建延迟任务"""
    """
    创建延迟任务的便捷函数

    Args:
        task_name: 任务名称
        countdown: 延迟秒数
        eta: 具体的执行时间
        **kwargs: 任务参数

    Returns:
        AsyncResult
    """
    return celery_app.send_task(
        task_name,
        kwargs=kwargs,
        countdown=countdown,
        eta=eta,
    )


# 批量任务创建器
def create_batch_tasks(task_name: str, args_list: list, **kwargs):
    """创建批量任务"""
    """
    创建批量任务的便捷函数

    Args:
        task_name: 任务名称
        args_list: 参数列表
        **kwargs: 额外的任务选项

    Returns:
        List[AsyncResult]
    """
    from celery import group

    tasks = [celery_app.signature(task_name, args=args) for args in args_list]
    return group(*tasks).apply_async(**kwargs)


# 链式任务创建器
def create_task_chain(*tasks):
    """创建任务链"""
    """
    创建任务链的便捷函数

    Args:
        *tasks: 任务列表

    Returns:
        chain
    """
    from celery import chain

    return chain(*tasks)


# 任务状态查询
def get_task_status(task_id: str):
    """获取任务状态"""
    """
    获取任务状态的便捷函数

    Args:
        task_id: 任务ID

    Returns:
        dict: 任务状态信息
    """
    result = celery_app.AsyncResult(task_id)

    return {
        "task_id": task_id,
        "state": result.state,
        "result": result.result if result.ready() else None,
        "traceback": result.traceback if result.failed() else None,
        "date_done": result.date_done,
    }


# 取消任务
def revoke_task(task_id: str, terminate: bool = False):
    """取消任务"""
    """
    取消任务的便捷函数

    Args:
        task_id: 任务ID
        terminate: 是否强制终止
    """
    celery_app.control.revoke(task_id, terminate=terminate)


# 工作进程管理
def get_active_workers():
    """获取活跃的workers"""
    """
    获取活跃的workers列表

    Returns:
        list: workers信息
    """
    stats = celery_app.control.inspect().stats()
    return stats


def get_active_tasks():
    """获取活跃的任务"""
    """
    获取活跃的任务列表

    Returns:
        list: 任务信息
    """
    active = celery_app.control.inspect().active()
    return active


if __name__ == "__main__":
    celery_app.start()