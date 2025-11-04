"""
MultiModalProcessor 实现方法（续）
MultiModalProcessor Implementation Methods (Continued)
"""

import re
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .multimodal_processor import (
    MultiModalProcessor, TextProcessingResult, ProcessedTable, ProcessedAlgorithm,
    ProcessedContent, CrossModalRelationship, ContentModality, TableType, AlgorithmType,
    ClinicalImportance, ProcessingStatus, ProcessingMetrics
)
from .medical_parser import DocumentSection, MedicalTable, ClinicalAlgorithm


class MultiModalProcessorImplementation:
    """MultiModalProcessor 实现细节"""

    # 文本章节处理方法
    def _process_single_text_section(self, section: DocumentSection) -> TextProcessingResult:
        """处理单个文本章节"""
        start_time = time.time()

        result = TextProcessingResult(
            section_id=section.section_id,
            section_type=section.section_type.value,
            original_content=section.content,
            status=ProcessingStatus.PROCESSING
        )

        try:
            # 1. 基础文本处理
            processed_content = self._clean_and_normalize_text(section.content)
            result.processed_content = processed_content

            # 2. 提取关键点
            result.key_points = self._extract_key_points(processed_content)

            # 3. 生成摘要
            result.summary = self._generate_text_summary(processed_content)

            # 4. 提取医学实体
            result.medical_entities = self._extract_medical_entities(processed_content)

            # 5. 识别临床概念
            result.clinical_concepts = self._identify_clinical_concepts(processed_content)

            # 6. 确定证据等级
            if section.evidence_level:
                result.evidence_level = section.evidence_level.value

            # 7. 提取推荐强度
            result.recommendation_strength = self._extract_recommendation_strength(processed_content)

            # 8. 查找交叉引用
            result.cross_references = self._find_cross_references(processed_content)

            # 计算处理指标
            processing_time = time.time() - start_time
            result.metrics = ProcessingMetrics(
                processing_time=processing_time,
                tokens_used=len(processed_content.split()),
                api_calls=1,
                confidence_score=self._calculate_confidence_score(result),
                quality_score=self._calculate_text_quality_score(result)
            )

            result.status = ProcessingStatus.COMPLETED
            result.processing_log.append("Text processing completed successfully")

        except Exception as e:
            result.status = ProcessingStatus.FAILED
            result.processing_log.append(f"Text processing failed: {str(e)}")
            result.metrics.processing_time = time.time() - start_time

        return result

    # 表格处理方法
    def _process_single_table(self, table: MedicalTable) -> ProcessedTable:
        """处理单个表格"""
        start_time = time.time()

        result = ProcessedTable(
            table_id=table.table_id,
            original_table=table,
            title=table.title,
            table_type=self._classify_table_type(table),
            clinical_importance=self._assess_table_clinical_importance(table),
            status=ProcessingStatus.PROCESSING
        )

        try:
            # 1. 结构化数据提取
            result.structured_data = self._extract_structured_table_data(table)

            # 2. 生成表格解释
            result.interpretation = self._generate_table_interpretation(table, result.structured_data)

            # 3. 生成表格摘要
            result.summary = self._generate_table_summary(table, result.interpretation)

            # 4. 提取关键发现
            result.key_findings = self._extract_table_key_findings(result.structured_data)

            # 5. 分析临床背景
            result.clinical_context = self._analyze_table_clinical_context(table)

            # 6. 确定目标人群
            result.target_population = self._identify_table_target_population(table)

            # 7. 提取适用条件
            result.applicability_conditions = self._extract_applicability_conditions(table)

            # 8. 确定证据等级
            if table.evidence_level:
                result.evidence_level = table.evidence_level.value

            # 9. 提取来源引用
            result.source_references = self._extract_table_references(table)

            # 10. 评估数据质量
            result.completeness_score = self._assess_table_completeness(table)
            result.accuracy_score = self._assess_table_accuracy(result.structured_data)

            # 计算处理指标
            processing_time = time.time() - start_time
            result.metrics = ProcessingMetrics(
                processing_time=processing_time,
                tokens_used=len(table.content_text.split()),
                api_calls=2,  # interpretation + summary
                confidence_score=self._calculate_table_confidence_score(result),
                quality_score=self._calculate_table_quality_score(result)
            )

            result.status = ProcessingStatus.COMPLETED
            result.processing_log.append("Table processing completed successfully")

        except Exception as e:
            result.status = ProcessingStatus.FAILED
            result.processing_log.append(f"Table processing failed: {str(e)}")
            result.metrics.processing_time = time.time() - start_time

        return result

    # 算法处理方法
    def _process_single_algorithm(self, algorithm: ClinicalAlgorithm) -> ProcessedAlgorithm:
        """处理单个算法"""
        start_time = time.time()

        result = ProcessedAlgorithm(
            algorithm_id=algorithm.algorithm_id,
            original_algorithm=algorithm,
            title=algorithm.title,
            algorithm_type=self._classify_algorithm_type(algorithm),
            clinical_importance=self._assess_algorithm_clinical_importance(algorithm),
            status=ProcessingStatus.PROCESSING
        )

        try:
            # 1. 结构化步骤
            result.structured_steps = self._structure_algorithm_steps(algorithm.steps)

            # 2. 构建决策树
            result.decision_tree = self._build_decision_tree(algorithm.decision_points, algorithm.steps)

            # 3. 生成流程图表示
            result.flowchart_representation = self._generate_flowchart_representation(algorithm)

            # 4. 生成算法摘要
            result.algorithm_summary = self._generate_algorithm_summary(algorithm)

            # 5. 提取关键决策点
            result.key_decision_points = self._extract_key_decision_points(algorithm.decision_points)

            # 6. 分析分支逻辑
            result.branching_logic = self._analyze_branching_logic(algorithm.decision_points)

            # 7. 分析临床背景
            result.clinical_context = self._analyze_algorithm_clinical_context(algorithm)

            # 8. 确定目标人群
            result.target_population = algorithm.target_population

            # 9. 提取输入参数
            result.input_parameters = self._extract_algorithm_inputs(algorithm)

            # 10. 提取输出结果
            result.output_outcomes = self._extract_algorithm_outcomes(algorithm)

            # 11. 生成实施说明
            result.implementation_notes = self._generate_implementation_notes(algorithm)

            # 12. 识别限制条件
            result.limitations = self._identify_algorithm_limitations(algorithm)

            # 13. 找出替代方案
            result.alternatives = self._identify_algorithm_alternatives(algorithm)

            # 14. 质量评估
            result.clarity_score = self._assess_algorithm_clarity(algorithm)
            result.completeness_score = self._assess_algorithm_completeness(algorithm)

            # 计算处理指标
            processing_time = time.time() - start_time
            result.metrics = ProcessingMetrics(
                processing_time=processing_time,
                tokens_used=len(algorithm.flowchart_text.split()),
                api_calls=3,  # summary + decision tree + implementation
                confidence_score=self._calculate_algorithm_confidence_score(result),
                quality_score=self._calculate_algorithm_quality_score(result)
            )

            result.status = ProcessingStatus.COMPLETED
            result.processing_log.append("Algorithm processing completed successfully")

        except Exception as e:
            result.status = ProcessingStatus.FAILED
            result.processing_log.append(f"Algorithm processing failed: {str(e)}")
            result.metrics.processing_time = time.time() - start_time

        return result

    # 内容整合方法
    def _generate_integrated_summary(self, processed_content: ProcessedContent) -> str:
        """生成整合摘要"""
        summary_parts = []

        # 文档总体描述
        if processed_content.text_results:
            summary_parts.append("本指南包含以下核心内容：")

        # 章节摘要
        if processed_content.text_results:
            text_summary = "主要涵盖" + "、".join([
                f"{result.section_type}章节" for result in processed_content.text_results[:3]
            ])
            if len(processed_content.text_results) > 3:
                text_summary += f"等{len(processed_content.text_results)}个章节"
            summary_parts.append(text_summary)

        # 表格摘要
        if processed_content.processed_tables:
            table_types = [table.table_type.value for table in processed_content.processed_tables]
            table_summary = f"包含{len(processed_content.processed_tables)}个重要表格，涵盖{table_types[0]}"
            if len(set(table_types)) > 1:
                table_summary += f"等{len(set(table_types))}种类型"
            summary_parts.append(table_summary)

        # 算法摘要
        if processed_content.processed_algorithms:
            algorithm_types = [algo.algorithm_type.value for algo in processed_content.processed_algorithms]
            algo_summary = f"提供{len(processed_content.processed_algorithms)}个临床算法，包括{algorithm_types[0]}"
            if len(set(algorithm_types)) > 1:
                algo_summary += f"等{len(set(algorithm_types))}种类型"
            summary_parts.append(algo_summary)

        # 关键洞察
        if processed_content.key_clinical_insights:
            summary_parts.append("关键临床洞察：" + "；".join(processed_content.key_clinical_insights[:2]))

        return "。".join(summary_parts) + "。"

    def _extract_key_clinical_insights(self, processed_content: ProcessedContent) -> List[str]:
        """提取关键临床洞察"""
        insights = []

        # 从文本结果中提取
        for text_result in processed_content.text_results:
            if text_result.key_points:
                insights.extend(text_result.key_points[:2])  # 每个章节取前2个关键点

        # 从表格结果中提取
        for table in processed_content.processed_tables:
            if table.key_findings:
                insights.extend(table.key_findings[:1])  # 每个表格取1个关键发现

        # 从算法结果中提取
        for algorithm in processed_content.processed_algorithms:
            if algorithm.key_decision_points:
                insights.append(f"算法'{algorithm.title}'包含{len(algorithm.key_decision_points)}个关键决策点")

        # 去重并限制数量
        unique_insights = list(dict.fromkeys(insights))  # 保持顺序的去重
        return unique_insights[:5]  # 最多返回5个洞察

    # 关系发现方法
    def _find_text_table_relationship(self, text_result: TextProcessingResult, table: ProcessedTable) -> Optional[CrossModalRelationship]:
        """发现文本与表格的关系"""
        # 简单的基于关键词匹配的关系发现
        text_keywords = set(text_result.summary.lower().split())
        table_keywords = set(table.title.lower().split() + table.summary.lower().split())

        intersection = text_keywords.intersection(table_keywords)

        if len(intersection) >= 2:  # 至少2个共同关键词
            return CrossModalRelationship(
                source_id=text_result.section_id,
                source_type=ContentModality.TEXT,
                target_id=table.table_id,
                target_type=ContentModality.TABLE,
                relationship_type="supports",
                confidence=len(intersection) / max(len(text_keywords), len(table_keywords)),
                description=f"文本章节与表格'{table.title}'共享关键词：{', '.join(intersection)}"
            )

        return None

    def _find_text_algorithm_relationship(self, text_result: TextProcessingResult, algorithm: ProcessedAlgorithm) -> Optional[CrossModalRelationship]:
        """发现文本与算法的关系"""
        text_content = text_result.processed_content.lower()
        algo_content = algorithm.title.lower() + " " + algorithm.algorithm_summary.lower()

        # 检查是否有直接引用
        if any(word in text_content for word in algorithm.title.lower().split()):
            return CrossModalRelationship(
                source_id=text_result.section_id,
                source_type=ContentModality.TEXT,
                target_id=algorithm.algorithm_id,
                target_type=ContentModality.ALGORITHM,
                relationship_type="references",
                confidence=0.8,
                description=f"文本章节引用了算法'{algorithm.title}'"
            )

        return None

    def _find_table_algorithm_relationship(self, table: ProcessedTable, algorithm: ProcessedAlgorithm) -> Optional[CrossModalRelationship]:
        """发现表格与算法的关系"""
        table_content = table.title.lower() + " " + table.summary.lower()
        algo_content = algorithm.title.lower() + " " + algorithm.algorithm_summary.lower()

        # 检查临床概念重叠
        table_concepts = set(table.clinical_context.lower().split())
        algo_concepts = set(algorithm.clinical_context.lower().split())

        intersection = table_concepts.intersection(algo_concepts)

        if len(intersection) >= 2:
            return CrossModalRelationship(
                source_id=table.table_id,
                source_type=ContentModality.TABLE,
                target_id=algorithm.algorithm_id,
                target_type=ContentModality.ALGORITHM,
                relationship_type="elaborates",
                confidence=0.7,
                description=f"表格'{table.title}'与算法'{algorithm.title}'在临床概念上相关"
            )

        return None

    # 辅助方法
    def _prioritize_text_sections(self, sections: List[DocumentSection]) -> List[DocumentSection]:
        """按优先级排序文本章节"""
        # 定义章节类型优先级
        priority_map = {
            "recommendations": 5,
            "summary": 4,
            "introduction": 3,
            "methods": 2,
            "results": 2,
            "discussion": 1,
            "conclusion": 1,
            "references": 0
        }

        def get_priority(section):
            return priority_map.get(section.section_type.value, 1)

        return sorted(sections, key=get_priority, reverse=True)

    def _clean_and_normalize_text(self, text: str) -> str:
        """清理和规范化文本"""
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)

        # 移除特殊字符（保留基本标点）
        text = re.sub(r'[^\w\s.,;:!?()[\]{}"-]', '', text)

        # 规范化引号
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")

        return text.strip()

    def _extract_key_points(self, content: str) -> List[str]:
        """提取关键点"""
        # 基于简单规则提取关键点
        sentences = content.split('.')

        key_points = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # 过滤太短的句子
                # 查找包含重要关键词的句子
                important_keywords = [
                    "recommend", "suggest", "should", "must", "important",
                    "significant", "effective", "evidence", "clinical"
                ]

                if any(keyword in sentence.lower() for keyword in important_keywords):
                    key_points.append(sentence + '.')

                    if len(key_points) >= 5:  # 最多提取5个关键点
                        break

        return key_points

    def _generate_text_summary(self, content: str) -> str:
        """生成文本摘要"""
        # 简单的摘要生成：取前几句和最后一句
        sentences = [s.strip() for s in content.split('.') if s.strip()]

        if len(sentences) <= 3:
            return content

        # 取前两句和最后一句
        summary = '. '.join(sentences[:2]) + '.'
        if len(sentences) > 2:
            summary += ' ' + sentences[-1] + '.'

        return summary

    def _extract_medical_entities(self, content: str) -> List[Dict[str, Any]]:
        """提取医学实体"""
        # 简单的实体提取（实际应用中应使用专业的NER模型）
        entities = []

        # 医学术语模式
        patterns = {
            "disease": r'\b(?:diabetes|hypertension|cancer|heart disease|stroke)\b',
            "medication": r'\b(?:aspirin|metformin|insulin|lisinopril)\b',
            "symptom": r'\b(?:pain|fever|fatigue|nausea|headache)\b',
            "test": r'\b(?:blood test|mri|ct scan|x-ray)\b'
        }

        for entity_type, pattern in patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                entities.append({
                    "text": match.group(),
                    "type": entity_type,
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.8
                })

        return entities

    def _identify_clinical_concepts(self, content: str) -> List[str]:
        """识别临床概念"""
        clinical_concepts = []

        concept_keywords = [
            "treatment", "diagnosis", "prevention", "management", "therapy",
            "prognosis", "screening", "monitoring", "follow-up", "complications",
            "risk factors", "symptoms", "signs", "etiology", "pathophysiology"
        ]

        content_lower = content.lower()
        for concept in concept_keywords:
            if concept in content_lower:
                clinical_concepts.append(concept)

        return list(set(clinical_concepts))  # 去重

    def _extract_recommendation_strength(self, content: str) -> Optional[str]:
        """提取推荐强度"""
        strength_patterns = {
            "strong": r'\b(?:strongly recommend|must|should)\b',
            "moderate": r'\b(?:recommend|suggest|advise)\b',
            "weak": r'\b(?:may|might|consider|optional)\b'
        }

        for strength, pattern in strength_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                return strength

        return None

    def _find_cross_references(self, content: str) -> List[str]:
        """查找交叉引用"""
        references = []

        # 查找章节引用
        section_refs = re.findall(r'(?:see|refer to|as described in) (?:section|chapter) (\w+)', content, re.IGNORECASE)
        references.extend([f"section_{ref}" for ref in section_refs])

        # 查找表格引用
        table_refs = re.findall(r'(?:table|tab\.?)\s*(\d+)', content, re.IGNORECASE)
        references.extend([f"table_{ref}" for ref in table_refs])

        # 查找图引用
        figure_refs = re.findall(r'(?:figure|fig\.?)\s*(\d+)', content, re.IGNORECASE)
        references.extend([f"figure_{ref}" for ref in figure_refs])

        return references