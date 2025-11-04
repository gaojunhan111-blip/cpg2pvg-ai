"""
增强安全相关功能
CPG2PVG-AI System Enhanced Security
"""

import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Any, Dict, List
from dataclasses import dataclass
from enum import Enum

from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext
import redis.asyncio as redis

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 安全相关枚举
class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"
    RESET = "reset"
    VERIFICATION = "verification"

class SecurityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# HTTP Bearer安全方案
security = HTTPBearer(auto_error=False)

@dataclass
class SecurityContext:
    """安全上下文"""
    user_id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    roles: List[str] = None
    permissions: List[str] = None
    token_type: Optional[TokenType] = None
    security_level: SecurityLevel = SecurityLevel.LOW
    is_active: bool = True
    is_verified: bool = False
    is_premium: bool = False
    api_quota: int = 0
    api_usage: int = 0

    def __post_init__(self):
        if self.roles is None:
            self.roles = []
        if self.permissions is None:
            self.permissions = []

    def has_role(self, role: str) -> bool:
        """检查是否具有指定角色"""
        return role in self.roles

    def has_permission(self, permission: str) -> bool:
        """检查是否具有指定权限"""
        return permission in self.permissions

    def has_api_quota(self) -> bool:
        """检查是否有API配额"""
        return self.api_usage < self.api_quota

    def consume_api_quota(self, amount: int = 1) -> bool:
        """消耗API配额"""
        if self.has_api_quota():
            self.api_usage += amount
            return True
        return False

class RateLimiter:
    """API限流器"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    async def _get_redis_client(self) -> redis.Redis:
        """获取Redis客户端"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis_client

    async def is_rate_limited(
        self,
        key: str,
        limit: int,
        window: int = 60
    ) -> tuple[bool, Dict[str, Any]]:
        """检查是否触发限流"""
        try:
            client = await self._get_redis_client()
            current_time = int(time.time())
            window_start = current_time - window

            # 使用滑动窗口算法
            pipe = client.pipeline()

            # 移除过期的请求记录
            pipe.zremrangebyscore(key, 0, window_start)

            # 添加当前请求
            pipe.zadd(key, {str(current_time): current_time})

            # 获取当前窗口内的请求数
            pipe.zcard(key)

            # 设置过期时间
            pipe.expire(key, window)

            results = await pipe.execute()
            request_count = results[2]

            is_limited = request_count > limit

            return is_limited, {
                "request_count": request_count,
                "limit": limit,
                "window": window,
                "reset_time": window_start + window + window,
                "retry_after": window if is_limited else 0
            }

        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # 如果Redis不可用，允许请求通过
            return False, {"request_count": 0, "limit": limit, "window": window}

class TokenManager:
    """令牌管理器"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    async def _get_redis_client(self) -> redis.Redis:
        """获取Redis客户端"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis_client

    async def create_token(
        self,
        subject: str,
        token_type: TokenType,
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建令牌"""
        if expires_delta is None:
            if token_type == TokenType.ACCESS:
                expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            elif token_type == TokenType.REFRESH:
                expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            elif token_type == TokenType.API_KEY:
                expires_delta = timedelta(days=365)  # API key有效期1年
            elif token_type == TokenType.RESET:
                expires_delta = timedelta(hours=1)  # 重置令牌1小时有效
            elif token_type == TokenType.VERIFICATION:
                expires_delta = timedelta(hours=24)  # 验证令牌24小时有效
            else:
                expires_delta = timedelta(hours=1)

        expire = datetime.utcnow() + expires_delta

        # 基础声明
        claims = {
            "exp": expire,
            "iat": datetime.utcnow(),
            "sub": str(subject),
            "type": token_type.value,
            "jti": secrets.token_urlsafe(16)  # JWT ID
        }

        # 添加额外声明
        if additional_claims:
            claims.update(additional_claims)

        # 创建令牌
        token = jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        # 如果是刷新令牌，存储到Redis
        if token_type == TokenType.REFRESH:
            await self._store_refresh_token(subject, token, expires_delta)

        return token

    async def _store_refresh_token(self, user_id: str, token: str, expires_delta: timedelta):
        """存储刷新令牌"""
        try:
            client = await self._get_redis_client()
            key = f"refresh_token:{user_id}"
            await client.setex(
                key,
                int(expires_delta.total_seconds()),
                token
            )
        except Exception as e:
            logger.error(f"Failed to store refresh token: {e}")

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            return payload
        except ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except JWTError as e:
            logger.warning(f"Token validation failed: {e}")
            return None

    async def revoke_token(self, user_id: str, token_type: TokenType = TokenType.REFRESH):
        """撤销令牌"""
        try:
            if token_type == TokenType.REFRESH:
                client = await self._get_redis_client()
                key = f"refresh_token:{user_id}"
                await client.delete(key)
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")

    async def revoke_all_tokens(self, user_id: str):
        """撤销用户所有令牌"""
        await self.revoke_token(user_id, TokenType.REFRESH)

class PasswordManager:
    """密码管理器"""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """获取密码哈希"""
        return pwd_context.hash(password)

    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """验证密码强度"""
        errors = []

        if len(password) < 8:
            errors.append("密码长度至少8位")

        if len(password) > 128:
            errors.append("密码长度不能超过128位")

        if not any(c.islower() for c in password):
            errors.append("密码必须包含小写字母")

        if not any(c.isupper() for c in password):
            errors.append("密码必须包含大写字母")

        if not any(c.isdigit() for c in password):
            errors.append("密码必须包含数字")

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            errors.append("密码必须包含特殊字符")

        # 计算密码强度分数
        score = 0
        if len(password) >= 12:
            score += 1
        if len(password) >= 16:
            score += 1
        if any(c.islower() for c in password):
            score += 1
        if any(c.isupper() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 1
        if any(c in special_chars for c in password):
            score += 1

        strength_levels = {
            0: "非常弱",
            1: "弱",
            2: "一般",
            3: "中等",
            4: "强",
            5: "很强",
            6: "非常强"
        }

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "score": score,
            "strength": strength_levels.get(score, "未知")
        }

class APIKeyManager:
    """API密钥管理器"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    async def _get_redis_client(self) -> redis.Redis:
        """获取Redis客户端"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis_client

    @staticmethod
    def generate_api_key() -> str:
        """生成API密钥"""
        return f"cpg2pvg_{secrets.token_urlsafe(32)}"

    async def create_api_key(
        self,
        user_id: str,
        name: str,
        permissions: List[str],
        expires_at: Optional[datetime] = None
    ) -> str:
        """创建API密钥"""
        api_key = self.generate_api_key()
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        key_data = {
            "user_id": user_id,
            "name": name,
            "permissions": ",".join(permissions),
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "is_active": True
        }

        try:
            client = await self._get_redis_client()
            key_prefix = f"api_key:{key_hash}"

            # 存储API密钥信息
            await client.hset(key_prefix, mapping=key_data)

            # 设置过期时间
            if expires_at:
                ttl = int((expires_at - datetime.utcnow()).total_seconds())
                await client.expire(key_prefix, ttl)

            # 添加到用户的API密钥列表
            await client.sadd(f"user_api_keys:{user_id}", key_hash)

            return api_key

        except Exception as e:
            logger.error(f"Failed to create API key: {e}")
            raise

    async def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """验证API密钥"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        try:
            client = await self._get_redis_client()
            key_data = await client.hgetall(f"api_key:{key_hash}")

            if not key_data:
                return None

            # 检查是否激活
            if key_data.get("is_active") != "True":
                return None

            # 检查是否过期
            expires_at = key_data.get("expires_at")
            if expires_at:
                expire_time = datetime.fromisoformat(expires_at)
                if datetime.utcnow() > expire_time:
                    return None

            return key_data

        except Exception as e:
            logger.error(f"Failed to verify API key: {e}")
            return None

    async def revoke_api_key(self, api_key: str):
        """撤销API密钥"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        try:
            client = await self._get_redis_client()
            key_prefix = f"api_key:{key_hash}"

            # 获取用户ID
            user_id = await client.hget(key_prefix, "user_id")

            if user_id:
                # 从用户的API密钥列表中移除
                await client.srem(f"user_api_keys:{user_id}", key_hash)

            # 删除API密钥
            await client.delete(key_prefix)

        except Exception as e:
            logger.error(f"Failed to revoke API key: {e}")

# 全局实例
rate_limiter = RateLimiter()
token_manager = TokenManager()
password_manager = PasswordManager()
api_key_manager = APIKeyManager()

# 便捷函数（向后兼容）
async def create_access_token(
    subject: str, expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问令牌"""
    return await token_manager.create_token(
        subject=subject,
        token_type=TokenType.ACCESS,
        expires_delta=expires_delta
    )

async def verify_token(token: str) -> Optional[str]:
    """验证令牌"""
    payload = await token_manager.verify_token(token)
    return payload.get("sub") if payload else None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return password_manager.verify_password(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return password_manager.get_password_hash(password)

def generate_api_key() -> str:
    """生成API密钥"""
    return api_key_manager.generate_api_key()

def generate_reset_token() -> str:
    """生成重置令牌"""
    return secrets.token_urlsafe(32)

# 异常类
class SecurityException(HTTPException):
    """安全异常"""

    def __init__(self, detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

class RateLimitException(HTTPException):
    """限流异常"""

    def __init__(self, detail: str, retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(retry_after)},
        )

class InsufficientPermissionException(HTTPException):
    """权限不足异常"""

    def __init__(self, detail: str = "权限不足"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )

class APIKeyException(HTTPException):
    """API密钥异常"""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )

# 认证依赖
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = security,
    request: Request = None
) -> Optional[SecurityContext]:
    """获取当前用户（可选）"""
    if not credentials:
        # 尝试API密钥认证
        api_key = request.headers.get("X-API-Key") if request else None
        if api_key:
            return await authenticate_api_key(api_key)
        return None

    try:
        payload = await token_manager.verify_token(credentials.credentials)
        if not payload:
            return None

        token_type = payload.get("type")
        if token_type != TokenType.ACCESS:
            return None

        # 构建安全上下文
        context = SecurityContext(
            user_id=payload.get("sub"),
            token_type=TokenType.ACCESS,
            is_active=True
        )

        return context

    except Exception:
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = security,
    request: Request = None
) -> SecurityContext:
    """获取当前用户（必需）"""
    if not credentials:
        # 尝试API密钥认证
        api_key = request.headers.get("X-API-Key") if request else None
        if api_key:
            context = await authenticate_api_key(api_key)
            if context:
                return context
        raise SecurityException("缺少认证凭据")

    try:
        payload = await token_manager.verify_token(credentials.credentials)
        if not payload:
            raise SecurityException("无效的认证令牌")

        token_type = payload.get("type")
        if token_type != TokenType.ACCESS:
            raise SecurityException("令牌类型错误")

        # 构建安全上下文
        context = SecurityContext(
            user_id=payload.get("sub"),
            token_type=TokenType.ACCESS,
            is_active=True
        )

        # TODO: 从数据库加载用户详细信息
        # 这里需要实现从数据库获取用户信息的逻辑

        return context

    except SecurityException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise SecurityException("认证失败")

async def authenticate_api_key(api_key: str) -> Optional[SecurityContext]:
    """API密钥认证"""
    try:
        key_data = await api_key_manager.verify_api_key(api_key)
        if not key_data:
            return None

        # 构建安全上下文
        context = SecurityContext(
            user_id=key_data.get("user_id"),
            token_type=TokenType.API_KEY,
            permissions=key_data.get("permissions", "").split(","),
            is_active=True
        )

        return context

    except Exception as e:
        logger.error(f"API key authentication error: {e}")
        return None

# 权限检查装饰器
def require_permissions(required_permissions: List[str]):
    """需要指定权限的装饰器"""
    def dependency(current_user: SecurityContext = get_current_user) -> SecurityContext:
        for permission in required_permissions:
            if not current_user.has_permission(permission):
                raise InsufficientPermissionException(f"缺少权限: {permission}")
        return current_user
    return dependency

def require_roles(required_roles: List[str]):
    """需要指定角色的装饰器"""
    def dependency(current_user: SecurityContext = get_current_user) -> SecurityContext:
        for role in required_roles:
            if not current_user.has_role(role):
                raise InsufficientPermissionException(f"缺少角色: {role}")
        return current_user
    return dependency

def require_premium():
    """需要高级版的装饰器"""
    def dependency(current_user: SecurityContext = get_current_user) -> SecurityContext:
        if not current_user.is_premium:
            raise InsufficientPermissionException("需要高级版账户")
        return current_user
    return dependency

def require_verified():
    """需要验证账户的装饰器"""
    def dependency(current_user: SecurityContext = get_current_user) -> SecurityContext:
        if not current_user.is_verified:
            raise InsufficientPermissionException("需要验证邮箱")
        return current_user
    return dependency

# 限流装饰器
def rate_limit(key_func: callable, limit: int, window: int = 60):
    """API限流装饰器"""
    async def dependency(request: Request) -> None:
        rate_key = key_func(request)
        is_limited, limit_info = await rate_limiter.is_rate_limited(rate_key, limit, window)

        if is_limited:
            raise RateLimitException(
                detail=f"请求过于频繁，请在{limit_info['retry_after']}秒后重试",
                retry_after=limit_info['retry_after']
            )

    return dependency

# 常用限流函数
def rate_limit_by_ip(limit: int, window: int = 60):
    """基于IP的限流"""
    return rate_limit(
        key_func=lambda request: f"rate_limit:ip:{request.client.host}",
        limit=limit,
        window=window
    )

def rate_limit_by_user(limit: int, window: int = 60):
    """基于用户的限流"""
    async def key_func(request: Request) -> str:
        # 尝试从请求中获取用户ID
        current_user = await get_current_user_optional(
            request=request
        )
        if current_user and current_user.user_id:
            return f"rate_limit:user:{current_user.user_id}"
        else:
            return f"rate_limit:ip:{request.client.host}"

    return rate_limit(key_func=key_func, limit=limit, window=window)

# CORS安全配置
def get_cors_config() -> Dict[str, Any]:
    """获取CORS配置"""
    return {
        "allow_origins": settings.get_allowed_origins(),
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": [
            "Authorization",
            "Content-Type",
            "X-API-Key",
            "X-Request-ID"
        ]
    }

# 安全头配置
def get_security_headers() -> Dict[str, str]:
    """获取安全头配置"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }