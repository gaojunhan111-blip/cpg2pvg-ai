"""
测试main.py修复
Test main.py fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.main import create_application
    print("main.py 导入成功")

    # 创建应用实例
    app = create_application()
    print("FastAPI应用创建成功")

    # 检查路由
    routes = [route.path for route in app.routes]
    print(f"已注册的路由: {routes}")

    print("main.py 修复验证成功!")

except Exception as e:
    print(f"main.py 验证失败: {e}")
    import traceback
    traceback.print_exc()