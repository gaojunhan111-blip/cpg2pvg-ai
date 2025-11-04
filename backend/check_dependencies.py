"""
检查和修复导入依赖问题
Check and fix import dependencies
"""

import os
import sys
import importlib
from pathlib import Path
import re

def check_imports(file_path: Path):
    """检查文件中的导入"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取导入语句
    import_patterns = [
        r'from ([\w\.]+) import',
        r'import ([\w\.]+)',
    ]

    imports = []
    for pattern in import_patterns:
        matches = re.findall(pattern, content)
        imports.extend(matches)

    return imports

def fix_missing_imports():
    """修复缺失的导入"""
    app_dir = Path(__file__).parent / 'app'

    # 关键文件的导入检查
    critical_files = [
        'core/auth.py',
        'core/error_handling.py',
        'core/llm_client.py',
        'main.py',
        'api/v1/endpoints/auth.py',
        'services/slow_workflow_orchestrator.py'
    ]

    missing_modules = []

    for file_path in critical_files:
        full_path = app_dir / file_path
        if full_path.exists():
            try:
                imports = check_imports(full_path)
                for imp in imports:
                    # 检查是否是本地导入
                    if imp.startswith('app.'):
                        module_path = imp.replace('.', '/') + '.py'
                        if not (app_dir / module_path).exists():
                            missing_modules.append(imp)
                    else:
                        # 检查第三方模块
                        try:
                            importlib.import_module(imp)
                        except ImportError:
                            missing_modules.append(imp)
            except Exception as e:
                print(f"检查 {file_path} 时出错: {e}")

    return missing_modules

def create_missing_modules():
    """创建缺失的本地模块"""
    app_dir = Path(__file__).parent / 'app'

    # 需要创建的模块
    required_modules = [
        'services/performance_optimizer.py',
        'services/quality_controller.py',
        'services/progressive_generator.py',
        'services/hierarchical_parser.py',
        'services/multimodal_processor.py',
    ]

    for module_path in required_modules:
        full_path = app_dir / module_path
        if not full_path.exists():
            print(f"创建缺失模块: {module_path}")

            # 创建目录
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # 创建基础模块内容
            module_name = full_path.stem
            class_name = ''.join(word.capitalize() for word in module_name.split('_')) + 'Service'

            content = f'''"""
{module_name} 服务模块
{module_name.capitalize()} Service Module
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from app.core.logger import get_logger
from app.core.error_handling import CPG2PVGException, retry, DEFAULT_RETRY_CONFIG

logger = get_logger(__name__)


@dataclass
class {class_name}Config:
    """{module_name}配置"""
    enabled: bool = True
    timeout: int = 300
    max_retries: int = 3


class {class_name}:
    """{module_name}服务"""

    def __init__(self, config: Optional[{class_name}Config] = None):
        self.config = config or {class_name}Config()
        logger.info(f"{class_name} 初始化完成")

    @retry(config=DEFAULT_RETRY_CONFIG)
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理数据

        Args:
            data: 输入数据

        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            logger.info(f"开始{module_name}处理")

            # TODO: 实现具体的处理逻辑
            result = {{
                "status": "success",
                "processed": True,
                "data": data
            }}

            logger.info(f"{module_name}处理完成")
            return result

        except Exception as e:
            logger.error(f"{module_name}处理失败: {{str(e)}}")
            raise CPG2PVGException(
                message=f"{module_name}处理失败: {{str(e)}}",
                category="business_logic",
                severity="medium"
            )

    async def validate_input(self, data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        # TODO: 实现输入验证逻辑
        return True

    async def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {{
            "service": "{module_name}",
            "enabled": self.config.enabled,
            "status": "running"
        }}


# 全局实例
{module_name}_service = {class_name}()


def get_{module_name}_service() -> {class_name}:
    """获取{module_name}服务实例"""
    return {module_name}_service
'''

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

    print("缺失模块创建完成")

def main():
    """主函数"""
    print("开始检查导入依赖...")

    # 检查缺失的模块
    missing_modules = fix_missing_imports()

    if missing_modules:
        print(f"发现缺失的模块: {missing_modules}")
    else:
        print("所有模块导入正常")

    # 创建缺失的本地模块
    create_missing_modules()

    print("依赖检查完成!")

if __name__ == "__main__":
    main()