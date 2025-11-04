"""
测试导入修复
Test import fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_core_imports():
    """测试核心模块导入"""
    try:
        # 测试基础模块
        from app.core.config import get_settings
        from app.core.logger import get_logger
        from app.core.error_handling import CPG2PVGException
        print("核心基础模块导入成功")

        # 测试服务模块
        from app.services.performance_optimizer import get_performance_optimizer_service
        from app.services.hierarchical_parser import get_hierarchical_parser_service
        print("服务模块导入成功")

        return True
    except Exception as e:
        print(f"核心模块导入失败: {e}")
        return False

def test_api_imports():
    """测试API模块导入"""
    try:
        from app.api.v1.endpoints.files import router as files_router
        print("API端点模块导入成功")
        return True
    except Exception as e:
        print(f"API模块导入失败: {e}")
        return False

def main():
    """主函数"""
    print("开始测试导入修复...")

    success = True
    success &= test_core_imports()
    success &= test_api_imports()

    if success:
        print("所有导入修复验证成功!")
    else:
        print("部分导入仍有问题")

    return success

if __name__ == "__main__":
    main()