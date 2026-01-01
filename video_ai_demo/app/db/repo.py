"""数据仓储层"""
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import json

from .models import Job, JobStatus, Asset, Artifact, VirtualMotionJob
from ..core.errors import JobNotFoundError


class JobRepository:
    """Job仓储"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, job: Job) -> Job:
        """创建Job"""
        self.db.add(job)
        self.db.flush()
        return job
    
    def get(self, job_id: str) -> Optional[Job]:
        """获取Job"""
        return self.db.query(Job).filter(Job.id == job_id).first()
    
    def get_or_raise(self, job_id: str) -> Job:
        """获取Job，不存在则抛异常"""
        job = self.get(job_id)
        if not job:
            raise JobNotFoundError(f"Job {job_id} 不存在")
        return job
    
    def update_status(
        self,
        job_id: str,
        status: JobStatus,
        error_message: Optional[str] = None,
        error_details: Optional[dict] = None
    ) -> Job:
        """更新Job状态"""
        job = self.get_or_raise(job_id)
        job.status = status
        job.updated_at = datetime.utcnow()
        
        if status == JobStatus.RUNNING and not job.started_at:
            job.started_at = datetime.utcnow()
        
        if status in [JobStatus.SUCCEEDED, JobStatus.FAILED]:
            job.completed_at = datetime.utcnow()
        
        if error_message:
            job.error_message = error_message
        
        if error_details:
            job.error_details = json.dumps(error_details, ensure_ascii=False)
        
        self.db.flush()
        return job
    
    def update_progress(
        self,
        job_id: str,
        stage: str,
        percent: float,
        message: Optional[str] = None
    ) -> Job:
        """更新Job进度"""
        job = self.get_or_raise(job_id)
        job.progress_stage = stage
        job.progress_percent = percent
        job.progress_message = message
        job.updated_at = datetime.utcnow()
        self.db.flush()
        return job
    
    def save_result(self, job_id: str, result: dict) -> Job:
        """保存Job最终结果"""
        job = self.get_or_raise(job_id)
        job.result_json = json.dumps(result, ensure_ascii=False)
        job.updated_at = datetime.utcnow()
        self.db.flush()
        return job
    
    def save_partial_result(self, job_id: str, partial_result: dict) -> Job:
        """保存Job部分结果（用于流式更新）"""
        job = self.get_or_raise(job_id)
        job.partial_result_json = json.dumps(partial_result, ensure_ascii=False)
        job.updated_at = datetime.utcnow()
        self.db.flush()
        return job
    
    def update_summary(
        self,
        job_id: str,
        title: Optional[str] = None,
        learning_points: Optional[List[str]] = None,
        thumbnail_url: Optional[str] = None
    ) -> Job:
        """更新Job总结信息"""
        job = self.get_or_raise(job_id)
        if title:
            job.title = title
        if learning_points:
            job.learning_points_json = json.dumps(learning_points, ensure_ascii=False)
        if thumbnail_url:
            job.thumbnail_url = thumbnail_url
        job.updated_at = datetime.utcnow()
        self.db.flush()
        return job
    
    def list_history(self, limit: int = 50) -> List[Job]:
        """获取历史记录列表"""
        return self.db.query(Job).order_by(Job.created_at.desc()).limit(limit).all()
    
    def delete(self, job_id: str) -> bool:
        """删除Job"""
        job = self.get(job_id)
        if not job:
            return False
        self.db.delete(job)
        self.db.flush()
        return True


class AssetRepository:
    """Asset仓储"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, asset: Asset) -> Asset:
        """创建Asset"""
        self.db.add(asset)
        self.db.flush()
        return asset
    
    def get_by_job_and_role(self, job_id: str, role: str) -> Optional[Asset]:
        """根据Job和角色获取Asset"""
        return self.db.query(Asset).filter(
            Asset.job_id == job_id,
            Asset.role == role
        ).first()


class ArtifactRepository:
    """Artifact仓储"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, artifact: Artifact) -> Artifact:
        """创建Artifact"""
        self.db.add(artifact)
        self.db.flush()
        return artifact
    
    def list_by_job(self, job_id: str) -> List[Artifact]:
        """列出Job的所有Artifact"""
        return self.db.query(Artifact).filter(Artifact.job_id == job_id).all()


class VirtualMotionJobRepository:
    """虚拟运镜Job仓储"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, vm_job: VirtualMotionJob) -> VirtualMotionJob:
        """创建虚拟运镜Job"""
        self.db.add(vm_job)
        self.db.flush()
        return vm_job
    
    def get(self, vm_job_id: str) -> Optional[VirtualMotionJob]:
        """获取虚拟运镜Job"""
        return self.db.query(VirtualMotionJob).filter(
            VirtualMotionJob.id == vm_job_id
        ).first()
    
    def update_status(
        self,
        vm_job_id: str,
        status: JobStatus,
        result_video_path: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> VirtualMotionJob:
        """更新虚拟运镜Job状态"""
        vm_job = self.get(vm_job_id)
        if not vm_job:
            raise JobNotFoundError(f"虚拟运镜Job {vm_job_id} 不存在")
        
        vm_job.status = status
        vm_job.updated_at = datetime.utcnow()
        
        if status in [JobStatus.SUCCEEDED, JobStatus.FAILED]:
            vm_job.completed_at = datetime.utcnow()
        
        if result_video_path:
            vm_job.result_video_path = result_video_path
        
        if error_message:
            vm_job.error_message = error_message
        
        self.db.flush()
        return vm_job

