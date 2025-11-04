"""
工作流API端点 - Slow工作流完整集成
Workflow API Endpoints - Complete Slow Workflow Integration
"""

import os
import uuid
import hashlib
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks, Query
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.logger import get_logger
from app.core.celery_app import celery_app
from app.tasks.guideline_tasks import process_guideline_task, batch_process_guidelines
from app.services.slow_workflow_orchestrator import get_slow_workflow_orchestrator, WorkflowConfig, WorkflowStatus
from app.models.task import Task, TaskStatus as DBTaskStatus, TaskType, TaskPriority
from app.models.user import User

logger = get_logger(__name__)
settings = get_settings()
security = HTTPBearer()
router = APIRouter()


class WorkflowUploadRequest(BaseModel):
    """工作流上传请求"""
    title: str = Field(..., description="文档标题")
    description: Optional[str] = Field(None, description="文档描述")
    processing_mode: str = Field("slow", description="处理模式: slow/fast/thorough")
    priority: str = Field("normal", description="任务优先级: low/normal/high/urgent")
    enable_visualization: bool = Field(True, description="启用可视化")
    enable_caching: bool = Field(True, description="启用缓存")
    enable_cost_optimization: bool = Field(True, description="启用成本优化")
    enable_quality_control: bool = Field(True, description="启用质量控制")
    custom_config: Optional[Dict[str, Any]] = Field(None, description="自定义配置")
    tags: Optional[List[str]] = Field(None, description="标签")


class WorkflowUploadResponse(BaseModel):
    """工作流上传响应"""
    task_id: str
    guideline_id: str
    celery_task_id: str
    status: str
    message: str
    upload_time: datetime
    estimated_processing_time: int


class WorkflowStatusResponse(BaseModel):
    """工作流状态响应"""
    task_id: str
    guideline_id: str
    status: str
    current_phase: str
    progress_percentage: float
    current_node: Optional[str]
    completed_nodes: List[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_completion: Optional[datetime]
    processing_time: float
    total_cost: float
    tokens_used: int
    quality_score: Optional[float]
    error_message: Optional[str]
    retry_count: int
    output_files: List[str]
    worker_hostname: Optional[str]
    node_results: Dict[str, Any]


@router.post("/workflow/upload", response_model=WorkflowUploadResponse)
async def upload_guideline_workflow(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    processing_mode: str = Form("slow"),
    priority: str = Form("normal"),
    enable_visualization: bool = Form(True),
    enable_caching: bool = Form(True),
    enable_cost_optimization: bool = Form(True),
    enable_quality_control: bool = Form(True),
    custom_config: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db_session),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    上传并执行完整的Slow工作流处理
    """
    try:
        logger.info(f"Starting Slow workflow upload: {file.filename}")

        # 验证文件类型和大小
        await _validate_upload_file(file)

        # 生成唯一ID和文件路径
        guideline_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix.lower()
        safe_filename = f"{guideline_id}_{file.filename}"
        upload_path = Path(settings.UPLOAD_DIR) / "guidelines" / safe_filename

        # 确保目录存在
        upload_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存文件
        file_hash = await _save_uploaded_file(file, upload_path)

        # 解析自定义配置
        workflow_config = {}
        if custom_config:
            try:
                workflow_config = json.loads(custom_config)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid configuration JSON")

        # 解析标签
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # 创建工作流配置
        config = WorkflowConfig(
            processing_mode=processing_mode,
            enable_visualization=enable_visualization,
            enable_caching=enable_caching,
            enable_cost_optimization=enable_cost_optimization,
            enable_quality_control=enable_quality_control,
            **workflow_config
        )

        # 创建任务记录
        task_id = str(uuid.uuid4())
        task = Task(
            task_id=task_id,
            user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),  # 临时用户ID
            title=title,
            description=description,
            task_type=TaskType.FULL_PROCESSING,
            status=DBTaskStatus.PENDING,
            priority=TaskPriority(priority.upper()),
            guideline_id=guideline_id,
            original_filename=file.filename,
            file_path=str(upload_path),
            file_size=upload_path.stat().st_size,
            file_hash=file_hash,
            config=config.__dict__,
            tags=tag_list,
            metadata={
                "content_type": file.content_type,
                "processing_mode": processing_mode,
                "upload_ip": "client_ip",
                "workflow_type": "slow"
            }
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        # 提交异步处理任务到Celery
        celery_task = process_guideline_task.delay(
            guideline_id=guideline_id,
            file_path=str(upload_path),
            config={
                "processing_mode": processing_mode,
                "enable_visualization": enable_visualization,
                "enable_caching": enable_caching,
                "enable_cost_optimization": enable_cost_optimization,
                "enable_quality_control": enable_quality_control,
                "task_db_id": str(task.id),
                **workflow_config
            }
        )

        # 更新任务的Celery ID
        task.task_id = celery_task.id
        await db.commit()

        logger.info(f"Slow workflow uploaded successfully: {guideline_id}, task_id: {task.id}")

        return WorkflowUploadResponse(
            task_id=str(task.id),
            guideline_id=guideline_id,
            celery_task_id=celery_task.id,
            status="pending",
            message="Slow工作流已启动，正在处理医学指南",
            upload_time=datetime.utcnow(),
            estimated_processing_time=_estimate_processing_time(file.size, processing_mode)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload guideline for workflow: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/workflow/{task_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    task_id: str,
    db: AsyncSession = Depends(get_db_session),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    获取Slow工作流状态
    """
    try:
        # 从数据库获取任务
        result = await db.execute(
            "SELECT * FROM tasks WHERE id = :task_id OR task_id = :task_id",
            {"task_id": task_id}
        )
        task_data = result.fetchone()

        if not task_data:
            raise HTTPException(status_code=404, detail="工作流任务不存在")

        # 转换为Task对象
        task = Task(**task_data._mapping)

        # 如果任务仍在处理中，从Celery获取最新状态
        if task.status in [DBTaskStatus.PENDING, DBTaskStatus.RUNNING]:
            celery_result = celery_app.AsyncResult(task.task_id)
            if celery_result.state and celery_result.info:
                task.status = celery_result.state
                task.progress_percentage = celery_result.info.get('current', 0)
                task.current_phase = celery_result.info.get('phase', task.current_phase)
                task.current_node = celery_result.info.get('current_node', task.current_node)
                task.completed_nodes = celery_result.info.get('completed_nodes', task.completed_nodes)
                task.error_message = celery_result.info.get('error_message', task.error_message)

        # 获取节点结果
        node_results = task.result_data.get('node_results', {}) if task.result_data else {}

        return WorkflowStatusResponse(
            task_id=str(task.id),
            guideline_id=task.guideline_id,
            status=task.status,
            current_phase=task.current_phase,
            progress_percentage=task.progress_percentage,
            current_node=task.current_node,
            completed_nodes=task.completed_nodes,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            estimated_completion=task.estimated_completion,
            processing_time=task.processing_time,
            total_cost=task.total_cost,
            tokens_used=task.tokens_used,
            quality_score=task.quality_score,
            error_message=task.error_message,
            retry_count=task.retry_count,
            output_files=task.output_files or [],
            worker_hostname=task.worker_hostname,
            node_results=node_results
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        raise HTTPException(status_code=500, detail=f"获取工作流状态失败: {str(e)}")


@router.get("/workflow/{task_id}/stream")
async def stream_workflow_updates(
    task_id: str,
    db: AsyncSession = Depends(get_db_session),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    实时流式推送Slow工作流状态更新 (Server-Sent Events)
    """
    async def event_generator():
        try:
            # 验证任务存在
            result = await db.execute(
                "SELECT id, task_id FROM tasks WHERE id = :task_id OR task_id = :task_id",
                {"task_id": task_id}
            )
            task_data = result.fetchone()

            if not task_data:
                yield f"data: {json.dumps({'error': 'Workflow task not found'})}\n\n"
                return

            task = Task(**task_data._mapping)
            last_update = None

            while True:
                # 获取Celery最新状态
                celery_result = celery_app.AsyncResult(task.task_id)

                # 获取数据库中的最新状态
                current_result = await db.execute(
                    "SELECT * FROM tasks WHERE id = :task_id",
                    {"task_id": str(task.id)}
                )
                current_task = Task(**current_result.fetchone()._mapping)

                # 构建事件数据
                event_data = {
                    'type': 'workflow_update',
                    'task_id': str(current_task.id),
                    'guideline_id': current_task.guideline_id,
                    'status': current_task.status,
                    'progress_percentage': current_task.progress_percentage,
                    'current_phase': current_task.current_phase,
                    'current_node': current_task.current_node,
                    'completed_nodes': current_task.completed_nodes,
                    'error_message': current_task.error_message,
                    'updated_at': current_task.updated_at.isoformat() if current_task.updated_at else None
                }

                # 添加Celery状态信息
                if celery_result.info:
                    event_data.update({
                        'celery_state': celery_result.state,
                        'celery_info': celery_result.info
                    })

                # 检查是否有更新
                current_update = {
                    'status': current_task.status,
                    'progress': current_task.progress_percentage,
                    'phase': current_task.current_phase,
                    'updated_at': event_data['updated_at']
                }

                if current_update != last_update:
                    if current_task.status == DBTaskStatus.COMPLETED:
                        event_data['type'] = 'workflow_completed'
                        event_data.update({
                            'processing_time': current_task.processing_time,
                            'total_cost': current_task.total_cost,
                            'tokens_used': current_task.tokens_used,
                            'quality_score': current_task.quality_score,
                            'output_files': current_task.output_files,
                            'pvg_document_path': current_task.pvg_document_path
                        })
                        yield f"data: {json.dumps(event_data)}\n\n"
                        break

                    elif current_task.status == DBTaskStatus.FAILED:
                        event_data['type'] = 'workflow_failed'
                        yield f"data: {json.dumps(event_data)}\n\n"
                        break

                    else:
                        yield f"data: {json.dumps(event_data)}\n\n"
                        last_update = current_update

                # 检查任务是否完成
                if current_task.status in [DBTaskStatus.COMPLETED, DBTaskStatus.FAILED, DBTaskStatus.CANCELLED]:
                    break

                # 等待下次更新
                await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"Error in workflow stream: {e}")
            yield f"data: {json.dumps({'error': str(e), 'type': 'stream_error'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "X-Accel-Buffering": "no",  # 禁用nginx缓冲
        }
    )


@router.get("/workflow/{guideline_id}/pvg/download")
async def download_workflow_pvg(
    guideline_id: str,
    format: str = Query("json", description="下载格式: json/html/pdf"),
    db: AsyncSession = Depends(get_db_session),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    下载Slow工作流生成的PVG文档
    """
    try:
        # 查找已完成的任务
        result = await db.execute(
            "SELECT * FROM tasks WHERE guideline_id = :guideline_id AND status = 'completed'",
            {"guideline_id": guideline_id}
        )
        task_data = result.fetchone()

        if not task_data:
            raise HTTPException(status_code=404, detail="PVG文档不存在或处理未完成")

        task = Task(**task_data._mapping)

        # 检查PVG文档路径
        if not task.pvg_document_path:
            raise HTTPException(status_code=404, detail="PVG文档路径不存在")

        # 构建文件路径
        if format == "json":
            file_path = Path(task.pvg_document_path)
            filename = f"PVG_{guideline_id}.json"
            media_type = "application/json"
        elif format == "html":
            # 查找HTML文件
            json_path = Path(task.pvg_document_path)
            html_path = json_path.with_suffix('.html')
            if not html_path.exists():
                # 如果HTML不存在，生成它
                await _generate_html_output(task.pvg_document_path, html_path)
            file_path = html_path
            filename = f"PVG_{guideline_id}.html"
            media_type = "text/html"
        else:
            raise HTTPException(status_code=400, detail="不支持的格式")

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type=media_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download PVG: {e}")
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")


@router.post("/workflow/batch")
async def batch_workflow_upload(
    files: List[UploadFile] = File(...),
    processing_mode: str = Form("slow"),
    priority: str = Form("normal"),
    db: AsyncSession = Depends(get_db_session),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    批量Slow工作流处理
    """
    try:
        if len(files) > 5:  # 限制批量处理数量
            raise HTTPException(status_code=400, detail="批量处理最多支持5个文件")

        guideline_configs = []
        uploaded_files = []

        for file in files:
            # 验证文件
            await _validate_upload_file(file)

            # 生成唯一ID和路径
            guideline_id = str(uuid.uuid4())
            safe_filename = f"{guideline_id}_{file.filename}"
            upload_path = Path(settings.UPLOAD_DIR) / "guidelines" / safe_filename
            upload_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存文件
            file_hash = await _save_uploaded_file(file, upload_path)

            guideline_configs.append({
                "guideline_id": guideline_id,
                "file_path": str(upload_path),
                "config": {
                    "processing_mode": processing_mode,
                    "priority": priority,
                    "workflow_type": "slow_batch"
                }
            })

            uploaded_files.append({
                "guideline_id": guideline_id,
                "original_filename": file.filename,
                "file_size": upload_path.stat().st_size
            })

        # 提交批量处理任务
        batch_task = batch_process_guidelines.delay(guideline_configs)

        logger.info(f"Batch Slow workflow started: {len(files)} files, batch_task_id: {batch_task.id}")

        return {
            "batch_task_id": batch_task.id,
            "total_files": len(files),
            "uploaded_files": uploaded_files,
            "status": "processing",
            "message": f"开始批量Slow工作流处理 {len(files)} 个文件",
            "estimated_total_time": _estimate_processing_time(
                sum(f.size for f in files), processing_mode
            ) * len(files)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to batch workflow upload: {e}")
        raise HTTPException(status_code=500, detail=f"批量上传失败: {str(e)}")


@router.delete("/workflow/{task_id}")
async def cancel_workflow(
    task_id: str,
    db: AsyncSession = Depends(get_db_session),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    取消Slow工作流
    """
    try:
        # 查找任务
        result = await db.execute(
            "SELECT * FROM tasks WHERE id = :task_id OR task_id = :task_id",
            {"task_id": task_id}
        )
        task_data = result.fetchone()

        if not task_data:
            raise HTTPException(status_code=404, detail="工作流任务不存在")

        task = Task(**task_data._mapping)

        if task.status not in [DBTaskStatus.PENDING, DBTaskStatus.RUNNING]:
            raise HTTPException(status_code=400, detail="任务无法取消")

        # 取消Celery任务
        celery_app.control.revoke(task.task_id, terminate=True)

        # 获取工作流编排器并取消
        try:
            orchestrator = await get_slow_workflow_orchestrator()
            await orchestrator.cancel_workflow(task.task_id)
        except Exception as e:
            logger.warning(f"Failed to cancel workflow in orchestrator: {e}")

        # 更新数据库状态
        task.status = DBTaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()
        await db.commit()

        return {
            "message": "Slow工作流已取消",
            "task_id": str(task.id),
            "guideline_id": task.guideline_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel workflow: {e}")
        raise HTTPException(status_code=500, detail=f"取消工作流失败: {str(e)}")


# 辅助函数
async def _validate_upload_file(file: UploadFile):
    """验证上传文件"""
    # 检查文件大小
    if file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE} bytes)"
        )

    # 检查文件类型（使用共享常量）
    from shared.constants.file_types import ALLOWED_FILE_EXTENSIONS
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_extension}"
        )


async def _save_uploaded_file(file: UploadFile, file_path: Path) -> str:
    """保存上传文件并计算哈希"""
    hash_sha256 = hashlib.sha256()

    async with aiofiles.open(file_path, 'wb') as f:
        while chunk := await file.read(8192):
            hash_sha256.update(chunk)
            await f.write(chunk)

    return hash_sha256.hexdigest()


def _estimate_processing_time(file_size: int, processing_mode: str) -> int:
    """估算Slow工作流处理时间（秒）"""
    base_time = 300  # Slow工作流基础时间5分钟

    # 根据文件大小调整
    size_factor = max(1, file_size / (1024 * 1024))  # MB为单位

    # 根据处理模式调整
    if processing_mode == "slow":
        mode_multiplier = 3.0
    elif processing_mode == "thorough":
        mode_multiplier = 5.0
    else:
        mode_multiplier = 1.0

    return int(base_time * size_factor * mode_multiplier)


async def _generate_html_output(json_path: str, html_path: Path):
    """从JSON生成HTML输出"""
    try:
        import json
        from jinja2 import Template

        # 读取JSON数据
        with open(json_path, 'r', encoding='utf-8') as f:
            pvg_data = json.load(f)

        # HTML模板
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }
        h1 { color: #2c3e50; }
        h2 { color: #3498db; border-bottom: 2px solid #3498db; }
        h3 { color: #e74c3c; }
        .metadata { background: #f8f9fa; padding: 15px; border-radius: 5px; }
        .section { margin: 20px 0; }
        .emergency { background: #ffe6e6; padding: 15px; border-radius: 5px; }
        .quality-score { background: #e8f5e8; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>

    <div class="metadata">
        <p><strong>文档ID:</strong> {{ document_id }}</p>
        <p><strong>指南ID:</strong> {{ guideline_id }}</p>
        <p><strong>版本:</strong> {{ version }}</p>
        <p><strong>生成时间:</strong> {{ created_at }}</p>
        <p><strong>总章节:</strong> {{ sections|length }}</p>
        {% if quality_score %}
        <div class="quality-score">
            <p><strong>质量评分:</strong> {{ "%.2f"|format(quality_score) }}/1.0</p>
        </div>
        {% endif %}
    </div>

    {% for section in sections %}
    <div class="section {% if section.section_type == 'emergency_guidance' %}emergency{% endif %}">
        <h2>{{ section.title }}</h2>
        <div>{{ section.html_content or section.content }}</div>
    </div>
    {% endfor %}
</body>
</html>
        """

        template = Template(html_template)
        html_content = template.render(
            title=pvg_data.get('title', 'PVG Document'),
            document_id=pvg_data.get('document_id'),
            guideline_id=pvg_data.get('guideline_id'),
            version=pvg_data.get('version', '1.0'),
            created_at=pvg_data.get('created_at', ''),
            sections=pvg_data.get('sections', []),
            quality_score=pvg_data.get('quality_score')
        )

        # 保存HTML文件
        async with aiofiles.open(html_path, 'w', encoding='utf-8') as f:
            await f.write(html_content)

    except Exception as e:
        logger.error(f"Failed to generate HTML output: {e}")
        raise