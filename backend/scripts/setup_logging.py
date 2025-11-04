#!/usr/bin/env python3
"""
日志系统设置脚本
Logging System Setup Script
"""

import asyncio
import os
import sys
import time
import json
import uuid
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import get_settings
from app.core.logger import (
    get_logger,
    set_log_context,
    get_log_context,
    LogContext,
    LogCategory,
    log_api_request,
    log_api_response,
    log_security_event,
    log_workflow_event,
    log_llm_call,
    log_performance_metric,
    log_audit_event,
    LogContextManager
)

logger = get_logger(__name__)


async def test_basic_logging():
    """测试基础日志功能"""
    print("📝 测试基础日志功能...")

    test_logger = get_logger("test_basic")

    # 测试不同级别的日志
    test_logger.debug("这是一条调试信息")
    test_logger.info("这是一条信息日志")
    test_logger.warning("这是一条警告日志")
    test_logger.error("这是一条错误日志")

    # 测试结构化日志
    structured_logger = get_logger()
    structured_logger.info(
        "结构化日志测试",
        context=LogContext(
            request_id=str(uuid.uuid4()),
            component="test_component",
            category=LogCategory.SYSTEM,
            tags={"test": True, "version": "1.0.0"}
        )
    )

    print("  [OK] 基础日志测试完成")


async def test_context_logging():
    """测试上下文日志"""
    print("\n🔄 测试上下文日志...")

    # 设置上下文
    context = LogContext(
        request_id=str(uuid.uuid4()),
        user_id="test_user_123",
        component="workflow_processor",
        category=LogCategory.WORKFLOW
    )
    set_log_context(context)

    # 在上下文中记录日志
    logger.info("这是在上下文中记录的日志")
    logger.info("上下文会自动附加到所有日志")

    # 验证上下文
    current_context = get_log_context()
    if current_context and current_context.request_id == context.request_id:
        print("  [OK] 上下文设置和获取成功")
    else:
        print("  [FAIL] 上下文设置或获取失败")

    # 清除上下文
    get_logger().clear_context()
    print("  [OK] 上下文已清除")


async def test_context_manager():
    """测试上下文管理器"""
    print("\n[CONFIG] 测试上下文管理器...")

    context = LogContext(
        request_id=str(uuid.uuid4()),
        user_id="test_user_456",
        component="api_handler",
        category=LogCategory.API
    )

    with LogContextManager(context) as ctx:
        logger.info("在上下文管理器中记录日志")
        logger.info("这个上下文会自动管理生命周期")
        print(f"  [OK] 上下文管理器工作正常, request_id: {ctx.request_id}")

    # 上下文应该已经被清除
    if get_log_context() is None:
        print("  [OK] 上下文已自动清除")
    else:
        print("  [FAIL] 上下文未被清除")


async def test_specialized_logging():
    """测试专门的日志函数"""
    print("\n[TARGET] 测试专门的日志函数...")

    request_id = str(uuid.uuid4())
    user_id = "test_user_789"

    # 测试API日志
    log_api_request("POST", "/api/v1/guidelines", user_id, request_id)
    await asyncio.sleep(0.1)  # 模拟处理时间
    log_api_response("POST", "/api/v1/guidelines", 201, 120.5, user_id, request_id)

    # 测试安全事件日志
    log_security_event("user_login", user_id, "192.168.1.100", success=True)
    log_security_event("failed_login", "unknown_user", "192.168.1.101", success=False)

    # 测试工作流日志
    workflow_id = str(uuid.uuid4())
    log_workflow_event(workflow_id, "started", "running", user_id)
    log_workflow_event(workflow_id, "processing", "running", user_id)
    log_workflow_event(workflow_id, "completed", "success", user_id)

    # 测试LLM调用日志
    log_llm_call(
        provider="openai",
        model="gpt-4",
        tokens_used=150,
        cost=0.009,
        duration_ms=1250.0,
        user_id=user_id
    )

    # 测试性能指标日志
    log_performance_metric("api_response_time", 120.5, "ms", "api_handler")
    log_performance_metric("memory_usage", 512.0, "MB", "system")

    # 测试审计日志
    log_audit_event("create_guideline", "guideline:123", user_id, success=True)
    log_audit_event("delete_task", "task:456", user_id, success=False, error="Permission denied")

    print("  [OK] 专门日志函数测试完成")


async def test_error_logging():
    """测试错误日志"""
    print("\n[FAIL] 测试错误日志...")

    try:
        # 故意引发一个异常
        raise ValueError("这是一个测试异常")
    except Exception as e:
        logger.error("捕获到测试异常", exception=e)
        logger.critical("这是一个严重错误", exception=e, context=LogContext(
            component="error_test",
            category=LogCategory.SYSTEM,
            tags={"error_code": "TEST_ERROR"}
        ))

    print("  [OK] 错误日志测试完成")


async def test_log_configuration():
    """测试日志配置"""
    print("\n⚙️  测试日志配置...")

    settings = get_settings()

    # 显示当前配置
    print(f"  日志级别: {settings.LOG_LEVEL}")
    print(f"  JSON格式: {settings.LOG_JSON_FORMAT}")
    print(f"  彩色输出: {settings.LOG_ENABLE_COLORS}")
    print(f"  结构化日志: {settings.LOG_STRUCTURED}")
    print(f"  日志文件: {settings.LOG_FILE_PATH or '未配置'}")

    # 测试不同级别的日志
    test_logger = get_logger("config_test")
    test_logger.setLevel("DEBUG")

    test_logger.debug("调试级别日志 - 应该显示")
    test_logger.info("信息级别日志 - 应该显示")
    test_logger.warning("警告级别日志 - 应该显示")
    test_logger.error("错误级别日志 - 应该显示")

    print("  [OK] 日志配置测试完成")


async def test_log_performance():
    """测试日志性能"""
    print("\n⚡ 测试日志性能...")

    test_logger = get_logger("performance_test")
    num_logs = 1000

    start_time = time.time()
    for i in range(num_logs):
        test_logger.info(f"性能测试日志 {i}", context=LogContext(
            request_id=str(uuid.uuid4()),
            component="performance_test",
            tags={"iteration": i}
        ))

    end_time = time.time()
    duration = end_time - start_time
    logs_per_second = num_logs / duration

    print(f"  记录 {num_logs} 条日志用时: {duration:.3f}秒")
    print(f"  日志性能: {logs_per_second:.0f} 条/秒")

    if logs_per_second > 1000:
        print("  [OK] 日志性能良好")
    elif logs_per_second > 500:
        print("  [WARN]  日志性能一般")
    else:
        print("  [FAIL] 日志性能较差")


async def generate_log_samples():
    """生成日志样本"""
    print("\n📄 生成日志样本...")

    # 生成各种类型的日志样本
    samples = [
        ("system_startup", "CPG2PVG-AI系统启动", LogCategory.SYSTEM),
        ("user_registration", "用户注册成功", LogCategory.USER),
        ("api_request", "处理API请求", LogCategory.API),
        ("database_query", "执行数据库查询", LogCategory.DATABASE),
        ("cache_hit", "缓存命中", LogCategory.CACHE),
        ("security_event", "安全事件检测", LogCategory.SECURITY),
        ("workflow_start", "工作流开始", LogCategory.WORKFLOW),
        ("llm_call", "LLM模型调用", LogCategory.LLM),
        ("file_upload", "文件上传", LogCategory.FILE_STORAGE),
        ("performance_metric", "性能指标", LogCategory.PERFORMANCE),
        ("business_event", "业务事件", LogCategory.BUSINESS),
    ]

    for sample_id, message, category in samples:
        logger.info(
            message,
            context=LogContext(
                request_id=str(uuid.uuid4()),
                component="sample_generator",
                category=category,
                tags={"sample_id": sample_id, "timestamp": time.time()}
            )
        )

    print("  [OK] 日志样本生成完成")


async def main():
    """主函数"""
    print("[LIST] CPG2PVG-AI 日志系统设置")
    print("=" * 50)

    # 显示日志配置信息
    settings = get_settings()
    print(f"日志配置:")
    print(f"  级别: {settings.LOG_LEVEL}")
    print(f"  格式: {'JSON' if settings.LOG_JSON_FORMAT else 'Plain Text'}")
    print(f"  彩色: {'是' if settings.LOG_ENABLE_COLORS else '否'}")
    print(f"  文件: {settings.LOG_FILE_PATH or '控制台'}")
    print(f"  结构化: {'是' if settings.LOG_STRUCTURED else '否'}")
    print()

    # 运行各项测试
    await test_basic_logging()
    await test_context_logging()
    await test_context_manager()
    await test_specialized_logging()
    await test_error_logging()
    await test_log_configuration()
    await test_log_performance()
    await generate_log_samples()

    print("\n[SUCCESS] 日志系统设置完成！")
    print("\n[LIST] 使用建议:")
    print("1. 在生产环境中使用JSON格式日志")
    print("2. 配置日志文件路径进行持久化存储")
    print("3. 使用专门的日志函数记录特定事件")
    print("4. 利用上下文管理器跟踪请求链路")
    print("5. 监控日志性能，避免过度日志记录")
    print("6. 配置日志聚合和监控系统")
    print("7. 定期清理旧日志文件")
    print("8. 确保敏感信息不被记录到日志中")

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)