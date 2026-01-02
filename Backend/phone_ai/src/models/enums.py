"""
Enumeration types for the Video Shooting Assistant.

Defines all enum types used across the system for motion types,
speed profiles, and suggested scales.
"""
from enum import Enum


class MotionType(str, Enum):
    """
    相机运动类型枚举
    Camera motion type classification.
    """
    DOLLY_IN = "dolly_in"       # 推镜头
    DOLLY_OUT = "dolly_out"     # 拉镜头
    PAN = "pan"                 # 横摇
    TILT = "tilt"               # 纵摇
    TRACK = "track"             # 跟踪
    HANDHELD = "handheld"       # 手持
    STATIC = "static"           # 静止
    
    @classmethod
    def values(cls) -> list[str]:
        """Return all valid enum values."""
        return [e.value for e in cls]


class SpeedProfile(str, Enum):
    """
    速度曲线类型枚举
    Speed curve profile for camera motion.
    """
    EASE_IN = "ease_in"         # 渐入
    EASE_OUT = "ease_out"       # 渐出
    EASE_IN_OUT = "ease_in_out" # 渐入渐出
    LINEAR = "linear"           # 线性
    
    @classmethod
    def values(cls) -> list[str]:
        """Return all valid enum values."""
        return [e.value for e in cls]


class SuggestedScale(str, Enum):
    """
    景别建议枚举
    Suggested framing scale for shots.
    """
    EXTREME_CLOSEUP = "extreme_closeup"  # 特写
    CLOSEUP = "closeup"                  # 近景
    MEDIUM = "medium"                    # 中景
    WIDE = "wide"                        # 远景/全景
    
    @classmethod
    def values(cls) -> list[str]:
        """Return all valid enum values."""
        return [e.value for e in cls]


class TaskStatus(str, Enum):
    """
    任务状态枚举
    Analysis task status.
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    
    @classmethod
    def values(cls) -> list[str]:
        """Return all valid enum values."""
        return [e.value for e in cls]


class FeedbackAction(str, Enum):
    """
    用户反馈动作枚举
    User feedback action types.
    """
    ACCEPT = "accept"
    MODIFY = "modify"
    IGNORE = "ignore"
    
    @classmethod
    def values(cls) -> list[str]:
        """Return all valid enum values."""
        return [e.value for e in cls]
