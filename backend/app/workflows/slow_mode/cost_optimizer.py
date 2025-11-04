"""
成本优化策略
CPG2PVG-AI System AdaptiveCostOptimizer (Node 7)
"""

import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from app.workflows.base import BaseWorkflowNode, BaseCostOptimizer
from app.workflows.types import (
    ProcessingContext,
    ProcessingResult,
    ProcessingStatus,
    CostLevel,
    QualityLevel,
)
from app.core.llm_client import LLMClient

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """优化策略"""
    AGGRESSIVE = "aggressive"      # 激进优化（最低成本）
    BALANCED = "balanced"          # 平衡优化
    QUALITY_FOCUSED = "quality_focused"  # 质量优先
    ADAPTIVE = "adaptive"          # 自适应优化


class TaskComplexity(Enum):
    """任务复杂度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ModelTier(Enum):
    """模型层级"""
    BASIC = "basic"          # 基础模型（最快最便宜）
    STANDARD = "standard"    # 标准模型
    PREMIUM = "premium"      # 高级模型
    ULTIMATE = "ultimate"    # 顶级模型（最贵最好）


@dataclass
class CostEstimate:
    """成本估算"""
    task_id: str
    task_type: str
    model_tier: ModelTier
    estimated_tokens: int
    estimated_cost_usd: float
    estimated_time_seconds: int
    quality_impact: float  # 对质量的影响 (0-1)


@dataclass
class OptimizationSuggestion:
    """优化建议"""
    suggestion_id: str
    target_task: str
    optimization_type: str
    description: str
    potential_savings: float  # 潜在节省（美元）
    quality_impact: float    # 质量影响 (0-1)
    implementation_complexity: str  # 实施复杂度


@dataclass
class CostBudget:
    """成本预算"""
    total_budget: float
    allocated_costs: Dict[str, float]
    current_spending: float
    remaining_budget: float
    warning_threshold: float = 0.8  # 警告阈值
    critical_threshold: float = 0.95  # 临界阈值


class ModelCostCalculator:
    """模型成本计算器"""

    # 模型定价（每1K tokens）
    MODEL_PRICING = {
        ModelTier.BASIC: {
            "input_cost": 0.0001,    # $0.10 per 1M tokens
            "output_cost": 0.0002,   # $0.20 per 1M tokens
            "model_name": "gpt-3.5-turbo",
            "quality_score": 0.7
        },
        ModelTier.STANDARD: {
            "input_cost": 0.0005,    # $0.50 per 1M tokens
            "output_cost": 0.0015,   # $1.50 per 1M tokens
            "model_name": "gpt-4",
            "quality_score": 0.85
        },
        ModelTier.PREMIUM: {
            "input_cost": 0.003,     # $3.00 per 1M tokens
            "output_cost": 0.012,    # $12.00 per 1M tokens
            "model_name": "gpt-4-turbo",
            "quality_score": 0.92
        },
        ModelTier.ULTIMATE: {
            "input_cost": 0.015,     # $15.00 per 1M tokens
            "output_cost": 0.060,    # $60.00 per 1M tokens
            "model_name": "claude-3-opus",
            "quality_score": 0.98
        }
    }

    @classmethod
    def calculate_cost(cls, model_tier: ModelTier, input_tokens: int, output_tokens: int) -> float:
        """计算成本"""
        pricing = cls.MODEL_PRICING[model_tier]
        input_cost = (input_tokens / 1000) * pricing["input_cost"]
        output_cost = (output_tokens / 1000) * pricing["output_cost"]
        return input_cost + output_cost

    @classmethod
    def estimate_tokens(cls, task_type: str, complexity: TaskComplexity, model_tier: ModelTier) -> Tuple[int, int]:
        """估算token数量"""
        # 基础token估算
        base_estimates = {
            "document_parsing": (500, 1500),
            "entity_extraction": (800, 2000),
            "content_generation": (1000, 2500),
            "quality_check": (600, 1200),
            "safety_review": (400, 800),
            "coordination": (300, 600)
        }

        base_input, base_output = base_estimates.get(task_type, (500, 1000))

        # 根据复杂度调整
        complexity_multipliers = {
            TaskComplexity.LOW: 0.5,
            TaskComplexity.MEDIUM: 1.0,
            TaskComplexity.HIGH: 1.5,
            TaskComplexity.CRITICAL: 2.0
        }

        multiplier = complexity_multipliers.get(complexity, 1.0)

        # 根据模型层级调整（更高级的模型通常需要更多tokens）
        tier_multipliers = {
            ModelTier.BASIC: 0.8,
            ModelTier.STANDARD: 1.0,
            ModelTier.PREMIUM: 1.2,
            ModelTier.ULTIMATE: 1.4
        }

        tier_multiplier = tier_multipliers.get(model_tier, 1.0)

        total_multiplier = multiplier * tier_multiplier

        estimated_input = int(base_input * total_multiplier)
        estimated_output = int(base_output * total_multiplier)

        return estimated_input, estimated_output

    @classmethod
    def get_quality_score(cls, model_tier: ModelTier) -> float:
        """获取模型质量分数"""
        return cls.MODEL_PRICING[model_tier]["quality_score"]

    @classmethod
    def get_model_name(cls, model_tier: ModelTier) -> str:
        """获取模型名称"""
        return cls.MODEL_PRICING[model_tier]["model_name"]


class AdaptiveCostOptimizer(BaseWorkflowNode):
    """自适应成本优化器"""

    def __init__(self):
        super().__init__(
            name="AdaptiveCostOptimizer",
            description="智能成本优化策略，平衡质量和成本效率"
        )

        # 初始化LLM客户端
        self.llm_client = LLMClient()

        # 成本计算器
        self.cost_calculator = ModelCostCalculator()

        # 成本跟踪
        self.total_spent = 0.0
        self.task_costs: Dict[str, float] = {}
        self.optimization_history: List[Dict[str, Any]] = []

        # 配置参数
        self.default_budget = 2.0  # 默认预算 $2.0
        self.cost_target_ratio = 0.8  # 目标成本比例

    async def execute(
        self,
        context: ProcessingContext,
        input_data: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[ProcessingResult, None]:
        """执行成本优化"""

        try:
            # 解析输入数据
            cache_results = input_data.get("cache_hit_results", {})
            storage_results = input_data.get("storage_results", {})
            memory_results = input_data.get("memory_results", [])
            cache_statistics = input_data.get("cache_statistics", {})

            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.RUNNING,
                success=True,
                message="开始自适应成本优化"
            )

            # 1. 分析当前成本状况
            yield ProcessingResult(
                step_name=f"{self.name}_cost_analysis",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="分析当前成本状况"
            )

            cost_analysis = await self._analyze_current_costs(
                cache_results, storage_results, memory_results, context
            )

            yield ProcessingResult(
                step_name=f"{self.name}_cost_analysis",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data=cost_analysis,
                message=f"成本分析完成，当前花费${cost_analysis['total_cost']:.4f}"
            )

            # 2. 制定成本优化策略
            yield ProcessingResult(
                step_name=f"{self.name}_strategy_formulation",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="制定成本优化策略"
            )

            optimization_strategy = await self._formulate_optimization_strategy(
                cost_analysis, context
            )

            yield ProcessingResult(
                step_name=f"{self.name}_strategy_formulation",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data=optimization_strategy,
                message=f"优化策略制定完成：{optimization_strategy['strategy_type']}"
            )

            # 3. 生成优化建议
            yield ProcessingResult(
                step_name=f"{self.name}_suggestion_generation",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="生成成本优化建议"
            )

            optimization_suggestions = await self._generate_optimization_suggestions(
                cost_analysis, optimization_strategy, context
            )

            yield ProcessingResult(
                step_name=f"{self.name}_suggestion_generation",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data={"suggestions_count": len(optimization_suggestions)},
                message=f"优化建议生成完成，共{len(optimization_suggestions)}条建议"
            )

            # 4. 实施成本优化
            yield ProcessingResult(
                step_name=f"{self.name}_optimization_implementation",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="实施成本优化措施"
            )

            implementation_results = await self._implement_optimizations(
                optimization_suggestions, context
            )

            yield ProcessingResult(
                step_name=f"{self.name}_optimization_implementation",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data=implementation_results,
                message=f"成本优化实施完成，预计节省${implementation_results['estimated_savings']:.4f}"
            )

            # 5. 生成成本报告
            yield ProcessingResult(
                step_name=f"{self.name}_cost_reporting",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="生成成本优化报告"
            )

            cost_report = await self._generate_cost_report(
                cost_analysis, optimization_strategy, optimization_suggestions, implementation_results
            )

            yield ProcessingResult(
                step_name=f"{self.name}_cost_reporting",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data=cost_report,
                message="成本优化报告生成完成"
            )

            # 生成最终结果
            final_result = {
                "cost_analysis": cost_analysis,
                "optimization_strategy": optimization_strategy,
                "optimization_suggestions": [suggestion.__dict__ for suggestion in optimization_suggestions],
                "implementation_results": implementation_results,
                "cost_report": cost_report,
                "cost_optimization_metadata": {
                    "original_cost": cost_analysis["total_cost"],
                    "optimized_cost": cost_analysis["total_cost"] - implementation_results["estimated_savings"],
                    "savings_percentage": (implementation_results["estimated_savings"] / cost_analysis["total_cost"]) * 100,
                    "optimization_time": datetime.utcnow().isoformat(),
                    "cost_level": context.cost_level.value,
                    "quality_preservation": implementation_results["quality_impact"]
                }
            }

            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.COMPLETED,
                success=True,
                data=final_result,
                message=f"成本优化完成，预计节省${implementation_results['estimated_savings']:.4f}，质量保持{implementation_results['quality_impact']:.1%}"
            )

        except Exception as e:
            logger.error(f"成本优化失败: {str(e)}")
            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.FAILED,
                success=False,
                error_message=str(e)
            )

    async def _analyze_current_costs(
        self, cache_results: Dict[str, Any], storage_results: Dict[str, Any],
        memory_results: List[Dict[str, Any]], context: ProcessingContext
    ) -> Dict[str, Any]:
        """分析当前成本状况"""
        cost_analysis = {
            "total_cost": 0.0,
            "cost_breakdown": {},
            "cache_savings": 0.0,
            "processing_costs": {},
            "efficiency_metrics": {}
        }

        try:
            # 估算缓存节省的成本
            cache_hit_count = cache_results.get("cache_hits", 0)
            cache_savings_per_hit = 0.05  # 假设每次缓存命中节省 $0.05
            cost_analysis["cache_savings"] = cache_hit_count * cache_savings_per_hit

            # 估算各处理节点的成本
            processing_tasks = [
                ("document_parser", TaskComplexity.HIGH),
                ("multimodal_processor", TaskComplexity.HIGH),
                ("knowledge_graph", TaskComplexity.CRITICAL),
                ("agent_system", TaskComplexity.CRITICAL),
                ("content_generator", TaskComplexity.HIGH),
                ("cache_system", TaskComplexity.MEDIUM)
            ]

            total_processing_cost = 0.0

            for task_name, complexity in processing_tasks:
                # 根据成本级别选择模型层级
                model_tier = self._select_model_tier_for_task(task_name, complexity, context)

                # 估算token和成本
                input_tokens, output_tokens = self.cost_calculator.estimate_tokens(
                    task_name, complexity, model_tier
                )
                task_cost = self.cost_calculator.calculate_cost(model_tier, input_tokens, output_tokens)

                cost_analysis["processing_costs"][task_name] = {
                    "model_tier": model_tier.value,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": task_cost,
                    "quality_score": self.cost_calculator.get_quality_score(model_tier)
                }

                total_processing_cost += task_cost

            cost_analysis["total_cost"] = total_processing_cost - cost_analysis["cache_savings"]
            cost_analysis["cost_breakdown"]["processing"] = total_processing_cost
            cost_analysis["cost_breakdown"]["cache_savings"] = -cost_analysis["cache_savings"]

            # 计算效率指标
            cache_hit_rate = cache_results.get("cache_hits", 0) / max(1, cache_results.get("cache_hits", 0) + cache_results.get("cache_misses", 0))
            cost_analysis["efficiency_metrics"]["cache_hit_rate"] = cache_hit_rate
            cost_analysis["efficiency_metrics"]["cost_per_task"] = total_processing_cost / len(processing_tasks)

            # 更新跟踪数据
            self.total_spent += cost_analysis["total_cost"]
            self.task_costs.update({task: data["cost"] for task, data in cost_analysis["processing_costs"].items()})

        except Exception as e:
            logger.error(f"成本分析失败: {str(e)}")

        return cost_analysis

    async def _formulate_optimization_strategy(
        self, cost_analysis: Dict[str, Any], context: ProcessingContext
    ) -> Dict[str, Any]:
        """制定优化策略"""
        try:
            # 根据成本级别和质量要求选择策略
            cost_level = context.cost_level
            quality_requirement = context.quality_requirement
            total_cost = cost_analysis["total_cost"]

            # 策略选择逻辑
            if cost_level == CostLevel.LOW:
                if quality_requirement == QualityLevel.BASIC:
                    strategy = OptimizationStrategy.AGGRESSIVE
                else:
                    strategy = OptimizationStrategy.BALANCED
            elif cost_level == CostLevel.MEDIUM:
                if quality_requirement == QualityLevel.HIGH:
                    strategy = OptimizationStrategy.QUALITY_FOCUSED
                else:
                    strategy = OptimizationStrategy.BALANCED
            else:  # HIGH cost level
                strategy = OptimizationStrategy.QUALITY_FOCUSED

            # 根据当前成本调整策略
            if total_cost > self.default_budget * 0.8:
                if strategy == OptimizationStrategy.QUALITY_FOCUSED:
                    strategy = OptimizationStrategy.BALANCED
                elif strategy == OptimizationStrategy.BALANCED:
                    strategy = OptimizationStrategy.AGGRESSIVE

            # 制定策略详情
            strategy_details = {
                "strategy_type": strategy.value,
                "cost_target": self.default_budget * self.cost_target_ratio,
                "quality_target": self._get_quality_target(quality_requirement),
                "optimization_focus": self._get_optimization_focus(strategy),
                "implementation_priority": self._get_implementation_priority(strategy)
            }

            return strategy_details

        except Exception as e:
            logger.error(f"制定优化策略失败: {str(e)}")
            return {"strategy_type": "balanced", "error": str(e)}

    async def _generate_optimization_suggestions(
        self, cost_analysis: Dict[str, Any], strategy: Dict[str, Any], context: ProcessingContext
    ) -> List[OptimizationSuggestion]:
        """生成优化建议"""
        suggestions = []

        try:
            # 基于策略生成不同类型的建议

            # 1. 模型降级建议
            for task_name, task_data in cost_analysis["processing_costs"].items():
                current_tier = ModelTier(task_data["model_tier"])
                if current_tier != ModelTier.BASIC:
                    lower_tier = self._get_lower_model_tier(current_tier)
                    if lower_tier:
                        suggestion = OptimizationSuggestion(
                            suggestion_id=f"model_downgrade_{task_name}",
                            target_task=task_name,
                            optimization_type="model_downgrade",
                            description=f"将{task_name}的模型从{current_tier.value}降级到{lower_tier.value}",
                            potential_savings=self._calculate_model_downgrade_savings(task_name, current_tier, lower_tier),
                            quality_impact=self._calculate_quality_impact(current_tier, lower_tier),
                            implementation_complexity="low"
                        )
                        suggestions.append(suggestion)

            # 2. Token优化建议
            suggestions.append(OptimizationSuggestion(
                suggestion_id="token_optimization",
                target_task="all_tasks",
                optimization_type="token_reduction",
                description="通过优化提示词和响应长度来减少token使用",
                potential_savings=cost_analysis["total_cost"] * 0.15,  # 15%节省
                quality_impact=0.05,  # 5%质量影响
                implementation_complexity="medium"
            ))

            # 3. 缓存优化建议
            cache_hit_rate = cost_analysis["efficiency_metrics"].get("cache_hit_rate", 0)
            if cache_hit_rate < 0.3:
                suggestions.append(OptimizationSuggestion(
                    suggestion_id="cache_optimization",
                    target_task="cache_system",
                    optimization_type="cache_enhancement",
                    description="增强缓存策略以提高命中率",
                    potential_savings=0.10,  # $0.10潜在节省
                    quality_impact=0.0,  # 无质量影响
                    implementation_complexity="low"
                ))

            # 4. 并行处理建议
            suggestions.append(OptimizationSuggestion(
                suggestion_id="parallel_processing",
                target_task="workflow_optimization",
                optimization_type="parallel_execution",
                description="增加并行处理以提高效率",
                potential_savings=cost_analysis["total_cost"] * 0.10,  # 10%节省
                quality_impact=0.0,  # 无质量影响
                implementation_complexity="high"
            ))

            # 按潜在节省排序
            suggestions.sort(key=lambda s: s.potential_savings, reverse=True)

        except Exception as e:
            logger.error(f"生成优化建议失败: {str(e)}")

        return suggestions

    async def _implement_optimizations(
        self, suggestions: List[OptimizationSuggestion], context: ProcessingContext
    ) -> Dict[str, Any]:
        """实施优化措施"""
        implementation_results = {
            "implemented_suggestions": [],
            "estimated_savings": 0.0,
            "quality_impact": 0.0,
            "implementation_summary": {}
        }

        try:
            # 选择实施的建议（基于成本效益）
            max_implementations = 3  # 最多实施3个建议
            total_savings = 0.0
            total_quality_impact = 0.0

            for suggestion in suggestions[:max_implementations]:
                # 检查实施复杂度和质量影响
                if suggestion.implementation_complexity == "low" or \
                   (suggestion.implementation_complexity == "medium" and suggestion.quality_impact < 0.1):

                    implementation_results["implemented_suggestions"].append({
                        "suggestion_id": suggestion.suggestion_id,
                        "description": suggestion.description,
                        "expected_savings": suggestion.potential_savings,
                        "quality_impact": suggestion.quality_impact
                    })

                    total_savings += suggestion.potential_savings
                    total_quality_impact += suggestion.quality_impact

                    # 记录优化历史
                    self.optimization_history.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "suggestion_id": suggestion.suggestion_id,
                        "savings": suggestion.potential_savings,
                        "quality_impact": suggestion.quality_impact
                    })

            implementation_results["estimated_savings"] = total_savings
            implementation_results["quality_impact"] = 1.0 - (total_quality_impact / len(implementation_results["implemented_suggestions"])) if implementation_results["implemented_suggestions"] else 1.0

            implementation_results["implementation_summary"] = {
                "total_suggestions": len(suggestions),
                "implemented_count": len(implementation_results["implemented_suggestions"]),
                "total_savings": total_savings,
                "average_quality_preservation": implementation_results["quality_impact"]
            }

        except Exception as e:
            logger.error(f"实施优化失败: {str(e)}")

        return implementation_results

    async def _generate_cost_report(
        self, cost_analysis: Dict[str, Any], strategy: Dict[str, Any],
        suggestions: List[OptimizationSuggestion], implementation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成成本报告"""
        try:
            report = {
                "executive_summary": {
                    "original_cost": cost_analysis["total_cost"],
                    "optimized_cost": cost_analysis["total_cost"] - implementation["estimated_savings"],
                    "total_savings": implementation["estimated_savings"],
                    "savings_percentage": (implementation["estimated_savings"] / cost_analysis["total_cost"]) * 100 if cost_analysis["total_cost"] > 0 else 0,
                    "quality_preservation": implementation["quality_impact"]
                },
                "detailed_analysis": cost_analysis,
                "optimization_strategy": strategy,
                "recommendations": [s.__dict__ for s in suggestions],
                "implementation_results": implementation,
                "cost_trends": {
                    "historical_spending": self.total_spent,
                    "optimization_history": self.optimization_history[-5:]  # 最近5次优化
                },
                "benchmark_metrics": {
                    "cost_per_guideline": cost_analysis["total_cost"],
                    "cache_efficiency": cost_analysis["efficiency_metrics"].get("cache_hit_rate", 0),
                    "processing_efficiency": cost_analysis["efficiency_metrics"].get("cost_per_task", 0)
                }
            }

            return report

        except Exception as e:
            logger.error(f"生成成本报告失败: {str(e)}")
            return {"error": str(e)}

    def _select_model_tier_for_task(
        self, task_name: str, complexity: TaskComplexity, context: ProcessingContext
    ) -> ModelTier:
        """为任务选择模型层级"""
        cost_level = context.cost_level
        quality_requirement = context.quality_requirement

        # 基础选择逻辑
        if cost_level == CostLevel.LOW:
            if quality_requirement == QualityLevel.BASIC:
                return ModelTier.BASIC
            else:
                return ModelTier.STANDARD
        elif cost_level == CostLevel.MEDIUM:
            if quality_requirement == QualityLevel.HIGH:
                return ModelTier.PREMIUM
            else:
                return ModelTier.STANDARD
        else:  # HIGH cost level
            return ModelTier.ULTIMATE

    def _get_quality_target(self, quality_requirement: QualityLevel) -> float:
        """获取质量目标"""
        quality_targets = {
            QualityLevel.BASIC: 0.7,
            QualityLevel.MEDIUM: 0.8,
            QualityLevel.HIGH: 0.9
        }
        return quality_targets.get(quality_requirement, 0.8)

    def _get_optimization_focus(self, strategy: OptimizationStrategy) -> List[str]:
        """获取优化重点"""
        focus_areas = {
            OptimizationStrategy.AGGRESSIVE: ["cost_reduction", "model_downgrade", "token_optimization"],
            OptimizationStrategy.BALANCED: ["cost_efficiency", "selective_optimization", "cache_improvement"],
            OptimizationStrategy.QUALITY_FOCUSED: ["quality_preservation", "targeted_savings", "process_optimization"],
            OptimizationStrategy.ADAPTIVE: ["dynamic_balancing", "real_time_adjustment", "context_aware"]
        }
        return focus_areas.get(strategy, ["balanced_optimization"])

    def _get_implementation_priority(self, strategy: OptimizationStrategy) -> List[str]:
        """获取实施优先级"""
        priorities = {
            OptimizationStrategy.AGGRESSIVE: ["high_impact", "quick_wins", "immediate_savings"],
            OptimizationStrategy.BALANCED: ["medium_impact", "sustainable", "gradual_implementation"],
            OptimizationStrategy.QUALITY_FOCUSED: ["low_risk", "quality_preserving", "selective_optimization"],
            OptimizationStrategy.ADAPTIVE: ["flexible", "responsive", "continuous_improvement"]
        }
        return priorities.get(strategy, ["standard_implementation"])

    def _get_lower_model_tier(self, current_tier: ModelTier) -> Optional[ModelTier]:
        """获取更低的模型层级"""
        tier_order = [ModelTier.ULTIMATE, ModelTier.PREMIUM, ModelTier.STANDARD, ModelTier.BASIC]
        current_index = tier_order.index(current_tier)
        if current_index < len(tier_order) - 1:
            return tier_order[current_index + 1]
        return None

    def _calculate_model_downgrade_savings(
        self, task_name: str, current_tier: ModelTier, lower_tier: ModelTier
    ) -> float:
        """计算模型降级节省"""
        # 使用默认复杂度估算
        input_tokens, output_tokens = self.cost_calculator.estimate_tokens(
            task_name, TaskComplexity.MEDIUM, current_tier
        )

        current_cost = self.cost_calculator.calculate_cost(current_tier, input_tokens, output_tokens)
        lower_cost = self.cost_calculator.calculate_cost(lower_tier, input_tokens, output_tokens)

        return current_cost - lower_cost

    def _calculate_quality_impact(self, current_tier: ModelTier, lower_tier: ModelTier) -> float:
        """计算质量影响"""
        current_quality = self.cost_calculator.get_quality_score(current_tier)
        lower_quality = self.cost_calculator.get_quality_score(lower_tier)
        return (current_quality - lower_quality) / current_quality

    def get_cost_statistics(self) -> Dict[str, Any]:
        """获取成本统计信息"""
        return {
            "total_spent": self.total_spent,
            "task_costs": self.task_costs,
            "optimization_count": len(self.optimization_history),
            "average_optimization_savings": sum(opt["savings"] for opt in self.optimization_history) / len(self.optimization_history) if self.optimization_history else 0,
            "last_optimization": self.optimization_history[-1] if self.optimization_history else None
        }

    async def estimate_workflow_cost(self, context: ProcessingContext) -> float:
        """估算整个工作流的成本"""
        total_cost = 0.0

        processing_tasks = [
            ("document_parser", TaskComplexity.HIGH),
            ("multimodal_processor", TaskComplexity.HIGH),
            ("knowledge_graph", TaskComplexity.CRITICAL),
            ("agent_system", TaskComplexity.CRITICAL),
            ("content_generator", TaskComplexity.HIGH),
            ("cache_system", TaskComplexity.MEDIUM)
        ]

        for task_name, complexity in processing_tasks:
            model_tier = self._select_model_tier_for_task(task_name, complexity, context)
            input_tokens, output_tokens = self.cost_calculator.estimate_tokens(task_name, complexity, model_tier)
            task_cost = self.cost_calculator.calculate_cost(model_tier, input_tokens, output_tokens)
            total_cost += task_cost

        return total_cost