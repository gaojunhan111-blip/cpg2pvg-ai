"""
通用枚举定义
Common Enums
"""

from enum import Enum


class SectionType(str, Enum):
    """PVG章节类型"""
    EMERGENCY_GUIDANCE = "emergency_guidance"
    KEY_RECOMMENDATIONS = "key_recommendations"
    TREATMENT_OPTIONS = "treatment_options"
    SAFETY_WARNINGS = "safety_warnings"
    BACKGROUND_INFORMATION = "background_information"
    RESEARCH_DETAILS = "research_details"
    REFERENCES = "references"
    IMPLEMENTATION_TIPS = "implementation_tips"
    APPENDICES = "appendices"
    MONITORING = "monitoring"


class ContentPriority(str, Enum):
    """内容优先级"""
    HIGH = "high"      # 关键内容，使用GPT-4
    MEDIUM = "medium"   # 平衡内容，使用GPT-3.5-turbo
    LOW = "low"         # 成本优化内容，使用GPT-3.5-turbo-instruct


class GenerationStatus(str, Enum):
    """生成状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    STREAMING = "streaming"


class AgentType(str, Enum):
    """智能体类型"""
    DIAGNOSIS = "diagnosis"
    TREATMENT = "treatment"
    PREVENTION = "prevention"
    MONITORING = "monitoring"
    SPECIAL_POPULATIONS = "special_populations"
    FOLLOW_UP = "follow_up"
    EDUCATION = "education"
    COORDINATION = "coordination"