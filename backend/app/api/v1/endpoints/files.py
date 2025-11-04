"""
文件管理API端点
File Management API Endpoints
"""

import os
import mimetypes
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.auth import get_current_active_user
from app.core.file_manager import get_file_manager
from app.models.user import User
from app.core.error_handling import CPG2PVGException

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    file_manager = Depends(get_file_manager),
    db: AsyncSession = Depends(get_db_session)
):
    """
    上传文件
    """
    try:
        # 验证文件大小
        if file.size and file.size > 100 * 1024 * 1024:  # 100MB
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="文件大小超过限制(100MB)"
            )

        # 验证文件类型
        allowed_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
            'text/plain',
            'text/markdown',
            'text/html'
        ]

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {file.content_type}"
            )

        # 读取文件内容
        content = await file.read()

        # 保存文件
        file_info = await file_manager.save_uploaded_file(
            file_content=content,
            original_filename=file.filename,
            user_id=str(current_user.id)
        )

        return {
            "message": "文件上传成功",
            "file_info": {
                "file_id": file_info["file_id"],
                "original_filename": file_info["original_filename"],
                "file_size": file_info["file_size"],
                "file_type": file_info["file_type"],
                "file_hash": file_info["file_hash"],
                "upload_time": file_info["upload_time"]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}"
        )


@router.get("/download/{file_path:path}")
async def download_file(
    file_path: str,
    current_user: User = Depends(get_current_active_user),
    file_manager = Depends(get_file_manager)
):
    """
    下载文件
    """
    try:
        # 验证路径安全性
        if not file_manager.is_safe_path(file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的文件路径"
            )

        # 获取文件信息
        full_path = file_manager.get_full_path(file_path)

        if not os.path.exists(full_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )

        # 获取MIME类型
        mime_type, _ = mimetypes.guess_type(file_path)

        return FileResponse(
            path=full_path,
            filename=os.path.basename(file_path),
            media_type=mime_type or "application/octet-stream"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件下载失败: {str(e)}"
        )


@router.delete("/{file_path:path}")
async def delete_file(
    file_path: str,
    current_user: User = Depends(get_current_active_user),
    file_manager = Depends(get_file_manager)
):
    """
    删除文件
    """
    try:
        # 验证路径安全性
        if not file_manager.is_safe_path(file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的文件路径"
            )

        # 删除文件
        success = await file_manager.delete_file(file_path, user_id=str(current_user.id))

        if success:
            return {"message": "文件删除成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在或无权限删除"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件删除失败: {str(e)}"
        )


@router.get("/list")
async def list_files(
    path: Optional[str] = "",
    current_user: User = Depends(get_current_active_user),
    file_manager = Depends(get_file_manager)
):
    """
    列出文件
    """
    try:
        files = await file_manager.list_files(
            path=path,
            user_id=str(current_user.id)
        )

        return {
            "files": files,
            "total_count": len(files)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件列表获取失败: {str(e)}"
        )


@router.get("/stats")
async def get_storage_stats(
    current_user: User = Depends(get_current_active_user),
    file_manager = Depends(get_file_manager)
):
    """
    获取存储统计信息
    """
    try:
        stats = await file_manager.get_storage_stats(user_id=str(current_user.id))

        return {
            "total_files": stats.get("total_files", 0),
            "total_size": stats.get("total_size", 0),
            "file_types": stats.get("file_types", {}),
            "quota_used": stats.get("quota_used", 0),
            "quota_total": getattr(current_user, 'storage_quota', 1073741824),  # 1GB默认
            "quota_percentage": stats.get("quota_percentage", 0)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"存储统计获取失败: {str(e)}"
        )