"""
自适应成本优化系统
Adaptive Cost Optimization System
节点7：成本优化策略
"""

import re
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from app.core.logger import get_logger
from app.core.llm_client import get_llm_client
from app.schemas.medical_schemas import CostOptimizationConfig
from app.services.medical_cache import get_medical_cache

logger = get_logger(__name__)


class TaskType(str, Enum):
    """任务类型"""
    CONTENT_GENERATION = "content_generation"
    CONTENT_ANALYSIS = "content_analysis"
    CONTENT_SUMMARIZATION = "content_summarization"
    MEDICAL_TRANSLATION = "medical_translation"
    QUALITY_CHECK = "quality_check"
    PATTERN_EXTRACTION = "pattern_extraction"


class QualityRequirement(str, Enum):
    """质量要求"""
    HIGH = "high"           # 最高质量，关键医疗决策
    MEDIUM = "medium"       # 中等质量，一般医疗应用
    LOW = "low"            # 较低质量，辅助应用
    DRAFT = "draft"        # 草稿质量，内部使用


class ModelTier(str, Enum):
    """模型层级"""
    PREMIUM = "premium"     # GPT-4, Claude-3 Opus
    STANDARD = "standard"   # GPT-3.5-turbo, Claude-3 Sonnet
    ECONOMY = "economy"     # GPT-3.5-turbo-instruct, Claude-3 Haiku


@dataclass
class ModelInfo:
    """模型信息"""
    model_name: str
    tier: ModelTier
    cost_per_1k_tokens: float
    quality_score: float
    speed_score: float
    max_tokens: int
    supported_tasks: List[TaskType]

    # 性能指标
    average_latency: float = 0.0
    reliability_score: float = 1.0


@dataclass
class CostOptimizationResult:
    """成本优化结果"""
    original_model: str
    optimized_model: str
    cost_reduction: float
    estimated_savings: float

    # 质量影响
    quality_impact: float
    risk_assessment: str

    # 优化策略
    optimization_strategy: List[str]
    applied_techniques: List[str]

    # 元数据
    processing_time: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class AdaptiveCostOptimizer:
    """自适应成本优化器"""

    def __init__(self, config: Optional[CostOptimizationConfig] = None) -> None:
        self.logger = get_logger(__name__)
        self.config = config or CostOptimizationConfig()

        # 模型数据库
        self.model_database = self._initialize_model_database()

        # 成本历史
        self.cost_history: List[Dict[str, Any]] = []

        # 优化统计
        self.optimization_stats = {
            "total_optimizations": 0,
            "total_savings": 0.0,
            "average_cost_reduction": 0.0,
            "quality_degradation": 0.0
        }

        # 学习权重
        self.learning_weights = {
            "cost_importance": 0.4,
            "quality_importance": 0.4,
            "speed_importance": 0.2
        }

    def _initialize_model_database(self) -> Dict[str, ModelInfo]:
        """初始化模型数据库"""
        return {
            # Premium models
            "gpt-4": ModelInfo(
                model_name="gpt-4",
                tier=ModelTier.PREMIUM,
                cost_per_1k_tokens=0.03,
                quality_score=0.95,
                speed_score=0.7,
                max_tokens=8192,
                supported_tasks=[TaskType.CONTENT_GENERATION, TaskType.MEDICAL_TRANSLATION, TaskType.QUALITY_CHECK],
                average_latency=2.5,
                reliability_score=0.98
            ),
            "claude-3-opus": ModelInfo(
                model_name="claude-3-opus",
                tier=ModelTier.PREMIUM,
                cost_per_1k_tokens=0.015,
                quality_score=0.93,
                speed_score=0.8,
                max_tokens=4096,
                supported_tasks=[TaskType.CONTENT_GENERATION, TaskType.CONTENT_ANALYSIS],
                average_latency=2.0,
                reliability_score=0.97
            ),

            # Standard models
            "gpt-3.5-turbo": ModelInfo(
                model_name="gpt-3.5-turbo",
                tier=ModelTier.STANDARD,
                cost_per_1k_tokens=0.002,
                quality_score=0.85,
                speed_score=0.9,
                max_tokens=4096,
                supported_tasks=[
                    TaskType.CONTENT_GENERATION, TaskType.CONTENT_ANALYSIS,
                    TaskType.CONTENT_SUMMARIZATION, TaskType.QUALITY_CHECK
                ],
                average_latency=1.0,
                reliability_score=0.95
            ),
            "claude-3-sonnet": ModelInfo(
                model_name="claude-3-sonnet",
                tier=ModelTier.STANDARD,
                cost_per_1k_tokens=0.003,
                quality_score=0.88,
                speed_score=0.85,
                max_tokens=4096,
                supported_tasks=[TaskType.CONTENT_GENERATION, TaskType.CONTENT_ANALYSIS],
                average_latency=1.2,
                reliability_score=0.96
            ),

            # Economy models
            "gpt-3.5-turbo-instruct": ModelInfo(
                model_name="gpt-3.5-turbo-instruct",
                tier=ModelTier.ECONOMY,
                cost_per_1k_tokens=0.0015,
                quality_score=0.75,
                speed_score=0.95,
                max_tokens=4096,
                supported_tasks=[
                    TaskType.CONTENT_SUMMARIZATION, TaskType.PATTERN_EXTRACTION,
                    TaskType.QUALITY_CHECK
                ],
                average_latency=0.8,
                reliability_score=0.92
            ),
            "claude-3-haiku": ModelInfo(
                model_name="claude-3-haiku",
                tier=ModelTier.ECONOMY,
                cost_per_1k_tokens=0.00025,
                quality_score=0.78,
                speed_score=0.98,
                max_tokens=4096,
                supported_tasks=[
                    TaskType.CONTENT_SUMMARIZATION, TaskType.PATTERN_EXTRACTION
                ],
                average_latency=0.5,
                reliability_score=0.90
            )
        }

    async def select_optimal_model(
        self,
        task_type: TaskType,
        content_complexity: float,
        quality_requirement: QualityRequirement,
        estimated_tokens: int = 1000,
        budget_constraint: Optional[float] = None
    ) -> str:
        """选择最优模型"""
        try:
            self.logger.info(f"Selecting optimal model for task: {task_type}, quality: {quality_requirement}")

            # 筛选支持该任务的模型
            suitable_models = [
                model for model in self.model_database.values()
                if task_type in model.supported_tasks
            ]

            # 根据质量要求筛选
            min_quality = self._get_min_quality_requirement(quality_requirement)
            suitable_models = [
                model for model in suitable_models
                if model.quality_score >= min_quality
            ]

            # 根据预算约束筛选
            if budget_constraint:
                suitable_models = [
                    model for model in suitable_models
                    if model.cost_per_1k_tokens * (estimated_tokens / 1000) <= budget_constraint
                ]

            if not suitable_models:
                self.logger.warning("No suitable models found, using default fallback")
                return "gpt-3.5-turbo"

            # 计算综合评分
            scored_models = []
            for model in suitable_models:
                score = await self._calculate_model_score(
                    model, task_type, content_complexity, quality_requirement
                )
                scored_models.append((model, score))

            # 选择评分最高的模型
            scored_models.sort(key=lambda x: x[1], reverse=True)
            selected_model = scored_models[0][0].model_name

            self.logger.info(f"Selected model: {selected_model} with score: {scored_models[0][1]:.3f}")
            return selected_model

        except Exception as e:
            self.logger.error(f"Failed to select optimal model: {e}")
            return "gpt-3.5-turbo"  # 默认回退

    async def optimize_token_usage(
        self,
        content: str,
        target_reduction: float = 0.3,
        preserve_context: bool = True
    ) -> Tuple[str, CostOptimizationResult]:
        """优化token使用"""
        try:
            original_tokens = await self._estimate_tokens(content)
            target_tokens = int(original_tokens * (1 - target_reduction))

            self.logger.info(f"Optimizing content from {original_tokens} to {target_tokens} tokens")

            optimization_techniques = []
            optimized_content = content

            # 1. 移除冗余空白和格式化
            optimized_content, reduction = await self._remove_redundant_whitespace(optimized_content)
            if reduction > 0:
                optimization_techniques.append("whitespace_optimization")

            # 2. 简化表达方式
            if target_reduction > reduction:
                simplified_content, simple_reduction = await self._simplify_expressions(
                    optimized_content, target_reduction - reduction
                )
                optimized_content = simplified_content
                reduction += simple_reduction
                optimization_techniques.append("expression_simplification")

            # 3. 压缩重复内容
            if target_reduction > reduction and preserve_context:
                compressed_content, compress_reduction = await self._compress_repetitive_content(
                    optimized_content, target_reduction - reduction
                )
                optimized_content = compressed_content
                reduction += compress_reduction
                optimization_techniques.append("content_compression")

            # 4. 医学术语优化
            if target_reduction > reduction:
                medical_optimized, medical_reduction = await self._simplify_medical_terms(optimized_content)
                optimized_content = medical_optimized
                reduction += medical_reduction
                optimization_techniques.append("medical_term_optimization")

            # 计算最终结果
            final_tokens = await self._estimate_tokens(optimized_content)
            actual_reduction = (original_tokens - final_tokens) / original_tokens

            # 质量评估
            quality_impact = await self._assess_quality_impact(content, optimized_content)

            # 成本节省估算
            estimated_savings = await self._calculate_cost_savings(
                original_tokens, final_tokens, "gpt-3.5-turbo"
            )

            result = CostOptimizationResult(
                original_model="gpt-3.5-turbo",
                optimized_model="gpt-3.5-turbo",
                cost_reduction=actual_reduction,
                estimated_savings=estimated_savings,
                quality_impact=quality_impact,
                risk_assessment=self._assess_risk(quality_impact, actual_reduction),
                optimization_strategy=["token_reduction"],
                applied_techniques=optimization_techniques,
                processing_time=0.0  # 实际应用中需要计算
            )

            # 更新统计
            self._update_optimization_stats(result)

            self.logger.info(f"Token optimization completed: {actual_reduction:.2%} reduction, quality impact: {quality_impact:.3f}")
            return optimized_content, result

        except Exception as e:
            self.logger.error(f"Failed to optimize token usage: {e}")
            return content, CostOptimizationResult(
                original_model="gpt-3.5-turbo",
                optimized_model="gpt-3.5-turbo",
                cost_reduction=0.0,
                estimated_savings=0.0,
                quality_impact=0.0,
                risk_assessment="high",
                optimization_strategy=[],
                applied_techniques=[],
                processing_time=0.0
            )

    async def _simplify_medical_terms(self, content: str) -> Tuple[str, float]:
        """简化和优化医学术语"""
        try:
            # 医学术语简化映射
            medical_simplifications = {
                # 常见医学术语简化
                "hypertension": "high blood pressure",
                "myocardial infarction": "heart attack",
                "cerebrovascular accident": "stroke",
                "chronic obstructive pulmonary disease": "COPD",
                "gastroesophageal reflux disease": "GERD",
                "attention deficit hyperactivity disorder": "ADHD",
                "magnetic resonance imaging": "MRI",
                "computed tomography": "CT scan",
                "electrocardiogram": "EKG",
                "intravenous": "IV",
                "subcutaneous": "subQ",
                "intramuscular": "IM",
                "blood pressure": "BP",
                "heart rate": "HR",
                "respiratory rate": "RR",
                "body temperature": "temp",

                # 缩写词优化
                "etc.": "etc",
                "i.e.": "ie",
                "e.g.": "eg",
                "vs.": "vs",
                "Dr.": "Dr",
                "Mr.": "Mr",
                "Ms.": "Ms",
            }

            simplified_content = content
            total_reduction = 0

            # 应用医学术语简化
            for complex_term, simple_term in medical_simplifications.items():
                if complex_term in simplified_content.lower():
                    old_content = simplified_content
                    simplified_content = re.sub(
                        r'\b' + re.escape(complex_term) + r'\b',
                        simple_term,
                        simplified_content,
                        flags=re.IGNORECASE
                    )
                    reduction = len(old_content) - len(simplified_content)
                    total_reduction += reduction

            # 移除不必要的医学修饰词
            patterns_to_remove = [
                r'\bvery\s+',  # 移除"very"
                r'\bextremely\s+',  # 移除"extremely"
                r'\bsignificantly\s+',  # 移除"significantly"
                r'\bsubstantially\s+',  # 移除"substantially"
            ]

            for pattern in patterns_to_remove:
                old_content = simplified_content
                simplified_content = re.sub(pattern, '', simplified_content, flags=re.IGNORECASE)
                reduction = len(old_content) - len(simplified_content)
                total_reduction += reduction

            # 简化医学句式结构
            simplified_content = await self._simplify_medical_sentences(simplified_content)

            final_reduction = len(content) - len(simplified_content)
            reduction_percentage = final_reduction / len(content) if content else 0

            return simplified_content, reduction_percentage

        except Exception as e:
            self.logger.error(f"Failed to simplify medical terms: {e}")
            return content, 0.0

    async def _simplify_medical_sentences(self, content: str) -> str:
        """简化医学句子结构"""
        try:
            # 句式简化规则
            sentence_transformations = [
                # 被动语态转主动语态
                (r'(\w+)\s+is\s+(\w+)\s+by\s+(\w+)', r'\3 \2s \1'),
                (r'(\w+)\s+are\s+(\w+)\s+by\s+(\w+)', r'\3 \2 \1'),

                # 简化复杂的表达
                (r'it is important to note that', ''),
                (r'it should be noted that', ''),
                (r'it is worth mentioning that', ''),
                (r'as previously mentioned', ''),
                (r'in order to', 'to'),

                # 移除冗余的连接词
                (r', however,', ','),
                (r', therefore,', ','),
                (r', consequently,', ','),
                (r', in addition,', ','),
            ]

            simplified_content = content
            for pattern, replacement in sentence_transformations:
                simplified_content = re.sub(pattern, replacement, simplified_content, flags=re.IGNORECASE)

            return simplified_content

        except Exception as e:
            self.logger.error(f"Failed to simplify medical sentences: {e}")
            return content

    async def _calculate_model_score(
        self,
        model: ModelInfo,
        task_type: TaskType,
        content_complexity: float,
        quality_requirement: QualityRequirement
    ) -> float:
        """计算模型综合评分"""
        try:
            # 基础评分因素
            quality_score = model.quality_score
            cost_score = 1.0 / (model.cost_per_1k_tokens + 0.001)  # 成本越低分数越高
            speed_score = model.speed_score
            reliability_score = model.reliability_score

            # 复杂度调整
            complexity_adjustment = 1.0 - (content_complexity * 0.3)

            # 质量要求调整
            quality_multiplier = {
                QualityRequirement.HIGH: 1.5,
                QualityRequirement.MEDIUM: 1.0,
                QualityRequirement.LOW: 0.7,
                QualityRequirement.DRAFT: 0.5
            }[quality_requirement]

            # 任务类型适配性
            task_compatibility = await self._calculate_task_compatibility(model, task_type)

            # 综合评分计算
            weighted_score = (
                quality_score * self.learning_weights["quality_importance"] +
                cost_score * self.learning_weights["cost_importance"] +
                speed_score * self.learning_weights["speed_importance"]
            ) * complexity_adjustment * quality_multiplier * task_compatibility * reliability_score

            return weighted_score

        except Exception as e:
            self.logger.error(f"Failed to calculate model score: {e}")
            return 0.0

    async def _calculate_task_compatibility(self, model: ModelInfo, task_type: TaskType) -> float:
        """计算任务兼容性"""
        # 基于任务类型的兼容性评分
        compatibility_scores = {
            TaskType.CONTENT_GENERATION: {
                ModelTier.PREMIUM: 1.0,
                ModelTier.STANDARD: 0.9,
                ModelTier.ECONOMY: 0.6
            },
            TaskType.CONTENT_ANALYSIS: {
                ModelTier.PREMIUM: 0.9,
                ModelTier.STANDARD: 1.0,
                ModelTier.ECONOMY: 0.8
            },
            TaskType.CONTENT_SUMMARIZATION: {
                ModelTier.PREMIUM: 0.8,
                ModelTier.STANDARD: 0.9,
                ModelTier.ECONOMY: 1.0
            },
            TaskType.MEDICAL_TRANSLATION: {
                ModelTier.PREMIUM: 1.0,
                ModelTier.STANDARD: 0.7,
                ModelTier.ECONOMY: 0.5
            },
            TaskType.QUALITY_CHECK: {
                ModelTier.PREMIUM: 0.9,
                ModelTier.STANDARD: 1.0,
                ModelTier.ECONOMY: 0.8
            },
            TaskType.PATTERN_EXTRACTION: {
                ModelTier.PREMIUM: 0.7,
                ModelTier.STANDARD: 0.8,
                ModelTier.ECONOMY: 1.0
            }
        }

        return compatibility_scores.get(task_type, {}).get(model.tier, 0.5)

    def _get_min_quality_requirement(self, quality_requirement: QualityRequirement) -> float:
        """获取最低质量要求"""
        quality_thresholds = {
            QualityRequirement.HIGH: 0.9,
            QualityRequirement.MEDIUM: 0.8,
            QualityRequirement.LOW: 0.7,
            QualityRequirement.DRAFT: 0.6
        }
        return quality_thresholds[quality_requirement]

    async def _estimate_tokens(self, content: str) -> int:
        """估算token数量"""
        # 简单的token估算：大约每个字符0.25个token（考虑中英文混合）
        return int(len(content) * 0.4)

    async def _remove_redundant_whitespace(self, content: str) -> Tuple[str, float]:
        """移除冗余空白字符"""
        old_length = len(content)

        # 移除多余的空行和空格
        optimized = re.sub(r'\n\s*\n', '\n', content)  # 移除空行
        optimized = re.sub(r'[ \t]+', ' ', optimized)  # 合并多个空格
        optimized = re.sub(r'\n[ \t]+', '\n', optimized)  # 移除行首空格
        optimized = re.sub(r'[ \t]+\n', '\n', optimized)  # 移除行尾空格

        reduction = (old_length - len(optimized)) / old_length if old_length > 0 else 0
        return optimized.strip(), reduction

    async def _simplify_expressions(self, content: str, target_reduction: float) -> Tuple[str, float]:
        """简化表达方式"""
        # 这里可以集成LLM来简化表达
        # 目前使用基础的简化规则
        old_length = len(content)

        # 基础简化规则
        simplifications = {
            r'in order to': 'to',
            r'it is necessary to': 'must',
            r'it is important to': 'must',
            r'it should be noted that': '',
            r'it is worth mentioning that': '',
            r'as a matter of fact': '',
            r'for the purpose of': 'for',
            r'on the basis of': 'based on',
            r'with regard to': 'about',
            r'in the event that': 'if',
        }

        simplified = content
        for pattern, replacement in simplifications.items():
            simplified = re.sub(pattern, replacement, simplified, flags=re.IGNORECASE)

        reduction = (old_length - len(simplified)) / old_length if old_length > 0 else 0

        # 如果还需要更多简化，可以在这里添加更复杂的逻辑
        return simplified, reduction

    async def _compress_repetitive_content(self, content: str, target_reduction: float) -> Tuple[str, float]:
        """压缩重复内容"""
        old_length = len(content)

        # 移除重复的句子（简单实现）
        sentences = content.split('.')
        unique_sentences = []
        seen = set()

        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and sentence not in seen:
                unique_sentences.append(sentence)
                seen.add(sentence)

        compressed = '. '.join(unique_sentences)
        reduction = (old_length - len(compressed)) / old_length if old_length > 0 else 0

        return compressed, reduction

    async def _assess_quality_impact(self, original: str, optimized: str) -> float:
        """评估质量影响"""
        # 简单的长度比例评估
        length_ratio = len(optimized) / len(original) if original else 1.0

        # 检查关键信息保留情况
        original_words = set(original.lower().split())
        optimized_words = set(optimized.lower().split())

        preservation_rate = len(optimized_words & original_words) / len(original_words) if original_words else 1.0

        # 质量影响评分（1.0表示无影响，0.0表示严重影响）
        quality_impact = length_ratio * preservation_rate

        return quality_impact

    def _assess_risk(self, quality_impact: float, reduction: float) -> str:
        """评估风险等级"""
        if quality_impact > 0.9 and reduction < 0.3:
            return "low"
        elif quality_impact > 0.8 and reduction < 0.5:
            return "medium"
        else:
            return "high"

    async def _calculate_cost_savings(self, original_tokens: int, final_tokens: int, model: str) -> float:
        """计算成本节省"""
        model_info = self.model_database.get(model)
        if not model_info:
            return 0.0

        cost_per_token = model_info.cost_per_1k_tokens / 1000
        original_cost = original_tokens * cost_per_token
        final_cost = final_tokens * cost_per_token

        return original_cost - final_cost

    def _update_optimization_stats(self, result: CostOptimizationResult) -> None:
        """更新优化统计"""
        self.optimization_stats["total_optimizations"] += 1
        self.optimization_stats["total_savings"] += result.estimated_savings

        # 更新平均成本削减
        total = self.optimization_stats["total_optimizations"]
        current_avg = self.optimization_stats["average_cost_reduction"]
        new_avg = ((current_avg * (total - 1)) + result.cost_reduction) / total
        self.optimization_stats["average_cost_reduction"] = new_avg

    async def get_optimization_statistics(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        return {
            "statistics": self.optimization_stats.copy(),
            "model_database": {
                name: {
                    "tier": model.tier.value,
                    "cost_per_1k_tokens": model.cost_per_1k_tokens,
                    "quality_score": model.quality_score,
                    "supported_tasks": [task.value for task in model.supported_tasks]
                }
                for name, model in self.model_database.items()
            },
            "config": {
                "target_cost_reduction": self.config.target_cost_reduction,
                "quality_threshold": self.config.quality_threshold,
                "learning_weights": self.learning_weights
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    async def update_learning_weights(
        self,
        cost_importance: Optional[float] = None,
        quality_importance: Optional[float] = None,
        speed_importance: Optional[float] = None
    ) -> None:
        """更新学习权重"""
        if cost_importance is not None:
            self.learning_weights["cost_importance"] = max(0.0, min(1.0, cost_importance))
        if quality_importance is not None:
            self.learning_weights["quality_importance"] = max(0.0, min(1.0, quality_importance))
        if speed_importance is not None:
            self.learning_weights["speed_importance"] = max(0.0, min(1.0, speed_importance))

        # 归一化权重
        total = sum(self.learning_weights.values())
        if total > 0:
            for key in self.learning_weights:
                self.learning_weights[key] /= total

        self.logger.info(f"Updated learning weights: {self.learning_weights}")


# 全局实例
cost_optimizer = AdaptiveCostOptimizer()


async def get_cost_optimizer() -> AdaptiveCostOptimizer:
    """获取成本优化器实例"""
    return cost_optimizer