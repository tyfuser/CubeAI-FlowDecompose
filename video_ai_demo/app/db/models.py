"""数据库模型"""
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum


Base = declarative_base()


class JobStatus(str, enum.Enum):
    """Job状态"""
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class JobMode(str, enum.Enum):
    """Job模式"""
    LEARN = "learn"
    COMPARE = "compare"


class Job(Base):
    """Job表"""
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True)
    mode = Column(SQLEnum(JobMode), nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.QUEUED, nullable=False)
    
    # 进度
    progress_stage = Column(String)  # 当前阶段
    progress_percent = Column(Float, default=0.0)  # 进度百分比
    progress_message = Column(String)  # 进度消息
    
    # 结果
    result_json = Column(Text)  # 最终JSON字符串
    partial_result_json = Column(Text)  # 部分结果JSON（流式更新）
    error_message = Column(Text)  # 错误信息
    error_details = Column(Text)  # 错误详情JSON
    
    # 总结信息
    title = Column(String)  # AI生成的任务标题
    learning_points_json = Column(Text)  # 学习要点JSON数组
    thumbnail_url = Column(String)  # 缩略图URL（可选）
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # 关联
    assets = relationship("Asset", back_populates="job", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="job", cascade="all, delete-orphan")


class AssetRole(str, enum.Enum):
    """资源角色"""
    TARGET = "target"
    USER = "user"


class Asset(Base):
    """资源表（视频输入）"""
    __tablename__ = "assets"
    
    id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    role = Column(SQLEnum(AssetRole), nullable=False)
    
    # 来源
    source_type = Column(String)  # url / file
    source_url = Column(String)
    source_path = Column(String)
    
    # 本地存储
    local_path = Column(String)
    
    # 元数据
    duration_ms = Column(Float)
    width = Column(Integer)
    height = Column(Integer)
    fps = Column(Float)
    codec = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    job = relationship("Job", back_populates="assets")


class ArtifactType(str, enum.Enum):
    """产物类型"""
    FRAMES = "frames"
    KEYFRAME = "keyframe"
    PREVIEW_VIDEO = "preview_video"
    RESULT_JSON = "result_json"


class Artifact(Base):
    """产物表（生成的文件）"""
    __tablename__ = "artifacts"
    
    id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    artifact_type = Column(SQLEnum(ArtifactType), nullable=False)
    
    # 存储
    file_path = Column(String)
    
    # 关联信息
    asset_role = Column(String)  # 关联的asset role
    segment_id = Column(String)  # 关联的segment id
    
    # 元数据
    metadata_json = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    job = relationship("Job", back_populates="artifacts")


class VirtualMotionJob(Base):
    """虚拟运镜子任务表"""
    __tablename__ = "virtual_motion_jobs"
    
    id = Column(String, primary_key=True)
    parent_job_id = Column(String, nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.QUEUED, nullable=False)
    
    # 输入参数
    asset_role = Column(String)
    segment_id = Column(String)
    motion_recipe_json = Column(Text)  # JSON字符串
    
    # 结果
    result_video_path = Column(String)
    error_message = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

