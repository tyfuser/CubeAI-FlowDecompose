"""
SQLAlchemy database models for the Video Shooting Assistant.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class AnalysisTask(Base):
    """
    视频分析任务表
    Stores video analysis tasks and their intermediate results.
    """
    __tablename__ = "analysis_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(String(255), nullable=False, index=True)
    status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Intermediate results stored as JSONB
    uploader_output = Column(JSONB, nullable=True)
    feature_output = Column(JSONB, nullable=True)
    heuristic_output = Column(JSONB, nullable=True)
    metadata_output = Column(JSONB, nullable=True)
    instruction_card = Column(JSONB, nullable=True)
    
    # Relationships
    feedbacks = relationship("UserFeedback", back_populates="task", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="valid_status"
        ),
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_video_id", "video_id"),
    )
    
    def __repr__(self) -> str:
        return f"<AnalysisTask(id={self.id}, video_id={self.video_id}, status={self.status})>"


class UserFeedback(Base):
    """
    用户反馈表
    Stores user feedback on generated instruction cards.
    """
    __tablename__ = "user_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("analysis_tasks.id"), nullable=False)
    instruction_index = Column(Integer, nullable=True)
    action = Column(String(50), nullable=False)  # accept, modify, ignore
    rating = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    task = relationship("AnalysisTask", back_populates="feedbacks")
    
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="valid_rating"),
        Index("idx_feedback_task_id", "task_id"),
    )
    
    def __repr__(self) -> str:
        return f"<UserFeedback(id={self.id}, task_id={self.task_id}, action={self.action})>"


class ReferenceVideo(Base):
    """
    参考视频索引表
    Stores reference videos for similarity search.
    """
    __tablename__ = "reference_videos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_path = Column(String(500), nullable=False)
    motion_type = Column(String(50), nullable=True, index=True)
    subject_type = Column(String(100), nullable=True)
    embedding_id = Column(String(255), nullable=True)  # FAISS index ID
    video_metadata = Column(JSONB, nullable=True)  # renamed from 'metadata' to avoid SQLAlchemy conflict
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_reference_motion_type", "motion_type"),
    )
    
    def __repr__(self) -> str:
        return f"<ReferenceVideo(id={self.id}, motion_type={self.motion_type})>"


def get_engine(database_url: str):
    """Create database engine."""
    return create_engine(database_url, echo=False)


def get_session_factory(engine):
    """Create session factory."""
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db(database_url: str):
    """Initialize database and create all tables."""
    engine = get_engine(database_url)
    Base.metadata.create_all(bind=engine)
    return engine
