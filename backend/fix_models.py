"""
数据模型修复脚本
Fix data model inconsistencies
"""

import os
import re
from pathlib import Path

def fix_enum_default_values(file_path: Path):
    """修复枚举类型的默认值"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 修复UserRole默认值
    content = re.sub(
        r'default=UserRole\.USER',
        'default=UserRole.USER.value',
        content
    )

    # 修复其他枚举默认值
    content = re.sub(
        r'default=TaskStatus\.PENDING',
        'default=TaskStatus.PENDING.value',
        content
    )

    content = re.sub(
        r'default=TaskType\.DOCUMENT_PARSING',
        'default=TaskType.DOCUMENT_PARSING.value',
        content
    )

    content = re.sub(
        r'default=TaskPriority\.NORMAL',
        'default=TaskPriority.NORMAL.value',
        content
    )

    content = re.sub(
        r'default=GuidelineStatus\.UPLOADED',
        'default=GuidelineStatus.UPLOADED.value',
        content
    )

    content = re.sub(
        r'default=ProcessingMode\.SLOW',
        'default=ProcessingMode.SLOW.value',
        content
    )

    content = re.sub(
        r'default=DocumentType\.PDF',
        'default=DocumentType.PDF.value',
        content
    )

    content = re.sub(
        r'default=ResultStatus\.GENERATED',
        'default=ResultStatus.GENERATED.value',
        content
    )

    content = re.sub(
        r'default=ContentFormat\.HTML',
        'default=ContentFormat.HTML.value',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def add_missing_imports(file_path: Path):
    """添加缺失的导入"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 确保有正确的导入
    if 'from datetime import datetime' not in content:
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('from sqlalchemy') or line.startswith('import sqlalchemy'):
                insert_pos = i
                break

        if insert_pos > 0:
            lines.insert(insert_pos, 'from datetime import datetime')
            content = '\n'.join(lines)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def fix_base_model_update_method(file_path: Path):
    """修复BaseModel的update_from_dict方法"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 确保update_from_dict方法使用正确的datetime导入
    content = content.replace(
        'self.updated_at = datetime.utcnow()',
        'from datetime import datetime; self.updated_at = datetime.utcnow()'
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    """主函数"""
    models_dir = Path(__file__).parent / 'app' / 'models'

    model_files = [
        'user.py',
        'guideline.py',
        'task.py',
        'processing_result.py'
    ]

    print("开始修复数据模型...")

    for model_file in model_files:
        file_path = models_dir / model_file
        if file_path.exists():
            print(f"修复 {model_file}...")
            fix_enum_default_values(file_path)
            add_missing_imports(file_path)
            print(f"✅ {model_file} 修复完成")
        else:
            print(f"⚠️ {model_file} 不存在")

    # 修复base.py
    base_file = models_dir / 'base.py'
    if base_file.exists():
        print("修复 base.py...")
        fix_base_model_update_method(base_file)
        print("✅ base.py 修复完成")

    print("🎉 所有模型修复完成!")

if __name__ == "__main__":
    main()