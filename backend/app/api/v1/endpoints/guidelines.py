"""
指南管理端点
CPG2PVG-AI System Guidelines API
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
import uuid
import os
from datetime import datetime

from app.core.database import get_db
from app.models.guideline import Guideline, GuidelineStatus
from app.schemas.guideline import GuidelineCreate, GuidelineResponse, GuidelineListResponse
from sqlalchemy import func, or_

router = APIRouter()


@router.post("/upload", response_model=GuidelineResponse)
async def upload_guideline(
    file: UploadFile = File(...),
    mode: str = Form("slow"),
    user_id: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """上传医学指南文件"""

    # 文件验证（使用共享常量）
    from shared.constants.file_types import ALLOWED_FILE_EXTENSIONS, FileValidationConfig

    if file.size > FileValidationConfig.MAX_SIZE:  # 50MB
        raise HTTPException(status_code=413, detail="文件大小超过限制")

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    # 保存文件
    file_hash = f"{uuid.uuid4().hex}"
    file_path = f"uploads/{file_hash}_{file.filename}"

    try:
        # 这里应该实现实际的文件保存逻辑
        # await save_uploaded_file(file, file_path)

        # 创建数据库记录
        guideline = Guideline(
            title=f"指南: {file.filename}",
            original_filename=file.filename,
            file_path=file_path,
            file_size=file.size,
            file_type=file_ext,
            file_hash=file_hash,
            uploaded_by=user_id,
            processing_mode=mode
        )

        db.add(guideline)
        await db.commit()
        await db.refresh(guideline)

        # TODO: 启动异步处理任务
        # process_guideline_task.delay(guideline.id, mode)

        return guideline

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/", response_model=GuidelineListResponse)
async def get_guidelines(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """获取指南列表"""

    # 构建查询
    query = select(Guideline)
    count_query = select(func.count(Guideline.id))

    # 添加过滤条件
    conditions = []

    if status:
        conditions.append(Guideline.status == GuidelineStatus(status))

    if user_id:
        conditions.append(Guideline.uploaded_by == user_id)

    if search:
        conditions.append(
            or_(
                Guideline.title.ilike(f"%{search}%"),
                Guideline.description.ilike(f"%{search}%")
            )
        )

    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))

    # 分页
    offset = (page - 1) * size
    query = query.order_by(Guideline.created_at.desc()).offset(offset).limit(size)

    # 执行查询
    result = await db.execute(query)
    guidelines = result.scalars().all()

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return GuidelineListResponse(
        items=guidelines,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/{guideline_id}", response_model=GuidelineResponse)
async def get_guideline(
    guideline_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取指南详情"""

    guideline = await db.get(Guideline, guideline_id)
    if not guideline:
        raise HTTPException(status_code=404, detail="指南不存在")

    return guideline


@router.delete("/{guideline_id}")
async def delete_guideline(
    guideline_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除指南"""

    guideline = await db.get(Guideline, guideline_id)
    if not guideline:
        raise HTTPException(status_code=404, detail="指南不存在")

    # TODO: 删除文件
    # await delete_file(guideline.file_path)

    await db.delete(guideline)
    await db.commit()

    return {"message": "指南删除成功"}