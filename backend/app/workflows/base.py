"""
工作流基类
CPG2PVG-AI System Workflow Base
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime
import time
import psutil
import traceback

from app.workflows.types import (
    ProcessingContext,
    ProcessingResult,
    WorkflowState,
    ProcessingStatus,
    ContentType,
)

logger = logging.getLogger(__name__)


class BaseWorkflowNode(ABC):
    """工作流节点基类"""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    @abstractmethod
    async def execute(
        self,
        context: ProcessingContext,
        input_data: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[ProcessingResult, None]:
        """
        执行工作流节点

        Args:
            context: 处理上下文
            input_data: 输入数据

        Yields:
            ProcessingResult: 处理结果
        """
        pass

    async def execute_with_monitoring(
        self,
        context: ProcessingContext,
        input_data: Optional[Dict[str, Any]] = None
    ) -> List[ProcessingResult]:
        """带监控的执行方法"""
        self.start_time = time.time()
        results = []

        try:
            # 开始执行
            logger.info(f"开始执行工作流节点: {self.name}")
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

            # 执行节点
            async for result in self.execute(context, input_data):
                results.append(result)

                # 实时监控
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                if current_memory > start_memory + 100:  # 如果内存增长超过100MB
                    logger.warning(f"节点 {self.name} 内存使用较高: {current_memory:.1f}MB")

            self.end_time = time.time()
            execution_time = self.end_time - self.start_time

            logger.info(f"工作流节点 {self.name} 执行完成，耗时: {execution_time:.2f}秒")

            return results

        except Exception as e:
            self.end_time = time.time()
            execution_time = self.end_time - self.start_time if self.start_time else 0

            error_result = ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.FAILED,
                success=False,
                error_message=str(e),
                execution_time=execution_time,
                metadata={
                    "traceback": traceback.format_exc(),
                    "memory_usage": psutil.Process().memory_info().rss / 1024 / 1024,
                }
            )

            logger.error(f"工作流节点 {self.name} 执行失败: {str(e)}")
            return [error_result]

    def get_execution_info(self) -> Dict[str, Any]:
        """获取执行信息"""
        info = {
            "name": self.name,
            "description": self.description,
        }

        if self.start_time:
            info["start_time"] = self.start_time

        if self.end_time:
            info["end_time"] = self.end_time
            info["execution_time"] = self.end_time - self.start_time

        return info


class BaseWorkflowOrchestrator(ABC):
    """工作流编排器基类"""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.nodes: Dict[str, BaseWorkflowNode] = {}
        self.workflow_steps: List[str] = []

    def add_node(self, node: BaseWorkflowNode) -> None:
        """添加工作流节点"""
        self.nodes[node.name] = node

    def add_step(self, step_name: str) -> None:
        """添加工作流步骤"""
        if step_name not in self.nodes:
            raise ValueError(f"Node {step_name} not found")
        self.workflow_steps.append(step_name)

    def remove_step(self, step_name: str) -> None:
        """移除工作流步骤"""
        if step_name in self.workflow_steps:
            self.workflow_steps.remove(step_name)

    @abstractmethod
    async def execute_workflow(
        self,
        context: ProcessingContext,
        input_data: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """
        执行工作流

        Args:
            context: 处理上下文
            input_data: 输入数据

        Returns:
            WorkflowState: 工作流状态
        """
        pass

    async def execute_workflow_step(
        self,
        step_name: str,
        context: ProcessingContext,
        input_data: Optional[Dict[str, Any]] = None
    ) -> List[ProcessingResult]:
        """执行单个工作流步骤"""
        if step_name not in self.nodes:
            raise ValueError(f"Step {step_name} not found")

        node = self.nodes[step_name]

        try:
            logger.info(f"执行工作流步骤: {step_name}")
            results = await node.execute_with_monitoring(context, input_data)

            # 更新工作流状态
            if not all(result.success for result in results):
                logger.error(f"工作流步骤 {step_name} 执行失败")

            return results

        except Exception as e:
            logger.error(f"执行工作流步骤 {step_name} 时发生错误: {str(e)}")

            error_result = ProcessingResult(
                step_name=step_name,
                status=ProcessingStatus.FAILED,
                success=False,
                error_message=str(e),
                execution_time=0.0,
            )

            return [error_result]

    def get_workflow_info(self) -> Dict[str, Any]:
        """获取工作流信息"""
        return {
            "name": self.name,
            "description": self.description,
            "nodes": list(self.nodes.keys()),
            "steps": self.workflow_steps,
            "total_steps": len(self.workflow_steps),
        }


class BaseProcessor(ABC):
    """基础处理器"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def process(self, data: Any, context: ProcessingContext) -> Any:
        """处理数据"""
        pass

    def validate_input(self, data: Any) -> bool:
        """验证输入数据"""
        return data is not None

    def log_processing(self, data_type: str, message: str) -> None:
        """记录处理日志"""
        logger.info(f"[{self.name}] {data_type}: {message}")


class BaseCache(ABC):
    """基础缓存接口"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存数据"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存数据"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        pass


class BaseMonitor(ABC):
    """基础监控接口"""

    @abstractmethod
    async def collect_metrics(self) -> Dict[str, Any]:
        """收集指标"""
        pass

    @abstractmethod
    async def record_event(self, event: str, data: Dict[str, Any]) -> None:
        """记录事件"""
        pass

    @abstractmethod
    async def check_alerts(self) -> List[Dict[str, Any]]:
        """检查告警"""
        pass


class BaseQualityController(ABC):
    """基础质量控制接口"""

    @abstractmethod
    async def validate_quality(
        self,
        content: str,
        context: ProcessingContext
    ) -> Dict[str, Any]:
        """验证内容质量"""
        pass

    @abstractmethod
    async def calculate_score(self, content: str) -> float:
        """计算质量分数"""
        pass

    @abstractmethod
    async def suggest_improvements(
        self,
        content: str,
        issues: List[str]
    ) -> List[str]:
        """建议改进措施"""
        pass


class BaseCostOptimizer(ABC):
    """基础成本优化接口"""

    @abstractmethod
    async def select_model(
        self,
        task_type: str,
        complexity: float,
        quality_requirement: str
    ) -> str:
        """选择模型"""
        pass

    @abstractmethod
    async def estimate_cost(self, model: str, tokens: int) -> float:
        """估算成本"""
        pass

    @abstractmethod
    async def optimize_usage(self, content: str) -> str:
        """优化使用"""
        pass


# 工具函数
def create_processing_result(
    step_name: str,
    status: ProcessingStatus,
    success: bool = True,
    data: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None,
    **kwargs
) -> ProcessingResult:
    """创建处理结果的便捷函数"""
    return ProcessingResult(
        step_name=step_name,
        status=status,
        success=success,
        data=data,
        error_message=message if not success else None,
        **kwargs
    )


def format_time(seconds: float) -> str:
    """格式化时间显示"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        return f"{seconds/60:.1f}分钟"
    else:
        return f"{seconds/3600:.1f}小时"


def format_cost(cost: float) -> str:
    """格式化成本显示"""
    if cost < 1:
        return f"${cost*1000:.1f}c"
    else:
        return f"${cost:.2f}"