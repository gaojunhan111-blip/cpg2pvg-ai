"""
基于知识图谱的语义理解层
CPG2PVG-AI System MedicalKnowledgeGraph (Node 3)
"""

import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator, List, Tuple
from dataclasses import dataclass
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

logger = logging.getLogger(__name__)


@dataclass
class MedicalEntity:
    """医学实体"""
    name: str
    entity_type: str  # disease, symptom, treatment, drug, procedure
    synonyms: List[str]
    description: str
    confidence: float
    context: str


@dataclass
class MedicalRelation:
    """医学关系"""
    subject: str
    predicate: str  # treats, causes, symptom_of, contraindication, etc.
    object: str
    confidence: float
    evidence: str


@dataclass
class KnowledgeTriple:
    """知识三元组"""
    subject: str
    relation: str
    object: str
    confidence: float
    source_section: str


class MedicalKnowledgeGraph(BaseWorkflowNode):
    """医学知识图谱构建器 - 基于知识图谱的语义理解"""

    def __init__(self):
        super().__init__(
            name="MedicalKnowledgeGraph",
            description="构建医学知识图谱，实现深层语义理解和关系推理"
        )

        # 初始化LLM客户端
        self.llm_client = LLMClient()

        # 知识图谱存储
        self.entities: Dict[str, MedicalEntity] = {}
        self.relations: List[MedicalRelation] = []
        self.triples: List[KnowledgeTriple] = []

        # 医学术语词典（简化实现）
        self.medical_dict = self._initialize_medical_dict()

        # 关系类型映射
        self.relation_types = {
            "treats": "治疗",
            "causes": "导致",
            "symptom_of": "是...的症状",
            "diagnoses": "诊断",
            "prevents": "预防",
            "contraindicates": "禁忌",
            "interacts_with": "相互作用",
            "belongs_to_category": "属于类别",
            "has_severity": "严重程度",
            "requires_test": "需要检查"
        }

    async def execute(
        self,
        context: ProcessingContext,
        input_data: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[ProcessingResult, None]:
        """执行知识图谱构建"""

        try:
            # 解析输入数据
            processed_content = input_data.get("processed_content", {})

            text_sections = processed_content.get("text_sections", [])
            table_sections = processed_content.get("table_sections", [])
            algorithm_sections = processed_content.get("algorithm_sections", [])
            image_sections = processed_content.get("image_sections", [])

            if not any([text_sections, table_sections, algorithm_sections]):
                yield ProcessingResult(
                    step_name=self.name,
                    status=ProcessingStatus.FAILED,
                    success=False,
                    error_message="没有可用的处理内容进行知识图谱构建"
                )
                return

            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.RUNNING,
                success=True,
                message="开始构建医学知识图谱"
            )

            # 1. 实体识别和抽取
            yield ProcessingResult(
                step_name=f"{self.name}_entity_extraction",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="开始医学实体识别"
            )

            all_sections = text_sections + table_sections + algorithm_sections
            entities = await self._extract_medical_entities(all_sections, context)

            yield ProcessingResult(
                step_name=f"{self.name}_entity_extraction",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data={"entity_count": len(entities)},
                message=f"实体识别完成，共识别{len(entities)}个医学实体"
            )

            # 2. 关系抽取
            yield ProcessingResult(
                step_name=f"{self.name}_relation_extraction",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="开始医学关系抽取"
            )

            relations = await self._extract_medical_relations(all_sections, entities, context)

            yield ProcessingResult(
                step_name=f"{self.name}_relation_extraction",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data={"relation_count": len(relations)},
                message=f"关系抽取完成，共抽取{len(relations)}个医学关系"
            )

            # 3. 知识推理和增强
            yield ProcessingResult(
                step_name=f"{self.name}_knowledge_reasoning",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="开始知识推理和增强"
            )

            enhanced_knowledge = await self._perform_knowledge_reasoning(
                entities, relations, context
            )

            yield ProcessingResult(
                step_name=f"{self.name}_knowledge_reasoning",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data={"enhanced_triples": len(enhanced_knowledge)},
                message="知识推理和增强完成"
            )

            # 4. 构建知识图谱结构
            yield ProcessingResult(
                step_name=f"{self.name}_graph_construction",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="构建知识图谱结构"
            )

            knowledge_graph = await self._construct_knowledge_graph(enhanced_knowledge)

            yield ProcessingResult(
                step_name=f"{self.name}_graph_construction",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data={"graph_nodes": len(knowledge_graph["nodes"]), "graph_edges": len(knowledge_graph["edges"])},
                message="知识图谱构建完成"
            )

            # 生成最终结果
            final_result = {
                "knowledge_graph": knowledge_graph,
                "entities": [entity.__dict__ for entity in entities],
                "relations": [relation.__dict__ for relation in relations],
                "triples": [triple.__dict__ for triple in enhanced_knowledge],
                "processing_metadata": {
                    "total_entities": len(entities),
                    "total_relations": len(relations),
                    "total_triples": len(enhanced_knowledge),
                    "processing_time": datetime.utcnow().isoformat(),
                    "medical_specialties": context.medical_specialties,
                    "cost_level": context.cost_level.value
                }
            }

            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.COMPLETED,
                success=True,
                data=final_result,
                message=f"知识图谱构建完成，包含{len(entities)}个实体和{len(relations)}个关系"
            )

        except Exception as e:
            logger.error(f"知识图谱构建失败: {str(e)}")
            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.FAILED,
                success=False,
                error_message=str(e)
            )

    async def _extract_medical_entities(
        self, sections: List[Dict[str, Any]], context: ProcessingContext
    ) -> List[MedicalEntity]:
        """提取医学实体"""
        entities = []

        for section in sections:
            try:
                content = section.get("content", "") or section.get("enhanced_content", "")
                title = section.get("title", "")

                if not content:
                    continue

                # 使用LLM提取医学实体
                entity_prompt = self._build_entity_extraction_prompt(
                    title, content, context.medical_specialties
                )

                response = await self.llm_client.chat_completion(
                    messages=[{
                        "role": "user",
                        "content": entity_prompt
                    }],
                    max_tokens=1500,
                    temperature=0.1
                )

                # 解析实体提取结果
                section_entities = self._parse_entities_response(response, title, content)
                entities.extend(section_entities)

            except Exception as e:
                logger.error(f"提取段落实体失败: {str(e)}")
                continue

        # 去重和标准化
        entities = self._deduplicate_entities(entities)
        return entities

    async def _extract_medical_relations(
        self, sections: List[Dict[str, Any]], entities: List[MedicalEntity], context: ProcessingContext
    ) -> List[MedicalRelation]:
        """提取医学关系"""
        relations = []
        entity_names = {entity.name.lower() for entity in entities}

        for section in sections:
            try:
                content = section.get("content", "") or section.get("enhanced_content", "")
                title = section.get("title", "")

                if not content:
                    continue

                # 使用LLM提取医学关系
                relation_prompt = self._build_relation_extraction_prompt(
                    title, content, entities, context.medical_specialties
                )

                response = await self.llm_client.chat_completion(
                    messages=[{
                        "role": "user",
                        "content": relation_prompt
                    }],
                    max_tokens=2000,
                    temperature=0.1
                )

                # 解析关系提取结果
                section_relations = self._parse_relations_response(response, title, content)
                relations.extend(section_relations)

            except Exception as e:
                logger.error(f"提取段落关系失败: {str(e)}")
                continue

        return relations

    async def _perform_knowledge_reasoning(
        self, entities: List[MedicalEntity], relations: List[MedicalRelation], context: ProcessingContext
    ) -> List[KnowledgeTriple]:
        """执行知识推理和增强"""
        triples = []

        # 将现有关系转换为三元组
        for relation in relations:
            triple = KnowledgeTriple(
                subject=relation.subject,
                relation=relation.predicate,
                object=relation.object,
                confidence=relation.confidence,
                source_section="original_relation"
            )
            triples.append(triple)

        # 使用LLM进行推理增强
        try:
            reasoning_prompt = self._build_knowledge_reasoning_prompt(
                entities, relations, context.medical_specialties
            )

            response = await self.llm_client.chat_completion(
                messages=[{
                    "role": "user",
                    "content": reasoning_prompt
                }],
                max_tokens=2500,
                temperature=0.2
            )

            # 解析推理结果
            inferred_triples = self._parse_reasoning_response(response)
            triples.extend(inferred_triples)

        except Exception as e:
            logger.error(f"知识推理失败: {str(e)}")

        return triples

    async def _construct_knowledge_graph(
        self, triples: List[KnowledgeTriple]
    ) -> Dict[str, Any]:
        """构建知识图谱结构"""
        nodes = {}
        edges = []

        # 构建节点
        for triple in triples:
            # 添加主语节点
            if triple.subject not in nodes:
                nodes[triple.subject] = {
                    "id": triple.subject,
                    "label": triple.subject,
                    "type": self._infer_entity_type(triple.subject),
                    "properties": {}
                }

            # 添加宾语节点
            if triple.object not in nodes:
                nodes[triple.object] = {
                    "id": triple.object,
                    "label": triple.object,
                    "type": self._infer_entity_type(triple.object),
                    "properties": {}
                }

            # 添加边
            edge = {
                "source": triple.subject,
                "target": triple.object,
                "label": triple.relation,
                "weight": triple.confidence,
                "properties": {
                    "source_section": triple.source_section
                }
            }
            edges.append(edge)

        # 构建图结构
        graph = {
            "nodes": list(nodes.values()),
            "edges": edges,
            "metadata": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "construction_time": datetime.utcnow().isoformat()
            }
        }

        return graph

    def _build_entity_extraction_prompt(
        self, title: str, content: str, specialties: List[str]
    ) -> str:
        """构建实体提取提示词"""
        specialties_str = ", ".join(specialties) if specialties else "综合医学"

        return f"""
请从以下医学文档段落中提取重要的医学实体：

专业领域: {specialties_str}
标题: {title}
内容: {content[:1500]}

请提取以下类型的医学实体：
1. 疾病名称 (Disease)
2. 症状描述 (Symptom)
3. 治疗方法 (Treatment)
4. 药物名称 (Drug)
5. 检查项目 (Test)
6. 医学程序 (Procedure)

对于每个实体，请提供：
- 实体名称
- 实体类型
- 同义词或别名（如果有）
- 简要描述
- 置信度 (0-1)

请以JSON格式返回结果。
"""

    def _build_relation_extraction_prompt(
        self, title: str, content: str, entities: List[MedicalEntity], specialties: List[str]
    ) -> str:
        """构建关系提取提示词"""
        specialties_str = ", ".join(specialties) if specialties else "综合医学"
        entity_names = [entity.name for entity in entities]
        entities_str = ", ".join(entity_names[:20])  # 限制实体数量避免提示词过长

        return f"""
请从以下医学文档段落中提取医学实体之间的关系：

专业领域: {specialties_str}
标题: {title}
内容: {content[:1500]}

已知医学实体: {entities_str}

请识别以下类型的关系：
1. 治疗 (treats): A治疗B
2. 病因 (causes): A导致B
3. 症状 (symptom_of): A是B的症状
4. 诊断 (diagnoses): A用于诊断B
5. 预防 (prevents): A预防B
6. 禁忌 (contraindicates): A是B的禁忌
7. 相互作用 (interacts_with): A与B相互作用

对于每个关系，请提供：
- 主语实体
- 关系类型
- 宾语实体
- 置信度 (0-1)
- 支撑证据

请以JSON格式返回结果。
"""

    def _build_knowledge_reasoning_prompt(
        self, entities: List[MedicalEntity], relations: List[MedicalRelation], specialties: List[str]
    ) -> str:
        """构建知识推理提示词"""
        specialties_str = ", ".join(specialties) if specialties else "综合医学"

        # 提取实体和关系的摘要信息
        entity_summary = [(entity.name, entity.entity_type) for entity in entities[:10]]
        relation_summary = [(rel.subject, rel.predicate, rel.object) for rel in relations[:10]]

        return f"""
基于以下医学知识，请进行推理和知识增强：

专业领域: {specialties_str}

主要实体:
{entity_summary}

主要关系:
{relation_summary}

请进行以下推理：
1. 传递关系推理：如果A治疗B，B是C的症状，那么A可能缓解C
2. 禁忌推理：如果A治疗B，C与A有相互作用，那么使用A时需注意C
3. 关联推理：如果多个疾病有相同症状，可能涉及相似机制
4. 层级推理：如果A属于B类别，B属于C类别，那么A也属于C类别

请提供推理得出的新知识三元组，每个包含：
- 主语
- 关系
- 宾语
- 置信度
- 推理依据

请以JSON格式返回结果。
"""

    def _parse_entities_response(self, response: str, title: str, content: str) -> List[MedicalEntity]:
        """解析实体提取响应"""
        try:
            # 这里应该解析LLM返回的JSON响应
            # 简化实现，返回示例实体
            entities = [
                MedicalEntity(
                    name="示例疾病",
                    entity_type="disease",
                    synonyms=["疾病A", "病症A"],
                    description="从文档中提取的示例疾病",
                    confidence=0.8,
                    context=title
                )
            ]
            return entities
        except Exception as e:
            logger.error(f"解析实体响应失败: {str(e)}")
            return []

    def _parse_relations_response(self, response: str, title: str, content: str) -> List[MedicalRelation]:
        """解析关系提取响应"""
        try:
            # 这里应该解析LLM返回的JSON响应
            # 简化实现，返回示例关系
            relations = [
                MedicalRelation(
                    subject="示例药物",
                    predicate="treats",
                    object="示例疾病",
                    confidence=0.7,
                    evidence=f"在'{title}'中发现的治疗关系"
                )
            ]
            return relations
        except Exception as e:
            logger.error(f"解析关系响应失败: {str(e)}")
            return []

    def _parse_reasoning_response(self, response: str) -> List[KnowledgeTriple]:
        """解析推理响应"""
        try:
            # 这里应该解析LLM返回的JSON响应
            # 简化实现，返回示例三元组
            triples = [
                KnowledgeTriple(
                    subject="推理结果A",
                    relation="influences",
                    object="推理结果B",
                    confidence=0.6,
                    source_section="knowledge_reasoning"
                )
            ]
            return triples
        except Exception as e:
            logger.error(f"解析推理响应失败: {str(e)}")
            return []

    def _deduplicate_entities(self, entities: List[MedicalEntity]) -> List[MedicalEntity]:
        """实体去重"""
        seen = set()
        deduplicated = []

        for entity in entities:
            key = (entity.name.lower(), entity.entity_type)
            if key not in seen:
                seen.add(key)
                deduplicated.append(entity)

        return deduplicated

    def _infer_entity_type(self, entity_name: str) -> str:
        """推断实体类型"""
        entity_lower = entity_name.lower()

        # 简化的类型推断逻辑
        if any(keyword in entity_lower for keyword in ["病", "症", "炎", "癌", "综合征"]):
            return "disease"
        elif any(keyword in entity_lower for keyword in ["药", "剂", "素", "胶囊", "片"]):
            return "drug"
        elif any(keyword in entity_lower for keyword in ["治疗", "手术", "检查", "化验"]):
            return "procedure"
        else:
            return "unknown"

    def _initialize_medical_dict(self) -> Dict[str, List[str]]:
        """初始化医学词典"""
        return {
            "diseases": ["高血压", "糖尿病", "心脏病", "肺炎", "癌症"],
            "symptoms": ["发热", "咳嗽", "胸痛", "头痛", "恶心"],
            "treatments": ["手术治疗", "药物治疗", "物理治疗", "化学治疗"],
            "drugs": ["阿司匹林", "青霉素", "胰岛素", "布洛芬"]
        }

    def get_entity_by_name(self, name: str) -> Optional[MedicalEntity]:
        """根据名称获取实体"""
        return self.entities.get(name.lower())

    def get_relations_for_entity(self, entity_name: str) -> List[MedicalRelation]:
        """获取与实体相关的所有关系"""
        entity_lower = entity_name.lower()
        relations = []

        for relation in self.relations:
            if (relation.subject.lower() == entity_lower or
                relation.object.lower() == entity_lower):
                relations.append(relation)

        return relations

    def get_statistics(self) -> Dict[str, Any]:
        """获取知识图谱统计信息"""
        return {
            "total_entities": len(self.entities),
            "total_relations": len(self.relations),
            "total_triples": len(self.triples),
            "entity_types": self._count_entity_types(),
            "relation_types": self._count_relation_types()
        }

    def _count_entity_types(self) -> Dict[str, int]:
        """统计实体类型分布"""
        type_counts = {}
        for entity in self.entities.values():
            type_counts[entity.entity_type] = type_counts.get(entity.entity_type, 0) + 1
        return type_counts

    def _count_relation_types(self) -> Dict[str, int]:
        """统计关系类型分布"""
        type_counts = {}
        for relation in self.relations:
            type_counts[relation.predicate] = type_counts.get(relation.predicate, 0) + 1
        return type_counts