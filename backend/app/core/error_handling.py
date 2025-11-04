"""
统一错误处理和重试机制
Unified Error Handling and Retry Mechanism
"""

import asyncio
import functools
import random
import traceback
from typing import Any, Callable, Dict, List, Optional, Type, Union
from datetime import datetime, timedelta
from enum import Enum

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# 可选的sentry集成
try:
    import sentry_sdk
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

from app.core.logger import get_logger

logger = get_logger(__name__)


class ErrorSeverity(str, Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """错误类别"""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    FILE_SYSTEM = "file_system"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    NETWORK = "network"


class CPG2PVGException(Exception):
    """CPG2PVG系统基础异常类"""

    def __init__(
        self,
        message: str,
        error_code: str = None,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Dict[str, Any] = None,
        cause: Exception = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "cause": str(self.cause) if self.cause else None
        }


class ValidationError(CPG2PVGException):
    """验证错误"""

    def __init__(self, message: str, field: str = None, value: Any = None, **kwargs):
        details = kwargs.get('details', {})
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = str(value)

        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            details=details,
            **kwargs
        )


class AuthenticationError(CPG2PVGException):
    """认证错误"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class AuthorizationError(CPG2PVGException):
    """授权错误"""

    def __init__(self, message: str, required_permission: str = None, **kwargs):
        details = kwargs.get('details', {})
        if required_permission:
            details['required_permission'] = required_permission

        super().__init__(
            message=message,
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            **kwargs
        )


class DatabaseError(CPG2PVGException):
    """数据库错误"""

    def __init__(self, message: str, operation: str = None, **kwargs):
        details = kwargs.get('details', {})
        if operation:
            details['operation'] = operation

        super().__init__(
            message=message,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            details=details,
            **kwargs
        )


class ExternalAPIError(CPG2PVGException):
    """外部API错误"""

    def __init__(self, message: str, api_name: str = None, status_code: int = None, **kwargs):
        details = kwargs.get('details', {})
        if api_name:
            details['api_name'] = api_name
        if status_code:
            details['status_code'] = status_code

        super().__init__(
            message=message,
            category=ErrorCategory.EXTERNAL_API,
            severity=ErrorSeverity.HIGH,
            details=details,
            **kwargs
        )


class FileSystemError(CPG2PVGException):
    """文件系统错误"""

    def __init__(self, message: str, file_path: str = None, operation: str = None, **kwargs):
        details = kwargs.get('details', {})
        if file_path:
            details['file_path'] = file_path
        if operation:
            details['operation'] = operation

        super().__init__(
            message=message,
            category=ErrorCategory.FILE_SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            **kwargs
        )


class WorkflowError(CPG2PVGException):
    """工作流错误"""

    def __init__(self, message: str, workflow_id: str = None, stage: str = None, **kwargs):
        details = kwargs.get('details', {})
        if workflow_id:
            details['workflow_id'] = workflow_id
        if stage:
            details['stage'] = stage

        super().__init__(
            message=message,
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.HIGH,
            details=details,
            **kwargs
        )


class RetryConfig:
    """重试配置"""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: List[Type[Exception]] = None,
        stop_on_exception: List[Type[Exception]] = None
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [
            ConnectionError,
            TimeoutError,
            ExternalAPIError,
            DatabaseError
        ]
        self.stop_on_exception = stop_on_exception or [
            AuthenticationError,
            AuthorizationError,
            ValidationError
        ]


def retry(
    config: RetryConfig = None,
    default_config: RetryConfig = None
):
    """
    重试装饰器

    Args:
        config: 重试配置
        default_config: 默认重试配置
    """
    if config is None:
        config = default_config or RetryConfig()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    # 检查是否应该停止重试
                    for stop_exception in config.stop_on_exception:
                        if isinstance(e, stop_exception):
                            raise

                    # 检查是否是可重试的异常
                    is_retryable = any(isinstance(e, exc_type) for exc_type in config.retryable_exceptions)

                    if not is_retryable or attempt == config.max_attempts - 1:
                        # 记录重试失败
                        logger.error(
                            f"Function {func.__name__} failed after {attempt + 1} attempts",
                            extra_data={
                                "function": func.__name__,
                                "attempts": attempt + 1,
                                "max_attempts": config.max_attempts,
                                "error": str(e),
                                "error_type": type(e).__name__
                            }
                        )
                        raise

                    # 计算延迟时间
                    delay = min(
                        config.base_delay * (config.backoff_factor ** attempt),
                        config.max_delay
                    )

                    if config.jitter:
                        delay *= (0.5 + random.random() * 0.5)

                    logger.warning(
                        f"Function {func.__name__} attempt {attempt + 1} failed, retrying in {delay:.2f}s",
                        extra_data={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "error": str(e),
                            "retry_delay": delay
                        }
                    )

                    await asyncio.sleep(delay)

            # 这里不应该到达，但为了类型安全
            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 同步函数版本的简单实现
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    # 检查是否应该停止重试
                    for stop_exception in config.stop_on_exception:
                        if isinstance(e, stop_exception):
                            raise

                    # 检查是否是可重试的异常
                    is_retryable = any(isinstance(e, exc_type) for exc_type in config.retryable_exceptions)

                    if not is_retryable or attempt == config.max_attempts - 1:
                        logger.error(
                            f"Function {func.__name__} failed after {attempt + 1} attempts",
                            extra_data={
                                "function": func.__name__,
                                "attempts": attempt + 1,
                                "error": str(e),
                                "error_type": type(e).__name__
                            }
                        )
                        raise

                    # 计算延迟时间
                    delay = min(
                        config.base_delay * (config.backoff_factor ** attempt),
                        config.max_delay
                    )

                    if config.jitter:
                        delay *= (0.5 + random.random() * 0.5)

                    logger.warning(
                        f"Function {func.__name__} attempt {attempt + 1} failed, retrying in {delay:.2f}s",
                        extra_data={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "error": str(e),
                            "retry_delay": delay
                        }
                    )

                    import time
                    time.sleep(delay)

            raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """错误处理中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        try:
            response = await call_next(request)
            return response

        except CPG2PVGException as e:
            # 处理CPG2PVG系统异常
            logger.error(
                f"CPG2PVG Exception: {e.message}",
                extra_data={
                    "error_type": e.__class__.__name__,
                    "error_code": e.error_code,
                    "category": e.category.value,
                    "severity": e.severity.value,
                    "details": e.details,
                    "path": request.url.path,
                    "method": request.method
                }
            )

            # 根据严重程度决定是否发送到监控系统
            if e.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                await self._send_alert(e)

            return self._create_error_response(e)

        except HTTPException as e:
            # FastAPI HTTP异常
            logger.warning(
                f"HTTP Exception: {e.detail}",
                extra_data={
                    "status_code": e.status_code,
                    "path": request.url.path,
                    "method": request.method
                }
            )
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": True,
                    "message": e.detail,
                    "status_code": e.status_code,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        except Exception as e:
            # 未预期的异常
            logger.error(
                f"Unexpected error: {str(e)}",
                extra_data={
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc(),
                    "path": request.url.path,
                    "method": request.method
                }
            )

            # 发送紧急告警
            await self._send_alert(CPG2PVGException(
                message=str(e),
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                details={
                    "traceback": traceback.format_exc(),
                    "path": request.url.path,
                    "method": request.method
                }
            ))

            return JSONResponse(
                status_code=500,
                content={
                    "error": True,
                    "message": "Internal server error",
                    "status_code": 500,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

    def _create_error_response(self, exception: CPG2PVGException) -> JSONResponse:
        """创建错误响应"""
        status_code_map = {
            ErrorSeverity.LOW: 400,
            ErrorSeverity.MEDIUM: 400,
            ErrorSeverity.HIGH: 500,
            ErrorSeverity.CRITICAL: 500
        }

        status_code = status_code_map.get(exception.severity, 500)

        return JSONResponse(
            status_code=status_code,
            content={
                "error": True,
                "message": exception.message,
                "error_code": exception.error_code,
                "category": exception.category.value,
                "severity": exception.severity.value,
                "details": exception.details,
                "timestamp": exception.timestamp.isoformat()
            }
        )

    async def _send_alert(self, exception: CPG2PVGException):
        """发送告警"""
        try:
            # 这里可以集成各种告警系统
            # 例如：邮件、短信、Slack、钉钉等

            # 示例：记录到Sentry
            if SENTRY_AVAILABLE and hasattr(exception, '__traceback__') and exception.__traceback__:
                sentry_sdk.capture_exception(exception)

            # 示例：发送邮件告警
            if exception.severity == ErrorSeverity.CRITICAL:
                await self._send_email_alert(exception)

        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    async def _send_email_alert(self, exception: CPG2PVGException):
        """发送邮件告警"""
        # 这里实现邮件发送逻辑
        logger.critical(f"CRITICAL ALERT: {exception.message}")


class ErrorHandler:
    """错误处理器"""

    @staticmethod
    def handle_validation_error(field: str, value: Any, message: str = None) -> ValidationError:
        """处理验证错误"""
        error_message = message or f"Invalid value for field '{field}': {value}"
        return ValidationError(
            message=error_message,
            field=field,
            value=value
        )

    @staticmethod
    def handle_database_error(operation: str, original_error: Exception) -> DatabaseError:
        """处理数据库错误"""
        return DatabaseError(
            message=f"Database operation failed: {operation}",
            operation=operation,
            cause=original_error
        )

    @staticmethod
    def handle_external_api_error(api_name: str, status_code: int, response_text: str) -> ExternalAPIError:
        """处理外部API错误"""
        return ExternalAPIError(
            message=f"External API '{api_name}' returned error: {status_code}",
            api_name=api_name,
            status_code=status_code,
            details={"response": response_text[:500]}  # 限制响应文本长度
        )

    @staticmethod
    def handle_file_system_error(operation: str, file_path: str, original_error: Exception) -> FileSystemError:
        """处理文件系统错误"""
        return FileSystemError(
            message=f"File system operation failed: {operation}",
            file_path=file_path,
            operation=operation,
            cause=original_error
        )

    @staticmethod
    def handle_workflow_error(workflow_id: str, stage: str, original_error: Exception) -> WorkflowError:
        """处理工作流错误"""
        return WorkflowError(
            message=f"Workflow error in stage '{stage}': {str(original_error)}",
            workflow_id=workflow_id,
            stage=stage,
            cause=original_error
        )


# 默认重试配置实例
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    backoff_factor=2.0,
    jitter=True
)

# 工作流重试配置（更宽松）
WORKFLOW_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    base_delay=2.0,
    max_delay=120.0,
    backoff_factor=1.5,
    jitter=True,
    retryable_exceptions=[
        ConnectionError,
        TimeoutError,
        ExternalAPIError,
        DatabaseError,
        WorkflowError
    ]
)

# 外部API重试配置
API_RETRY_CONFIG = RetryConfig(
    max_attempts=4,
    base_delay=0.5,
    max_delay=10.0,
    backoff_factor=2.0,
    jitter=True,
    retryable_exceptions=[
        ConnectionError,
        TimeoutError,
        ExternalAPIError
    ]
)