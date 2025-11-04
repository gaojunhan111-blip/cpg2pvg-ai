"""
文件类型常量定义 - 后端Python版本
File Type Constants Definition - Backend Python Version

这个文件定义了前后端共享的文件类型常量，确保一致性
This file defines shared file type constants for frontend-backend consistency
"""

from enum import Enum
from typing import Dict, List, Set, Optional, Tuple
import mimetypes


class FileType(str, Enum):
    """文件类型枚举"""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"
    HTML = "html"
    MARKDOWN = "markdown"


# 文件扩展名映射
FILE_EXTENSIONS: Dict[FileType, List[str]] = {
    FileType.PDF: [".pdf"],
    FileType.DOCX: [".docx"],
    FileType.DOC: [".doc"],
    FileType.TXT: [".txt"],
    FileType.HTML: [".html", ".htm"],
    FileType.MARKDOWN: [".md", ".markdown"]
}

# 允许的文件扩展名（后端和前端统一使用）
ALLOWED_FILE_EXTENSIONS: List[str] = []
for extensions in FILE_EXTENSIONS.values():
    ALLOWED_FILE_EXTENSIONS.extend(extensions)

# 允许的MIME类型
ALLOWED_MIME_TYPES: List[str] = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'text/plain',
    'text/html',
    'text/markdown'
]

# MIME类型到文件类型的映射
MIME_TO_FILE_TYPE: Dict[str, FileType] = {
    'application/pdf': FileType.PDF,
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': FileType.DOCX,
    'application/msword': FileType.DOC,
    'text/plain': FileType.TXT,
    'text/html': FileType.HTML,
    'text/markdown': FileType.MARKDOWN
}

# 文件类型显示名称
FILE_TYPE_NAMES: Dict[FileType, str] = {
    FileType.PDF: "PDF文档",
    FileType.DOCX: "Word文档 (DOCX)",
    FileType.DOC: "Word文档 (DOC)",
    FileType.TXT: "纯文本",
    FileType.HTML: "HTML网页",
    FileType.MARKDOWN: "Markdown文档"
}

# 文件类型图标映射 (对应Ant Design图标)
FILE_TYPE_ICONS: Dict[FileType, str] = {
    FileType.PDF: "FilePdfOutlined",
    FileType.DOCX: "FileWordOutlined",
    FileType.DOC: "FileWordOutlined",
    FileType.TXT: "FileTextOutlined",
    FileType.HTML: "FileMarkdownOutlined",
    FileType.MARKDOWN: "FileMarkdownOutlined"
}

# 文件验证配置
class FileValidationConfig:
    MAX_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_SIZE_MB = 50
    MIN_SIZE = 1  # 1字节
    MAX_FILES = 10  # 单次上传最大文件数
    CHUNK_SIZE = 1024 * 1024  # 1MB
    MAX_CONCURRENT_UPLOADS = 3
    UPLOAD_TIMEOUT = 5 * 60 * 1000  # 5分钟


def validate_file_type(filename: str, mime_type: Optional[str] = None) -> Dict[str, any]:
    """
    文件类型验证函数

    Args:
        filename: 文件名
        mime_type: 可选的MIME类型

    Returns:
        验证结果字典: {valid: bool, fileType?: str, error?: str}
    """
    file_extension = f".{filename.split('.')[-1].lower()}" if '.' in filename else ""

    if not file_extension:
        return {"valid": False, "error": "文件缺少扩展名"}

    # 检查扩展名是否允许
    if file_extension not in ALLOWED_FILE_EXTENSIONS:
        return {
            "valid": False,
            "error": f"不支持的文件类型，允许的类型: {', '.join(sorted(set(ALLOWED_FILE_EXTENSIONS)))}"
        }

    # 如果有MIME类型，也要验证
    if mime_type and mime_type not in ALLOWED_MIME_TYPES:
        return {
            "valid": False,
            "error": f"不支持的文件类型 (MIME: {mime_type})"
        }

    # 获取文件类型
    file_type = None
    for ft, extensions in FILE_EXTENSIONS.items():
        if file_extension in extensions:
            file_type = ft.value
            break

    return {"valid": True, "fileType": file_type}


def validate_file_size(file_size: int) -> Dict[str, any]:
    """
    文件大小验证函数

    Args:
        file_size: 文件大小（字节）

    Returns:
        验证结果字典: {valid: bool, error?: str}
    """
    if file_size < FileValidationConfig.MIN_SIZE:
        return {"valid": False, "error": "文件大小不能为0"}

    if file_size > FileValidationConfig.MAX_SIZE:
        return {
            "valid": False,
            "error": f"文件大小超过限制，最大 {FileValidationConfig.MAX_SIZE_MB}MB"
        }

    return {"valid": True}


def format_file_size(bytes_size: int) -> str:
    """
    格式化文件大小显示

    Args:
        bytes_size: 文件大小（字节）

    Returns:
        格式化后的文件大小字符串
    """
    if bytes_size == 0:
        return "0 B"

    k = 1024
    sizes = ["B", "KB", "MB", "GB"]
    i = min(len(sizes) - 1, int(bytes_size.bit_length() / 10))

    return f"{round(bytes_size / (k ** i), 2)} {sizes[i]}"


def is_image_file(filename: str, mime_type: Optional[str] = None) -> bool:
    """
    检查文件是否为图片类型（用于预览）

    Args:
        filename: 文件名
        mime_type: 可选的MIME类型

    Returns:
        是否为图片文件
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    image_mime_types = {'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp'}

    file_extension = f".{filename.split('.')[-1].lower()}" if '.' in filename else ""

    return (file_extension in image_extensions) or (mime_type and mime_type in image_mime_types)


def get_file_info(filename: str, mime_type: Optional[str] = None) -> Dict[str, any]:
    """
    获取文件类型的显示信息

    Args:
        filename: 文件名
        mime_type: 可选的MIME类型

    Returns:
        文件信息字典
    """
    validation_result = validate_file_type(filename, mime_type)

    if not validation_result["valid"]:
        return {"error": validation_result["error"], "valid": False}

    file_type = validation_result["fileType"]
    file_type_enum = FileType(file_type)

    return {
        "valid": True,
        "fileType": file_type,
        "fileName": filename,
        "displayName": FILE_TYPE_NAMES[file_type_enum],
        "icon": FILE_TYPE_ICONS[file_type_enum],
        "extensions": FILE_EXTENSIONS[file_type_enum],
        "mimeTypes": [
            mime for mime, ft in MIME_TO_FILE_TYPE.items()
            if ft == file_type_enum
        ]
    }


# 导出的便捷属性
FILE_TYPE_SET: Set[str] = {ft.value for ft in FileType}
EXTENSION_SET: Set[str] = set(ALLOWED_FILE_EXTENSIONS)
MIME_TYPE_SET: Set[str] = set(ALLOWED_MIME_TYPES)