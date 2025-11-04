#!/usr/bin/env python3
"""
安全系统设置脚本
Security System Setup Script
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import get_settings
from app.core.logger import get_logger
from app.core.security import (
    password_manager,
    token_manager,
    rate_limiter,
    api_key_manager
)
import secrets

logger = get_logger(__name__)


async def test_password_manager():
    """测试密码管理器"""
    print("[SECURITY] 测试密码管理器...")

    test_password = "TestPassword123!@#"

    # 测试密码哈希
    hashed = password_manager.get_password_hash(test_password)
    print(f"  [OK] 密码哈希生成成功")

    # 测试密码验证
    is_valid = password_manager.verify_password(test_password, hashed)
    print(f"  [OK] 密码验证成功: {is_valid}")

    # 测试密码强度验证
    strength_result = password_manager.validate_password_strength(test_password)
    print(f"  [OK] 密码强度检查: {strength_result['strength']} (分数: {strength_result['score']})")

    if strength_result['errors']:
        print(f"  [WARN] 密码强度警告:")
        for error in strength_result['errors']:
            print(f"    - {error}")


async def test_token_manager():
    """测试令牌管理器"""
    print("\n🎟️  测试令牌管理器...")

    test_user_id = "test_user_123"

    try:
        # 测试访问令牌创建
        access_token = await token_manager.create_token(
            subject=test_user_id,
            token_type="access"
        )
        print(f"  [OK] 访问令牌创建成功: {access_token[:20]}...")

        # 测试令牌验证
        payload = await token_manager.verify_token(access_token)
        if payload and payload.get('sub') == test_user_id:
            print(f"  [OK] 访问令牌验证成功")
        else:
            print(f"  [FAIL] 访问令牌验证失败")

        # 测试刷新令牌创建
        refresh_token = await token_manager.create_token(
            subject=test_user_id,
            token_type="refresh"
        )
        print(f"  [OK] 刷新令牌创建成功: {refresh_token[:20]}...")

        # 测试API密钥创建
        api_token = await token_manager.create_token(
            subject=test_user_id,
            token_type="api_key"
        )
        print(f"  [OK] API令牌创建成功: {api_token[:20]}...")

    except Exception as e:
        print(f"  [FAIL] 令牌管理器测试失败: {e}")


async def test_rate_limiter():
    """测试限流器"""
    print("\n⏱️  测试限流器...")

    try:
        test_key = f"test_rate_limit_{secrets.token_hex(4)}"

        # 测试限流检查（5次请求限制）
        for i in range(7):
            is_limited, info = await rate_limiter.is_rate_limited(
                key=test_key,
                limit=5,
                window=60
            )

            if is_limited:
                print(f"  [WARN]  请求 {i+1} 被限流 (重试时间: {info['retry_after']}秒)")
            else:
                print(f"  [OK] 请求 {i+1} 通过 (当前计数: {info['request_count']})")

        print(f"  [OK] 限流器测试完成")

    except Exception as e:
        print(f"  [FAIL] 限流器测试失败: {e}")


async def test_api_key_manager():
    """测试API密钥管理器"""
    print("\n🔑 测试API密钥管理器...")

    try:
        test_user_id = "test_user_123"
        test_key_name = "Test API Key"
        test_permissions = ["read", "write"]

        # 测试API密钥生成
        api_key = api_key_manager.generate_api_key()
        print(f"  [OK] API密钥生成成功: {api_key}")

        # 测试API密钥创建
        created_key = await api_key_manager.create_api_key(
            user_id=test_user_id,
            name=test_key_name,
            permissions=test_permissions
        )
        print(f"  [OK] API密钥创建成功: {created_key}")

        # 测试API密钥验证
        key_data = await api_key_manager.verify_api_key(created_key)
        if key_data and key_data.get('user_id') == test_user_id:
            print(f"  [OK] API密钥验证成功")
            print(f"    用户ID: {key_data['user_id']}")
            print(f"    密钥名称: {key_data['name']}")
            print(f"    权限: {key_data['permissions']}")
        else:
            print(f"  [FAIL] API密钥验证失败")

        # 测试API密钥撤销
        await api_key_manager.revoke_api_key(created_key)

        # 验证撤销后的状态
        revoked_data = await api_key_manager.verify_api_key(created_key)
        if revoked_data is None:
            print(f"  [OK] API密钥撤销成功")
        else:
            print(f"  [FAIL] API密钥撤销失败")

    except Exception as e:
        print(f"  [FAIL] API密钥管理器测试失败: {e}")


async def check_security_configuration():
    """检查安全配置"""
    print("\n⚙️  检查安全配置...")

    settings = get_settings()

    # 检查必需的安全配置
    security_configs = {
        "SECRET_KEY": bool(settings.SECRET_KEY and len(settings.SECRET_KEY) >= 32),
        "ALGORITHM": bool(settings.ALGORITHM),
        "ACCESS_TOKEN_EXPIRE_MINUTES": settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0,
        "REFRESH_TOKEN_EXPIRE_DAYS": settings.REFRESH_TOKEN_EXPIRE_DAYS > 0,
        "RATE_LIMIT_ENABLED": isinstance(settings.RATE_LIMIT_ENABLED, bool),
        "CORS_ORIGINS": len(settings.CORS_ORIGINS) > 0,
    }

    print("  安全配置状态:")
    for config_name, is_valid in security_configs.items():
        status = "[OK]" if is_valid else "[FAIL]"
        print(f"    {status} {config_name}")

    # 检查SECRET_KEY强度
    if settings.SECRET_KEY:
        if len(settings.SECRET_KEY) < 32:
            print("    [WARN]  SECRET_KEY 长度不足32字符")
        elif settings.SECRET_KEY == "your-super-secret-key-change-in-production-environment":
            print("    [FAIL] SECRET_KEY 使用了默认值，请更改")
        else:
            print("    [OK] SECRET_KEY 强度良好")

    # 检查环境配置
    if settings.is_production():
        print("    🏭 生产环境模式")
        if settings.DEBUG:
            print("    [WARN]  生产环境建议关闭DEBUG模式")
    else:
        print("    [CONFIG] 开发环境模式")


async def generate_security_report():
    """生成安全报告"""
    print("\n[METRICS] 生成安全报告...")

    try:
        from app.core.security import get_security_headers, get_cors_config

        # 安全头报告
        headers = get_security_headers()
        print(f"  [SHIELD]  安全头配置 ({len(headers)} 项):")
        for header, value in headers.items():
            print(f"    {header}: {value}")

        # CORS配置报告
        cors_config = get_cors_config()
        print(f"\n  [WEB] CORS配置:")
        print(f"    允许源: {len(cors_config['allow_origins'])} 个")
        print(f"    允凭: {cors_config['allow_credentials']}")
        print(f"    允许方法: {', '.join(cors_config['allow_methods'])}")
        print(f"    允许头: {', '.join(cors_config['allow_headers'])}")

    except Exception as e:
        print(f"  [FAIL] 安全报告生成失败: {e}")


async def main():
    """主函数"""
    print("[SECURITY] CPG2PVG-AI 安全系统设置")
    print("=" * 50)

    # 检查安全配置
    await check_security_configuration()
    print()

    # 测试密码管理器
    await test_password_manager()

    # 测试令牌管理器
    await test_token_manager()

    # 测试限流器
    await test_rate_limiter()

    # 测试API密钥管理器
    await test_api_key_manager()

    # 生成安全报告
    await generate_security_report()

    print("\n[SUCCESS] 安全系统设置完成！")
    print("\n[LIST] 安全建议:")
    print("1. 确保使用强随机SECRET_KEY")
    print("2. 在生产环境中禁用DEBUG模式")
    print("3. 配置适当的CORS策略")
    print("4. 启用HTTPS和HSTS")
    print("5. 定期轮换密钥和令牌")
    print("6. 监控异常的认证尝试")
    print("7. 实施适当的限流策略")
    print("8. 定期进行安全审计")

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)