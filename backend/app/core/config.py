"""
应用配置管理
CPG2PVG-AI System Configuration
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional, Dict, Any
from functools import lru_cache
import os
import logging


class Settings(BaseSettings):
    """应用设置"""

    # 基础配置
    PROJECT_NAME: str = "CPG2PVG-AI"
    PROJECT_DESCRIPTION: str = "将临床医学指南转化为公众医学指南的智能系统"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # 安全配置
    SECRET_KEY: str = Field(default="", description="JWT密钥，生产环境必须设置")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS配置
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "https://yourdomain.com",
    ]

    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./cpg2pvg_dev.db"  # 开发环境默认使用SQLite
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1小时
    REDIS_SESSION_TTL: int = 86400  # 24小时

    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    DEFAULT_TASK_TIMEOUT: int = 1800  # 30分钟

    # MinIO配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = Field(default="", description="MinIO访问密钥，生产环境必须设置")
    MINIO_SECRET_KEY: str = Field(default="", description="MinIO密钥，生产环境必须设置")
    MINIO_BUCKET_NAME: str = "cpg2pvg-docs"
    MINIO_SECURE: bool = False
    MINIO_REGION: str = "us-east-1"

    # 文件上传配置
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".docx", ".txt", ".doc", ".html", ".md"]
    UPLOAD_DIR: str = "uploads"

    # AI模型配置
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    ANTHROPIC_BASE_URL: Optional[str] = None

    # 默认模型配置
    DEFAULT_LLM_MODEL: str = "gpt-3.5-turbo"
    HIGH_QUALITY_MODEL: str = "gpt-4"
    COST_EFFECTIVE_MODEL: str = "gpt-3.5-turbo-instruct"
    MAX_TOKENS_PER_REQUEST: int = 4000
    TEMPERATURE: float = 0.7

    # 工作流配置
    MAX_CHUNK_SIZE: int = 800
    MIN_CHUNK_SIZE: int = 100
    DEFAULT_PROCESSING_MODE: str = "slow"
    WORKFLOW_TIMEOUT: int = 3600  # 1小时

    # 监控配置
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE_PATH: Optional[str] = None  # 如果设置，将日志写入文件
    LOG_MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    LOG_BACKUP_COUNT: int = 5
    LOG_JSON_FORMAT: bool = True  # 是否使用JSON格式
    LOG_ENABLE_COLORS: bool = True  # 是否启用彩色输出
    LOG_INCLUDE_TRACEBACK: bool = True  # 是否包含异常堆栈

    # 结构化日志配置
    LOG_STRUCTURED: bool = True
    LOG_CORRELATION_ID_HEADER: str = "X-Correlation-ID"
    LOG_REQUEST_ID_HEADER: str = "X-Request-ID"
    LOG_TRACE_ID_HEADER: str = "X-Trace-ID"

    # 日志收集配置
    LOG_ENABLE_AGGREGATION: bool = False
    LOG_AGGREGATION_INTERVAL: int = 60  # 秒
    LOG_METRICS_ENDPOINT: Optional[str] = None
    LOG_SPLUNK_URL: Optional[str] = None
    LOG_SPLUNK_TOKEN: Optional[str] = None
    LOG_ELASTICSEARCH_URL: Optional[str] = None
    LOG_ELASTICSEARCH_INDEX: str = "cpg2pvg-logs"

    # 邮件配置
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: str = "CPG2PVG-AI"

    # 缓存配置
    CACHE_TTL: int = 300  # 5分钟
    SESSION_CACHE_TTL: int = 86400  # 24小时

    # 限流配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 200

    # 分页配置
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Webhook配置
    WEBHOOK_SECRET: Optional[str] = None
    WEBHOOK_TIMEOUT: int = 30
    WEBHOOK_RETRY_ATTEMPTS: int = 3

    # 搜索配置
    SEARCH_RESULTS_LIMIT: int = 50
    SEARCH_HIGHLIGHT_ENABLED: bool = True

    # API版本控制
    API_VERSION: str = "v1"
    API_DEPRECATED_VERSIONS: List[str] = []

    # 实验性功能
    ENABLE_EXPERIMENTAL_FEATURES: bool = False
    ENABLE_AI_FEATURES: bool = True
    ENABLE_ADVANCED_ANALYTICS: bool = False

    # 成本控制配置
    MAX_MONTHLY_COST_PER_USER: float = 100.0  # 每月最大成本限制
    COST_TRACKING_ENABLED: bool = True

    # 质量控制配置
    MIN_QUALITY_SCORE_THRESHOLD: float = 0.6
    AUTO_REJECT_LOW_QUALITY: bool = False

    # 备份配置
    BACKUP_ENABLED: bool = True
    BACKUP_RETENTION_DAYS: int = 30

    # 开发配置
    RELOAD_ON_CHANGE: bool = True
    SHOW_DOCS: bool = True
    ENABLE_PROFILER: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略额外的环境变量

    def get_database_url(self, async_db: bool = True) -> str:
        """获取数据库URL"""
        if async_db:
            return self.DATABASE_URL
        else:
            # 转换为同步URL用于Alembic等工具
            if "+asyncpg://" in self.DATABASE_URL:
                return self.DATABASE_URL.replace("+asyncpg://", "://")
            elif "postgresql+asyncpg://" in self.DATABASE_URL:
                return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
            else:
                return self.DATABASE_URL

    def get_celery_config(self) -> Dict[str, Any]:
        """获取Celery配置"""
        return {
            "broker_url": self.CELERY_BROKER_URL,
            "result_backend": self.CELERY_RESULT_BACKEND,
            "task_serializer": "json",
            "accept_content": ["json"],
            "result_serializer": "json",
            "timezone": "Asia/Shanghai",
            "enable_utc": True,
            "task_soft_time_limit": self.DEFAULT_TASK_TIMEOUT - 60,
            "task_time_limit": self.DEFAULT_TASK_TIMEOUT,
            "worker_prefetch_multiplier": 1,
            "task_acks_late": True,
            "worker_max_tasks_per_child": 1000,
        }

    def get_minio_config(self) -> Dict[str, Any]:
        """获取MinIO配置"""
        return {
            "endpoint": self.MINIO_ENDPOINT,
            "access_key": self.MINIO_ACCESS_KEY,
            "secret_key": self.MINIO_SECRET_KEY,
            "secure": self.MINIO_SECURE,
            "region": self.MINIO_REGION,
        }

    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        config = {
            "default_model": self.DEFAULT_LLM_MODEL,
            "high_quality_model": self.HIGH_QUALITY_MODEL,
            "cost_effective_model": self.COST_EFFECTIVE_MODEL,
            "max_tokens": self.MAX_TOKENS_PER_REQUEST,
            "temperature": self.TEMPERATURE,
        }

        if self.OPENAI_API_KEY:
            config["openai"] = {
                "api_key": self.OPENAI_API_KEY,
                "base_url": self.OPENAI_BASE_URL,
            }

        if self.ANTHROPIC_API_KEY:
            config["anthropic"] = {
                "api_key": self.ANTHROPIC_API_KEY,
                "base_url": self.ANTHROPIC_BASE_URL,
            }

        return config

    def is_development(self) -> bool:
        """判断是否为开发环境"""
        return self.DEBUG or self.ENVIRONMENT == "development"

    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return self.ENVIRONMENT == "production"

    def get_allowed_origins(self) -> List[str]:
        """获取允许的CORS源"""
        if self.is_development():
            return ["*"]
        return self.CORS_ORIGINS

    def get_upload_config(self) -> Dict[str, Any]:
        """获取文件上传配置"""
        return {
            "max_size": self.MAX_FILE_SIZE,
            "allowed_types": self.ALLOWED_FILE_TYPES,
            "upload_dir": self.UPLOAD_DIR,
            "bucket": self.MINIO_BUCKET_NAME,
        }

    def get_rate_limit_config(self) -> Dict[str, Any]:
        """获取限流配置"""
        if not self.RATE_LIMIT_ENABLED:
            return {"enabled": False}

        return {
            "enabled": True,
            "requests_per_minute": self.RATE_LIMIT_REQUESTS_PER_MINUTE,
            "burst": self.RATE_LIMIT_BURST,
        }

    def validate_config(self) -> List[str]:
        """验证配置的有效性"""
        errors = []

        # 检查必需的配置
        if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
            if self.is_production():
                errors.append("SECRET_KEY must be set in production")

        if not self.DATABASE_URL:
            errors.append("DATABASE_URL is required")

        if self.ENABLE_AI_FEATURES:
            if not self.OPENAI_API_KEY and not self.ANTHROPIC_API_KEY:
                errors.append("At least one AI API key must be set when AI features are enabled")

        # 检查文件大小限制
        if self.MAX_FILE_SIZE > 100 * 1024 * 1024:  # 100MB
            errors.append("MAX_FILE_SIZE should not exceed 100MB")

        # 检查任务超时
        if self.DEFAULT_TASK_TIMEOUT > 3600:  # 1小时
            errors.append("DEFAULT_TASK_TIMEOUT should not exceed 1 hour")

        return errors

    @property
    def ENVIRONMENT(self) -> str:
        """获取环境类型"""
        return os.getenv("ENVIRONMENT", "development")


# 创建全局设置实例
settings = Settings()


@lru_cache()
def get_settings() -> Settings:
    """获取设置实例（带缓存）"""
    return settings


def reload_settings():
    """重新加载设置"""
    global settings
    settings = Settings()
    get_settings.cache_clear()


# 验证配置
def validate_settings() -> bool:
    """验证设置"""
    errors = settings.validate_config()
    if errors:
        for error in errors:
            logger.error(f"Configuration Error: {error}")
        return False
    return True