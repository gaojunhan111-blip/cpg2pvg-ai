"""
监控任务
CPG2PVG-AI System Monitoring Tasks
"""

import logging
import psutil
import redis
from datetime import datetime
from celery import celery_app
from app.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(
    name="system_performance_check",
    soft_time_limit=60,  # 1分钟
    time_limit=120,       # 2分钟
)
def system_performance_check():
    """系统性能检查"""
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)

        # 内存使用情况
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent

        # Redis连接检查
        redis_status = "healthy"
        try:
            redis_client = redis.from_url(settings.REDIS_URL)
            redis_client.ping()
        except Exception as e:
            redis_status = f"unhealthy: {str(e)}"

        performance_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {
                "usage_percent": cpu_percent
            },
            "memory": {
                "usage_percent": memory_percent,
                "available_gb": round(memory.available / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2)
            },
            "disk": {
                "usage_percent": disk_percent,
                "free_gb": round(disk.free / (1024**3), 2),
                "total_gb": round(disk.total / (1024**3), 2)
            },
            "redis": {
                "status": redis_status
            }
        }

        # 检查是否需要告警
        alerts = []
        if cpu_percent > 80:
            alerts.append({"type": "cpu", "message": f"CPU使用率过高: {cpu_percent}%"})
        if memory_percent > 85:
            alerts.append({"type": "memory", "message": f"内存使用率过高: {memory_percent}%"})
        if disk_percent > 90:
            alerts.append({"type": "disk", "message": f"磁盘使用率过高: {disk_percent}%"})

        if alerts:
            logger.warning(f"Performance alerts: {alerts}")
            # TODO: 发送告警通知

        logger.info("Performance check completed")
        return {
            "success": True,
            "data": performance_data,
            "alerts": alerts
        }

    except Exception as e:
        logger.error(f"Performance check failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }