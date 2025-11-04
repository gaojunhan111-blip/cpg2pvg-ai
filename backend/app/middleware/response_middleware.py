"""
统一响应格式中间件
Unified Response Format Middleware

这个中间件确保所有API响应都遵循统一的格式
This middleware ensures all API responses follow a unified format
"""

import json
import uuid
import traceback
from typing import Any, Callable, Dict, Optional, Union
from datetime import datetime

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from app.core.logger import get_logger

# 导入共享的响应格式常量
import sys
import os

# 获取项目根目录的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

# 添加项目根目录到Python路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 添加shared目录到Python路径
shared_dir = os.path.join(project_root, 'shared')
if shared_dir not in sys.path:
    sys.path.insert(0, shared_dir)

try:
    from shared.constants.response import (
        BaseResponse,
        SuccessResponse,
        ErrorResponse,
        InternalServerErrorResponse,
        ErrorCode,
        create_success_response,
        create_error_response
    )
    logger = get_logger(__name__)
except ImportError as e:
    # 如果shared模块不可用，使用本地定义
    print(f"Warning: Could not import shared constants: {e}")

    # 本地定义基本响应格式
    from enum import Enum
    from typing import Any, Dict, Optional
    from datetime import datetime
    import uuid

    class ErrorCode(str, Enum):
        UNKNOWN_ERROR = "UNKNOWN_ERROR"
        INVALID_REQUEST = "INVALID_REQUEST"
        VALIDATION_ERROR = "VALIDATION_ERROR"
        UNAUTHORIZED = "UNAUTHORIZED"
        FORBIDDEN = "FORBIDDEN"
        RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
        INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
        EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
        NETWORK_ERROR = "NETWORK_ERROR"
        TIMEOUT_ERROR = "TIMEOUT_ERROR"
        SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
        OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
        RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
        FILE_TOO_LARGE = "FILE_TOO_LARGE"
        UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
        RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    class BaseResponse:
        def __init__(self, success: bool, message: str, data: Any = None, error: Optional[Dict[str, Any]] = None,
                     status_code: int = 200, request_id: Optional[str] = None, timestamp: Optional[datetime] = None):
            self.success = success
            self.message = message
            self.data = data
            self.error = error
            self.status_code = status_code
            self.request_id = request_id or str(uuid.uuid4())
            self.timestamp = timestamp or datetime.utcnow()

        def to_dict(self) -> Dict[str, Any]:
            result = {
                "success": self.success,
                "message": self.message,
                "timestamp": self.timestamp.isoformat(),
                "requestId": self.request_id,
                "statusCode": self.status_code
            }
            if self.data is not None:
                result["data"] = self.data
            if self.error:
                result["error"] = self.error
            return result

    class SuccessResponse(BaseResponse):
        def __init__(self, data: Any = None, message: str = "操作成功", status_code: int = 200, **kwargs):
            super().__init__(success=True, message=message, data=data, status_code=status_code, **kwargs)

    class ErrorResponse(BaseResponse):
        def __init__(self, error_code: ErrorCode, message: str, details: Optional[Dict[str, Any]] = None,
                     status_code: int = 400, cause: Optional[str] = None, **kwargs):
            error = {
                "code": error_code.value,
                "message": message,
                "details": details or {}
            }
            if cause:
                error["cause"] = cause
            super().__init__(success=False, message=message, error=error, status_code=status_code, **kwargs)

    class InternalServerErrorResponse(ErrorResponse):
        def __init__(self, message: str = "服务器内部错误", details: Optional[Dict[str, Any]] = None,
                     cause: Optional[str] = None, **kwargs):
            super().__init__(error_code=ErrorCode.INTERNAL_SERVER_ERROR, message=message,
                           details=details, status_code=500, cause=cause, **kwargs)

    def create_success_response(data: Any = None, message: str = "操作成功", status_code: int = 200, **kwargs) -> SuccessResponse:
        return SuccessResponse(data=data, message=message, status_code=status_code, **kwargs)

    def create_error_response(error_code: ErrorCode, message: str, details: Optional[Dict[str, Any]] = None,
                            status_code: int = 400, **kwargs) -> ErrorResponse:
        return ErrorResponse(error_code=error_code, message=message, details=details, status_code=status_code, **kwargs)

    # 创建一个简单的logger替代品
    class MockLogger:
        def info(self, msg, **kwargs): print(f"INFO: {msg}")
        def warning(self, msg, **kwargs): print(f"WARNING: {msg}")
        def error(self, msg, **kwargs): print(f"ERROR: {msg}")
        def debug(self, msg, **kwargs): print(f"DEBUG: {msg}")

    logger = MockLogger()


class ResponseMiddleware(BaseHTTPMiddleware):
    """统一响应格式中间件"""

    def __init__(self, app, debug: bool = False):
        super().__init__(app)
        self.debug = debug

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并统一响应格式

        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件或路由处理器

        Returns:
            统一格式的响应对象
        """
        start_time = datetime.utcnow()

        try:
            # 调用下一个中间件或路由处理器
            response = await call_next(request)

            # 如果已经是StreamingResponse，直接返回
            if isinstance(response, StreamingResponse):
                return response

            # 如果响应已经是JSON格式且符合我们的规范，直接返回
            if (hasattr(response, 'headers') and
                response.headers.get('content-type', '').startswith('application/json')):
                try:
                    # 对于已经是我们的响应格式的，不做处理
                    if hasattr(response, 'body'):
                        body = response.body
                        if isinstance(body, bytes):
                            body_str = body.decode('utf-8')
                        else:
                            body_str = body

                        # 检查是否已经是标准格式
                        if body_str and ('"success":' in body_str or '"statusCode":' in body_str):
                            return response
                except Exception:
                    pass  # 解析失败，继续处理

            # 计算处理时间
            process_time = (datetime.utcnow() - start_time).total_seconds()

            # 包装为统一格式
            if hasattr(response, 'status_code'):
                status_code = response.status_code
            else:
                status_code = 200

            # 如果是2xx状态码，包装为成功响应
            if 200 <= status_code < 300:
                try:
                    # 尝试解析响应内容
                    if hasattr(response, 'body'):
                        content = response.body
                        if isinstance(content, bytes):
                            content = content.decode('utf-8')

                        # 如果内容已经是JSON，解析它
                        if content and content.strip():
                            try:
                                data = json.loads(content)
                            except (json.JSONDecodeError, TypeError):
                                # 如果不是JSON，作为字符串处理
                                data = content
                        else:
                            data = None

                        # 创建成功响应
                        unified_response = SuccessResponse(
                            data=data,
                            message="操作成功",
                            status_code=status_code,
                            request_id=self._get_request_id(request)
                        )

                        return JSONResponse(
                            content=unified_response.to_dict(),
                            status_code=status_code
                        )

                except Exception as e:
                    logger.warning(f"Failed to process response body: {e}")

            # 对于非成功响应，创建错误响应
            unified_response = ErrorResponse(
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                message=f"HTTP {status_code}",
                status_code=status_code,
                request_id=self._get_request_id(request)
            )

            return JSONResponse(
                content=unified_response.to_dict(),
                status_code=status_code
            )

        except HTTPException as http_exc:
            # 处理HTTP异常
            error_code = self._get_error_code_from_status(http_exc.status_code)
            unified_response = ErrorResponse(
                error_code=error_code,
                message=http_exc.detail,
                status_code=http_exc.status_code,
                request_id=self._get_request_id(request)
            )

            return JSONResponse(
                content=unified_response.to_dict(),
                status_code=http_exc.status_code
            )

        except Exception as exc:
            # 处理未捕获的异常
            logger.error(
                f"Unhandled exception in {request.method} {request.url}: {exc}",
                exc_info=True
            )

            # 记录异常详情
            error_details = {}
            if self.debug:
                error_details = {
                    "exceptionType": type(exc).__name__,
                    "exceptionMessage": str(exc),
                    "stackTrace": traceback.format_exc(),
                    "url": str(request.url),
                    "method": request.method,
                    "headers": dict(request.headers)
                }

            unified_response = InternalServerErrorResponse(
                message="服务器内部错误",
                details=error_details,
                cause=str(exc),
                request_id=self._get_request_id(request)
            )

            return JSONResponse(
                content=unified_response.to_dict(),
                status_code=500
            )

    def _get_request_id(self, request: Request) -> str:
        """获取或生成请求ID"""
        # 尝试从请求头获取请求ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = request.headers.get("request-id")

        # 如果没有，生成新的请求ID
        if not request_id:
            request_id = str(uuid.uuid4())

        return request_id

    def _get_error_code_from_status(self, status_code: int) -> ErrorCode:
        """根据HTTP状态码获取错误代码"""
        error_mapping = {
            400: ErrorCode.INVALID_REQUEST,
            401: ErrorCode.UNAUTHORIZED,
            403: ErrorCode.FORBIDDEN,
            404: ErrorCode.RESOURCE_NOT_FOUND,
            405: ErrorCode.OPERATION_NOT_ALLOWED,
            409: ErrorCode.RESOURCE_ALREADY_EXISTS,
            413: ErrorCode.FILE_TOO_LARGE,
            415: ErrorCode.UNSUPPORTED_FILE_TYPE,
            422: ErrorCode.VALIDATION_ERROR,
            429: ErrorCode.RATE_LIMIT_EXCEEDED,
            500: ErrorCode.INTERNAL_SERVER_ERROR,
            502: ErrorCode.EXTERNAL_SERVICE_ERROR,
            503: ErrorCode.SERVICE_UNAVAILABLE,
            504: ErrorCode.TIMEOUT_ERROR
        }

        return error_mapping.get(status_code, ErrorCode.UNKNOWN_ERROR)


class ExceptionHandlerMiddleware:
    """异常处理中间件辅助类"""

    @staticmethod
    def create_error_response(
        exc: Exception,
        request_id: Optional[str] = None,
        debug: bool = False
    ) -> ErrorResponse:
        """创建错误响应"""
        error_code = ErrorCode.INTERNAL_SERVER_ERROR
        message = "服务器内部错误"
        details = {}

        # 根据异常类型设置错误代码和消息
        if hasattr(exc, 'error_code'):
            error_code = ErrorCode(exc.error_code)
            message = str(exc)
        elif isinstance(exc, ValueError):
            error_code = ErrorCode.VALIDATION_ERROR
            message = str(exc)
        elif isinstance(exc, PermissionError):
            error_code = ErrorCode.FORBIDDEN
            message = "权限不足"
        elif isinstance(exc, FileNotFoundError):
            error_code = ErrorCode.RESOURCE_NOT_FOUND
            message = "资源未找到"
        elif isinstance(exc, TimeoutError):
            error_code = ErrorCode.TIMEOUT_ERROR
            message = "请求超时"

        # 在调试模式下添加详细信息
        if debug:
            details.update({
                "exceptionType": type(exc).__name__,
                "exceptionMessage": str(exc),
                "stackTrace": traceback.format_exc()
            })

        return ErrorResponse(
            error_code=error_code,
            message=message,
            details=details,
            request_id=request_id
        )


# 装饰器：统一响应格式
def unified_response(
    success_message: str = "操作成功",
    error_message: Optional[str] = None
):
    """
    统一响应格式装饰器

    Args:
        success_message: 成功消息
        error_message: 错误消息（可选）
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)

                # 如果结果已经是BaseResponse，直接返回
                if isinstance(result, BaseResponse):
                    return result

                # 否则包装为成功响应
                return create_success_response(
                    data=result,
                    message=success_message
                )

            except HTTPException:
                # HTTP异常由中间件处理
                raise

            except Exception as exc:
                # 其他异常包装为错误响应
                logger.error(f"Error in {func.__name__}: {exc}", exc_info=True)

                error_code = ErrorCode.INTERNAL_SERVER_ERROR
                if hasattr(exc, 'error_code'):
                    error_code = ErrorCode(exc.error_code)

                return create_error_response(
                    error_code=error_code,
                    message=error_message or str(exc),
                    details={"function": func.__name__} if isinstance(exc, Exception) else None
                )

        return wrapper
    return decorator


# 装饰器：分页响应
def paginated_response(
    message: str = "获取数据成功"
):
    """
    分页响应格式装饰器

    Args:
        message: 成功消息
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # 如果结果已经是分页响应，直接返回
            if hasattr(result, 'to_dict') and hasattr(result, 'pagination'):
                return result

            # 如果结果是字典且包含pagination字段
            if isinstance(result, dict) and 'pagination' in result:
                data = result.get('data', [])
                pagination = result['pagination']

                try:
                    from shared.constants.response import PaginationResponse
                    return PaginationResponse(
                        data=data,
                        pagination=pagination,
                        message=message
                    )
                except ImportError:
                    # 如果没有PaginationResponse，使用普通成功响应
                    return create_success_response(
                        data=result,
                        message=message
                    )

            # 否则包装为普通成功响应
            return create_success_response(
                data=result,
                message=message
            )

        return wrapper
    return decorator