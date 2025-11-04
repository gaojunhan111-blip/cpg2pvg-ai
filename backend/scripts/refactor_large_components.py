#!/usr/bin/env python3
"""
Large Component Refactoring Tool
大型组件重构工具
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import ast

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ComponentRefactorer:
    """组件重构器"""

    def __init__(self):
        self.project_root = project_root
        self.refactored_files = []

    def analyze_large_components(self, file_path: str) -> Dict[str, any]:
        """分析大型组件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        analyzer = ComponentAnalyzer(file_path)
        analyzer.visit(tree)

        return analyzer.get_analysis()

    def refactor_hierarchical_parser(self):
        """重构层次医学解析器"""
        parser_file = self.project_root / "app/services/medical_parser.py"

        print("REFACTORING: HierarchicalMedicalParser")
        print("=" * 50)

        # 读取原始文件
        with open(parser_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 创建分解后的文件
        base_file = self.project_root / "app/services/parsers/base_parser.py"
        analyzer_file = self.project_root / "app/services/parsers/document_analyzer.py"
        extractor_file = self.project_root / "app/services/parsers/entity_extractor.py"
        chunker_file = self.project_root / "app/services/parsers/document_chunker.py"

        # 确保目录存在
        (self.project_root / "app/services/parsers").mkdir(exist_ok=True)

        # 创建基础解析器
        base_parser_content = self._create_base_parser_content()
        with open(base_file, 'w', encoding='utf-8') as f:
            f.write(base_parser_content)

        # 创建文档分析器
        document_analyzer_content = self._create_document_analyzer_content()
        with open(analyzer_file, 'w', encoding='utf-8') as f:
            f.write(document_analyzer_content)

        # 创建实体提取器
        entity_extractor_content = self._create_entity_extractor_content()
        with open(extractor_file, 'w', encoding='utf-8') as f:
            f.write(entity_extractor_content)

        # 创建文档分块器
        document_chunker_content = self._create_document_chunker_content()
        with open(chunker_file, 'w', encoding='utf-8') as f:
            f.write(document_chunker_content)

        # 重构主文件
        refactored_content = self._refactor_main_parser_file(content)
        with open(parser_file, 'w', encoding='utf-8') as f:
            f.write(refactored_content)

        self.refactored_files.extend([str(base_file), str(analyzer_file), str(extractor_file), str(chunker_file), str(parser_file)])

        print(f"  Created base parser: {base_file.relative_to(self.project_root)}")
        print(f"  Created document analyzer: {analyzer_file.relative_to(self.project_root)}")
        print(f"  Created entity extractor: {extractor_file.relative_to(self.project_root)}")
        print(f"  Created document chunker: {chunker_file.relative_to(self.project_root)}")
        print(f"  Refactored main parser: {parser_file.relative_to(self.project_root)}")

    def _create_base_parser_content(self) -> str:
        """创建基础解析器内容"""
        return '''"""
Base Parser Components
基础解析器组件
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DocumentMetadata:
    """文档元数据"""
    file_path: str = ""
    file_name: str = ""
    file_size: int = 0
    file_type: str = ""
    encoding: str = "utf-8"
    created_at: Optional[datetime] = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = field(default_factory=datetime.utcnow)


@dataclass
class ProcessingConfig:
    """处理配置"""
    max_chunk_size: int = 1000
    chunk_overlap: int = 100
    preserve_structure: bool = True
    extract_tables: bool = True
    extract_algorithms: bool = True
    confidence_threshold: float = 0.7


class BaseDocumentProcessor(ABC):
    """基础文档处理器"""

    def __init__(self, config: Optional[ProcessingConfig] = None):
        self.config = config or ProcessingConfig()
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    async def process(self, content: str, metadata: DocumentMetadata) -> Dict[str, Any]:
        """处理文档内容"""
        pass

    def validate_input(self, content: str) -> bool:
        """验证输入内容"""
        if not content or not content.strip():
            self.logger.warning("Empty content provided")
            return False
        return True

    def calculate_processing_metrics(self, start_time: datetime, end_time: datetime, content_length: int) -> Dict[str, float]:
        """计算处理指标"""
        processing_time = (end_time - start_time).total_seconds()
        chars_per_second = content_length / processing_time if processing_time > 0 else 0

        return {
            "processing_time_seconds": processing_time,
            "content_length": content_length,
            "chars_per_second": chars_per_second,
            "efficiency_score": min(1.0, chars_per_second / 1000)  # 1000 chars/sec as baseline
        }
'''

    def _create_document_analyzer_content(self) -> str:
        """创建文档分析器内容"""
        return '''"""
Document Analyzer
文档分析器
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from app.core.logger import get_logger
from .base_parser import BaseDocumentProcessor, DocumentMetadata, ProcessingConfig

logger = get_logger(__name__)


@dataclass
class DocumentSection:
    """文档段落"""
    section_id: str
    title: str
    content: str
    level: int
    start_line: int
    end_line: int
    section_type: str = "unknown"


class DocumentStructureAnalyzer:
    """文档结构分析器"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.section_patterns = self._initialize_section_patterns()

    def _initialize_section_patterns(self) -> Dict[str, re.Pattern]:
        """初始化段落模式"""
        return {
            "main_title": re.compile(r'^#{1,3}\s+(.+)$', re.MULTILINE),
            "section": re.compile(r'^#{4,6}\s+(.+)$', re.MULTILINE),
            "numbered": re.compile(r'^(\d+\.?\d*)\s+(.+)$', re.MULTILINE),
            "bullet": re.compile(r'^[-*•]\s+(.+)$', re.MULTILINE),
            "table": re.compile(r'^[\|].*?[\|]$', re.MULTILINE),
            "algorithm": re.compile(r'(?i)(algorithm|flowchart|workflow|steps?)', re.MULTILINE)
        }

    def analyze_structure(self, content: str) -> List[DocumentSection]:
        """分析文档结构"""
        sections = []
        lines = content.split('\\n')

        current_section = None
        line_number = 0

        for line in lines:
            line_number += 1
            stripped_line = line.strip()

            # 检查是否为标题
            if self._is_title_line(stripped_line):
                if current_section:
                    current_section.end_line = line_number - 1
                    sections.append(current_section)

                title, level = self._extract_title_and_level(stripped_line)
                current_section = DocumentSection(
                    section_id=f"section_{len(sections) + 1}",
                    title=title,
                    content="",
                    level=level,
                    start_line=line_number,
                    end_line=line_number,
                    section_type=self._classify_section(title, level)
                )
            elif current_section:
                # 添加内容到当前段落
                current_section.content += line + '\\n'

        # 处理最后一个段落
        if current_section:
            current_section.end_line = line_number
            sections.append(current_section)

        return sections

    def _is_title_line(self, line: str) -> bool:
        """检查是否为标题行"""
        return (
            line.startswith('#') or
            re.match(r'^\\d+\\.?\\d*\\s+', line) or
            re.match(r'^[A-Z][A-Z\\s]*:.*$', line)
        )

    def _extract_title_and_level(self, line: str) -> Tuple[str, int]:
        """提取标题和级别"""
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            title = line.lstrip('#').strip()
        elif re.match(r'^\\d+\\.?\\d*\\s+', line):
            level = 1
            title = re.sub(r'^\\d+\\.?\\d*\\s+', '', line)
        else:
            level = 1
            title = line

        return title, level

    def _classify_section(self, title: str, level: int) -> str:
        """分类段落类型"""
        title_lower = title.lower()

        if any(keyword in title_lower for keyword in ['overview', 'introduction', 'summary', 'background']):
            return 'overview'
        elif any(keyword in title_lower for keyword in ['diagnosis', 'clinical', 'presentation', 'symptoms']):
            return 'clinical'
        elif any(keyword in title_lower for keyword in ['treatment', 'therapy', 'management', 'medication']):
            return 'treatment'
        elif any(keyword in title_lower for keyword in ['prevention', 'screening', 'prophylaxis']):
            return 'prevention'
        elif any(keyword in title_lower for keyword in ['monitoring', 'follow-up', 'surveillance']):
            return 'monitoring'
        elif any(keyword in title_lower for keyword in ['algorithm', 'workflow', 'flowchart']):
            return 'algorithm'
        else:
            return 'general'

    def extract_key_sentences(self, content: str, max_sentences: int = 5) -> List[str]:
        """提取关键句子"""
        sentences = re.split(r'[.!?]+', content)

        # 过滤空句子和短句子
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        # 简单的关键性评分
        keyword_weights = {
            'diagnosis': 3, 'treatment': 3, 'prevention': 2, 'monitoring': 2,
            'recommend': 2, 'should': 2, 'important': 2, 'critical': 3,
            'patient': 1, 'clinical': 2, 'medical': 1
        }

        scored_sentences = []
        for sentence in sentences:
            score = 0
            sentence_lower = sentence.lower()
            for keyword, weight in keyword_weights.items():
                score += sentence_lower.count(keyword) * weight
            scored_sentences.append((sentence, score))

        # 按分数排序并返回前N个
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored_sentences[:max_sentences]]
'''

    def _create_entity_extractor_content(self) -> str:
        """创建实体提取器内容"""
        return '''"""
Entity Extractor
实体提取器
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from app.core.logger import get_logger
from .base_parser import ProcessingConfig

logger = get_logger(__name__)


class EntityType(str, Enum):
    """实体类型"""
    DISEASE = "disease"
    SYMPTOM = "symptom"
    MEDICATION = "medication"
    PROCEDURE = "procedure"
    LAB_TEST = "lab_test"
    ANATOMY = "anatomy"
    OTHER = "other"


@dataclass
class MedicalEntity:
    """医学实体"""
    text: str
    entity_type: EntityType
    start_pos: int
    end_pos: int
    confidence: float = 0.8
    canonical_form: str = ""
    attributes: Dict[str, any] = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}
        if not self.canonical_form:
            self.canonical_form = self.text.lower().strip()


class MedicalEntityExtractor:
    """医学实体提取器"""

    def __init__(self, config: Optional[ProcessingConfig] = None):
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.entity_patterns = self._initialize_entity_patterns()
        self.stopwords = self._initialize_stopwords()

    def _initialize_entity_patterns(self) -> Dict[EntityType, List[re.Pattern]]:
        """初始化实体模式"""
        return {
            EntityType.DISEASE: [
                re.compile(r'\\b(diabetes|hypertension|cancer|pneumonia|heart disease|stroke|asthma|arthritis|depression|anxiety)\\b', re.IGNORECASE),
                re.compile(r'\\b(\\w+\\s+disease|\\w+\\s+syndrome|\\w+\\s+disorder)\\b', re.IGNORECASE),
            ],
            EntityType.SYMPTOM: [
                re.compile(r'\\b(pain|fever|cough|fatigue|nausea|headache|dizziness|shortness of breath|chest pain)\\b', re.IGNORECASE),
                re.compile(r'\\b(swelling|bleeding|weakness|numbness|tingling|rash|itching|vomiting)\\b', re.IGNORECASE),
            ],
            EntityType.MEDICATION: [
                re.compile(r'\\b(metformin|insulin|lisinopril|aspirin|ibuprofen|acetaminophen|prednisone)\\b', re.IGNORECASE),
                re.compile(r'\\b(\\w+in|\\w+ol|\\w+ine|\\w+amide|\\w+azole)\\b', re.IGNORECASE),
            ],
            EntityType.LAB_TEST: [
                re.compile(r'\\b(blood sugar|glucose|hemoglobin|cholesterol|blood pressure|heart rate)\\b', re.IGNORECASE),
                re.compile(r'\\b(ECG|EKG|MRI|CT|X-ray|ultrasound|biopsy)\\b', re.IGNORECASE),
            ],
        }

    def _initialize_stopwords(self) -> Set[str]:
        """初始化停用词"""
        return {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'shall'
        }

    def extract_entities(self, text: str) -> List[MedicalEntity]:
        """提取医学实体"""
        entities = []

        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = pattern.finditer(text)
                for match in matches:
                    entity_text = match.group().strip()

                    # 过滤短实体和停用词
                    if len(entity_text) < 2 or entity_text.lower() in self.stopwords:
                        continue

                    # 计算置信度
                    confidence = self._calculate_confidence(entity_text, entity_type, match, text)

                    entity = MedicalEntity(
                        text=entity_text,
                        entity_type=entity_type,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=confidence,
                        attributes={
                            'pattern_matched': pattern.pattern,
                            'context': self._extract_context(text, match.start(), match.end())
                        }
                    )

                    entities.append(entity)

        # 去重和排序
        entities = self._deduplicate_entities(entities)
        entities.sort(key=lambda x: x.start_pos)

        return entities

    def _calculate_confidence(self, entity_text: str, entity_type: EntityType, match: re.Match, full_text: str) -> float:
        """计算置信度"""
        base_confidence = 0.7

        # 长度权重
        length_weight = min(len(entity_text) / 10, 1.0)

        # 上下文权重
        context = self._extract_context(full_text, match.start(), match.end())
        context_weight = self._analyze_context_relevance(context, entity_type)

        # 模式权重
        pattern_weight = 0.8  # 基础模式权重

        confidence = base_confidence + (length_weight * 0.1) + (context_weight * 0.1) + (pattern_weight * 0.1)
        return min(confidence, 1.0)

    def _extract_context(self, text: str, start: int, end: int, window: int = 20) -> str:
        """提取上下文"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()

    def _analyze_context_relevance(self, context: str, entity_type: EntityType) -> float:
        """分析上下文相关性"""
        context_lower = context.lower()

        relevance_keywords = {
            EntityType.DISEASE: ['patient', 'diagnosed', 'suffering', 'condition', 'case'],
            EntityType.SYMPTOM: ['experience', 'complain', 'report', 'present', 'sign'],
            EntityType.MEDICATION: ['prescribed', 'dose', 'treatment', 'therapy', 'medication'],
            EntityType.LAB_TEST: ['test', 'result', 'normal', 'abnormal', 'value', 'level'],
        }

        keywords = relevance_keywords.get(entity_type, [])
        relevance_score = sum(1 for keyword in keywords if keyword in context_lower)

        return min(relevance_score / 3.0, 1.0)  # 标准化到0-1

    def _deduplicate_entities(self, entities: List[MedicalEntity]) -> List[MedicalEntity]:
        """去重实体"""
        if not entities:
            return entities

        # 按位置排序
        entities.sort(key=lambda x: x.start_pos)

        deduplicated = []
        current_entity = entities[0]

        for entity in entities[1:]:
            # 检查是否重叠或相同
            if (entity.entity_type == current_entity.entity_type and
                abs(entity.start_pos - current_entity.start_pos) < len(entity.text)):
                # 保留置信度更高的实体
                if entity.confidence > current_entity.confidence:
                    current_entity = entity
            else:
                deduplicated.append(current_entity)
                current_entity = entity

        deduplicated.append(current_entity)
        return deduplicated

    def get_entity_statistics(self, entities: List[MedicalEntity]) -> Dict[str, int]:
        """获取实体统计信息"""
        stats = {}
        for entity_type in EntityType:
            stats[entity_type.value] = sum(1 for e in entities if e.entity_type == entity_type)

        stats['total'] = len(entities)
        stats['unique_texts'] = len(set(e.text.lower() for e in entities))

        return stats
'''

    def _create_document_chunker_content(self) -> str:
        """创建文档分块器内容"""
        return '''"""
Document Chunker
文档分块器
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from app.core.logger import get_logger
from .base_parser import ProcessingConfig

logger = get_logger(__name__)


@dataclass
class DocumentChunk:
    """文档块"""
    chunk_id: str
    content: str
    start_line: int
    end_line: int
    chunk_type: str = "text"
    metadata: Dict[str, any] = None
    entities: List[str] = None
    importance_score: float = 0.0

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.entities is None:
            self.entities = []


class IntelligentDocumentChunker:
    """智能文档分块器"""

    def __init__(self, config: Optional[ProcessingConfig] = None):
        self.config = config or ProcessingConfig()
        self.logger = get_logger(self.__class__.__name__)

    def create_chunks(self, content: str, entities: List = None) -> List[DocumentChunk]:
        """创建文档块"""
        if entities is None:
            entities = []

        # 首先尝试按结构分块
        structural_chunks = self._create_structural_chunks(content)

        # 如果结构分块不够，进行语义分块
        if not structural_chunks:
            semantic_chunks = self._create_semantic_chunks(content)
        else:
            semantic_chunks = []

        # 合并和优化分块
        all_chunks = structural_chunks + semantic_chunks
        optimized_chunks = self._optimize_chunks(all_chunks, entities)

        return optimized_chunks

    def _create_structural_chunks(self, content: str) -> List[DocumentChunk]:
        """创建结构化分块"""
        chunks = []
        lines = content.split('\\n')

        current_chunk = []
        current_start = 0
        line_number = 0

        for line in lines:
            line_number += 1
            stripped_line = line.strip()

            # 检查是否为新的段落标题
            if self._is_section_header(stripped_line) and current_chunk:
                # 保存当前块
                chunk_content = '\\n'.join(current_chunk)
                chunks.append(self._create_chunk_from_content(
                    chunk_content, current_start + 1, line_number - 1
                ))

                # 开始新块
                current_chunk = [line]
                current_start = line_number - 1
            else:
                current_chunk.append(line)

            # 检查块大小
            if len('\\n'.join(current_chunk)) > self.config.max_chunk_size:
                chunk_content = '\\n'.join(current_chunk)
                if len(chunk_content) > self.config.max_chunk_size:
                    # 分割大块
                    sub_chunks = self._split_large_chunk(chunk_content, current_start + 1)
                    chunks.extend(sub_chunks)
                    current_chunk = []
                    current_start = line_number

        # 处理最后一个块
        if current_chunk:
            chunk_content = '\\n'.join(current_chunk)
            chunks.append(self._create_chunk_from_content(
                chunk_content, current_start + 1, line_number
            ))

        return chunks

    def _create_semantic_chunks(self, content: str) -> List[DocumentChunk]:
        """创建语义分块"""
        chunks = []

        # 按段落分割
        paragraphs = content.split('\\n\\n')
        current_chunk_content = ""
        start_line = 1

        for i, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # 检查添加当前段落是否超过最大大小
            if (len(current_chunk_content) + len(paragraph) > self.config.max_chunk_size and
                current_chunk_content):
                # 创建块
                chunks.append(self._create_chunk_from_content(
                    current_chunk_content, start_line, start_line + current_chunk_content.count('\\n')
                ))
                current_chunk_content = paragraph
                start_line = start_line + current_chunk_content.count('\\n') + 2  # +2 for paragraph separators
            else:
                if current_chunk_content:
                    current_chunk_content += "\\n\\n" + paragraph
                else:
                    current_chunk_content = paragraph

        # 处理最后的内容
        if current_chunk_content:
            chunks.append(self._create_chunk_from_content(
                current_chunk_content, start_line, start_line + current_chunk_content.count('\\n')
            ))

        return chunks

    def _create_chunk_from_content(self, content: str, start_line: int, end_line: int) -> DocumentChunk:
        """从内容创建块"""
        chunk_id = f"chunk_{start_line}_{end_line}"
        chunk_type = self._classify_chunk_type(content)
        importance_score = self._calculate_importance_score(content)

        return DocumentChunk(
            chunk_id=chunk_id,
            content=content.strip(),
            start_line=start_line,
            end_line=end_line,
            chunk_type=chunk_type,
            importance_score=importance_score,
            metadata={
                "char_count": len(content),
                "word_count": len(content.split()),
                "line_count": content.count('\\n') + 1
            }
        )

    def _classify_chunk_type(self, content: str) -> str:
        """分类块类型"""
        content_lower = content.lower()

        if re.search(r'\\|.*\\|', content):
            return 'table'
        elif any(keyword in content_lower for keyword in ['algorithm', 'step', 'workflow', 'procedure']):
            return 'algorithm'
        elif any(keyword in content_lower for keyword in ['diagnosis', 'clinical', 'symptoms', 'presentation']):
            return 'clinical'
        elif any(keyword in content_lower for keyword in ['treatment', 'therapy', 'medication', 'management']):
            return 'treatment'
        elif any(keyword in content_lower for keyword in ['prevention', 'screening', 'prophylaxis']):
            return 'prevention'
        elif any(keyword in content_lower for keyword in ['monitoring', 'follow-up', 'surveillance']):
            return 'monitoring'
        else:
            return 'general'

    def _calculate_importance_score(self, content: str) -> float:
        """计算重要性评分"""
        score = 0.5  # 基础分数

        content_lower = content.lower()

        # 关键词权重
        importance_keywords = {
            'diagnosis': 0.2, 'treatment': 0.2, 'critical': 0.3, 'important': 0.2,
            'recommend': 0.15, 'should': 0.1, 'must': 0.2, 'emergency': 0.3,
            'contraindication': 0.25, 'warning': 0.2, 'adverse': 0.15
        }

        for keyword, weight in importance_keywords.items():
            score += content_lower.count(keyword) * weight

        # 长度权重（中等长度更重要）
        word_count = len(content.split())
        if 50 <= word_count <= 200:
            score += 0.2
        elif 200 < word_count <= 500:
            score += 0.1
        elif word_count > 500:
            score -= 0.1

        return min(max(score, 0.0), 1.0)

    def _is_section_header(self, line: str) -> bool:
        """检查是否为段落标题"""
        return (
            line.startswith('#') or
            re.match(r'^\\d+\\.?\\d*\\s+', line) or
            re.match(r'^[A-Z][A-Z\\s]*:.*$', line) or
            len(line) < 100 and re.search(r'\\b(overview|summary|introduction|conclusion)\\b', line, re.IGNORECASE)
        )

    def _split_large_chunk(self, content: str, start_line: int) -> List[DocumentChunk]:
        """分割大块"""
        sentences = re.split(r'[.!?]+', content)
        chunks = []
        current_content = ""
        current_start = start_line

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if (len(current_content) + len(sentence) > self.config.max_chunk_size and
                current_content):
                chunks.append(self._create_chunk_from_content(
                    current_content, current_start, current_start + current_content.count('\\n')
                ))
                current_start = current_start + current_content.count('\\n') + 1
                current_content = sentence + "."
            else:
                current_content += (sentence + "." if current_content else sentence + ".")

        # 处理剩余内容
        if current_content:
            chunks.append(self._create_chunk_from_content(
                current_content, current_start, start_line + content.count('\\n')
            ))

        return chunks

    def _optimize_chunks(self, chunks: List[DocumentChunk], entities: List) -> List[DocumentChunk]:
        """优化分块"""
        # 按重要性排序
        chunks.sort(key=lambda x: x.importance_score, reverse=True)

        # 为高重要性块添加实体标记
        entity_texts = [entity.text.lower() for entity in entities] if entities else []

        for chunk in chunks:
            chunk_content_lower = chunk.content.lower()
            chunk.entities = [
                entity_text for entity_text in entity_texts
                if entity_text in chunk_content_lower
            ]

        # 按行号重新排序
        chunks.sort(key=lambda x: x.start_line)

        return chunks
'''

    def _refactor_main_parser_file(self, original_content: str) -> str:
        """重构主解析器文件"""
        refactored_content = '''"""
Medical Document Parser - Refactored
医学文档解析器 - 重构版
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from app.core.logger import get_logger
from app.services.parsers.base_parser import (
    BaseDocumentProcessor, DocumentMetadata, ProcessingConfig
)
from app.services.parsers.document_analyzer import DocumentStructureAnalyzer
from app.services.parsers.entity_extractor import MedicalEntityExtractor
from app.services.parsers.document_chunker import IntelligentDocumentChunker

logger = get_logger(__name__)


class DocumentType(str, Enum):
    """文档类型"""
    CLINICAL_GUIDELINE = "clinical_guideline"
    RESEARCH_PAPER = "research_paper"
    TEXTBOOK = "textbook"
    PROTOCOL = "protocol"
    OTHER = "other"


@dataclass
class MedicalDocument:
    """医学文档"""
    document_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str = ""
    file_type: DocumentType = DocumentType.OTHER
    metadata: Optional[DocumentMetadata] = None
    structured_sections: List[Dict[str, Any]] = field(default_factory=list)
    extracted_tables: List[Dict[str, Any]] = field(default_factory=list)
    extracted_algorithms: List[Dict[str, Any]] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    document_chunks: List[Dict[str, Any]] = field(default_factory=list)
    processing_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)


class HierarchicalMedicalParser(BaseDocumentProcessor):
    """层次医学文档解析器 - 重构版"""

    def __init__(self, config: Optional[ProcessingConfig] = None):
        super().__init__(config)

        # 初始化组件
        self.structure_analyzer = DocumentStructureAnalyzer()
        self.entity_extractor = MedicalEntityExtractor(config)
        self.document_chunker = IntelligentDocumentChunker(config)

        self.logger.info("HierarchicalMedicalParser initialized with modular components")

    async def parse_medical_document(
        self,
        file_path: str,
        document_type: DocumentType = DocumentType.OTHER
    ) -> MedicalDocument:
        """解析医学文档"""
        start_time = datetime.utcnow()

        try:
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if not self.validate_input(content):
                raise ValueError("Invalid document content")

            # 创建文档元数据
            metadata = self._create_document_metadata(file_path, content)

            # 处理文档
            processed_content = await self.process(content, metadata)

            # 创建医学文档对象
            document = MedicalDocument(
                file_path=file_path,
                file_type=document_type,
                metadata=metadata,
                structured_sections=processed_content.get('sections', []),
                extracted_tables=processed_content.get('tables', []),
                extracted_algorithms=processed_content.get('algorithms', []),
                entities=processed_content.get('entities', []),
                document_chunks=processed_content.get('chunks', []),
                processing_time=(datetime.utcnow() - start_time).total_seconds()
            )

            self.logger.info(f"Document parsed successfully: {document.document_id}")
            return document

        except Exception as e:
            self.logger.error(f"Document parsing failed: {e}")
            raise

    async def process(self, content: str, metadata: DocumentMetadata) -> Dict[str, Any]:
        """处理文档内容"""
        # 分析文档结构
        sections = self.structure_analyzer.analyze_structure(content)

        # 提取医学实体
        entities = self.entity_extractor.extract_entities(content)

        # 创建文档分块
        chunks = self.document_chunker.create_chunks(content, entities)

        # 提取表格和算法（简化版）
        tables = self._extract_tables(content)
        algorithms = self._extract_algorithms(content)

        return {
            'sections': [self._section_to_dict(section) for section in sections],
            'entities': [self._entity_to_dict(entity) for entity in entities],
            'chunks': [self._chunk_to_dict(chunk) for chunk in chunks],
            'tables': tables,
            'algorithms': algorithms,
            'statistics': {
                'total_sections': len(sections),
                'total_entities': len(entities),
                'total_chunks': len(chunks),
                'entity_stats': self.entity_extractor.get_entity_statistics(entities)
            }
        }

    def _create_document_metadata(self, file_path: str, content: str) -> DocumentMetadata:
        """创建文档元数据"""
        from pathlib import Path

        file_path_obj = Path(file_path)

        return DocumentMetadata(
            file_path=str(file_path_obj.absolute()),
            file_name=file_path_obj.name,
            file_size=len(content.encode('utf-8')),
            file_type=file_path_obj.suffix.lower(),
            encoding='utf-8'
        )

    def _extract_tables(self, content: str) -> List[Dict[str, Any]]:
        """提取表格"""
        tables = []
        lines = content.split('\\n')

        current_table = []
        table_start = 0
        in_table = False

        for i, line in enumerate(lines):
            if '|' in line and line.strip().startswith('|') and line.strip().endswith('|'):
                if not in_table:
                    in_table = True
                    table_start = i + 1
                current_table.append(line)
            else:
                if in_table and current_table:
                    # 保存表格
                    tables.append({
                        'table_id': f"table_{len(tables) + 1}",
                        'content': '\\n'.join(current_table),
                        'start_line': table_start,
                        'end_line': i,
                        'row_count': len(current_table)
                    })
                    current_table = []
                    in_table = False

        # 处理最后一个表格
        if in_table and current_table:
            tables.append({
                'table_id': f"table_{len(tables) + 1}",
                'content': '\\n'.join(current_table),
                'start_line': table_start,
                'end_line': len(lines),
                'row_count': len(current_table)
            })

        return tables

    def _extract_algorithms(self, content: str) -> List[Dict[str, Any]]:
        """提取算法流程"""
        algorithms = []
        content_lower = content.lower()

        # 简单的算法检测
        algorithm_keywords = ['algorithm', 'workflow', 'flowchart', 'steps', 'procedure']

        for keyword in algorithm_keywords:
            if keyword in content_lower:
                algorithms.append({
                    'algorithm_id': f"algorithm_{len(algorithms) + 1}",
                    'type': keyword,
                    'description': f"Contains {keyword} content",
                    'confidence': 0.7
                })

        return algorithms

    def _section_to_dict(self, section) -> Dict[str, Any]:
        """段落转换为字典"""
        return {
            'section_id': section.section_id,
            'title': section.title,
            'content': section.content,
            'level': section.level,
            'section_type': section.section_type,
            'line_range': [section.start_line, section.end_line]
        }

    def _entity_to_dict(self, entity) -> Dict[str, Any]:
        """实体转换为字典"""
        return {
            'text': entity.text,
            'entity_type': entity.entity_type.value,
            'start_pos': entity.start_pos,
            'end_pos': entity.end_pos,
            'confidence': entity.confidence,
            'canonical_form': entity.canonical_form,
            'attributes': entity.attributes
        }

    def _chunk_to_dict(self, chunk) -> Dict[str, Any]:
        """块转换为字典"""
        return {
            'chunk_id': chunk.chunk_id,
            'content': chunk.content,
            'chunk_type': chunk.chunk_type,
            'start_line': chunk.start_line,
            'end_line': chunk.end_line,
            'importance_score': chunk.importance_score,
            'entities': chunk.entities,
            'metadata': chunk.metadata
        }

    def get_parser_statistics(self) -> Dict[str, Any]:
        """获取解析器统计信息"""
        return {
            'components_initialized': 4,
            'components': [
                'DocumentStructureAnalyzer',
                'MedicalEntityExtractor',
                'IntelligentDocumentChunker',
                'TableAndAlgorithmExtractor'
            ],
            'supported_entity_types': len(self.entity_extractor.entity_patterns),
            'config': {
                'max_chunk_size': self.config.max_chunk_size,
                'preserve_structure': self.config.preserve_structure,
                'extract_tables': self.config.extract_tables,
                'extract_algorithms': self.config.extract_algorithms
            }
        }
'''

        return refactored_content

    def run_refactoring(self):
        """运行重构"""
        print("LARGE COMPONENT REFACTORING")
        print("="*60)

        # 分析当前最大的组件
        medical_parser_file = self.project_root / "app/services/medical_parser.py"

        if medical_parser_file.exists():
            print(f"Analyzing: {medical_parser_file.relative_to(self.project_root)}")
            analysis = self.analyze_large_components(str(medical_parser_file))

            # 显示分析结果
            print(f"  Total lines: {analysis.get('total_lines', 0)}")
            print(f"  Classes: {len(analysis.get('classes', []))}")
            print(f"  Functions: {len(analysis.get('functions', []))}")

            # 显示大组件
            large_classes = analysis.get('large_classes', [])
            large_functions = analysis.get('large_functions', [])

            if large_classes:
                print(f"  Large classes: {len(large_classes)}")
                for cls in large_classes:
                    print(f"    - {cls['name']}: {cls['lines']} lines")

            if large_functions:
                print(f"  Large functions: {len(large_functions)}")
                for func in large_functions:
                    print(f"    - {func['name']}: {func['lines']} lines")

            # 执行重构
            if large_classes:
                print("\\nStarting refactoring...")
                self.refactor_hierarchical_parser()
                print(f"\\nRefactoring completed. Files refactored: {len(self.refactored_files)}")
            else:
                print("\\nNo large components found for refactoring.")
        else:
            print(f"File not found: {medical_parser_file}")


class ComponentAnalyzer(ast.NodeVisitor):
    """组件分析器"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.total_lines = 0
        self.classes = []
        self.functions = []
        self.large_classes = []
        self.large_functions = []

    def get_analysis(self) -> Dict[str, any]:
        return {
            'file_path': self.file_path,
            'total_lines': self.total_lines,
            'classes': self.classes,
            'functions': self.functions,
            'large_classes': self.large_classes,
            'large_functions': self.large_functions
        }

    def visit_ClassDef(self, node: ast.ClassDef):
        """分析类定义"""
        if hasattr(node, 'end_lineno') and node.end_lineno:
            lines = node.end_lineno - node.lineno + 1
            class_info = {
                'name': node.name,
                'line': node.lineno,
                'lines': lines,
                'methods': len([n for n in node.body if isinstance(n, ast.FunctionDef)])
            }
            self.classes.append(class_info)

            if lines > 200:  # 大于200行的类
                self.large_classes.append(class_info)

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """分析函数定义"""
        if hasattr(node, 'end_lineno') and node.end_lineno:
            lines = node.end_lineno - node.lineno + 1
            func_info = {
                'name': node.name,
                'line': node.lineno,
                'lines': lines
            }
            self.functions.append(func_info)

            if lines > 50:  # 大于50行的函数
                self.large_functions.append(func_info)

        self.generic_visit(node)


def main():
    """主函数"""
    try:
        refactorer = ComponentRefactorer()
        refactorer.run_refactoring()

    except KeyboardInterrupt:
        print("\\nRefactoring interrupted by user")
    except Exception as e:
        print(f"\\nRefactoring failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()