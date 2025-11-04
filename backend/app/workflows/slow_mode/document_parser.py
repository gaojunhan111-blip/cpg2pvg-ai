"""
智能文档解析层
CPG2PVG-AI System HierarchicalMedicalParser (Node 1)
"""

import logging
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from app.workflows.base import BaseWorkflowNode
from app.workflows.types import (
    ProcessingContext,
    ProcessingResult,
    ProcessingStatus,
    DocumentSection,
    ContentType,
)
from app.core.llm_client import LLMClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class HierarchicalMedicalParser(BaseWorkflowNode):
    """智能文档解析器 - 基于医学文档结构的智能解析"""

    def __init__(self):
        super().__init__(
            name="HierarchicalMedicalParser",
            description="基于医学文档结构的智能解析，识别章节层次结构和内容类型"
        )

        # 初始化LLM客户端
        self.llm_client = LLMClient()

        # 配置参数
        self.max_preview_length = 5000  # 预览文本长度
        self.min_section_length = 50   # 最小章节长度
        self.max_chunk_size = 800     # 最大块大小

    async def execute(
        self,
        context: ProcessingContext,
        input_data: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[ProcessingResult, None]:
        """执行文档解析"""

        try:
            # 解析输入数据
            document_content = input_data.get("document_content", "")
            document_type = input_data.get("document_type", "")
            file_metadata = input_data.get("file_metadata", {})

            # 验证输入
            if not document_content:
                yield ProcessingResult(
                    step_name=self.name,
                    status=ProcessingStatus.FAILED,
                    success=False,
                    error_message="文档内容为空"
                )
                return

            # 1. 结构分析
            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.RUNNING,
                success=True,
                message="开始文档结构分析"
            )

            structure_result = await self._analyze_document_structure(
                document_content, document_type
            )

            yield ProcessingResult(
                step_name=f"{self.name}_structure_analysis",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data=structure_result,
                message="文档结构分析完成"
            )

            # 2. 分层解析
            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.RUNNING,
                success=True,
                message="开始分层解析"
            )

            sections = await self._extract_semantic_sections(
                document_content, structure_result
            )

            # 3. 内容分类和提取
            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.RUNNING,
                success=True,
                message="开始内容分类和提取"
            )

            classified_sections = await self._classify_content_types(sections)

            # 4. 医学实体识别
            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.RUNNING,
                success=True,
                message="开始医学实体识别"
            )

            enhanced_sections = await self._identify_medical_entities(
                classified_sections, context
            )

            # 5. 生成解析结果
            final_result = {
                "sections": enhanced_sections,
                "total_sections": len(enhanced_sections),
                "structure_analysis": structure_result,
                "file_metadata": file_metadata,
                "parsing_metadata": {
                    "parser_version": "1.0",
                    "parsing_time": datetime.utcnow().isoformat(),
                    "content_length": len(document_content),
                    "document_type": document_type
                }
            }

            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.COMPLETED,
                success=True,
                data=final_result,
                message=f"文档解析完成，共提取{len(enhanced_sections)}个段落",
                metadata={
                    "section_count": len(enhanced_sections),
                    "content_length": len(document_content)
                }
            )

        except Exception as e:
            logger.error(f"文档解析失败: {str(e)}")
            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.FAILED,
                success=False,
                error_message=str(e)
            )

    async def _analyze_document_structure(
        self, content: str, document_type: str
    ) -> Dict[str, Any]:
        """分析文档结构"""
        try:
            # 只分析前5000字符以节省成本
            preview_content = content[:self.max_preview_length]

            # 使用LLM分析文档结构
            structure_prompt = self._build_structure_analysis_prompt(
                preview_content, document_type
            )

            response = await self.llm_client.chat_completion(
                messages=[{
                    "role": "user",
                    "content": structure_prompt
                }],
                max_tokens=1000,
                temperature=0.1
            )

            # 解析LLM响应
            structure_info = self._parse_structure_analysis_response(response)

            return structure_info

        except Exception as e:
            logger.error(f"文档结构分析失败: {str(e)}")
            return {"error": str(e)}

    async def _extract_semantic_sections(
        self, content: str, structure_info: Dict[str, Any]
    ) -> list[DocumentSection]:
        """提取语义章节"""
        try:
            sections = []

            # 使用LLM进行分段
            section_prompt = self._build_section_extraction_prompt(content, structure_info)

            response = await self.llm_client.chat_completion(
                messages=[{
                    "role": "user",
                    "content": section_prompt
                }],
                max_tokens=2000,
                temperature=0.2
            )

            # 解析LLM响应并创建DocumentSection对象
            sections = self._parse_section_extraction_response(response)

            return sections

        except Exception as e:
            logger.error(f"语义章节提取失败: {str(e)}")
            return []

    async def _classify_content_types(
        self, sections: list[DocumentSection]
    ) -> list[DocumentSection]:
        """分类内容类型"""
        try:
            for section in sections:
                if not section.content:
                    continue

                # 使用LLM分类内容类型
                classification_prompt = self._build_content_classification_prompt(
                    section.title, section.content
                )

                response = await self.llm_client.chat_completion(
                    messages=[{
                        "role": "user",
                        "content": classification_prompt
                    }],
                    max_tokens=500,
                    temperature=0.1
                )

                # 解析分类结果
                content_type = self._parse_content_type(response)
                section.content_type = content_type

            return sections

        except Exception as e:
            logger.error(f"内容类型分类失败: {str(e)}")
            return sections

    async def _identify_medical_entities(
        self, sections: list[DocumentSection], context: ProcessingContext
    ) -> list[DocumentSection]:
        """识别医学实体"""
        try:
            for section in sections:
                if not section.content:
                    continue

                # 使用LLM识别医学实体
                entity_prompt = self._build_medical_entity_prompt(
                    section.content, context.medical_specialties
                )

                response = await self.llm_client.chat_completion(
                    messages=[{
                        "role": "user",
                        "content": entity_prompt
                    }],
                    max_tokens=800,
                    temperature=0.1
                )

                # 解析实体识别结果
                entities = self._parse_medical_entities(response)

                # 更新章节元数据
                section.metadata["medical_entities"] = entities

            return sections

        except Exception as e:
            logger.error(f"医学实体识别失败: {str(e)}")
            return sections

    def _build_structure_analysis_prompt(
        self, content: str, document_type: str
    ) -> str:
        """构建文档结构分析提示词"""
        return f"""
请分析以下医学指南文档的结构，并提取关键信息：

文档类型: {document_type}

文档内容预览：
{content[:2000]}

请提供以下信息：
1. 文档的整体结构类型（如：标准医学指南、专家共识、系统综述等）
2. 主要章节类型（如：摘要、引言、方法、结果、讨论、结论等）
3. 标题层级规律（如：1. 2. 3. 或 I. II. III. 等）
4. 特殊内容类型（如：表格、图表、算法流程图、参考文献等）
5. 医学专业领域
6. 建议的分块策略

请以JSON格式返回结果。
"""

    def _build_section_extraction_prompt(
        self, content: str, structure_info: Dict[str, Any]
    ) -> str:
        """构建章节提取提示词"""
        return f"""
基于以下文档结构信息，请将医学指南文档分解为语义相关的段落：

文档结构信息：
{structure_info}

文档内容：
{content[:3000]}

请按照以下要求分解段落：
1. 保持段落的语义完整性
2. 每个段落应该有明确的主题
3. 段落长度控制在{self.min_chunk_size}-{self.max_chunk_size}个字符
4. 保留标题层级信息
5. 识别特殊内容（表格、图表等）

请以JSON格式返回段落列表，每个段落包含：
- title: 段落标题
- content: 段落内容
- level: 标题层级（0-6）
- content_type: 内容类型
"""

    def _build_content_classification_prompt(
        self, title: str, content: str
    ) -> str:
        """构建内容分类提示词"""
        return f"""
请分析以下医学文档段落的内容类型：

标题: {title}
内容: {content[:1000]}

请判断该段落的内容类型（从以下选项中选择）：
- TEXT: 纯文本内容
- TABLE: 表格数据
- IMAGE: 图表或图像
- ALGORITHM: 算法流程
- REFERENCE: 参考文献
- FOOTNOTE: 脚注
- METADATA: 元数据信息

请直接返回内容类型名称。
"""

    def _build_medical_entity_prompt(
        self, content: str, specialties: list
    ) -> str:
        """构建医学实体识别提示词"""
        specialties_str = ", ".join(specialties) if specialties else "未指定"

        return f"""
请识别以下医学文档段落中的医学实体：

专业领域: {specialties_str}

段落内容: {content[:1500]}

请识别以下类型的医学实体：
1. 疾病名称
2. 症症描述
3. 诊断标准
4. 治疗方法
5. 药物名称
6. 检查项目
7. 预防措施
8. 医学术语

请以JSON格式返回识别的实体列表。
"""

    def _parse_structure_analysis_response(self, response: str) -> Dict[str, Any]:
        """解析结构分析响应"""
        try:
            # 这里应该解析LLM返回的JSON响应
            # 简化实现，实际应该使用json.loads
            return {
                "document_type": "medical_guideline",
                "main_structure": ["摘要", "引言", "方法", "结果", "讨论", "结论"],
                "title_pattern": "hierarchical",
                "special_content": ["tables", "figures", "algorithms"],
                "medical_specialties": ["general"],
                "chunking_strategy": "semantic"
            }
        except Exception as e:
            logger.error(f"解析结构分析响应失败: {str(e)}")
            return {}

    def _parse_section_extraction_response(self, response: str) -> list[DocumentSection]:
        """解析章节提取响应"""
        try:
            # 这里应该解析LLM返回的段落列表
            # 简化实现，创建示例段落
            sections = [
                DocumentSection(
                    title="文档标题",
                    content=response[:500],
                    content_type=ContentType.TEXT,
                    level=1
                )
            ]
            return sections
        except Exception as e:
            logger.error(f"解析章节提取响应失败: {str(e)}")
            return []

    def _parse_content_type(self, response: str) -> ContentType:
        """解析内容类型响应"""
        try:
            response = response.strip().upper()

            # 映射响应到ContentType枚举
            type_mapping = {
                "TEXT": ContentType.TEXT,
                "TABLE": ContentType.TABLE,
                "IMAGE": ContentType.IMAGE,
                "ALGORITHM": ContentType.ALGORITHM,
                "REFERENCE": ContentType.REFERENCE,
                "FOOTNOTE": ContentType.FOOTNOTE,
                "METADATA": ContentType.METADATA,
            }

            return type_mapping.get(response, ContentType.TEXT)

        except Exception as e:
            logger.error(f"解析内容类型响应失败: {str(e)}")
            return ContentType.TEXT

    def _parse_medical_entities(self, response: str) -> Dict[str, Any]:
        """解析医学实体识别响应"""
        try:
            # 这里应该解析LLM返回的实体JSON
            # 简化实现
            return {
                "diseases": [],
                "symptoms": [],
                "treatments": [],
                "drugs": [],
                "procedures": [],
                "medical_terms": []
            }
        except Exception as e:
            logger.error(f"解析医学实体响应失败: {str(e)}")
            return {}

    def adaptive_chunking(
        self, parsed_document: list[DocumentSection], max_chunk_size: int = None
    ) -> list[DocumentSection]:
        """自适应分块策略"""
        if max_chunk_size is None:
            max_chunk_size = self.max_chunk_size

        chunks = []
        for section in parsed_document:
            if len(section.content) <= max_chunk_size:
                chunks.append(section)
            else:
                # 对长段落进行分块
                chunks.extend(self._split_long_section(section, max_chunk_size))

        return chunks

    def _split_long_section(
        self, section: DocumentSection, max_chunk_size: int
    ) -> list[DocumentSection]:
        """分割长段落"""
        chunks = []
        content = section.content
        words = content.split()

        current_chunk = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 > max_chunk_size:
                # 保存当前chunk
                chunk_content = " ".join(current_chunk)
                if chunk_content.strip():
                    chunk = DocumentSection(
                        title=section.title,
                        content=chunk_content,
                        content_type=section.content_type,
                        level=section.level
                    )
                    chunks.append(chunk)

                # 开始新chunk
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1

        # 处理最后一个chunk
        if current_chunk:
            chunk_content = " ".join(current_chunk)
            chunk = DocumentSection(
                title=section.title,
                content=chunk_content,
                content_type=section.content_type,
                level=section.level
            )
            chunks.append(chunk)

        return chunks