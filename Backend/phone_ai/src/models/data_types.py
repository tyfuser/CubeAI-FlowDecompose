"""
Core data types and dataclasses for the Video Shooting Assistant.

Defines all input/output schemas for agents and data transfer objects.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional
import json

from .enums import MotionType, SpeedProfile, SuggestedScale


@dataclass
class BBox:
    """
    归一化边界框
    Normalized bounding box with coordinates in [0, 1] range.
    
    Attributes:
        x: Left edge x-coordinate (0-1)
        y: Top edge y-coordinate (0-1)
        w: Width (0-1)
        h: Height (0-1)
    """
    x: float
    y: float
    w: float
    h: float
    
    def area(self) -> float:
        """Calculate the area of the bounding box."""
        return self.w * self.h
    
    def is_valid(self) -> bool:
        """
        Check if the bounding box is valid.
        
        A valid bounding box has:
        - All coordinates in [0, 1] range
        - x + w <= 1 (doesn't exceed right edge)
        - y + h <= 1 (doesn't exceed bottom edge)
        """
        return (
            0 <= self.x <= 1 and
            0 <= self.y <= 1 and
            0 <= self.w <= 1 and
            0 <= self.h <= 1 and
            self.x + self.w <= 1 and
            self.y + self.h <= 1
        )
    
    def normalize(self) -> "BBox":
        """
        Return a normalized version of the bounding box.
        Clamps all values to valid ranges.
        """
        x = max(0.0, min(1.0, self.x))
        y = max(0.0, min(1.0, self.y))
        w = max(0.0, min(1.0 - x, self.w))
        h = max(0.0, min(1.0 - y, self.h))
        return BBox(x=x, y=y, w=w, h=h)
    
    def to_list(self) -> list[float]:
        """Convert to list format [x, y, w, h]."""
        return [self.x, self.y, self.w, self.h]
    
    @classmethod
    def from_list(cls, coords: list[float]) -> "BBox":
        """Create BBox from list [x, y, w, h]."""
        if len(coords) != 4:
            raise ValueError("BBox requires exactly 4 coordinates [x, y, w, h]")
        return cls(x=coords[0], y=coords[1], w=coords[2], h=coords[3])
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ExifData:
    """
    EXIF 元数据
    Camera EXIF metadata extracted from video.
    """
    focal_length_mm: Optional[float] = None
    aperture: Optional[float] = None
    sensor_size: Optional[str] = None
    iso: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class UploaderOutput:
    """
    Uploader Agent 输出
    Output schema for the Uploader Agent.
    """
    video_id: str
    frames_path: str
    frame_count: int
    fps: float
    duration_s: float
    resolution: tuple[int, int]
    exif: ExifData
    audio_path: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "video_id": self.video_id,
            "frames_path": self.frames_path,
            "frame_count": self.frame_count,
            "fps": self.fps,
            "duration_s": self.duration_s,
            "resolution": list(self.resolution),
            "exif": self.exif.to_dict(),
            "audio_path": self.audio_path,
        }


@dataclass
class OpticalFlowData:
    """
    光流数据
    Optical flow analysis results.
    """
    avg_speed_px_s: float
    primary_direction_deg: float
    flow_vectors: list[tuple[float, float]] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "avg_speed_px_s": self.avg_speed_px_s,
            "primary_direction_deg": self.primary_direction_deg,
            "flow_vectors": self.flow_vectors,
        }


@dataclass
class SubjectTrackingData:
    """
    主体跟踪数据
    Subject detection and tracking results.
    """
    bbox_sequence: list[BBox] = field(default_factory=list)
    confidence_scores: list[float] = field(default_factory=list)
    timestamps: list[float] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "bbox_sequence": [bbox.to_list() for bbox in self.bbox_sequence],
            "confidence_scores": self.confidence_scores,
            "timestamps": self.timestamps,
        }


@dataclass
class FeatureOutput:
    """
    Feature Extractor 输出
    Output schema for the Feature Extractor Agent.
    """
    video_id: str
    optical_flow: OpticalFlowData
    subject_tracking: SubjectTrackingData
    keypoints: Optional[list[dict]] = None
    frame_embeddings: Optional[list[list[float]]] = None
    audio_beats: Optional[list[float]] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "video_id": self.video_id,
            "optical_flow": self.optical_flow.to_dict(),
            "subject_tracking": self.subject_tracking.to_dict(),
            "keypoints": self.keypoints,
            "frame_embeddings": self.frame_embeddings,
            "audio_beats": self.audio_beats,
        }


@dataclass
class HeuristicOutput:
    """
    Heuristic Analyzer 输出
    Output schema for the Heuristic Analyzer Agent.
    """
    video_id: str
    time_range: tuple[float, float]
    avg_motion_px_per_s: float
    frame_pct_change: float
    motion_smoothness: float
    subject_occupancy: float
    beat_alignment_score: float
    
    def is_valid(self) -> bool:
        """Check if all indicators are in valid ranges."""
        return (
            self.avg_motion_px_per_s >= 0 and
            0 <= self.frame_pct_change <= 1 and
            0 <= self.motion_smoothness <= 1 and
            0 <= self.subject_occupancy <= 1 and
            0 <= self.beat_alignment_score <= 1 and
            self.time_range[0] >= 0 and
            self.time_range[0] < self.time_range[1]
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "video_id": self.video_id,
            "time_range": list(self.time_range),
            "avg_motion_px_per_s": self.avg_motion_px_per_s,
            "frame_pct_change": self.frame_pct_change,
            "motion_smoothness": self.motion_smoothness,
            "subject_occupancy": self.subject_occupancy,
            "beat_alignment_score": self.beat_alignment_score,
        }


@dataclass
class MotionParams:
    """
    运动参数
    Motion parameters for metadata output.
    """
    duration_s: float
    frame_pct_change: float
    speed_profile: SpeedProfile
    motion_smoothness: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "duration_s": self.duration_s,
            "frame_pct_change": self.frame_pct_change,
            "speed_profile": self.speed_profile.value,
            "motion_smoothness": self.motion_smoothness,
        }


@dataclass
class FramingData:
    """
    构图数据
    Framing and composition data.
    """
    subject_bbox: BBox
    subject_occupancy: float
    suggested_scale: SuggestedScale
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "subject_bbox": self.subject_bbox.to_list(),
            "subject_occupancy": self.subject_occupancy,
            "suggested_scale": self.suggested_scale.value,
        }


@dataclass
class MetadataOutput:
    """
    Metadata Synthesizer 输出
    Output schema for the Metadata Synthesizer Agent.
    """
    time_range: tuple[float, float]
    motion_type: MotionType
    motion_params: MotionParams
    framing: FramingData
    beat_alignment_score: float
    confidence: float
    explainability: str
    
    def is_valid(self) -> bool:
        """Check if metadata is valid."""
        return (
            self.time_range[0] >= 0 and
            self.time_range[0] < self.time_range[1] and
            0 <= self.confidence <= 1 and
            0 <= self.beat_alignment_score <= 1 and
            0 <= self.motion_params.frame_pct_change <= 1 and
            0 <= self.motion_params.motion_smoothness <= 1 and
            0 <= self.framing.subject_occupancy <= 1 and
            self.framing.subject_bbox.is_valid()
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "time_range": list(self.time_range),
            "motion": {
                "type": self.motion_type.value,
                "params": self.motion_params.to_dict(),
            },
            "framing": self.framing.to_dict(),
            "beat_alignment_score": self.beat_alignment_score,
            "confidence": self.confidence,
            "explainability": self.explainability,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class AdvancedParams:
    """
    高级参数
    Advanced parameters for instruction cards.
    """
    target_occupancy: str
    duration_s: float
    speed_curve: str
    stabilization: str
    notes: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "target_occupancy": self.target_occupancy,
            "duration_s": self.duration_s,
            "speed_curve": self.speed_curve,
            "stabilization": self.stabilization,
            "notes": self.notes,
        }


@dataclass
class InstructionCard:
    """
    拍摄指令卡
    Three-layer shooting instruction card.
    """
    video_id: str
    primary: list[str]  # Layer 1: 1-4 lines of actionable advice
    explain: str        # Layer 2: 1-3 sentences explaining rationale
    advanced: AdvancedParams  # Layer 3: Adjustable parameters
    
    def is_complete(self) -> bool:
        """Check if all three layers are present and non-empty."""
        return (
            len(self.primary) > 0 and
            len(self.explain) > 0 and
            self.advanced is not None
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "video_id": self.video_id,
            "instruction_card": {
                "primary": self.primary,
                "explain": self.explain,
                "advanced": self.advanced.to_dict(),
            }
        }


@dataclass
class RetrievalResult:
    """
    检索结果
    Single retrieval result from reference video search.
    """
    ref_video_id: str
    thumbnail_url: str
    similarity_score: float
    annotation: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "ref_video_id": self.ref_video_id,
            "thumbnail_url": self.thumbnail_url,
            "similarity_score": self.similarity_score,
            "annotation": self.annotation,
        }


@dataclass
class RetrievalOutput:
    """
    Retrieval Agent 输出
    Output schema for the Retrieval Agent.
    """
    query_video_id: str
    results: list[RetrievalResult] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "query_video_id": self.query_video_id,
            "results": [r.to_dict() for r in self.results],
        }


@dataclass
class PipelineResult:
    """
    完整流水线结果
    Complete pipeline execution result.
    """
    video_id: str
    uploader_output: Optional[UploaderOutput] = None
    feature_output: Optional[FeatureOutput] = None
    heuristic_output: Optional[HeuristicOutput] = None
    metadata_output: Optional[MetadataOutput] = None
    instruction_card: Optional[InstructionCard] = None
    retrieval_output: Optional[RetrievalOutput] = None
    error: Optional[str] = None
    
    def is_successful(self) -> bool:
        """Check if pipeline completed successfully."""
        return (
            self.error is None and
            self.instruction_card is not None
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {"video_id": self.video_id}
        
        if self.uploader_output:
            result["uploader_output"] = self.uploader_output.to_dict()
        if self.feature_output:
            result["feature_output"] = self.feature_output.to_dict()
        if self.heuristic_output:
            result["heuristic_output"] = self.heuristic_output.to_dict()
        if self.metadata_output:
            result["metadata_output"] = self.metadata_output.to_dict()
        if self.instruction_card:
            result["instruction_card"] = self.instruction_card.to_dict()
        if self.retrieval_output:
            result["retrieval_output"] = self.retrieval_output.to_dict()
        if self.error:
            result["error"] = self.error
            
        return result
