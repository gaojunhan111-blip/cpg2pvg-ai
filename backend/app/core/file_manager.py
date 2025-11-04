"""
文件管理和存储系统
File Management and Storage System
"""

import os
import hashlib
import mimetypes
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union, BinaryIO
import asyncio
import aiofiles
from urllib.parse import quote

from app.core.config import get_settings
from app.core.logger import get_logger
from app.core.error_handling import FileSystemError, ErrorHandler, ErrorCategory, ErrorSeverity

logger = get_logger(__name__)
settings = get_settings()


class FileManager:
    """文件管理器"""

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.output_dir = Path(settings.OUTPUT_DIR)
        self.temp_dir = Path(settings.TEMP_DIR)
        self.backup_dir = Path(settings.BACKUP_DIR)

        # 确保所有目录存在
        self._ensure_directories()

        # 导入共享的文件类型常量
        from shared.constants.file_types import MIME_TO_FILE_TYPE, ALLOWED_MIME_TYPES
        self.supported_types = {ft.value: mime for mime, ft in MIME_TO_FILE_TYPE.items()}

    def _ensure_directories(self):
        """确保所有必要的目录存在"""
        directories = [
            self.upload_dir,
            self.output_dir,
            self.temp_dir,
            self.backup_dir,
            self.upload_dir / "guidelines",
            self.upload_dir / "templates",
            self.output_dir / "pvg_documents",
            self.output_dir / "exports",
            self.output_dir / "archives"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")

    async def save_uploaded_file(
        self,
        file_content: Union[bytes, BinaryIO],
        original_filename: str,
        subdirectory: str = "guidelines",
        overwrite: bool = False
    ) -> Dict[str, any]:
        """
        保存上传的文件

        Args:
            file_content: 文件内容
            original_filename: 原始文件名
            subdirectory: 子目录名称
            overwrite: 是否覆盖已存在的文件

        Returns:
            Dict[str, any]: 文件信息
        """
        try:
            # 验证文件名和类型
            file_info = self._validate_filename(original_filename)

            # 生成唯一文件名
            file_id = self._generate_file_id(original_filename)
            safe_filename = f"{file_id}_{original_filename}"
            file_path = self.upload_dir / subdirectory / safe_filename

            # 检查文件是否已存在
            if file_path.exists() and not overwrite:
                raise FileSystemError(
                    message=f"File already exists: {original_filename}",
                    file_path=str(file_path),
                    operation="save_uploaded_file"
                )

            # 保存文件
            if isinstance(file_content, bytes):
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(file_content)
            else:
                # 处理文件流
                async with aiofiles.open(file_path, 'wb') as f:
                    while chunk := file_content.read(8192):
                        await f.write(chunk)

            # 计算文件哈希
            file_hash = await self._calculate_file_hash(file_path)

            # 获取文件大小
            file_size = file_path.stat().st_size

            # 创建备份
            if subdirectory == "guidelines":
                await self._create_backup(file_path, subdirectory)

            file_info.update({
                "file_id": file_id,
                "safe_filename": safe_filename,
                "file_path": str(file_path),
                "relative_path": f"{subdirectory}/{safe_filename}",
                "file_size": file_size,
                "file_hash": file_hash,
                "upload_time": datetime.utcnow(),
                "mime_type": file_info["mime_type"]
            })

            logger.info(f"File saved successfully: {file_path}")
            return file_info

        except Exception as e:
            logger.error(f"Failed to save file: {original_filename}", extra_data={"error": str(e)})
            raise ErrorHandler.handle_file_system_error("save_uploaded_file", original_filename, e)

    def _validate_filename(self, filename: str) -> Dict[str, str]:
        """验证文件名和类型（使用共享常量）"""
        if not filename or filename.strip() == "":
            raise FileSystemError(
                message="Filename cannot be empty",
                operation="validate_filename"
            )

        # 使用共享常量验证文件类型
        from shared.constants.file_types import validate_file_type, ALLOWED_FILE_EXTENSIONS
        validation_result = validate_file_type(filename)

        if not validation_result["valid"]:
            raise FileSystemError(
                message=validation_result["error"],
                operation="validate_filename"
            )

        # 获取文件扩展名
        file_ext = Path(filename).suffix.lower().lstrip('.')
        if file_ext not in [ext.lstrip('.') for ext in ALLOWED_FILE_EXTENSIONS]:
            raise FileSystemError(
                message=f"Unsupported file type: {file_ext}",
                operation="validate_filename"
            )

        # 检查文件名中的非法字符
        illegal_chars = ['<', '>', ':', '"', '|', '?', '*', '/', '\\']
        if any(char in filename for char in illegal_chars):
            raise FileSystemError(
                message=f"Filename contains illegal characters: {filename}",
                operation="validate_filename"
            )

        return {
            "extension": file_ext,
            "mime_type": self.supported_types[file_ext]
        }

    def _generate_file_id(self, filename: str) -> str:
        """生成唯一文件ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        hash_input = f"{filename}_{timestamp}_{os.urandom(8).hex()}"
        file_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"{timestamp}_{file_hash}"

    async def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件SHA256哈希"""
        hash_sha256 = hashlib.sha256()

        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_sha256.update(chunk)

        return hash_sha256.hexdigest()

    async def _create_backup(self, file_path: Path, subdirectory: str):
        """创建文件备份"""
        try:
            backup_dir = self.backup_dir / subdirectory
            backup_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = backup_dir / backup_filename

            shutil.copy2(file_path, backup_path)
            logger.debug(f"Backup created: {backup_path}")

        except Exception as e:
            logger.warning(f"Failed to create backup for {file_path}: {e}")

    async def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, any]:
        """
        获取文件信息

        Args:
            file_path: 文件路径

        Returns:
            Dict[str, any]: 文件信息
        """
        try:
            path = Path(file_path)

            if not path.exists():
                raise FileSystemError(
                    message=f"File not found: {file_path}",
                    file_path=str(path),
                    operation="get_file_info"
                )

            stat = path.stat()
            file_ext = path.suffix.lower().lstrip('.')
            mime_type = mimetypes.guess_type(str(path))[0] or 'application/octet-stream'

            return {
                "filename": path.name,
                "file_path": str(path),
                "file_size": stat.st_size,
                "file_extension": file_ext,
                "mime_type": mime_type,
                "created_time": datetime.fromtimestamp(stat.st_ctime),
                "modified_time": datetime.fromtimestamp(stat.st_mtime),
                "is_file": path.is_file(),
                "is_readable": os.access(path, os.R_OK)
            }

        except Exception as e:
            logger.error(f"Failed to get file info: {file_path}", extra_data={"error": str(e)})
            raise ErrorHandler.handle_file_system_error("get_file_info", str(file_path), e)

    async def read_file(self, file_path: Union[str, Path], mode: str = 'r') -> Union[str, bytes]:
        """
        读取文件内容

        Args:
            file_path: 文件路径
            mode: 读取模式 ('r' for text, 'rb' for binary)

        Returns:
            Union[str, bytes]: 文件内容
        """
        try:
            path = Path(file_path)

            if not path.exists():
                raise FileSystemError(
                    message=f"File not found: {file_path}",
                    file_path=str(path),
                    operation="read_file"
                )

            if mode == 'r':
                async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                    return await f.read()
            elif mode == 'rb':
                async with aiofiles.open(path, 'rb') as f:
                    return await f.read()
            else:
                raise FileSystemError(
                    message=f"Invalid read mode: {mode}",
                    operation="read_file"
                )

        except Exception as e:
            logger.error(f"Failed to read file: {file_path}", extra_data={"error": str(e)})
            raise ErrorHandler.handle_file_system_error("read_file", str(file_path), e)

    async def write_file(
        self,
        file_path: Union[str, Path],
        content: Union[str, bytes],
        mode: str = 'w',
        create_dirs: bool = True
    ) -> None:
        """
        写入文件内容

        Args:
            file_path: 文件路径
            content: 文件内容
            mode: 写入模式 ('w' for text, 'wb' for binary)
            create_dirs: 是否创建目录
        """
        try:
            path = Path(file_path)

            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)

            if mode == 'w':
                async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                    await f.write(content)
            elif mode == 'wb':
                async with aiofiles.open(path, 'wb') as f:
                    await f.write(content)
            else:
                raise FileSystemError(
                    message=f"Invalid write mode: {mode}",
                    operation="write_file"
                )

            logger.debug(f"File written successfully: {file_path}")

        except Exception as e:
            logger.error(f"Failed to write file: {file_path}", extra_data={"error": str(e)})
            raise ErrorHandler.handle_file_system_error("write_file", str(file_path), e)

    async def delete_file(self, file_path: Union[str, Path], create_backup: bool = True) -> bool:
        """
        删除文件

        Args:
            file_path: 文件路径
            create_backup: 是否创建备份

        Returns:
            bool: 删除是否成功
        """
        try:
            path = Path(file_path)

            if not path.exists():
                logger.warning(f"File not found for deletion: {file_path}")
                return True

            # 创建备份
            if create_backup:
                relative_path = path.relative_to(self.upload_dir)
                backup_subdir = str(relative_path.parent)
                await self._create_backup(path, backup_subdir)

            # 删除文件
            path.unlink()
            logger.info(f"File deleted successfully: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file: {file_path}", extra_data={"error": str(e)})
            raise ErrorHandler.handle_file_system_error("delete_file", str(file_path), e)

    async def move_file(
        self,
        source_path: Union[str, Path],
        target_path: Union[str, Path],
        create_dirs: bool = True
    ) -> None:
        """
        移动文件

        Args:
            source_path: 源文件路径
            target_path: 目标文件路径
            create_dirs: 是否创建目标目录
        """
        try:
            source = Path(source_path)
            target = Path(target_path)

            if not source.exists():
                raise FileSystemError(
                    message=f"Source file not found: {source_path}",
                    file_path=str(source),
                    operation="move_file"
                )

            if create_dirs:
                target.parent.mkdir(parents=True, exist_ok=True)

            # 如果目标文件已存在，先创建备份
            if target.exists():
                await self._create_backup(target, "moved_files")

            shutil.move(str(source), str(target))
            logger.info(f"File moved from {source_path} to {target_path}")

        except Exception as e:
            logger.error(f"Failed to move file: {source_path} to {target_path}", extra_data={"error": str(e)})
            raise ErrorHandler.handle_file_system_error("move_file", str(source_path), e)

    async def copy_file(
        self,
        source_path: Union[str, Path],
        target_path: Union[str, Path],
        create_dirs: bool = True
    ) -> None:
        """
        复制文件

        Args:
            source_path: 源文件路径
            target_path: 目标文件路径
            create_dirs: 是否创建目标目录
        """
        try:
            source = Path(source_path)
            target = Path(target_path)

            if not source.exists():
                raise FileSystemError(
                    message=f"Source file not found: {source_path}",
                    file_path=str(source),
                    operation="copy_file"
                )

            if create_dirs:
                target.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(str(source), str(target))
            logger.info(f"File copied from {source_path} to {target_path}")

        except Exception as e:
            logger.error(f"Failed to copy file: {source_path} to {target_path}", extra_data={"error": str(e)})
            raise ErrorHandler.handle_file_system_error("copy_file", str(source_path), e)

    async def list_files(
        self,
        directory: Union[str, Path],
        pattern: str = "*",
        recursive: bool = False
    ) -> List[Dict[str, any]]:
        """
        列出目录中的文件

        Args:
            directory: 目录路径
            pattern: 文件模式
            recursive: 是否递归搜索

        Returns:
            List[Dict[str, any]]: 文件信息列表
        """
        try:
            dir_path = Path(directory)

            if not dir_path.exists() or not dir_path.is_dir():
                raise FileSystemError(
                    message=f"Directory not found: {directory}",
                    file_path=str(dir_path),
                    operation="list_files"
                )

            files = []
            if recursive:
                file_paths = dir_path.rglob(pattern)
            else:
                file_paths = dir_path.glob(pattern)

            for file_path in file_paths:
                if file_path.is_file():
                    try:
                        file_info = await self.get_file_info(file_path)
                        files.append(file_info)
                    except Exception as e:
                        logger.warning(f"Failed to get info for {file_path}: {e}")

            return sorted(files, key=lambda x: x['modified_time'], reverse=True)

        except Exception as e:
            logger.error(f"Failed to list files in directory: {directory}", extra_data={"error": str(e)})
            raise ErrorHandler.handle_file_system_error("list_files", str(directory), e)

    async def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        清理临时文件

        Args:
            max_age_hours: 最大保存时间（小时）

        Returns:
            int: 清理的文件数量
        """
        try:
            if not self.temp_dir.exists():
                return 0

            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            cleaned_count = 0

            for file_path in self.temp_dir.rglob("*"):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        try:
                            file_path.unlink()
                            cleaned_count += 1
                            logger.debug(f"Cleaned up temp file: {file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to delete temp file {file_path}: {e}")

            logger.info(f"Cleaned up {cleaned_count} temporary files")
            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup temp files", extra_data={"error": str(e)})
            raise ErrorHandler.handle_file_system_error("cleanup_temp_files", str(self.temp_dir), e)

    async def generate_download_url(self, file_path: Union[str, Path], filename: str = None) -> str:
        """
        生成文件下载URL

        Args:
            file_path: 文件路径
            filename: 自定义文件名

        Returns:
            str: 下载URL
        """
        try:
            path = Path(file_path)

            if not path.exists():
                raise FileSystemError(
                    message=f"File not found: {file_path}",
                    file_path=str(path),
                    operation="generate_download_url"
                )

            # 构建下载URL
            relative_path = path.relative_to(self.output_dir)
            download_filename = filename or path.name

            # URL编码文件名
            encoded_filename = quote(download_filename)

            download_url = f"{settings.BASE_URL}/api/v1/files/download/{relative_path}?filename={encoded_filename}"

            return download_url

        except Exception as e:
            logger.error(f"Failed to generate download URL: {file_path}", extra_data={"error": str(e)})
            raise ErrorHandler.handle_file_system_error("generate_download_url", str(file_path), e)

    async def get_storage_stats(self) -> Dict[str, any]:
        """
        获取存储统计信息

        Returns:
            Dict[str, any]: 存储统计
        """
        try:
            stats = {
                "upload_dir": {
                    "path": str(self.upload_dir),
                    "exists": self.upload_dir.exists(),
                    "size_bytes": 0,
                    "file_count": 0
                },
                "output_dir": {
                    "path": str(self.output_dir),
                    "exists": self.output_dir.exists(),
                    "size_bytes": 0,
                    "file_count": 0
                },
                "temp_dir": {
                    "path": str(self.temp_dir),
                    "exists": self.temp_dir.exists(),
                    "size_bytes": 0,
                    "file_count": 0
                }
            }

            # 计算目录大小和文件数量
            for dir_name, dir_path in [
                ("upload_dir", self.upload_dir),
                ("output_dir", self.output_dir),
                ("temp_dir", self.temp_dir)
            ]:
                if dir_path.exists():
                    total_size = 0
                    file_count = 0

                    for file_path in dir_path.rglob("*"):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
                            file_count += 1

                    stats[dir_name]["size_bytes"] = total_size
                    stats[dir_name]["file_count"] = file_count

            return stats

        except Exception as e:
            logger.error(f"Failed to get storage stats", extra_data={"error": str(e)})
            raise ErrorHandler.handle_file_system_error("get_storage_stats", "system", e)


# 全局文件管理器实例
_file_manager: Optional[FileManager] = None


def get_file_manager() -> FileManager:
    """获取文件管理器实例"""
    global _file_manager
    if _file_manager is None:
        _file_manager = FileManager()
    return _file_manager