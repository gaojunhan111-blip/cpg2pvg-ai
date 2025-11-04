"""
统一响应格式定义
Unified Response Format Definition

这个文件定义了前后端共享的响应格式常量，确保一致性
This file defines shared response format constants for frontend-backend consistency
"""

from enum import Enum
from typing import Any, Dict, Optional, Union
from datetime import datetime
import uuid


class ResponseStatus(str, Enum):
    """响应状态枚举"""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    PENDING = "pending"


class ErrorCode(str, Enum):
    """错误代码枚举"""
    # 通用错误 (1000-1999)
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    INVALID_FORMAT = "INVALID_FORMAT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # 认证错误 (2000-2999)
    UNAUTHORIZED = "UNAUTHORIZED"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    FORBIDDEN = "FORBIDDEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"

    # 业务逻辑错误 (3000-3999)
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    INVALID_STATE = "INVALID_STATE"
    DUPLICATE_OPERATION = "DUPLICATE_OPERATION"

    # 文件处理错误 (4000-4999)
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    FILE_UPLOAD_FAILED = "FILE_UPLOAD_FAILED"
    FILE_PROCESSING_FAILED = "FILE_PROCESSING_FAILED"
    CORRUPTED_FILE = "CORRUPTED_FILE"

    # 系统错误 (5000-5999)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

    # 任务处理错误 (6000-6999)
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    TASK_FAILED = "TASK_FAILED"
    TASK_CANCELLED = "TASK_CANCELLED"
    TASK_TIMEOUT = "TASK_TIMEOUT"
    PROCESSING_ERROR = "PROCESSING_ERROR"


class BaseResponse:
    """基础响应类"""

    def __init__(
        self,
        success: bool,
        message: str,
        data: Any = None,
        error: Optional[Dict[str, Any]] = None,
        status_code: int = 200,
        request_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        self.success = success
        self.message = message
        self.data = data
        self.error = error
        self.status_code = status_code
        self.request_id = request_id or str(uuid.uuid4())
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
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
    """成功响应类"""

    def __init__(
        self,
        data: Any = None,
        message: str = "操作成功",
        status_code: int = 200,
        **kwargs
    ):
        super().__init__(
            success=True,
            message=message,
            data=data,
            status_code=status_code,
            **kwargs
        )


class ErrorResponse(BaseResponse):
    """错误响应类"""

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400,
        cause: Optional[str] = None,
        **kwargs
    ):
        error = {
            "code": error_code.value,
            "message": message,
            "details": details or {}
        }

        if cause:
            error["cause"] = cause

        super().__init__(
            success=False,
            message=message,
            error=error,
            status_code=status_code,
            **kwargs
        )


class ValidationErrorResponse(ErrorResponse):
    """验证错误响应类"""

    def __init__(
        self,
        field: str,
        message: str,
        value: Any = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        validation_details = details or {}
        validation_details["field"] = field
        if value is not None:
            validation_details["value"] = str(value)

        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=f"验证失败: {message}",
            details=validation_details,
            status_code=422,
            **kwargs
        )


class NotFoundResponse(ErrorResponse):
    """资源未找到响应类"""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        message: Optional[str] = None,
        **kwargs
    ):
        message = message or f"{resource_type}不存在: {resource_id}"
        details = {"resourceType": resource_type, "resourceId": resource_id}

        super().__init__(
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            message=message,
            details=details,
            status_code=404,
            **kwargs
        )


class UnauthorizedResponse(ErrorResponse):
    """未授权响应类"""

    def __init__(
        self,
        message: str = "未授权访问",
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(
            error_code=ErrorCode.UNAUTHORIZED,
            message=message,
            details=details,
            status_code=401,
            **kwargs
        )


class ForbiddenResponse(ErrorResponse):
    """禁止访问响应类"""

    def __init__(
        self,
        message: str = "权限不足",
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        error_details = details or {}
        if required_permission:
            error_details["requiredPermission"] = required_permission

        super().__init__(
            error_code=ErrorCode.FORBIDDEN,
            message=message,
            details=error_details,
            status_code=403,
            **kwargs
        )


class InternalServerErrorResponse(ErrorResponse):
    """服务器内部错误响应类"""

    def __init__(
        self,
        message: str = "服务器内部错误",
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=message,
            details=details,
            status_code=500,
            cause=cause,
            **kwargs
        )


class PaginationResponse(SuccessResponse):
    """分页响应类"""

    def __init__(
        self,
        data: Any,
        pagination: Dict[str, Any],
        message: str = "获取数据成功",
        **kwargs
    ):
        # 确保分页信息包含必要字段
        required_fields = ["current", "pageSize", "total", "totalPages"]
        for field in required_fields:
            if field not in pagination:
                raise ValueError(f"Pagination info missing required field: {field}")

        super().__init__(
            data=data,
            message=message,
            **kwargs
        )
        self.pagination = pagination

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = super().to_dict()
        result["pagination"] = self.pagination
        return result


class TaskResponse(SuccessResponse):
    """任务响应类"""

    def __init__(
        self,
        task_id: str,
        status: str,
        data: Any = None,
        message: str = "任务操作成功",
        progress: Optional[float] = None,
        estimated_time: Optional[int] = None,
        **kwargs
    ):
        task_data = {
            "taskId": task_id,
            "status": status
        }

        if progress is not None:
            task_data["progress"] = progress
        if estimated_time is not None:
            task_data["estimatedTime"] = estimated_time

        if data:
            task_data.update(data)

        super().__init__(
            data=task_data,
            message=message,
            **kwargs
        )


class FileUploadResponse(SuccessResponse):
    """文件上传响应类"""

    def __init__(
        self,
        file_info: Dict[str, Any],
        message: str = "文件上传成功",
        **kwargs
    ):
        super().__init__(
            data=file_info,
            message=message,
            **kwargs
        )


class ValidationErrorDict:
    """验证错误字典工具类"""

    @staticmethod
    def create(
        field: str,
        message: str,
        value: Any = None,
        code: str = "VALIDATION_ERROR"
    ) -> Dict[str, Any]:
        """创建验证错误字典"""
        error_dict = {
            "field": field,
            "message": message,
            "code": code
        }

        if value is not None:
            error_dict["value"] = str(value)

        return error_dict


# HTTP状态码映射
HTTP_STATUS_CODES = {
    # 成功
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",

    # 重定向
    301: "Moved Permanently",
    302: "Found",
    304: "Not Modified",

    # 客户端错误
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    413: "Payload Too Large",
    415: "Unsupported Media Type",
    422: "Unprocessable Entity",
    429: "Too Many Requests",

    # 服务器错误
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout"
}


# 响应创建工厂函数
def create_success_response(
    data: Any = None,
    message: str = "操作成功",
    status_code: int = 200,
    **kwargs
) -> SuccessResponse:
    """创建成功响应"""
    return SuccessResponse(
        data=data,
        message=message,
        status_code=status_code,
        **kwargs
    )


def create_error_response(
    error_code: ErrorCode,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 400,
    **kwargs
) -> ErrorResponse:
    """创建错误响应"""
    return ErrorResponse(
        error_code=error_code,
        message=message,
        details=details,
        status_code=status_code,
        **kwargs
    )


def create_validation_error(
    field: str,
    message: str,
    value: Any = None,
    details: Optional[Dict[str, Any]] = None,
    **kwargs
) -> ValidationErrorResponse:
    """创建验证错误响应"""
    return ValidationErrorResponse(
        field=field,
        message=message,
        value=value,
        details=details,
        **kwargs
    )


def create_not_found_response(
    resource_type: str,
    resource_id: str,
    message: Optional[str] = None,
    **kwargs
) -> NotFoundResponse:
    """创建资源未找到响应"""
    return NotFoundResponse(
        resource_type=resource_type,
        resource_id=resource_id,
        message=message,
        **kwargs
    )


def create_pagination_response(
    data: Any,
    pagination: Dict[str, Any],
    message: str = "获取数据成功",
    **kwargs
) -> PaginationResponse:
    """创建分页响应"""
    return PaginationResponse(
        data=data,
        pagination=pagination,
        message=message,
        **kwargs
    )