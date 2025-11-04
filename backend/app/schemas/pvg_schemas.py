"""
PVG数据模式定义
Practice Guideline Visualization Data Schemas
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

from app.enums.common import SectionType, ContentPriority, GenerationStatus


@dataclass
class SectionContent:
    """章节内容"""
    section_type: SectionType
    title: str
    priority: ContentPriority
    description: str
    required_elements: List[str] = field(default_factory=list)
    optional_elements: List[str] = field(default_factory=list)
    context_data: Dict[str, Any] = field(default_factory=dict)
    estimated_tokens: int = 500
    quality_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PVGSection:
    """PVG章节"""
    section_id: str
    section_type: SectionType
    title: str
    content: str
    priority: ContentPriority
    order: int

    # 可选字段和有默认值的字段
    html_content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 生成信息
    status: GenerationStatus = GenerationStatus.PENDING
    model_used: str = ""
    generation_time: float = 0.0
    tokens_used: int = 0
    cost_estimate: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class PVGStructure:
    """PVG结构定义"""
    sections: List[Dict[str, Any]] = field(default_factory=list)
    template_name: str = "standard_pvg"
    version: str = "1.0"

    def get_section_by_type(self, section_type: SectionType) -> Optional[Dict[str, Any]]:
        """根据类型获取章节配置"""
        return next((s for s in self.sections if s.get("type") == section_type.value), None)

    def get_high_priority_sections(self) -> List[Dict[str, Any]]:
        """获取高优先级章节"""
        return [s for s in self.sections if s.get("priority") == ContentPriority.HIGH.value]

    def get_section_order(self) -> List[Dict[str, Any]]:
        """获取章节顺序"""
        return sorted(self.sections, key=lambda x: x.get("order", 999))


@dataclass
class GenerationConfig:
    """生成配置"""
    high_quality_llm: str = "gpt-4"
    balanced_llm: str = "gpt-3.5-turbo"
    cost_effective_llm: str = "gpt-3.5-turbo-instruct"

    # 质量要求
    high_priority_iterations: int = 3
    medium_priority_iterations: int = 2
    low_priority_iterations: int = 1

    # 成本控制
    max_total_tokens: int = 4000
    emergency_tokens_limit: int = 1000

    # 流式输出
    enable_streaming: bool = True
    chunk_size: int = 100

    # 模型选择策略
    model_strategy: Dict[str, str] = field(default_factory=lambda: {
        "emergency_guidance": "gpt-4",
        "key_recommendations": "gpt-4",
        "treatment_options": "gpt-3.5-turbo",
        "safety_warnings": "gpt-4",
        "background_information": "gpt-3.5-turbo-instruct",
        "research_details": "gpt-3.5-turbo-instruct",
        "references": "gpt-3.5-turbo-instruct",
        "implementation_tips": "gpt-3.5-turbo",
        "appendices": "gpt-3.5-turbo-instruct"
    })


@dataclass
class PVGDocument:
    """PVG文档"""
    document_id: str
    guideline_id: str
    title: str
    subtitle: str = ""
    version: str = "1.0"

    sections: List[PVGSection] = field(default_factory=list)
    template_structure: Optional[PVGStructure] = None

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 生成状态
    status: GenerationStatus = GenerationStatus.PENDING
    progress: float = 0.0

    # 统计信息
    total_tokens: int = 0
    total_cost: float = 0.0
    generation_time: float = 0.0

    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def get_section(self, section_type: SectionType) -> Optional[PVGSection]:
        """获取指定类型的章节"""
        return next((s for s in self.sections if s.section_type == section_type), None)

    def get_completed_sections(self) -> List[PVGSection]:
        """获取已完成的章节"""
        return [s for s in self.sections if s.status == GenerationStatus.COMPLETED]

    def update_progress(self) -> None:
        """更新进度"""
        if self.sections:
            completed = len([s for s in self.sections if s.status == GenerationStatus.COMPLETED])
            self.progress = completed / len(self.sections)

    def get_section_content(self, section_type: SectionType) -> str:
        """获取章节内容"""
        section = self.get_section(section_type)
        return section.content if section else ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "document_id": self.document_id,
            "guideline_id": self.guideline_id,
            "title": self.title,
            "subtitle": self.subtitle,
            "version": self.version,
            "sections": [self._section_to_dict(s) for s in self.sections],
            "status": self.status,
            "progress": self.progress,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

    def _section_to_dict(self, section: PVGSection) -> Dict[str, Any]:
        """章节转换为字典"""
        return {
            "section_id": section.section_id,
            "section_type": section.section_type,
            "title": section.title,
            "content": section.content,
            "priority": section.priority,
            "status": section.status,
            "order": section.order,
            "metadata": section.metadata
        }


# Pydantic模型用于API响应
class PVGSectionResponse(BaseModel):
    """PVG章节响应模型"""
    section_id: str
    section_type: str
    title: str
    content: str
    priority: str
    status: str
    order: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PVGDocumentResponse(BaseModel):
    """PVG文档响应模型"""
    document_id: str
    guideline_id: str
    title: str
    subtitle: Optional[str] = None
    version: str
    sections: List[PVGSectionResponse]
    status: str
    progress: float
    total_tokens: int
    total_cost: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    completed_at: Optional[datetime] = None


class GenerationRequest(BaseModel):
    """生成请求模型"""
    guideline_id: str
    agent_results: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None
    template: Optional[str] = None
    enable_streaming: bool = True