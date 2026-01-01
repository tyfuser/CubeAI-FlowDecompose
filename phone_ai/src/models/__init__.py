# Models module
"""
Data models, enums, and database schemas for the Video Shooting Assistant.
"""

from .enums import (
    MotionType,
    SpeedProfile,
    SuggestedScale,
    TaskStatus,
    FeedbackAction,
)

from .data_types import (
    BBox,
    ExifData,
    UploaderOutput,
    OpticalFlowData,
    SubjectTrackingData,
    FeatureOutput,
    HeuristicOutput,
    MotionParams,
    FramingData,
    MetadataOutput,
    AdvancedParams,
    InstructionCard,
    RetrievalResult,
    RetrievalOutput,
    PipelineResult,
)

from .database import (
    Base,
    AnalysisTask,
    UserFeedback,
    ReferenceVideo,
    get_engine,
    get_session_factory,
    init_db,
)

__all__ = [
    # Enums
    "MotionType",
    "SpeedProfile",
    "SuggestedScale",
    "TaskStatus",
    "FeedbackAction",
    # Data types
    "BBox",
    "ExifData",
    "UploaderOutput",
    "OpticalFlowData",
    "SubjectTrackingData",
    "FeatureOutput",
    "HeuristicOutput",
    "MotionParams",
    "FramingData",
    "MetadataOutput",
    "AdvancedParams",
    "InstructionCard",
    "RetrievalResult",
    "RetrievalOutput",
    "PipelineResult",
    # Database
    "Base",
    "AnalysisTask",
    "UserFeedback",
    "ReferenceVideo",
    "get_engine",
    "get_session_factory",
    "init_db",
]
