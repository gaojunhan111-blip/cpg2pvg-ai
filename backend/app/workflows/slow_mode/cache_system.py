"""
智能缓存和记忆系统
CPG2PVG-AI System MedicalContentCache (Node 6)
"""

import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator, List, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
import pickle
from collections import defaultdict

from app.workflows.base import BaseWorkflowNode
from app.workflows.types import (
    ProcessingContext,
    ProcessingResult,
    ProcessingStatus,
)
from app.core.redis_client import RedisClient

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """缓存级别"""
    MEMORY = "memory"      # 内存缓存
    REDIS = "redis"        # Redis缓存
    DATABASE = "database"  # 数据库缓存
    HYBRID = "hybrid"      # 混合缓存


class CacheStrategy(Enum):
    """缓存策略"""
    LRU = "lru"                    # 最近最少使用
    LFU = "lfu"                    # 最少使用频率
    TTL_BASED = "ttl_based"        # 基于TTL
    ADAPTIVE = "adaptive"           # 自适应策略


class MemoryType(Enum):
    """记忆类型"""
    EPISODIC = "episodic"         # 情节记忆（具体的处理实例）
    SEMANTIC = "semantic"         # 语义记忆（医学知识）
    PROCEDURAL = "procedural"     # 程序记忆（处理流程）
    WORKING = "working"           # 工作记忆（临时状态）


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl: Optional[int] = None
    size_bytes: int = 0
    cache_level: CacheLevel = CacheLevel.MEMORY
    tags: List[str] = field(default_factory=list)


@dataclass
class MemoryItem:
    """记忆项"""
    memory_id: str
    memory_type: MemoryType
    content: Any
    context: Dict[str, Any]
    importance: float  # 重要性评分 (0-1)
    access_frequency: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    related_memories: List[str] = field(default_factory=list)


@dataclass
class CacheStats:
    """缓存统计"""
    total_entries: int = 0
    memory_entries: int = 0
    redis_entries: int = 0
    hit_count: int = 0
    miss_count: int = 0
    eviction_count: int = 0
    memory_usage_bytes: int = 0
    hit_rate: float = 0.0


class MemoryCache:
    """内存缓存实现"""

    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order = []  # 用于LRU
        self.access_frequency = defaultdict(int)  # 用于LFU
        self.current_memory_usage = 0
        self.stats = CacheStats()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        entry = self.cache.get(key)
        if entry is None:
            self.stats.miss_count += 1
            return None

        # 更新访问信息
        entry.last_accessed = datetime.utcnow()
        entry.access_count += 1
        self.access_frequency[key] += 1

        # 更新LRU顺序
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)

        self.stats.hit_count += 1
        self._update_hit_rate()

        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None, tags: List[str] = None) -> bool:
        """设置缓存值"""
        try:
            # 序列化值以计算大小
            serialized_value = pickle.dumps(value)
            size_bytes = len(serialized_value)

            # 检查是否需要清理空间
            if self._needs_eviction(size_bytes):
                self._evict_entries(size_bytes)

            # 创建缓存条目
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow(),
                ttl=ttl,
                size_bytes=size_bytes,
                tags=tags or []
            )

            # 更新缓存
            self.cache[key] = entry
            self.current_memory_usage += size_bytes
            self.stats.total_entries += 1
            self.stats.memory_entries += 1
            self.stats.memory_usage_bytes = self.current_memory_usage

            # 更新访问顺序
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)

            return True

        except Exception as e:
            logger.error(f"设置缓存失败: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存条目"""
        entry = self.cache.pop(key, None)
        if entry:
            self.current_memory_usage -= entry.size_bytes
            self.stats.total_entries -= 1
            self.stats.memory_entries -= 1
            self.stats.memory_usage_bytes = self.current_memory_usage

            if key in self.access_order:
                self.access_order.remove(key)
            if key in self.access_frequency:
                del self.access_frequency[key]

            return True
        return False

    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_order.clear()
        self.access_frequency.clear()
        self.current_memory_usage = 0
        self.stats = CacheStats()

    def _needs_eviction(self, new_entry_size: int) -> bool:
        """检查是否需要清理"""
        return (
            len(self.cache) >= self.max_size or
            self.current_memory_usage + new_entry_size > self.max_memory_bytes
        )

    def _evict_entries(self, needed_space: int):
        """清理缓存条目"""
        freed_space = 0
        evicted_count = 0

        # 使用LRU策略清理
        for key in list(self.access_order):
            if freed_space >= needed_space:
                break

            entry = self.cache.get(key)
            if entry:
                freed_space += entry.size_bytes
                evicted_count += 1
                self.delete(key)

        self.stats.eviction_count += evicted_count

    def _update_hit_rate(self):
        """更新命中率"""
        total_requests = self.stats.hit_count + self.stats.miss_count
        if total_requests > 0:
            self.stats.hit_rate = self.stats.hit_count / total_requests


class MedicalMemorySystem:
    """医学记忆系统"""

    def __init__(self, redis_client: RedisClient):
        self.redis_client = redis_client
        self.episodic_memory: Dict[str, MemoryItem] = {}
        self.semantic_memory: Dict[str, MemoryItem] = {}
        self.procedural_memory: Dict[str, MemoryItem] = {}
        self.working_memory: Dict[str, MemoryItem] = {}
        self.memory_connections: Dict[str, List[str]] = defaultdict(list)

    async def store_memory(
        self, memory_type: MemoryType, content: Any, context: Dict[str, Any],
        importance: float = 0.5
    ) -> str:
        """存储记忆"""
        memory_id = self._generate_memory_id(content, context)

        memory_item = MemoryItem(
            memory_id=memory_id,
            memory_type=memory_type,
            content=content,
            context=context,
            importance=importance
        )

        # 存储到相应的记忆区域
        if memory_type == MemoryType.EPISODIC:
            self.episodic_memory[memory_id] = memory_item
        elif memory_type == MemoryType.SEMANTIC:
            self.semantic_memory[memory_id] = memory_item
        elif memory_type == MemoryType.PROCEDURAL:
            self.procedural_memory[memory_id] = memory_item
        elif memory_type == MemoryType.WORKING:
            self.working_memory[memory_id] = memory_item

        # 查找相关记忆并建立连接
        related_memories = await self._find_related_memories(memory_item)
        memory_item.related_memories = related_memories
        for related_id in related_memories:
            self.memory_connections[memory_id].append(related_id)
            self.memory_connections[related_id].append(memory_id)

        # 对于长期记忆，同时存储到Redis
        if memory_type in [MemoryType.SEMANTIC, MemoryType.PROCEDURAL]:
            await self._store_to_redis(memory_item)

        return memory_id

    async def retrieve_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """检索记忆"""
        # 首先在本地查找
        memory_item = None
        memory_item = self.episodic_memory.get(memory_id)
        if not memory_item:
            memory_item = self.semantic_memory.get(memory_id)
        if not memory_item:
            memory_item = self.procedural_memory.get(memory_id)
        if not memory_item:
            memory_item = self.working_memory.get(memory_id)

        if memory_item:
            memory_item.access_frequency += 1
            memory_item.last_accessed = datetime.utcnow()
            return memory_item

        # 如果本地没有，从Redis查找
        memory_item = await self._retrieve_from_redis(memory_id)
        if memory_item:
            memory_item.access_frequency += 1
            memory_item.last_accessed = datetime.utcnow()
            # 重新存储到本地缓存
            if memory_item.memory_type == MemoryType.SEMANTIC:
                self.semantic_memory[memory_id] = memory_item
            elif memory_item.memory_type == MemoryType.PROCEDURAL:
                self.procedural_memory[memory_id] = memory_item

        return memory_item

    async def search_memories(self, query: str, memory_type: Optional[MemoryType] = None) -> List[MemoryItem]:
        """搜索记忆"""
        all_memories = []

        # 收集相关记忆
        if memory_type is None or memory_type == MemoryType.EPISODIC:
            all_memories.extend(self.episodic_memory.values())
        if memory_type is None or memory_type == MemoryType.SEMANTIC:
            all_memories.extend(self.semantic_memory.values())
        if memory_type is None or memory_type == MemoryType.PROCEDURAL:
            all_memories.extend(self.procedural_memory.values())
        if memory_type is None or memory_type == MemoryType.WORKING:
            all_memories.extend(self.working_memory.values())

        # 简化的搜索实现
        matching_memories = []
        query_lower = query.lower()

        for memory in all_memories:
            # 检查内容和上下文是否匹配查询
            content_str = str(memory.content).lower()
            context_str = str(memory.context).lower()

            if query_lower in content_str or query_lower in context_str:
                matching_memories.append(memory)

        # 按重要性和访问频率排序
        matching_memories.sort(
            key=lambda m: (m.importance, m.access_frequency),
            reverse=True
        )

        return matching_memories[:10]  # 返回前10个最相关的记忆

    def _generate_memory_id(self, content: Any, context: Dict[str, Any]) -> str:
        """生成记忆ID"""
        content_str = str(content) + str(context)
        return hashlib.md5(content_str.encode()).hexdigest()

    async def _find_related_memories(self, memory_item: MemoryItem) -> List[str]:
        """查找相关记忆"""
        # 简化的相关记忆查找
        related_ids = []
        content_str = str(memory_item.content).lower()

        # 在语义记忆中查找相似内容
        for existing_id, existing_memory in self.semantic_memory.items():
            if existing_id != memory_item.memory_id:
                existing_content = str(existing_memory.content).lower()
                # 简单的相似性检查
                common_words = set(content_str.split()) & set(existing_content.split())
                if len(common_words) > 2:  # 有超过2个共同词
                    related_ids.append(existing_id)

        return related_ids[:3]  # 最多返回3个相关记忆

    async def _store_to_redis(self, memory_item: MemoryItem):
        """存储记忆到Redis"""
        try:
            key = f"medical_memory:{memory_item.memory_type.value}:{memory_item.memory_id}"
            value = {
                "memory_id": memory_item.memory_id,
                "memory_type": memory_item.memory_type.value,
                "content": memory_item.content,
                "context": memory_item.context,
                "importance": memory_item.importance,
                "created_at": memory_item.created_at.isoformat(),
                "related_memories": memory_item.related_memories
            }

            # 设置TTL为30天
            await self.redis_client.set(key, value, ttl=30 * 24 * 3600)

        except Exception as e:
            logger.error(f"存储记忆到Redis失败: {str(e)}")

    async def _retrieve_from_redis(self, memory_id: str) -> Optional[MemoryItem]:
        """从Redis检索记忆"""
        try:
            # 在所有记忆类型中查找
            for memory_type in MemoryType:
                key = f"medical_memory:{memory_type.value}:{memory_id}"
                value = await self.redis_client.get(key)
                if value:
                    return MemoryItem(
                        memory_id=value["memory_id"],
                        memory_type=MemoryType(value["memory_type"]),
                        content=value["content"],
                        context=value["context"],
                        importance=value["importance"],
                        related_memories=value.get("related_memories", []),
                        created_at=datetime.fromisoformat(value["created_at"])
                    )
            return None

        except Exception as e:
            logger.error(f"从Redis检索记忆失败: {str(e)}")
            return None


class MedicalContentCache(BaseWorkflowNode):
    """智能缓存和记忆系统"""

    def __init__(self):
        super().__init__(
            name="MedicalContentCache",
            description="智能缓存和记忆系统，优化处理效率和知识积累"
        )

        # 初始化缓存组件
        self.memory_cache = MemoryCache(max_size=1000, max_memory_mb=50)
        self.redis_client = RedisClient()
        self.memory_system = MedicalMemorySystem(self.redis_client)

        # 缓存配置
        self.default_ttl = 3600  # 1小时
        self.long_term_ttl = 30 * 24 * 3600  # 30天

    async def execute(
        self,
        context: ProcessingContext,
        input_data: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[ProcessingResult, None]:
        """执行缓存和记忆系统处理"""

        try:
            # 解析输入数据
            pvg_content = input_data.get("pvg_content", {})
            content_sections = input_data.get("content_sections", [])
            knowledge_graph = input_data.get("knowledge_graph", {})

            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.RUNNING,
                success=True,
                message="启动智能缓存和记忆系统"
            )

            # 1. 检查相关缓存
            yield ProcessingResult(
                step_name=f"{self.name}_cache_lookup",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="检查相关缓存"
            )

            cache_results = await self._check_relevant_caches(context)

            yield ProcessingResult(
                step_name=f"{self.name}_cache_lookup",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data=cache_results,
                message=f"缓存检查完成，找到{len(cache_results)}个相关缓存"
            )

            # 2. 存储新的处理结果
            yield ProcessingResult(
                step_name=f"{self.name}_result_storage",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="存储新的处理结果"
            )

            storage_results = await self._store_processing_results(
                pvg_content, content_sections, knowledge_graph, context
            )

            yield ProcessingResult(
                step_name=f"{self.name}_result_storage",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data=storage_results,
                message="处理结果存储完成"
            )

            # 3. 构建和存储记忆
            yield ProcessingResult(
                step_name=f"{self.name}_memory_construction",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="构建和存储医学记忆"
            )

            memory_results = await self._construct_memories(
                pvg_content, content_sections, knowledge_graph, context
            )

            yield ProcessingResult(
                step_name=f"{self.name}_memory_construction",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data={"memory_count": len(memory_results)},
                message=f"医学记忆构建完成，共存储{len(memory_results)}个记忆项"
            )

            # 4. 优化缓存策略
            yield ProcessingResult(
                step_name=f"{self.name}_cache_optimization",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="优化缓存策略"
            )

            optimization_results = await self._optimize_cache_strategy(context)

            yield ProcessingResult(
                step_name=f"{self.name}_cache_optimization",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data=optimization_results,
                message="缓存策略优化完成"
            )

            # 生成最终结果
            final_result = {
                "cache_hit_results": cache_results,
                "storage_results": storage_results,
                "memory_results": [memory.__dict__ for memory in memory_results],
                "cache_statistics": self._get_cache_statistics(),
                "memory_statistics": self._get_memory_statistics(),
                "optimization_results": optimization_results,
                "processing_metadata": {
                    "processing_time": datetime.utcnow().isoformat(),
                    "cache_hit_rate": self.memory_cache.stats.hit_rate,
                    "total_memories": len(memory_results),
                    "cost_level": context.cost_level.value
                }
            }

            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.COMPLETED,
                success=True,
                data=final_result,
                message=f"智能缓存和记忆系统处理完成"
            )

        except Exception as e:
            logger.error(f"缓存和记忆系统处理失败: {str(e)}")
            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.FAILED,
                success=False,
                error_message=str(e)
            )

    async def _check_relevant_caches(self, context: ProcessingContext) -> Dict[str, Any]:
        """检查相关缓存"""
        cache_results = {
            "found_caches": [],
            "cache_hits": 0,
            "cache_misses": 0
        }

        try:
            # 生成缓存键
            cache_keys = self._generate_cache_keys(context)

            for key_info in cache_keys:
                cache_key = key_info["key"]
                cache_type = key_info["type"]

                # 检查内存缓存
                cached_value = self.memory_cache.get(cache_key)
                if cached_value:
                    cache_results["found_caches"].append({
                        "key": cache_key,
                        "type": cache_type,
                        "source": "memory",
                        "data": cached_value
                    })
                    cache_results["cache_hits"] += 1
                    continue

                # 检查Redis缓存
                redis_key = f"pvg_cache:{cache_key}"
                redis_value = await self.redis_client.get(redis_key)
                if redis_value:
                    cache_results["found_caches"].append({
                        "key": cache_key,
                        "type": cache_type,
                        "source": "redis",
                        "data": redis_value
                    })
                    cache_results["cache_hits"] += 1

                    # 同时存储到内存缓存
                    self.memory_cache.set(cache_key, redis_value, ttl=self.default_ttl)
                else:
                    cache_results["cache_misses"] += 1

        except Exception as e:
            logger.error(f"检查缓存失败: {str(e)}")

        return cache_results

    async def _store_processing_results(
        self, pvg_content: Dict[str, Any], content_sections: List[Dict[str, Any]],
        knowledge_graph: Dict[str, Any], context: ProcessingContext
    ) -> Dict[str, Any]:
        """存储处理结果"""
        storage_results = {
            "stored_items": [],
            "storage_locations": []
        }

        try:
            # 存储PVG内容
            if pvg_content:
                pvg_key = f"pvg_content:{context.guideline_id}"
                self.memory_cache.set(pvg_key, pvg_content, ttl=self.long_term_ttl)
                await self.redis_client.set(pvg_key, pvg_content, ttl=self.long_term_ttl)
                storage_results["stored_items"].append({"key": pvg_key, "type": "pvg_content"})
                storage_results["storage_locations"].append("memory", "redis")

            # 存储内容段落
            if content_sections:
                sections_key = f"content_sections:{context.guideline_id}"
                self.memory_cache.set(sections_key, content_sections, ttl=self.default_ttl)
                await self.redis_client.set(sections_key, content_sections, ttl=self.default_ttl)
                storage_results["stored_items"].append({"key": sections_key, "type": "content_sections"})

            # 存储知识图谱
            if knowledge_graph:
                graph_key = f"knowledge_graph:{context.guideline_id}"
                self.memory_cache.set(graph_key, knowledge_graph, ttl=self.default_ttl)
                await self.redis_client.set(graph_key, knowledge_graph, ttl=self.default_ttl)
                storage_results["stored_items"].append({"key": graph_key, "type": "knowledge_graph"})

        except Exception as e:
            logger.error(f"存储处理结果失败: {str(e)}")

        return storage_results

    async def _construct_memories(
        self, pvg_content: Dict[str, Any], content_sections: List[Dict[str, Any]],
        knowledge_graph: Dict[str, Any], context: ProcessingContext
    ) -> List[MemoryItem]:
        """构建记忆"""
        memories = []

        try:
            # 构建情节记忆（具体的处理实例）
            episodic_content = {
                "guideline_id": context.guideline_id,
                "processing_timestamp": datetime.utcnow().isoformat(),
                "pvg_summary": self._extract_pvg_summary(pvg_content),
                "specialties": context.medical_specialties,
                "cost_level": context.cost_level.value
            }

            episodic_memory_id = await self.memory_system.store_memory(
                MemoryType.EPISODIC,
                episodic_content,
                {"context": context.__dict__},
                importance=0.7
            )
            episodic_memory = await self.memory_system.retrieve_memory(episodic_memory_id)
            if episodic_memory:
                memories.append(episodic_memory)

            # 构建语义记忆（医学知识）
            if knowledge_graph.get("entities"):
                semantic_content = {
                    "entities": knowledge_graph["entities"][:10],  # 限制数量
                    "medical_concepts": self._extract_medical_concepts(knowledge_graph),
                    "specialties": context.medical_specialties
                }

                semantic_memory_id = await self.memory_system.store_memory(
                    MemoryType.SEMANTIC,
                    semantic_content,
                    {"source": "knowledge_graph", "guideline_id": context.guideline_id},
                    importance=0.9
                )
                semantic_memory = await self.memory_system.retrieve_memory(semantic_memory_id)
                if semantic_memory:
                    memories.append(semantic_memory)

            # 构建程序记忆（处理流程）
            procedural_content = {
                "workflow_steps": ["document_parser", "multimodal_processor", "knowledge_graph"],
                "processing_time": "estimated_processing_time",
                "quality_metrics": self._extract_quality_metrics(pvg_content),
                "cost_analysis": self._extract_cost_analysis(pvg_content)
            }

            procedural_memory_id = await self.memory_system.store_memory(
                MemoryType.PROCEDURAL,
                procedural_content,
                {"workflow": "slow_mode", "context": context.__dict__},
                importance=0.6
            )
            procedural_memory = await self.memory_system.retrieve_memory(procedural_memory_id)
            if procedural_memory:
                memories.append(procedural_memory)

        except Exception as e:
            logger.error(f"构建记忆失败: {str(e)}")

        return memories

    async def _optimize_cache_strategy(self, context: ProcessingContext) -> Dict[str, Any]:
        """优化缓存策略"""
        optimization_results = {
            "current_hit_rate": self.memory_cache.stats.hit_rate,
            "memory_usage": self.memory_cache.current_memory_usage,
            "optimizations_applied": []
        }

        try:
            # 根据命中率调整策略
            if self.memory_cache.stats.hit_rate < 0.3:
                # 命中率低，增加缓存大小
                if self.memory_cache.max_size < 2000:
                    self.memory_cache.max_size = int(self.memory_cache.max_size * 1.2)
                    optimization_results["optimizations_applied"].append("increased_cache_size")

            # 根据内存使用情况清理
            if self.memory_cache.current_memory_usage > self.memory_cache.max_memory_bytes * 0.8:
                self.memory_cache._evict_entries(int(self.memory_cache.max_memory_bytes * 0.2))
                optimization_results["optimizations_applied"].append("memory_cleanup")

            # 更新统计信息
            optimization_results["updated_hit_rate"] = self.memory_cache.stats.hit_rate
            optimization_results["updated_memory_usage"] = self.memory_cache.current_memory_usage

        except Exception as e:
            logger.error(f"优化缓存策略失败: {str(e)}")

        return optimization_results

    def _generate_cache_keys(self, context: ProcessingContext) -> List[Dict[str, Any]]:
        """生成缓存键"""
        keys = []

        # 基于指南ID的键
        keys.append({
            "key": f"guideline:{context.guideline_id}",
            "type": "guideline_data"
        })

        # 基于专业领域的键
        specialties_str = "_".join(sorted(context.medical_specialties))
        keys.append({
            "key": f"specialties:{specialties_str}",
            "type": "specialty_data"
        })

        # 基于质量级别的键
        keys.append({
            "key": f"quality:{context.quality_requirement.value}",
            "type": "quality_template"
        })

        return keys

    def _extract_pvg_summary(self, pvg_content: Dict[str, Any]) -> str:
        """提取PVG摘要"""
        if not pvg_content or not pvg_content.get("sections"):
            return "无可用内容"

        # 简化的摘要提取
        summary = f"包含{len(pvg_content.get('sections', []))}个内容段落"
        if "quick_summary" in pvg_content:
            summary = pvg_content["quick_summary"][:100]

        return summary

    def _extract_medical_concepts(self, knowledge_graph: Dict[str, Any]) -> List[str]:
        """提取医学概念"""
        concepts = []

        # 从实体中提取概念
        entities = knowledge_graph.get("entities", [])
        for entity in entities[:5]:  # 限制数量
            if isinstance(entity, dict) and "name" in entity:
                concepts.append(entity["name"])

        return concepts

    def _extract_quality_metrics(self, pvg_content: Dict[str, Any]) -> Dict[str, Any]:
        """提取质量指标"""
        return {
            "content_sections": len(pvg_content.get("sections", [])),
            "estimated_quality": "high" if len(pvg_content.get("sections", [])) > 5 else "medium",
            "completeness_score": 0.85  # 简化实现
        }

    def _extract_cost_analysis(self, pvg_content: Dict[str, Any]) -> Dict[str, Any]:
        """提取成本分析"""
        return {
            "estimated_cost": 0.50,
            "cost_efficiency": "good",
            "processing_complexity": "medium"
        }

    def _get_cache_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "memory_cache": {
                "total_entries": self.memory_cache.stats.total_entries,
                "hit_count": self.memory_cache.stats.hit_count,
                "miss_count": self.memory_cache.stats.miss_count,
                "hit_rate": self.memory_cache.stats.hit_rate,
                "memory_usage_bytes": self.memory_cache.stats.memory_usage_bytes,
                "eviction_count": self.memory_cache.stats.eviction_count
            }
        }

    def _get_memory_statistics(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        return {
            "episodic_memories": len(self.memory_system.episodic_memory),
            "semantic_memories": len(self.memory_system.semantic_memory),
            "procedural_memories": len(self.memory_system.procedural_memory),
            "working_memories": len(self.memory_system.working_memory),
            "total_memory_connections": len(self.memory_system.memory_connections)
        }

    async def get_cached_content(self, key: str) -> Optional[Any]:
        """获取缓存内容的便捷方法"""
        # 先检查内存缓存
        cached_value = self.memory_cache.get(key)
        if cached_value:
            return cached_value

        # 检查Redis缓存
        redis_key = f"pvg_cache:{key}"
        redis_value = await self.redis_client.get(redis_key)
        if redis_value:
            # 存储到内存缓存
            self.memory_cache.set(key, redis_value, ttl=self.default_ttl)
            return redis_value

        return None

    async def set_cached_content(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存内容的便捷方法"""
        actual_ttl = ttl or self.default_ttl

        # 存储到内存缓存
        memory_result = self.memory_cache.set(key, value, ttl=actual_ttl)

        # 存储到Redis
        redis_key = f"pvg_cache:{key}"
        redis_result = await self.redis_client.set(redis_key, value, ttl=actual_ttl)

        return memory_result or redis_result