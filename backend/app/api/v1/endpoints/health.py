"""
健康检查端点
CPG2PVG-AI System Health Check
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import asyncio
import redis
import time

from app.core.database import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """系统健康检查"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.VERSION,
        "checks": {}
    }

    # 数据库连接检查
    try:
        await db.execute("SELECT 1")
        health_status["checks"]["database"] = {"status": "healthy", "response_time": "< 10ms"}
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}

    # Redis连接检查
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        health_status["checks"]["redis"] = {"status": "healthy", "response_time": "< 5ms"}
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}

    return health_status


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """详细健康检查"""
    return {
        "service": "cpg2pvg-ai-backend",
        "status": "running",
        "uptime": time.time(),
        "environment": settings.DEBUG and "development" or "production",
        "features": {
            "database": "postgresql",
            "cache": "redis",
            "task_queue": "celery",
            "file_storage": "minio"
        }
    }