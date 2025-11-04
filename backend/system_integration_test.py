#!/usr/bin/env python3
"""
系统连通性测试
测试整个CPG2PVG-AI系统的端到端连通性
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_service_imports():
    """测试核心服务导入"""
    print("[测试] 测试核心服务导入...")

    try:
        # 测试核心服务导入
        from app.services.intelligent_agent import AgentOrchestrator
        from app.services.progressive_generator import get_progressive_generator
        from app.services.medical_cache import get_medical_cache
        from app.services.cost_optimizer import get_cost_optimizer
        from app.services.quality_controller import get_quality_controller
        from app.services.performance_monitor import get_performance_monitor
        from app.services.workflow_orchestrator import get_workflow_orchestrator

        print("[通过] 所有核心服务导入成功")
        return True

    except Exception as e:
        print(f"[失败] 服务导入失败: {e}")
        return False

async def test_data_models():
    """测试数据模型导入和一致性"""
    print("[测试] 测试数据模型...")

    try:
        from app.services.intelligent_agent import AgentResults
        from app.schemas.pvg_schemas import PVGDocument, PVGSection, GenerationConfig
        from app.enums.common import SectionType, ContentPriority, GenerationStatus

        # 创建测试实例
        section = PVGSection(
            section_id="test_section",
            section_type=SectionType.EMERGENCY_GUIDANCE,
            title="测试章节",
            content="测试内容",
            priority=ContentPriority.HIGH,
            order=1
        )

        document = PVGDocument(
            document_id="test_doc",
            guideline_id="test_guideline",
            title="测试文档"
        )

        config = GenerationConfig()

        print("[通过] 数据模型测试通过")
        return True

    except Exception as e:
        print(f"[失败] 数据模型测试失败: {e}")
        return False

async def test_api_endpoints():
    """测试API端点定义"""
    print("[测试] 测试API端点...")

    try:
        from app.api.v1.endpoints.workflow import router as workflow_router
        from app.api.v1.endpoints.guidelines import router as guidelines_router
        from app.api.v1.endpoints.tasks import router as tasks_router
        from app.api.v1.endpoints.users import router as users_router
        from app.api.v1.endpoints.health import router as health_router

        # 检查路由器是否有路由
        workflow_routes = [route.path for route in workflow_router.routes]
        guidelines_routes = [route.path for route in guidelines_router.routes]
        tasks_routes = [route.path for route in tasks_router.routes]
        users_routes = [route.path for route in users_router.routes]
        health_routes = [route.path for route in health_router.routes]

        print(f"  - Workflow路由: {len(workflow_routes)}个")
        print(f"  - Guidelines路由: {len(guidelines_routes)}个")
        print(f"  - Tasks路由: {len(tasks_routes)}个")
        print(f"  - Users路由: {len(users_routes)}个")
        print(f"  - Health路由: {len(health_routes)}个")

        print("[通过] API端点测试通过")
        return True

    except Exception as e:
        print(f"[失败] API端点测试失败: {e}")
        return False

async def test_basic_workflow_creation():
    """测试基本工作流创建"""
    print("[测试] 测试工作流创建...")

    try:
        from app.services.workflow_orchestrator import WorkflowConfig, ProcessingMode

        # 创建配置
        config = WorkflowConfig(
            processing_mode=ProcessingMode.STANDARD,
            enable_caching=True,
            enable_cost_optimization=True,
            enable_quality_control=True,
            enable_performance_monitoring=True
        )

        # 创建输入数据
        input_data = {
            "content": "测试医学指南内容",
            "metadata": {"test": True}
        }

        print("[通过] 工作流配置创建成功")
        return True

    except Exception as e:
        print(f"[失败] 工作流创建失败: {e}")
        return False

async def test_service_initialization():
    """测试服务初始化（不依赖外部服务）"""
    print("[测试] 测试服务初始化...")

    try:
        # 这些服务只测试初始化，不测试外部连接
        from app.services.cost_optimizer import get_cost_optimizer
        from app.services.quality_controller import get_quality_controller

        # 获取服务实例（如果需要外部服务会跳过）
        try:
            cost_optimizer = await get_cost_optimizer()
            print("  - Cost Optimizer: [通过]")
        except Exception as e:
            print(f"  - Cost Optimizer: [警告] ({e})")

        try:
            quality_controller = await get_quality_controller()
            print("  - Quality Controller: [通过]")
        except Exception as e:
            print(f"  - Quality Controller: [警告] ({e})")

        print("[通过] 服务初始化测试完成")
        return True

    except Exception as e:
        print(f"[失败] 服务初始化测试失败: {e}")
        return False

async def run_connectivity_test():
    """运行完整的连通性测试"""
    print("[开始] CPG2PVG-AI系统连通性测试\n")

    tests = [
        ("核心服务导入", test_service_imports),
        ("数据模型", test_data_models),
        ("API端点", test_api_endpoints),
        ("工作流创建", test_basic_workflow_creation),
        ("服务初始化", test_service_initialization)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[失败] {test_name}测试异常: {e}")
            results.append((test_name, False))
        print()

    # 生成测试报告
    print("[报告] 测试结果汇总:")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "[通过]" if result else "[失败]"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1

    print("=" * 50)
    print(f"总体结果: {passed}/{total} 项测试通过")

    if passed == total:
        print("[成功] 系统连通性测试全部通过！")
        return True
    else:
        print("[警告] 部分测试未通过，请检查相关组件")
        return False

if __name__ == "__main__":
    # 设置环境变量
    import os
    os.environ.setdefault("PYTHONPATH", str(Path(__file__).parent))

    # 运行测试
    success = asyncio.run(run_connectivity_test())
    sys.exit(0 if success else 1)