"""
Realtime Advisor Data Types

实时建议系统的数据类型定义。
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, TypedDict
import time

from src.models.data_types import BBox
from src.models.enums import MotionType


class AdvicePriority(str, Enum):
    """
    建议优先级枚举
    Advice priority levels for display and haptic feedback.
    """
    CRITICAL = "critical"  # Red - severe issues, triggers haptic
    WARNING = "warning"    # Yellow - moderate issues
    INFO = "info"          # Blue - informational
    POSITIVE = "positive"  # Green - encouragement


class AdviceCategory(str, Enum):
    """
    建议类别枚举
    Categories of shooting advice.
    """
    STABILITY = "stability"      # 稳定性建议
    SPEED = "speed"              # 速度建议
    COMPOSITION = "composition"  # 构图建议
    BEAT = "beat"                # 节拍同步建议
    EQUIPMENT = "equipment"      # 设备建议


@dataclass
class RealtimeAnalysisResult:
    """
    实时分析结果
    Result of realtime frame buffer analysis.
    """
    # Raw indicators
    avg_speed_px_frame: float
    speed_variance: float
    motion_smoothness: float
    primary_direction_deg: float

    # Subject tracking
    subject_bbox: Optional[BBox] = None
    subject_occupancy: float = 0.0
    subject_lost: bool = False

    # Environment features
    brightness: float = 0.5  # 0-1, average brightness
    contrast: float = 0.5    # 0-1, image contrast measure
    sharpness: float = 0.5   # 0-1, image sharpness/blurriness
    saturation: float = 0.5  # 0-1, color saturation
    dominant_light: str = "neutral"  # warm/cool/neutral lighting
    composition_score: float = 0.5   # 0-1, rule of thirds compliance

    # Timing
    analysis_latency_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)

    # Confidence
    confidence: float = 0.5
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "avg_speed_px_frame": self.avg_speed_px_frame,
            "speed_variance": self.speed_variance,
            "motion_smoothness": self.motion_smoothness,
            "primary_direction_deg": self.primary_direction_deg,
            "subject_bbox": self.subject_bbox.to_list() if self.subject_bbox else None,
            "subject_occupancy": self.subject_occupancy,
            "subject_lost": self.subject_lost,
            "brightness": self.brightness,
            "contrast": self.contrast,
            "sharpness": self.sharpness,
            "saturation": self.saturation,
            "dominant_light": self.dominant_light,
            "composition_score": self.composition_score,
            "analysis_latency_ms": self.analysis_latency_ms,
            "timestamp": self.timestamp,
            "confidence": self.confidence,
        }


@dataclass
class AdvicePayload:
    """
    建议载荷
    Advice payload for WebSocket transmission.
    """
    priority: AdvicePriority
    category: AdviceCategory
    message: str
    advanced_message: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    suppress_duration_s: float = 3.0
    trigger_haptic: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": "advice",
            "priority": self.priority.value,
            "category": self.category.value,
            "message": self.message,
            "advanced_message": self.advanced_message,
            "timestamp": int(self.timestamp * 1000),
            "suppress_duration_ms": int(self.suppress_duration_s * 1000),
            "trigger_haptic": self.trigger_haptic,
        }
    
    def with_substitution(self, **kwargs) -> "AdvicePayload":
        """
        Create a new AdvicePayload with template variables substituted.
        
        Args:
            **kwargs: Template variables to substitute (e.g., direction="左")
            
        Returns:
            New AdvicePayload with substituted message
        """
        new_message = self.message.format(**kwargs) if kwargs else self.message
        new_advanced = None
        if self.advanced_message:
            new_advanced = self.advanced_message.format(**kwargs) if kwargs else self.advanced_message
        
        return AdvicePayload(
            priority=self.priority,
            category=self.category,
            message=new_message,
            advanced_message=new_advanced,
            timestamp=time.time(),
            suppress_duration_s=self.suppress_duration_s,
            trigger_haptic=self.trigger_haptic,
        )


@dataclass
class SessionState:
    """
    会话状态
    State for a realtime analysis session.
    """
    session_id: str
    created_at: float = field(default_factory=time.time)
    
    # Analysis state
    motion_state: MotionType = MotionType.STATIC
    
    # Subject tracking state
    subject_lost_since: Optional[float] = None
    
    # Performance metrics
    total_analyses: int = 0
    avg_latency_ms: float = 0.0
    
    def update_latency(self, latency_ms: float) -> None:
        """Update average latency with new measurement."""
        if self.total_analyses == 0:
            self.avg_latency_ms = latency_ms
        else:
            # Exponential moving average
            alpha = 0.2
            self.avg_latency_ms = alpha * latency_ms + (1 - alpha) * self.avg_latency_ms
        self.total_analyses += 1
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "motion_state": self.motion_state.value,
            "subject_lost_since": self.subject_lost_since,
            "total_analyses": self.total_analyses,
            "avg_latency_ms": self.avg_latency_ms,
        }


class FrameBufferPayload(TypedDict):
    """
    帧缓冲区载荷
    WebSocket payload format for frame buffer (Mobile → Server).
    """
    type: str  # "frames"
    session_id: str
    frames: list[str]  # Base64-encoded JPEG images
    fps: float
    timestamp: int  # Unix timestamp in ms


class RealtimeAdvicePayload(TypedDict):
    """
    实时建议载荷
    WebSocket payload format for advice (Server → Mobile).
    """
    type: str  # "advice"
    priority: str  # critical/warning/info/positive
    category: str
    message: str
    advanced_message: Optional[str]
    timestamp: int  # Unix timestamp in ms
    suppress_duration_ms: int
    trigger_haptic: bool


class TelemetryPayload(TypedDict):
    """
    遥测数据载荷
    WebSocket payload format for realtime telemetry data (Server → Mobile).
    """
    type: str  # "telemetry"
    avg_speed_px_frame: float
    speed_variance: float
    motion_smoothness: float
    primary_direction_deg: float
    subject_occupancy: float
    confidence: float
    timestamp: int  # Unix timestamp in ms


class TaskPayload(TypedDict):
    """
    任务载荷
    WebSocket payload format for task information (Server → Mobile).
    """
    type: str  # "task"
    task_id: str
    task_name: str
    description: str
    target_duration_s: float
    risk_level: str
    success_criteria: str
    target_motion: Optional[str]
    target_speed_range: Optional[list[float]]
    state: str  # TaskState value
    progress: float  # 0-1
    timestamp: int  # Unix timestamp in ms


class EnvironmentAnalysisPayload(TypedDict):
    """
    环境分析载荷
    WebSocket payload format for environment analysis results (Server → Mobile).
    """
    type: str  # "environment"
    environment_tags: list[str]
    shootability_score: float
    constraints: list[str]
    recommended_risk_level: str
    theme_candidates: list[str]
    confidence: float
    timestamp: int  # Unix timestamp in ms


class ErrorPayload(TypedDict):
    """
    错误载荷
    WebSocket payload format for errors.
    """
    type: str  # "error"
    code: str
    message: str
    recoverable: bool
    timestamp: int


# Error codes and messages
ERROR_CODES: dict[str, tuple[str, bool]] = {
    "CAMERA_ACCESS_DENIED": ("无法访问摄像头，请检查权限设置", True),
    "ANALYSIS_TIMEOUT": ("分析超时，正在切换到轻量模式", True),
    "CONNECTION_LOST": ("连接已断开，正在重连...", True),
    "SESSION_EXPIRED": ("会话已过期，请重新扫码", False),
    "RESOURCE_EXHAUSTED": ("设备资源不足，建议关闭其他应用", True),
}
