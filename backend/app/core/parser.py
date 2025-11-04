"""
医学指南解析器
Medical Guideline Parser
"""

import re
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib

from app.core.logger import get_logger
from app.core.error_handling import CPG2PVGException, retry, DEFAULT_RETRY_CONFIG

logger = get_logger(__name__)


class DocumentType(str, Enum):
    """文档类型"""
    CLINICAL_GUIDELINE = "clinical_guideline"
    PROTOCOL = "protocol"
    CONSENSUS = "consensus"
    REVIEW = "review"
    OTHER = "other"


class SectionType(str, Enum):
    """章节类型"""
    INTRODUCTION = "introduction"
    METHODS = "methods"
    RECOMMENDATIONS = "recommendations"
    EVIDENCE = "evidence"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"
    REFERENCES = "references"
    APPENDIX = "appendix"


@dataclass
class ParsedSection:
    """解析的章节"""
    id: str
    title: str
    content: str
    section_type: SectionType
    level: int  # 层级深度
    start_pos: int
    end_pos: int
    metadata: Dict[str, Any]


@dataclass
class ParsedDocument:
    """解析的文档"""
    id: str
    title: str
    content: str
    document_type: DocumentType
    sections: List[ParsedSection]
    metadata: Dict[str, Any]
    hash: str


class DocumentParser:
    """文档解析器基类"""

    def __init__(self):
        self.content = ""
        self.metadata = {}

    async def parse(self, content: str) -> ParsedDocument:
        """解析文档"""
        raise NotImplementedError("Subclasses must implement parse method")

    def _generate_hash(self, content: str) -> str:
        """生成内容哈希"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()


class MarkdownParser(DocumentParser):
    """Markdown文档解析器"""

    def __init__(self):
        super().__init__()
        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self.code_block_pattern = re.compile(r'```[\s\S]*?```')
        self.link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        self.table_pattern = re.compile(r'\|(.+)\|')

    async def parse(self, content: str) -> ParsedDocument:
        """解析Markdown文档"""
        logger.info("开始解析Markdown文档", extra_data={"content_length": len(content)})

        self.content = content
        doc_hash = self._generate_hash(content)

        # 提取标题
        title = self._extract_title(content)

        # 识别文档类型
        doc_type = self._identify_document_type(content)

        # 解析章节
        sections = self._parse_sections(content)

        # 提取元数据
        metadata = self._extract_metadata(content)

        document = ParsedDocument(
            id=f"doc_{doc_hash[:16]}",
            title=title,
            content=content,
            document_type=doc_type,
            sections=sections,
            metadata=metadata,
            hash=doc_hash
        )

        logger.info("Markdown文档解析完成", extra_data={
            "title": title,
            "sections_count": len(sections),
            "document_type": doc_type.value
        })

        return document

    def _extract_title(self, content: str) -> str:
        """提取文档标题"""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()

        # 如果没有找到一级标题，使用第一行作为标题
        return lines[0][:100] if lines else "Untitled Document"

    def _identify_document_type(self, content: str) -> DocumentType:
        """识别文档类型"""
        content_lower = content.lower()

        keywords_map = {
            DocumentType.CLINICAL_GUIDELINE: [
                'clinical guideline', 'practice guideline', 'treatment guideline',
                '诊断指南', '治疗指南', '临床指南'
            ],
            DocumentType.PROTOCOL: [
                'protocol', 'standard operating procedure', 'sop',
                '操作规程', '标准流程', '协议'
            ],
            DocumentType.CONSENSUS: [
                'consensus', 'expert opinion', 'recommendation',
                '专家共识', '意见一致', '推荐意见'
            ],
            DocumentType.REVIEW: [
                'review', 'systematic review', 'meta-analysis',
                '综述', '系统评价', '荟萃分析'
            ]
        }

        for doc_type, keywords in keywords_map.items():
            if any(keyword in content_lower for keyword in keywords):
                return doc_type

        return DocumentType.OTHER

    def _parse_sections(self, content: str) -> List[ParsedSection]:
        """解析章节结构"""
        sections = []
        lines = content.split('\n')
        current_section = None
        position = 0

        for line_num, line in enumerate(lines):
            position += len(line) + 1  # +1 for newline

            heading_match = self.heading_pattern.match(line)
            if heading_match:
                # 保存前一个章节
                if current_section:
                    current_section.end_pos = position - len(line) - 1
                    sections.append(current_section)

                # 开始新章节
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                section_type = self._classify_section(title, level)

                current_section = ParsedSection(
                    id=f"section_{len(sections) + 1}",
                    title=title,
                    content="",  # 将在后续填充
                    section_type=section_type,
                    level=level,
                    start_pos=position - len(line) - 1,
                    end_pos=position,
                    metadata={}
                )
            elif current_section and current_section.content == "":
                # 章节的第一行非标题内容
                current_section.content = line.strip()

        # 保存最后一个章节
        if current_section:
            current_section.end_pos = position
            sections.append(current_section)

        # 如果没有找到章节，创建一个默认章节
        if not sections:
            sections.append(ParsedSection(
                id="section_1",
                title="Full Document",
                content=content[:200] + "..." if len(content) > 200 else content,
                section_type=SectionType.INTRODUCTION,
                level=1,
                start_pos=0,
                end_pos=len(content),
                metadata={}
            ))

        return sections

    def _classify_section(self, title: str, level: int) -> SectionType:
        """分类章节类型"""
        title_lower = title.lower()

        section_keywords = {
            SectionType.INTRODUCTION: [
                'introduction', 'background', 'overview', '摘要', '介绍', '背景'
            ],
            SectionType.METHODS: [
                'methods', 'methodology', 'approach', '方法', '方法学'
            ],
            SectionType.RECOMMENDATIONS: [
                'recommendations', 'guidelines', 'suggestions', '建议', '指南', '推荐'
            ],
            SectionType.EVIDENCE: [
                'evidence', 'results', 'findings', '证据', '结果', '发现'
            ],
            SectionType.DISCUSSION: [
                'discussion', 'analysis', 'interpretation', '讨论', '分析', '解读'
            ],
            SectionType.CONCLUSION: [
                'conclusion', 'summary', 'conclusions', '结论', '总结'
            ],
            SectionType.REFERENCES: [
                'references', 'bibliography', 'citations', '参考文献', '引用'
            ],
            SectionType.APPENDIX: [
                'appendix', 'supplementary', 'appendices', '附录', '补充'
            ]
        }

        for section_type, keywords in section_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                return section_type

        # 根据层级推断
        if level <= 2:
            return SectionType.INTRODUCTION
        elif level == 3:
            return SectionType.METHODS
        else:
            return SectionType.EVIDENCE

    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """提取文档元数据"""
        metadata = {
            "word_count": len(content.split()),
            "char_count": len(content),
            "line_count": len(content.split('\n')),
            "has_code_blocks": bool(self.code_block_pattern.search(content)),
            "has_links": bool(self.link_pattern.search(content)),
            "has_tables": bool(self.table_pattern.search(content)),
        }

        # 提取关键词（简单实现）
        words = re.findall(r'\b\w+\b', content.lower())
        word_freq = {}
        for word in words:
            if len(word) > 3:  # 只统计长度大于3的词
                word_freq[word] = word_freq.get(word, 0) + 1

        # 取前10个高频词作为关键词
        metadata["keywords"] = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        return metadata


class TextParser(DocumentParser):
    """纯文本文档解析器"""

    async def parse(self, content: str) -> ParsedDocument:
        """解析纯文本文档"""
        logger.info("开始解析纯文本文档", extra_data={"content_length": len(content)})

        self.content = content
        doc_hash = self._generate_hash(content)

        # 简单的结构分析
        lines = content.split('\n')
        title = lines[0][:100] if lines else "Untitled Document"

        # 按段落分割
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        sections = []
        for i, paragraph in enumerate(paragraphs[:10]):  # 最多取前10个段落
            section = ParsedSection(
                id=f"section_{i + 1}",
                title=f"Paragraph {i + 1}",
                content=paragraph[:200] + "..." if len(paragraph) > 200 else paragraph,
                section_type=SectionType.INTRODUCTION,
                level=1,
                start_pos=content.find(paragraph),
                end_pos=content.find(paragraph) + len(paragraph),
                metadata={"paragraph_index": i}
            )
            sections.append(section)

        metadata = {
            "paragraph_count": len(paragraphs),
            "word_count": len(content.split()),
            "char_count": len(content)
        }

        document = ParsedDocument(
            id=f"doc_{doc_hash[:16]}",
            title=title,
            content=content,
            document_type=DocumentType.OTHER,
            sections=sections,
            metadata=metadata,
            hash=doc_hash
        )

        logger.info("纯文本文档解析完成", extra_data={
            "title": title,
            "sections_count": len(sections)
        })

        return document


class GuidelineParser:
    """医学指南解析器管理类"""

    def __init__(self):
        self.parsers = {
            'md': MarkdownParser(),
            'markdown': MarkdownParser(),
            'txt': TextParser(),
            'text': TextParser()
        }

    @retry(config=DEFAULT_RETRY_CONFIG)
    async def parse_document(self, content: str, file_type: str = 'auto') -> ParsedDocument:
        """
        解析文档

        Args:
            content: 文档内容
            file_type: 文件类型 ('auto', 'md', 'txt' 等)

        Returns:
            ParsedDocument: 解析后的文档对象
        """
        try:
            # 自动检测文件类型
            if file_type == 'auto':
                file_type = self._detect_file_type(content)

            # 选择合适的解析器
            parser = self.parsers.get(file_type.lower())
            if not parser:
                logger.warning(f"不支持的文件类型: {file_type}, 使用默认解析器")
                parser = TextParser()

            # 执行解析
            document = await parser.parse(content)

            # 验证解析结果
            self._validate_document(document)

            logger.info("文档解析成功", extra_data={
                "document_id": document.id,
                "title": document.title,
                "sections_count": len(document.sections)
            })

            return document

        except Exception as e:
            logger.error("文档解析失败", extra_data={
                "file_type": file_type,
                "error": str(e),
                "content_length": len(content)
            })
            raise CPG2PVGException(
                message=f"文档解析失败: {str(e)}",
                category="business_logic",
                severity="medium",
                details={"file_type": file_type, "error": str(e)}
            )

    def _detect_file_type(self, content: str) -> str:
        """自动检测文件类型"""
        # 检测Markdown特征
        markdown_indicators = [
            r'^#{1,6}\s+',  # 标题
            r'\*\*.*?\*\*',  # 粗体
            r'\*.*?\*',  # 斜体
            r'\[.*?\]\(.*?\)',  # 链接
            r'^\|.*\|',  # 表格
            r'^\s*[-*+]\s+',  # 列表
        ]

        for pattern in markdown_indicators:
            if re.search(pattern, content, re.MULTILINE):
                return 'md'

        return 'txt'

    def _validate_document(self, document: ParsedDocument) -> None:
        """验证解析结果"""
        if not document.title:
            raise ValueError("文档标题不能为空")

        if not document.sections:
            raise ValueError("文档必须包含至少一个章节")

        if len(document.content) == 0:
            raise ValueError("文档内容不能为空")

        # 验证章节内容
        empty_sections = [s for s in document.sections if not s.content.strip()]
        if empty_sections:
            logger.warning(f"发现 {len(empty_sections)} 个空章节")

    async def extract_key_information(self, document: ParsedDocument) -> Dict[str, Any]:
        """提取关键信息"""
        key_info = {
            "document_id": document.id,
            "title": document.title,
            "type": document.document_type.value,
            "sections_summary": [],
            "recommendations": [],
            "evidence_level": {},
            "keywords": []
        }

        # 章节摘要
        for section in document.sections:
            section_summary = {
                "title": section.title,
                "type": section.section_type.value,
                "level": section.level,
                "content_preview": section.content[:100] + "..." if len(section.content) > 100 else section.content
            }
            key_info["sections_summary"].append(section_summary)

        # 提取推荐意见（从推荐章节）
        recommendation_sections = [s for s in document.sections if s.section_type == SectionType.RECOMMENDATIONS]
        for section in recommendation_sections:
            # 简单的推荐意见提取（可以用更复杂的NLP方法）
            recommendations = re.findall(r'[0-9]+\.\s*([^.\n]+)', section.content)
            key_info["recommendations"].extend(recommendations[:5])  # 最多取5个

        # 关键词
        if "keywords" in document.metadata:
            key_info["keywords"] = [word for word, freq in document.metadata["keywords"]]

        return key_info


# 全局解析器实例
guideline_parser = GuidelineParser()