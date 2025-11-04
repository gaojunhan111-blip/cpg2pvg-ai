"""
API版本控制常量
API Version Control Constants

这个文件定义了API版本控制相关的常量，确保前后端一致性
This file defines API version control related constants for frontend-backend consistency
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime


class APIVersion(str, Enum):
    """API版本枚举"""
    V1 = "v1"
    V2 = "v2"  # 未来版本
    LATEST = "latest"
    LEGACY = "legacy"


class APIStatus(str, Enum):
    """API状态枚举"""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"
    BETA = "beta"
    ALPHA = "alpha"


class HTTPMethod(str, Enum):
    """HTTP方法枚举"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ResponseFormat(str, Enum):
    """响应格式枚举"""
    JSON = "json"
    XML = "xml"
    YAML = "yaml"
    CSV = "csv"
    HTML = "html"
    PLAIN = "plain"


@dataclass
class APIEndpoint:
    """API端点定义"""
    path: str
    method: HTTPMethod
    version: APIVersion
    description: str
    parameters: List[Dict[str, Any]] = None
    responses: Dict[str, Any] = None
    deprecated: bool = False
    deprecated_since: Optional[APIVersion] = None
    sunset_date: Optional[datetime] = None
    alternatives: List[str] = None
    tags: List[str] = None
    security: List[str] = None
    rate_limit: Optional[Dict[str, Any]] = None
    cache_ttl: Optional[int] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []
        if self.responses is None:
            self.responses = {}
        if self.alternatives is None:
            self.alternatives = []
        if self.tags is None:
            self.tags = []
        if self.security is None:
            self.security = []


@dataclass
class APIVersionInfo:
    """API版本信息"""
    version: APIVersion
    status: APIStatus
    release_date: datetime
    sunset_date: Optional[datetime] = None
    deprecation_date: Optional[datetime] = None
    description: str = ""
    changelog: List[str] = None
    breaking_changes: List[str] = None
    new_features: List[str] = None
    bug_fixes: List[str] = None
    supported_formats: List[ResponseFormat] = None
    base_path: str = ""

    def __post_init__(self):
        if self.changelog is None:
            self.changelog = []
        if self.breaking_changes is None:
            self.breaking_changes = []
        if self.new_features is None:
            self.new_features = []
        if self.bug_fixes is None:
            self.bug_fixes = []
        if self.supported_formats is None:
            self.supported_formats = [ResponseFormat.JSON]


@dataclass
class APIConfig:
    """API配置"""
    default_version: APIVersion = APIVersion.V1
    supported_versions: List[APIVersion] = None
    version_header: str = "X-API-Version"
    format_header: str = "Accept"
    version_param: str = "version"
    format_param: str = "format"
    enable_version_negotiation: bool = True
    enable_format_negotiation: bool = True
    strict_versioning: bool = False
    deprecated_version_grace_period: int = 90  # 天数

    def __post_init__(self):
        if self.supported_versions is None:
            self.supported_versions = [APIVersion.V1]


# API版本信息定义
API_VERSIONS: Dict[APIVersion, APIVersionInfo] = {
    APIVersion.V1: APIVersionInfo(
        version=APIVersion.V1,
        status=APIStatus.ACTIVE,
        release_date=datetime(2024, 1, 1),
        description="第一版API，提供核心功能",
        changelog=[
            "初始版本发布",
            "支持指南上传和处理",
            "支持任务管理",
            "支持用户认证"
        ],
        new_features=[
            "文件上传和处理",
            "任务进度跟踪",
            "用户认证和授权",
            "WebSocket实时通信"
        ],
        supported_formats=[ResponseFormat.JSON, ResponseFormat.XML],
        base_path="/api/v1"
    ),

    APIVersion.V2: APIVersionInfo(
        version=APIVersion.V2,
        status=APIStatus.BETA,
        release_date=datetime(2024, 6, 1),
        description="第二版API，增强功能和性能",
        changelog=[
            "新增批量操作支持",
            "优化响应格式",
            "增强错误处理",
            "改进认证机制"
        ],
        breaking_changes=[
            "更改了响应格式结构",
            "移除了部分deprecated端点",
            "修改了认证流程"
        ],
        new_features=[
            "批量文件处理",
            "GraphQL支持",
            "高级搜索功能",
            "增强的缓存机制"
        ],
        supported_formats=[ResponseFormat.JSON, ResponseFormat.XML, ResponseFormat.YAML],
        base_path="/api/v2"
    ),

    APIVersion.LATEST: APIVersionInfo(
        version=APIVersion.LATEST,
        status=APIStatus.ACTIVE,
        release_date=datetime(2024, 6, 1),
        description="最新稳定版API",
        supported_formats=[ResponseFormat.JSON],
        base_path="/api/latest"
    ),

    APIVersion.LEGACY: APIVersionInfo(
        version=APIVersion.LEGACY,
        status=APIStatus.SUNSET,
        release_date=datetime(2023, 1, 1),
        deprecation_date=datetime(2024, 1, 1),
        sunset_date=datetime(2024, 12, 31),
        description="旧版API，即将停止支持",
        changelog=[
            "初始版本"
        ],
        breaking_changes=[
            "不再维护"
        ],
        supported_formats=[ResponseFormat.JSON],
        base_path="/api/legacy"
    )
}

# API端点定义
API_ENDPOINTS: Dict[str, List[APIEndpoint]] = {
    "v1": [
        # 认证相关
        APIEndpoint(
            path="/auth/login",
            method=HTTPMethod.POST,
            version=APIVersion.V1,
            description="用户登录",
            tags=["authentication"],
            cache_ttl=0
        ),
        APIEndpoint(
            path="/auth/logout",
            method=HTTPMethod.POST,
            version=APIVersion.V1,
            description="用户登出",
            tags=["authentication"],
            security=["jwt"],
            cache_ttl=0
        ),
        APIEndpoint(
            path="/auth/refresh",
            method=HTTPMethod.POST,
            version=APIVersion.V1,
            description="刷新访问令牌",
            tags=["authentication"],
            cache_ttl=0
        ),

        # 指南管理
        APIEndpoint(
            path="/guidelines",
            method=HTTPMethod.GET,
            version=APIVersion.V1,
            description="获取指南列表",
            parameters=[
                {"name": "page", "type": "integer", "default": 1},
                {"name": "size", "type": "integer", "default": 10},
                {"name": "search", "type": "string"},
                {"name": "status", "type": "string"}
            ],
            tags=["guidelines"],
            cache_ttl=300
        ),
        APIEndpoint(
            path="/guidelines",
            method=HTTPMethod.POST,
            version=APIVersion.V1,
            description="上传指南",
            tags=["guidelines"],
            security=["jwt"],
            cache_ttl=0
        ),
        APIEndpoint(
            path="/guidelines/{id}",
            method=HTTPMethod.GET,
            version=APIVersion.V1,
            description="获取指南详情",
            tags=["guidelines"],
            cache_ttl=600
        ),
        APIEndpoint(
            path="/guidelines/{id}",
            method=HTTPMethod.PUT,
            version=APIVersion.V1,
            description="更新指南",
            tags=["guidelines"],
            security=["jwt"],
            cache_ttl=0
        ),
        APIEndpoint(
            path="/guidelines/{id}",
            method=HTTPMethod.DELETE,
            version=APIVersion.V1,
            description="删除指南",
            tags=["guidelines"],
            security=["jwt"],
            cache_ttl=0
        ),

        # 任务管理
        APIEndpoint(
            path="/tasks",
            method=HTTPMethod.GET,
            version=APIVersion.V1,
            description="获取任务列表",
            tags=["tasks"],
            security=["jwt"],
            cache_ttl=60
        ),
        APIEndpoint(
            path="/tasks/{id}",
            method=HTTPMethod.GET,
            version=APIVersion.V1,
            description="获取任务详情",
            tags=["tasks"],
            security=["jwt"],
            cache_ttl=30
        ),
        APIEndpoint(
            path="/tasks/{id}/stream",
            method=HTTPMethod.GET,
            version=APIVersion.V1,
            description="任务进度流",
            tags=["tasks"],
            security=["jwt"],
            cache_ttl=0
        ),

        # 文件管理
        APIEndpoint(
            path="/files/upload",
            method=HTTPMethod.POST,
            version=APIVersion.V1,
            description="文件上传",
            tags=["files"],
            security=["jwt"],
            cache_ttl=0
        ),
        APIEndpoint(
            path="/files/{id}",
            method=HTTPMethod.GET,
            version=APIVersion.V1,
            description="文件下载",
            tags=["files"],
            security=["jwt"],
            cache_ttl=3600
        ),

        # 工作流管理
        APIEndpoint(
            path="/workflow/upload",
            method=HTTPMethod.POST,
            version=APIVersion.V1,
            description="工作流文件上传",
            tags=["workflow"],
            security=["jwt"],
            cache_ttl=0
        ),
        APIEndpoint(
            path="/workflow/{id}/status",
            method=HTTPMethod.GET,
            version=APIVersion.V1,
            description="获取工作流状态",
            tags=["workflow"],
            security=["jwt"],
            cache_ttl=30
        ),
        APIEndpoint(
            path="/workflow/{id}/stream",
            method=HTTPMethod.GET,
            version=APIVersion.V1,
            description="工作流进度流",
            tags=["workflow"],
            security=["jwt"],
            cache_ttl=0
        )
    ]
}

# HTTP状态码映射
HTTP_STATUS_MAPPING: Dict[int, str] = {
    100: "Continue",
    101: "Switching Protocols",
    102: "Processing",
    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-Authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    306: "Unused",
    307: "Temporary Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Payload Too Large",
    414: "URI Too Long",
    415: "Unsupported Media Type",
    416: "Requested Range Not Satisfiable",
    417: "Expectation Failed",
    422: "Unprocessable Entity",
    423: "Locked",
    424: "Failed Dependency",
    426: "Upgrade Required",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported"
}

# 内容类型映射
CONTENT_TYPE_MAPPING: Dict[ResponseFormat, str] = {
    ResponseFormat.JSON: "application/json",
    ResponseFormat.XML: "application/xml",
    ResponseFormat.YAML: "application/x-yaml",
    ResponseFormat.CSV: "text/csv",
    ResponseFormat.HTML: "text/html",
    ResponseFormat.PLAIN: "text/plain"
}

# 缓存策略
CACHE_STRATEGIES = {
    "no_cache": {"max_age": 0, "no_store": True},
    "short": {"max_age": 60, "no_store": False},
    "medium": {"max_age": 300, "no_store": False},
    "long": {"max_age": 3600, "no_store": False},
    "extended": {"max_age": 86400, "no_store": False}
}

# 速率限制策略
RATE_LIMIT_STRATEGIES = {
    "none": {"requests": 0, "window": 0},
    "low": {"requests": 100, "window": 3600},
    "medium": {"requests": 1000, "window": 3600},
    "high": {"requests": 10000, "window": 3600},
    "strict": {"requests": 100, "window": 60}
}

def get_api_version_info(version: APIVersion) -> Optional[APIVersionInfo]:
    """获取API版本信息"""
    return API_VERSIONS.get(version)

def is_version_supported(version: APIVersion) -> bool:
    """检查版本是否支持"""
    version_info = get_api_version_info(version)
    if not version_info:
        return False
    return version_info.status in [APIStatus.ACTIVE, APIStatus.BETA]

def get_latest_version() -> APIVersion:
    """获取最新版本"""
    active_versions = [
        version for version, info in API_VERSIONS.items()
        if info.status == APIStatus.ACTIVE
    ]
    return max(active_versions, key=lambda v: v.value) if active_versions else APIVersion.V1

def get_base_path(version: APIVersion) -> str:
    """获取版本的基础路径"""
    version_info = get_api_version_info(version)
    return version_info.base_path if version_info else f"/api/{version.value}"

def resolve_version(
    requested_version: Optional[str],
    header_version: Optional[str],
    default_version: APIVersion = APIVersion.V1
) -> APIVersion:
    """解析API版本"""
    # 优先级：参数 > 请求头 > 默认版本
    version_str = requested_version or header_version

    if not version_str:
        return default_version

    # 特殊值处理
    if version_str.lower() == "latest":
        return get_latest_version()

    try:
        version = APIVersion(version_str.lower())
        if is_version_supported(version):
            return version
    except ValueError:
        pass

    # 版本无效，返回默认版本
    return default_version

def resolve_format(
    accept_header: Optional[str],
    format_param: Optional[str],
    default_format: ResponseFormat = ResponseFormat.JSON
) -> ResponseFormat:
    """解析响应格式"""
    # 优先级：参数 > Accept头 > 默认格式
    if format_param:
        try:
            return ResponseFormat(format_param.lower())
        except ValueError:
            pass

    if accept_header:
        # 解析Accept头
        for media_range in accept_header.split(','):
            media_range = media_range.strip()
            for format_type, content_type in CONTENT_TYPE_MAPPING.items():
                if content_type in media_range:
                    return format_type

    return default_format

def get_deprecation_headers(version_info: APIVersionInfo) -> Dict[str, str]:
    """获取弃用相关的响应头"""
    headers = {}

    if version_info.status == APIStatus.DEPRECATED:
        headers["Deprecation"] = "true"
        if version_info.deprecation_date:
            headers["Sunset"] = version_info.deprecation_date.strftime("%a, %d %b %Y %H:%M:%S GMT")

    if version_info.alternatives:
        headers["Link"] = ", ".join([
            f'<{alt}>; rel="alternate"' for alt in version_info.alternatives
        ])

    return headers

# 导出主要类型和常量
__all__ = [
    'APIVersion',
    'APIStatus',
    'HTTPMethod',
    'ResponseFormat',
    'APIEndpoint',
    'APIVersionInfo',
    'APIConfig',
    'API_VERSIONS',
    'API_ENDPOINTS',
    'HTTP_STATUS_MAPPING',
    'CONTENT_TYPE_MAPPING',
    'CACHE_STRATEGIES',
    'RATE_LIMIT_STRATEGIES',
    'get_api_version_info',
    'is_version_supported',
    'get_latest_version',
    'get_base_path',
    'resolve_version',
    'resolve_format',
    'get_deprecation_headers'
]