"""
PVG模板系统
Practice Guideline Visualization Templates
"""

from typing import Dict, Any, List
from app.schemas.pvg_schemas import PVGStructure
from app.enums.common import SectionType, ContentPriority, AgentType


class PVGTemplateManager:
    """PVG模板管理器"""

    def __init__(self):
        self.templates = {
            "standard_clinical": self._create_standard_clinical_template(),
            "emergency_guideline": self._create_emergency_template(),
            "special_population": self._create_special_population_template(),
            "chronic_disease": self._create_chronic_disease_template()
        }

    def get_template(self, template_name: str) -> PVGStructure:
        """获取模板"""
        template = self.templates.get(template_name)
        if not template:
            # 默认使用标准临床模板
            template = self.templates["standard_clinical"]
        return template

    def _create_standard_clinical_template(self) -> PVGStructure:
        """创建标准临床模板"""
        return PVGStructure(
            template_name="standard_clinical",
            version="1.0",
            sections=[
                {
                    "type": SectionType.EMERGENCY_GUIDANCE,
                    "title": "紧急情况处理指南",
                    "priority": ContentPriority.HIGH,
                    "order": 1,
                    "required_elements": [
                        "识别紧急情况的标准",
                        "立即行动步骤",
                        "紧急联系方式",
                        "禁忌症和警告"
                    ],
                    "estimated_tokens": 800
                },
                {
                    "type": SectionType.KEY_RECOMMENDATIONS,
                    "title": "核心推荐意见",
                    "priority": ContentPriority.HIGH,
                    "order": 2,
                    "required_elements": [
                        "主要推荐建议",
                        "证据等级",
                        "推荐强度",
                        "适用人群"
                    ],
                    "estimated_tokens": 1200
                },
                {
                    "type": SectionType.TREATMENT_OPTIONS,
                    "title": "治疗方案",
                    "priority": ContentPriority.HIGH,
                    "order": 3,
                    "required_elements": [
                        "一线治疗方案",
                        "替代治疗方案",
                        "药物选择和剂量",
                        "非药物治疗"
                    ],
                    "estimated_tokens": 1000
                },
                {
                    "type": SectionType.SAFETY_WARNINGS,
                    "title": "安全注意事项",
                    "priority": ContentPriority.HIGH,
                    "order": 4,
                    "required_elements": [
                        "药物相互作用",
                        "禁忌症",
                        "不良反应监测",
                        "特殊人群注意事项"
                    ],
                    "estimated_tokens": 800
                },
                {
                    "type": SectionType.BACKGROUND_INFORMATION,
                    "title": "背景信息",
                    "priority": ContentPriority.MEDIUM,
                    "order": 5,
                    "required_elements": [
                        "疾病概述",
                        "流行病学数据",
                        "病理生理",
                        "临床表现"
                    ],
                    "estimated_tokens": 1000
                },
                {
                    "type": SectionType.RESEARCH_DETAILS,
                    "title": "研究证据详情",
                    "priority": ContentPriority.LOW,
                    "order": 6,
                    "required_elements": [
                        "关键研究总结",
                        "研究方法",
                        "结果分析",
                        "局限性"
                    ],
                    "estimated_tokens": 1200
                },
                {
                    "type": SectionType.REFERENCES,
                    "title": "参考文献",
                    "priority": ContentPriority.LOW,
                    "order": 7,
                    "required_elements": [
                        "核心文献列表",
                        "引用格式",
                        "证据等级标记"
                    ],
                    "estimated_tokens": 600
                },
                {
                    "type": SectionType.IMPLEMENTATION_TIPS,
                    "title": "实施建议",
                    "priority": ContentPriority.MEDIUM,
                    "order": 8,
                    "required_elements": [
                        "临床实施步骤",
                        "患者教育要点",
                        "随访计划",
                        "质量保证措施"
                    ],
                    "estimated_tokens": 800
                }
            ]
        )

    def _create_emergency_template(self) -> PVGStructure:
        """创建紧急情况模板"""
        return PVGStructure(
            template_name="emergency_guideline",
            version="1.0",
            sections=[
                {
                    "type": SectionType.EMERGENCY_GUIDANCE,
                    "title": "紧急情况识别和处理",
                    "priority": ContentPriority.HIGH,
                    "order": 1,
                    "required_elements": [
                        "紧急情况识别标准",
                        "立即处理流程",
                        "紧急联系方式",
                        "生命体征监测要求"
                    ],
                    "estimated_tokens": 600
                },
                {
                    "type": SectionType.KEY_RECOMMENDATIONS,
                    "title": "紧急处理推荐",
                    "priority": ContentPriority.HIGH,
                    "order": 2,
                    "required_elements": [
                        "紧急治疗措施",
                        "药物选择",
                        "监测要点",
                        "转诊标准"
                    ],
                    "estimated_tokens": 800
                },
                {
                    "type": SectionType.SAFETY_WARNINGS,
                    "title": "安全警告",
                    "priority": ContentPriority.HIGH,
                    "order": 3,
                    "required_elements": [
                        "紧急情况禁忌",
                        "药物注意事项",
                        "设备要求",
                        "人员配置"
                    ],
                    "estimated_tokens": 600
                },
                {
                    "type": SectionType.REFERENCES,
                    "title": "紧急指南参考",
                    "priority": ContentPriority.LOW,
                    "order": 4,
                    "required_elements": [
                        "相关指南链接",
                        "培训资源",
                        "质量控制标准"
                    ],
                    "estimated_tokens": 400
                }
            ]
        )

    def _create_special_population_template(self) -> PVGStructure:
        """创建特殊人群模板"""
        return PVGStructure(
            template_name="special_population",
            version="1.0",
            sections=[
                {
                    "type": SectionType.KEY_RECOMMENDATIONS,
                    "title": "特殊人群推荐",
                    "priority": ContentPriority.HIGH,
                    "order": 1,
                    "required_elements": [
                        "人群特征描述",
                        "特殊考虑因素",
                        "调整的治疗方案",
                        "监测要求"
                    ],
                    "estimated_tokens": 1000
                },
                {
                    "type": SectionType.TREATMENT_OPTIONS,
                    "title": "治疗方案调整",
                    "priority": ContentPriority.HIGH,
                    "order": 2,
                    "required_elements": [
                        "剂量调整",
                        "药物选择",
                        "非药物干预",
                        "特殊注意事项"
                    ],
                    "estimated_tokens": 800
                },
                {
                    "type": SectionType.SAFETY_WARNINGS,
                    "title": "特殊安全考虑",
                    "priority": ContentPriority.HIGH,
                    "order": 3,
                    "required_elements": [
                        "药物相互作用",
                        "不良反应风险",
                        "监测指标",
                        "并发症预防"
                    ],
                    "estimated_tokens": 700
                },
                {
                    "type": SectionType.IMPLEMENTATION_TIPS,
                    "title": "实施要点",
                    "priority": ContentPriority.MEDIUM,
                    "order": 4,
                    "required_elements": [
                        "护理要点",
                        "患者教育",
                        "家庭指导",
                        "随访安排"
                    ],
                    "estimated_tokens": 600
                }
            ]
        )

    def _create_chronic_disease_template(self) -> PVGStructure:
        """创建慢性疾病模板"""
        return PVGStructure(
            template_name="chronic_disease",
            version="1.0",
            sections=[
                {
                    "type": SectionType.KEY_RECOMMENDATIONS,
                    "title": "长期管理推荐",
                    "priority": ContentPriority.HIGH,
                    "order": 1,
                    "required_elements": [
                        "治疗目标设定",
                        "综合治疗方案",
                        "生活质量考虑",
                        "长期随访计划"
                    ],
                    "estimated_tokens": 1200
                },
                {
                    "type": SectionType.TREATMENT_OPTIONS,
                    "title": "治疗策略",
                    "priority": ContentPriority.HIGH,
                    "order": 2,
                    "required_elements": [
                        "药物治疗",
                        "生活方式干预",
                        "心理支持",
                        "康复治疗"
                    ],
                    "estimated_tokens": 1000
                },
                {
                    "type": SectionType.SAFETY_WARNINGS,
                    "title": "长期安全性",
                    "priority": ContentPriority.HIGH,
                    "order": 3,
                    "required_elements": [
                        "长期用药安全性",
                        "药物相互作用",
                        "监测频率",
                        "不良反应预防"
                    ],
                    "estimated_tokens": 800
                },
                {
                    "type": SectionType.MONITORING,
                    "title": "监测和评估",
                    "priority": ContentPriority.MEDIUM,
                    "order": 4,
                    "required_elements": [
                        "临床指标监测",
                        "治疗效果评估",
                        "并发症筛查",
                        "生活质量评估"
                    ],
                    "estimated_tokens": 700
                },
                {
                    "type": SectionType.IMPLEMENTATION_TIPS,
                    "title": "实施指南",
                    "priority": ContentPriority.MEDIUM,
                    "order": 5,
                    "required_elements": [
                        "团队协作",
                        "患者自我管理",
                        "社区资源利用",
                        "信息化管理"
                    ],
                    "estimated_tokens": 800
                }
            ]
        )

    def create_custom_template(self, sections_config: List[Dict[str, Any]]) -> PVGStructure:
        """创建自定义模板"""
        return PVGStructure(
            template_name="custom",
            version="1.0",
            sections=sections_config
        )

    def get_template_for_agent_types(self, agent_types: List[AgentType]) -> str:
        """根据智能体类型选择模板"""
        if AgentType.DIAGNOSIS in agent_types or AgentType.TREATMENT in agent_types:
            return "standard_clinical"
        elif any("emergency" in str(agent_type).lower() for agent_type in agent_types):
            return "emergency_guideline"
        elif AgentType.SPECIAL_POPULATIONS in agent_types:
            return "special_population"
        else:
            return "standard_clinical"

    def extract_sections_from_agent_results(self, agent_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从智能体结果中提取章节信息"""
        sections = []

        # 根据智能体结果确定需要的章节
        if "diagnosis" in agent_results:
            sections.append({
                "type": SectionType.KEY_RECOMMENDATIONS,
                "title": "诊断相关推荐",
                "priority": ContentPriority.HIGH,
                "order": 1
            })

        if "treatment" in agent_results:
            sections.append({
                "type": SectionType.TREATMENT_OPTIONS,
                "title": "治疗方案",
                "priority": ContentPriority.HIGH,
                "order": 2
            })

        if "prevention" in agent_results:
            sections.append({
                "type": SectionType.SAFETY_WARNINGS,
                "title": "预防和安全警告",
                "priority": ContentPriority.HIGH,
                "order": 3
            })

        if "monitoring" in agent_results:
            sections.append({
                "type": SectionType.IMPLEMENTATION_TIPS,
                "title": "监测和实施建议",
                "priority": ContentPriority.MEDIUM,
                "order": 5
            })

        return sections