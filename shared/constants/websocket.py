"""
WebSocket连接配置常量
WebSocket Connection Configuration Constants

这个文件定义了WebSocket连接相关的常量，确保前后端一致性
This file defines WebSocket connection related constants for frontend-backend consistency
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import time


class WebSocketMessageType(str, Enum):
    """WebSocket消息类型枚举"""
    # 连接管理
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    HEARTBEAT = "heartbeat"
    PING = "ping"
    PONG = "pong"

    # 认证相关
    AUTH = "auth"
    AUTH_RESPONSE = "auth_response"

    # 任务相关
    TASK_UPDATE = "task_update"
    TASK_PROGRESS = "task_progress"
    TASK_STATUS = "task_status"
    TASK_STEP = "task_step"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"

    # 工作流相关
    WORKFLOW_UPDATE = "workflow_update"
    WORKFLOW_PHASE = "workflow_phase"
    WORKFLOW_NODE = "workflow_node"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"

    # 系统相关
    SYSTEM_NOTIFICATION = "system_notification"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    # 文件相关
    FILE_UPLOAD_PROGRESS = "file_upload_progress"
    FILE_PROCESSING = "file_processing"
    FILE_COMPLETED = "file_completed"


class WebSocketConnectionStatus(str, Enum):
    """WebSocket连接状态枚举"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class WebSocketErrorCode(str, Enum):
    """WebSocket错误代码枚举"""
    CONNECTION_FAILED = "CONNECTION_FAILED"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    AUTHENTICATION_EXPIRED = "AUTHENTICATION_EXPIRED"
    CONNECTION_TIMEOUT = "CONNECTION_TIMEOUT"
    CONNECTION_LOST = "CONNECTION_LOST"
    MAX_RECONNECT_ATTEMPTS_REACHED = "MAX_RECONNECT_ATTEMPTS_REACHED"
    INVALID_MESSAGE_FORMAT = "INVALID_MESSAGE_FORMAT"
    UNSUPPORTED_MESSAGE_TYPE = "UNSUPPORTED_MESSAGE_TYPE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SERVER_ERROR = "SERVER_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"


@dataclass
class WebSocketMessage:
    """WebSocket消息结构"""
    type: WebSocketMessageType
    data: Any = None
    timestamp: float = field(default_factory=time.time)
    message_id: str = field(default_factory=lambda: str(int(time.time() * 1000000)))
    request_id: Optional[str] = None
    error: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "messageId": self.message_id,
            "requestId": self.request_id,
            "error": self.error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebSocketMessage':
        """从字典创建消息对象"""
        return cls(
            type=WebSocketMessageType(data["type"]),
            data=data.get("data"),
            timestamp=data.get("timestamp", time.time()),
            message_id=data.get("messageId"),
            request_id=data.get("requestId"),
            error=data.get("error")
        )


@dataclass
class WebSocketConfig:
    """WebSocket连接配置"""
    # 连接配置
    url: str
    protocol: str = "ws"
    port: Optional[int] = None
    path: str = "/ws"

    # 重连配置
    auto_reconnect: bool = True
    max_reconnect_attempts: int = 5
    reconnect_interval: int = 3000  # 毫秒
    reconnect_backoff_factor: float = 1.5
    max_reconnect_interval: int = 30000  # 毫秒

    # 心跳配置
    enable_heartbeat: bool = True
    heartbeat_interval: int = 30000  # 毫秒
    heartbeat_timeout: int = 5000  # 毫秒
    heartbeat_retry_count: int = 3

    # 消息配置
    message_timeout: int = 10000  # 毫秒
    max_message_size: int = 1024 * 1024  # 1MB
    buffer_size: int = 8192

    # 认证配置
    auth_required: bool = True
    auth_timeout: int = 5000  # 毫秒
    token_refresh_threshold: int = 300000  # 5分钟

    # 性能配置
    compression: bool = True
    enable_statistics: bool = True
    connection_timeout: int = 10000  # 毫秒

    # 调试配置
    debug: bool = False
    log_messages: bool = False

    def get_websocket_url(self) -> str:
        """获取WebSocket URL"""
        url_parts = []

        if self.protocol:
            url_parts.append(self.protocol)

        if self.url.startswith(('http://', 'https://')):
            url_parts.append(self.url.split('://')[1])
        else:
            url_parts.append(self.url)

        if self.port:
            url_parts[-1] += f":{self.port}"

        url_parts.append(self.path)

        return ''.join(url_parts)


@dataclass
class ConnectionStatistics:
    """连接统计信息"""
    # 连接统计
    total_connections: int = 0
    successful_connections: int = 0
    failed_connections: int = 0
    reconnections: int = 0
    current_connections: int = 0

    # 消息统计
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0

    # 时间统计
    total_connection_time: float = 0.0
    average_connection_time: float = 0.0
    last_connection_time: Optional[float] = None
    last_message_time: Optional[float] = None

    # 错误统计
    connection_errors: int = 0
    message_errors: int = 0
    timeout_errors: int = 0
    auth_errors: int = 0

    def update_connection_time(self, duration: float):
        """更新连接时间统计"""
        self.total_connection_time += duration
        self.total_connections += 1
        self.average_connection_time = self.total_connection_time / self.total_connections
        self.last_connection_time = time.time()

    def update_message_stats(self, bytes_count: int, is_sent: bool = True):
        """更新消息统计"""
        if is_sent:
            self.messages_sent += 1
            self.bytes_sent += bytes_count
        else:
            self.messages_received += 1
            self.bytes_received += bytes_count
        self.last_message_time = time.time()


# 默认配置
DEFAULT_WEBSOCKET_CONFIG = WebSocketConfig(
    url="localhost:8000",
    protocol="ws",
    path="/ws",
    auto_reconnect=True,
    max_reconnect_attempts=5,
    reconnect_interval=3000,
    enable_heartbeat=True,
    heartbeat_interval=30000,
    heartbeat_timeout=5000,
    auth_required=True,
    compression=True,
    debug=False
)

# 消息类型验证规则
MESSAGE_TYPE_VALIDATORS = {
    # 连接管理消息
    WebSocketMessageType.CONNECT: {
        "required_fields": ["data"],
        "optional_fields": ["requestId"],
        "data_schema": {"token": "string"}
    },

    WebSocketMessageType.HEARTBEAT: {
        "required_fields": [],
        "optional_fields": ["data", "requestId"],
        "data_schema": {}
    },

    # 任务相关消息
    WebSocketMessageType.TASK_UPDATE: {
        "required_fields": ["data"],
        "optional_fields": ["requestId"],
        "data_schema": {
            "taskId": "string",
            "status": "string",
            "progress": "number"
        }
    },

    # 错误消息
    WebSocketMessageType.ERROR: {
        "required_fields": ["data"],
        "optional_fields": ["requestId"],
        "data_schema": {
            "code": "string",
            "message": "string"
        }
    }
}


def validate_websocket_message(message: WebSocketMessage) -> tuple[bool, Optional[str]]:
    """
    验证WebSocket消息格式

    Args:
        message: WebSocket消息对象

    Returns:
        (is_valid, error_message)
    """
    # 检查消息类型
    if message.type not in MESSAGE_TYPE_VALIDATORS:
        return False, f"Unsupported message type: {message.type}"

    validator = MESSAGE_TYPE_VALIDATORS[message.type]

    # 检查必需字段
    for field in validator["required_fields"]:
        if not hasattr(message, field) or getattr(message, field) is None:
            return False, f"Missing required field: {field}"

    # 检查数据结构
    if message.data and "data_schema" in validator:
        schema = validator["data_schema"]
        for field, field_type in schema.items():
            if not isinstance(message.data, dict) or field not in message.data:
                return False, f"Missing required data field: {field}"

            if field_type == "string" and not isinstance(message.data[field], str):
                return False, f"Invalid type for field {field}: expected {field_type}"
            elif field_type == "number" and not isinstance(message.data[field], (int, float)):
                return False, f"Invalid type for field {field}: expected {field_type}"

    return True, None


def create_heartbeat_message() -> WebSocketMessage:
    """创建心跳消息"""
    return WebSocketMessage(
        type=WebSocketMessageType.HEARTBEAT,
        data={"timestamp": time.time()}
    )


def create_auth_message(token: str) -> WebSocketMessage:
    """创建认证消息"""
    return WebSocketMessage(
        type=WebSocketMessageType.AUTH,
        data={"token": token}
    )


def create_task_update_message(
    task_id: str,
    status: str,
    progress: Optional[float] = None,
    data: Optional[Dict[str, Any]] = None
) -> WebSocketMessage:
    """创建任务更新消息"""
    message_data = {
        "taskId": task_id,
        "status": status
    }

    if progress is not None:
        message_data["progress"] = progress

    if data:
        message_data.update(data)

    return WebSocketMessage(
        type=WebSocketMessageType.TASK_UPDATE,
        data=message_data
    )


def create_error_message(
    error_code: str,
    error_message: str,
    details: Optional[Dict[str, Any]] = None
) -> WebSocketMessage:
    """创建错误消息"""
    error_data = {
        "code": error_code,
        "message": error_message
    }

    if details:
        error_data["details"] = details

    return WebSocketMessage(
        type=WebSocketMessageType.ERROR,
        data=error_data
    )


# 连接质量指标
@dataclass
class ConnectionQuality:
    """连接质量指标"""
    latency: float = 0.0  # 延迟 (毫秒)
    packet_loss: float = 0.0  # 丢包率 (百分比)
    jitter: float = 0.0  # 抖动 (毫秒)
    bandwidth: float = 0.0  # 带宽 (kbps)
    quality_score: float = 100.0  # 质量评分 (0-100)

    def update_quality_score(self):
        """更新质量评分"""
        # 基于延迟、丢包率和抖动计算质量评分
        latency_factor = max(0, 100 - self.latency / 10)  # 延迟因子
        packet_loss_factor = max(0, 100 - self.packet_loss * 2)  # 丢包率因子
        jitter_factor = max(0, 100 - self.jitter / 5)  # 抖动因子

        self.quality_score = (latency_factor + packet_loss_factor + jitter_factor) / 3


# 导出主要类型和配置
__all__ = [
    'WebSocketMessageType',
    'WebSocketConnectionStatus',
    'WebSocketErrorCode',
    'WebSocketMessage',
    'WebSocketConfig',
    'ConnectionStatistics',
    'ConnectionQuality',
    'DEFAULT_WEBSOCKET_CONFIG',
    'MESSAGE_TYPE_VALIDATORS',
    'validate_websocket_message',
    'create_heartbeat_message',
    'create_auth_message',
    'create_task_update_message',
    'create_error_message'
]