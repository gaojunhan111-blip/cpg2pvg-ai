"""
任务管理端点
CPG2PVG-AI System Tasks API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import json
import asyncio
from fastapi.responses import StreamingResponse

from app.core.database import get_db
from app.models.task import Task, TaskStatus
from app.models.guideline import Guideline
from app.schemas.task import TaskResponse, TaskListResponse, TaskProgressUpdate

router = APIRouter()


@router.get("/", response_model=TaskListResponse)
async def get_tasks(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """获取任务列表"""

    query = select(Task)
    count_query = select(func.count(Task.id))

    # 添加过滤条件
    if status:
        query = query.where(Task.status == TaskStatus(status))
        count_query = count_query.where(Task.status == TaskStatus(status))

    if user_id:
        # 这里需要通过guideline关联查找用户任务
        query = query.join(Task.guideline).where(Guideline.uploaded_by == user_id)
        count_query = count_query.join(Task.guideline).where(Guideline.uploaded_by == user_id)

    # 分页
    offset = (page - 1) * size
    query = query.order_by(Task.created_at.desc()).offset(offset).limit(size)

    result = await db.execute(query)
    tasks = result.scalars().all()

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return TaskListResponse(
        items=tasks,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取任务详情"""

    result = await db.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task


@router.get("/{task_id}/stream")
async def stream_task_updates(task_id: str):
    """SSE流式返回任务实时进度"""

    async def event_generator():
        while True:
            try:
                # 从数据库获取最新任务状态
                # 这里需要实现异步的数据库查询
                # async with AsyncSessionLocal() as db:
                #     task = await db.get(Task, task_id)
                #     if task:
                #         progress = await task_service.get_task_progress(task_id)
                #         yield f"data: {json.dumps(progress.dict())}\n\n"

                # 模拟数据
                mock_data = {
                    "task_id": task_id,
                    "status": "processing",
                    "progress_percentage": 75,
                    "current_step": "智能体处理",
                    "message": "正在处理医学内容..."
                }
                yield f"data: {json.dumps(mock_data)}\n\n"

                # 每2秒更新一次
                await asyncio.sleep(2)

            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.delete("/{task_id}")
async def cancel_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """取消任务"""

    result = await db.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status not in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
        raise HTTPException(status_code=400, detail="任务无法取消")

    task.status = TaskStatus.CANCELLED
    await db.commit()

    # TODO: 取消Celery任务
    # celery_app.control.revoke(task_id, terminate=True)

    return {"message": "任务已取消"}