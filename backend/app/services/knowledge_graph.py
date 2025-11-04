"""
知识图谱构建服务
Knowledge Graph Construction Service
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Set, Tuple
import uuid

from app.core.logger import get_logger

logger = get_logger(__name__)


class EntityType(str, Enum):
    """实体类型"""
    DISEASE = "disease"
    SYMPTOM = "symptom"
    TREATMENT = "treatment"
    MEDICATION = "medication"
    TEST = "test"
    PROCEDURE = "procedure"


class RelationType(str, Enum):
    """关系类型"""
    CAUSES = "causes"
    TREATS = "treats"
    PREVENTS = "prevents"
    DIAGNOSES = "diagnoses"
    ASSOCIATED_WITH = "associated_with"
    CONTRAINDICATED = "contraindicated"


@dataclass
class Entity:
    """知识图谱实体"""
    id: str
    name: str
    entity_type: EntityType
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source: str = ""


@dataclass
class Relation:
    """知识图谱关系"""
    id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: RelationType
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source: str = ""


@dataclass
class KnowledgeGraph:
    """知识图谱"""
    graph_id: str
    entities: List[Entity] = field(default_factory=list)
    relations: List[Relation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


class KnowledgeGraphBuilder:
    """知识图谱构建器"""

    def __init__(self):
        self.logger = get_logger(__name__)

    async def build_graph_from_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> KnowledgeGraph:
        """从文档构建知识图谱"""
        graph_id = str(uuid.uuid4())

        self.logger.info(f"Building knowledge graph from {len(documents)} documents")

        try:
            # 1. 提取实体
            all_entities = []
            for doc in documents:
                entities = await self._extract_entities_from_document(doc)
                all_entities.extend(entities)

            # 2. 去重实体
            unique_entities = await self._deduplicate_entities(all_entities)

            # 3. 提取关系
            all_relations = []
            for doc in documents:
                relations = await self._extract_relations_from_document(doc, unique_entities)
                all_relations.extend(relations)

            # 4. 构建知识图谱
            knowledge_graph = KnowledgeGraph(
                graph_id=graph_id,
                entities=unique_entities,
                relations=all_relations,
                metadata={
                    "document_count": len(documents),
                    "entity_count": len(unique_entities),
                    "relation_count": len(all_relations)
                }
            )

            self.logger.info(f"Knowledge graph built: {len(unique_entities)} entities, {len(all_relations)} relations")
            return knowledge_graph

        except Exception as e:
            self.logger.error(f"Failed to build knowledge graph: {e}")
            raise

    async def _extract_entities_from_document(self, document: Dict[str, Any]) -> List[Entity]:
        """从文档中提取实体"""
        entities = []
        content = document.get("content", "")

        # 简化的实体提取模式
        entity_patterns = {
            EntityType.DISEASE: [
                r'\b(diabetes|hypertension|cancer|pneumonia|asthma)\b',
                r'\b(心脏病|糖尿病|高血压|癌症|肺炎)\b'
            ],
            EntityType.SYMPTOM: [
                r'\b(fever|cough|pain|headache|fatigue)\b',
                r'\b(发热|咳嗽|疼痛|头痛)\b'
            ],
            EntityType.TREATMENT: [
                r'\b(chemotherapy|surgery|radiation|therapy)\b',
                r'\b(化疗|手术|放疗|治疗)\b'
            ],
            EntityType.MEDICATION: [
                r'\b(metformin|insulin|aspirin|lisinopril)\b',
                r'\b(胰岛素|降压药|抗生素)\b'
            ]
        }

        import re
        for entity_type, patterns in entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    entity = Entity(
                        id=f"{entity_type.value}_{match.group().lower()}_{uuid.uuid4().hex[:8]}",
                        name=match.group(),
                        entity_type=entity_type,
                        properties={
                            "document_id": document.get("id", ""),
                            "position": match.start()
                        },
                        confidence=0.8,
                        source="document_extraction"
                    )
                    entities.append(entity)

        return entities

    async def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """去重实体"""
        unique_entities = []
        seen_names = set()

        for entity in entities:
            normalized_name = entity.name.lower().strip()
            if normalized_name not in seen_names:
                unique_entities.append(entity)
                seen_names.add(normalized_name)

        return unique_entities

    async def _extract_relations_from_document(
        self,
        document: Dict[str, Any],
        entities: List[Entity]
    ) -> List[Relation]:
        """从文档中提取关系"""
        relations = []
        content = document.get("content", "")

        # 简化的关系提取
        relation_patterns = {
            RelationType.TREATS: [
                r'(\w+)\s+(?:treats|treatment for|治疗)\s+(\w+)',
                r'(\w+)\s+治疗\s+(\w+)'
            ],
            RelationType.CAUSES: [
                r'(\w+)\s+(?:causes|leads to|导致)\s+(\w+)',
                r'(\w+)\s+导致\s+(\w+)'
            ],
            RelationType.ASSOCIATED_WITH: [
                r'(\w+)\s+(?:associated with|related to|相关)\s+(\w+)',
                r'(\w+)\s+相关\s+(\w+)'
            ]
        }

        # 创建实体名称映射
        entity_name_map = {entity.name.lower(): entity.id for entity in entities}

        import re
        for relation_type, patterns in relation_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    source_name = match.group(1).lower()
                    target_name = match.group(2).lower()

                    if source_name in entity_name_map and target_name in entity_name_map:
                        relation = Relation(
                            id=f"{relation_type.value}_{uuid.uuid4().hex[:8]}",
                            source_entity_id=entity_name_map[source_name],
                            target_entity_id=entity_name_map[target_name],
                            relation_type=relation_type,
                            properties={
                                "document_id": document.get("id", ""),
                                "confidence": 0.7
                            },
                            confidence=0.7,
                            source="document_extraction"
                        )
                        relations.append(relation)

        return relations

    async def enrich_graph(self, graph: KnowledgeGraph) -> KnowledgeGraph:
        """丰富知识图谱"""
        self.logger.info(f"Enriching knowledge graph {graph.graph_id}")

        try:
            # 1. 计算实体重要性
            await self._calculate_entity_importance(graph)

            # 2. 推断新关系
            inferred_relations = await self._infer_relations(graph)
            graph.relations.extend(inferred_relations)

            # 3. 更新元数据
            graph.metadata.update({
                "enrichment_applied": True,
                "inferred_relations": len(inferred_relations)
            })

            self.logger.info(f"Graph enriched: {len(inferred_relations)} new relations")
            return graph

        except Exception as e:
            self.logger.error(f"Failed to enrich graph: {e}")
            raise

    async def _calculate_entity_importance(self, graph: KnowledgeGraph) -> None:
        """计算实体重要性"""
        # 简单的重要性计算：基于连接数
        entity_connections = {}

        for relation in graph.relations:
            source_id = relation.source_entity_id
            target_id = relation.target_entity_id

            entity_connections[source_id] = entity_connections.get(source_id, 0) + 1
            entity_connections[target_id] = entity_connections.get(target_id, 0) + 1

        # 更新实体重要性
        for entity in graph.entities:
            importance = entity_connections.get(entity.id, 0)
            entity.properties["importance"] = importance
            entity.properties["centrality"] = importance / max(1, len(graph.relations))

    async def _infer_relations(self, graph: KnowledgeGraph) -> List[Relation]:
        """推断新关系"""
        inferred_relations = []

        # 简单的关系推断：传递性
        # 如果 A treats B，且 B causes C，则 A treats C
        relations_by_source = {}
        relations_by_target = {}

        for relation in graph.relations:
            if relation.source_entity_id not in relations_by_source:
                relations_by_source[relation.source_entity_id] = []
            relations_by_source[relation.source_entity_id].append(relation)

            if relation.target_entity_id not in relations_by_target:
                relations_by_target[relation.target_entity_id] = []
            relations_by_target[relation.target_entity_id].append(relation)

        # 推断传递性关系
        for entity in graph.entities:
            if entity.id in relations_by_source and entity.id in relations_by_target:
                # 查找 entity -> B (treats) 和 C -> entity (causes)
                outgoing_treats = [r for r in relations_by_source[entity.id]
                                  if r.relation_type == RelationType.TREATS]
                incoming_causes = [r for r in relations_by_target[entity.id]
                                 if r.relation_type == RelationType.CAUSES]

                for treats_rel in outgoing_treats:
                    for causes_rel in incoming_causes:
                        # 创建推断关系：causes_rel.source -> treats_rel.target (treats)
                        inferred_relation = Relation(
                            id=f"inferred_{uuid.uuid4().hex[:8]}",
                            source_entity_id=causes_rel.source_entity_id,
                            target_entity_id=treats_rel.target_entity_id,
                            relation_type=RelationType.TREATS,
                            properties={
                                "inferred": True,
                                "confidence": 0.5,
                                "reasoning": "transitive_inference"
                            },
                            confidence=0.5,
                            source="inference"
                        )
                        inferred_relations.append(inferred_relation)

        return inferred_relations

    async def query_graph(
        self,
        graph: KnowledgeGraph,
        query_type: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """查询知识图谱"""
        results = []

        if query_type == "find_entities_by_type":
            entity_type = kwargs.get("entity_type")
            results = [
                {
                    "id": entity.id,
                    "name": entity.name,
                    "type": entity.entity_type,
                    "properties": entity.properties
                }
                for entity in graph.entities
                if entity.entity_type == entity_type
            ]

        elif query_type == "find_relations":
            entity_id = kwargs.get("entity_id")
            results = [
                {
                    "id": relation.id,
                    "source": relation.source_entity_id,
                    "target": relation.target_entity_id,
                    "type": relation.relation_type,
                    "confidence": relation.confidence
                }
                for relation in graph.relations
                if relation.source_entity_id == entity_id or relation.target_entity_id == entity_id
            ]

        elif query_type == "find_path":
            source_id = kwargs.get("source_id")
            target_id = kwargs.get("target_id")
            path = await self._find_path(graph, source_id, target_id)
            results = [{"path": path}]

        return results

    async def _find_path(
        self,
        graph: KnowledgeGraph,
        source_id: str,
        target_id: str,
        max_depth: int = 5
    ) -> Optional[List[str]]:
        """查找两个实体间的路径"""
        if source_id == target_id:
            return [source_id]

        # 构建邻接表
        adjacency = {}
        for entity in graph.entities:
            adjacency[entity.id] = []

        for relation in graph.relations:
            adjacency[relation.source_entity_id].append(relation.target_entity_id)
            adjacency[relation.target_entity_id].append(relation.source_entity_id)

        # BFS搜索
        from collections import deque
        queue = deque([(source_id, [source_id])])
        visited = {source_id}

        while queue and len(queue[0][1]) < max_depth:
            current, path = queue.popleft()

            for neighbor in adjacency.get(current, []):
                if neighbor == target_id:
                    return path + [neighbor]

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def get_graph_stats(self, graph: KnowledgeGraph) -> Dict[str, Any]:
        """获取图谱统计信息"""
        return {
            "entity_count": len(graph.entities),
            "relation_count": len(graph.relations),
            "entity_types": list(set(e.entity_type for e in graph.entities)),
            "relation_types": list(set(r.relation_type for r in graph.relations)),
            "metadata": graph.metadata
        }


# 全局实例
knowledge_graph_builder = KnowledgeGraphBuilder()


async def get_knowledge_graph_builder() -> KnowledgeGraphBuilder:
    """获取知识图谱构建器实例"""
    return knowledge_graph_builder