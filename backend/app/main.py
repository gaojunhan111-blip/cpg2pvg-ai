"""
FastAPI应用主入口 - 改进版
Enhanced FastAPI Application Entry Point
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import uuid

from app.core.config import get_settings
from app.core.database import engine, get_db_session
from app.models.base import Base
from app.api.v1.api import api_router
from app.core.error_handling import ErrorHandlingMiddleware
from app.middleware.response_middleware import ResponseMiddleware
from app.core.logger import get_logger
from app.core.llm_client import llm_client

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("CPG2PVG-AI Backend Starting...")

    try:
        # 创建数据库表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表创建成功")

        # 初始化LLM客户端 (暂时跳过)
        # TODO: 修复LLM客户端初始化问题
        logger.info("跳过LLM客户端初始化，使用Mock模式")

        logger.info("CPG2PVG-AI Backend 启动完成")

    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise

    yield

    # 关闭时执行
    logger.info("CPG2PVG-AI Backend Shutting down...")

    try:
        # 关闭LLM客户端连接
        await llm_client.close()
        logger.info("LLM客户端连接已关闭")

        # 关闭数据库连接
        await engine.dispose()
        logger.info("数据库连接已关闭")

    except Exception as e:
        logger.error(f"应用关闭时出错: {e}")


async def request_logging_middleware(request: Request, call_next):
    """请求日志中间件"""
    start_time = time.time()

    # 生成请求ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # 记录请求开始
    logger.info(f"[{request_id}] {request.method} {request.url.path} - 开始处理")

    try:
        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 记录请求完成
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"状态码: {response.status_code}, "
            f"处理时间: {process_time:.3f}s"
        )

        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"处理失败: {str(e)}, "
            f"处理时间: {process_time:.3f}s"
        )
        raise


async def security_headers_middleware(request: Request, call_next):
    """安全头中间件"""
    response = await call_next(request)

    # 添加安全头
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # 只在开发环境禁用HSTS
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


def create_application() -> FastAPI:
    """创建FastAPI应用实例"""

    app = FastAPI(
        title=getattr(settings, 'PROJECT_NAME', 'CPG2PVG-AI'),
        description=getattr(settings, 'PROJECT_DESCRIPTION', '将临床医学指南转化为公众医学指南的智能系统'),
        version=getattr(settings, 'VERSION', '1.0.0'),
        openapi_url=f"{getattr(settings, 'API_V1_STR', '/api/v1')}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # 添加中间件 (顺序很重要)

    # 1. 统一响应格式中间件 (最外层)
    app.add_middleware(ResponseMiddleware, debug=settings.DEBUG)

    # 2. 错误处理中间件
    app.add_middleware(ErrorHandlingMiddleware)

    # 3. 请求日志中间件
    app.middleware("http")(request_logging_middleware)

    # 4. Gzip压缩中间件
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 5. 安全头中间件
    app.middleware("http")(security_headers_middleware)

    # 6. CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=getattr(settings, 'ALLOWED_HOSTS', ["*"]),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # 包含API路由
    app.include_router(api_router, prefix=getattr(settings, 'API_V1_STR', '/api/v1'))

    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return {
            "status": "healthy",
            "service": "cpg2pvg-ai-backend",
            "version": getattr(settings, 'VERSION', '1.0.0'),
            "timestamp": time.time()
        }

    @app.get("/")
    async def root():
        """根端点"""
        return {
            "message": "欢迎使用 CPG2PVG-AI 系统",
            "version": getattr(settings, 'VERSION', '1.0.0'),
            "docs": "/docs",
            "health": "/health"
        }

    return app


app = create_application()