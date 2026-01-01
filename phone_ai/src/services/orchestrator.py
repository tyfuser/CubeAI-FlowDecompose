"""
Orchestrator Service for the Video Shooting Assistant.

Coordinates the execution of the video analysis pipeline:
Uploader → Feature_Extractor → Heuristic_Analyzer → Metadata_Synthesizer → Instruction_Generator

Requirements covered:
- 7.1: Trigger agents in sequence
- 7.4: confidence > 0.75 -> proceed normally
- 7.5: 0.55 <= confidence <= 0.75 -> add warning prompt
- 7.6: confidence < 0.55 -> pause and request manual annotation
"""
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, TYPE_CHECKING
from uuid import UUID

from src.models.data_types import (
    ExifData,
    FeatureOutput,
    HeuristicOutput,
    InstructionCard,
    MetadataOutput,
    PipelineResult,
    UploaderOutput,
)
from src.models.enums import TaskStatus
from src.schemas.validator import SchemaValidator, SchemaValidationError

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from src.agents.uploader import UploaderAgent, UploaderConfig
    from src.agents.feature_extractor import FeatureExtractorAgent, FeatureExtractorConfig
    from src.agents.heuristic_analyzer import HeuristicAnalyzerAgent, HeuristicAnalyzerConfig
    from src.agents.metadata_synthesizer import MetadataSynthesizerAgent, MetadataSynthesizerConfig
    from src.agents.instruction_generator import InstructionGeneratorAgent, InstructionGeneratorConfig


logger = logging.getLogger(__name__)


class ConfidenceAction(str, Enum):
    """Actions based on confidence threshold."""
    PROCEED = "proceed"  # confidence > 0.75
    WARN = "warn"  # 0.55 <= confidence <= 0.75
    MANUAL = "manual"  # confidence < 0.55


class PipelineStage(str, Enum):
    """Pipeline execution stages."""
    UPLOAD = "upload"
    FEATURE_EXTRACTION = "feature_extraction"
    HEURISTIC_ANALYSIS = "heuristic_analysis"
    METADATA_SYNTHESIS = "metadata_synthesis"
    INSTRUCTION_GENERATION = "instruction_generation"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineConfig:
    """Configuration for the pipeline execution."""
    # Uploader settings
    target_resolution: tuple[int, int] = (640, 360)
    max_file_size_mb: float = 2048.0
    
    # Feature extractor settings
    enable_keypoints: bool = False
    
    # Confidence thresholds (Requirements 7.4, 7.5, 7.6)
    high_confidence_threshold: float = 0.75
    medium_confidence_threshold: float = 0.55
    
    # Retry settings
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    
    # Validation settings
    validate_metadata: bool = True
    auto_complete_missing: bool = True


@dataclass
class ValidationResult:
    """Result of schema validation."""
    is_valid: bool
    errors: list[str]
    auto_fixed: bool = False


@dataclass
class PipelineProgress:
    """Progress tracking for pipeline execution."""
    task_id: str
    stage: PipelineStage
    progress_pct: float
    message: str
    started_at: datetime
    updated_at: datetime


class RetryableError(Exception):
    """Exception that can be retried."""
    pass


class Orchestrator:
    """
    工作流编排器
    
    Coordinates the execution of the video analysis pipeline,
    handling validation, error recovery, and confidence-based actions.
    """
    
    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        uploader: Optional[Any] = None,
        feature_extractor: Optional[Any] = None,
        heuristic_analyzer: Optional[Any] = None,
        metadata_synthesizer: Optional[Any] = None,
        instruction_generator: Optional[Any] = None,
    ):
        """
        Initialize the Orchestrator.
        
        Args:
            config: Pipeline configuration
            uploader: Optional pre-configured Uploader Agent
            feature_extractor: Optional pre-configured Feature Extractor Agent
            heuristic_analyzer: Optional pre-configured Heuristic Analyzer Agent
            metadata_synthesizer: Optional pre-configured Metadata Synthesizer Agent
            instruction_generator: Optional pre-configured Instruction Generator Agent
        """
        self.config = config or PipelineConfig()
        self.schema_validator = SchemaValidator()
        
        # Initialize agents
        self._uploader = uploader
        self._feature_extractor = feature_extractor
        self._heuristic_analyzer = heuristic_analyzer
        self._metadata_synthesizer = metadata_synthesizer
        self._instruction_generator = instruction_generator
        
        # Progress callback
        self._progress_callback: Optional[Callable[[PipelineProgress], None]] = None

    @property
    def uploader(self):
        """Lazy-load Uploader Agent."""
        if self._uploader is None:
            from src.agents.uploader import UploaderAgent, UploaderConfig
            uploader_config = UploaderConfig(
                target_resolution=self.config.target_resolution,
                max_file_size_mb=self.config.max_file_size_mb,
            )
            self._uploader = UploaderAgent(config=uploader_config)
        return self._uploader
    
    @property
    def feature_extractor(self):
        """Lazy-load Feature Extractor Agent."""
        if self._feature_extractor is None:
            from src.agents.feature_extractor import FeatureExtractorAgent, FeatureExtractorConfig
            fe_config = FeatureExtractorConfig(
                enable_keypoints=self.config.enable_keypoints,
            )
            self._feature_extractor = FeatureExtractorAgent(config=fe_config)
        return self._feature_extractor
    
    @property
    def heuristic_analyzer(self):
        """Lazy-load Heuristic Analyzer Agent."""
        if self._heuristic_analyzer is None:
            from src.agents.heuristic_analyzer import HeuristicAnalyzerAgent
            self._heuristic_analyzer = HeuristicAnalyzerAgent()
        return self._heuristic_analyzer
    
    @property
    def metadata_synthesizer(self):
        """Lazy-load Metadata Synthesizer Agent."""
        if self._metadata_synthesizer is None:
            from src.agents.metadata_synthesizer import MetadataSynthesizerAgent
            self._metadata_synthesizer = MetadataSynthesizerAgent()
        return self._metadata_synthesizer
    
    @property
    def instruction_generator(self):
        """Lazy-load Instruction Generator Agent."""
        if self._instruction_generator is None:
            from src.agents.instruction_generator import InstructionGeneratorAgent
            self._instruction_generator = InstructionGeneratorAgent()
        return self._instruction_generator
    
    def set_progress_callback(
        self,
        callback: Callable[[PipelineProgress], None]
    ) -> None:
        """Set callback for progress updates."""
        self._progress_callback = callback
    
    def _report_progress(
        self,
        task_id: str,
        stage: PipelineStage,
        progress_pct: float,
        message: str,
        started_at: datetime
    ) -> None:
        """Report progress to callback if set."""
        if self._progress_callback:
            progress = PipelineProgress(
                task_id=task_id,
                stage=stage,
                progress_pct=progress_pct,
                message=message,
                started_at=started_at,
                updated_at=datetime.utcnow(),
            )
            self._progress_callback(progress)
    
    # =========================================================================
    # Confidence Threshold Handling (Requirements 7.4, 7.5, 7.6)
    # =========================================================================
    
    def handle_confidence(self, confidence: float) -> ConfidenceAction:
        """
        Determine action based on confidence score.
        
        Requirements:
        - 7.4: confidence > 0.75 -> proceed normally
        - 7.5: 0.55 <= confidence <= 0.75 -> add warning prompt
        - 7.6: confidence < 0.55 -> pause and request manual annotation
        
        Args:
            confidence: Confidence score from metadata (0-1)
            
        Returns:
            ConfidenceAction indicating what action to take
        """
        if confidence > self.config.high_confidence_threshold:
            return ConfidenceAction.PROCEED
        elif confidence >= self.config.medium_confidence_threshold:
            return ConfidenceAction.WARN
        else:
            return ConfidenceAction.MANUAL
    
    def get_confidence_message(self, action: ConfidenceAction) -> Optional[str]:
        """
        Get user-facing message for confidence action.
        
        Args:
            action: The confidence action
            
        Returns:
            Message string or None for PROCEED action
        """
        if action == ConfidenceAction.PROCEED:
            return None
        elif action == ConfidenceAction.WARN:
            return "请尝试并拍摄两条版本"
        else:  # MANUAL
            return "置信度较低，建议人工确认后再执行"
    
    # =========================================================================
    # Schema Validation (Requirements 7.2, 7.3)
    # =========================================================================
    
    def validate_metadata(self, metadata: MetadataOutput) -> ValidationResult:
        """
        Validate metadata output against JSON Schema.
        
        Requirement 7.2: Validate metadata against predefined JSON Schema.
        
        Args:
            metadata: Metadata to validate
            
        Returns:
            ValidationResult with validation status and errors
        """
        metadata_dict = metadata.to_dict()
        is_valid, errors = self.schema_validator.validate_metadata(metadata_dict)
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            auto_fixed=False,
        )
    
    def auto_complete_metadata(
        self,
        metadata: MetadataOutput,
        heuristic_output: HeuristicOutput
    ) -> MetadataOutput:
        """
        Auto-complete missing or invalid fields in metadata.
        
        Requirement 7.3: Trigger auto-completion for missing fields.
        
        Args:
            metadata: Metadata with potential missing fields
            heuristic_output: Original heuristic output for fallback values
            
        Returns:
            Completed metadata
        """
        # The MetadataSynthesizerAgent already handles auto-fixing
        # This method provides an additional layer of completion if needed
        
        # Ensure confidence is in valid range
        confidence = max(0.0, min(1.0, metadata.confidence))
        
        # Ensure beat_alignment_score is in valid range
        beat_alignment = max(0.0, min(1.0, metadata.beat_alignment_score))
        
        # If values were adjusted, create new metadata
        if confidence != metadata.confidence or beat_alignment != metadata.beat_alignment_score:
            from src.models.data_types import MetadataOutput
            return MetadataOutput(
                time_range=metadata.time_range,
                motion_type=metadata.motion_type,
                motion_params=metadata.motion_params,
                framing=metadata.framing,
                beat_alignment_score=beat_alignment,
                confidence=confidence,
                explainability=metadata.explainability,
            )
        
        return metadata

    # =========================================================================
    # Retry Logic
    # =========================================================================
    
    async def retry_with_backoff(
        self,
        func: Callable,
        *args,
        max_retries: Optional[int] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with exponential backoff retry.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for func
            max_retries: Override default max retries
            **kwargs: Keyword arguments for func
            
        Returns:
            Result from func
            
        Raises:
            Exception: If all retries fail
        """
        retries = max_retries or self.config.max_retries
        last_error = None
        
        for attempt in range(retries):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except RetryableError as e:
                last_error = e
                delay = self._calculate_delay(attempt)
                logger.warning(
                    f"Retryable error, attempt {attempt + 1}/{retries}, "
                    f"retrying in {delay:.1f}s: {e}"
                )
                await asyncio.sleep(delay)
            except Exception as e:
                # Non-retryable error
                logger.error(f"Non-retryable error: {e}")
                raise
        
        raise last_error or Exception("All retries failed")
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        delay = self.config.base_delay * (2 ** attempt)
        return min(delay, self.config.max_delay)
    
    # =========================================================================
    # Pipeline Execution (Requirement 7.1)
    # =========================================================================
    
    async def run_pipeline(
        self,
        video_path: str,
        video_id: Optional[str] = None,
        config: Optional[PipelineConfig] = None
    ) -> PipelineResult:
        """
        Execute the complete video analysis pipeline.
        
        Requirement 7.1: Trigger agents in sequence:
        Uploader → Feature_Extractor → Heuristic_Analyzer → 
        Metadata_Synthesizer → Instruction_Generator
        
        Args:
            video_path: Path to the video file
            video_id: Optional video identifier
            config: Optional config override
            
        Returns:
            PipelineResult with all intermediate and final results
        """
        if config:
            self.config = config
        
        started_at = datetime.utcnow()
        task_id = video_id or str(datetime.utcnow().timestamp())
        
        result = PipelineResult(video_id=task_id)
        
        try:
            # Stage 1: Upload and preprocess
            self._report_progress(
                task_id, PipelineStage.UPLOAD, 0.0,
                "开始处理视频...", started_at
            )
            
            uploader_output = await self.retry_with_backoff(
                self.uploader.process,
                video_path,
                video_id=task_id,
            )
            result.uploader_output = uploader_output
            
            self._report_progress(
                task_id, PipelineStage.UPLOAD, 20.0,
                "视频预处理完成", started_at
            )
            
            # Stage 2: Feature extraction
            self._report_progress(
                task_id, PipelineStage.FEATURE_EXTRACTION, 20.0,
                "正在提取特征...", started_at
            )
            
            feature_output = await self.retry_with_backoff(
                self.feature_extractor.process,
                uploader_output,
            )
            result.feature_output = feature_output
            
            self._report_progress(
                task_id, PipelineStage.FEATURE_EXTRACTION, 50.0,
                "特征提取完成", started_at
            )
            
            # Stage 3: Heuristic analysis
            self._report_progress(
                task_id, PipelineStage.HEURISTIC_ANALYSIS, 50.0,
                "正在分析运动特征...", started_at
            )
            
            time_range = (0.0, uploader_output.duration_s)
            heuristic_output = await self.retry_with_backoff(
                self.heuristic_analyzer.process,
                feature_output,
                time_range,
            )
            result.heuristic_output = heuristic_output
            
            self._report_progress(
                task_id, PipelineStage.HEURISTIC_ANALYSIS, 70.0,
                "运动分析完成", started_at
            )
            
            # Stage 4: Metadata synthesis
            self._report_progress(
                task_id, PipelineStage.METADATA_SYNTHESIS, 70.0,
                "正在生成元数据...", started_at
            )
            
            primary_direction = feature_output.optical_flow.primary_direction_deg
            metadata_output = await self.retry_with_backoff(
                self.metadata_synthesizer.process,
                heuristic_output,
                uploader_output.exif,
                primary_direction,
            )
            
            # Validate metadata (Requirement 7.2)
            if self.config.validate_metadata:
                validation = self.validate_metadata(metadata_output)
                if not validation.is_valid:
                    logger.warning(f"Metadata validation errors: {validation.errors}")
                    if self.config.auto_complete_missing:
                        metadata_output = self.auto_complete_metadata(
                            metadata_output, heuristic_output
                        )
            
            result.metadata_output = metadata_output
            
            self._report_progress(
                task_id, PipelineStage.METADATA_SYNTHESIS, 85.0,
                "元数据生成完成", started_at
            )
            
            # Stage 5: Instruction generation
            self._report_progress(
                task_id, PipelineStage.INSTRUCTION_GENERATION, 85.0,
                "正在生成拍摄指令...", started_at
            )
            
            instruction_card = await self.retry_with_backoff(
                self.instruction_generator.process,
                metadata_output,
            )
            # Update video_id in instruction card
            instruction_card.video_id = task_id
            result.instruction_card = instruction_card
            
            # Handle confidence threshold
            confidence_action = self.handle_confidence(metadata_output.confidence)
            confidence_message = self.get_confidence_message(confidence_action)
            
            if confidence_message:
                logger.info(f"Confidence action: {confidence_action.value} - {confidence_message}")
            
            self._report_progress(
                task_id, PipelineStage.COMPLETED, 100.0,
                "分析完成", started_at
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            result.error = str(e)
            
            self._report_progress(
                task_id, PipelineStage.FAILED, 0.0,
                f"处理失败: {e}", started_at
            )
            
            return result

    def run_pipeline_sync(
        self,
        video_path: str,
        video_id: Optional[str] = None,
        config: Optional[PipelineConfig] = None
    ) -> PipelineResult:
        """
        Synchronous version of run_pipeline().
        
        Args:
            video_path: Path to the video file
            video_id: Optional video identifier
            config: Optional config override
            
        Returns:
            PipelineResult with all results
        """
        return asyncio.run(self.run_pipeline(video_path, video_id, config))
    
    async def run_stage(
        self,
        stage: PipelineStage,
        input_data: Any,
        **kwargs
    ) -> Any:
        """
        Run a single pipeline stage.
        
        Useful for re-running specific stages or testing.
        
        Args:
            stage: The stage to run
            input_data: Input data for the stage
            **kwargs: Additional arguments for the stage
            
        Returns:
            Output from the stage
        """
        if stage == PipelineStage.UPLOAD:
            return await self.uploader.process(input_data, **kwargs)
        elif stage == PipelineStage.FEATURE_EXTRACTION:
            return await self.feature_extractor.process(input_data, **kwargs)
        elif stage == PipelineStage.HEURISTIC_ANALYSIS:
            time_range = kwargs.get("time_range", (0.0, 10.0))
            return await self.heuristic_analyzer.process(input_data, time_range)
        elif stage == PipelineStage.METADATA_SYNTHESIS:
            exif_data = kwargs.get("exif_data")
            primary_direction = kwargs.get("primary_direction_deg")
            return await self.metadata_synthesizer.process(
                input_data, exif_data, primary_direction
            )
        elif stage == PipelineStage.INSTRUCTION_GENERATION:
            return await self.instruction_generator.process(input_data)
        else:
            raise ValueError(f"Unknown stage: {stage}")


def create_orchestrator(
    config: Optional[PipelineConfig] = None
) -> Orchestrator:
    """
    Factory function to create an Orchestrator instance.
    
    Args:
        config: Optional pipeline configuration
        
    Returns:
        Configured Orchestrator instance
    """
    return Orchestrator(config=config)
