"""
MultiModalProcessor 表格处理方法
MultiModalProcessor Table Processing Methods
"""

import re
import json
from typing import Dict, List, Any, Optional

from .multimodal_processor import (
    ProcessedTable, TableType, ClinicalImportance, ProcessingMetrics
)
from .medical_parser import MedicalTable


class TableProcessorMixin:
    """表格处理混入类"""

    def _classify_table_type(self, table: MedicalTable) -> TableType:
        """分类表格类型"""
        title_lower = table.title.lower()
        content_lower = table.content_text.lower()

        # 基于标题和内容的关键词分类
        type_keywords = {
            TableType.RECOMMENDATION: [
                "recommendation", "guideline", "suggest", "advice", "should"
            ],
            TableType.EVIDENCE: [
                "evidence", "study", "trial", "research", "data"
            ],
            TableType.COMPARISON: [
                "comparison", "versus", "vs", "compare", "difference"
            ],
            TableType.FLOWCHART: [
                "flowchart", "algorithm", "workflow", "process", "decision"
            ],
            TableType.DIAGNOSTIC: [
                "diagnostic", "diagnosis", "test", "criteria", "classification"
            ],
            TableType.TREATMENT: [
                "treatment", "therapy", "medication", "drug", "dosage"
            ],
            TableType.ADVERSE_EVENTS: [
                "adverse", "side effect", "toxicity", "complication", "reaction"
            ],
            TableType.SUMMARY: [
                "summary", "overview", "key points", "highlights", "conclusions"
            ]
        }

        # 计算每种类型的匹配分数
        type_scores = {}
        for table_type, keywords in type_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in title_lower:
                    score += 2  # 标题中的关键词权重更高
                if keyword in content_lower:
                    score += 1
            type_scores[table_type] = score

        # 返回得分最高的类型
        best_type = max(type_scores, key=type_scores.get)
        return best_type if type_scores[best_type] > 0 else TableType.OTHER

    def _assess_table_clinical_importance(self, table: MedicalTable) -> ClinicalImportance:
        """评估表格的临床重要性"""
        importance_score = 0

        # 1. 基于表格类型的评估
        table_type = self._classify_table_type(table)
        type_importance = {
            TableType.RECOMMENDATION: 0.8,
            TableType.TREATMENT: 0.8,
            TableType.DIAGNOSTIC: 0.7,
            TableType.EVIDENCE: 0.6,
            TableType.COMPARISON: 0.5,
            TableType.ADVERSE_EVENTS: 0.6,
            TableType.SUMMARY: 0.4,
            TableType.FLOWCHART: 0.3,
            TableType.OTHER: 0.2
        }

        importance_score += type_importance.get(table_type, 0.2)

        # 2. 基于标题关键词的评估
        high_importance_keywords = [
            "mortality", "survival", "life-threatening", "critical",
            "emergency", "severe", "major", "primary"
        ]

        medium_importance_keywords = [
            "efficacy", "safety", "outcome", "response", "benefit",
            "risk", "adverse", "moderate"
        ]

        title_lower = table.title.lower()
        content_lower = table.content_text.lower()

        for keyword in high_importance_keywords:
            if keyword in title_lower or keyword in content_lower:
                importance_score += 0.2
                break  # 只加分一次

        for keyword in medium_importance_keywords:
            if keyword in title_lower or keyword in content_lower:
                importance_score += 0.1
                break

        # 3. 基于证据等级的评估
        if table.evidence_level:
            evidence_level = table.evidence_level.value.lower()
            if "high" in evidence_level or "a" in evidence_level:
                importance_score += 0.2
            elif "moderate" in evidence_level or "b" in evidence_level:
                importance_score += 0.1

        # 4. 基于数据质量的评估
        if len(table.rows) > 5 and len(table.headers) > 2:
            importance_score += 0.1

        # 转换为ClinicalImportance枚举
        if importance_score >= 0.8:
            return ClinicalImportance.CRITICAL
        elif importance_score >= 0.6:
            return ClinicalImportance.HIGH
        elif importance_score >= 0.4:
            return ClinicalImportance.MEDIUM
        elif importance_score >= 0.2:
            return ClinicalImportance.LOW
        else:
            return ClinicalImportance.UNKNOWN

    def _extract_structured_table_data(self, table: MedicalTable) -> List[Dict[str, Any]]:
        """提取结构化表格数据"""
        structured_data = []

        for i, row in enumerate(table.rows):
            row_data = {}
            for j, cell in enumerate(row):
                # 使用表头作为键，如果表头不够则使用索引
                if j < len(table.headers):
                    header = table.headers[j]
                else:
                    header = f"Column_{j+1}"

                # 清理单元格数据
                cleaned_cell = str(cell).strip()

                # 尝试解析数字
                if cleaned_cell.replace('.', '').replace('-', '').isdigit():
                    try:
                        if '.' in cleaned_cell:
                            row_data[header] = float(cleaned_cell)
                        else:
                            row_data[header] = int(cleaned_cell)
                    except ValueError:
                        row_data[header] = cleaned_cell
                else:
                    row_data[header] = cleaned_cell

            row_data['_row_index'] = i
            structured_data.append(row_data)

        return structured_data

    def _generate_table_interpretation(self, table: MedicalTable, structured_data: List[Dict[str, Any]]) -> str:
        """生成表格解释"""
        interpretations = []

        # 1. 基本描述
        interpretation = f"该{self._classify_table_type(table).value}表格包含{len(table.rows)}行数据，"
        interpretation += f"涵盖{len(table.headers)}个维度：{', '.join(table.headers[:3])}"
        if len(table.headers) > 3:
            interpretation += f"等{len(table.headers)}个维度"
        interpretations.append(interpretation)

        # 2. 数据模式分析
        if structured_data:
            # 分析数值数据
            numeric_columns = []
            for header in table.headers:
                values = [row.get(header) for row in structured_data if isinstance(row.get(header), (int, float))]
                if values:
                    numeric_columns.append((header, values))

            for column, values in numeric_columns[:2]:  # 只分析前两个数值列
                if values:
                    avg_val = sum(values) / len(values)
                    min_val = min(values)
                    max_val = max(values)
                    interpretations.append(
                        f"{column}列数值范围为{min_val}到{max_val}，平均值为{avg_val:.2f}"
                    )

        # 3. 临床意义
        table_type = self._classify_table_type(table)
        if table_type == TableType.TREATMENT:
            interpretations.append("该表格提供了不同治疗方案的比较数据，有助于临床决策。")
        elif table_type == TableType.DIAGNOSTIC:
            interpretations.append("该表格包含诊断标准或测试结果，用于疾病识别和分类。")
        elif table_type == TableType.EVIDENCE:
            interpretations.append("该表格总结了研究证据，为临床实践提供科学依据。")

        return "。".join(interpretations)

    def _generate_table_summary(self, table: MedicalTable, interpretation: str) -> str:
        """生成表格摘要"""
        summary_parts = []

        # 表格标题和类型
        table_type = self._classify_table_type(table)
        summary_parts.append(f"表格'{table.title}'是一个{table_type.value}类型的表格。")

        # 关键数据点
        if table.rows:
            # 提取第一行的关键信息作为示例
            first_row = table.rows[0]
            if len(first_row) >= 2 and len(table.headers) >= 2:
                example_data = f"{table.headers[0]}为{first_row[0]}，{table.headers[1]}为{first_row[1]}"
                summary_parts.append(f"例如，{example_data}。")

        # 临床意义
        clinical_importance = self._assess_table_clinical_importance(table)
        if clinical_importance in [ClinicalImportance.CRITICAL, ClinicalImportance.HIGH]:
            summary_parts.append("该表格具有重要的临床指导价值。")

        # 证据等级
        if table.evidence_level:
            summary_parts.append(f"证据等级为{table.evidence_level.value}。")

        return "".join(summary_parts)

    def _extract_table_key_findings(self, structured_data: List[Dict[str, Any]]) -> List[str]:
        """提取表格关键发现"""
        findings = []

        if not structured_data:
            return findings

        # 1. 数值分析
        for header in list(structured_data[0].keys())[:3]:  # 只分析前三列
            values = [row.get(header) for row in structured_data if isinstance(row.get(header), (int, float))]

            if len(values) >= 2:
                max_val = max(values)
                min_val = min(values)

                # 找到最大值和最小值对应的行
                max_row = next((row for row in structured_data if row.get(header) == max_val), None)
                min_row = next((row for row in structured_data if row.get(header) == min_val), None)

                if max_row and min_row:
                    findings.append(f"{header}：最高值{max_val}，最低值{min_val}")

        # 2. 分类数据分析
        for header in list(structured_data[0].keys())[:3]:
            values = [str(row.get(header, "")) for row in structured_data]
            unique_values = list(set(values))

            if len(unique_values) > 1 and len(unique_values) <= 5:
                # 统计各类别数量
                value_counts = {}
                for value in values:
                    value_counts[value] = value_counts.get(value, 0) + 1

                most_common = max(value_counts, key=value_counts.get)
                findings.append(f"{header}中{most_common}出现最频繁({value_counts[most_common]}次)")

        return findings[:3]  # 最多返回3个关键发现

    def _analyze_table_clinical_context(self, table: MedicalTable) -> str:
        """分析表格的临床背景"""
        context_parts = []

        title_lower = table.title.lower()
        content_lower = table.content_text.lower()

        # 识别医学领域
        medical_domains = {
            "cardiology": ["heart", "cardiac", "cardiovascular", "blood pressure"],
            "oncology": ["cancer", "tumor", "malignant", "chemotherapy"],
            "endocrinology": ["diabetes", "insulin", "thyroid", "hormone"],
            "neurology": ["brain", "neural", "stroke", "seizure"],
            "respiratory": ["lung", "respiratory", "asthma", "copd"]
        }

        for domain, keywords in medical_domains.items():
            if any(keyword in title_lower or keyword in content_lower for keyword in keywords):
                context_parts.append(f"该表格涉及{domain}领域")
                break

        # 识别患者群体
        population_keywords = [
            "adult", "pediatric", "elderly", "children", "adolescent",
            "pregnant", "neonatal", "geriatric"
        ]

        for keyword in population_keywords:
            if keyword in content_lower:
                context_parts.append(f"针对{keyword}患者群体")
                break

        # 识别临床场景
        clinical_scenarios = [
            ("emergency", "急诊场景"),
            ("outpatient", "门诊场景"),
            ("inpatient", "住院场景"),
            ("icu", "重症监护场景"),
            ("surgery", "手术场景")
        ]

        for scenario, description in clinical_scenarios:
            if scenario in content_lower:
                context_parts.append(f"适用于{description}")
                break

        return "，".join(context_parts) if context_parts else "临床背景尚不明确"

    def _identify_table_target_population(self, table: MedicalTable) -> str:
        """识别表格的目标人群"""
        content_lower = table.content_text.lower()
        title_lower = table.title.lower()

        # 年龄组识别
        age_groups = [
            ("children", "儿童"),
            ("pediatric", "儿科患者"),
            ("adult", "成人"),
            ("elderly", "老年患者"),
            ("geriatric", "老年患者"),
            ("adolescent", "青少年"),
            ("neonatal", "新生儿")
        ]

        for term, group in age_groups:
            if term in content_lower or term in title_lower:
                return group

        # 疾病状态识别
        disease_states = [
            ("diabetes", "糖尿病患者"),
            ("hypertension", "高血压患者"),
            ("cancer", "癌症患者"),
            ("heart disease", "心脏病患者"),
            ("stroke", "中风患者")
        ]

        for term, state in disease_states:
            if term in content_lower or term in title_lower:
                return state

        return "患者群体"

    def _extract_applicability_conditions(self, table: MedicalTable) -> List[str]:
        """提取适用条件"""
        conditions = []
        content_lower = table.content_text.lower()

        condition_patterns = [
            ("contraindicated", "禁忌症"),
            ("not suitable", "不适用"),
            ("caution", "慎用"),
            ("monitoring required", "需要监测"),
            ("special consideration", "特殊考虑")
        ]

        for pattern, condition in condition_patterns:
            if pattern in content_lower:
                conditions.append(condition)

        return conditions

    def _extract_table_references(self, table: MedicalTable) -> List[str]:
        """提取表格引用"""
        references = []

        # 查找参考文献标记
        ref_patterns = [
            r'\[(\d+)\]',  # [1], [2] etc.
            r'\((\d{4})\)',  # (2023) etc.
            r'reference[:\s]+(\w+)',  # reference: PMID123 etc.
        ]

        for pattern in ref_patterns:
            matches = re.findall(pattern, table.content_text)
            for match in matches:
                references.append(f"ref_{match}")

        return list(set(references))  # 去重

    def _assess_table_completeness(self, table: MedicalTable) -> float:
        """评估表格完整性"""
        completeness_score = 1.0

        # 1. 检查表头
        if not table.headers:
            completeness_score -= 0.3
        elif len(table.headers) < 2:
            completeness_score -= 0.1

        # 2. 检查数据行
        if not table.rows:
            completeness_score -= 0.4
        elif len(table.rows) < 3:
            completeness_score -= 0.2

        # 3. 检查数据一致性
        if table.headers and table.rows:
            expected_cols = len(table.headers)
            for i, row in enumerate(table.rows):
                if len(row) != expected_cols:
                    completeness_score -= 0.1 * (i + 1) / len(table.rows)
                    break

        # 4. 检查内容质量
        empty_cells = 0
        total_cells = len(table.headers) * len(table.rows) if table.headers and table.rows else 1

        for row in table.rows:
            for cell in row:
                if not str(cell).strip():
                    empty_cells += 1

        empty_ratio = empty_cells / total_cells
        completeness_score -= empty_ratio * 0.3

        return max(0.0, completeness_score)

    def _assess_table_accuracy(self, structured_data: List[Dict[str, Any]]) -> float:
        """评估表格数据准确性"""
        if not structured_data:
            return 0.0

        accuracy_score = 1.0

        # 1. 数据一致性检查
        for column_name in list(structured_data[0].keys()):
            if column_name.startswith('_'):  # 跳过元数据列
                continue

            values = [row.get(column_name) for row in structured_data]
            non_empty_values = [v for v in values if v is not None and str(v).strip()]

            if not non_empty_values:
                accuracy_score -= 0.1
                continue

            # 检查数据类型一致性
            types = set(type(v).__name__ for v in non_empty_values)
            if len(types) > 2:  # 允许数字和字符串混合
                accuracy_score -= 0.1

        # 2. 数值合理性检查
        for column_name in list(structured_data[0].keys()):
            if column_name.startswith('_'):
                continue

            numeric_values = [
                row.get(column_name) for row in structured_data
                if isinstance(row.get(column_name), (int, float))
            ]

            if len(numeric_values) >= 3:
                # 检查是否有极端异常值
                mean_val = sum(numeric_values) / len(numeric_values)
                std_val = (sum((x - mean_val) ** 2 for x in numeric_values) / len(numeric_values)) ** 0.5

                outliers = sum(1 for x in numeric_values if abs(x - mean_val) > 3 * std_val)
                if outliers > len(numeric_values) * 0.1:  # 超过10%的异常值
                    accuracy_score -= 0.2

        return max(0.0, accuracy_score)

    def _calculate_table_confidence_score(self, table_result: ProcessedTable) -> float:
        """计算表格处理置信度"""
        base_score = 0.8

        # 基于完整性调整
        base_score += (table_result.completeness_score - 0.5) * 0.2

        # 基于准确性调整
        base_score += (table_result.accuracy_score - 0.5) * 0.2

        # 基于临床重要性调整
        importance_scores = {
            ClinicalImportance.CRITICAL: 0.1,
            ClinicalImportance.HIGH: 0.05,
            ClinicalImportance.MEDIUM: 0.0,
            ClinicalImportance.LOW: -0.05,
            ClinicalImportance.UNKNOWN: -0.1
        }

        base_score += importance_scores.get(table_result.clinical_importance, 0)

        return max(0.0, min(1.0, base_score))

    def _calculate_table_quality_score(self, table_result: ProcessedTable) -> float:
        """计算表格质量分数"""
        quality_score = 0.0

        # 完整性权重 30%
        quality_score += table_result.completeness_score * 0.3

        # 准确性权重 30%
        quality_score += table_result.accuracy_score * 0.3

        # 内容质量权重 20%
        if table_result.interpretation and table_result.summary:
            content_quality = 1.0
        elif table_result.interpretation or table_result.summary:
            content_quality = 0.7
        else:
            content_quality = 0.3
        quality_score += content_quality * 0.2

        # 结构化程度权重 20%
        if table_result.structured_data:
            structure_quality = 1.0
        else:
            structure_quality = 0.5
        quality_score += structure_quality * 0.2

        return max(0.0, min(1.0, quality_score))