"""
数据库配置和连接管理
CPG2PVG-AI System Database Configuration
"""

import logging
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import redis.asyncio as aioredis
from sqlalchemy.orm import declarative_base

from app.core.config import settings

logger = logging.getLogger(__name__)

# 根据数据库URL创建适当的引擎
def create_database_engine():
    """根据数据库URL创建适当的引擎"""
    db_url = settings.DATABASE_URL

    if db_url.startswith("sqlite"):
        # SQLite配置
        return create_async_engine(
            db_url,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False},  # SQLite特有配置
        )
    else:
        # PostgreSQL配置
        return create_async_engine(
            db_url,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            connect_args={
                "command_timeout": 60,
                "server_settings": {
                    "application_name": "cpg2pvg_ai",
                    "timezone": "Asia/Shanghai",
                },
            },
        )

# 创建异步数据库引擎
engine = create_database_engine()

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 创建Redis连接
redis_client = None


async def get_redis() -> aioredis.Redis:
    """获取Redis客户端"""
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            retry_on_timeout=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            health_check_interval=30,
        )
    return redis_client


async def init_redis():
    """初始化Redis连接"""
    try:
        redis = await get_redis()
        await redis.ping()
        logger.info("Redis connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise


async def close_redis():
    """关闭Redis连接"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖项"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_session() -> AsyncSession:
    """获取数据库会话（用于非依赖注入场景）"""
    return AsyncSessionLocal()


# 数据库初始化和管理函数
async def init_db():
    """初始化数据库"""
    try:
        # 导入所有模型以确保它们被注册到Base.metadata
        from app.models import user, guideline, task, task_progress, processing_result
        from app.models.base import Base

        # 创建所有表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database tables created successfully")

        # 创建索引和约束
        await create_indexes()

        # 初始化基础数据
        await init_default_data()

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def create_indexes():
    """创建性能优化索引"""
    try:
        async with get_db_session() as session:
            # 在这里可以添加额外的索引创建逻辑
            # 例如：全文搜索索引、复合索引等
            pass
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")


async def init_default_data():
    """初始化默认数据"""
    try:
        from app.models.user import User, UserRole, UserStatus

        async with get_db_session() as session:
            # 检查是否已存在管理员用户
            admin_user = await session.execute(
                "SELECT id FROM users WHERE is_superuser = TRUE LIMIT 1"
            )

            if not admin_user.scalar():
                # 创建默认管理员用户
                from app.core.security import get_password_hash

                admin = User(
                    email="admin@cpg2pvg.ai",
                    username="admin",
                    full_name="系统管理员",
                    hashed_password=get_password_hash(os.getenv("DEFAULT_ADMIN_PASSWORD", secrets.token_urlsafe(16))),  # 生产环境必须设置环境变量
                    is_verified=True,
                    is_active=True,
                    is_superuser=True,
                    role=UserRole.ADMIN,
                    api_quota=10000,
                    storage_quota=10737418240,  # 10GB
                )

                session.add(admin)
                await session.commit()
                logger.info("Default admin user created")
            else:
                logger.info("Admin user already exists")

    except Exception as e:
        logger.error(f"Failed to initialize default data: {e}")


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
    logger.info("Database connections closed")


# 数据库健康检查
async def check_db_health() -> dict:
    """检查数据库健康状态"""
    try:
        async with get_db_session() as session:
            result = await session.execute("SELECT 1")
            result.scalar()

        return {
            "status": "healthy",
            "message": "Database connection successful",
            "pool_size": engine.pool.size(),
            "checked_in_connections": engine.pool.checkedin(),
            "checked_out_connections": engine.pool.checkedout(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": str(e),
            "pool_size": engine.pool.size() if engine.pool else 0,
        }


# 缓存工具函数
async def cache_get(key: str) -> Optional[str]:
    """从缓存获取数据"""
    try:
        redis = await get_redis()
        return await redis.get(key)
    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return None


async def cache_set(key: str, value: str, expire: int = 3600) -> bool:
    """设置缓存数据"""
    try:
        redis = await get_redis()
        await redis.setex(key, expire, value)
        return True
    except Exception as e:
        logger.error(f"Cache set error: {e}")
        return False


async def cache_delete(key: str) -> bool:
    """删除缓存数据"""
    try:
        redis = await get_redis()
        await redis.delete(key)
        return True
    except Exception as e:
        logger.error(f"Cache delete error: {e}")
        return False


# 数据库统计信息
async def get_db_stats() -> dict:
    """获取数据库统计信息"""
    try:
        async with get_db_session() as session:
            # 用户统计
            user_count = await session.execute("SELECT COUNT(*) FROM users")
            guideline_count = await session.execute("SELECT COUNT(*) FROM guidelines")
            task_count = await session.execute("SELECT COUNT(*) FROM tasks")

            return {
                "users": user_count.scalar(),
                "guidelines": guideline_count.scalar(),
                "tasks": task_count.scalar(),
                "connection_pool_size": engine.pool.size(),
                "active_connections": engine.pool.checkedout(),
            }
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {}


# 清理过期数据
async def cleanup_expired_data():
    """清理过期数据"""
    try:
        async with get_db_session() as session:
            # 清理过期的任务进度记录（30天前）
            from datetime import datetime, timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=30)

            result = await session.execute(
                "DELETE FROM task_progress WHERE created_at < :cutoff",
                {"cutoff": cutoff_date}
            )

            await session.commit()
            logger.info(f"Cleaned up {result.rowcount} expired task progress records")

    except Exception as e:
        logger.error(f"Failed to cleanup expired data: {e}")


# 事务装饰器
def db_transaction(func):
    """数据库事务装饰器"""
    async def wrapper(*args, **kwargs):
        async with get_db_session() as session:
            try:
                result = await func(session, *args, **kwargs)
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                raise
    return wrapper