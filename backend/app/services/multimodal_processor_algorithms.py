"""
MultiModalProcessor 算法处理方法
MultiModalProcessor Algorithm Processing Methods
"""

import re
import json
from typing import Dict, List, Any, Optional

from .multimodal_processor import (
    ProcessedAlgorithm, AlgorithmType, ClinicalImportance, ProcessingMetrics
)
from .medical_parser import ClinicalAlgorithm


class AlgorithmProcessorMixin:
    """算法处理混入类"""

    def _classify_algorithm_type(self, algorithm: ClinicalAlgorithm) -> AlgorithmType:
        """分类算法类型"""
        title_lower = algorithm.title.lower()
        content_lower = algorithm.flowchart_text.lower()

        # 基于关键词分类
        type_keywords = {
            AlgorithmType.DIAGNOSTIC: [
                "diagnosis", "diagnostic", "test", "detect", "identify", "classify"
            ],
            AlgorithmType.TREATMENT: [
                "treatment", "therapy", "medication", "drug", "intervention", "manage"
            ],
            AlgorithmType.FOLLOW_UP: [
                "follow-up", "monitor", "surveillance", "check", "review", "observation"
            ],
            AlgorithmType.RISK_ASSESSMENT: [
                "risk", "assessment", "stratify", "score", "predict", "probability"
            ],
            AlgorithmType.SCREENING: [
                "screening", "screen", "early detection", "preventive", "check-up"
            ],
            AlgorithmType.DECISION_SUPPORT: [
                "decision", "choose", "select", "recommend", "guide", "support"
            ]
        }

        # 计算每种类型的匹配分数
        type_scores = {}
        for algo_type, keywords in type_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in title_lower:
                    score += 3  # 标题权重更高
                if keyword in content_lower:
                    score += 1
            type_scores[algo_type] = score

        # 返回得分最高的类型
        best_type = max(type_scores, key=type_scores.get)
        return best_type if type_scores[best_type] > 0 else AlgorithmType.OTHER

    def _assess_algorithm_clinical_importance(self, algorithm: ClinicalAlgorithm) -> ClinicalImportance:
        """评估算法的临床重要性"""
        importance_score = 0

        # 1. 基于算法类型的评估
        algo_type = self._classify_algorithm_type(algorithm)
        type_importance = {
            AlgorithmType.DIAGNOSTIC: 0.8,
            AlgorithmType.TREATMENT: 0.8,
            AlgorithmType.RISK_ASSESSMENT: 0.7,
            AlgorithmType.DECISION_SUPPORT: 0.6,
            AlgorithmType.SCREENING: 0.6,
            AlgorithmType.FOLLOW_UP: 0.5,
            AlgorithmType.OTHER: 0.3
        }

        importance_score += type_importance.get(algo_type, 0.3)

        # 2. 基于复杂度的评估
        complexity_score = 0
        if len(algorithm.steps) > 5:
            complexity_score += 0.1
        if len(algorithm.decision_points) > 3:
            complexity_score += 0.1
        if algorithm.step_count > 10:
            complexity_score += 0.1

        importance_score += complexity_score

        # 3. 基于关键词的评估
        critical_keywords = [
            "emergency", "urgent", "critical", "life-threatening", "mortality",
            "survival", "severe", "major complication"
        ]

        content_lower = algorithm.flowchart_text.lower()
        for keyword in critical_keywords:
            if keyword in content_lower:
                importance_score += 0.2
                break

        # 4. 基于证据等级的评估
        if algorithm.evidence_level:
            evidence_level = algorithm.evidence_level.value.lower()
            if "high" in evidence_level or "a" in evidence_level:
                importance_score += 0.2
            elif "moderate" in evidence_level or "b" in evidence_level:
                importance_score += 0.1

        # 5. 基于目标人群的评估
        if algorithm.target_population:
            population_importance = {
                "general population": 0.1,
                "high-risk": 0.2,
                "critically ill": 0.3,
                "emergency": 0.3
            }

            target_lower = algorithm.target_population.lower()
            for pop_term, importance in population_importance.items():
                if pop_term in target_lower:
                    importance_score += importance
                    break

        # 转换为ClinicalImportance枚举
        if importance_score >= 0.9:
            return ClinicalImportance.CRITICAL
        elif importance_score >= 0.7:
            return ClinicalImportance.HIGH
        elif importance_score >= 0.5:
            return ClinicalImportance.MEDIUM
        elif importance_score >= 0.3:
            return ClinicalImportance.LOW
        else:
            return ClinicalImportance.UNKNOWN

    def _structure_algorithm_steps(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """结构化算法步骤"""
        structured_steps = []

        for i, step in enumerate(steps):
            structured_step = {
                "step_number": i + 1,
                "step_id": step.get("id", f"step_{i+1}"),
                "title": step.get("title", f"步骤 {i+1}"),
                "description": step.get("description", ""),
                "action": step.get("action", ""),
                "conditions": step.get("conditions", []),
                "outcomes": step.get("outcomes", []),
                "decision_points": step.get("decision_points", []),
                "next_steps": step.get("next_steps", []),
                "is_decision": step.get("is_decision", False),
                "time_estimates": step.get("time_estimates", {}),
                "resources_needed": step.get("resources_needed", []),
                "risks": step.get("risks", []),
                "alternatives": step.get("alternatives", [])
            }

            structured_steps.append(structured_step)

        return structured_steps

    def _build_decision_tree(self, decision_points: List[Dict[str, Any]], steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建决策树"""
        decision_tree = {
            "title": "Clinical Decision Tree",
            "nodes": [],
            "edges": [],
            "root_nodes": []
        }

        # 创建决策节点
        for i, decision_point in enumerate(decision_points):
            node = {
                "id": f"decision_{i+1}",
                "type": "decision",
                "title": decision_point.get("question", f"Decision Point {i+1}"),
                "description": decision_point.get("description", ""),
                "options": decision_point.get("options", []),
                "conditions": decision_point.get("conditions", []),
                "criteria": decision_point.get("criteria", {}),
                "position": {"x": i * 200, "y": 100}
            }

            decision_tree["nodes"].append(node)

            # 设置根节点
            if i == 0:
                decision_tree["root_nodes"].append(node["id"])

        # 创建动作节点
        for i, step in enumerate(steps):
            if not step.get("is_decision", False):
                node = {
                    "id": f"action_{i+1}",
                    "type": "action",
                    "title": step.get("title", f"Action {i+1}"),
                    "description": step.get("description", ""),
                    "action": step.get("action", ""),
                    "outcomes": step.get("outcomes", []),
                    "position": {"x": (i % 3) * 150, "y": 200 + (i // 3) * 100}
                }

                decision_tree["nodes"].append(node)

        # 创建连接边（简化版本）
        for i, decision_point in enumerate(decision_points):
            decision_id = f"decision_{i+1}"
            options = decision_point.get("options", [])

            for j, option in enumerate(options):
                edge = {
                    "id": f"edge_{i+1}_{j+1}",
                    "source": decision_id,
                    "target": f"action_{(i+j+1)%len(steps)+1}" if j < len(steps) else f"action_{i+1}",
                    "label": option.get("label", f"Option {j+1}"),
                    "condition": option.get("condition", ""),
                    "weight": option.get("weight", 1.0)
                }

                decision_tree["edges"].append(edge)

        return decision_tree

    def _generate_flowchart_representation(self, algorithm: ClinicalAlgorithm) -> str:
        """生成流程图表示"""
        flowchart_lines = ["flowchart TD"]

        # 添加样式定义
        flowchart_lines.extend([
            "    classDef decision fill:#f9f,stroke:#333,stroke-width:2px",
            "    classDef action fill:#bbf,stroke:#333,stroke-width:2px",
            "    classDef startend fill:#9f9,stroke:#333,stroke-width:2px"
        ])

        # 添加开始节点
        start_id = "A[开始]"
        flowchart_lines.append(f"    {start_id}")

        # 添加步骤节点
        current_id = start_id
        for i, step in enumerate(algorithm.steps):
            step_id = f"S{i+1}"
            step_title = step.get("title", f"步骤{i+1}")

            if step.get("is_decision", False):
                node_text = f"D{step_id}{{{step_title}?"
                flowchart_lines.append(f"    {node_text}}}")
                flowchart_lines.append(f"    {current_id} --> {node_text}")

                # 添加决策分支
                options = step.get("options", [])
                for j, option in enumerate(options[:2]):  # 最多2个分支
                    option_id = f"O{i+1}_{j+1}"
                    option_text = option.get("label", f"选项{j+1}")
                    flowchart_lines.append(f"    {node_text} --> |{option_text}| {option_id}")
                    current_id = option_id
            else:
                node_text = f"S{step_id}[{step_title}]"
                flowchart_lines.append(f"    {node_text}")
                flowchart_lines.append(f"    {current_id} --> {node_text}")
                current_id = node_text

        # 添加结束节点
        end_id = "B[结束]"
        flowchart_lines.append(f"    {end_id}")
        flowchart_lines.append(f"    {current_id} --> {end_id}")

        # 添加类定义
        flowchart_lines.extend([
            "    class A,B startend",
            "    class D startend decision",
            "    class S startend action"
        ])

        return "\n".join(flowchart_lines)

    def _generate_algorithm_summary(self, algorithm: ClinicalAlgorithm) -> str:
        """生成算法摘要"""
        summary_parts = []

        # 基本描述
        algo_type = self._classify_algorithm_type(algorithm)
        summary_parts.append(f"该{algo_type.value}算法包含{algorithm.step_count}个步骤")

        if algorithm.decision_point_count > 0:
            summary_parts.append(f"和{algorithm.decision_point_count}个关键决策点")

        summary_parts.append("。")

        # 适用人群
        if algorithm.target_population:
            summary_parts.append(f"适用于{algorithm.target_population}。")

        # 关键特征
        features = []
        if algorithm.step_count > 5:
            features.append("步骤详细")
        if algorithm.decision_point_count > 2:
            features.append("决策复杂")
        if "emergency" in algorithm.flowchart_text.lower():
            features.append("紧急处理")
        if "monitoring" in algorithm.flowchart_text.lower():
            features.append("需要监测")

        if features:
            summary_parts.append(f"该算法特点：{','.join(features)}。")

        # 证据等级
        if algorithm.evidence_level:
            summary_parts.append(f"基于{algorithm.evidence_level.value}证据。")

        return "".join(summary_parts)

    def _extract_key_decision_points(self, decision_points: List[Dict[str, Any]]) -> List[str]:
        """提取关键决策点"""
        key_points = []

        for i, decision in enumerate(decision_points):
            question = decision.get("question", f"决策点{i+1}")
            options = decision.get("options", [])

            decision_text = f"{question}"
            if options:
                option_texts = [opt.get("label", "") for opt in options[:2]]  # 最多2个选项
                decision_text += f"（{' 或 '.join(option_texts)}）"

            key_points.append(decision_text)

        return key_points

    def _analyze_branching_logic(self, decision_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析分支逻辑"""
        branching_logic = []

        for i, decision in enumerate(decision_points):
            logic = {
                "decision_id": f"decision_{i+1}",
                "decision_question": decision.get("question", ""),
                "branches": [],
                "logic_type": "conditional",
                "complexity": "simple"
            }

            options = decision.get("options", [])
            conditions = decision.get("conditions", [])

            for j, option in enumerate(options):
                branch = {
                    "branch_id": f"branch_{i+1}_{j+1}",
                    "condition": option.get("condition", ""),
                    "label": option.get("label", f"选项{j+1}"),
                    "outcome": option.get("outcome", ""),
                    "next_step": option.get("next_step", ""),
                    "probability": option.get("probability", None)
                }

                logic["branches"].append(branch)

            # 评估复杂度
            if len(options) > 3 or len(conditions) > 2:
                logic["complexity"] = "complex"
            elif len(options) > 2 or len(conditions) > 1:
                logic["complexity"] = "moderate"

            branching_logic.append(logic)

        return branching_logic

    def _analyze_algorithm_clinical_context(self, algorithm: ClinicalAlgorithm) -> str:
        """分析算法的临床背景"""
        context_parts = []

        content_lower = algorithm.flowchart_text.lower()

        # 识别临床场景
        clinical_scenarios = {
            "emergency": "急诊场景",
            "outpatient": "门诊场景",
            "inpatient": "住院场景",
            "icu": "重症监护",
            "surgery": "手术相关",
            "follow-up": "随访管理"
        }

        for scenario, description in clinical_scenarios.items():
            if scenario in content_lower:
                context_parts.append(description)
                break

        # 识别医学专业
        medical_specialties = {
            "cardiology": "心血管科",
            "oncology": "肿瘤科",
            "neurology": "神经科",
            "respiratory": "呼吸科",
            "endocrinology": "内分泌科"
        }

        for specialty, description in medical_specialties.items():
            if specialty in content_lower:
                context_parts.append(description)
                break

        # 识别处理方式
        treatment_types = {
            "medication": "药物治疗",
            "surgery": "手术治疗",
            "diagnostic": "诊断流程",
            "monitoring": "监测管理",
            "rehabilitation": "康复治疗"
        }

        for treatment, description in treatment_types.items():
            if treatment in content_lower:
                context_parts.append(description)
                break

        return "，".join(context_parts) if context_parts else "临床背景尚不明确"

    def _extract_algorithm_inputs(self, algorithm: ClinicalAlgorithm) -> List[Dict[str, Any]]:
        """提取算法输入参数"""
        inputs = []

        # 从步骤中提取输入信息
        for step in algorithm.steps:
            step_inputs = step.get("inputs", [])
            for step_input in step_inputs:
                input_param = {
                    "name": step_input.get("name", ""),
                    "type": step_input.get("type", "string"),
                    "description": step_input.get("description", ""),
                    "required": step_input.get("required", True),
                    "range": step_input.get("range", {}),
                    "default_value": step_input.get("default_value", None)
                }
                inputs.append(input_param)

        # 从决策点中提取条件参数
        for decision in algorithm.decision_points:
            conditions = decision.get("conditions", [])
            for condition in conditions:
                if "parameter" in condition:
                    input_param = {
                        "name": condition.get("parameter", ""),
                        "type": condition.get("type", "string"),
                        "description": f"用于判断{condition.get('description', '')}",
                        "required": True,
                        "range": condition.get("range", {}),
                        "default_value": None
                    }
                    inputs.append(input_param)

        # 去重
        unique_inputs = []
        seen_names = set()
        for input_param in inputs:
            if input_param["name"] not in seen_names:
                unique_inputs.append(input_param)
                seen_names.add(input_param["name"])

        return unique_inputs

    def _extract_algorithm_outcomes(self, algorithm: ClinicalAlgorithm) -> List[str]:
        """提取算法输出结果"""
        outcomes = []

        # 从步骤中提取结果
        for step in algorithm.steps:
            step_outcomes = step.get("outcomes", [])
            outcomes.extend(step_outcomes)

        # 从决策点中提取结果
        for decision in algorithm.decision_points:
            options = decision.get("options", [])
            for option in options:
                outcome = option.get("outcome", "")
                if outcome and outcome not in outcomes:
                    outcomes.append(outcome)

        # 从流程图文本中提取结果关键词
        content_lower = algorithm.flowchart_text.lower()
        outcome_keywords = [
            "result", "outcome", "diagnosis", "treatment", "recommendation",
            "conclusion", "finding", "decision"
        ]

        for keyword in outcome_keywords:
            if keyword in content_lower:
                # 提取包含关键词的短语
                pattern = rf'\b[^.]*{keyword}[^.]*\b'
                matches = re.findall(pattern, content_lower)
                for match in matches[:2]:  # 最多2个匹配
                    clean_match = match.strip().capitalize()
                    if clean_match not in outcomes:
                        outcomes.append(clean_match)

        return outcomes[:5]  # 最多返回5个结果

    def _generate_implementation_notes(self, algorithm: ClinicalAlgorithm) -> str:
        """生成实施说明"""
        notes = []

        # 基于复杂度的实施建议
        if algorithm.step_count > 10:
            notes.append("该算法较为复杂，建议分阶段实施")

        if algorithm.decision_point_count > 5:
            notes.append("包含多个决策点，需要充分的培训和评估")

        # 基于内容的实施建议
        content_lower = algorithm.flowchart_text.lower()

        if "monitoring" in content_lower:
            notes.append("实施过程中需要建立监测机制")

        if "emergency" in content_lower:
            notes.append("适用于紧急情况，需要快速响应能力")

        if "team" in content_lower or "multidisciplinary" in content_lower:
            notes.append("需要多学科团队协作")

        if "documentation" in content_lower or "record" in content_lower:
            notes.append("需要完善的文档记录系统")

        return "；".join(notes) if notes else "按照标准临床流程实施"

    def _identify_algorithm_limitations(self, algorithm: ClinicalAlgorithm) -> List[str]:
        """识别算法限制"""
        limitations = []

        # 基于复杂度的限制
        if algorithm.step_count > 15:
            limitations.append("步骤过多，可能影响执行效率")

        if algorithm.decision_point_count > 8:
            limitations.append("决策点过多，增加执行难度")

        # 基于内容的限制
        content_lower = algorithm.flowchart_text.lower()

        if not algorithm.target_population:
            limitations.append("未明确目标人群")

        if "subjective" in content_lower or "judgment" in content_lower:
            limitations.append("包含主观判断，可能存在变异")

        if "rare" in content_lower or "unusual" in content_lower:
            limitations.append("适用于特殊情况，常规应用需谨慎")

        if "cost" in content_lower or "expensive" in content_lower:
            limitations.append("可能涉及较高成本")

        return limitations

    def _identify_algorithm_alternatives(self, algorithm: ClinicalAlgorithm) -> List[str]:
        """识别算法替代方案"""
        alternatives = []

        algo_type = self._classify_algorithm_type(algorithm)

        # 基于算法类型的替代方案
        type_alternatives = {
            AlgorithmType.DIAGNOSTIC: [
                "其他诊断标准",
                "影像学检查",
                "实验室检测",
                "临床评分系统"
            ],
            AlgorithmType.TREATMENT: [
                "药物治疗方案",
                "手术治疗选择",
                "物理治疗",
                "保守治疗方案"
            ],
            AlgorithmType.FOLLOW_UP: [
                "远程监测",
                "电话随访",
                "门诊复查",
                "自我管理"
            ]
        }

        if algo_type in type_alternatives:
            alternatives.extend(type_alternatives[algo_type][:2])

        # 从内容中提取替代方案
        content_lower = algorithm.flowchart_text.lower()
        alternative_keywords = [
            "alternative", "option", "choice", "consider", "instead"
        ]

        for keyword in alternative_keywords:
            if keyword in content_lower:
                # 简单提取替代方案描述
                pattern = rf'[^.]*{keyword}[^.]*'
                matches = re.findall(pattern, content_lower)
                for match in matches[:1]:  # 只取第一个匹配
                    clean_match = match.strip().capitalize()
                    if len(clean_match) > 10:  # 过滤太短的匹配
                        alternatives.append(clean_match)
                break

        return list(set(alternatives))  # 去重

    def _assess_algorithm_clarity(self, algorithm: ClinicalAlgorithm) -> float:
        """评估算法清晰度"""
        clarity_score = 0.8

        # 基于步骤描述的清晰度
        step_descriptions = [
            step.get("description", "") for step in algorithm.steps
        ]
        avg_description_length = sum(len(desc) for desc in step_descriptions) / len(step_descriptions) if step_descriptions else 0

        if avg_description_length < 20:
            clarity_score -= 0.2
        elif avg_description_length > 200:
            clarity_score -= 0.1

        # 基于决策点的清晰度
        for decision in algorithm.decision_points:
            question = decision.get("question", "")
            options = decision.get("options", [])

            if not question:
                clarity_score -= 0.1
            elif len(question) < 10:
                clarity_score -= 0.05

            if not options:
                clarity_score -= 0.15
            elif len(options) > 5:
                clarity_score -= 0.1

        # 基于结构清晰度
        if algorithm.step_count > 0:
            step_id_consistency = all(
                step.get("id") for step in algorithm.steps
            )
            if not step_id_consistency:
                clarity_score -= 0.1

        return max(0.0, clarity_score)

    def _assess_algorithm_completeness(self, algorithm: ClinicalAlgorithm) -> float:
        """评估算法完整性"""
        completeness_score = 0.0

        # 基本结构完整性 (40%)
        if algorithm.steps:
            completeness_score += 0.2

        if algorithm.decision_points:
            completeness_score += 0.1

        if algorithm.target_population:
            completeness_score += 0.1

        # 描述完整性 (30%)
        described_steps = sum(
            1 for step in algorithm.steps
            if step.get("description") and len(step.get("description", "")) > 10
        )
        if algorithm.steps:
            completeness_score += 0.3 * (described_steps / len(algorithm.steps))

        # 决策完整性 (20%)
        described_decisions = sum(
            1 for decision in algorithm.decision_points
            if decision.get("question") and decision.get("options")
        )
        if algorithm.decision_points:
            completeness_score += 0.2 * (described_decisions / len(algorithm.decision_points))

        # 结果完整性 (10%)
        outcomes = self._extract_algorithm_outcomes(algorithm)
        if outcomes:
            completeness_score += 0.1

        return max(0.0, min(1.0, completeness_score))

    def _calculate_algorithm_confidence_score(self, algorithm_result: ProcessedAlgorithm) -> float:
        """计算算法处理置信度"""
        base_score = 0.8

        # 基于清晰度调整
        base_score += (algorithm_result.clarity_score - 0.5) * 0.2

        # 基于完整性调整
        base_score += (algorithm_result.completeness_score - 0.5) * 0.2

        # 基于临床重要性调整
        importance_scores = {
            ClinicalImportance.CRITICAL: 0.1,
            ClinicalImportance.HIGH: 0.05,
            ClinicalImportance.MEDIUM: 0.0,
            ClinicalImportance.LOW: -0.05,
            ClinicalImportance.UNKNOWN: -0.1
        }

        base_score += importance_scores.get(algorithm_result.clinical_importance, 0)

        return max(0.0, min(1.0, base_score))

    def _calculate_algorithm_quality_score(self, algorithm_result: ProcessedAlgorithm) -> float:
        """计算算法质量分数"""
        quality_score = 0.0

        # 清晰度权重 35%
        quality_score += algorithm_result.clarity_score * 0.35

        # 完整性权重 35%
        quality_score += algorithm_result.completeness_score * 0.35

        # 内容质量权重 20%
        if algorithm_result.algorithm_summary and algorithm_result.implementation_notes:
            content_quality = 1.0
        elif algorithm_result.algorithm_summary or algorithm_result.implementation_notes:
            content_quality = 0.7
        else:
            content_quality = 0.3
        quality_score += content_quality * 0.2

        # 结构化程度权重 10%
        if algorithm_result.structured_steps and algorithm_result.decision_tree:
            structure_quality = 1.0
        elif algorithm_result.structured_steps or algorithm_result.decision_tree:
            structure_quality = 0.6
        else:
            structure_quality = 0.3
        quality_score += structure_quality * 0.1

        return max(0.0, min(1.0, quality_score))