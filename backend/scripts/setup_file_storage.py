#!/usr/bin/env python3
"""
文件存储服务设置脚本
File Storage Service Setup Script
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.minio_setup import main as setup_minio_main


async def main():
    """主函数"""
    print("[FILE] CPG2PVG-AI 文件存储服务设置")
    print("=" * 50)

    # 检查环境变量
    required_env_vars = [
        "MINIO_ENDPOINT",
        "MINIO_ACCESS_KEY",
        "MINIO_SECRET_KEY",
        "MINIO_BUCKET_NAME"
    ]

    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"[FAIL] 缺少必需的环境变量: {', '.join(missing_vars)}")
        print("请设置以下环境变量:")
        for var in missing_vars:
            print(f"  export {var}=your_value")
        return False

    print("[OK] 环境变量检查通过")
    print()

    # 运行MinIO设置
    success = await setup_minio_main()

    if success:
        print("\n[SUCCESS] 文件存储服务设置完成！")
        print("\n[LIST] 下一步:")
        print("1. 启动应用服务: python -m app.main")
        print("2. 测试文件上传API")
        print("3. 检查MinIO控制台")
    else:
        print("\n[FAIL] 文件存储服务设置失败")
        print("请检查配置和服务状态")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)