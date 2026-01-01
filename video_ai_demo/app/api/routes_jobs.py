"""Job相关API路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import json

from ..db.session import get_db
from ..db.repo import JobRepository
from ..db.models import Job, JobMode, JobStatus
from ..pipeline.orchestrator import submit_job
from ..core.logging import logger


router = APIRouter(prefix="/v1/video-analysis", tags=["jobs"])


# ===== 历史记录响应模型 =====

class HistoryItem(BaseModel):
    """历史记录项"""
    job_id: str
    title: Optional[str] = None
    status: str
    learning_points: List[str] = []
    segment_count: Optional[int] = None
    duration_sec: Optional[float] = None
    thumbnail_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== 请求模型 =====

class VideoSource(BaseModel):
    """视频来源"""
    type: str = Field(..., description="url 或 file")
    url: Optional[str] = None
    path: Optional[str] = None


class VideoInput(BaseModel):
    """视频输入"""
    source: VideoSource


class FrameExtractOptions(BaseModel):
    """抽帧选项"""
    fps: float = Field(default=2.0, ge=0.1, le=10.0)
    max_frames: int = Field(default=240, ge=10, le=1000)


class AnalysisOptions(BaseModel):
    """分析选项"""
    enabled_modules: List[str] = Field(
        default=["camera_motion", "lighting", "color_grading"]
    )


class CompareOptions(BaseModel):
    """对比选项"""
    enabled: bool = True
    virtual_camera_motion: Dict[str, Any] = Field(default={"enabled": True})


class LLMOptions(BaseModel):
    """LLM选项"""
    provider: str = "sophnet"
    model: Optional[str] = None


class JobOptions(BaseModel):
    """Job选项"""
    frame_extract: FrameExtractOptions = Field(default_factory=FrameExtractOptions)
    analysis: AnalysisOptions = Field(default_factory=AnalysisOptions)
    compare: Optional[CompareOptions] = None
    llm: LLMOptions = Field(default_factory=LLMOptions)


class CreateJobRequest(BaseModel):
    """创建Job请求"""
    mode: str = Field(..., description="learn 或 compare")
    target_video: VideoInput
    user_video: Optional[VideoInput] = None
    options: JobOptions = Field(default_factory=JobOptions)


class CreateJobResponse(BaseModel):
    """创建Job响应"""
    job_id: str
    status: str
    status_url: str


# ===== 响应模型 =====

class JobProgress(BaseModel):
    """Job进度"""
    stage: Optional[str] = None
    percent: float = 0.0
    message: Optional[str] = None


class JobErrorInfo(BaseModel):
    """Job错误信息"""
    message: str
    details: Optional[Dict[str, Any]] = None


class JobResponse(BaseModel):
    """Job响应"""
    job_id: str
    mode: str
    status: str
    progress: Optional[JobProgress] = None
    result: Optional[Dict[str, Any]] = None
    partial_result: Optional[Dict[str, Any]] = None  # 部分结果（流式更新）
    error: Optional[JobErrorInfo] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ===== 路由处理 =====

@router.post("/jobs", response_model=CreateJobResponse)
async def create_job(request: CreateJobRequest):
    """创建视频分析Job"""
    
    logger.info(f"创建Job: mode={request.mode}")
    
    # 校验
    if request.mode not in ["learn", "compare"]:
        raise HTTPException(status_code=400, detail=f"不支持的mode: {request.mode}")
    
    if request.mode == "compare" and not request.user_video:
        raise HTTPException(status_code=400, detail="compare模式需要提供user_video")
    
    # 生成Job ID
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    
    # 创建Job记录
    with get_db() as db:
        job_repo = JobRepository(db)
        
        job = Job(
            id=job_id,
            mode=JobMode(request.mode),
            status=JobStatus.QUEUED
        )
        
        job_repo.create(job)
    
    # 构建Job配置
    job_config = {
        "mode": request.mode,
        "target_video": request.target_video.dict(),
        "user_video": request.user_video.dict() if request.user_video else None,
        "options": {
            "frame_extract": request.options.frame_extract.dict(),
            "llm": {
                "provider": request.options.llm.provider,
                "model": request.options.llm.model,
                "enabled_modules": request.options.analysis.enabled_modules
            }
        }
    }
    
    # 提交到运行器（异步执行）
    await submit_job(job_id, job_config)
    
    return CreateJobResponse(
        job_id=job_id,
        status="queued",
        status_url=f"/v1/video-analysis/jobs/{job_id}"
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """查询Job状态"""
    
    with get_db() as db:
        job_repo = JobRepository(db)
        job = job_repo.get(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} 不存在")
        
        # 构建响应
        response = JobResponse(
            job_id=job.id,
            mode=job.mode.value,
            status=job.status.value,
            created_at=job.created_at,
            updated_at=job.updated_at,
            started_at=job.started_at,
            completed_at=job.completed_at
        )
        
        # 进度
        if job.status == JobStatus.RUNNING:
            response.progress = JobProgress(
                stage=job.progress_stage,
                percent=job.progress_percent,
                message=job.progress_message
            )
        
        # 最终结果
        if job.status == JobStatus.SUCCEEDED and job.result_json:
            try:
                response.result = json.loads(job.result_json)
            except json.JSONDecodeError:
                logger.error(f"Job {job_id} 结果JSON解析失败")
        
        # 部分结果（用于流式显示）
        if job.status == JobStatus.RUNNING and job.partial_result_json:
            try:
                response.partial_result = json.loads(job.partial_result_json)
            except json.JSONDecodeError:
                logger.error(f"Job {job_id} 部分结果JSON解析失败")
        
        # 错误
        if job.status == JobStatus.FAILED:
            error_details = None
            if job.error_details:
                try:
                    error_details = json.loads(job.error_details)
                except json.JSONDecodeError:
                    pass
            
            response.error = JobErrorInfo(
                message=job.error_message or "未知错误",
                details=error_details
            )
        
        return response


@router.get("/history", response_model=List[HistoryItem])
async def get_history(limit: int = 50):
    """
    获取历史记录列表
    
    Args:
        limit: 返回数量限制，默认50
    
    Returns:
        历史记录列表
    """
    try:
        with get_db() as db:
            job_repo = JobRepository(db)
            jobs = job_repo.list_history(limit=limit)
            
            history_items = []
            for job in jobs:
                # 解析结果获取统计信息
                segment_count = None
                duration_sec = None
                
                if job.result_json:
                    try:
                        result = json.loads(job.result_json)
                        target = result.get("target", {})
                        segments = target.get("segments", [])
                        segment_count = len(segments)
                        if segments:
                            duration_sec = segments[-1].get("end_ms", 0) / 1000
                    except:
                        pass
                
                # 解析学习要点
                learning_points = []
                if job.learning_points_json:
                    try:
                        learning_points = json.loads(job.learning_points_json)
                    except:
                        pass
                
                history_items.append(HistoryItem(
                    job_id=job.id,
                    title=job.title,
                    status=job.status.value,
                    learning_points=learning_points,
                    segment_count=segment_count,
                    duration_sec=duration_sec,
                    thumbnail_url=job.thumbnail_url,
                    created_at=job.created_at
                ))
            
            return history_items
    
    except Exception as e:
        logger.error(f"获取历史记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    删除指定的 Job 及其相关数据
    
    Args:
        job_id: Job ID
    
    Returns:
        删除结果
    """
    try:
        import shutil
        from pathlib import Path
        from ..core.config import settings
        
        with get_db() as db:
            job_repo = JobRepository(db)
            
            # 检查 Job 是否存在
            job = job_repo.get(job_id)
            if not job:
                raise HTTPException(status_code=404, detail=f"Job {job_id} 不存在")
            
            # 删除文件系统中的数据
            job_dir = settings.data_dir / "jobs" / job_id
            if job_dir.exists():
                try:
                    shutil.rmtree(job_dir)
                    logger.info(f"已删除 Job {job_id} 的文件: {job_dir}")
                except Exception as e:
                    logger.warning(f"删除 Job {job_id} 文件失败: {str(e)}")
            
            # 从数据库中删除 Job（级联删除相关的 assets 和 artifacts）
            db.delete(job)
            db.commit()
            
            logger.info(f"Job {job_id} 已成功删除")
            
            return {
                "success": True,
                "message": f"Job {job_id} 已删除",
                "job_id": job_id
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除 Job {job_id} 失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

