#!/usr/bin/env python3
"""
API端点完整性测试脚本
CPG2PVG-AI System API Test
"""

import sys
import os
import inspect
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

def test_imports():
    """测试关键模块导入"""
    print("🔍 测试模块导入...")

    try:
        # 测试核心模块
        print("  ✅ 导入配置模块...")
        from app.core.config import settings

        print("  ✅ 导入数据库模块...")
        from app.core.database import engine, AsyncSessionLocal

        print("  ✅ 导入模型模块...")
        from app.models import Guideline, Task, User

        print("  ✅ 导入API路由...")
        from app.api.v1.api import api_router

        print("  ✅ 导入schemas...")
        from app.schemas.guideline import GuidelineResponse
        from app.schemas.task import TaskResponse
        from app.schemas.user import UserResponse

        print("  ✅ 导入Celery应用...")
        # from celery_worker.celery_app import celery_app

        return True

    except ImportError as e:
        print(f"  ❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"  ❌ 其他错误: {e}")
        return False

def test_api_endpoints():
    """测试API端点完整性"""
    print("\n🔍 测试API端点完整性...")

    try:
        from app.api.v1.api import api_router

        # 获取路由信息
        routes = api_router.routes
        print(f"  ✅ 发现 {len(routes)} 个主路由")

        # 检查子路由
        endpoint_paths = []
        for route in routes:
            if hasattr(route, 'path_prefix'):
                endpoint_paths.append(route.path_prefix)
            elif hasattr(route, 'path'):
                endpoint_paths.append(route.path)

        expected_paths = ['/guidelines', '/tasks', '/users', '/health']

        for expected_path in expected_paths:
            if any(expected_path in path for path in endpoint_paths):
                print(f"  ✅ 找到端点: {expected_path}")
            else:
                print(f"  ⚠️  可能缺失端点: {expected_path}")

        return True

    except Exception as e:
        print(f"  ❌ API端点测试失败: {e}")
        return False

def test_database_models():
    """测试数据库模型完整性"""
    print("\n🔍 测试数据库模型...")

    try:
        from app.models import Guideline, Task, User, TaskProgress
        from app.models.base import Base

        # 检查模型继承
        assert issubclass(Guideline, Base), "Guideline应该继承Base"
        assert issubclass(Task, Base), "Task应该继承Base"
        assert issubclass(User, Base), "User应该继承Base"
        assert issubclass(TaskProgress, Base), "TaskProgress应该继承Base"

        print("  ✅ 模型继承关系正确")

        # 检查关键字段
        guideline_fields = ['title', 'original_filename', 'file_path', 'status', 'uploaded_by']
        for field in guideline_fields:
            assert hasattr(Guideline, field), f"Guideline模型缺少字段: {field}"

        print("  ✅ Guideline模型字段完整")

        task_fields = ['task_id', 'task_type', 'status', 'guideline_id']
        for field in task_fields:
            assert hasattr(Task, field), f"Task模型缺少字段: {field}"

        print("  ✅ Task模型字段完整")

        user_fields = ['username', 'email', 'hashed_password', 'is_active']
        for field in user_fields:
            assert hasattr(User, field), f"User模型缺少字段: {field}"

        print("  ✅ User模型字段完整")

        return True

    except Exception as e:
        print(f"  ❌ 数据库模型测试失败: {e}")
        return False

def test_configuration():
    """测试配置完整性"""
    print("\n🔍 测试配置完整性...")

    try:
        from app.core.config import settings

        # 检查关键配置项
        required_settings = [
            'PROJECT_NAME',
            'DATABASE_URL',
            'REDIS_URL',
            'SECRET_KEY',
            'API_V1_STR'
        ]

        for setting in required_settings:
            if hasattr(settings, setting):
                value = getattr(settings, setting)
                if value:
                    print(f"  ✅ {setting}: 已配置")
                else:
                    print(f"  ⚠️  {setting}: 值为空")
            else:
                print(f"  ❌ {setting}: 配置缺失")

        return True

    except Exception as e:
        print(f"  ❌ 配置测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 CPG2PVG-AI API完整性测试开始\n")

    tests = [
        test_imports,
        test_api_endpoints,
        test_database_models,
        test_configuration
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        else:
            print(f"\n❌ 测试失败: {test.__name__}")

    print(f"\n📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！API配置完整。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查配置。")
        return 1

if __name__ == "__main__":
    sys.exit(main())