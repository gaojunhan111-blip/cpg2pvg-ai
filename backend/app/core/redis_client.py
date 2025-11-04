"""
Redis客户端配置
CPG2PVG-AI System Redis Client
"""

import json
import pickle
import logging
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
import redis.asyncio as aioredis
from functools import wraps

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis客户端封装类"""

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._connected = False

    async def connect(self) -> None:
        """连接到Redis"""
        try:
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=False,  # 保持bytes以支持pickle
                max_connections=20,
                retry_on_timeout=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                health_check_interval=30,
            )
            # 测试连接
            await self._redis.ping()
            self._connected = True
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False
            raise

    async def disconnect(self) -> None:
        """断开Redis连接"""
        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.info("Redis connection closed")

    @property
    def client(self) -> aioredis.Redis:
        """获取Redis客户端"""
        if not self._connected or not self._redis:
            raise RuntimeError("Redis client not connected")
        return self._redis

    # 基础操作
    async def get(self, key: str) -> Optional[str]:
        """获取字符串值"""
        try:
            value = await self.client.get(key)
            return value.decode('utf-8') if value else None
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None

    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """设置字符串值"""
        try:
            if expire:
                return await self.client.setex(key, expire, value)
            else:
                return await self.client.set(key, value)
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除键"""
        try:
            return bool(await self.client.delete(key))
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return bool(await self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """设置键的过期时间"""
        try:
            return bool(await self.client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False

    # JSON操作
    async def get_json(self, key: str) -> Optional[Dict]:
        """获取JSON对象"""
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value.decode('utf-8'))
            return None
        except Exception as e:
            logger.error(f"Redis GET JSON error for key {key}: {e}")
            return None

    async def set_json(self, key: str, value: Dict, expire: Optional[int] = None) -> bool:
        """设置JSON对象"""
        try:
            json_str = json.dumps(value, default=str)
            if expire:
                return await self.client.setex(key, expire, json_str)
            else:
                return await self.client.set(key, json_str)
        except Exception as e:
            logger.error(f"Redis SET JSON error for key {key}: {e}")
            return False

    # Pickle操作（用于复杂对象）
    async def get_pickle(self, key: str) -> Optional[Any]:
        """获取pickle序列化对象"""
        try:
            value = await self.client.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET pickle error for key {key}: {e}")
            return None

    async def set_pickle(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置pickle序列化对象"""
        try:
            pickled_value = pickle.dumps(value)
            if expire:
                return await self.client.setex(key, expire, pickled_value)
            else:
                return await self.client.set(key, pickled_value)
        except Exception as e:
            logger.error(f"Redis SET pickle error for key {key}: {e}")
            return False

    # 列表操作
    async def lpush(self, key: str, *values) -> int:
        """从左侧推入列表"""
        try:
            return await self.client.lpush(key, *values)
        except Exception as e:
            logger.error(f"Redis LPUSH error for key {key}: {e}")
            return 0

    async def rpush(self, key: str, *values) -> int:
        """从右侧推入列表"""
        try:
            return await self.client.rpush(key, *values)
        except Exception as e:
            logger.error(f"Redis RPUSH error for key {key}: {e}")
            return 0

    async def lpop(self, key: str) -> Optional[str]:
        """从左侧弹出元素"""
        try:
            value = await self.client.lpop(key)
            return value.decode('utf-8') if value else None
        except Exception as e:
            logger.error(f"Redis LPOP error for key {key}: {e}")
            return None

    async def rpop(self, key: str) -> Optional[str]:
        """从右侧弹出元素"""
        try:
            value = await self.client.rpop(key)
            return value.decode('utf-8') if value else None
        except Exception as e:
            logger.error(f"Redis RPOP error for key {key}: {e}")
            return None

    async def llen(self, key: str) -> int:
        """获取列表长度"""
        try:
            return await self.client.llen(key)
        except Exception as e:
            logger.error(f"Redis LLEN error for key {key}: {e}")
            return 0

    async def lrange(self, key: str, start: int, end: int) -> List[str]:
        """获取列表范围内的元素"""
        try:
            values = await self.client.lrange(key, start, end)
            return [value.decode('utf-8') for value in values]
        except Exception as e:
            logger.error(f"Redis LRANGE error for key {key}: {e}")
            return []

    # 哈希操作
    async def hget(self, key: str, field: str) -> Optional[str]:
        """获取哈希字段值"""
        try:
            value = await self.client.hget(key, field)
            return value.decode('utf-8') if value else None
        except Exception as e:
            logger.error(f"Redis HGET error for key {key}, field {field}: {e}")
            return None

    async def hset(self, key: str, field: str, value: str) -> bool:
        """设置哈希字段值"""
        try:
            return bool(await self.client.hset(key, field, value))
        except Exception as e:
            logger.error(f"Redis HSET error for key {key}, field {field}: {e}")
            return False

    async def hgetall(self, key: str) -> Dict[str, str]:
        """获取哈希所有字段"""
        try:
            hash_data = await self.client.hgetall(key)
            return {field.decode('utf-8'): value.decode('utf-8')
                   for field, value in hash_data.items()}
        except Exception as e:
            logger.error(f"Redis HGETALL error for key {key}: {e}")
            return {}

    async def hdel(self, key: str, *fields) -> int:
        """删除哈希字段"""
        try:
            return await self.client.hdel(key, *fields)
        except Exception as e:
            logger.error(f"Redis HDEL error for key {key}: {e}")
            return 0

    # 集合操作
    async def sadd(self, key: str, *members) -> int:
        """添加集合成员"""
        try:
            return await self.client.sadd(key, *members)
        except Exception as e:
            logger.error(f"Redis SADD error for key {key}: {e}")
            return 0

    async def smembers(self, key: str) -> set:
        """获取集合所有成员"""
        try:
            members = await self.client.smembers(key)
            return {member.decode('utf-8') for member in members}
        except Exception as e:
            logger.error(f"Redis SMEMBERS error for key {key}: {e}")
            return set()

    async def sismember(self, key: str, member: str) -> bool:
        """检查成员是否在集合中"""
        try:
            return bool(await self.client.sismember(key, member))
        except Exception as e:
            logger.error(f"Redis SISMEMBER error for key {key}, member {member}: {e}")
            return False

    # 缓存装饰器
    def cache_result(self, expire: int = 3600, key_prefix: str = ""):
        """缓存结果装饰器"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = f"{key_prefix}{func.__name__}:{hash(str(args) + str(kwargs))}"

                # 尝试从缓存获取
                cached_result = await self.get_pickle(cache_key)
                if cached_result is not None:
                    return cached_result

                # 执行函数
                result = await func(*args, **kwargs)

                # 缓存结果
                await self.set_pickle(cache_key, result, expire)

                return result
            return wrapper
        return decorator

    # 分布式锁
    async def acquire_lock(self, key: str, expire: int = 30) -> bool:
        """获取分布式锁"""
        try:
            lock_key = f"lock:{key}"
            # 使用SETNX获取锁
            return bool(await self.client.set(lock_key, "1", ex=expire, nx=True))
        except Exception as e:
            logger.error(f"Redis ACQUIRE LOCK error for key {key}: {e}")
            return False

    async def release_lock(self, key: str) -> bool:
        """释放分布式锁"""
        try:
            lock_key = f"lock:{key}"
            return bool(await self.client.delete(lock_key))
        except Exception as e:
            logger.error(f"Redis RELEASE LOCK error for key {key}: {e}")
            return False

    # 统计操作
    async def increment(self, key: str, amount: int = 1) -> int:
        """递增计数器"""
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCREMENT error for key {key}: {e}")
            return 0

    async def decrement(self, key: str, amount: int = 1) -> int:
        """递减计数器"""
        try:
            return await self.client.decrby(key, amount)
        except Exception as e:
            logger.error(f"Redis DECREMENT error for key {key}: {e}")
            return 0

    # 健康检查
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            start_time = datetime.utcnow()
            await self.client.ping()
            end_time = datetime.utcnow()

            response_time = (end_time - start_time).total_seconds() * 1000

            info = await self.client.info()

            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# 全局Redis客户端实例
redis_client = RedisClient()


# 便捷函数
async def get_redis_client() -> RedisClient:
    """获取Redis客户端实例"""
    if not redis_client._connected:
        await redis_client.connect()
    return redis_client


# 缓存管理器
class CacheManager:
    """缓存管理器"""

    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        self.default_expire = settings.REDIS_CACHE_TTL

    async def cache_user_session(self, user_id: int, session_data: Dict) -> bool:
        """缓存用户会话"""
        key = f"session:user:{user_id}"
        return await self.redis.set_json(key, session_data, expire=86400)  # 24小时

    async def get_user_session(self, user_id: int) -> Optional[Dict]:
        """获取用户会话"""
        key = f"session:user:{user_id}"
        return await self.redis.get_json(key)

    async def cache_task_progress(self, task_id: str, progress_data: Dict) -> bool:
        """缓存任务进度"""
        key = f"task_progress:{task_id}"
        return await self.redis.set_json(key, progress_data, expire=3600)  # 1小时

    async def get_task_progress(self, task_id: str) -> Optional[Dict]:
        """获取任务进度"""
        key = f"task_progress:{task_id}"
        return await self.redis.get_json(key)

    async def cache_processing_result(self, guideline_id: int, result_data: Dict) -> bool:
        """缓存处理结果"""
        key = f"processing_result:{guideline_id}"
        return await self.redis.set_json(key, result_data, expire=7200)  # 2小时

    async def get_processing_result(self, guideline_id: int) -> Optional[Dict]:
        """获取处理结果缓存"""
        key = f"processing_result:{guideline_id}"
        return await self.redis.get_json(key)

    async def increment_api_usage(self, user_id: int) -> int:
        """递增API使用次数"""
        key = f"api_usage:{user_id}:{datetime.utcnow().strftime('%Y-%m')}"
        return await self.redis.increment(key)

    async def get_api_usage(self, user_id: int) -> int:
        """获取API使用次数"""
        key = f"api_usage:{user_id}:{datetime.utcnow().strftime('%Y-%m')}"
        usage = await self.redis.get(key)
        return int(usage) if usage else 0

    async def cache_llm_response(self, prompt_hash: str, response: Dict, expire: int = 3600) -> bool:
        """缓存LLM响应"""
        key = f"llm_cache:{prompt_hash}"
        return await self.redis.set_json(key, response, expire)


# 全局缓存管理器实例
cache_manager = CacheManager(redis_client)