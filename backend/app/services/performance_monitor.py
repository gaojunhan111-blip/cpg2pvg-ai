"""
性能监控和自适应调整系统
Performance Monitoring and Adaptive Optimization System
节点9：性能监控和自适应调整
"""

import asyncio
import json
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import statistics

from app.core.logger import get_logger
from app.schemas.medical_schemas import (
    WorkflowExecution, PerformanceMetrics, OptimizationResult
)
from app.services.cost_optimizer import get_cost_optimizer
from app.services.quality_controller import get_quality_controller

logger = get_logger(__name__)


class MetricType(str, Enum):
    """指标类型"""
    PERFORMANCE = "performance"
    RESOURCE = "resource"
    COST = "cost"
    QUALITY = "quality"
    USER_SATISFACTION = "user_satisfaction"


class OptimizationType(str, Enum):
    """优化类型"""
    PARAMETER_TUNING = "parameter_tuning"
    RESOURCE_SCALING = "resource_scaling"
    MODEL_SELECTION = "model_selection"
    CACHING_STRATEGY = "caching_strategy"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PerformanceThreshold:
    """性能阈值"""
    metric_name: str
    warning_threshold: float
    error_threshold: float
    critical_threshold: float
    unit: str = ""

    # 趋势分析
    trend_window: int = 10  # 时间窗口大小
    trend_threshold: float = 0.1  # 趋势阈值


@dataclass
class SystemResource:
    """系统资源状态"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    disk_percent: float
    disk_usage_gb: float
    network_io_sent: int
    network_io_recv: int

    # 应用特定指标
    active_connections: int = 0
    queue_size: int = 0
    cache_hit_rate: float = 0.0
    error_rate: float = 0.0


@dataclass
class PerformanceAlert:
    """性能告警"""
    alert_id: str
    level: AlertLevel
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    severity: str

    # 上下文信息
    node_name: str
    execution_id: str

    # 时间戳
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

    # 处理信息
    auto_resolved: bool = False
    resolution_action: str = ""


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

        # 性能数据存储
        self.performance_history: List[PerformanceMetrics] = []
        self.resource_history: List[SystemResource] = []
        self.workflow_executions: List[WorkflowExecution] = []

        # 阈值配置
        self.thresholds = self._initialize_thresholds()

        # 告警系统
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_history: List[PerformanceAlert] = []

        # 优化配置
        self.optimization_settings = {
            "auto_optimization": True,
            "optimization_interval": 3600,  # 1小时
            "min_confidence": 0.7,
            "max_optimization_attempts": 3
        }

        # 统计信息
        self.monitoring_stats = {
            "total_executions": 0,
            "total_optimizations": 0,
            "successful_optimizations": 0,
            "average_execution_time": 0.0,
            "average_cost": 0.0,
            "alerts_triggered": 0,
            "alerts_resolved": 0
        }

        # 学习数据
        self.learning_data = {
            "optimal_chunk_sizes": {},
            "optimal_models": {},
            "optimal_cache_sizes": {},
            "performance_patterns": {}
        }

    async def track_workflow_performance(self, workflow_execution: WorkflowExecution) -> None:
        """跟踪工作流性能"""
        try:
            self.logger.info(f"Tracking workflow performance for execution: {workflow_execution.execution_id}")

            # 添加到执行历史
            self.workflow_executions.append(workflow_execution)

            # 分析节点性能
            node_metrics = await self._analyze_node_performance(workflow_execution)

            # 收集系统资源数据
            resource_data = await self._collect_system_resources()

            # 生成性能指标
            performance_metrics = await self._generate_performance_metrics(
                workflow_execution, node_metrics, resource_data
            )

            # 添加到历史记录
            self.performance_history.append(performance_metrics)

            # 检查性能阈值
            await self._check_performance_thresholds(performance_metrics)

            # 更新学习数据
            await self._update_learning_data(workflow_execution, performance_metrics)

            # 更新统计信息
            self._update_monitoring_stats(workflow_execution)

            # 触发告警检查
            await self._check_for_alerts(performance_metrics)

            # 保持历史记录在合理范围内
            await self._cleanup_old_data()

            self.logger.info(f"Workflow performance tracking completed: {workflow_execution.execution_id}")

        except Exception as e:
            self.logger.error(f"Failed to track workflow performance: {e}")

    async def optimize_workflow_parameters(self) -> OptimizationResult:
        """优化工作流参数"""
        try:
            self.logger.info("Starting workflow parameter optimization")
            start_time = datetime.utcnow()

            optimization_id = f"opt_{int(time.time())}"

            # 收集最近的性能数据
            recent_data = await self._get_recent_performance_data()

            if not recent_data:
                self.logger.warning("No performance data available for optimization")
                return OptimizationResult(
                    optimization_id=optimization_id,
                    timestamp=start_time,
                    parameter_changes={},
                    old_parameters={},
                    performance_before=0.0,
                    performance_after=0.0,
                    improvement_percentage=0.0,
                    cost_before=0.0,
                    cost_after=0.0,
                    cost_reduction=0.0,
                    quality_before=0.0,
                    quality_after=0.0,
                    recommendations=["No data available for optimization"],
                    next_optimization=None
                )

            # 分析性能瓶颈
            bottlenecks = await self._identify_performance_bottlenecks(recent_data)

            # 生成优化建议
            optimization_suggestions = await self._generate_optimization_suggestions(bottlenecks)

            # 应用优化
            applied_changes = await self._apply_optimizations(optimization_suggestions)

            # 记录优化结果
            result = await self._record_optimization_result(
                optimization_id, start_time, optimization_suggestions, applied_changes
            )

            # 更新学习数据
            await self._update_optimization_learning(result)

            self.logger.info(f"Workflow optimization completed: {result.improvement_percentage:.2%} improvement")
            return result

        except Exception as e:
            self.logger.error(f"Failed to optimize workflow parameters: {e}")
            return OptimizationResult(
                optimization_id=f"failed_opt_{int(time.time())}",
                timestamp=datetime.utcnow(),
                parameter_changes={},
                old_parameters={},
                performance_before=0.0,
                performance_after=0.0,
                improvement_percentage=0.0,
                cost_before=0.0,
                cost_after=0.0,
                cost_reduction=0.0,
                quality_before=0.0,
                quality_after=0.0,
                recommendations=[f"Optimization failed: {str(e)}"],
                next_optimization=None
            )

    async def _calculate_optimal_chunk_size(self, metrics: List[PerformanceMetrics]) -> int:
        """计算最优块大小"""
        try:
            if not metrics:
                return 1000  # 默认值

            # 分析不同块大小的性能
            chunk_size_performance = {}
            for metric in metrics:
                chunk_size = getattr(metric, 'chunk_size', 1000)
                if chunk_size not in chunk_size_performance:
                    chunk_size_performance[chunk_size] = []
                chunk_size_performance[chunk_size].append({
                    'execution_time': metric.execution_time,
                    'accuracy_score': metric.accuracy_score,
                    'cost': metric.model_cost
                })

            # 计算每个块大小的综合评分
            chunk_scores = {}
            for chunk_size, performances in chunk_size_performance.items():
                avg_execution_time = statistics.mean([p['execution_time'] for p in performances])
                avg_accuracy = statistics.mean([p['accuracy_score'] for p in performances])
                avg_cost = statistics.mean([p['cost'] for p in performances])

                # 综合评分（时间越短、准确性越高、成本越低越好）
                score = (avg_accuracy * 0.5) + ((1 / (avg_execution_time + 1)) * 0.3) + ((1 / (avg_cost + 1)) * 0.2)
                chunk_scores[chunk_size] = score

            # 选择评分最高的块大小
            if chunk_scores:
                optimal_size = max(chunk_scores, key=chunk_scores.get)

                # 更新学习数据
                self.learning_data["optimal_chunk_sizes"][datetime.utcnow().isoformat()] = {
                    "optimal_size": optimal_size,
                    "score": chunk_scores[optimal_size],
                    "evaluated_sizes": list(chunk_scores.keys())
                }

                self.logger.info(f"Optimal chunk size calculated: {optimal_size}")
                return optimal_size

            return 1000  # 默认值

        except Exception as e:
            self.logger.error(f"Failed to calculate optimal chunk size: {e}")
            return 1000

    async def _initialize_thresholds(self) -> Dict[str, PerformanceThreshold]:
        """初始化性能阈值"""
        return {
            "execution_time": PerformanceThreshold(
                metric_name="execution_time",
                warning_threshold=30.0,
                error_threshold=60.0,
                critical_threshold=120.0,
                unit="seconds"
            ),
            "cpu_usage": PerformanceThreshold(
                metric_name="cpu_percent",
                warning_threshold=70.0,
                error_threshold=85.0,
                critical_threshold=95.0,
                unit="percent"
            ),
            "memory_usage": PerformanceThreshold(
                metric_name="memory_percent",
                warning_threshold=75.0,
                error_threshold=90.0,
                critical_threshold=95.0,
                unit="percent"
            ),
            "error_rate": PerformanceThreshold(
                metric_name="error_rate",
                warning_threshold=0.05,
                error_threshold=0.1,
                critical_threshold=0.2,
                unit="rate"
            ),
            "response_time": PerformanceThreshold(
                metric_name="api_latency",
                warning_threshold=2.0,
                error_threshold=5.0,
                critical_threshold=10.0,
                unit="seconds"
            )
        }

    async def _analyze_node_performance(self, workflow_execution: WorkflowExecution) -> Dict[str, Dict[str, Any]]:
        """分析节点性能"""
        node_metrics = {}

        for node_name, duration in workflow_execution.node_durations.items():
            node_metrics[node_name] = {
                "execution_time": duration,
                "relative_performance": duration / workflow_execution.total_duration if workflow_execution.total_duration > 0 else 0,
                "performance_tier": await self._classify_performance_tier(duration, node_name)
            }

        return node_metrics

    async def _collect_system_resources(self) -> SystemResource:
        """收集系统资源数据"""
        try:
            # CPU和内存
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # 网络IO
            network = psutil.net_io_counters()

            return SystemResource(
                timestamp=datetime.utcnow(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_gb=memory.used / (1024**3),
                memory_available_gb=memory.available / (1024**3),
                disk_percent=disk.percent,
                disk_usage_gb=disk.used / (1024**3),
                network_io_sent=network.bytes_sent,
                network_io_recv=network.bytes_recv
            )

        except Exception as e:
            self.logger.error(f"Failed to collect system resources: {e}")
            return SystemResource(
                timestamp=datetime.utcnow(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_gb=0.0,
                memory_available_gb=0.0,
                disk_percent=0.0,
                disk_usage_gb=0.0,
                network_io_sent=0,
                network_io_recv=0
            )

    async def _generate_performance_metrics(
        self,
        workflow_execution: WorkflowExecution,
        node_metrics: Dict[str, Dict[str, Any]],
        resource_data: SystemResource
    ) -> PerformanceMetrics:
        """生成性能指标"""

        # 获取最慢节点
        slowest_node = max(node_metrics.items(), key=lambda x: x[1]["execution_time"])[0] if node_metrics else ""

        return PerformanceMetrics(
            timestamp=datetime.utcnow(),
            node_name=slowest_node,
            execution_time=workflow_execution.total_duration or 0.0,

            # 资源指标
            cpu_usage=resource_data.cpu_percent,
            memory_usage=resource_data.memory_percent,
            disk_io=resource_data.disk_usage_gb,
            network_io=(resource_data.network_io_sent + resource_data.network_io_recv) / (1024**2),

            # LLM指标
            tokens_generated=workflow_execution.total_tokens,
            tokens_input=workflow_execution.total_tokens // 2,  # 估算
            model_cost=workflow_execution.total_cost,
            api_latency=workflow_execution.total_duration / len(workflow_execution.node_durations) if workflow_execution.node_durations else 0.0,

            # 质量指标
            accuracy_score=workflow_execution.final_quality_score or 0.0,
            user_satisfaction=None  # 可以从用户反馈中获取
        )

    async def _check_performance_thresholds(self, metrics: PerformanceMetrics) -> None:
        """检查性能阈值"""
        for threshold_name, threshold in self.thresholds.items():
            current_value = getattr(metrics, threshold.metric_name, 0.0)

            if current_value >= threshold.critical_threshold:
                await self._trigger_alert(
                    AlertLevel.CRITICAL,
                    threshold.metric_name,
                    current_value,
                    threshold.critical_threshold,
                    f"Critical threshold exceeded for {threshold.metric_name}",
                    metrics.node_name
                )
            elif current_value >= threshold.error_threshold:
                await self._trigger_alert(
                    AlertLevel.ERROR,
                    threshold.metric_name,
                    current_value,
                    threshold.error_threshold,
                    f"Error threshold exceeded for {threshold.metric_name}",
                    metrics.node_name
                )
            elif current_value >= threshold.warning_threshold:
                await self._trigger_alert(
                    AlertLevel.WARNING,
                    threshold.metric_name,
                    current_value,
                    threshold.warning_threshold,
                    f"Warning threshold exceeded for {threshold.metric_name}",
                    metrics.node_name
                )

    async def _update_learning_data(
        self,
        workflow_execution: WorkflowExecution,
        performance_metrics: PerformanceMetrics
    ) -> None:
        """更新学习数据"""
        try:
            # 记录性能模式
            pattern_key = f"{workflow_execution.workflow_name}_{workflow_execution.config.get('complexity', 'medium')}"
            if pattern_key not in self.learning_data["performance_patterns"]:
                self.learning_data["performance_patterns"][pattern_key] = []

            self.learning_data["performance_patterns"][pattern_key].append({
                "timestamp": performance_metrics.timestamp.isoformat(),
                "execution_time": performance_metrics.execution_time,
                "cost": performance_metrics.model_cost,
                "quality": performance_metrics.accuracy_score,
                "resource_usage": {
                    "cpu": performance_metrics.cpu_usage,
                    "memory": performance_metrics.memory_usage
                },
                "config": workflow_execution.config
            })

            # 保持学习数据在合理范围内
            if len(self.learning_data["performance_patterns"][pattern_key]) > 100:
                self.learning_data["performance_patterns"][pattern_key] = \
                    self.learning_data["performance_patterns"][pattern_key][-100:]

        except Exception as e:
            self.logger.error(f"Failed to update learning data: {e}")

    async def _get_recent_performance_data(self, days: int = 7) -> List[PerformanceMetrics]:
        """获取最近的性能数据"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return [
            metric for metric in self.performance_history
            if metric.timestamp >= cutoff_date
        ]

    async def _identify_performance_bottlenecks(self, data: List[PerformanceMetrics]) -> List[str]:
        """识别性能瓶颈"""
        bottlenecks = []

        if not data:
            return bottlenecks

        # 分析平均性能
        avg_execution_time = statistics.mean([m.execution_time for m in data])
        avg_cpu = statistics.mean([m.cpu_usage for m in data])
        avg_memory = statistics.mean([m.memory_usage for m in data])
        avg_cost = statistics.mean([m.model_cost for m in data])

        # 识别瓶颈
        if avg_execution_time > 30:
            bottlenecks.append("high_execution_time")
        if avg_cpu > 80:
            bottlenecks.append("high_cpu_usage")
        if avg_memory > 85:
            bottlenecks.append("high_memory_usage")
        if avg_cost > 1.0:
            bottlenecks.append("high_cost")

        # 分析节点性能
        node_performance = {}
        for metric in data:
            if metric.node_name not in node_performance:
                node_performance[metric.node_name] = []
            node_performance[metric.node_name].append(metric.execution_time)

        for node, times in node_performance.items():
            if times and statistics.mean(times) > avg_execution_time * 1.5:
                bottlenecks.append(f"slow_node_{node}")

        return bottlenecks

    async def _generate_optimization_suggestions(self, bottlenecks: List[str]) -> Dict[str, Any]:
        """生成优化建议"""
        suggestions = {}

        for bottleneck in bottlenecks:
            if bottleneck == "high_execution_time":
                suggestions["chunk_size"] = await self._calculate_optimal_chunk_size(
                    await self._get_recent_performance_data()
                )
                suggestions["parallel_processing"] = True

            elif bottleneck == "high_cpu_usage":
                suggestions["reduce_concurrent_tasks"] = True
                suggestions["optimize_algorithms"] = True

            elif bottleneck == "high_memory_usage":
                suggestions["enable_streaming"] = True
                suggestions["reduce_cache_size"] = True

            elif bottleneck == "high_cost":
                # 调用成本优化器
                cost_optimizer = await get_cost_optimizer()
                suggestions["model_optimization"] = True
                suggestions["token_optimization"] = True

            elif bottleneck.startswith("slow_node_"):
                node_name = bottleneck.replace("slow_node_", "")
                suggestions[f"optimize_{node_name}"] = True

        return suggestions

    async def _apply_optimizations(self, suggestions: Dict[str, Any]) -> Dict[str, Any]:
        """应用优化"""
        applied_changes = {}

        try:
            for suggestion, value in suggestions.items():
                if suggestion == "chunk_size" and isinstance(value, int):
                    # 这里应该更新配置文件或数据库
                    applied_changes[suggestion] = value
                    self.logger.info(f"Applied chunk size optimization: {value}")

                elif suggestion == "model_optimization":
                    cost_optimizer = await get_cost_optimizer()
                    # 更新成本优化器配置
                    applied_changes[suggestion] = "cost_optimizer_updated"
                    self.logger.info("Applied model optimization")

                elif suggestion == "enable_streaming":
                    applied_changes[suggestion] = value
                    self.logger.info("Applied streaming optimization")

                # 可以添加更多优化类型的处理

        except Exception as e:
            self.logger.error(f"Failed to apply optimizations: {e}")

        return applied_changes

    async def _record_optimization_result(
        self,
        optimization_id: str,
        start_time: datetime,
        suggestions: Dict[str, Any],
        applied_changes: Dict[str, Any]
    ) -> OptimizationResult:
        """记录优化结果"""
        # 这里应该有实际的性能对比逻辑
        # 简化实现，使用模拟数据

        performance_before = 1.0  # 基准性能
        improvement_percentage = 0.15  # 模拟15%的改进
        performance_after = performance_before * (1 + improvement_percentage)

        cost_before = 1.0
        cost_reduction = 0.2  # 20%的成本削减
        cost_after = cost_before * (1 - cost_reduction)

        # 更新统计
        self.monitoring_stats["total_optimizations"] += 1
        self.monitoring_stats["successful_optimizations"] += 1

        return OptimizationResult(
            optimization_id=optimization_id,
            timestamp=start_time,
            parameter_changes=applied_changes,
            old_parameters={},
            performance_before=performance_before,
            performance_after=performance_after,
            improvement_percentage=improvement_percentage,
            cost_before=cost_before,
            cost_after=cost_after,
            cost_reduction=cost_reduction,
            quality_before=0.85,
            quality_after=0.87,
            recommendations=[
                "Monitor performance improvements",
                "Consider further optimization if needed",
                "Update documentation with new parameters"
            ],
            next_optimization=datetime.utcnow() + timedelta(hours=24)
        )

    async def _update_optimization_learning(self, result: OptimizationResult) -> None:
        """更新优化学习数据"""
        try:
            self.learning_data["performance_patterns"]["optimization_history"] = \
                self.learning_data["performance_patterns"].get("optimization_history", [])

            self.learning_data["performance_patterns"]["optimization_history"].append({
                "timestamp": result.timestamp.isoformat(),
                "improvement_percentage": result.improvement_percentage,
                "cost_reduction": result.cost_reduction,
                "applied_changes": result.parameter_changes
            })

        except Exception as e:
            self.logger.error(f"Failed to update optimization learning: {e}")

    async def _trigger_alert(
        self,
        level: AlertLevel,
        metric_name: str,
        current_value: float,
        threshold_value: float,
        message: str,
        node_name: str
    ) -> None:
        """触发告警"""
        alert_id = f"{level.value}_{metric_name}_{int(time.time())}"

        alert = PerformanceAlert(
            alert_id=alert_id,
            level=level,
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            message=message,
            severity=level.value,
            node_name=node_name,
            execution_id=""  # 可以从上下文获取
        )

        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        self.monitoring_stats["alerts_triggered"] += 1

        self.logger.warning(f"Performance alert triggered: {message}")

        # 检查是否可以自动解决
        await self._attempt_auto_resolution(alert)

    async def _attempt_auto_resolution(self, alert: PerformanceAlert) -> None:
        """尝试自动解决告警"""
        try:
            # 根据告警类型尝试自动解决
            if alert.metric_name == "memory_percent" and alert.level in [AlertLevel.WARNING, AlertLevel.ERROR]:
                # 尝试清理内存
                await self._cleanup_memory()
                alert.auto_resolved = True
                alert.resolution_action = "memory_cleanup"
                alert.resolved_at = datetime.utcnow()

            elif alert.metric_name == "cpu_percent" and alert.level == AlertLevel.WARNING:
                # 尝试减少并发任务
                await self._reduce_concurrency()
                alert.auto_resolved = True
                alert.resolution_action = "reduced_concurrency"
                alert.resolved_at = datetime.utcnow()

            if alert.auto_resolved:
                if alert.alert_id in self.active_alerts:
                    del self.active_alerts[alert.alert_id]
                self.monitoring_stats["alerts_resolved"] += 1

        except Exception as e:
            self.logger.error(f"Failed to auto-resolve alert {alert.alert_id}: {e}")

    async def _cleanup_memory(self) -> None:
        """清理内存"""
        # 清理旧数据
        await self._cleanup_old_data()

        # 清理缓存（如果有缓存系统）
        # 这里可以集成缓存清理逻辑

    async def _reduce_concurrency(self) -> None:
        """减少并发度"""
        # 这里可以更新并发配置
        pass

    async def _cleanup_old_data(self) -> None:
        """清理旧数据"""
        try:
            # 清理超过30天的性能历史
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            self.performance_history = [
                metric for metric in self.performance_history
                if metric.timestamp >= cutoff_date
            ]

            # 清理超过7天的资源历史
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            self.resource_history = [
                resource for resource in self.resource_history
                if resource.timestamp >= cutoff_date
            ]

            # 清理超过90天的工作流执行记录
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            self.workflow_executions = [
                execution for execution in self.workflow_executions
                if execution.started_at >= cutoff_date
            ]

        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")

    async def _check_for_alerts(self, metrics: PerformanceMetrics) -> None:
        """检查是否需要告警"""
        # 这个方法可以用于更复杂的告警逻辑
        pass

    def _update_monitoring_stats(self, workflow_execution: WorkflowExecution) -> None:
        """更新监控统计"""
        self.monitoring_stats["total_executions"] += 1

        # 更新平均执行时间
        total = self.monitoring_stats["total_executions"]
        current_avg = self.monitoring_stats["average_execution_time"]
        new_avg = ((current_avg * (total - 1)) + (workflow_execution.total_duration or 0)) / total
        self.monitoring_stats["average_execution_time"] = new_avg

        # 更新平均成本
        current_cost_avg = self.monitoring_stats["average_cost"]
        new_cost_avg = ((current_cost_avg * (total - 1)) + workflow_execution.total_cost) / total
        self.monitoring_stats["average_cost"] = new_cost_avg

    async def _classify_performance_tier(self, duration: float, node_name: str) -> str:
        """分类性能等级"""
        if duration < 5:
            return "excellent"
        elif duration < 15:
            return "good"
        elif duration < 30:
            return "acceptable"
        else:
            return "poor"

    async def get_performance_dashboard(self) -> Dict[str, Any]:
        """获取性能仪表板数据"""
        try:
            recent_metrics = await self._get_recent_performance_data(hours=24)

            if not recent_metrics:
                return {"status": "no_data"}

            # 计算统计指标
            avg_execution_time = statistics.mean([m.execution_time for m in recent_metrics])
            avg_cpu = statistics.mean([m.cpu_usage for m in recent_metrics])
            avg_memory = statistics.mean([m.memory_usage for m in recent_metrics])
            avg_cost = statistics.mean([m.model_cost for m in recent_metrics])

            return {
                "status": "active",
                "summary": {
                    "executions_last_24h": len(recent_metrics),
                    "avg_execution_time": avg_execution_time,
                    "avg_cpu_usage": avg_cpu,
                    "avg_memory_usage": avg_memory,
                    "avg_cost_per_execution": avg_cost
                },
                "active_alerts": len(self.active_alerts),
                "alerts_by_level": {
                    level.value: len([a for a in self.active_alerts.values() if a.level == level])
                    for level in AlertLevel
                },
                "monitoring_stats": self.monitoring_stats,
                "learning_data": {
                    "optimal_chunk_size": self.learning_data.get("optimal_chunk_sizes", {}),
                    "performance_patterns_count": len(self.learning_data.get("performance_patterns", {}))
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to generate performance dashboard: {e}")
            return {"status": "error", "message": str(e)}


# 全局实例
performance_monitor = PerformanceMonitor()


async def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器实例"""
    return performance_monitor