"""
MinIO文件存储服务
CPG2PVG-AI System File Storage Service
"""

import asyncio
import hashlib
import io
import mimetypes
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, BinaryIO
from urllib.parse import quote

import aiofiles
from minio import Minio
from minio.error import S3Error
import aiofiles.os

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class FileStorageError(Exception):
    """文件存储异常"""
    pass


class MinIOClient:
    """MinIO客户端封装"""

    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[Minio] = None
        self._bucket_name = self.settings.MINIO_BUCKET_NAME

    async def _get_client(self) -> Minio:
        """获取MinIO客户端"""
        if self._client is None:
            self._client = Minio(
                endpoint=self.settings.MINIO_ENDPOINT,
                access_key=self.settings.MINIO_ACCESS_KEY,
                secret_key=self.settings.MINIO_SECRET_KEY,
                secure=self.settings.MINIO_SECURE,
                region=self.settings.MINIO_REGION
            )

            # 确保bucket存在
            await self._ensure_bucket_exists()

        return self._client

    async def _ensure_bucket_exists(self):
        """确保bucket存在"""
        try:
            client = await self._get_client()

            # 在线程池中执行同步操作
            loop = asyncio.get_event_loop()

            def check_bucket():
                try:
                    if not client.bucket_exists(self._bucket_name):
                        client.make_bucket(
                            bucket_name=self._bucket_name,
                            location=self.settings.MINIO_REGION
                        )
                        logger.info(f"Created MinIO bucket: {self._bucket_name}")
                    else:
                        logger.info(f"MinIO bucket already exists: {self._bucket_name}")
                except S3Error as e:
                    logger.error(f"Failed to ensure bucket exists: {e}")
                    raise FileStorageError(f"Bucket操作失败: {e}")

            await loop.run_in_executor(None, check_bucket)

        except Exception as e:
            logger.error(f"Failed to ensure bucket exists: {e}")
            raise FileStorageError(f"Bucket检查失败: {e}")

    def _generate_object_name(self, original_filename: str, prefix: str = "") -> str:
        """生成对象名称"""
        # 获取文件扩展名
        file_ext = os.path.splitext(original_filename)[1]

        # 生成唯一标识
        unique_id = str(uuid.uuid4())

        # 添加时间前缀
        date_prefix = datetime.now().strftime("%Y/%m/%d")

        # 组合路径
        if prefix:
            object_name = f"{prefix}/{date_prefix}/{unique_id}{file_ext}"
        else:
            object_name = f"{date_prefix}/{unique_id}{file_ext}"

        return object_name

    def _calculate_file_hash(self, content: bytes) -> str:
        """计算文件哈希值"""
        return hashlib.sha256(content).hexdigest()

    async def upload_file(
        self,
        file_content: bytes,
        original_filename: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        prefix: str = "files"
    ) -> Dict[str, Any]:
        """上传文件"""
        try:
            client = await self._get_client()

            # 自动检测content_type
            if content_type is None:
                content_type, _ = mimetypes.guess_type(original_filename)
                if content_type is None:
                    content_type = "application/octet-stream"

            # 生成对象名称
            object_name = self._generate_object_name(original_filename, prefix)

            # 计算文件哈希
            file_hash = self._calculate_file_hash(file_content)
            file_size = len(file_content)

            # 准备元数据
            object_metadata = {
                "original-filename": original_filename,
                "file-hash": file_hash,
                "upload-time": datetime.utcnow().isoformat(),
                "content-type": content_type
            }

            if metadata:
                object_metadata.update(metadata)

            # 在线程池中执行上传
            loop = asyncio.get_event_loop()

            def upload_sync():
                try:
                    client.put_object(
                        bucket_name=self._bucket_name,
                        object_name=object_name,
                        data=io.BytesIO(file_content),
                        length=file_size,
                        content_type=content_type,
                        metadata=object_metadata
                    )
                    return {
                        "object_name": object_name,
                        "file_hash": file_hash,
                        "file_size": file_size,
                        "content_type": content_type
                    }
                except S3Error as e:
                    logger.error(f"MinIO upload error: {e}")
                    raise FileStorageError(f"文件上传失败: {e}")

            result = await loop.run_in_executor(None, upload_sync)

            logger.info(f"Successfully uploaded file: {object_name} ({file_size} bytes)")

            return {
                "object_name": object_name,
                "original_filename": original_filename,
                "file_size": file_size,
                "file_hash": result["file_hash"],
                "content_type": content_type,
                "bucket": self._bucket_name,
                "upload_url": f"{object_name}",
                "metadata": object_metadata
            }

        except Exception as e:
            logger.error(f"Failed to upload file {original_filename}: {e}")
            raise FileStorageError(f"文件上传失败: {e}")

    async def upload_file_from_path(
        self,
        file_path: str,
        original_filename: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        prefix: str = "files"
    ) -> Dict[str, Any]:
        """从文件路径上传文件"""
        try:
            # 读取文件内容
            async with aiofiles.open(file_path, 'rb') as f:
                file_content = await f.read()

            # 使用原始文件名（如果未提供）
            if original_filename is None:
                original_filename = os.path.basename(file_path)

            return await self.upload_file(
                file_content=file_content,
                original_filename=original_filename,
                content_type=content_type,
                metadata=metadata,
                prefix=prefix
            )

        except Exception as e:
            logger.error(f"Failed to upload file from path {file_path}: {e}")
            raise FileStorageError(f"文件路径上传失败: {e}")

    async def download_file(self, object_name: str) -> bytes:
        """下载文件"""
        try:
            client = await self._get_client()

            # 在线程池中执行下载
            loop = asyncio.get_event_loop()

            def download_sync():
                try:
                    response = client.get_object(
                        bucket_name=self._bucket_name,
                        object_name=object_name
                    )
                    return response.read()
                except S3Error as e:
                    if e.code == "NoSuchKey":
                        raise FileStorageError(f"文件不存在: {object_name}")
                    else:
                        raise FileStorageError(f"文件下载失败: {e}")
                finally:
                    if 'response' in locals():
                        response.close()
                        response.release_conn()

            file_content = await loop.run_in_executor(None, download_sync)

            logger.info(f"Successfully downloaded file: {object_name}")
            return file_content

        except FileStorageError:
            raise
        except Exception as e:
            logger.error(f"Failed to download file {object_name}: {e}")
            raise FileStorageError(f"文件下载失败: {e}")

    async def download_file_to_path(self, object_name: str, local_path: str):
        """下载文件到本地路径"""
        try:
            file_content = await self.download_file(object_name)

            # 确保目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # 写入文件
            async with aiofiles.open(local_path, 'wb') as f:
                await f.write(file_content)

            logger.info(f"Successfully downloaded file to: {local_path}")

        except Exception as e:
            logger.error(f"Failed to download file to path {local_path}: {e}")
            raise FileStorageError(f"文件下载到路径失败: {e}")

    async def get_file_info(self, object_name: str) -> Dict[str, Any]:
        """获取文件信息"""
        try:
            client = await self._get_client()

            # 在线程池中执行查询
            loop = asyncio.get_event_loop()

            def get_stat_sync():
                try:
                    stat = client.stat_object(
                        bucket_name=self._bucket_name,
                        object_name=object_name
                    )
                    return {
                        "object_name": object_name,
                        "file_size": stat.size,
                        "last_modified": stat.last_modified.isoformat(),
                        "content_type": stat.content_type,
                        "etag": stat.etag,
                        "metadata": stat.metadata
                    }
                except S3Error as e:
                    if e.code == "NoSuchKey":
                        raise FileStorageError(f"文件不存在: {object_name}")
                    else:
                        raise FileStorageError(f"获取文件信息失败: {e}")

            file_info = await loop.run_in_executor(None, get_stat_sync)

            return file_info

        except FileStorageError:
            raise
        except Exception as e:
            logger.error(f"Failed to get file info for {object_name}: {e}")
            raise FileStorageError(f"获取文件信息失败: {e}")

    async def delete_file(self, object_name: str) -> bool:
        """删除文件"""
        try:
            client = await self._get_client()

            # 在线程池中执行删除
            loop = asyncio.get_event_loop()

            def delete_sync():
                try:
                    client.remove_object(
                        bucket_name=self._bucket_name,
                        object_name=object_name
                    )
                    return True
                except S3Error as e:
                    if e.code == "NoSuchKey":
                        return False
                    else:
                        raise FileStorageError(f"文件删除失败: {e}")

            result = await loop.run_in_executor(None, delete_sync)

            if result:
                logger.info(f"Successfully deleted file: {object_name}")

            return result

        except FileStorageError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete file {object_name}: {e}")
            raise FileStorageError(f"文件删除失败: {e}")

    async def list_files(
        self,
        prefix: str = "",
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """列出文件"""
        try:
            client = await self._get_client()

            # 在线程池中执行列出
            loop = asyncio.get_event_loop()

            def list_sync():
                try:
                    objects = client.list_objects(
                        bucket_name=self._bucket_name,
                        prefix=prefix,
                        recursive=True
                    )

                    files = []
                    for i, obj in enumerate(objects):
                        if i >= limit:
                            break
                        files.append({
                            "object_name": obj.object_name,
                            "file_size": obj.size,
                            "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                            "etag": obj.etag
                        })

                    return files
                except S3Error as e:
                    raise FileStorageError(f"文件列表获取失败: {e}")

            files = await loop.run_in_executor(None, list_sync)

            logger.info(f"Listed {len(files)} files with prefix: {prefix}")

            return files

        except Exception as e:
            logger.error(f"Failed to list files with prefix {prefix}: {e}")
            raise FileStorageError(f"文件列表获取失败: {e}")

    async def generate_presigned_url(
        self,
        object_name: str,
        expires: timedelta = timedelta(hours=1),
        method: str = "GET"
    ) -> str:
        """生成预签名URL"""
        try:
            client = await self._get_client()

            # 在线程池中执行URL生成
            loop = asyncio.get_event_loop()

            def generate_url_sync():
                try:
                    if method.upper() == "GET":
                        url = client.presigned_get_object(
                            bucket_name=self._bucket_name,
                            object_name=object_name,
                            expires=expires
                        )
                    elif method.upper() == "PUT":
                        url = client.presigned_put_object(
                            bucket_name=self._bucket_name,
                            object_name=object_name,
                            expires=expires
                        )
                    else:
                        raise FileStorageError(f"不支持的HTTP方法: {method}")

                    return url
                except S3Error as e:
                    raise FileStorageError(f"预签名URL生成失败: {e}")

            url = await loop.run_in_executor(None, generate_url_sync)

            logger.info(f"Generated presigned URL for {object_name} (expires in {expires})")

            return url

        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {object_name}: {e}")
            raise FileStorageError(f"预签名URL生成失败: {e}")

    async def check_file_exists(self, object_name: str) -> bool:
        """检查文件是否存在"""
        try:
            await self.get_file_info(object_name)
            return True
        except FileStorageError:
            return False

    async def get_file_hash(self, object_name: str) -> str:
        """获取文件哈希值"""
        try:
            file_info = await self.get_file_info(object_name)
            return file_info.get("metadata", {}).get("file-hash", "")
        except Exception as e:
            logger.error(f"Failed to get file hash for {object_name}: {e}")
            return ""

    async def cleanup_old_files(self, days: int = 30) -> int:
        """清理旧文件"""
        try:
            client = await self._get_client()

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # 在线程池中执行清理
            loop = asyncio.get_event_loop()

            def cleanup_sync():
                try:
                    deleted_count = 0
                    objects = client.list_objects(
                        bucket_name=self._bucket_name,
                        recursive=True
                    )

                    for obj in objects:
                        if obj.last_modified and obj.last_modified < cutoff_date:
                            try:
                                client.remove_object(
                                    bucket_name=self._bucket_name,
                                    object_name=obj.object_name
                                )
                                deleted_count += 1
                            except S3Error as e:
                                logger.warning(f"Failed to delete old file {obj.object_name}: {e}")

                    return deleted_count
                except S3Error as e:
                    raise FileStorageError(f"文件清理失败: {e}")

            deleted_count = await loop.run_in_executor(None, cleanup_sync)

            logger.info(f"Cleaned up {deleted_count} old files (older than {days} days)")

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")
            raise FileStorageError(f"文件清理失败: {e}")


# 创建全局MinIO客户端实例
minio_client = MinIOClient()


# 便捷函数
async def upload_file(
    file_content: bytes,
    original_filename: str,
    content_type: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
    prefix: str = "files"
) -> Dict[str, Any]:
    """上传文件便捷函数"""
    return await minio_client.upload_file(
        file_content=file_content,
        original_filename=original_filename,
        content_type=content_type,
        metadata=metadata,
        prefix=prefix
    )


async def download_file(object_name: str) -> bytes:
    """下载文件便捷函数"""
    return await minio_client.download_file(object_name)


async def get_file_info(object_name: str) -> Dict[str, Any]:
    """获取文件信息便捷函数"""
    return await minio_client.get_file_info(object_name)


async def delete_file(object_name: str) -> bool:
    """删除文件便捷函数"""
    return await minio_client.delete_file(object_name)


async def generate_presigned_url(
    object_name: str,
    expires: timedelta = timedelta(hours=1),
    method: str = "GET"
) -> str:
    """生成预签名URL便捷函数"""
    return await minio_client.generate_presigned_url(
        object_name=object_name,
        expires=expires,
        method=method
    )