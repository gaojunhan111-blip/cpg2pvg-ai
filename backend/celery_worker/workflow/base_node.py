"""
工作流基类定义
Workflow Base Node Definition
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from app.core.logger import get_logger

logger = get_logger(__name__)


class NodeStatus(str, Enum):
    """节点状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class NodePriority(str, Enum):
    """节点优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class NodeResult:
    """节点执行结果"""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    warning: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class NodeContext:
    """节点执行上下文"""
    workflow_id: str
    task_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    start_time: datetime = None
    timeout: int = 3600  # 1小时默认超时
    priority: NodePriority = NodePriority.MEDIUM
    metadata: Dict[str, Any] = None
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


class BaseWorkflowNode(ABC):
    """工作流节点基类"""

    def __init__(self, node_id: str, node_name: str, description: str = ""):
        self.node_id = node_id
        self.node_name = node_name
        self.description = description
        self.status = NodeStatus.PENDING
        self.result: Optional[NodeResult] = None
        self.context: Optional[NodeContext] = None
        self.execution_start_time: Optional[datetime] = None

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行节点逻辑"""
        pass

    async def validate_input(self, context: Dict[str, Any]) -> bool:
        """验证输入参数"""
        return True

    async def get_estimated_duration(self, context: Dict[str, Any]) -> int:
        """估算执行时间（秒）"""
        return 300  # 默认5分钟

    def get_resource_requirements(self) -> Dict[str, Any]:
        """获取资源需求"""
        return {
            "memory_mb": 256,
            "cpu_cores": 1,
            "gpu_required": False,
            "storage_mb": 50,
            "network_required": False
        }

    async def pre_execute(self, context: Dict[str, Any]) -> bool:
        """执行前准备"""
        self.status = NodeStatus.RUNNING
        self.execution_start_time = datetime.utcnow()

        # 创建上下文
        self.context = NodeContext(
            workflow_id=context.get("workflow_id", str(uuid.uuid4())),
            task_id=context.get("task_id", str(uuid.uuid4())),
            user_id=context.get("user_id"),
            session_id=context.get("session_id"),
            priority=NodePriority(context.get("priority", "medium")),
            timeout=context.get("timeout", 3600)
        )

        logger.info(f"[{self.node_id}] 开始执行节点")
        return True

    async def post_execute(self, result: Dict[str, Any]) -> NodeResult:
        """执行后处理"""
        execution_time = 0.0
        if self.execution_start_time:
            execution_time = (datetime.utcnow() - self.execution_start_time).total_seconds()

        if result.get("success", False):
            self.status = NodeStatus.COMPLETED
            node_result = NodeResult(
                success=True,
                data=result,
                execution_time=execution_time
            )
        else:
            self.status = NodeStatus.FAILED
            node_result = NodeResult(
                success=False,
                data=result,
                error=result.get("error", "未知错误"),
                execution_time=execution_time
            )

        self.result = node_result
        logger.info(f"[{self.node_id}] 节点执行完成，状态: {self.status.value}")

        return node_result

    async def handle_timeout(self) -> Dict[str, Any]:
        """处理超时"""
        self.status = NodeStatus.TIMEOUT
        return {
            "success": False,
            "error": f"节点执行超时 ({self.context.timeout}秒)",
            "timeout": self.context.timeout
        }

    async def handle_error(self, error: Exception) -> Dict[str, Any]:
        """处理错误"""
        self.status = NodeStatus.FAILED
        logger.error(f"[{self.node_id}] 节点执行错误: {str(error)}")

        return {
            "success": False,
            "error": str(error),
            "error_type": type(error).__name__
        }

    async def retry(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """重试执行"""
        if self.context and self.context.retry_count >= self.context.max_retries:
            return {
                "success": False,
                "error": f"已达到最大重试次数 ({self.context.max_retries})"
            }

        if self.context:
            self.context.retry_count += 1

        logger.info(f"[{self.node_id}] 重试执行 (第{self.context.retry_count}次)")

        try:
            # 清理之前的状态
            self.status = NodeStatus.PENDING
            self.result = None
            self.execution_start_time = None

            # 重新执行
            return await self.execute(context)

        except Exception as e:
            return await self.handle_error(e)

    async def run(self, context: Dict[str, Any]) -> NodeResult:
        """运行节点（完整的执行流程）"""
        try:
            # 执行前准备
            if not await self.pre_execute(context):
                return NodeResult(
                    success=False,
                    data={},
                    error="执行前准备失败"
                )

            # 验证输入
            if not await self.validate_input(context):
                return NodeResult(
                    success=False,
                    data={},
                    error="输入验证失败"
                )

            # 检查超时
            if self.context and self.context.timeout:
                estimated_duration = await self.get_estimated_duration(context)
                if estimated_duration > self.context.timeout:
                    return NodeResult(
                        success=False,
                        data=await self.handle_timeout()
                    )

            # 执行节点逻辑
            try:
                result_data = await self.execute(context)

                # 执行后处理
                return await self.post_execute(result_data)

            except TimeoutError:
                timeout_result = await self.handle_timeout()
                return NodeResult(
                    success=False,
                    data=timeout_result,
                    error="执行超时"
                )

            except Exception as e:
                error_result = await self.handle_error(e)
                return NodeResult(
                    success=False,
                    data=error_result,
                    error=str(e)
                )

        except Exception as e:
            logger.error(f"[{self.node_id}] 节点运行失败: {str(e)}")
            return NodeResult(
                success=False,
                data={},
                error=str(e)
            )

    def get_status(self) -> NodeStatus:
        """获取节点状态"""
        return self.status

    def get_result(self) -> Optional[NodeResult]:
        """获取执行结果"""
        return self.result

    def get_context(self) -> Optional[NodeContext]:
        """获取执行上下文"""
        return self.context

    def reset(self):
        """重置节点状态"""
        self.status = NodeStatus.PENDING
        self.result = None
        self.context = None
        self.execution_start_time = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "description": self.description,
            "status": self.status.value,
            "result": {
                "success": self.result.success,
                "error": self.result.error,
                "warning": self.result.warning,
                "execution_time": self.result.execution_time,
                "metadata": self.result.metadata
            } if self.result else None,
            "context": {
                "workflow_id": self.context.workflow_id,
                "task_id": self.context.task_id,
                "user_id": self.context.user_id,
                "start_time": self.context.start_time.isoformat() if self.context.start_time else None,
                "timeout": self.context.timeout,
                "priority": self.context.priority.value,
                "retry_count": self.context.retry_count,
                "max_retries": self.context.max_retries
            } if self.context else None,
            "execution_start_time": self.execution_start_time.isoformat() if self.execution_start_time else None
        }


class WorkflowError(Exception):
    """工作流错误"""
    pass


class NodeTimeoutError(WorkflowError):
    """节点超时错误"""
    pass


class NodeValidationError(WorkflowError):
    """节点验证错误"""
    pass


class NodeExecutionError(WorkflowError):
    """节点执行错误"""
    pass


# 便捷函数
def create_node_context(
    workflow_id: str,
    task_id: str,
    user_id: Optional[str] = None,
    timeout: int = 3600,
    priority: str = "medium",
    metadata: Optional[Dict[str, Any]] = None
) -> NodeContext:
    """创建节点上下文的便捷函数"""
    return NodeContext(
        workflow_id=workflow_id,
        task_id=task_id,
        user_id=user_id,
        timeout=timeout,
        priority=NodePriority(priority),
        metadata=metadata
    )