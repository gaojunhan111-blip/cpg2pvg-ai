#!/usr/bin/env python3
"""
LLM提供商设置脚本
LLM Provider Setup Script
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.llm_config import get_llm_config_manager, ModelSelectionStrategy
from app.core.llm_client import get_llm_client
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)


async def check_llm_health():
    """检查LLM提供商健康状态"""
    print("[AI] 检查LLM提供商健康状态...")

    try:
        llm_client = await get_llm_client()
        health_result = await llm_client.health_check()

        print(f"总体状态: {health_result['status']}")
        print("\n提供商状态:")
        for provider_name, provider_status in health_result['providers'].items():
            status_icon = "[OK]" if provider_status['status'] == 'healthy' else "[FAIL]"
            print(f"  {status_icon} {provider_name}: {provider_status['status']}")
            if provider_status['status'] == 'unhealthy':
                print(f"    错误: {provider_status.get('error', 'Unknown error')}")
            elif 'model' in provider_status:
                print(f"    模型: {provider_status['model']}")

        return health_result['status'] != 'unhealthy'

    except Exception as e:
        print(f"[FAIL] LLM健康检查失败: {e}")
        return False


async def test_llm_providers():
    """测试LLM提供商功能"""
    print("\n🧪 测试LLM提供商功能...")

    try:
        llm_client = await get_llm_client()
        config_manager = get_llm_config_manager()

        # 测试消息
        test_message = "请简单解释什么是医学指南？"

        print(f"测试消息: {test_message}")
        print()

        providers = config_manager.get_providers(enabled_only=True)

        for provider in providers:
            if provider.provider_type.value == 'mock':
                continue  # 跳过Mock提供商

            print(f"测试提供商: {provider.name}")
            try:
                response = await llm_client.chat_completion(
                    messages=[{"role": "user", "content": test_message}],
                    provider=provider.name,
                    max_tokens=100
                )
                print(f"  [OK] 响应成功: {response[:100]}...")

            except Exception as e:
                print(f"  [FAIL] 响应失败: {e}")
            print()

        return True

    except Exception as e:
        print(f"[FAIL] LLM测试失败: {e}")
        return False


async def show_available_models():
    """显示可用模型"""
    print("[LIST] 可用模型列表:")

    try:
        config_manager = get_llm_config_manager()

        # 按分类显示
        categories = ["general", "reasoning", "medical"]

        for category in categories:
            models = config_manager.get_models(category=category)
            if models:
                print(f"\n🏷️  {category.upper()} 模型:")
                for model in models:
                    cost_icon = "💰" if model.cost_per_1k_tokens > 0.01 else "💵"
                    tags_str = ", ".join(model.tags[:3])  # 只显示前3个标签
                    if len(model.tags) > 3:
                        tags_str += "..."

                    print(f"  {cost_icon} {model.provider.value}:{model.name}")
                    print(f"     📝 {model.description}")
                    print(f"     🏷️  {tags_str} | 💵 ${model.cost_per_1k_tokens}/1K tokens")
                    print(f"     📏 上下文: {model.context_length} tokens")

        # 推荐模型
        print(f"\n[TARGET] 推荐模型:")
        strategies = [
            ("最快响应", ModelSelectionStrategy.fastest),
            ("成本效益", ModelSelectionStrategy.cost_effective),
            ("最高质量", ModelSelectionStrategy.highest_quality),
            ("长上下文", ModelSelectionStrategy.long_context)
        ]

        for strategy_name, strategy_func in strategies:
            model = strategy_func()
            if model:
                print(f"  {strategy_name}: {model.provider.value}:{model.name}")
            else:
                print(f"  {strategy_name}: 无可用模型")

    except Exception as e:
        print(f"[FAIL] 获取模型列表失败: {e}")


async def show_configuration():
    """显示当前配置"""
    print("⚙️  当前LLM配置:")

    try:
        settings = get_settings()
        config_manager = get_llm_config_manager()

        print(f"默认LLM模型: {settings.DEFAULT_LLM_MODEL}")
        print(f"高质量模型: {settings.HIGH_QUALITY_MODEL}")
        print(f"成本效益模型: {settings.COST_EFFECTIVE_MODEL}")
        print(f"最大tokens: {settings.MAX_TOKENS_PER_REQUEST}")
        print(f"默认温度: {settings.TEMPERATURE}")
        print()

        providers = config_manager.get_providers()
        print(f"已配置提供商 ({len(providers)} 个):")

        for provider in providers:
            status = "[GREEN]" if provider.enabled else "[REDIS]"
            priority = f"⭐ {provider.priority}" if provider.priority <= 2 else f"  {provider.priority}"
            print(f"  {status} {priority} {provider.name} ({provider.provider_type.value})")

            if provider.base_url:
                print(f"    URL: {provider.base_url}")

            if provider.models:
                print(f"    模型: {len(provider.models)} 个")

    except Exception as e:
        print(f"[FAIL] 获取配置失败: {e}")


async def validate_configuration():
    """验证配置"""
    print("[OK] 验证LLM配置...")

    try:
        config_manager = get_llm_config_manager()
        errors = config_manager.validate_config()

        if errors:
            print("[FAIL] 发现配置问题:")
            for error in errors:
                print(f"  - {error}")
            return False
        else:
            print("[OK] 配置验证通过")
            return True

    except Exception as e:
        print(f"[FAIL] 配置验证失败: {e}")
        return False


async def save_configuration():
    """保存配置到文件"""
    try:
        config_manager = get_llm_config_manager()
        config_path = project_root / "config" / "llm_config.json"
        config_path.parent.mkdir(exist_ok=True)

        config_manager.save_config(config_path)
        print(f"[OK] 配置已保存到: {config_path}")

    except Exception as e:
        print(f"[FAIL] 保存配置失败: {e}")


async def main():
    """主函数"""
    print("[AI] CPG2PVG-AI LLM提供商设置")
    print("=" * 50)

    # 显示当前配置
    await show_configuration()
    print()

    # 显示可用模型
    await show_available_models()
    print()

    # 验证配置
    config_valid = await validate_configuration()
    if not config_valid:
        print("\n[WARN]  配置验证失败，请检查配置")
        return False
    print()

    # 健康检查
    health_ok = await check_llm_health()
    print()

    # 功能测试
    if health_ok:
        test_ok = await test_llm_providers()
        if not test_ok:
            print("\n[WARN]  部分LLM提供商测试失败")

    # 保存配置
    await save_configuration()

    print("\n[SUCCESS] LLM提供商设置完成！")
    print("\n[LIST] 下一步:")
    print("1. 检查API密钥配置")
    print("2. 测试不同模型的效果")
    print("3. 根据需要调整模型优先级")
    print("4. 监控使用成本")

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)