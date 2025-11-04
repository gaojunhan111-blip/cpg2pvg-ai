"""
多模态内容处理管道
CPG2PVG-AI System MultiModalProcessor (Node 2)
"""

import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator, List
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from app.workflows.base import BaseWorkflowNode
from app.workflows.types import (
    ProcessingContext,
    ProcessingResult,
    ProcessingStatus,
    DocumentSection,
    ContentType,
)

logger = logging.getLogger(__name__)


class MultiModalProcessor(BaseWorkflowNode):
    """多模态内容处理器 - 并行处理不同类型的内容"""

    def __init__(self):
        super().__init__(
            name="MultiModalProcessor",
            description="并行处理文本、表格、算法等不同类型的内容"
        )
        self.thread_pool = ThreadPoolExecutor(max_workers=3)
        self.max_tables = 10  # 限制处理表格数量以控制成本

    async def execute(
        self,
        context: ProcessingContext,
        input_data: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[ProcessingResult, None]:
        """执行多模态处理"""

        try:
            # 解析输入数据
            parsed_document = input_data.get("parsed_sections", [])

            if not parsed_document:
                yield ProcessingResult(
                    step_name=self.name,
                    status=ProcessingStatus.FAILED,
                    success=False,
                    error_message="解析后的文档内容为空"
                )
                return

            # 分类不同类型的内容
            text_sections = []
            table_sections = []
            image_sections = []
            algorithm_sections = []
            other_sections = []

            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.RUNNING,
                success=True,
                message="开始内容分类"
            )

            for section in parsed_document:
                if section.content_type == ContentType.TEXT:
                    text_sections.append(section)
                elif section.content_type == ContentType.TABLE:
                    table_sections.append(section)
                elif section.content_type == ContentType.IMAGE:
                    image_sections.append(section)
                elif section.content_type == ContentType.ALGORITHM:
                    algorithm_sections.append(section)
                else:
                    other_sections.append(section)

            yield ProcessingResult(
                step_name=f"{self.name}_classification",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data={
                    "text_count": len(text_sections),
                    "table_count": len(table_sections),
                    "image_count": len(image_sections),
                    "algorithm_count": len(algorithm_sections),
                    "other_count": len(other_sections)
                },
                message="内容分类完成"
            )

            # 并行处理不同类型的内容
            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.RUNNING,
                success=True,
                message="开始并行处理"
            )

            # 创建并行任务
            tasks = {}
            if text_sections:
                tasks["text"] = self.thread_pool.submit(
                    self._process_text_sections, text_sections
                )
            if table_sections:
                tasks["tables"] = self.thread_pool.submit(
                    self._process_medical_tables, table_sections[:self.max_tables]
                )
            if image_sections:
                tasks["images"] = self.thread_pool.submit(
                    self._process_medical_images, image_sections
                )
            if algorithm_sections:
                tasks["algorithms"] = self.thread_pool.submit(
                    self._process_clinical_algorithms, algorithm_sections
                )

            # 等待所有任务完成
            results = {}
            for content_type, future in tasks.items():
                try:
                    results[content_type] = await asyncio.wrap_future(future)
                except Exception as e:
                    logger.error(f"处理{content_type}内容失败: {str(e)}")
                    results[content_type] = []

            # 生成处理结果
            processed_content = {
                "text_sections": results.get("text", []),
                "table_sections": results.get("tables", []),
                "image_sections": results.get("images", []),
                "algorithm_sections": results.get("algorithms", []),
                "other_sections": other_sections,
                "processing_metadata": {
                    "parallel_tasks": len(tasks),
                    "processing_time": datetime.utcnow().isoformat(),
                    "cost_level": context.cost_level.value
                }
            }

            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.COMPLETED,
                success=True,
                data=processed_content,
                message=f"多模态处理完成，共处理{len(parsed_document)}个段落"
            )

        except Exception as e:
            logger.error(f"多模态处理失败: {str(e)}")
            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.FAILED,
                success=False,
                error_message=str(e)
            )

    def _process_text_sections(self, sections: List[DocumentSection]) -> List[Dict[str, Any]]:
        """处理文本段落"""
        try:
            processed_texts = []
            for section in sections:
                # 文本预处理和增强
                enhanced_text = self._enhance_text_content(section)
                processed_texts.append(enhanced_text)
            return processed_texts
        except Exception as e:
            logger.error(f"处理文本段落失败: {str(e)}")
            return []

    def _process_medical_tables(self, tables: List[DocumentSection]) -> List[Dict[str, Any]]:
        """处理医学表格"""
        try:
            processed_tables = []
            for table in tables:
                if self._is_clinically_important(table):
                    # 智能表格处理
                    enhanced_table = self._extract_and_process_table(table)
                    processed_tables.append(enhanced_table)
            return processed_tables
        except Exception as e:
            logger.error(f"处理医学表格失败: {str(e)}")
            return []

    def _process_medical_images(self, images: List[DocumentSection]) -> List[Dict[str, Any]]:
        """处理医学图像和图表"""
        try:
            processed_images = []
            for image in images:
                # 使用多模态LLM分析图像
                enhanced_image = self._analyze_medical_image(image)
                processed_images.append(enhanced_image)
            return processed_images
        except Exception as e:
            logger.error(f"处理医学图像失败: {str(e)}")
            return []

    def _process_clinical_algorithms(self, algorithms: List[DocumentSection]) -> List[Dict[str, Any]]:
        """处理临床算法流程"""
        try:
            processed_algorithms = []
            for algorithm in algorithms:
                # 解析算法流程
                enhanced_algorithm = self._parse_algorithm_flow(algorithm)
                processed_algorithms.append(enhanced_algorithm)
            return processed_algorithms
        except Exception as e:
            logger.error(f"处理临床算法失败: {str(e)}")
            return []

    def _enhance_text_content(self, section: DocumentSection) -> Dict[str, Any]:
        """增强文本内容"""
        return {
            "id": section.id,
            "title": section.title,
            "content": section.content,
            "enhanced_content": section.content,  # 这里可以添加文本增强逻辑
            "metadata": {
                "original_length": len(section.content),
                "content_type": section.content_type.value,
                "level": section.level
            }
        }

    def _is_clinically_important(self, table_section: DocumentSection) -> bool:
        """判断表格是否具有临床重要性"""
        # 简化的判断逻辑
        important_keywords = [
            "试验", "研究", "结果", "数据", "统计",
            "比较", "随访", "疗效", "安全性", "不良事件",
            "诊断", "治疗", "预防", "筛查", "指南", "推荐"
        ]
        title_lower = table_section.title.lower()
        return any(keyword in title_lower for keyword in important_keywords)

    def _extract_and_process_table(self, table_section: DocumentSection) -> Dict[str, Any]:
        """提取和处理表格"""
        # 这里应该实现具体的表格提取逻辑
        return {
            "id": table_section.id,
            "title": table_section.title,
            "summary": f"表格摘要: {table_section.title}",
            "data": [],  # 实际应该提取表格数据
            "columns": [],
            "rows": 0,
            "metadata": {
                "content_type": table_section.content_type.value
            }
        }

    def _analyze_medical_image(self, image_section: DocumentSection) -> Dict[str, Any]:
        """分析医学图像"""
        # 这里应该使用多模态LLM分析图像
        return {
            "id": image_section.id,
            "description": f"图像分析: {image_section.title}",
            "content": image_section.content,
            "analysis": {
                "type": "medical_image",
                "description": "医学相关图像或图表"
            },
            "metadata": {
                "content_type": image_section.content_type.value
            }
        }

    def _parse_algorithm_flow(self, algorithm_section: DocumentSection) -> Dict[str, Any]:
        """解析算法流程"""
        return {
            "id": algorithm_section.id,
            "title": algorithm_section.title,
            "content": algorithm_section.content,
            "flow": {
                "steps": [],  # 实际应该解析算法步骤
                "description": "临床决策算法流程"
            },
            "metadata": {
                "content_type": algorithm_section.content_type.value
            }
        }