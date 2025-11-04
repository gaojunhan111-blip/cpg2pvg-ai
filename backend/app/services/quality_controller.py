"""
多层质量控制系统
Multi-Layer Quality Control System
节点8：质量控制和验证系统
"""

import asyncio
import re
import json
from collections import deque, defaultdict
import heapq
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from app.core.logger import get_logger
from app.core.llm_client import get_llm_client
from app.schemas.medical_schemas import QualityResult, QualityControlConfig
from app.services.medical_cache import get_medical_cache

logger = get_logger(__name__)


class QualityDimension(str, Enum):
    """质量维度"""
    MEDICAL_ACCURACY = "medical_accuracy"
    READABILITY = "readability"
    COMPLETENESS = "completeness"
    COHERENCE = "coherence"
    RELEVANCE = "relevance"
    SAFETY = "safety"
    EVIDENCE_LEVEL = "evidence_level"


class SeverityLevel(str, Enum):
    """问题严重程度"""
    CRITICAL = "critical"    # 关键问题，必须修复
    HIGH = "high"          # 高优先级问题
    MEDIUM = "medium"      # 中等优先级问题
    LOW = "low"           # 低优先级问题
    INFO = "info"         # 信息性提示


@dataclass
class QualityIssue:
    """质量问题"""
    issue_id: str
    dimension: QualityDimension
    severity: SeverityLevel
    description: str
    location: str  # 问题位置
    suggestion: str

    # 自动修复信息
    auto_fixable: bool = False
    fix_suggestion: str = ""

    # 上下文信息
    context: str = ""
    affected_text: str = ""

    # 时间戳
    detected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EvidenceAssessment:
    """证据评估"""
    evidence_level: str  # A, B, C, D级证据
    source_type: str     # RCT, Meta-analysis, Expert opinion等
    sample_size: int
    confidence_interval: str
    publication_year: int

    # 证据质量评分
    methodological_quality: float
    relevance_score: float
    recency_score: float


@dataclass
class ReadabilityMetrics:
    """可读性指标"""
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    average_sentence_length: float
    average_word_length: float
    complex_words_percentage: float

    # 医学可读性
    medical_terms_density: float
    technical_jargon_score: float
    patient_friendly_score: float


class MultiLayerQualityController:
    """多层质量控制器"""

    def __init__(self, config: Optional[QualityControlConfig] = None) -> None:
        self.logger = get_logger(__name__)
        self.config = config or QualityControlConfig()

        # 质量检查器
        self.quality_checkers = {
            QualityDimension.MEDICAL_ACCURACY: self._check_medical_accuracy,
            QualityDimension.READABILITY: self._check_readability,
            QualityDimension.COMPLETENESS: self._check_completeness,
            QualityDimension.COHERENCE: self._check_coherence,
            QualityDimension.SAFETY: self._check_safety,
            QualityDimension.EVIDENCE_LEVEL: self._check_evidence_level
        }

        # 医学术语词典
        self.medical_dictionary = self._initialize_medical_dictionary()

        # 常见医学错误模式
        self.error_patterns = self._initialize_error_patterns()

        # 使用deque替代list，提高头部删除效率
        self.quality_history: deque = deque(maxlen=1000)  # 自动限制大小

        # 使用defaultdict避免重复检查键存在
        self.quality_dimension_stats = defaultdict(lambda: {
            "checks": 0, "issues": 0, "avg_score": 0.0
        })

        # 使用堆维护top-N问题
        self.critical_issues_heap = []  # 最小堆，保持最重要的100个问题

        # 统计信息
        self.quality_stats = {
            "total_checks": 0,
            "issues_found": 0,
            "auto_fixes_applied": 0,
            "average_quality_score": 0.0,
            "critical_issues_prevented": 0
        }

    async def validate_pvg_quality(
        self,
        original_cpg: str,
        generated_pvg: str
    ) -> QualityResult:
        """验证PVG质量"""
        try:
            self.logger.info("Starting comprehensive PVG quality validation")
            start_time = datetime.utcnow()

            # 并行执行多层质量检查
            quality_issues = []
            dimension_scores = {}

            # 准备并行检查任务
            check_tasks = []
            dimensions_to_check = []

            for dimension, checker in self.quality_checkers.items():
                if self._should_check_dimension(dimension):
                    check_tasks.append(checker(original_cpg, generated_pvg))
                    dimensions_to_check.append(dimension)

            # 并行执行所有检查
            self.logger.info(f"Executing {len(check_tasks)} quality checks in parallel")
            check_results = await asyncio.gather(*check_tasks, return_exceptions=True)

            # 处理结果
            for i, result in enumerate(check_results):
                if isinstance(result, Exception):
                    self.logger.error(f"Quality check {dimensions_to_check[i]} failed: {result}")
                    dimension_scores[dimensions_to_check[i].value] = 0.0
                    # 添加错误问题
                    quality_issues.append(QualityIssue(
                        issue_id=f"check_error_{dimensions_to_check[i].value}",
                        dimension=dimensions_to_check[i],
                        severity=SeverityLevel.MEDIUM,
                        description=f"Quality check failed: {str(result)}",
                        location="system",
                        suggestion="Manual review recommended",
                        auto_fixable=False
                    ))
                else:
                    issues, score = result
                    quality_issues.extend(issues)
                    dimension_scores[dimensions_to_check[i].value] = score

            # 计算综合评分
            overall_score = self._calculate_overall_score(dimension_scores)

            # 生成建议和推荐
            suggestions, recommendations = await self._generate_recommendations(
                quality_issues, dimension_scores
            )

            # 内容相似度和保留度分析
            similarity_score = await self._calculate_similarity(original_cpg, generated_pvg)
            content_preservation = await self._calculate_content_preservation(
                original_cpg, generated_pvg
            )
            information_loss = await self._identify_information_loss(
                original_cpg, generated_pvg
            )

            # 质量问题按严重程度分组
            issues_by_severity = self._group_issues_by_severity(quality_issues)

            # 检查是否需要自动修复
            if self.config.enable_auto_correction:
                await self._apply_auto_fixes(generated_pvg, quality_issues)

            # 构建结果
            result = QualityResult(
                overall_score=overall_score,
                medical_accuracy=dimension_scores.get(QualityDimension.MEDICAL_ACCURACY.value, 0.0),
                readability_score=dimension_scores.get(QualityDimension.READABILITY.value, 0.0),
                completeness_score=dimension_scores.get(QualityDimension.COMPLETENESS.value, 0.0),
                coherence_score=dimension_scores.get(QualityDimension.COHERENCE.value, 0.0),
                issues_found=[issue.description for issue in quality_issues],
                suggestions=suggestions,
                recommendations=recommendations,
                similarity_score=similarity_score,
                content_preservation=content_preservation,
                information_loss=information_loss,
                evaluated_at=datetime.utcnow(),
                evaluation_time=(datetime.utcnow() - start_time).total_seconds()
            )

            # 更新统计
            await self._update_quality_stats(result, len(quality_issues))

            self.logger.info(f"PVG quality validation completed: overall score {overall_score:.3f}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to validate PVG quality: {e}")
            # 返回默认的失败结果
            return QualityResult(
                overall_score=0.0,
                medical_accuracy=0.0,
                readability_score=0.0,
                completeness_score=0.0,
                coherence_score=0.0,
                issues_found=["Quality validation failed"],
                suggestions=["Retry generation process"],
                recommendations=["Review input data"],
                similarity_score=0.0,
                content_preservation=0.0,
                information_loss=["All content"],
                evaluated_at=datetime.utcnow(),
                evaluation_time=0.0
            )

    async def _check_medical_accuracy(self, original: str, generated: str) -> Tuple[List[QualityIssue], float]:
        """检查医学准确性"""
        issues = []
        accuracy_score = 1.0

        try:
            # 1. 检查关键医学概念的准确性
            medical_concepts = await self._extract_medical_concepts(original)
            for concept in medical_concepts:
                if concept not in generated:
                    issues.append(QualityIssue(
                        issue_id=f"missing_concept_{concept}",
                        dimension=QualityDimension.MEDICAL_ACCURACY,
                        severity=SeverityLevel.HIGH,
                        description=f"Missing critical medical concept: {concept}",
                        location="content",
                        suggestion=f"Include proper explanation of {concept}",
                        auto_fixable=False
                    ))
                    accuracy_score -= 0.1

            # 2. 检查剂量和数值信息的准确性
            dosage_issues = await self._check_dosage_accuracy(original, generated)
            issues.extend(dosage_issues)
            accuracy_score -= len(dosage_issues) * 0.05

            # 3. 检查禁忌症和警告信息
            warning_issues = await self._check_safety_warnings(original, generated)
            issues.extend(warning_issues)
            accuracy_score -= len(warning_issues) * 0.15

            # 4. 使用LLM进行深度准确性检查
            llm_issues, llm_score = await self._llm_medical_accuracy_check(original, generated)
            issues.extend(llm_issues)
            accuracy_score = (accuracy_score + llm_score) / 2

            accuracy_score = max(0.0, accuracy_score)

        except Exception as e:
            self.logger.error(f"Medical accuracy check failed: {e}")
            issues.append(QualityIssue(
                issue_id="accuracy_check_error",
                dimension=QualityDimension.MEDICAL_ACCURACY,
                severity=SeverityLevel.MEDIUM,
                description=f"Medical accuracy check encountered an error: {str(e)}",
                location="system",
                suggestion="Manual review recommended",
                auto_fixable=False
            ))

        return issues, accuracy_score

    async def _check_readability(self, original: str, generated: str) -> Tuple[List[QualityIssue], float]:
        """检查可读性"""
        issues = []
        readability_score = 1.0

        try:
            # 计算可读性指标
            metrics = await self._calculate_readability_metrics(generated)

            # 检查Flesch-Kincaid年级水平
            if metrics.flesch_kincaid_grade > 12:  # 高中以上
                issues.append(QualityIssue(
                    issue_id="complex_reading_level",
                    dimension=QualityDimension.READABILITY,
                    severity=SeverityLevel.MEDIUM,
                    description=f"Reading level too high: {metrics.flesch_kincaid_grade:.1f} grade",
                    location="content",
                    suggestion="Simplify sentence structure and vocabulary",
                    auto_fixable=True
                ))
                readability_score -= 0.2

            # 检查平均句子长度
            if metrics.average_sentence_length > 20:
                issues.append(QualityIssue(
                    issue_id="long_sentences",
                    dimension=QualityDimension.READABILITY,
                    severity=SeverityLevel.LOW,
                    description=f"Average sentence length too long: {metrics.average_sentence_length:.1f} words",
                    location="content",
                    suggestion="Break long sentences into shorter ones",
                    auto_fixable=True
                ))
                readability_score -= 0.1

            # 检查医学术语密度
            if metrics.medical_terms_density > 0.15:  # 15%以上是医学术语
                issues.append(QualityIssue(
                    issue_id="high_medical_jargon",
                    dimension=QualityDimension.READABILITY,
                    severity=SeverityLevel.MEDIUM,
                    description=f"Medical jargon density too high: {metrics.medical_terms_density:.1%}",
                    location="content",
                    suggestion="Consider explaining medical terms or using simpler language",
                    auto_fixable=True
                ))
                readability_score -= 0.15

            # 检查患者友好性
            if metrics.patient_friendly_score < 0.7:
                issues.append(QualityIssue(
                    issue_id="low_patient_friendliness",
                    dimension=QualityDimension.READABILITY,
                    severity=SeverityLevel.LOW,
                    description="Content may not be patient-friendly",
                    location="content",
                    suggestion="Add explanations or use analogies for complex medical concepts",
                    auto_fixable=False
                ))
                readability_score -= 0.1

            readability_score = max(0.0, readability_score)

        except Exception as e:
            self.logger.error(f"Readability check failed: {e}")
            issues.append(QualityIssue(
                issue_id="readability_check_error",
                dimension=QualityDimension.READABILITY,
                severity=SeverityLevel.LOW,
                description=f"Readability check encountered an error: {str(e)}",
                location="system",
                suggestion="Manual readability assessment recommended",
                auto_fixable=False
            ))

        return issues, readability_score

    async def _check_completeness(self, original: str, generated: str) -> Tuple[List[QualityIssue], float]:
        """检查完整性"""
        issues = []
        completeness_score = 1.0

        try:
            # 提取原始文档的关键章节和元素
            original_elements = await self._extract_key_elements(original)
            generated_elements = await self._extract_key_elements(generated)

            # 检查缺失的关键元素
            missing_elements = set(original_elements) - set(generated_elements)
            for element in missing_elements:
                severity = SeverityLevel.HIGH if "critical" in element.lower() else SeverityLevel.MEDIUM
                issues.append(QualityIssue(
                    issue_id=f"missing_element_{element}",
                    dimension=QualityDimension.COMPLETENESS,
                    severity=severity,
                    description=f"Missing key element: {element}",
                    location="content",
                    suggestion=f"Add the {element} section",
                    auto_fixable=False
                ))
                completeness_score -= 0.15

            # 检查结构完整性
            structure_issues = await self._check_structure_completeness(original, generated)
            issues.extend(structure_issues)
            completeness_score -= len(structure_issues) * 0.1

            # 检查信息深度
            depth_issues = await self._check_information_depth(original, generated)
            issues.extend(depth_issues)
            completeness_score -= len(depth_issues) * 0.05

            completeness_score = max(0.0, completeness_score)

        except Exception as e:
            self.logger.error(f"Completeness check failed: {e}")
            issues.append(QualityIssue(
                issue_id="completeness_check_error",
                dimension=QualityDimension.COMPLETENESS,
                severity=SeverityLevel.MEDIUM,
                description=f"Completeness check encountered an error: {str(e)}",
                location="system",
                suggestion="Manual completeness review required",
                auto_fixable=False
            ))

        return issues, completeness_score

    async def _check_coherence(self, original: str, generated: str) -> Tuple[List[QualityIssue], float]:
        """检查连贯性"""
        issues = []
        coherence_score = 1.0

        try:
            # 检查段落间的逻辑连接
            connection_issues = await self._check_logical_connections(generated)
            issues.extend(connection_issues)
            coherence_score -= len(connection_issues) * 0.1

            # 检查术语一致性
            terminology_issues = await self._check_terminology_consistency(generated)
            issues.extend(terminology_issues)
            coherence_score -= len(terminology_issues) * 0.08

            # 检查时间线一致性
            timeline_issues = await self._check_timeline_consistency(generated)
            issues.extend(timeline_issues)
            coherence_score -= len(timeline_issues) * 0.12

            # 检查因果关系逻辑
            causality_issues = await self._check_causality_logic(generated)
            issues.extend(causality_issues)
            coherence_score -= len(causality_issues) * 0.15

            coherence_score = max(0.0, coherence_score)

        except Exception as e:
            self.logger.error(f"Coherence check failed: {e}")
            issues.append(QualityIssue(
                issue_id="coherence_check_error",
                dimension=QualityDimension.COHERENCE,
                severity=SeverityLevel.MEDIUM,
                description=f"Coherence check encountered an error: {str(e)}",
                location="system",
                suggestion="Manual coherence review recommended",
                auto_fixable=False
            ))

        return issues, coherence_score

    async def _check_safety(self, original: str, generated: str) -> Tuple[List[QualityIssue], float]:
        """检查安全性"""
        issues = []
        safety_score = 1.0

        try:
            # 检查缺失的安全警告
            original_warnings = await self._extract_safety_warnings(original)
            generated_warnings = await self._extract_safety_warnings(generated)

            missing_warnings = set(original_warnings) - set(generated_warnings)
            for warning in missing_warnings:
                issues.append(QualityIssue(
                    issue_id=f"missing_safety_warning_{warning}",
                    dimension=QualityDimension.SAFETY,
                    severity=SeverityLevel.CRITICAL,
                    description=f"Missing critical safety warning: {warning}",
                    location="content",
                    suggestion=f"Add safety warning about {warning}",
                    auto_fixable=False
                ))
                safety_score -= 0.25

            # 检查禁忌症信息
            contraindication_issues = await self._check_contraindications(original, generated)
            issues.extend(contraindication_issues)
            safety_score -= len(contraindication_issues) * 0.2

            # 检查药物相互作用
            interaction_issues = await self._check_drug_interactions(original, generated)
            issues.extend(interaction_issues)
            safety_score -= len(interaction_issues) * 0.18

            safety_score = max(0.0, safety_score)

        except Exception as e:
            self.logger.error(f"Safety check failed: {e}")
            issues.append(QualityIssue(
                issue_id="safety_check_error",
                dimension=QualityDimension.SAFETY,
                severity=SeverityLevel.HIGH,
                description=f"Safety check encountered an error: {str(e)}",
                location="system",
                suggestion="Manual safety review required",
                auto_fixable=False
            ))

        return issues, safety_score

    async def _check_evidence_level(self, original: str, generated: str) -> Tuple[List[QualityIssue], float]:
        """检查证据等级"""
        issues = []
        evidence_score = 1.0

        try:
            # 提取和比较证据等级信息
            original_evidence = await self._extract_evidence_levels(original)
            generated_evidence = await self._extract_evidence_levels(generated)

            # 检查证据等级缺失
            for finding, evidence in original_evidence.items():
                if finding not in generated_evidence:
                    issues.append(QualityIssue(
                        issue_id=f"missing_evidence_{finding}",
                        dimension=QualityDimension.EVIDENCE_LEVEL,
                        severity=SeverityLevel.MEDIUM,
                        description=f"Missing evidence level for: {finding}",
                        location="content",
                        suggestion=f"Add evidence level information for {finding}",
                        auto_fixable=False
                    ))
                    evidence_score -= 0.1

            # 检查证据等级准确性
            for finding, evidence in generated_evidence.items():
                if finding in original_evidence:
                    if evidence.level != original_evidence[finding].level:
                        issues.append(QualityIssue(
                            issue_id=f"incorrect_evidence_level_{finding}",
                            dimension=QualityDimension.EVIDENCE_LEVEL,
                            severity=SeverityLevel.HIGH,
                            description=f"Incorrect evidence level for {finding}: {evidence.level}",
                            location="content",
                            suggestion=f"Correct evidence level to {original_evidence[finding].level}",
                            auto_fixable=True
                        ))
                        evidence_score -= 0.15

            evidence_score = max(0.0, evidence_score)

        except Exception as e:
            self.logger.error(f"Evidence level check failed: {e}")
            issues.append(QualityIssue(
                issue_id="evidence_check_error",
                dimension=QualityDimension.EVIDENCE_LEVEL,
                severity=SeverityLevel.MEDIUM,
                description=f"Evidence level check encountered an error: {str(e)}",
                location="system",
                suggestion="Manual evidence review required",
                auto_fixable=False
            ))

        return issues, evidence_score

    async def _calculate_readability_metrics(self, content: str) -> ReadabilityMetrics:
        """计算可读性指标"""
        try:
            # 分句和分词
            sentences = [s.strip() for s in content.split('.') if s.strip()]
            words = content.split()

            # 基础指标
            total_words = len(words)
            total_sentences = len(sentences)
            total_syllables = sum(self._count_syllables(word) for word in words)

            # Flesch Reading Ease
            if total_sentences == 0 or total_words == 0:
                flesch_reading_ease = 0
            else:
                flesch_reading_ease = 206.835 - (1.015 * total_words / total_sentences) - (84.6 * total_syllables / total_words)

            # Flesch-Kincaid Grade Level
            if total_sentences == 0 or total_words == 0:
                flesch_kincaid_grade = 0
            else:
                flesch_kincaid_grade = (0.39 * total_words / total_sentences) + (11.8 * total_syllables / total_words)

            # 平均句长和词长
            average_sentence_length = total_words / total_sentences if total_sentences > 0 else 0
            average_word_length = sum(len(word) for word in words) / total_words if total_words > 0 else 0

            # 复杂词比例（超过3个音节的词）
            complex_words = sum(1 for word in words if self._count_syllables(word) > 3)
            complex_words_percentage = complex_words / total_words if total_words > 0 else 0

            # 医学可读性指标
            medical_terms = [word for word in words if word.lower() in self.medical_dictionary]
            medical_terms_density = len(medical_terms) / total_words if total_words > 0 else 0

            technical_jargon_score = await self._assess_technical_jargon(content)
            patient_friendly_score = await self._assess_patient_friendliness(content)

            return ReadabilityMetrics(
                flesch_reading_ease=flesch_reading_ease,
                flesch_kincaid_grade=flesch_kincaid_grade,
                average_sentence_length=average_sentence_length,
                average_word_length=average_word_length,
                complex_words_percentage=complex_words_percentage,
                medical_terms_density=medical_terms_density,
                technical_jargon_score=technical_jargon_score,
                patient_friendly_score=patient_friendly_score
            )

        except Exception as e:
            self.logger.error(f"Failed to calculate readability metrics: {e}")
            return ReadabilityMetrics(0, 0, 0, 0, 0, 0, 0, 0)

    def _count_syllables(self, word: str) -> int:
        """计算音节数（简化版）"""
        word = word.lower()
        vowels = "aeiouy"
        syllable_count = 0
        prev_char_was_vowel = False

        for char in word:
            if char in vowels:
                if not prev_char_was_vowel:
                    syllable_count += 1
                prev_char_was_vowel = True
            else:
                prev_char_was_vowel = False

        # 至少有一个音节
        return max(1, syllable_count)

    async def _initialize_medical_dictionary(self) -> set:
        """初始化医学术语词典"""
        # 这里应该从实际医学词典加载，目前使用简化版本
        return {
            "hypertension", "diabetes", "myocardial", "infarction", "cerebrovascular",
            "stroke", "pneumonia", "asthma", "copd", "arthritis", "osteoporosis",
            "cholesterol", "triglycerides", "electrocardiogram", "magnetic", "resonance",
            "computed", "tomography", "ultrasound", "endoscopy", "biopsy", "pathology",
            "pharmacology", "toxicology", "epidemiology", "physiology", "anatomy"
        }

    def _initialize_error_patterns(self) -> List[Dict[str, Any]]:
        """初始化常见医学错误模式"""
        return [
            {
                "pattern": r"(\d+)\s*mg\s*(?:per|/)\s*kg",
                "type": "dosage",
                "severity": "high",
                "description": "Check dosage calculation and units"
            },
            {
                "pattern": r"(\d+)\s*%\s*of\s*patients",
                "type": "statistics",
                "severity": "medium",
                "description": "Verify statistical accuracy"
            },
            {
                "pattern": r"contraindicated?\s+in",
                "type": "contraindication",
                "severity": "critical",
                "description": "Critical contraindication information"
            }
        ]

    async def _should_check_dimension(self, dimension: QualityDimension) -> bool:
        """判断是否应该检查该维度"""
        dimension_configs = {
            QualityDimension.MEDICAL_ACCURACY: self.config.check_medical_accuracy,
            QualityDimension.READABILITY: self.config.check_readability,
            QualityDimension.COMPLETENESS: self.config.check_completeness,
            QualityDimension.COHERENCE: self.config.check_coherence,
        }
        return dimension_configs.get(dimension, True)

    def _calculate_overall_score(self, dimension_scores: Dict[str, float]) -> float:
        """计算综合质量评分"""
        if not dimension_scores:
            return 0.0

        # 权重分配
        weights = {
            "medical_accuracy": 0.3,
            "readability": 0.2,
            "completeness": 0.25,
            "coherence": 0.15,
            "safety": 0.1
        }

        weighted_score = 0.0
        total_weight = 0.0

        for dimension, score in dimension_scores.items():
            weight = weights.get(dimension, 0.1)
            weighted_score += score * weight
            total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0.0

    async def _generate_recommendations(
        self,
        issues: List[QualityIssue],
        dimension_scores: Dict[str, float]
    ) -> Tuple[List[str], List[str]]:
        """生成建议和推荐"""
        suggestions = []
        recommendations = []

        # 基于问题生成建议
        critical_issues = [i for i in issues if i.severity == SeverityLevel.CRITICAL]
        if critical_issues:
            suggestions.append("Address critical issues immediately before deployment")

        high_issues = [i for i in issues if i.severity == SeverityLevel.HIGH]
        if high_issues:
            suggestions.append("Review and fix high-priority issues")

        # 基于评分生成推荐
        low_scores = [(dim, score) for dim, score in dimension_scores.items() if score < 0.7]
        for dimension, score in low_scores:
            if dimension == "medical_accuracy":
                recommendations.append("Consider medical expert review for accuracy improvements")
            elif dimension == "readability":
                recommendations.append("Simplify language and improve structure")
            elif dimension == "completeness":
                recommendations.append("Add missing information and expand sections")
            elif dimension == "coherence":
                recommendations.append("Improve logical flow and consistency")

        return suggestions, recommendations

    async def _calculate_similarity(self, original: str, generated: str) -> float:
        """计算相似度"""
        # 简化的相似度计算
        original_words = set(original.lower().split())
        generated_words = set(generated.lower().split())

        intersection = original_words & generated_words
        union = original_words | generated_words

        return len(intersection) / len(union) if union else 0.0

    async def _calculate_content_preservation(self, original: str, generated: str) -> float:
        """计算内容保留度"""
        # 提取关键信息并比较保留程度
        original_key_info = await self._extract_key_information(original)
        generated_key_info = await self._extract_key_information(generated)

        preserved_info = set(original_key_info) & set(generated_key_info)
        return len(preserved_info) / len(original_key_info) if original_key_info else 0.0

    async def _identify_information_loss(self, original: str, generated: str) -> List[str]:
        """识别信息损失"""
        original_info = await self._extract_key_information(original)
        generated_info = await self._extract_key_information(generated)

        lost_info = set(original_info) - set(generated_info)
        return list(lost_info)[:10]  # 返回前10个丢失的信息

    def _group_issues_by_severity(self, issues: List[QualityIssue]) -> Dict[SeverityLevel, List[QualityIssue]]:
        """按严重程度分组问题"""
        grouped = {
            SeverityLevel.CRITICAL: [],
            SeverityLevel.HIGH: [],
            SeverityLevel.MEDIUM: [],
            SeverityLevel.LOW: [],
            SeverityLevel.INFO: []
        }

        for issue in issues:
            grouped[issue.severity].append(issue)

        return grouped

    async def _update_quality_stats(self, result: QualityResult, issues_count: int) -> None:
        """优化的质量统计更新"""
        # 原子性更新统计，使用更高效的计算
        total = self.quality_stats["total_checks"] + 1

        # 使用增量计算平均值，避免重复计算
        current_avg = self.quality_stats["average_quality_score"]
        new_avg = (current_avg * (total - 1) + result.overall_score) / total

        # 批量更新统计数据
        self.quality_stats.update({
            "total_checks": total,
            "issues_found": self.quality_stats["issues_found"] + issues_count,
            "average_quality_score": new_avg
        })

        # 使用deque appendleft提高插入效率
        self.quality_history.appendleft({
            "timestamp": datetime.utcnow().isoformat(),
            "overall_score": result.overall_score,
            "issues_count": issues_count,
            "similarity_score": result.similarity_score
        })

    # 辅助方法的简化实现
    async def _extract_medical_concepts(self, text: str) -> List[str]:
        """提取医学概念"""
        # 简化实现，实际应使用NLP技术
        medical_terms = []
        for term in self.medical_dictionary:
            if term.lower() in text.lower():
                medical_terms.append(term)
        return medical_terms

    async def _check_dosage_accuracy(self, original: str, generated: str) -> List[QualityIssue]:
        """检查剂量准确性"""
        issues = []
        # 简化实现
        return issues

    async def _check_safety_warnings(self, original: str, generated: str) -> List[QualityIssue]:
        """检查安全警告"""
        issues = []
        # 简化实现
        return issues

    async def _llm_medical_accuracy_check(self, original: str, generated: str) -> Tuple[List[QualityIssue], float]:
        """使用LLM进行医学准确性检查"""
        issues = []
        # 这里可以调用LLM进行深度检查
        return issues, 0.8  # 默认分数

    async def _extract_key_elements(self, text: str) -> List[str]:
        """提取关键元素"""
        elements = []
        # 简化实现，提取章节标题等
        lines = text.split('\n')
        for line in lines:
            if len(line) < 100 and any(keyword in line.lower() for keyword in ['background', 'methods', 'results', 'conclusion']):
                elements.append(line.strip())
        return elements

    async def _check_structure_completeness(self, original: str, generated: str) -> List[QualityIssue]:
        """检查结构完整性"""
        issues = []
        # 简化实现
        return issues

    async def _check_information_depth(self, original: str, generated: str) -> List[QualityIssue]:
        """检查信息深度"""
        issues = []
        # 简化实现
        return issues

    async def _check_logical_connections(self, text: str) -> List[QualityIssue]:
        """检查逻辑连接"""
        issues = []
        # 简化实现
        return issues

    async def _check_terminology_consistency(self, text: str) -> List[QualityIssue]:
        """检查术语一致性"""
        issues = []
        # 简化实现
        return issues

    async def _check_timeline_consistency(self, text: str) -> List[QualityIssue]:
        """检查时间线一致性"""
        issues = []
        # 简化实现
        return issues

    async def _check_causality_logic(self, text: str) -> List[QualityIssue]:
        """检查因果关系逻辑"""
        issues = []
        # 简化实现
        return issues

    async def _extract_safety_warnings(self, text: str) -> List[str]:
        """提取安全警告"""
        warnings = []
        # 简化实现
        return warnings

    async def _check_contraindications(self, original: str, generated: str) -> List[QualityIssue]:
        """检查禁忌症"""
        issues = []
        # 简化实现
        return issues

    async def _check_drug_interactions(self, original: str, generated: str) -> List[QualityIssue]:
        """检查药物相互作用"""
        issues = []
        # 简化实现
        return issues

    async def _extract_evidence_levels(self, text: str) -> Dict[str, EvidenceAssessment]:
        """提取证据等级"""
        evidence = {}
        # 简化实现
        return evidence

    async def _assess_technical_jargon(self, text: str) -> float:
        """评估技术术语使用"""
        # 简化实现
        return 0.5

    async def _assess_patient_friendliness(self, text: str) -> float:
        """评估患者友好性"""
        # 简化实现
        return 0.7

    async def _extract_key_information(self, text: str) -> List[str]:
        """提取关键信息"""
        # 简化实现
        return text.split('.')[:10]  # 返回前10个句子

    async def _apply_auto_fixes(self, content: str, issues: List[QualityIssue]) -> str:
        """应用自动修复"""
        # 简化实现，实际应该根据问题类型进行修复
        return content


# 全局实例
quality_controller = MultiLayerQualityController()


async def get_quality_controller() -> MultiLayerQualityController:
    """获取质量控制器实例"""
    return quality_controller