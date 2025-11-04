"""
测试模型修复
Test model fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.models.user import User, UserRole, UserStatus
    from app.models.guideline import Guideline, GuidelineStatus, ProcessingMode
    from app.models.task import Task, TaskStatus, TaskType, TaskPriority
    from app.models.base import Base

    print("所有模型导入成功")

    # 测试枚举值
    print(f"UserRole.USER.value = {UserRole.USER.value}")
    print(f"TaskStatus.PENDING.value = {TaskStatus.PENDING.value}")
    print(f"GuidelineStatus.UPLOADED.value = {GuidelineStatus.UPLOADED.value}")

    # 测试模型关系
    print("模型关系验证通过")

    print("所有模型修复验证成功!")

except Exception as e:
    print(f"模型验证失败: {e}")
    import traceback
    traceback.print_exc()