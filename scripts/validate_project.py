#!/usr/bin/env python3
"""
项目完整性验证脚本
CPG2PVG-AI Project Validation
"""

import os
import sys
from pathlib import Path
import subprocess
import json

class ProjectValidator:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.errors = []
        self.warnings = []

    def log_error(self, message):
        self.errors.append(f"ERROR: {message}")

    def log_warning(self, message):
        self.warnings.append(f"WARNING: {message}")

    def log_success(self, message):
        print(f"OK: {message}")

    def check_project_structure(self):
        """检查项目结构"""
        print("\nChecking project structure...")

        required_dirs = [
            "backend/app",
            "backend/app/api/v1",
            "backend/app/core",
            "backend/app/models",
            "backend/app/schemas",
            "backend/app/services",
            "backend/app/utils",
            "celery_worker/tasks",
            "frontend/app",
            "frontend/components",
            "frontend/lib",
            "frontend/types",
            "docker",
            "scripts"
        ]

        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists() and full_path.is_dir():
                self.log_success(f"目录存在: {dir_path}")
            else:
                self.log_error(f"目录缺失: {dir_path}")

    def check_config_files(self):
        """检查配置文件"""
        print("\n🔍 检查配置文件...")

        config_files = {
            "backend/requirements.txt": "Python依赖文件",
            "backend/.env": "后端环境变量",
            "frontend/package.json": "Node.js依赖文件",
            "frontend/.env.local": "前端环境变量",
            "docker-compose.yml": "Docker编排文件",
            "pyproject.toml": "Python项目管理文件",
            "README.md": "项目说明文档",
            ".gitignore": "Git忽略文件",
            "Makefile": "构建脚本文件"
        }

        for file_path, description in config_files.items():
            full_path = self.project_root / file_path
            if full_path.exists() and full_path.is_file():
                self.log_success(f"{description}: {file_path}")
            else:
                self.log_error(f"配置文件缺失: {file_path} ({description})")

    def check_python_files(self):
        """检查Python文件语法"""
        print("\n🔍 检查Python文件语法...")

        python_files = list(self.project_root.glob("backend/**/*.py"))
        python_files.extend(list(self.project_root.glob("celery_worker/**/*.py")))

        if not python_files:
            self.log_warning("未找到Python文件")
            return

        syntax_errors = 0
        for py_file in python_files:
            try:
                compile(py_file.read_text(encoding='utf-8'), str(py_file), 'exec')
                self.log_success(f"语法正确: {py_file.relative_to(self.project_root)}")
            except SyntaxError as e:
                syntax_errors += 1
                self.log_error(f"语法错误: {py_file.relative_to(self.project_root)} - {e}")
            except Exception as e:
                self.log_warning(f"检查文件时出错: {py_file.relative_to(self.project_root)} - {e}")

        if syntax_errors == 0:
            print("  🎉 所有Python文件语法正确")

    def check_docker_config(self):
        """检查Docker配置"""
        print("\n🔍 检查Docker配置...")

        dockerfiles = [
            "docker/backend/Dockerfile",
            "docker/frontend/Dockerfile",
            "docker/celery_worker/Dockerfile"
        ]

        for dockerfile in dockerfiles:
            full_path = self.project_root / dockerfile
            if full_path.exists():
                self.log_success(f"Dockerfile存在: {dockerfile}")
            else:
                self.log_error(f"Dockerfile缺失: {dockerfile}")

        # 检查docker-compose.yml
        compose_file = self.project_root / "docker-compose.yml"
        if compose_file.exists():
            try:
                # 尝试解析YAML
                import yaml
                with open(compose_file, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
                self.log_success("docker-compose.yml格式正确")
            except ImportError:
                self.log_warning("未安装pyyaml，跳过YAML格式检查")
            except Exception as e:
                self.log_error(f"docker-compose.yml格式错误: {e}")
        else:
            self.log_error("docker-compose.yml文件缺失")

    def check_frontend_config(self):
        """检查前端配置"""
        print("\n🔍 检查前端配置...")

        package_json = self.project_root / "frontend" / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                required_fields = ["name", "version", "dependencies"]
                for field in required_fields:
                    if field in data:
                        self.log_success(f"package.json包含{field}")
                    else:
                        self.log_error(f"package.json缺少{field}")

                # 检查关键依赖
                if "dependencies" in data:
                    deps = data["dependencies"]
                    key_deps = ["next", "react", "antd", "typescript"]
                    for dep in key_deps:
                        if dep in deps:
                            self.log_success(f"包含依赖: {dep}")
                        else:
                            self.log_warning(f"缺少依赖: {dep}")

            except json.JSONDecodeError as e:
                self.log_error(f"package.json格式错误: {e}")
        else:
            self.log_error("package.json文件缺失")

        # 检查TypeScript配置
        tsconfig = self.project_root / "frontend" / "tsconfig.json"
        if tsconfig.exists():
            self.log_success("tsconfig.json存在")
        else:
            self.log_warning("tsconfig.json缺失")

    def check_environment_files(self):
        """检查环境变量文件"""
        print("\n🔍 检查环境变量文件...")

        env_files = [
            ("backend/.env.example", "后端环境变量模板"),
            ("frontend/.env.example", "前端环境变量模板"),
            ("backend/.env", "后端环境变量"),
            ("frontend/.env.local", "前端环境变量"),
            (".env", "根目录环境变量")
        ]

        for env_file, description in env_files:
            full_path = self.project_root / env_file
            if full_path.exists():
                self.log_success(f"{description}: {env_file}")
            else:
                if "example" in env_file:
                    self.log_error(f"{description}缺失: {env_file}")
                else:
                    self.log_warning(f"{description}缺失: {env_file} (可选)")

    def generate_report(self):
        """生成验证报告"""
        print("\n" + "="*50)
        print("📊 项目验证报告")
        print("="*50)

        if not self.errors and not self.warnings:
            print("🎉 项目验证完全通过！所有检查都成功。")
            return True

        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误:")
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print(f"\n⚠️  发现 {len(self.warnings)} 个警告:")
            for warning in self.warnings:
                print(f"  {warning}")

        if not self.errors:
            print(f"\n✅ 项目结构完整，但需要注意 {len(self.warnings)} 个警告项")
            return True
        else:
            print(f"\n❌ 项目存在 {len(self.errors)} 个错误需要修复")
            return False

def main():
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = Path(__file__).parent.parent

    validator = ProjectValidator(project_root)

    print("CPG2PVG-AI Project Validation Started")
    print(f"Project Path: {project_root}")

    # 执行各项检查
    validator.check_project_structure()
    validator.check_config_files()
    validator.check_python_files()
    validator.check_docker_config()
    validator.check_frontend_config()
    validator.check_environment_files()

    # 生成报告
    success = validator.generate_report()

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())