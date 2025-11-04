"""
节点1：智能文档解析层
Node 1: Intelligent Document Parsing Layer
"""

from pathlib import Path
from dataclasses import asdict
from typing import Dict, Any, List
import asyncio
import json

from app.core.database import get_db
from app.core.logger import get_logger
from app.models.medical_document import (
    MedicalDocumentModel,
    DocumentSectionModel,
    MedicalTableModel,
    ClinicalAlgorithmModel,
    EvidenceHierarchyModel,
    DocumentChunkModel
)
from app.services.medical_parser import (
    parse_medical_document,
    create_document_chunks,
    MedicalDocument,
    DocumentChunk
)
from celery_worker.workflow.base_node import BaseWorkflowNode


class MedicalParserNode(BaseWorkflowNode):
    """智能文档解析节点"""

    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.node_name = "medical_parser"
        self.node_description = "智能医学文档解析层"

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理医学文档解析任务"""
        try:
            self.logger.info(f"开始处理文档解析任务: {input_data.get('task_id', 'unknown')}")

            # 获取输入参数
            file_path = input_data.get('file_path')
            guideline_id = input_data.get('guideline_id')
            task_id = input_data.get('task_id')

            if not file_path:
                raise ValueError("缺少文件路径参数")

            if not guideline_id:
                raise ValueError("缺少指南ID参数")

            # 执行文档解析
            parsed_document = await parse_medical_document(file_path)

            # 创建文档分块
            chunks = await create_document_chunks(parsed_document)

            # 保存到数据库
            result_data = await self._save_to_database(
                parsed_document, chunks, guideline_id, task_id
            )

            self.logger.info(f"文档解析完成: {len(chunks)} 个分块")

            return {
                "status": "success",
                "document_id": parsed_document.document_id,
                "chunks_count": len(chunks),
                "sections_count": len(parsed_document.sections),
                "tables_count": len(parsed_document.tables),
                "algorithms_count": len(parsed_document.algorithms),
                "result_data": result_data
            }

        except Exception as e:
            self.logger.error(f"文档解析失败: {e}")
            return {
                "status": "error",
                "error_message": str(e)
            }

    async def _save_to_database(
        self,
        parsed_document: MedicalDocument,
        chunks: List[DocumentChunk],
        guideline_id: str,
        task_id: str
    ) -> Dict[str, Any]:
        """保存解析结果到数据库"""
        try:
            async with get_db() as db:
                # 保存文档主记录
                doc_model = MedicalDocumentModel(
                    guideline_id=guideline_id,
                    document_id=parsed_document.document_id,
                    file_path=parsed_document.metadata.file_path,
                    file_type=parsed_document.metadata.file_type.value,
                    word_count=parsed_document.metadata.word_count,
                    char_count=parsed_document.metadata.char_count,
                    processing_status="completed"
                )

                db.add(doc_model)
                await db.flush()

                # 保存章节
                for section in parsed_document.sections:
                    section_model = DocumentSectionModel(
                        document_id=doc_model.id,
                        section_id=section.section_id,
                        title=section.title,
                        section_type=section.section_type.value,
                        content=section.content,
                        start_position=section.start_position,
                        end_position=section.end_position,
                        level=section.level
                    )
                    db.add(section_model)

                # 保存表格
                for table in parsed_document.tables:
                    table_model = MedicalTableModel(
                        document_id=doc_model.id,
                        table_id=table.table_id,
                        title=table.title,
                        headers=table.headers,
                        rows=table.rows,
                        content_text=table.content_text
                    )
                    db.add(table_model)

                # 保存算法
                for algorithm in parsed_document.algorithms:
                    algorithm_model = ClinicalAlgorithmModel(
                        document_id=doc_model.id,
                        algorithm_id=algorithm.algorithm_id,
                        title=algorithm.title,
                        steps=algorithm.steps,
                        decision_points=algorithm.decision_points,
                        flowchart_text=algorithm.flowchart_text
                    )
                    db.add(algorithm_model)

                # 保存分块
                for chunk in chunks:
                    chunk_model = DocumentChunkModel(
                        document_id=doc_model.id,
                        chunk_id=chunk.chunk_id,
                        content=chunk.content,
                        chunk_type=chunk.chunk_type.value,
                        start_position=chunk.start_position,
                        end_position=chunk.end_position,
                        word_count=chunk.word_count
                    )
                    db.add(chunk_model)

                await db.commit()

                return {
                    "document_model_id": doc_model.id,
                    "sections_saved": len(parsed_document.sections),
                    "tables_saved": len(parsed_document.tables),
                    "algorithms_saved": len(parsed_document.algorithms),
                    "chunks_saved": len(chunks)
                }

        except Exception as e:
            self.logger.error(f"保存到数据库失败: {e}")
            raise

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        required_fields = ['file_path', 'guideline_id', 'task_id']

        for field in required_fields:
            if field not in input_data or not input_data[field]:
                self.logger.error(f"缺少必需字段: {field}")
                return False

        # 验证文件路径是否存在
        file_path = Path(input_data['file_path'])
        if not file_path.exists():
            self.logger.error(f"文件不存在: {file_path}")
            return False

        return True

    def get_node_info(self) -> Dict[str, Any]:
        """获取节点信息"""
        return {
            "node_name": self.node_name,
            "node_description": self.node_description,
            "node_type": "medical_parser",
            "supported_formats": ["pdf", "docx", "txt"],
            "capabilities": [
                "文档解析",
                "章节提取",
                "表格识别",
                "算法提取",
                "智能分块"
            ]
        }


# 节点工厂函数
def create_node():
    """创建医学文档解析节点实例"""
    return MedicalParserNode()


# 导出节点
__all__ = ['MedicalParserNode', 'create_node']