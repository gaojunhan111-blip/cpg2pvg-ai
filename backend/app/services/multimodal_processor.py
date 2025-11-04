"""
多模态内容处理服务
Multimodal Content Processing Service
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
import uuid

from app.core.logger import get_logger

logger = get_logger(__name__)


class ContentModality(str, Enum):
    """内容模态类型"""
    TEXT = "text"
    TABLE = "table"
    ALGORITHM = "algorithm"
    IMAGE = "image"


@dataclass
class ProcessedContent:
    """处理后的内容"""
    content_id: str
    original_content: str
    modality: ContentModality
    processed_text: str
    entities: List[Dict[str, Any]] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None
    processing_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)


class MultimodalProcessor:
    """多模态内容处理器"""

    def __init__(self):
        self.logger = get_logger(__name__)

    async def process_content(
        self,
        content: str,
        modality: ContentModality = ContentModality.TEXT,
        content_id: Optional[str] = None
    ) -> ProcessedContent:
        """处理多模态内容"""
        start_time = time.time()

        if not content_id:
            content_id = str(uuid.uuid4())

        try:
            # 预处理
            processed_text = await self._preprocess_content(content, modality)

            # 提取实体（简化版）
            entities = await self._extract_entities(processed_text)

            # 提取关键词
            keywords = await self._extract_keywords(processed_text)

            # 生成嵌入向量（模拟）
            embedding = await self._generate_embedding(processed_text)

            processing_time = time.time() - start_time

            return ProcessedContent(
                content_id=content_id,
                original_content=content,
                modality=modality,
                processed_text=processed_text,
                entities=entities,
                keywords=keywords,
                embedding=embedding,
                processing_time=processing_time
            )

        except Exception as e:
            self.logger.error(f"Failed to process content {content_id}: {e}")
            raise

    async def _preprocess_content(self, content: str, modality: ContentModality) -> str:
        """预处理内容"""
        # 基本文本清理
        processed = content.strip()

        # 移除多余空白
        import re
        processed = re.sub(r'\s+', ' ', processed)

        return processed

    async def _extract_entities(self, content: str) -> List[Dict[str, Any]]:
        """提取实体（简化版）"""
        entities = []

        # 简单的医学实体模式
        medical_terms = [
            "diabetes", "hypertension", "cancer", "pneumonia",
            "insulin", "metformin", "treatment", "diagnosis"
        ]

        content_lower = content.lower()
        for term in medical_terms:
            if term in content_lower:
                start_pos = content_lower.find(term)
                entities.append({
                    "text": term,
                    "label": "medical_term",
                    "confidence": 0.8,
                    "start_pos": start_pos,
                    "end_pos": start_pos + len(term)
                })

        return entities

    async def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词"""
        words = content.lower().split()

        medical_keywords = {
            "treatment", "diagnosis", "prevention", "monitoring",
            "patient", "clinical", "medical", "health"
        }

        keywords = [word for word in words if word in medical_keywords and len(word) > 3]
        return list(set(keywords))[:10]  # 去重并限制数量

    async def _generate_embedding(self, content: str) -> Optional[List[float]]:
        """生成嵌入向量（模拟）"""
        await asyncio.sleep(0.001)  # 模拟处理延迟

        # 生成简化的嵌入向量
        import random
        return [round(random.uniform(-1, 1), 4) for _ in range(128)]

    async def process_batch(self, contents: List[str]) -> List[ProcessedContent]:
        """批量处理内容"""
        tasks = [
            self.process_content(content)
            for content in contents
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)


# 全局实例
multimodal_processor = MultimodalProcessor()


async def get_multimodal_processor() -> MultimodalProcessor:
    """获取多模态处理器实例"""
    return multimodal_processor