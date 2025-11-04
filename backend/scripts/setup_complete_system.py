#!/usr/bin/env python3
"""
完整系统设置脚本
Complete System Setup Script
"""

import asyncio
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class SystemSetup:
    """系统设置管理器"""

    def __init__(self):
        self.settings = get_settings()
        self.setup_results: List[Tuple[str, bool, str]] = []

    def log_result(self, component: str, success: bool, message: str):
        """记录设置结果"""
        self.setup_results.append((component, success, message))
        status = "[OK]" if success else "[FAIL]"
        logger.info(f"{status} {component}: {message}")

    async def check_environment(self) -> bool:
        """检查环境要求"""
        print("[SEARCH] 检查环境要求...")

        try:
            # 检查Python版本
            python_version = sys.version_info
            if python_version < (3, 8):
                self.log_result(
                    "Python版本",
                    False,
                    f"Python {python_version.major}.{python_version.minor} 不满足要求 (需要 >= 3.8)"
                )
                return False
            else:
                self.log_result(
                    "Python版本",
                    True,
                    f"Python {python_version.major}.{python_version.minor}.{python_version.micro}"
                )

            # 检查必需的环境变量
            required_vars = [
                "DATABASE_URL",
                "REDIS_URL",
                "SECRET_KEY"
            ]

            missing_vars = []
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)

            if missing_vars:
                self.log_result(
                    "环境变量",
                    False,
                    f"缺少环境变量: {', '.join(missing_vars)}"
                )
            else:
                self.log_result("环境变量", True, "所有必需环境变量已设置")

            return len(missing_vars) == 0

        except Exception as e:
            self.log_result("环境检查", False, f"检查失败: {e}")
            return False

    async def install_dependencies(self) -> bool:
        """安装依赖"""
        print("\n[PACKAGE] 安装Python依赖...")

        try:
            requirements_file = project_root / "requirements.txt"
            if not requirements_file.exists():
                self.log_result("依赖安装", False, "requirements.txt文件不存在")
                return False

            # 安装依赖
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], capture_output=True, text=True, cwd=project_root)

            if result.returncode == 0:
                self.log_result("依赖安装", True, "所有依赖安装成功")
                return True
            else:
                self.log_result("依赖安装", False, f"安装失败: {result.stderr}")
                return False

        except Exception as e:
            self.log_result("依赖安装", False, f"安装过程出错: {e}")
            return False

    async def setup_database(self) -> bool:
        """设置数据库"""
        print("\n[DB]  设置数据库...")

        try:
            # 运行数据库迁移
            result = subprocess.run([
                sys.executable, "-m", "alembic", "upgrade", "head"
            ], capture_output=True, text=True, cwd=project_root)

            if result.returncode == 0:
                self.log_result("数据库迁移", True, "数据库迁移成功")
                return True
            else:
                self.log_result("数据库迁移", False, f"迁移失败: {result.stderr}")
                return False

        except Exception as e:
            self.log_result("数据库设置", False, f"设置过程出错: {e}")
            return False

    async def setup_redis(self) -> bool:
        """设置Redis"""
        print("\n[REDIS] 设置Redis...")

        try:
            # 这里可以添加Redis连接测试
            import redis.asyncio as redis_client
            redis = redis_client.from_url(self.settings.REDIS_URL)

            # 测试连接
            await redis.ping()
            await redis.close()

            self.log_result("Redis连接", True, "Redis连接测试成功")
            return True

        except Exception as e:
            self.log_result("Redis连接", False, f"Redis连接失败: {e}")
            return False

    async def setup_file_storage(self) -> bool:
        """设置文件存储"""
        print("\n[FILE] 设置文件存储...")

        try:
            # 运行MinIO设置脚本
            script_path = project_root / "scripts" / "setup_file_storage.py"
            result = subprocess.run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True, cwd=project_root)

            if result.returncode == 0:
                self.log_result("文件存储", True, "MinIO文件存储设置成功")
                return True
            else:
                self.log_result("文件存储", False, f"MinIO设置失败: {result.stderr}")
                return False

        except Exception as e:
            self.log_result("文件存储", False, f"文件存储设置出错: {e}")
            return False

    async def setup_llm_providers(self) -> bool:
        """设置LLM提供商"""
        print("\n[AI] 设置LLM提供商...")

        try:
            # 运行LLM提供商设置脚本
            script_path = project_root / "scripts" / "setup_llm_providers.py"
            result = subprocess.run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True, cwd=project_root)

            if result.returncode == 0:
                self.log_result("LLM提供商", True, "LLM提供商设置成功")
                return True
            else:
                self.log_result("LLM提供商", False, f"LLM提供商设置失败: {result.stderr}")
                return False

        except Exception as e:
            self.log_result("LLM提供商", False, f"LLM提供商设置出错: {e}")
            return False

    async def setup_security(self) -> bool:
        """设置安全系统"""
        print("\n[SECURITY] 设置安全系统...")

        try:
            # 运行安全设置脚本
            script_path = project_root / "scripts" / "setup_security.py"
            result = subprocess.run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True, cwd=project_root)

            if result.returncode == 0:
                self.log_result("安全系统", True, "安全系统设置成功")
                return True
            else:
                self.log_result("安全系统", False, f"安全系统设置失败: {result.stderr}")
                return False

        except Exception as e:
            self.log_result("安全系统", False, f"安全系统设置出错: {e}")
            return False

    async def setup_logging(self) -> bool:
        """设置日志系统"""
        print("\n[LIST] 设置日志系统...")

        try:
            # 运行日志设置脚本
            script_path = project_root / "scripts" / "setup_logging.py"
            result = subprocess.run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True, cwd=project_root)

            if result.returncode == 0:
                self.log_result("日志系统", True, "日志系统设置成功")
                return True
            else:
                self.log_result("日志系统", False, f"日志系统设置失败: {result.stderr}")
                return False

        except Exception as e:
            self.log_result("日志系统", False, f"日志系统设置出错: {e}")
            return False

    async def test_system_health(self) -> bool:
        """测试系统健康状态"""
        print("\n[HEALTH] 测试系统健康状态...")

        try:
            # 测试数据库连接
            from app.core.database import engine
            async with engine.begin() as conn:
                await conn.execute("SELECT 1")
            self.log_result("数据库健康检查", True, "数据库连接正常")

            # 测试Redis连接
            import redis.asyncio as redis_client
            redis = redis_client.from_url(self.settings.REDIS_URL)
            await redis.ping()
            await redis.close()
            self.log_result("Redis健康检查", True, "Redis连接正常")

            # 测试日志系统
            test_logger = get_logger("health_check")
            test_logger.info("系统健康检查日志")
            self.log_result("日志系统健康检查", True, "日志系统正常")

            return True

        except Exception as e:
            self.log_result("系统健康检查", False, f"健康检查失败: {e}")
            return False

    def print_summary(self):
        """打印设置总结"""
        print("\n" + "="*60)
        print("[METRICS] 系统设置总结")
        print("="*60)

        success_count = sum(1 for _, success, _ in self.setup_results if success)
        total_count = len(self.setup_results)

        for component, success, message in self.setup_results:
            status = "[OK]" if success else "[FAIL]"
            print(f"{status} {component}: {message}")

        print(f"\n设置结果: {success_count}/{total_count} 成功")

        if success_count == total_count:
            print("\n[SUCCESS] CPG2PVG-AI系统设置完成！")
            print("\n[LIST] 下一步:")
            print("1. 启动应用服务: python -m app.main")
            print("2. 启动Celery Worker: celery -A app.core.celery worker --loglevel=info")
            print("3. 启动Celery Beat: celery -A app.core.celery beat --loglevel=info")
            print("4. 访问API文档: http://localhost:8000/docs")
            print("5. 监控系统运行状态")
        else:
            print("\n[WARN]  系统设置未完全成功，请检查失败的组件")
            print("建议:")
            print("1. 检查环境变量配置")
            print("2. 确保外部服务（数据库、Redis、MinIO）正在运行")
            print("3. 检查网络连接和权限")
            print("4. 查看详细错误日志")

        print("\n📖 更多文档:")
        print("- README.md: 项目说明")
        print("- docs/: 详细文档")
        print("- config/: 配置示例")

    async def run_setup(self, skip_deps: bool = False):
        """运行完整设置"""
        print("[START] CPG2PVG-AI 系统完整设置")
        print("="*60)

        # 1. 检查环境
        env_ok = await self.check_environment()
        if not env_ok:
            print("[FAIL] 环境检查失败，请修复后重试")
            return False

        # 2. 安装依赖（可选）
        if not skip_deps:
            deps_ok = await self.install_dependencies()
            if not deps_ok:
                print("[WARN]  依赖安装失败，但继续设置...")

        # 3. 设置数据库
        db_ok = await self.setup_database()
        if not db_ok:
            print("[FAIL] 数据库设置失败")
            return False

        # 4. 设置Redis
        redis_ok = await self.setup_redis()
        if not redis_ok:
            print("[FAIL] Redis设置失败")
            return False

        # 5. 设置文件存储
        storage_ok = await self.setup_file_storage()

        # 6. 设置LLM提供商
        llm_ok = await self.setup_llm_providers()

        # 7. 设置安全系统
        security_ok = await self.setup_security()

        # 8. 设置日志系统
        logging_ok = await self.setup_logging()

        # 9. 测试系统健康状态
        health_ok = await self.test_system_health()

        # 打印总结
        self.print_summary()

        # 返回总体成功状态
        core_success = env_ok and db_ok and redis_ok and logging_ok
        return core_success


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="CPG2PVG-AI系统设置脚本")
    parser.add_argument("--skip-deps", action="store_true", help="跳过依赖安装")
    args = parser.parse_args()

    setup = SystemSetup()
    success = await setup.run_setup(skip_deps=args.skip_deps)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())