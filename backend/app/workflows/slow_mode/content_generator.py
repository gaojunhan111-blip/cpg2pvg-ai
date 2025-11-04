"""
渐进式内容生成系统
CPG2PVG-AI System ProgressiveContentGenerator (Node 5)
"""

import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import re

from app.workflows.base import BaseWorkflowNode
from app.workflows.types import (
    ProcessingContext,
    ProcessingResult,
    ProcessingStatus,
)
from app.core.llm_client import LLMClient

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """内容类型"""
    SUMMARY = "summary"                    # 内容摘要
    INTRODUCTION = "introduction"          # 介绍部分
    SYMPTOMS = "symptoms"                  # 症状说明
    DIAGNOSIS = "diagnosis"                # 诊断信息
    TREATMENT = "treatment"                # 治疗方案
    PREVENTION = "prevention"              # 预防措施
    LIFESTYLE = "lifestyle"                # 生活方式
    FAQ = "faq"                           # 常见问题
    RESOURCES = "resources"               # 资源链接
    DISCLAIMER = "disclaimer"             # 免责声明


class GenerationPriority(Enum):
    """生成优先级"""
    CRITICAL = 3    # 关键内容（如安全性警告）
    HIGH = 2        # 重要内容（如主要治疗方案）
    NORMAL = 1      # 普通内容（如背景介绍）
    LOW = 0         # 补充内容（如扩展资源）


@dataclass
class ContentSection:
    """内容段落"""
    section_id: str
    content_type: ContentType
    title: str
    content: str
    priority: GenerationPriority
    word_count: int
    reading_time: float  # 预估阅读时间（分钟）
    complexity_score: float  # 复杂度评分 (0-1)
    medical_accuracy: float  # 医学准确性 (0-1)
    patient_friendliness: float  # 患者友好度 (0-1)


@dataclass
class ContentTemplate:
    """内容模板"""
    template_id: str
    content_type: ContentType
    structure: Dict[str, Any]
    required_elements: List[str]
    optional_elements: List[str]
    style_guidelines: List[str]
    medical_safety_checks: List[str]


@dataclass
class GenerationTask:
    """生成任务"""
    task_id: str
    content_type: ContentType
    priority: GenerationPriority
    input_data: Dict[str, Any]
    template: Optional[ContentTemplate] = None
    max_words: int = 500
    target_reading_level: str = "8th grade"  # 目标阅读水平


class ProgressiveContentGenerator(BaseWorkflowNode):
    """渐进式内容生成器 - 关键部分优先，渐进生成"""

    def __init__(self):
        super().__init__(
            name="ProgressiveContentGenerator",
            description="渐进式生成患者友好内容，关键部分优先处理"
        )

        # 初始化LLM客户端
        self.llm_client = LLMClient()

        # 内容存储
        self.generated_sections: Dict[str, ContentSection] = {}
        self.content_templates: Dict[str, ContentTemplate] = {}

        # 生成配置
        self.max_retries = 3
        self.quality_threshold = 0.7
        self.safety_check_required = True

        # 初始化内容模板
        self._initialize_templates()

    async def execute(
        self,
        context: ProcessingContext,
        input_data: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[ProcessingResult, None]:
        """执行渐进式内容生成"""

        try:
            # 解析输入数据
            agent_system_output = input_data.get("agent_system_output", {})
            task_results = input_data.get("task_results", [])
            knowledge_graph = input_data.get("knowledge_graph", {})

            if not any([agent_system_output, task_results, knowledge_graph]):
                yield ProcessingResult(
                    step_name=self.name,
                    status=ProcessingStatus.FAILED,
                    success=False,
                    error_message="没有可用的智能体输出进行内容生成"
                )
                return

            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.RUNNING,
                success=True,
                message="开始渐进式内容生成"
            )

            # 1. 分析内容需求
            yield ProcessingResult(
                step_name=f"{self.name}_requirement_analysis",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="分析内容生成需求"
            )

            content_requirements = await self._analyze_content_requirements(
                agent_system_output, task_results, knowledge_graph, context
            )

            yield ProcessingResult(
                step_name=f"{self.name}_requirement_analysis",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data=content_requirements,
                message="内容需求分析完成"
            )

            # 2. 制定生成计划
            yield ProcessingResult(
                step_name=f"{self.name}_generation_planning",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="制定内容生成计划"
            )

            generation_tasks = await self._create_generation_plan(content_requirements, context)

            yield ProcessingResult(
                step_name=f"{self.name}_generation_planning",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data={"total_tasks": len(generation_tasks)},
                message=f"生成计划制定完成，共{len(generation_tasks)}个任务"
            )

            # 3. 渐进式生成内容
            yield ProcessingResult(
                step_name=f"{self.name}_progressive_generation",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="开始渐进式内容生成"
            )

            generated_content = await self._progressive_content_generation(generation_tasks, context)

            yield ProcessingResult(
                step_name=f"{self.name}_progressive_generation",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data={"generated_sections": len(generated_content)},
                message=f"内容生成完成，共生成{len(generated_content)}个段落"
            )

            # 4. 内容质量检查和优化
            yield ProcessingResult(
                step_name=f"{self.name}_quality_optimization",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="进行内容质量检查和优化"
            )

            optimized_content = await self._optimize_content_quality(generated_content, context)

            yield ProcessingResult(
                step_name=f"{self.name}_quality_optimization",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data={"optimized_sections": len(optimized_content)},
                message="内容质量优化完成"
            )

            # 5. 最终内容整合
            yield ProcessingResult(
                step_name=f"{self.name}_final_integration",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="进行最终内容整合"
            )

            final_pvg_content = await self._integrate_final_content(optimized_content, context)

            yield ProcessingResult(
                step_name=f"{self.name}_final_integration",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data={"total_words": sum(s.word_count for s in optimized_content)},
                message="最终内容整合完成"
            )

            # 生成最终结果
            final_result = {
                "pvg_content": final_pvg_content,
                "content_sections": [section.__dict__ for section in optimized_content],
                "generation_statistics": self._calculate_generation_statistics(optimized_content),
                "quality_metrics": self._calculate_quality_metrics(optimized_content),
                "processing_metadata": {
                    "total_sections": len(optimized_content),
                    "total_words": sum(s.word_count for s in optimized_content),
                    "average_reading_time": sum(s.reading_time for s in optimized_content),
                    "generation_time": datetime.utcnow().isoformat(),
                    "cost_level": context.cost_level.value
                }
            }

            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.COMPLETED,
                success=True,
                data=final_result,
                message=f"渐进式内容生成完成，共生成{len(optimized_content)}个内容段落"
            )

        except Exception as e:
            logger.error(f"渐进式内容生成失败: {str(e)}")
            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.FAILED,
                success=False,
                error_message=str(e)
            )

    async def _analyze_content_requirements(
        self, agent_output: Dict[str, Any], task_results: List[Dict[str, Any]],
        knowledge_graph: Dict[str, Any], context: ProcessingContext
    ) -> Dict[str, Any]:
        """分析内容生成需求"""
        try:
            # 使用LLM分析内容需求
            analysis_prompt = self._build_requirement_analysis_prompt(
                agent_output, task_results, knowledge_graph, context
            )

            response = await self.llm_client.chat_completion(
                messages=[{
                    "role": "user",
                    "content": analysis_prompt
                }],
                max_tokens=1500,
                temperature=0.2
            )

            # 解析分析结果
            requirements = self._parse_requirement_analysis(response)

            return requirements

        except Exception as e:
            logger.error(f"内容需求分析失败: {str(e)}")
            # 返回默认需求
            return {
                "primary_focus": ["treatment", "safety"],
                "content_types": ["summary", "introduction", "treatment", "safety"],
                "target_audience": "patients",
                "reading_level": "8th grade",
                "max_complexity": 0.7,
                "medical_accuracy_required": 0.9
            }

    async def _create_generation_plan(
        self, requirements: Dict[str, Any], context: ProcessingContext
    ) -> List[GenerationTask]:
        """创建内容生成计划"""
        tasks = []
        task_counter = 0

        # 根据优先级和重要性创建任务
        content_priorities = {
            "summary": GenerationPriority.HIGH,
            "introduction": GenerationPriority.NORMAL,
            "treatment": GenerationPriority.HIGH,
            "safety": GenerationPriority.CRITICAL,
            "symptoms": GenerationPriority.NORMAL,
            "diagnosis": GenerationPriority.NORMAL,
            "prevention": GenerationPriority.NORMAL,
            "lifestyle": GenerationPriority.LOW,
            "faq": GenerationPriority.LOW,
            "resources": GenerationPriority.LOW,
            "disclaimer": GenerationPriority.HIGH
        }

        # 根据需求确定要生成的内容类型
        required_content_types = requirements.get("content_types", [
            "summary", "introduction", "treatment", "safety"
        ])

        for content_type_str in required_content_types:
            if content_type_str not in content_priorities:
                continue

            content_type = ContentType(content_type_str)
            priority = content_priorities[content_type_str]

            # 查找对应模板
            template = self.content_templates.get(content_type_str)

            # 创建生成任务
            task = GenerationTask(
                task_id=f"gen_task_{task_counter:03d}",
                content_type=content_type,
                priority=priority,
                input_data={
                    "requirements": requirements,
                    "context": context.__dict__
                },
                template=template,
                max_words=self._get_max_words_for_type(content_type),
                target_reading_level=requirements.get("reading_level", "8th grade")
            )

            tasks.append(task)
            task_counter += 1

        # 按优先级排序
        tasks.sort(key=lambda t: t.priority.value, reverse=True)

        return tasks

    async def _progressive_content_generation(
        self, tasks: List[GenerationTask], context: ProcessingContext
    ) -> List[ContentSection]:
        """渐进式生成内容"""
        generated_sections = []

        for task in tasks:
            try:
                # 生成内容
                section = await self._generate_single_section(task, context)

                if section:
                    generated_sections.append(section)
                    self.generated_sections[section.section_id] = section

                    # 实时反馈生成进度
                    logger.info(f"生成内容段落: {section.title} ({section.content_type.value})")

            except Exception as e:
                logger.error(f"生成内容段落失败: {task.task_id} - {str(e)}")
                continue

        return generated_sections

    async def _generate_single_section(self, task: GenerationTask, context: ProcessingContext) -> Optional[ContentSection]:
        """生成单个内容段落"""
        try:
            # 构建生成提示词
            prompt = self._build_content_generation_prompt(task, context)

            # 使用LLM生成内容
            response = await self.llm_client.chat_completion(
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=task.max_words * 2,  # 大约1个token=0.5个单词
                temperature=0.3 if task.content_type in ["treatment", "safety"] else 0.5
            )

            # 解析生成结果
            generated_data = self._parse_generated_content(response, task)

            # 创建内容段落
            section = ContentSection(
                section_id=f"section_{task.content_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                content_type=task.content_type,
                title=generated_data.get("title", ""),
                content=generated_data.get("content", ""),
                priority=task.priority,
                word_count=len(generated_data.get("content", "").split()),
                reading_time=self._estimate_reading_time(generated_data.get("content", "")),
                complexity_score=self._calculate_complexity_score(generated_data.get("content", "")),
                medical_accuracy=generated_data.get("medical_accuracy", 0.8),
                patient_friendliness=generated_data.get("patient_friendliness", 0.8)
            )

            # 质量检查
            if section.medical_accuracy < self.quality_threshold:
                logger.warning(f"内容段落医学准确性较低: {section.section_id}")

            return section

        except Exception as e:
            logger.error(f"生成单个内容段落失败: {str(e)}")
            return None

    async def _optimize_content_quality(
        self, sections: List[ContentSection], context: ProcessingContext
    ) -> List[ContentSection]:
        """优化内容质量"""
        optimized_sections = []

        for section in sections:
            try:
                # 质量评估和优化
                optimization_prompt = self._build_optimization_prompt(section, context)

                response = await self.llm_client.chat_completion(
                    messages=[{
                        "role": "user",
                        "content": optimization_prompt
                    }],
                    max_tokens=section.word_count * 2,
                    temperature=0.2
                )

                # 应用优化建议
                optimized_data = self._parse_optimization_response(response)

                # 更新内容段落
                if optimized_data.get("improved_content"):
                    section.content = optimized_data["improved_content"]
                    section.word_count = len(section.content.split())
                    section.reading_time = self._estimate_reading_time(section.content)
                    section.complexity_score = optimized_data.get("new_complexity", section.complexity_score)
                    section.patient_friendliness = optimized_data.get("new_friendliness", section.patient_friendliness)

                optimized_sections.append(section)

            except Exception as e:
                logger.error(f"优化内容质量失败: {section.section_id} - {str(e)}")
                # 保留原始内容
                optimized_sections.append(section)

        return optimized_sections

    async def _integrate_final_content(
        self, sections: List[ContentSection], context: ProcessingContext
    ) -> Dict[str, Any]:
        """整合最终内容"""
        try:
            # 按内容类型排序段落
            content_order = [
                ContentType.SUMMARY,
                ContentType.INTRODUCTION,
                ContentType.SYMPTOMS,
                ContentType.DIAGNOSIS,
                ContentType.TREATMENT,
                ContentType.PREVENTION,
                ContentType.LIFESTYLE,
                ContentType.FAQ,
                ContentType.RESOURCES,
                ContentType.DISCLAIMER
            ]

            ordered_sections = []
            for content_type in content_order:
                type_sections = [s for s in sections if s.content_type == content_type]
                ordered_sections.extend(type_sections)

            # 生成最终PVG文档
            final_content = {
                "title": "患者版医学指南",
                "sections": [section.__dict__ for section in ordered_sections],
                "table_of_contents": self._generate_table_of_contents(ordered_sections),
                "quick_summary": self._generate_quick_summary(ordered_sections),
                "safety_warnings": self._extract_safety_warnings(ordered_sections),
                "reading_time_total": sum(s.reading_time for s in ordered_sections),
                "word_count_total": sum(s.word_count for s in ordered_sections),
                "last_updated": datetime.utcnow().isoformat(),
                "medical_disclaimer": self._get_medical_disclaimer()
            }

            return final_content

        except Exception as e:
            logger.error(f"整合最终内容失败: {str(e)}")
            return {"error": str(e)}

    def _initialize_templates(self):
        """初始化内容模板"""
        # 摘要模板
        self.content_templates["summary"] = ContentTemplate(
            template_id="summary_template",
            content_type=ContentType.SUMMARY,
            structure={
                "main_points": ["关键信息点"],
                "overview": "内容概要"
            },
            required_elements=["主要内容概述", "关键信息"],
            optional_elements=["背景说明", "重要提醒"],
            style_guidelines=["简洁明了", "重点突出", "患者易懂"],
            medical_safety_checks=["准确性验证", "误导性检查"]
        )

        # 治疗方案模板
        self.content_templates["treatment"] = ContentTemplate(
            template_id="treatment_template",
            content_type=ContentType.TREATMENT,
            structure={
                "treatment_options": ["治疗方案选项"],
                "effectiveness": "治疗效果",
                "side_effects": "副作用",
                "precautions": "注意事项"
            },
            required_elements=["治疗方案", "效果说明", "注意事项"],
            optional_elements=["替代方案", "副作用", "随访要求"],
            style_guidelines=["专业准确", "详细说明", "安全提醒"],
            medical_safety_checks=["治疗方案验证", "安全性检查", "完整性确认"]
        )

        # 安全警告模板
        self.content_templates["safety"] = ContentTemplate(
            template_id="safety_template",
            content_type=ContentType.SAFETY,
            structure={
                "emergency_situations": "紧急情况",
                "warning_signs": "警告信号",
                "when_to_seek_help": "何时寻求帮助"
            },
            required_elements=["安全警告", "紧急情况处理"],
            optional_elements=["预警信号", "就医时机"],
            style_guidelines=["醒目明确", "紧急性强调", "行动指导"],
            medical_safety_checks=["紧急性验证", "准确性确认", "完整性检查"]
        )

    def _build_requirement_analysis_prompt(
        self, agent_output: Dict[str, Any], task_results: List[Dict[str, Any]],
        knowledge_graph: Dict[str, Any], context: ProcessingContext
    ) -> str:
        """构建需求分析提示词"""
        return f"""
基于以下智能体处理结果，分析患者版指南的内容生成需求：

智能体输出摘要: {json.dumps(agent_output, ensure_ascii=False)[:1000]}
任务结果数量: {len(task_results)}
知识图谱节点数: {len(knowledge_graph.get('nodes', []))}

专业领域: {', '.join(context.medical_specialties)}
质量要求: {context.quality_requirement.value}
成本级别: {context.cost_level.value}

请分析以下方面：
1. 主要内容焦点（哪些内容最重要）
2. 需要生成的内容类型
3. 目标受众特征
4. 适当的阅读水平
5. 复杂度要求
6. 医学准确性标准

请以JSON格式返回分析结果。
"""

    def _build_content_generation_prompt(self, task: GenerationTask, context: ProcessingContext) -> str:
        """构建内容生成提示词"""
        requirements = task.input_data.get("requirements", {})

        base_prompt = f"""
请为患者生成{task.content_type.value}相关内容：

内容类型: {task.content_type.value}
目标受众: {requirements.get('target_audience', '患者')}
阅读水平: {task.target_reading_level}
字数限制: {task.max_words}字

专业领域: {', '.join(context.medical_specialties)}
质量要求: {context.quality_requirement.value}

"""

        # 添加特定内容类型的指导
        if task.content_type == ContentType.TREATMENT:
            base_prompt += """
请包含以下内容：
1. 主要治疗方案
2. 治疗效果和预期
3. 可能的副作用
4. 重要注意事项
5. 何时联系医生

请确保内容准确、易懂，包含重要的安全提醒。
"""

        elif task.content_type == ContentType.SAFETY:
            base_prompt += """
请重点包含：
1. 紧急情况识别
2. 警告信号和症状
3. 何时立即就医
4. 日常安全注意事项
5. 预防措施

请使用醒目的语言强调安全重要性。
"""

        elif task.content_type == ContentType.SUMMARY:
            base_prompt += """
请提供：
1. 疾病/状况的简要说明
2. 主要治疗选项
3. 关键注意事项
4. 预期结果
5. 重要提醒

保持简洁明了，突出关键信息。
"""

        base_prompt += f"""

请以JSON格式返回结果，包含：
- title: 段落标题
- content: 段落内容
- medical_accuracy: 医学准确性评分(0-1)
- patient_friendliness: 患者友好度评分(0-1)
"""

        return base_prompt

    def _build_optimization_prompt(self, section: ContentSection, context: ProcessingContext) -> str:
        """构建内容优化提示词"""
        return f"""
请优化以下医学内容的表达，使其更适合患者阅读：

当前内容:
标题: {section.title}
内容: {section.content[:1000]}
内容类型: {section.content_type.value}
当前复杂度: {section.complexity_score:.2f}
当前友好度: {section.patient_friendliness:.2f}

优化要求：
1. 保持医学准确性
2. 提高患者可读性
3. 降低复杂度
4. 增强友好度
5. 确保安全性提醒明确

专业领域: {', '.join(context.medical_specialties)}

请返回优化后的内容，包含：
- improved_content: 改进后的内容
- new_complexity: 新的复杂度评分
- new_friendliness: 新的友好度评分
- improvement_summary: 改进总结
"""

    def _parse_requirement_analysis(self, response: str) -> Dict[str, Any]:
        """解析需求分析响应"""
        try:
            # 这里应该解析LLM返回的JSON响应
            # 简化实现，返回默认需求
            return {
                "primary_focus": ["treatment", "safety"],
                "content_types": ["summary", "introduction", "treatment", "safety"],
                "target_audience": "patients",
                "reading_level": "8th grade",
                "max_complexity": 0.7,
                "medical_accuracy_required": 0.9
            }
        except Exception as e:
            logger.error(f"解析需求分析响应失败: {str(e)}")
            return {}

    def _parse_generated_content(self, response: str, task: GenerationTask) -> Dict[str, Any]:
        """解析生成的内容响应"""
        try:
            # 这里应该解析LLM返回的JSON响应
            # 简化实现，返回示例内容
            return {
                "title": f"{task.content_type.value}相关内容",
                "content": f"这是生成的{task.content_type.value}内容。",
                "medical_accuracy": 0.85,
                "patient_friendliness": 0.80
            }
        except Exception as e:
            logger.error(f"解析生成内容响应失败: {str(e)}")
            return {
                "title": "",
                "content": "",
                "medical_accuracy": 0.5,
                "patient_friendliness": 0.5
            }

    def _parse_optimization_response(self, response: str) -> Dict[str, Any]:
        """解析优化响应"""
        try:
            # 这里应该解析LLM返回的JSON响应
            # 简化实现，返回示例优化结果
            return {
                "improved_content": "这是优化后的内容",
                "new_complexity": 0.6,
                "new_friendliness": 0.85,
                "improvement_summary": "内容已优化以提高可读性"
            }
        except Exception as e:
            logger.error(f"解析优化响应失败: {str(e)}")
            return {}

    def _get_max_words_for_type(self, content_type: ContentType) -> int:
        """获取内容类型的最大字数"""
        word_limits = {
            ContentType.SUMMARY: 200,
            ContentType.INTRODUCTION: 300,
            ContentType.SYMPTOMS: 400,
            ContentType.DIAGNOSIS: 350,
            ContentType.TREATMENT: 600,
            ContentType.PREVENTION: 300,
            ContentType.LIFESTYLE: 400,
            ContentType.FAQ: 500,
            ContentType.RESOURCES: 200,
            ContentType.DISCLAIMER: 150,
            ContentType.SAFETY: 250
        }
        return word_limits.get(content_type, 400)

    def _estimate_reading_time(self, content: str) -> float:
        """估算阅读时间（分钟）"""
        word_count = len(content.split())
        # 假设平均阅读速度为每分钟200个单词
        return max(0.5, word_count / 200)

    def _calculate_complexity_score(self, content: str) -> float:
        """计算内容复杂度评分"""
        # 简化的复杂度计算
        word_count = len(content.split())
        sentence_count = len(re.split(r'[.!?]+', content))

        if sentence_count == 0:
            return 0.5

        avg_sentence_length = word_count / sentence_count

        # 医学术语检测
        medical_terms = ["治疗", "诊断", "症状", "药物", "手术", "检查", "预防"]
        medical_term_count = sum(content.lower().count(term.lower()) for term in medical_terms)

        # 复杂度计算（句子长度 + 医学术语密度）
        complexity = min(1.0, (avg_sentence_length / 20) * 0.5 + (medical_term_count / word_count) * 0.5)

        return complexity

    def _generate_table_of_contents(self, sections: List[ContentSection]) -> List[Dict[str, str]]:
        """生成目录"""
        return [
            {
                "title": section.title,
                "section_id": section.section_id,
                "page": idx + 1
            }
            for idx, section in enumerate(sections)
        ]

    def _generate_quick_summary(self, sections: List[ContentSection]) -> str:
        """生成快速摘要"""
        summary_sections = [s for s in sections if s.content_type == ContentType.SUMMARY]
        if summary_sections:
            return summary_sections[0].content[:200] + "..." if len(summary_sections[0].content) > 200 else summary_sections[0].content
        return "内容摘要..."

    def _extract_safety_warnings(self, sections: List[ContentSection]) -> List[str]:
        """提取安全警告"""
        safety_sections = [s for s in sections if s.content_type in [ContentType.SAFETY, ContentType.TREATMENT]]
        warnings = []

        for section in safety_sections:
            # 简化实现，提取包含安全关键词的句子
            content = section.content
            if "紧急" in content or "警告" in content or "立即" in content:
                warnings.append(section.title)

        return warnings

    def _get_medical_disclaimer(self) -> str:
        """获取医学免责声明"""
        return "本内容仅供参考，不能替代专业医疗建议。如有疑问，请咨询您的医生或其他医疗专业人员。"

    def _calculate_generation_statistics(self, sections: List[ContentSection]) -> Dict[str, Any]:
        """计算生成统计信息"""
        return {
            "total_sections": len(sections),
            "total_words": sum(s.word_count for s in sections),
            "average_reading_time": sum(s.reading_time for s in sections) / len(sections) if sections else 0,
            "average_complexity": sum(s.complexity_score for s in sections) / len(sections) if sections else 0,
            "average_medical_accuracy": sum(s.medical_accuracy for s in sections) / len(sections) if sections else 0,
            "content_type_distribution": self._calculate_type_distribution(sections)
        }

    def _calculate_quality_metrics(self, sections: List[ContentSection]) -> Dict[str, Any]:
        """计算质量指标"""
        if not sections:
            return {}

        return {
            "overall_quality_score": sum(
                (s.medical_accuracy + s.patient_friendliness) / 2 for s in sections
            ) / len(sections),
            "medical_accuracy_distribution": [s.medical_accuracy for s in sections],
            "patient_friendliness_distribution": [s.patient_friendliness for s in sections],
            "complexity_distribution": [s.complexity_score for s in sections],
            "sections_meeting_quality_threshold": sum(
                1 for s in sections if s.medical_accuracy >= self.quality_threshold
            )
        }

    def _calculate_type_distribution(self, sections: List[ContentSection]) -> Dict[str, int]:
        """计算内容类型分布"""
        type_counts = {}
        for section in sections:
            type_name = section.content_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        return type_counts