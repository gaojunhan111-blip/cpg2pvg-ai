"""
智能医学内容缓存系统
Medical Content Cache and Memory System
节点6：智能缓存和记忆系统
"""

import json
import hashlib
import asyncio
import functools
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import redis.asyncio as redis

from app.core.logger import get_logger
from app.core.config import get_settings
from app.schemas.medical_schemas import ProcessedContent, MedicalPattern

logger = get_logger(__name__)


class CacheStrategy(str, Enum):
    """缓存策略"""
    LRU = "lru"           # 最近最少使用
    LFU = "lfu"           # 最少使用频率
    TTL = "ttl"           # 生存时间
    ADAPTIVE = "adaptive"  # 自适应


class ContentType(str, Enum):
    """内容类型"""
    MEDICAL_GUIDELINE = "medical_guideline"
    TREATMENT_PROTOCOL = "treatment_protocol"
    DIAGNOSIS_CRITERIA = "diagnosis_criteria"
    DRUG_INFORMATION = "drug_information"
    RESEARCH_SUMMARY = "research_summary"
    CLINICAL_ALGORITHM = "clinical_algorithm"


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    content_hash: str
    content_type: ContentType
    processed_content: ProcessedContent
    medical_patterns: List[MedicalPattern] = field(default_factory=list)

    # 缓存元数据
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    # 质量评分
    quality_score: float = 0.0
    relevance_score: float = 0.0
    complexity_score: float = 0.0


@dataclass
class SimilarContentResult:
    """相似内容结果"""
    content: ProcessedContent
    similarity_score: float
    shared_patterns: List[MedicalPattern]
    relevance_hints: List[str]


class MedicalContentCache:
    """智能医学内容缓存系统"""

    def __init__(self, redis_url: Optional[str] = None) -> None:
        self.logger = get_logger(__name__)
        self.settings = get_settings()

        # Redis配置
        self.redis_url = redis_url or self.settings.REDIS_URL
        self.redis_client: Optional[redis.Redis] = None

        # 缓存配置
        self.default_ttl = 3600 * 24  # 24小时
        self.max_entries = 10000
        self.similarity_threshold = 0.7

        # 添加内存缓存层
        self.memory_cache: Dict[str, Any] = {}
        self.memory_cache_ttl: Dict[str, datetime] = {}
        self.memory_cache_max_size = 1000
        self.memory_cache_ttl_seconds = 300  # 5分钟

        # 缓存统计
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_patterns": 0,
            "cache_efficiency": 0.0,
            "memory_hits": 0,
            "redis_hits": 0
        }

    async def _get_redis_client(self) -> redis.Redis:
        """获取Redis客户端"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        return self.redis_client

    async def get_cached_processing_fast(
        self,
        content_hash: str,
        content_type: ContentType
    ) -> Optional[ProcessedContent]:
        """快速获取缓存（先内存后Redis）"""
        cache_key = f"medical_cache:{content_type.value}:{content_hash}"

        # 1. 检查内存缓存
        if cache_key in self.memory_cache:
            if self._is_memory_cache_valid(cache_key):
                self.cache_stats["hits"] += 1
                self.cache_stats["memory_hits"] += 1
                return self.memory_cache[cache_key]
            else:
                # 过期，从内存缓存中删除
                del self.memory_cache[cache_key]
                del self.memory_cache_ttl[cache_key]

        # 2. 检查Redis缓存
        result = await self.get_cached_processing(content_hash, content_type)

        # 3. 如果Redis命中，更新内存缓存
        if result:
            await self._update_memory_cache(cache_key, result)
            self.cache_stats["redis_hits"] += 1

        return result

    def _is_memory_cache_valid(self, cache_key: str) -> bool:
        """检查内存缓存是否有效"""
        if cache_key not in self.memory_cache_ttl:
            return False

        expiry_time = self.memory_cache_ttl[cache_key]
        return datetime.utcnow() < expiry_time

    async def _update_memory_cache(self, cache_key: str, content: ProcessedContent) -> None:
        """更新内存缓存"""
        # 如果缓存已满，删除最旧的条目
        if len(self.memory_cache) >= self.memory_cache_max_size:
            oldest_key = min(self.memory_cache_ttl.keys(),
                           key=lambda k: self.memory_cache_ttl[k])
            del self.memory_cache[oldest_key]
            del self.memory_cache_ttl[oldest_key]

        # 添加新内容
        self.memory_cache[cache_key] = content
        self.memory_cache_ttl[cache_key] = (
            datetime.utcnow() + timedelta(seconds=self.memory_cache_ttl_seconds)
        )

    async def get_cached_processing(
        self,
        content_hash: str,
        content_type: ContentType
    ) -> Optional[ProcessedContent]:
        """获取缓存的处理结果"""
        try:
            client = await self._get_redis_client()

            # 构建缓存键
            cache_key = f"medical_cache:{content_type.value}:{content_hash}"

            # 尝试从Redis获取
            cached_data = await client.get(cache_key)
            if cached_data:
                # 反序列化数据
                cache_entry = json.loads(cached_data)

                # 更新访问统计
                await self._update_access_stats(cache_key)

                self.cache_stats["hits"] += 1
                self.logger.info(f"Cache hit for content hash: {content_hash}")

                return ProcessedContent(**cache_entry["processed_content"])

            self.cache_stats["misses"] += 1
            self.logger.info(f"Cache miss for content hash: {content_hash}")
            return None

        except Exception as e:
            self.logger.error(f"Failed to get cached processing: {e}")
            self.cache_stats["misses"] += 1
            return None

    async def cache_medical_patterns(
        self,
        patterns: List[MedicalPattern],
        content_type: ContentType
    ) -> None:
        """缓存医学模式"""
        try:
            client = await self._get_redis_client()

            for pattern in patterns:
                # 构建模式缓存键
                pattern_key = f"medical_pattern:{content_type.value}:{pattern.pattern_id}"

                # 序列化模式数据
                pattern_data = {
                    "pattern": asdict(pattern),
                    "content_type": content_type.value,
                    "cached_at": datetime.utcnow().isoformat(),
                    "usage_count": 0
                }

                # 设置缓存，30天过期
                await client.setex(
                    pattern_key,
                    3600 * 24 * 30,  # 30天
                    json.dumps(pattern_data)
                )

                self.cache_stats["total_patterns"] += 1

            self.logger.info(f"Cached {len(patterns)} medical patterns")

        except Exception as e:
            self.logger.error(f"Failed to cache medical patterns: {e}")

    async def cache_processing_result(
        self,
        content_hash: str,
        content_type: ContentType,
        processed_content: ProcessedContent,
        medical_patterns: Optional[List[MedicalPattern]] = None,
        ttl: Optional[int] = None
    ) -> None:
        """缓存处理结果"""
        try:
            client = await self._get_redis_client()

            # 构建缓存键
            cache_key = f"medical_cache:{content_type.value}:{content_hash}"

            # 计算质量评分
            quality_score = await self._calculate_content_quality(processed_content)

            # 构建缓存条目
            cache_entry = CacheEntry(
                key=cache_key,
                content_hash=content_hash,
                content_type=content_type,
                processed_content=processed_content,
                medical_patterns=medical_patterns or [],
                quality_score=quality_score,
                expires_at=datetime.utcnow() + timedelta(seconds=ttl or self.default_ttl)
            )

            # 序列化并存储
            serialized_entry = json.dumps(asdict(cache_entry), default=str)

            if ttl:
                await client.setex(cache_key, ttl, serialized_entry)
            else:
                await client.set(cache_key, serialized_entry)

            # 更新缓存统计
            await self._update_cache_size()

            self.logger.info(f"Cached processing result for hash: {content_hash}")

        except Exception as e:
            self.logger.error(f"Failed to cache processing result: {e}")

    async def _find_similar_cached_content(
        self,
        content_hash: str,
        content_type: ContentType
    ) -> Optional[SimilarContentResult]:
        """查找相似的缓存内容"""
        try:
            client = await self._get_redis_client()

            # 获取所有相同类型的缓存内容
            pattern = f"medical_cache:{content_type.value}:*"
            keys = await client.keys(pattern)

            best_match = None
            best_score = 0.0

            for key in keys[:100]:  # 限制检查数量以避免性能问题
                try:
                    cached_data = await client.get(key)
                    if cached_data:
                        cache_entry = json.loads(cached_data)

                        # 计算相似度
                        similarity = await self._calculate_similarity(
                            content_hash,
                            cache_entry["content_hash"]
                        )

                        if similarity > best_score and similarity > self.similarity_threshold:
                            best_score = similarity
                            best_match = cache_entry

                except Exception as e:
                    self.logger.warning(f"Error checking key {key}: {e}")
                    continue

            if best_match:
                # 构建相似内容结果
                processed_content = ProcessedContent(**best_match["processed_content"])
                patterns = [MedicalPattern(**p) for p in best_match.get("medical_patterns", [])]

                # 分析共享模式
                shared_patterns = await self._find_shared_patterns(content_hash, patterns)

                # 生成相关性提示
                relevance_hints = await self._generate_relevance_hints(
                    best_match["content_type"],
                    best_score
                )

                return SimilarContentResult(
                    content=processed_content,
                    similarity_score=best_score,
                    shared_patterns=shared_patterns,
                    relevance_hints=relevance_hints
                )

            return None

        except Exception as e:
            self.logger.error(f"Failed to find similar cached content: {e}")
            return None

    async def get_relevant_patterns(
        self,
        content_type: ContentType,
        query: str,
        limit: int = 10
    ) -> List[MedicalPattern]:
        """获取相关的医学模式"""
        try:
            client = await self._get_redis_client()

            # 获取所有相关类型的模式
            pattern = f"medical_pattern:{content_type.value}:*"
            keys = await client.keys(pattern)

            relevant_patterns = []

            for key in keys:
                try:
                    pattern_data = await client.get(key)
                    if pattern_data:
                        data = json.loads(pattern_data)
                        pattern = MedicalPattern(**data["pattern"])

                        # 计算相关性
                        relevance = await self._calculate_pattern_relevance(pattern, query)

                        if relevance > 0.5:  # 相关性阈值
                            pattern.relevance_score = relevance
                            relevant_patterns.append(pattern)

                except Exception as e:
                    self.logger.warning(f"Error loading pattern {key}: {e}")
                    continue

            # 按相关性排序并限制数量
            relevant_patterns.sort(key=lambda p: p.relevance_score, reverse=True)
            return relevant_patterns[:limit]

        except Exception as e:
            self.logger.error(f"Failed to get relevant patterns: {e}")
            return []

    async def _update_access_stats(self, cache_key: str) -> None:
        """更新访问统计"""
        try:
            client = await self._get_redis_client()

            # 更新访问计数
            await client.hincrby("cache_stats", "total_accesses", 1)
            await client.hincrby("cache_stats", cache_key, 1)

            # 更新最后访问时间
            await client.hset("last_access", cache_key, datetime.utcnow().isoformat())

        except Exception as e:
            self.logger.warning(f"Failed to update access stats: {e}")

    async def _calculate_content_quality(self, content: ProcessedContent) -> float:
        """计算内容质量评分"""
        try:
            # 基于多个因素计算质量评分
            factors = {
                "completeness": len(content.sections) / 10.0,  # 假设10个章节为满分
                "coherence": content.confidence_score,
                "structure": 0.8,  # 基于结构化程度
                "medical_accuracy": content.medical_accuracy or 0.7
            }

            quality_score = sum(factors.values()) / len(factors)
            return min(1.0, quality_score)  # 确保不超过1.0

        except Exception as e:
            self.logger.error(f"Failed to calculate content quality: {e}")
            return 0.5  # 默认中等质量

    async def _calculate_similarity(self, hash1: str, hash2: str) -> float:
        """计算内容哈希相似度"""
        try:
            # 简单的哈希相似度计算
            # 在实际应用中，可以使用更复杂的语义相似度算法

            # 转换为二进制表示
            bin1 = bin(int(hash1, 16))[2:].zfill(256)
            bin2 = bin(int(hash2, 16))[2:].zfill(256)

            # 计算汉明距离
            hamming_distance = sum(c1 != c2 for c1, c2 in zip(bin1, bin2))
            max_distance = len(bin1)

            similarity = 1 - (hamming_distance / max_distance)
            return similarity

        except Exception as e:
            self.logger.error(f"Failed to calculate similarity: {e}")
            return 0.0

    async def _find_shared_patterns(
        self,
        content_hash: str,
        patterns: List[MedicalPattern]
    ) -> List[MedicalPattern]:
        """查找共享的医学模式"""
        # 这里可以实现更复杂的模式匹配算法
        # 目前返回相关性最高的模式
        return patterns[:5]  # 返回前5个最相关的模式

    async def _generate_relevance_hints(
        self,
        content_type: str,
        similarity_score: float
    ) -> List[str]:
        """生成相关性提示"""
        hints = []

        if similarity_score > 0.9:
            hints.append("内容高度相似，可能包含相同的治疗方案")

        if content_type == ContentType.TREATMENT_PROTOCOL.value:
            hints.append("相关的治疗协议，参考药物剂量和注意事项")
        elif content_type == ContentType.DIAGNOSIS_CRITERIA.value:
            hints.append("诊断标准相关，注意排除标准和鉴别诊断")
        elif content_type == ContentType.DRUG_INFORMATION.value:
            hints.append("药物信息相关，注意禁忌症和不良反应")

        return hints

    async def _calculate_pattern_relevance(self, pattern: MedicalPattern, query: str) -> float:
        """计算模式与查询的相关性"""
        try:
            # 简单的关键词匹配
            query_lower = query.lower()
            pattern_text = f"{pattern.pattern_name} {pattern.description}".lower()

            # 计算关键词匹配度
            common_words = set(query_lower.split()) & set(pattern_text.split())
            total_words = set(query_lower.split()) | set(pattern_text.split())

            if not total_words:
                return 0.0

            jaccard_similarity = len(common_words) / len(total_words)

            # 结合模式自身的置信度
            relevance = jaccard_similarity * pattern.confidence_score

            return relevance

        except Exception as e:
            self.logger.error(f"Failed to calculate pattern relevance: {e}")
            return 0.0

    async def _update_cache_size(self) -> None:
        """更新缓存大小统计"""
        try:
            client = await self._get_redis_client()

            # 获取当前缓存大小
            medical_cache_keys = await client.keys("medical_cache:*")
            current_size = len(medical_cache_keys)

            # 如果超过最大条目数，清理旧条目
            if current_size > self.max_entries:
                await self._evict_old_entries(current_size - self.max_entries)

            # 更新统计
            await client.hset("cache_stats", "total_entries", current_size)

        except Exception as e:
            self.logger.warning(f"Failed to update cache size: {e}")

    async def _evict_old_entries(self, count: int) -> None:
        """清理旧的缓存条目"""
        try:
            client = await self._get_redis_client()

            # 获取所有缓存键及其最后访问时间
            pattern = "medical_cache:*"
            keys = await client.keys(pattern)

            # 获取访问时间并排序
            key_access_times = []
            for key in keys:
                last_access = await client.hget("last_access", key)
                if last_access:
                    key_access_times.append((key, last_access))

            # 按最后访问时间排序，最旧的在前
            key_access_times.sort(key=lambda x: x[1])

            # 删除最旧的条目
            for i, (key, _) in enumerate(key_access_times[:count]):
                await client.delete(key)
                await client.hdel("last_access", key)
                self.cache_stats["evictions"] += 1

            self.logger.info(f"Evicted {count} old cache entries")

        except Exception as e:
            self.logger.error(f"Failed to evict old entries: {e}")

    async def get_cache_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            client = await self._get_redis_client()

            # 获取Redis统计
            stats = await client.hgetall("cache_stats")

            # 计算缓存效率
            total_accesses = self.cache_stats["hits"] + self.cache_stats["misses"]
            efficiency = self.cache_stats["hits"] / total_accesses if total_accesses > 0 else 0.0

            return {
                "hits": self.cache_stats["hits"],
                "misses": self.cache_stats["misses"],
                "evictions": self.cache_stats["evictions"],
                "total_patterns": self.cache_stats["total_patterns"],
                "cache_efficiency": efficiency,
                "redis_stats": stats,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to get cache statistics: {e}")
            return {}

    async def clear_cache(self, content_type: Optional[ContentType] = None) -> None:
        """清理缓存"""
        try:
            client = await self._get_redis_client()

            if content_type:
                # 清理特定类型的缓存
                pattern = f"medical_cache:{content_type.value}:*"
                keys = await client.keys(pattern)
                for key in keys:
                    await client.delete(key)
                    await client.hdel("last_access", key)
            else:
                # 清理所有医学缓存
                patterns = [
                    "medical_cache:*",
                    "medical_pattern:*"
                ]
                for pattern in patterns:
                    keys = await client.keys(pattern)
                    for key in keys:
                        await client.delete(key)

                # 清理统计信息
                await client.delete("cache_stats", "last_access")

            self.logger.info(f"Cleared cache for type: {content_type}")

        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")

    async def close(self) -> None:
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()


# 全局实例
medical_cache = MedicalContentCache()


async def get_medical_cache() -> MedicalContentCache:
    """获取医学缓存实例"""
    return medical_cache