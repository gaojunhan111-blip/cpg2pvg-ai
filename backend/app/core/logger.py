"""
结构化日志系统
CPG2PVG-AI System Structured Logging
"""

import logging
import logging.handlers
import sys
import json
import time
import traceback
import threading
from datetime import datetime
from typing import Any, Dict, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

import structlog
from pythonjsonlogger import jsonlogger

from app.core.config import get_settings


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(str, Enum):
    """日志分类"""
    SYSTEM = "system"
    API = "api"
    DATABASE = "database"
    SECURITY = "security"
    AUTH = "auth"
    WORKFLOW = "workflow"
    LLM = "llm"
    CACHE = "cache"
    TASK = "task"
    FILE_STORAGE = "file_storage"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    USER = "user"
    AUDIT = "audit"


@dataclass
class LogContext:
    """日志上下文"""
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    method: Optional[str] = None
    endpoint: Optional[str] = None
    status_code: Optional[int] = None
    duration_ms: Optional[float] = None
    error_type: Optional[str] = None
    error_code: Optional[str] = None
    component: Optional[str] = None
    category: LogCategory = LogCategory.SYSTEM
    tags: Dict[str, Any] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = {}


class JSONFormatter(jsonlogger.JsonFormatter):
    """JSON格式化器"""

    def format(self, record):
        # 添加自定义字段
        if hasattr(record, 'context'):
            context_data = asdict(record.context) if isinstance(record.context, LogContext) else record.context
        else:
            context_data = {}

        # 基础日志数据
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
            "process": record.process,
            "process_name": record.processName,
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # 合并上下文数据
        log_data.update(context_data)

        return json.dumps(log_data, ensure_ascii=False, default=str)


class PlainFormatter(logging.Formatter):
    """纯文本格式化器（开发环境使用）"""

    def format(self, record):
        # 基础格式
        log_format = "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s"

        # 添加上下文信息
        if hasattr(record, 'context') and isinstance(record.context, LogContext):
            context = record.context
            context_parts = []

            if context.request_id:
                context_parts.append(f"req:{context.request_id[:8]}")
            if context.user_id:
                context_parts.append(f"user:{context.user_id}")
            if context.component:
                context_parts.append(f"comp:{context.component}")
            if context.duration_ms:
                context_parts.append(f"duration:{context.duration_ms:.2f}ms")

            if context_parts:
                log_format = f"[%(asctime)s] %(levelname)-8s %(name)s [{', '.join(context_parts)}]: %(message)s"

        formatter = logging.Formatter(log_format)
        return formatter.format(record)


class StructuredLogger:
    """结构化日志器"""

    def __init__(self):
        self.settings = get_settings()
        self._context = threading.local()
        self._loggers: Dict[str, logging.Logger] = {}
        self._setup_logging()

    def _setup_logging(self):
        """设置日志系统"""
        # 配置structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        # 设置根日志级别
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.settings.LOG_LEVEL))

        # 清除现有处理器
        root_logger.handlers.clear()

        # 添加控制台处理器
        self._add_console_handler(root_logger)

        # 添加文件处理器（如果配置了日志目录）
        if self.settings.LOG_FILE_PATH:
            self._add_file_handlers(root_logger)

        # 配置特定日志器
        self._configure_specific_loggers()

    def _add_console_handler(self, logger: logging.Logger):
        """添加控制台处理器"""
        if self.settings.is_development():
            # 开发环境使用彩色输出
            from colorlog import ColoredFormatter
            formatter = ColoredFormatter(
                "%(log_color)s[%(asctime)s] %(levelname)-8s %(name)s: %(message)s%(reset)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white",
                }
            )
        else:
            # 生产环境使用JSON格式
            formatter = JSONFormatter()

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, self.settings.LOG_LEVEL))
        logger.addHandler(console_handler)

    def _add_file_handlers(self, logger: logging.Logger):
        """添加文件处理器"""
        log_dir = Path(self.settings.LOG_FILE_PATH).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # 主日志文件
        main_handler = logging.handlers.RotatingFileHandler(
            filename=self.settings.LOG_FILE_PATH,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=5,
            encoding='utf-8'
        )
        main_handler.setFormatter(JSONFormatter())
        main_handler.setLevel(logging.INFO)
        logger.addHandler(main_handler)

        # 错误日志文件
        error_file = log_dir / "error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            filename=error_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setFormatter(JSONFormatter())
        error_handler.setLevel(logging.ERROR)
        logger.addHandler(error_handler)

        # 审计日志文件
        audit_file = log_dir / "audit.log"
        audit_handler = logging.handlers.RotatingFileHandler(
            filename=audit_file,
            maxBytes=20 * 1024 * 1024,  # 20MB
            backupCount=5,
            encoding='utf-8'
        )
        audit_handler.setFormatter(JSONFormatter())
        audit_handler.addFilter(lambda record: hasattr(record, 'context') and
                              isinstance(record.context, LogContext) and
                              record.context.category == LogCategory.AUDIT)
        logger.addHandler(audit_handler)

    def _configure_specific_loggers(self):
        """配置特定日志器"""
        # 数据库日志
        db_logger = logging.getLogger("sqlalchemy.engine")
        db_logger.setLevel(logging.WARNING if not self.settings.is_development() else logging.INFO)

        # HTTP客户端日志
        http_logger = logging.getLogger("httpx")
        http_logger.setLevel(logging.WARNING)

        # Redis日志
        redis_logger = logging.getLogger("redis")
        redis_logger.setLevel(logging.WARNING)

        # Celery日志
        celery_logger = logging.getLogger("celery")
        celery_logger.setLevel(logging.INFO)

    def get_logger(self, name: str) -> logging.Logger:
        """获取日志器"""
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        return self._loggers[name]

    def set_context(self, context: LogContext):
        """设置日志上下文"""
        self._context.value = context

    def get_context(self) -> Optional[LogContext]:
        """获取当前日志上下文"""
        return getattr(self._context, 'value', None)

    def clear_context(self):
        """清除日志上下文"""
        self._context.value = None

    def _log_with_context(
        self,
        level: LogLevel,
        logger: logging.Logger,
        message: str,
        context: Optional[LogContext] = None,
        **kwargs
    ):
        """带上下文的日志记录"""
        # 合并上下文
        current_context = self.get_context()
        if context and current_context:
            # 合并上下文，新上下文优先级更高
            merged_context = LogContext(
                **{**asdict(current_context), **asdict(context)}
            )
        elif context:
            merged_context = context
        else:
            merged_context = current_context

        # 创建日志记录
        extra = {"context": merged_context} if merged_context else {}

        # 添加额外的字段到上下文
        if kwargs:
            if merged_context:
                merged_context.tags.update(kwargs)
            else:
                extra = {"context": LogContext(tags=kwargs)}

        # 记录日志
        getattr(logger, level.lower())(message, extra=extra)

    def debug(
        self,
        message: str,
        context: Optional[LogContext] = None,
        **kwargs
    ):
        """调试日志"""
        self._log_with_context(LogLevel.DEBUG, self.get_logger(__name__), message, context, **kwargs)

    def info(
        self,
        message: str,
        context: Optional[LogContext] = None,
        **kwargs
    ):
        """信息日志"""
        self._log_with_context(LogLevel.INFO, self.get_logger(__name__), message, context, **kwargs)

    def warning(
        self,
        message: str,
        context: Optional[LogContext] = None,
        **kwargs
    ):
        """警告日志"""
        self._log_with_context(LogLevel.WARNING, self.get_logger(__name__), message, context, **kwargs)

    def error(
        self,
        message: str,
        context: Optional[LogContext] = None,
        exception: Optional[Exception] = None,
        **kwargs
    ):
        """错误日志"""
        if exception:
            kwargs["exception_type"] = type(exception).__name__
            kwargs["exception_message"] = str(exception)

        self._log_with_context(LogLevel.ERROR, self.get_logger(__name__), message, context, **kwargs)

    def critical(
        self,
        message: str,
        context: Optional[LogContext] = None,
        exception: Optional[Exception] = None,
        **kwargs
    ):
        """严重错误日志"""
        if exception:
            kwargs["exception_type"] = type(exception).__name__
            kwargs["exception_message"] = str(exception)

        self._log_with_context(LogLevel.CRITICAL, self.get_logger(__name__), message, context, **kwargs)


# 全局日志器实例
structured_logger = StructuredLogger()


def get_logger(name: Optional[str] = None) -> Union[logging.Logger, StructuredLogger]:
    """获取日志器"""
    if name:
        return structured_logger.get_logger(name)
    return structured_logger


def set_log_context(context: LogContext):
    """设置日志上下文"""
    structured_logger.set_context(context)


def get_log_context() -> Optional[LogContext]:
    """获取当前日志上下文"""
    return structured_logger.get_context()


def clear_log_context():
    """清除日志上下文"""
    structured_logger.clear_context()


# 便捷函数
def log_api_request(
    method: str,
    endpoint: str,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    **kwargs
):
    """记录API请求日志"""
    context = LogContext(
        request_id=request_id or str(uuid.uuid4()),
        user_id=user_id,
        method=method,
        endpoint=endpoint,
        category=LogCategory.API,
        tags=kwargs
    )
    structured_logger.info(f"API {method} {endpoint}", context)


def log_api_response(
    method: str,
    endpoint: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    **kwargs
):
    """记录API响应日志"""
    context = LogContext(
        request_id=request_id,
        user_id=user_id,
        method=method,
        endpoint=endpoint,
        status_code=status_code,
        duration_ms=duration_ms,
        category=LogCategory.API,
        tags=kwargs
    )

    if status_code >= 400:
        structured_logger.warning(f"API {method} {endpoint} failed with {status_code}", context)
    else:
        structured_logger.info(f"API {method} {endpoint} completed", context)


def log_security_event(
    event: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    **kwargs
):
    """记录安全事件日志"""
    context = LogContext(
        user_id=user_id,
        ip_address=ip_address,
        category=LogCategory.SECURITY,
        tags={"event": event, **kwargs}
    )
    structured_logger.info(f"Security event: {event}", context)


def log_workflow_event(
    workflow_id: str,
    event: str,
    status: str,
    user_id: Optional[str] = None,
    **kwargs
):
    """记录工作流事件日志"""
    context = LogContext(
        user_id=user_id,
        category=LogCategory.WORKFLOW,
        tags={
            "workflow_id": workflow_id,
            "event": event,
            "status": status,
            **kwargs
        }
    )
    structured_logger.info(f"Workflow {workflow_id}: {event} - {status}", context)


def log_llm_call(
    provider: str,
    model: str,
    tokens_used: int,
    cost: float,
    duration_ms: float,
    user_id: Optional[str] = None,
    **kwargs
):
    """记录LLM调用日志"""
    context = LogContext(
        user_id=user_id,
        category=LogCategory.LLM,
        duration_ms=duration_ms,
        tags={
            "provider": provider,
            "model": model,
            "tokens_used": tokens_used,
            "cost": cost,
            **kwargs
        }
    )
    structured_logger.info(f"LLM call: {provider}/{model} - {tokens_used} tokens, ${cost:.6f}", context)


def log_performance_metric(
    metric_name: str,
    value: float,
    unit: str,
    component: Optional[str] = None,
    **kwargs
):
    """记录性能指标日志"""
    context = LogContext(
        component=component,
        category=LogCategory.PERFORMANCE,
        tags={
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            **kwargs
        }
    )
    structured_logger.info(f"Performance: {metric_name} = {value} {unit}", context)


def log_audit_event(
    action: str,
    resource: str,
    user_id: Optional[str] = None,
    success: bool = True,
    **kwargs
):
    """记录审计事件日志"""
    context = LogContext(
        user_id=user_id,
        category=LogCategory.AUDIT,
        tags={
            "action": action,
            "resource": resource,
            "success": success,
            **kwargs
        }
    )

    message = f"Audit: {action} on {resource}"
    if not success:
        structured_logger.error(message, context)
    else:
        structured_logger.info(message, context)


# 日志中间件上下文管理器
class LogContextManager:
    """日志上下文管理器"""

    def __init__(self, context: LogContext):
        self.context = context
        self.previous_context = None

    def __enter__(self):
        self.previous_context = get_log_context()
        set_log_context(self.context)
        return self.context

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.previous_context:
            set_log_context(self.previous_context)
        else:
            clear_log_context()

        # 如果有异常，记录错误日志
        if exc_type and exc_val:
            structured_logger.error(
                f"Exception in context: {exc_val}",
                context=self.context,
                exception=exc_val
            )