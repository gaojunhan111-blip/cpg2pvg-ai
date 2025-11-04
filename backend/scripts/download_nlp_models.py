#!/usr/bin/env python3
"""
NLP模型下载脚本
Download NLP Models Script
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def print_colored(message: str, color: str = "white"):
    """打印彩色消息"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, colors['white'])}{message}{colors['reset']}")


def download_nltk_data():
    """下载NLTK数据"""
    print_colored("🔤 下载NLTK数据...", "cyan")

    try:
        import nltk

        # 必需的NLTK数据包
        required_packages = [
            'punkt',  # 分词器
            'stopwords',  # 停用词
            'wordnet',   # 词汇数据库
        ]

        # 可选的NLTK数据包（用于更高级的NLP功能）
        optional_packages = [
            'averaged_perceptron_tagger',  # 词性标注
            'maxent_ne_chunker',          # 命名实体识别
            'words',                       # 单词列表
        ]

        print("  下载必需包...")
        for package in required_packages:
            try:
                nltk.data.find(f'tokenizers/{package}')
                print(f"    ✅ {package} - 已存在")
            except LookupError:
                print(f"    📥 下载 {package}...")
                nltk.download(package)

        print("  下载可选包...")
        for package in optional_packages:
            try:
                nltk.data.find(f'taggers/{package}')
                print(f"    ✅ {package} - 已存在")
            except LookupError:
                print(f"    📥 下载 {package}...")
                nltk.download(package)

        print_colored("✅ NLTK数据下载完成!", "green")
        return True

    except Exception as e:
        print_colored(f"❌ NLTK数据下载失败: {e}", "red")
        return False


def download_spacy_models():
    """下载SpaCy模型"""
    print_colored("🧠 下载SpaCy模型...", "cyan")

    try:
        import spacy

        # 支持的SpaCy模型
        models = [
            ('zh_core_web_sm', '中文小型模型'),
            ('en_core_web_sm', '英文小型模型'),
            ('zh_core_web_md', '中文中型模型'),
            ('en_core_web_md', '英文中型模型'),
        ]

        successful_downloads = 0
        for model_id, description in models:
            try:
                # 检查模型是否已下载
                spacy.load(model_id)
                print(f"    ✅ {model_id} ({description}) - 已存在")
                successful_downloads += 1
            except OSError:
                print(f"    📥 下载 {model_id} ({description})...")
                try:
                    spacy.cli.download(model_id)
                    successful_downloads += 1
                    print(f"    ✅ {model_id} - 下载成功")
                except Exception as download_error:
                    print(f"    ❌ {model_id} - 下载失败: {download_error}")

        if successful_downloads > 0:
            print_colored(f"✅ SpaCy模型下载完成! ({successful_downloads}/{len(models)} 个模型)", "green")
        else:
            print_colored("⚠️  没有下载SpaCy模型，某些功能可能受限", "yellow")

        return successful_downloads > 0

    except Exception as e:
        print_colored(f"❌ SpaCy模型下载失败: {e}", "red")
        return False


def check_huggingface_models():
    """检查HuggingFace模型"""
    print_colored("🤗 检查HuggingFace模型...", "cyan")

    try:
        from transformers import AutoTokenizer

        # 检查常用的中文BERT模型
        models_to_check = [
            'bert-base-chinese',
            'bert-base-multilingual-cased',
            'distilbert-base-multilingual-cased'
        ]

        successful_checks = 0
        for model_name in models_to_check:
            try:
                print(f"    🔍 检查模型: {model_name}")
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                print(f"    ✅ {model_name} - 可用")
                successful_checks += 1
            except Exception as e:
                print(f"    ❌ {model_name} - 不可用: {str(e)[:50]}...")

        if successful_checks > 0:
            print_colored(f"✅ HuggingFace模型检查完成! ({successful_checks}/{len(models_to_check)} 个模型可用)", "green")
        else:
            print_colored("⚠️  没有可用的HuggingFace模型", "yellow")

        return successful_checks > 0

    except Exception as e:
        print_colored(f"❌ HuggingFace模型检查失败: {e}", "red")
        return False


def create_model_config():
    """创建模型配置文件"""
    print_colored("⚙️  创建模型配置文件...", "cyan")

    config_dir = project_root / "config"
    config_dir.mkdir(exist_ok=True)

    config_content = """# NLP模型配置文件
# CPG2PVG-AI System NLP Model Configuration

# NLTK配置
NLTK_DATA_PATH = "nltk_data"
NLTK_LANGUAGE = "english"

# SpaCy配置
SPACY_MODEL_ZH = "zh_core_web_sm"  # 中文模型
SPACY_MODEL_EN = "en_core_web_sm"  # 英文模型

# HuggingFace配置
HF_MODEL_BASE = "bert-base-chinese"
HF_CACHE_DIR = "hf_cache"

# 模型优先级
PREFERRED_LANGUAGE = "zh"  # zh: 中文优先, en: 英文优先
FALLBACK_LANGUAGE = "en"

# 下载配置
AUTO_DOWNLOAD = true
SKIP_LARGE_MODELS = False

# 性能配置
MAX_CONCURRENT_DOWNLOADS = 3
DOWNLOAD_TIMEOUT = 300  # 5分钟
"""

    config_file = config_dir / "nlp_models.py"

    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)

        print_colored(f"✅ 配置文件已创建: {config_file}", "green")
        return True

    except Exception as e:
        print_colored(f"❌ 配置文件创建失败: {e}", "red")
        return False


def create_download_script():
    """创建模型下载脚本"""
    script_content = '''#!/bin/bash
#!/bin/bash
# NLP模型自动下载脚本
# 自动下载CPG2PVG-AI系统所需的NLP模型

set -e

echo "🚀 开始下载NLP模型..."

# 设置Python路径
PYTHON_PATH="$(dirname "$0")/../venv/bin"
if [ -d "$PYTHON_PATH" ]; then
    export PATH="$PYTHON_PATH:$PATH"
fi

# 激活虚拟环境（如果存在）
if [ -f "$(dirname "$0")/../venv/bin/activate" ]; then
    source "$(dirname "$0")/../venv/bin/activate"
fi

echo "📦 安装Python依赖..."
pip install nltk spacy transformers tokenizers

echo "🔤 下载NLTK数据..."
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet');"

echo "🧠 下载SpaCy模型..."
python -c "import spacy; spacy.cli.download('zh_core_web_sm');"

echo "✅ 所有NLP模型下载完成!"
'''

    script_file = project_root / "scripts" / "download_nlp_models.sh"

    try:
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # 设置执行权限
        os.chmod(script_file, 0o755)

        print_colored(f"✅ 下载脚本已创建: {script_file}", "green")
        print_colored("   运行命令: bash scripts/download_nlp_models.sh", "cyan")
        return True

    except Exception as e:
        print_colored(f"❌ 下载脚本创建失败: {e}", "red")
        return False


def check_system_requirements():
    """检查系统要求"""
    print_colored("🔍 检查系统要求...", "cyan")

    issues = []

    # 检查Python版本
    python_version = sys.version_info
    if python_version < (3, 8):
        issues.append(f"Python版本过低: {python_version[0]}.{python_version[1]} (需要 >= 3.8)")

    # 检查网络连接
    try:
        import requests
        response = requests.get("https://pypi.org", timeout=10)
        if response.status_code != 200:
            issues.append("网络连接异常")
    except Exception:
        issues.append("网络连接检查失败")

    # 检查磁盘空间
    import shutil
    total, used, free = shutil.disk_usage(".")
    free_gb = free // (1024**3)
    if free_gb < 2:  # 2GB
        issues.append(f"磁盘空间不足: {free_gb}GB (推荐至少2GB)")

    if issues:
        print_colored("⚠️  系统要求检查失败:", "yellow")
        for issue in issues:
            print(f"    - {issue}")
        return False

    print_colored("✅ 系统要求检查通过!", "green")
    return True


def main():
    """主函数"""
    print_colored("🧠 CPG2PVG-AI NLP模型下载脚本", "blue")
    print("=" * 60)

    # 检查系统要求
    if not check_system_requirements():
        print_colored("❌ 系统要求不满足，请解决后重试", "red")
        return False

    print()

    success_count = 0
    total_checks = 4

    # 1. 下载NLTK数据
    if download_nltk_data():
        success_count += 1

    # 2. 下载SpaCy模型
    if download_spacy_models():
        success_count += 1

    # 3. 检查HuggingFace模型
    if check_huggingface_models():
        success_count += 1

    # 4. 创建配置文件
    if create_model_config():
        success_count += 1

    # 5. 创建下载脚本
    if create_download_script():
        success_count += 1

    print()
    print_colored("=" * 60, "blue")
    print_colored("📊 下载总结", "blue")
    print(f"  成功: {success_count}/{total_checks} 项")

    if success_count == total_checks:
        print_colored("🎉 所有NLP模型下载/配置完成!", "green")
        print()
        print_colored("📋 下一步:", "cyan")
        print("  1. 运行医学文档解析器测试:")
        print("     python scripts/test_medical_parser.py")
        print("  2. 启动完整系统设置:")
        print("     python scripts/setup_complete_system.py")
        print("  3. 开始使用医学文档解析功能")
    else:
        print_colored(f"⚠️  部分下载失败 ({total_checks - success_count} 项)", "yellow")
        print()
        print_colored("🔧 故障排除:", "yellow")
        print("  1. 检查网络连接")
        print("  - 确保可以访问 https://github.com")
        print("  - 检查防火墙设置")
        print()
        print("  2. 检查权限设置")
        print("  - 确保有写入权限")
        print("  - 检查虚拟环境权限")
        print()
        print("  3. 手动安装缺失模型:")
        print("  - SpaCy: python -m spacy download zh_core_web_sm")
        print("  - NLTK: python -c \"import nltk; nltk.download('punkt')\"")

    return success_count == total_checks


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)