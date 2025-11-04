"""
增强的日志记录系统
Enhanced Logging System with Performance Monitoring and Metrics
"""

import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path

# 配置标准日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(str, Enum):
    """指标类型"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str] = None
    unit: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['metric_type'] = self.metric_type.value
        return result


@dataclass
class LogEntry:
    """增强的日志条目"""
    timestamp: datetime
    level: LogLevel
    logger_name: str
    message: str
    module: str = ""
    function: str = ""
    line_number: int = 0
    duration: Optional[float] = None
    extra_data: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['level'] = self.level.value
        return result


class EnhancedLogger:
    """增强的日志记录器"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        self.metrics: List[PerformanceMetric] = []
        self.performance_data: Dict[str, List[float]] = {}
        self.log_entries: List[LogEntry] = []
        self.max_entries = 10000

    def debug(self, message: str, **kwargs) -> None:
        """调试日志"""
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """信息日志"""
        self._log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """警告日志"""
        self._log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """错误日志"""
        self._log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """严重错误日志"""
        self._log(LogLevel.CRITICAL, message, **kwargs)

    def _log(self, level: LogLevel, message: str, **kwargs) -> None:
        """内部日志方法"""
        # 获取调用栈信息
        import inspect
        frame = inspect.currentframe().f_back.f_back
        module = frame.f_globals.get('__name__', '')
        function = frame.f_code.co_name
        line_number = frame.f_lineno

        # 创建日志条目
        entry = LogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            logger_name=self.name,
            message=message,
            module=module,
            function=function,
            line_number=line_number,
            duration=kwargs.get('duration'),
            extra_data=kwargs.get('extra_data', {})
        )

        # 添加到日志列表
        self.log_entries.append(entry)
        if len(self.log_entries) > self.max_entries:
            self.log_entries = self.log_entries[-self.max_entries:]

        # 标准日志输出
        log_method = getattr(self.logger, level.value)
        extra_data_str = f" | Extra: {json.dumps(kwargs.get('extra_data', {}), default=str)}" if kwargs.get('extra_data') else ""
        duration_str = f" | Duration: {kwargs.get('duration', 0):.3f}s" if kwargs.get('duration') else ""
        log_method(f"{message}{duration_str}{extra_data_str}")

    def log_performance(self, operation: str, duration: float, tags: Dict[str, str] = None) -> None:
        """记录性能指标"""
        metric = PerformanceMetric(
            name=f"{operation}_duration",
            value=duration,
            metric_type=MetricType.TIMER,
            timestamp=datetime.utcnow(),
            tags=tags or {},
            unit="seconds"
        )

        self.metrics.append(metric)
        if len(self.metrics) > self.max_entries:
            self.metrics = self.metrics[-self.max_entries:]

        # 维护性能数据
        if operation not in self.performance_data:
            self.performance_data[operation] = []
        self.performance_data[operation].append(duration)

        # 保持最近1000个数据点
        if len(self.performance_data[operation]) > 1000:
            self.performance_data[operation] = self.performance_data[operation][-1000:]

        self.info(f"Performance: {operation} completed in {duration:.3f}s",
                 extra_data={"operation": operation, "tags": tags})

    def log_metric(self, name: str, value: float, metric_type: MetricType,
                   tags: Dict[str, str] = None, unit: str = "") -> None:
        """记录自定义指标"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=datetime.utcnow(),
            tags=tags or {},
            unit=unit
        )

        self.metrics.append(metric)
        if len(self.metrics) > self.max_entries:
            self.metrics = self.metrics[-self.max_entries:]

    def get_performance_stats(self, operation: str = None) -> Dict[str, Any]:
        """获取性能统计"""
        if operation:
            if operation not in self.performance_data:
                return {}

            data = self.performance_data[operation]
            return {
                "operation": operation,
                "count": len(data),
                "avg": sum(data) / len(data),
                "min": min(data),
                "max": max(data),
                "p50": self._percentile(data, 50),
                "p95": self._percentile(data, 95),
                "p99": self._percentile(data, 99)
            }
        else:
            stats = {}
            for op, data in self.performance_data.items():
                if data:
                    stats[op] = {
                        "count": len(data),
                        "avg": sum(data) / len(data),
                        "min": min(data),
                        "max": max(data)
                    }
            return stats

    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]

    def get_recent_logs(self, level: LogLevel = None, limit: int = 100) -> List[LogEntry]:
        """获取最近的日志"""
        logs = self.log_entries

        if level:
            logs = [log for log in logs if log.level == level]

        return logs[-limit:]

    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        summary = {
            "total_metrics": len(self.metrics),
            "total_log_entries": len(self.log_entries),
            "operations_tracked": len(self.performance_data),
            "metric_types": {}
        }

        # 统计指标类型
        for metric in self.metrics:
            metric_type = metric.metric_type.value
            summary["metric_types"][metric_type] = summary["metric_types"].get(metric_type, 0) + 1

        return summary

    def export_logs(self, filepath: str) -> None:
        """导出日志到文件"""
        export_data = {
            "logger_name": self.name,
            "export_timestamp": datetime.utcnow().isoformat(),
            "logs": [log.to_dict() for log in self.log_entries],
            "metrics": [metric.to_dict() for metric in self.metrics],
            "performance_stats": self.get_performance_stats(),
            "summary": self.get_metrics_summary()
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        self.info(f"Logs exported to {filepath}")


class PerformanceTimer:
    """性能计时器上下文管理器"""

    def __init__(self, logger: EnhancedLogger, operation: str, tags: Dict[str, str] = None):
        self.logger = logger
        self.operation = operation
        self.tags = tags or {}
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.logger.log_performance(self.operation, duration, self.tags)


# 全局日志记录器实例
_enhanced_loggers: Dict[str, EnhancedLogger] = {}


def get_enhanced_logger(name: str) -> EnhancedLogger:
    """获取增强的日志记录器"""
    if name not in _enhanced_loggers:
        _enhanced_loggers[name] = EnhancedLogger(name)
    return _enhanced_loggers[name]


def timer(operation: str, tags: Dict[str, str] = None):
    """装饰器：计时函数执行"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_enhanced_logger(func.__module__)
            with PerformanceTimer(logger, operation, tags):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def async_timer(operation: str, tags: Dict[str, str] = None):
    """装饰器：计时异步函数执行"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            logger = get_enhanced_logger(func.__module__)
            with PerformanceTimer(logger, operation, tags):
                return await func(*args, **kwargs)
        return wrapper
    return decorator


# 导出标准日志记录器（保持向后兼容）
def get_logger(name: str) -> logging.Logger:
    """获取标准日志记录器"""
    return logging.getLogger(name)