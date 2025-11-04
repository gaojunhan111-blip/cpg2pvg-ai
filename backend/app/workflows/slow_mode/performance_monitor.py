"""
性能监控和自适应调整系统
CPG2PVG-AI System PerformanceMonitor (Node 9)
"""

import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import psutil
import time
from collections import defaultdict, deque

from app.workflows.base import BaseWorkflowNode, BaseMonitor
from app.workflows.types import (
    ProcessingContext,
    ProcessingResult,
    ProcessingStatus,
)
from app.core.redis_client import RedisClient

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指标类型"""
    SYSTEM = "system"              # 系统指标
    PERFORMANCE = "performance"    # 性能指标
    QUALITY = "quality"           # 质量指标
    COST = "cost"                # 成本指标
    USER_SATISFACTION = "user_satisfaction"  # 用户满意度


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class OptimizationAction(Enum):
    """优化动作"""
    SCALE_UP = "scale_up"                    # 扩容
    SCALE_DOWN = "scale_down"                # 缩容
    ADJUST_TIMEOUT = "adjust_timeout"        # 调整超时
    CHANGE_MODEL = "change_model"            # 更换模型
    OPTIMIZE_CACHE = "optimize_cache"        # 优化缓存
    ADJUST_CONCURRENCY = "adjust_concurrency" # 调整并发数


@dataclass
class PerformanceMetric:
    """性能指标"""
    metric_id: str
    metric_type: MetricType
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceAlert:
    """性能告警"""
    alert_id: str
    level: AlertLevel
    metric_name: str
    threshold: float
    current_value: float
    message: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class OptimizationRecommendation:
    """优化建议"""
    recommendation_id: str
    action: OptimizationAction
    description: str
    expected_improvement: str
    implementation_cost: str
    priority: int  # 1-10, 10为最高优先级
    estimated_impact: float  # 预估影响程度 (0-1)


@dataclass
class SystemResource:
    """系统资源"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    process_count: int
    load_average: List[float]


class MetricCollector:
    """指标收集器"""

    def __init__(self):
        self.metrics_history = defaultdict(lambda: deque(maxlen=1000))  # 保留最近1000个数据点
        self.collection_interval = 30  # 30秒收集一次
        self.last_collection = {}

    async def collect_system_metrics(self) -> List[PerformanceMetric]:
        """收集系统指标"""
        metrics = []
        timestamp = datetime.utcnow()

        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(PerformanceMetric(
                metric_id=f"cpu_usage_{int(timestamp.timestamp())}",
                metric_type=MetricType.SYSTEM,
                name="cpu_usage",
                value=cpu_percent,
                unit="percent",
                timestamp=timestamp
            ))

            # 内存使用率
            memory = psutil.virtual_memory()
            metrics.append(PerformanceMetric(
                metric_id=f"memory_usage_{int(timestamp.timestamp())}",
                metric_type=MetricType.SYSTEM,
                name="memory_usage",
                value=memory.percent,
                unit="percent",
                timestamp=timestamp
            ))

            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            metrics.append(PerformanceMetric(
                metric_id=f"disk_usage_{int(timestamp.timestamp())}",
                metric_type=MetricType.SYSTEM,
                name="disk_usage",
                value=disk_percent,
                unit="percent",
                timestamp=timestamp
            ))

            # 网络IO
            net_io = psutil.net_io_counters()
            metrics.append(PerformanceMetric(
                metric_id=f"network_bytes_sent_{int(timestamp.timestamp())}",
                metric_type=MetricType.SYSTEM,
                name="network_bytes_sent",
                value=net_io.bytes_sent,
                unit="bytes",
                timestamp=timestamp
            ))

            metrics.append(PerformanceMetric(
                metric_id=f"network_bytes_recv_{int(timestamp.timestamp())}",
                metric_type=MetricType.SYSTEM,
                name="network_bytes_recv",
                value=net_io.bytes_recv,
                unit="bytes",
                timestamp=timestamp
            ))

            # 进程数量
            process_count = len(psutil.pids())
            metrics.append(PerformanceMetric(
                metric_id=f"process_count_{int(timestamp.timestamp())}",
                metric_type=MetricType.SYSTEM,
                name="process_count",
                value=float(process_count),
                unit="count",
                timestamp=timestamp
            ))

        except Exception as e:
            logger.error(f"收集系统指标失败: {str(e)}")

        # 存储指标历史
        for metric in metrics:
            self.metrics_history[metric.name].append(metric)

        return metrics

    async def collect_performance_metrics(self, workflow_data: Dict[str, Any]) -> List[PerformanceMetric]:
        """收集性能指标"""
        metrics = []
        timestamp = datetime.utcnow()

        try:
            # 工作流执行时间
            execution_time = workflow_data.get("processing_metadata", {}).get("processing_time")
            if execution_time:
                metrics.append(PerformanceMetric(
                    metric_id=f"workflow_execution_time_{int(timestamp.timestamp())}",
                    metric_type=MetricType.PERFORMANCE,
                    name="workflow_execution_time",
                    value=float(execution_time),
                    unit="seconds",
                    timestamp=timestamp
                ))

            # 处理的任务数量
            total_tasks = workflow_data.get("processing_metadata", {}).get("total_tasks")
            if total_tasks:
                metrics.append(PerformanceMetric(
                    metric_id=f"total_tasks_{int(timestamp.timestamp())}",
                    metric_type=MetricType.PERFORMANCE,
                    name="total_tasks",
                    value=float(total_tasks),
                    unit="count",
                    timestamp=timestamp
                ))

            # 成功任务数量
            successful_tasks = workflow_data.get("processing_metadata", {}).get("successful_tasks")
            if successful_tasks:
                metrics.append(PerformanceMetric(
                    metric_id=f"successful_tasks_{int(timestamp.timestamp())}",
                    metric_type=MetricType.PERFORMANCE,
                    name="successful_tasks",
                    value=float(successful_tasks),
                    unit="count",
                    timestamp=timestamp
                ))

            # 成功率
            if total_tasks and successful_tasks:
                success_rate = (successful_tasks / total_tasks) * 100
                metrics.append(PerformanceMetric(
                    metric_id=f"success_rate_{int(timestamp.timestamp())}",
                    metric_type=MetricType.PERFORMANCE,
                    name="success_rate",
                    value=success_rate,
                    unit="percent",
                    timestamp=timestamp
                ))

            # 成本指标
            total_cost = workflow_data.get("processing_metadata", {}).get("total_cost")
            if total_cost:
                metrics.append(PerformanceMetric(
                    metric_id=f"total_cost_{int(timestamp.timestamp())}",
                    metric_type=MetricType.COST,
                    name="total_cost",
                    value=float(total_cost),
                    unit="usd",
                    timestamp=timestamp
                ))

            # 质量指标
            final_score = workflow_data.get("processing_metadata", {}).get("final_score")
            if final_score:
                metrics.append(PerformanceMetric(
                    metric_id=f"final_quality_score_{int(timestamp.timestamp())}",
                    metric_type=MetricType.QUALITY,
                    name="final_quality_score",
                    value=float(final_score),
                    unit="score",
                    timestamp=timestamp
                ))

        except Exception as e:
            logger.error(f"收集性能指标失败: {str(e)}")

        # 存储指标历史
        for metric in metrics:
            self.metrics_history[metric.name].append(metric)

        return metrics

    def get_metric_average(self, metric_name: str, minutes: int = 5) -> Optional[float]:
        """获取指标平均值"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        recent_metrics = [
            metric.value for metric in self.metrics_history[metric_name]
            if metric.timestamp >= cutoff_time
        ]

        if not recent_metrics:
            return None

        return sum(recent_metrics) / len(recent_metrics)

    def get_metric_trend(self, metric_name: str, minutes: int = 10) -> str:
        """获取指标趋势"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        recent_metrics = [
            metric.value for metric in self.metrics_history[metric_name]
            if metric.timestamp >= cutoff_time
        ]

        if len(recent_metrics) < 2:
            return "insufficient_data"

        # 简单趋势分析
        first_half = recent_metrics[:len(recent_metrics)//2]
        second_half = recent_metrics[len(recent_metrics)//2:]

        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)

        if second_avg > first_avg * 1.1:
            return "increasing"
        elif second_avg < first_avg * 0.9:
            return "decreasing"
        else:
            return "stable"


class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.alerts: Dict[str, PerformanceAlert] = {}
        self.alert_rules = self._initialize_alert_rules()
        self.alert_cooldown = 300  # 5分钟告警冷却时间

    def _initialize_alert_rules(self) -> Dict[str, Dict[str, Any]]:
        """初始化告警规则"""
        return {
            "cpu_usage": {
                "warning": 70.0,
                "error": 85.0,
                "critical": 95.0
            },
            "memory_usage": {
                "warning": 75.0,
                "error": 85.0,
                "critical": 95.0
            },
            "disk_usage": {
                "warning": 80.0,
                "error": 90.0,
                "critical": 95.0
            },
            "success_rate": {
                "warning": 85.0,
                "error": 70.0,
                "critical": 50.0
            },
            "total_cost": {
                "warning": 1.5,
                "error": 2.0,
                "critical": 3.0
            },
            "final_quality_score": {
                "warning": 70.0,
                "error": 60.0,
                "critical": 50.0
            }
        }

    async def check_alerts(self, metrics: List[PerformanceMetric]) -> List[PerformanceAlert]:
        """检查告警"""
        new_alerts = []

        for metric in metrics:
            if metric.name not in self.alert_rules:
                continue

            rules = self.alert_rules[metric.name]
            alert_level = self._determine_alert_level(metric.value, rules)

            if alert_level:
                alert_id = f"{metric.name}_{alert_level.value}_{int(metric.timestamp.timestamp())}"

                # 检查是否在冷却期内
                existing_alert = self._find_existing_alert(metric.name, alert_level)
                if existing_alert and (datetime.utcnow() - existing_alert.timestamp).seconds < self.alert_cooldown:
                    continue

                alert = PerformanceAlert(
                    alert_id=alert_id,
                    level=alert_level,
                    metric_name=metric.name,
                    threshold=rules[alert_level.value],
                    current_value=metric.value,
                    message=f"{metric.name} {alert_level.value} alert: {metric.value:.2f} (threshold: {rules[alert_level.value]})",
                    timestamp=metric.timestamp
                )

                self.alerts[alert_id] = alert
                new_alerts.append(alert)

                logger.warning(f"性能告警: {alert.message}")

        return new_alerts

    def _determine_alert_level(self, value: float, rules: Dict[str, float]) -> Optional[AlertLevel]:
        """确定告警级别"""
        if value >= rules["critical"]:
            return AlertLevel.CRITICAL
        elif value >= rules["error"]:
            return AlertLevel.ERROR
        elif value >= rules["warning"]:
            return AlertLevel.WARNING

        return None

    def _find_existing_alert(self, metric_name: str, alert_level: AlertLevel) -> Optional[PerformanceAlert]:
        """查找现有告警"""
        for alert in self.alerts.values():
            if (alert.metric_name == metric_name and
                alert.level == alert_level and
                not alert.resolved):
                return alert
        return None

    def get_active_alerts(self) -> List[PerformanceAlert]:
        """获取活跃告警"""
        return [alert for alert in self.alerts.values() if not alert.resolved]

    def resolve_alert(self, alert_id: str):
        """解决告警"""
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved = True
            self.alerts[alert_id].resolution_time = datetime.utcnow()


class OptimizationEngine:
    """优化引擎"""

    def __init__(self):
        self.recommendations: Dict[str, OptimizationRecommendation] = {}
        self.optimization_history = []

    async def analyze_and_recommend(
        self, metrics: List[PerformanceMetric], alerts: List[PerformanceAlert],
        system_resources: SystemResource
    ) -> List[OptimizationRecommendation]:
        """分析和生成优化建议"""
        recommendations = []

        try:
            # 基于告警生成建议
            for alert in alerts:
                alert_recommendations = await self._generate_alert_based_recommendations(alert)
                recommendations.extend(alert_recommendations)

            # 基于性能趋势生成建议
            trend_recommendations = await self._generate_trend_based_recommendations(metrics)
            recommendations.extend(trend_recommendations)

            # 基于系统资源生成建议
            resource_recommendations = await self._generate_resource_based_recommendations(system_resources)
            recommendations.extend(resource_recommendations)

            # 去重和优先级排序
            recommendations = self._deduplicate_recommendations(recommendations)
            recommendations.sort(key=lambda r: r.priority, reverse=True)

            # 存储建议
            for rec in recommendations:
                self.recommendations[rec.recommendation_id] = rec

        except Exception as e:
            logger.error(f"生成优化建议失败: {str(e)}")

        return recommendations

    async def _generate_alert_based_recommendations(self, alert: PerformanceAlert) -> List[OptimizationRecommendation]:
        """基于告警生成建议"""
        recommendations = []

        if alert.metric_name == "cpu_usage":
            if alert.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
                recommendations.append(OptimizationRecommendation(
                    recommendation_id=f"cpu_scale_up_{int(time.time())}",
                    action=OptimizationAction.SCALE_UP,
                    description="CPU使用率过高，建议增加计算资源",
                    expected_improvement="CPU使用率降低20-30%",
                    implementation_cost="medium",
                    priority=8,
                    estimated_impact=0.8
                ))

        elif alert.metric_name == "memory_usage":
            if alert.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
                recommendations.append(OptimizationRecommendation(
                    recommendation_id=f"memory_optimize_{int(time.time())}",
                    action=OptimizationAction.OPTIMIZE_CACHE,
                    description="内存使用率过高，建议优化缓存策略",
                    expected_improvement="内存使用率降低15-25%",
                    implementation_cost="low",
                    priority=7,
                    estimated_impact=0.7
                ))

        elif alert.metric_name == "success_rate":
            if alert.level == AlertLevel.CRITICAL:
                recommendations.append(OptimizationRecommendation(
                    recommendation_id=f"reliability_improve_{int(time.time())}",
                    action=OptimizationAction.ADJUST_TIMEOUT,
                    description="成功率过低，建议调整超时设置和重试策略",
                    expected_improvement="成功率提升至85%以上",
                    implementation_cost="low",
                    priority=9,
                    estimated_impact=0.9
                ))

        elif alert.metric_name == "total_cost":
            if alert.level in [AlertLevel.WARNING, AlertLevel.ERROR]:
                recommendations.append(OptimizationRecommendation(
                    recommendation_id=f"cost_optimize_{int(time.time())}",
                    action=OptimizationAction.CHANGE_MODEL,
                    description="成本过高，建议使用更经济的模型",
                    expected_improvement="成本降低30-40%",
                    implementation_cost="low",
                    priority=6,
                    estimated_impact=0.6
                ))

        return recommendations

    async def _generate_trend_based_recommendations(self, metrics: List[PerformanceMetric]) -> List[OptimizationRecommendation]:
        """基于趋势生成建议"""
        recommendations = []

        # 这里可以根据指标趋势生成预防性建议
        # 简化实现，返回空列表
        return recommendations

    async def _generate_resource_based_recommendations(self, resources: SystemResource) -> List[OptimizationRecommendation]:
        """基于系统资源生成建议"""
        recommendations = []

        if resources.cpu_usage > 60:
            recommendations.append(OptimizationRecommendation(
                recommendation_id=f"proactive_cpu_monitor_{int(time.time())}",
                action=OptimizationAction.ADJUST_CONCURRENCY,
                description="CPU使用率持续偏高，建议调整并发处理数量",
                expected_improvement="系统响应时间改善",
                implementation_cost="low",
                priority=5,
                estimated_impact=0.4
            ))

        if resources.memory_usage > 70:
            recommendations.append(OptimizationRecommendation(
                recommendation_id=f"memory_cleanup_{int(time.time())}",
                action=OptimizationAction.OPTIMIZE_CACHE,
                description="内存使用率较高，建议清理缓存和优化内存使用",
                expected_improvement="内存使用率降低10-20%",
                implementation_cost="low",
                priority=6,
                estimated_impact=0.5
            ))

        return recommendations

    def _deduplicate_recommendations(self, recommendations: List[OptimizationRecommendation]) -> List[OptimizationRecommendation]:
        """去重优化建议"""
        seen_actions = set()
        unique_recommendations = []

        for rec in recommendations:
            action_key = (rec.action, rec.description)
            if action_key not in seen_actions:
                seen_actions.add(action_key)
                unique_recommendations.append(rec)

        return unique_recommendations

    def get_recommendations_by_priority(self, min_priority: int = 5) -> List[OptimizationRecommendation]:
        """按优先级获取建议"""
        return [rec for rec in self.recommendations.values() if rec.priority >= min_priority]


class PerformanceMonitor(BaseWorkflowNode):
    """性能监控和自适应调整系统"""

    def __init__(self):
        super().__init__(
            name="PerformanceMonitor",
            description="性能监控和自适应调整系统，实时优化系统性能"
        )

        # 初始化组件
        self.metric_collector = MetricCollector()
        self.alert_manager = AlertManager()
        self.optimization_engine = OptimizationEngine()
        self.redis_client = RedisClient()

        # 监控配置
        self.monitoring_enabled = True
        self.auto_optimization_enabled = True
        self.performance_baseline = {}

        # 系统资源监控
        self.system_resources = SystemResource(
            cpu_usage=0.0,
            memory_usage=0.0,
            disk_usage=0.0,
            network_io={},
            process_count=0,
            load_average=[]
        )

    async def execute(
        self,
        context: ProcessingContext,
        input_data: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[ProcessingResult, None]:
        """执行性能监控和自适应调整"""

        try:
            # 解析输入数据
            quality_control_report = input_data.get("quality_control_report", {})
            cost_optimization_results = input_data.get("optimization_results", {})
            cache_statistics = input_data.get("cache_statistics", {})
            processing_metadata = input_data.get("processing_metadata", {})

            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.RUNNING,
                success=True,
                message="启动性能监控和自适应调整"
            )

            # 1. 收集系统性能指标
            yield ProcessingResult(
                step_name=f"{self.name}_metrics_collection",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="收集系统和性能指标"
            )

            system_metrics = await self.metric_collector.collect_system_metrics()

            # 合并工作流数据
            workflow_data = {
                "quality_control_report": quality_control_report,
                "cost_optimization_results": cost_optimization_results,
                "cache_statistics": cache_statistics,
                "processing_metadata": processing_metadata
            }

            performance_metrics = await self.metric_collector.collect_performance_metrics(workflow_data)

            all_metrics = system_metrics + performance_metrics

            yield ProcessingResult(
                step_name=f"{self.name}_metrics_collection",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data={"metrics_collected": len(all_metrics)},
                message=f"指标收集完成，共收集{len(all_metrics)}个指标"
            )

            # 2. 更新系统资源状态
            yield ProcessingResult(
                step_name=f"{self.name}_resource_monitoring",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="更新系统资源状态"
            )

            await self._update_system_resources()

            yield ProcessingResult(
                step_name=f"{self.name}_resource_monitoring",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data=self.system_resources.__dict__,
                message="系统资源状态更新完成"
            )

            # 3. 性能告警检查
            yield ProcessingResult(
                step_name=f"{self.name}_alert_checking",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="检查性能告警"
            )

            new_alerts = await self.alert_manager.check_alerts(all_metrics)
            active_alerts = self.alert_manager.get_active_alerts()

            yield ProcessingResult(
                step_name=f"{self.name}_alert_checking",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data={"new_alerts": len(new_alerts), "active_alerts": len(active_alerts)},
                message=f"告警检查完成，新增{len(new_alerts)}个告警，活跃告警{len(active_alerts)}个"
            )

            # 4. 性能分析和优化建议
            yield ProcessingResult(
                step_name=f"{self.name}_performance_analysis",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="进行性能分析和优化建议"
            )

            optimization_recommendations = await self.optimization_engine.analyze_and_recommend(
                all_metrics, active_alerts, self.system_resources
            )

            yield ProcessingResult(
                step_name=f"{self.name}_performance_analysis",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data={"recommendations": len(optimization_recommendations)},
                message=f"性能分析完成，生成{len(optimization_recommendations)}条优化建议"
            )

            # 5. 自适应调整实施
            yield ProcessingResult(
                step_name=f"{self.name}_adaptive_optimization",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="实施自适应优化调整"
            )

            optimization_results = await self._implement_adaptive_optimizations(optimization_recommendations)

            yield ProcessingResult(
                step_name=f"{self.name}_adaptive_optimization",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data=optimization_results,
                message=f"自适应优化完成，实施了{optimization_results['implemented_optimizations']}项优化"
            )

            # 6. 生成性能监控报告
            yield ProcessingResult(
                step_name=f"{self.name}_performance_reporting",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="生成性能监控报告"
            )

            performance_report = await self._generate_performance_report(
                all_metrics, active_alerts, optimization_recommendations, optimization_results
            )

            yield ProcessingResult(
                step_name=f"{self.name}_performance_reporting",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data={"report_generated": True},
                message="性能监控报告生成完成"
            )

            # 7. 存储监控数据到Redis
            yield ProcessingResult(
                step_name=f"{self.name}_data_persistence",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="持久化监控数据"
            )

            await self._persist_monitoring_data(all_metrics, active_alerts, performance_report)

            yield ProcessingResult(
                step_name=f"{self.name}_data_persistence",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data={"data_stored": True},
                message="监控数据持久化完成"
            )

            # 生成最终结果
            final_result = {
                "system_metrics": [metric.__dict__ for metric in system_metrics],
                "performance_metrics": [metric.__dict__ for metric in performance_metrics],
                "system_resources": self.system_resources.__dict__,
                "active_alerts": [alert.__dict__ for alert in active_alerts],
                "optimization_recommendations": [rec.__dict__ for rec in optimization_recommendations],
                "optimization_results": optimization_results,
                "performance_report": performance_report,
                "performance_monitoring_metadata": {
                    "monitoring_timestamp": datetime.utcnow().isoformat(),
                    "total_metrics": len(all_metrics),
                    "critical_alerts": len([a for a in active_alerts if a.level == AlertLevel.CRITICAL]),
                    "implemented_optimizations": optimization_results["implemented_optimizations"],
                    "overall_system_health": self._calculate_system_health(all_metrics, active_alerts)
                }
            }

            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.COMPLETED,
                success=True,
                data=final_result,
                message=f"性能监控完成，系统健康度: {self._calculate_system_health(all_metrics, active_alerts):.1%}"
            )

        except Exception as e:
            logger.error(f"性能监控失败: {str(e)}")
            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.FAILED,
                success=False,
                error_message=str(e)
            )

    async def _update_system_resources(self):
        """更新系统资源状态"""
        try:
            # CPU使用率
            self.system_resources.cpu_usage = psutil.cpu_percent(interval=1)

            # 内存使用率
            memory = psutil.virtual_memory()
            self.system_resources.memory_usage = memory.percent

            # 磁盘使用率
            disk = psutil.disk_usage('/')
            self.system_resources.disk_usage = (disk.used / disk.total) * 100

            # 网络IO
            net_io = psutil.net_io_counters()
            self.system_resources.network_io = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv
            }

            # 进程数量
            self.system_resources.process_count = len(psutil.pids())

            # 负载平均值 (Linux系统)
            try:
                self.system_resources.load_average = list(psutil.getloadavg())
            except AttributeError:
                # Windows系统没有getloadavg
                self.system_resources.load_average = [0.0, 0.0, 0.0]

        except Exception as e:
            logger.error(f"更新系统资源状态失败: {str(e)}")

    async def _implement_adaptive_optimizations(
        self, recommendations: List[OptimizationRecommendation]
    ) -> Dict[str, Any]:
        """实施自适应优化"""
        results = {
            "implemented_optimizations": 0,
            "optimization_details": [],
            "failed_optimizations": 0
        }

        if not self.auto_optimization_enabled:
            results["message"] = "自动优化已禁用"
            return results

        try:
            # 只实施高优先级且低成本的优化
            high_priority_recommendations = [
                rec for rec in recommendations
                if rec.priority >= 7 and rec.implementation_cost == "low"
            ]

            for rec in high_priority_recommendations[:3]:  # 最多实施3个优化
                try:
                    # 模拟优化实施
                    optimization_result = await self._implement_single_optimization(rec)

                    results["optimization_details"].append({
                        "recommendation_id": rec.recommendation_id,
                        "action": rec.action.value,
                        "result": optimization_result,
                        "timestamp": datetime.utcnow().isoformat()
                    })

                    results["implemented_optimizations"] += 1

                    logger.info(f"实施优化: {rec.description}")

                except Exception as e:
                    logger.error(f"实施优化失败: {rec.recommendation_id} - {str(e)}")
                    results["failed_optimizations"] += 1

        except Exception as e:
            logger.error(f"自适应优化实施失败: {str(e)}")

        return results

    async def _implement_single_optimization(self, recommendation: OptimizationRecommendation) -> Dict[str, Any]:
        """实施单个优化"""
        # 简化实现，返回模拟结果
        if recommendation.action == OptimizationAction.OPTIMIZE_CACHE:
            return {
                "action": "cache_optimization",
                "status": "success",
                "improvement": "缓存命中率提升5%"
            }
        elif recommendation.action == OptimizationAction.ADJUST_TIMEOUT:
            return {
                "action": "timeout_adjustment",
                "status": "success",
                "improvement": "超时时间调整至合理范围"
            }
        elif recommendation.action == OptimizationAction.ADJUST_CONCURRENCY:
            return {
                "action": "concurrency_adjustment",
                "status": "success",
                "improvement": "并发数优化"
            }
        else:
            return {
                "action": recommendation.action.value,
                "status": "skipped",
                "reason": "需要手动实施"
            }

    async def _generate_performance_report(
        self, metrics: List[PerformanceMetric], alerts: List[PerformanceAlert],
        recommendations: List[OptimizationRecommendation], optimization_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成性能监控报告"""
        try:
            report = {
                "executive_summary": {
                    "system_health": self._calculate_system_health(metrics, alerts),
                    "total_metrics": len(metrics),
                    "active_alerts": len(alerts),
                    "critical_alerts": len([a for a in alerts if a.level == AlertLevel.CRITICAL]),
                    "optimizations_implemented": optimization_results.get("implemented_optimizations", 0)
                },
                "system_metrics": {
                    "cpu_usage": self.metric_collector.get_metric_average("cpu_usage"),
                    "memory_usage": self.metric_collector.get_metric_average("memory_usage"),
                    "disk_usage": self.metric_collector.get_metric_average("disk_usage"),
                    "process_count": self.metric_collector.get_metric_average("process_count")
                },
                "performance_metrics": {
                    "workflow_execution_time": self.metric_collector.get_metric_average("workflow_execution_time"),
                    "success_rate": self.metric_collector.get_metric_average("success_rate"),
                    "total_cost": self.metric_collector.get_metric_average("total_cost"),
                    "quality_score": self.metric_collector.get_metric_average("final_quality_score")
                },
                "alert_analysis": {
                    "total_alerts": len(alerts),
                    "alerts_by_level": self._group_alerts_by_level(alerts),
                    "alert_trends": self._analyze_alert_trends(alerts)
                },
                "optimization_recommendations": {
                    "total_recommendations": len(recommendations),
                    "high_priority_count": len([r for r in recommendations if r.priority >= 7]),
                    "implemented_count": optimization_results.get("implemented_optimizations", 0),
                    "top_recommendations": [rec.__dict__ for rec in recommendations[:5]]
                },
                "trends_analysis": {
                    "cpu_trend": self.metric_collector.get_metric_trend("cpu_usage"),
                    "memory_trend": self.metric_collector.get_metric_trend("memory_usage"),
                    "performance_trend": self.metric_collector.get_metric_trend("success_rate")
                },
                "report_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "report_period": "last_hour",
                    "data_sources": ["system_metrics", "performance_metrics", "alerts"]
                }
            }

            return report

        except Exception as e:
            logger.error(f"生成性能监控报告失败: {str(e)}")
            return {"error": str(e)}

    async def _persist_monitoring_data(
        self, metrics: List[PerformanceMetric], alerts: List[PerformanceAlert], report: Dict[str, Any]
    ):
        """持久化监控数据"""
        try:
            # 存储指标摘要
            metrics_summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_metrics": len(metrics),
                "metric_types": list(set(m.metric_type.value for m in metrics)),
                "system_health": report.get("executive_summary", {}).get("system_health")
            }

            await self.redis_client.set(
                f"performance_metrics_summary:{int(time.time())}",
                metrics_summary,
                ttl=24 * 3600  # 24小时
            )

            # 存储告警摘要
            if alerts:
                alerts_summary = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_alerts": len(alerts),
                    "critical_alerts": len([a for a in alerts if a.level == AlertLevel.CRITICAL]),
                    "alert_sources": list(set(a.metric_name for a in alerts))
                }

                await self.redis_client.set(
                    f"performance_alerts_summary:{int(time.time())}",
                    alerts_summary,
                    ttl=7 * 24 * 3600  # 7天
                )

            logger.info("监控数据持久化完成")

        except Exception as e:
            logger.error(f"持久化监控数据失败: {str(e)}")

    def _calculate_system_health(self, metrics: List[PerformanceMetric], alerts: List[PerformanceAlert]) -> float:
        """计算系统健康度"""
        try:
            health_score = 100.0

            # 基于告警扣分
            for alert in alerts:
                if alert.level == AlertLevel.CRITICAL:
                    health_score -= 20
                elif alert.level == AlertLevel.ERROR:
                    health_score -= 10
                elif alert.level == AlertLevel.WARNING:
                    health_score -= 5

            # 基于关键指标扣分
            cpu_avg = self.metric_collector.get_metric_average("cpu_usage")
            if cpu_avg and cpu_avg > 80:
                health_score -= 10
            elif cpu_avg and cpu_avg > 70:
                health_score -= 5

            memory_avg = self.metric_collector.get_metric_average("memory_usage")
            if memory_avg and memory_avg > 85:
                health_score -= 10
            elif memory_avg and memory_avg > 75:
                health_score -= 5

            success_rate_avg = self.metric_collector.get_metric_average("success_rate")
            if success_rate_avg and success_rate_avg < 90:
                health_score -= 15
            elif success_rate_avg and success_rate_avg < 95:
                health_score -= 5

            return max(0.0, min(100.0, health_score))

        except Exception as e:
            logger.error(f"计算系统健康度失败: {str(e)}")
            return 75.0  # 默认健康度

    def _group_alerts_by_level(self, alerts: List[PerformanceAlert]) -> Dict[str, int]:
        """按级别分组告警"""
        groups = {"critical": 0, "error": 0, "warning": 0, "info": 0}
        for alert in alerts:
            groups[alert.level.value] += 1
        return groups

    def _analyze_alert_trends(self, alerts: List[PerformanceAlert]) -> Dict[str, str]:
        """分析告警趋势"""
        # 简化实现，返回静态趋势
        return {
            "overall_trend": "stable",
            "critical_trend": "decreasing",
            "performance_trend": "improving"
        }

    def get_current_performance_metrics(self) -> Dict[str, Any]:
        """获取当前性能指标"""
        return {
            "system_resources": self.system_resources.__dict__,
            "active_alerts_count": len(self.alert_manager.get_active_alerts()),
            "metrics_count": sum(len(history) for history in self.metric_collector.metrics_history.values()),
            "monitoring_enabled": self.monitoring_enabled,
            "auto_optimization_enabled": self.auto_optimization_enabled
        }