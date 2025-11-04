"""
API v1 路由聚合
CPG2PVG-AI System API v1
"""

from fastapi import APIRouter
from app.api.v1.endpoints import guidelines, tasks, users, health, workflow, auth, files

api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(
    guidelines.router,
    prefix="/guidelines",
    tags=["guidelines"],
    responses={404: {"description": "Not found"}}
)

api_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}}
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}}
)

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"],
    responses={404: {"description": "Not found"}}
)

# 认证路由 (不需要认证的公共端点)
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"],
    responses={404: {"description": "Not found"}}
)

api_router.include_router(
    workflow.router,
    prefix="/workflow",
    tags=["workflow"],
    responses={404: {"description": "Not found"}}
)

# 文件管理路由
api_router.include_router(
    files.router,
    prefix="/files",
    tags=["files"],
    responses={404: {"description": "Not found"}}
)

@api_router.get("/")
async def api_info():
    """API信息"""
    return {
        "name": "CPG2PVG-AI API",
        "version": "1.0.0",
        "description": "将临床医学指南转化为公众医学指南的智能系统API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }