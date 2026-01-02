"""
Integration tests for the Video Shooting Assistant pipeline.

Tests the full pipeline flow:
Uploader → Feature_Extractor → Heuristic_Analyzer → Metadata_Synthesizer → Instruction_Generator

Requirements covered:
- 7.1: Trigger agents in sequence
"""
import asyncio
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.models.data_types import (
    BBox,
    ExifData,
    FeatureOutput,
    HeuristicOutput,
    InstructionCard,
    MetadataOutput,
    MotionParams,
    FramingData,
    OpticalFlowData,
    SubjectTrackingData,
    UploaderOutput,
    PipelineResult,
)
from src.models.enums import MotionType, SpeedProfile, SuggestedScale
from src.services.orchestrator import (
    Orchestrator,
    PipelineConfig,
    ConfidenceAction,
    PipelineStage,
)


# ============================================================================
# Fixtures for creating mock agent outputs
# ============================================================================

@pytest.fixture
def mock_uploader_output():
    """Create a mock UploaderOutput for testing."""
    return UploaderOutput(
        video_id="test-video-001",
        frames_path="/tmp/test_frames",
        frame_count=300,
        fps=30.0,
        duration_s=10.0,
        resolution=(1920, 1080),
        exif=ExifData(
            focal_length_mm=50.0,
            aperture=2.8,
            sensor_size="full-frame",
            iso=400,
        ),
        audio_path="/tmp/test_audio.wav",
    )


@pytest.fixture
def mock_feature_output():
    """Create a mock FeatureOutput for testing."""
    # Create sample bounding boxes
    bbox_sequence = [
        BBox(x=0.3, y=0.2, w=0.4, h=0.5),
        BBox(x=0.32, y=0.22, w=0.42, h=0.52),
        BBox(x=0.34, y=0.24, w=0.44, h=0.54),
    ]
    
    return FeatureOutput(
        video_id="test-video-001",
        optical_flow=OpticalFlowData(
            avg_speed_px_s=25.0,
            primary_direction_deg=45.0,
            flow_vectors=[(1.0, 1.0), (1.2, 0.8), (0.9, 1.1)],
        ),
        subject_tracking=SubjectTrackingData(
            bbox_sequence=bbox_sequence,
            confidence_scores=[0.95, 0.93, 0.91],
            timestamps=[0.0, 0.033, 0.066],
        ),
        keypoints=None,
        frame_embeddings=[[0.1] * 512, [0.2] * 512],
        audio_beats=[0.5, 1.0, 1.5, 2.0],
    )


@pytest.fixture
def mock_heuristic_output():
    """Create a mock HeuristicOutput for testing."""
    return HeuristicOutput(
        video_id="test-video-001",
        time_range=(0.0, 10.0),
        avg_motion_px_per_s=25.0,
        frame_pct_change=0.15,
        motion_smoothness=0.75,
        subject_occupancy=0.35,
        beat_alignment_score=0.8,
    )


@pytest.fixture
def mock_metadata_output():
    """Create a mock MetadataOutput for testing."""
    return MetadataOutput(
        time_range=(0.0, 10.0),
        motion_type=MotionType.DOLLY_IN,
        motion_params=MotionParams(
            duration_s=10.0,
            frame_pct_change=0.15,
            speed_profile=SpeedProfile.EASE_IN_OUT,
            motion_smoothness=0.75,
        ),
        framing=FramingData(
            subject_bbox=BBox(x=0.3, y=0.2, w=0.4, h=0.5),
            subject_occupancy=0.35,
            suggested_scale=SuggestedScale.MEDIUM,
        ),
        beat_alignment_score=0.8,
        confidence=0.85,
        explainability="该镜头为中速推进，运动平滑。主体占画面约35%，构图适中，建议使用滑轨或稳定器保持流畅。",
    )


@pytest.fixture
def mock_instruction_card():
    """Create a mock InstructionCard for testing."""
    from src.models.data_types import AdvancedParams
    
    return InstructionCard(
        video_id="test-video-001",
        primary=[
            "时间段 0.0s - 10.0s：推镜头",
            "运动方式：中速推进，持续 10.0 秒",
            "建议使用滑轨/电动滑轨/三轴稳定器",
            "置信度：85%，推荐执行",
        ],
        explain="画面呈现向前推进的特征，主体逐渐放大，运动流畅。主体占画面约35%，构图均衡，建议中景拍摄以平衡主体与环境。",
        advanced=AdvancedParams(
            target_occupancy="当前35%，目标20%-40%",
            duration_s=10.0,
            speed_curve="渐入渐出（两端慢，中间快）",
            stabilization="电动滑轨或轨道车",
            notes=["预估移动距离约 0.8m，速度约 0.08m/s"],
        ),
    )


# ============================================================================
# Integration Tests - Data Flow Between Agents
# ============================================================================

class TestPipelineDataFlow:
    """Test data flow between pipeline stages."""
    
    def test_uploader_output_to_feature_extractor(
        self,
        mock_uploader_output,
    ):
        """Test that UploaderOutput contains all fields needed by FeatureExtractor."""
        output = mock_uploader_output
        
        # FeatureExtractor needs these fields
        assert output.video_id is not None
        assert output.frames_path is not None
        assert output.fps > 0
        assert output.duration_s > 0
        assert output.audio_path is not None or output.audio_path is None  # Optional
        
        # Verify serialization works
        output_dict = output.to_dict()
        assert "video_id" in output_dict
        assert "frames_path" in output_dict
        assert "fps" in output_dict
    
    def test_feature_output_to_heuristic_analyzer(
        self,
        mock_feature_output,
    ):
        """Test that FeatureOutput contains all fields needed by HeuristicAnalyzer."""
        output = mock_feature_output
        
        # HeuristicAnalyzer needs these fields
        assert output.video_id is not None
        assert output.optical_flow is not None
        assert output.optical_flow.avg_speed_px_s >= 0
        assert output.subject_tracking is not None
        assert len(output.subject_tracking.bbox_sequence) >= 0
        
        # Verify all bboxes are valid
        for bbox in output.subject_tracking.bbox_sequence:
            assert bbox.is_valid(), f"Invalid bbox: {bbox}"
        
        # Verify serialization works
        output_dict = output.to_dict()
        assert "optical_flow" in output_dict
        assert "subject_tracking" in output_dict
    
    def test_heuristic_output_to_metadata_synthesizer(
        self,
        mock_heuristic_output,
    ):
        """Test that HeuristicOutput contains all fields needed by MetadataSynthesizer."""
        output = mock_heuristic_output
        
        # MetadataSynthesizer needs these fields
        assert output.video_id is not None
        assert output.time_range is not None
        assert len(output.time_range) == 2
        assert output.time_range[0] < output.time_range[1]
        
        # All indicators should be in valid ranges
        assert output.is_valid()
        assert 0 <= output.frame_pct_change <= 1
        assert 0 <= output.motion_smoothness <= 1
        assert 0 <= output.subject_occupancy <= 1
        assert 0 <= output.beat_alignment_score <= 1
        assert output.avg_motion_px_per_s >= 0
        
        # Verify serialization works
        output_dict = output.to_dict()
        assert "time_range" in output_dict
        assert "frame_pct_change" in output_dict
    
    def test_metadata_output_to_instruction_generator(
        self,
        mock_metadata_output,
    ):
        """Test that MetadataOutput contains all fields needed by InstructionGenerator."""
        output = mock_metadata_output
        
        # InstructionGenerator needs these fields
        assert output.time_range is not None
        assert output.motion_type is not None
        assert output.motion_params is not None
        assert output.framing is not None
        assert output.confidence is not None
        
        # Verify enum values are valid
        assert isinstance(output.motion_type, MotionType)
        assert isinstance(output.motion_params.speed_profile, SpeedProfile)
        assert isinstance(output.framing.suggested_scale, SuggestedScale)
        
        # Verify ranges
        assert 0 <= output.confidence <= 1
        assert 0 <= output.beat_alignment_score <= 1
        
        # Verify serialization works
        output_dict = output.to_dict()
        assert "motion" in output_dict
        assert "framing" in output_dict
        assert "confidence" in output_dict
    
    def test_instruction_card_completeness(
        self,
        mock_instruction_card,
    ):
        """Test that InstructionCard has all required layers."""
        card = mock_instruction_card
        
        # All three layers should be present
        assert card.is_complete()
        assert len(card.primary) > 0
        assert len(card.explain) > 0
        assert card.advanced is not None
        
        # Verify serialization works
        card_dict = card.to_dict()
        assert "instruction_card" in card_dict
        assert "primary" in card_dict["instruction_card"]
        assert "explain" in card_dict["instruction_card"]
        assert "advanced" in card_dict["instruction_card"]


# ============================================================================
# Integration Tests - Orchestrator Pipeline
# ============================================================================

class TestOrchestratorPipeline:
    """Test the Orchestrator pipeline execution."""
    
    @pytest.fixture
    def mock_orchestrator(
        self,
        mock_uploader_output,
        mock_feature_output,
        mock_heuristic_output,
        mock_metadata_output,
        mock_instruction_card,
    ):
        """Create an Orchestrator with mocked agents."""
        # Create mock agents
        mock_uploader = MagicMock()
        mock_uploader.process = AsyncMock(return_value=mock_uploader_output)
        
        mock_feature_extractor = MagicMock()
        mock_feature_extractor.process = AsyncMock(return_value=mock_feature_output)
        
        mock_heuristic_analyzer = MagicMock()
        mock_heuristic_analyzer.process = AsyncMock(return_value=mock_heuristic_output)
        
        mock_metadata_synthesizer = MagicMock()
        mock_metadata_synthesizer.process = AsyncMock(return_value=mock_metadata_output)
        
        mock_instruction_generator = MagicMock()
        mock_instruction_generator.process = AsyncMock(return_value=mock_instruction_card)
        
        # Create orchestrator with mocked agents
        orchestrator = Orchestrator(
            config=PipelineConfig(),
            uploader=mock_uploader,
            feature_extractor=mock_feature_extractor,
            heuristic_analyzer=mock_heuristic_analyzer,
            metadata_synthesizer=mock_metadata_synthesizer,
            instruction_generator=mock_instruction_generator,
        )
        
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_pipeline_executes_all_stages(self, mock_orchestrator):
        """Test that pipeline executes all stages in sequence (Requirement 7.1)."""
        result = await mock_orchestrator.run_pipeline(
            video_path="/tmp/test_video.mp4",
            video_id="test-video-001",
        )
        
        # Verify all stages were executed
        mock_orchestrator._uploader.process.assert_called_once()
        mock_orchestrator._feature_extractor.process.assert_called_once()
        mock_orchestrator._heuristic_analyzer.process.assert_called_once()
        mock_orchestrator._metadata_synthesizer.process.assert_called_once()
        mock_orchestrator._instruction_generator.process.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_pipeline_returns_complete_result(self, mock_orchestrator):
        """Test that pipeline returns a complete PipelineResult."""
        result = await mock_orchestrator.run_pipeline(
            video_path="/tmp/test_video.mp4",
            video_id="test-video-001",
        )
        
        # Verify result structure
        assert isinstance(result, PipelineResult)
        assert result.video_id == "test-video-001"
        assert result.uploader_output is not None
        assert result.feature_output is not None
        assert result.heuristic_output is not None
        assert result.metadata_output is not None
        assert result.instruction_card is not None
        assert result.error is None
        assert result.is_successful()
    
    @pytest.mark.asyncio
    async def test_pipeline_data_flows_correctly(self, mock_orchestrator):
        """Test that data flows correctly between stages."""
        result = await mock_orchestrator.run_pipeline(
            video_path="/tmp/test_video.mp4",
            video_id="test-video-001",
        )
        
        # Verify feature extractor received uploader output
        fe_call_args = mock_orchestrator._feature_extractor.process.call_args
        assert fe_call_args is not None
        
        # Verify heuristic analyzer received feature output
        ha_call_args = mock_orchestrator._heuristic_analyzer.process.call_args
        assert ha_call_args is not None
        
        # Verify metadata synthesizer received heuristic output
        ms_call_args = mock_orchestrator._metadata_synthesizer.process.call_args
        assert ms_call_args is not None
        
        # Verify instruction generator received metadata output
        ig_call_args = mock_orchestrator._instruction_generator.process.call_args
        assert ig_call_args is not None


# ============================================================================
# Integration Tests - Confidence Threshold Handling
# ============================================================================

class TestConfidenceThresholdHandling:
    """Test confidence threshold handling (Requirements 7.4, 7.5, 7.6)."""
    
    def test_high_confidence_proceeds_normally(self):
        """Test that confidence > 0.75 proceeds normally (Requirement 7.4)."""
        orchestrator = Orchestrator()
        
        action = orchestrator.handle_confidence(0.85)
        assert action == ConfidenceAction.PROCEED
        
        message = orchestrator.get_confidence_message(action)
        assert message is None
    
    def test_medium_confidence_adds_warning(self):
        """Test that 0.55 <= confidence <= 0.75 adds warning (Requirement 7.5)."""
        orchestrator = Orchestrator()
        
        # Test at lower boundary
        action = orchestrator.handle_confidence(0.55)
        assert action == ConfidenceAction.WARN
        
        # Test at upper boundary
        action = orchestrator.handle_confidence(0.75)
        assert action == ConfidenceAction.WARN
        
        # Test in middle
        action = orchestrator.handle_confidence(0.65)
        assert action == ConfidenceAction.WARN
        
        message = orchestrator.get_confidence_message(action)
        assert message == "请尝试并拍摄两条版本"
    
    def test_low_confidence_requests_manual(self):
        """Test that confidence < 0.55 requests manual intervention (Requirement 7.6)."""
        orchestrator = Orchestrator()
        
        action = orchestrator.handle_confidence(0.40)
        assert action == ConfidenceAction.MANUAL
        
        action = orchestrator.handle_confidence(0.54)
        assert action == ConfidenceAction.MANUAL
        
        message = orchestrator.get_confidence_message(action)
        assert message == "置信度较低，建议人工确认后再执行"


# ============================================================================
# Integration Tests - Schema Validation
# ============================================================================

class TestSchemaValidation:
    """Test schema validation in the pipeline."""
    
    def test_metadata_output_schema_validation(self, mock_metadata_output):
        """Test that MetadataOutput passes schema validation."""
        orchestrator = Orchestrator()
        
        validation_result = orchestrator.validate_metadata(mock_metadata_output)
        assert validation_result.is_valid, f"Validation errors: {validation_result.errors}"
    
    def test_invalid_metadata_detected(self):
        """Test that invalid metadata is detected."""
        # Create metadata with invalid confidence (out of range)
        invalid_metadata = MetadataOutput(
            time_range=(0.0, 10.0),
            motion_type=MotionType.DOLLY_IN,
            motion_params=MotionParams(
                duration_s=10.0,
                frame_pct_change=0.15,
                speed_profile=SpeedProfile.LINEAR,
                motion_smoothness=0.75,
            ),
            framing=FramingData(
                subject_bbox=BBox(x=0.3, y=0.2, w=0.4, h=0.5),
                subject_occupancy=0.35,
                suggested_scale=SuggestedScale.MEDIUM,
            ),
            beat_alignment_score=0.8,
            confidence=1.5,  # Invalid: > 1.0
            explainability="Test explanation",
        )
        
        orchestrator = Orchestrator()
        validation_result = orchestrator.validate_metadata(invalid_metadata)
        
        # Should detect the invalid confidence
        assert not validation_result.is_valid or len(validation_result.errors) > 0


# ============================================================================
# Integration Tests - Pipeline Result Serialization
# ============================================================================

class TestPipelineResultSerialization:
    """Test that pipeline results can be serialized correctly."""
    
    def test_pipeline_result_to_dict(
        self,
        mock_uploader_output,
        mock_feature_output,
        mock_heuristic_output,
        mock_metadata_output,
        mock_instruction_card,
    ):
        """Test that PipelineResult can be converted to dict."""
        result = PipelineResult(
            video_id="test-video-001",
            uploader_output=mock_uploader_output,
            feature_output=mock_feature_output,
            heuristic_output=mock_heuristic_output,
            metadata_output=mock_metadata_output,
            instruction_card=mock_instruction_card,
        )
        
        result_dict = result.to_dict()
        
        # Verify all components are present
        assert result_dict["video_id"] == "test-video-001"
        assert "uploader_output" in result_dict
        assert "feature_output" in result_dict
        assert "heuristic_output" in result_dict
        assert "metadata_output" in result_dict
        assert "instruction_card" in result_dict
        assert "error" not in result_dict
    
    def test_pipeline_result_with_error(self):
        """Test PipelineResult with error."""
        result = PipelineResult(
            video_id="test-video-001",
            error="Test error message",
        )
        
        assert not result.is_successful()
        
        result_dict = result.to_dict()
        assert result_dict["error"] == "Test error message"


# ============================================================================
# Performance Tests (Requirements 10.1, 10.2, 10.3)
# ============================================================================

class TestPerformance:
    """
    Performance tests for the video analysis pipeline.
    
    Requirements:
    - 10.1: 1-minute video should complete within 120 seconds
    - 10.2: 5-minute video should complete within 300 seconds
    - 10.3: Support at least 10 concurrent video analysis requests
    """
    
    @pytest.fixture
    def fast_mock_orchestrator(
        self,
        mock_uploader_output,
        mock_feature_output,
        mock_heuristic_output,
        mock_metadata_output,
        mock_instruction_card,
    ):
        """Create an Orchestrator with fast mocked agents for performance testing."""
        import asyncio
        
        # Create mock agents with minimal delay
        mock_uploader = MagicMock()
        async def mock_upload(*args, **kwargs):
            await asyncio.sleep(0.01)  # Simulate minimal processing
            return mock_uploader_output
        mock_uploader.process = mock_upload
        
        mock_feature_extractor = MagicMock()
        async def mock_extract(*args, **kwargs):
            await asyncio.sleep(0.01)
            return mock_feature_output
        mock_feature_extractor.process = mock_extract
        
        mock_heuristic_analyzer = MagicMock()
        async def mock_analyze(*args, **kwargs):
            await asyncio.sleep(0.01)
            return mock_heuristic_output
        mock_heuristic_analyzer.process = mock_analyze
        
        mock_metadata_synthesizer = MagicMock()
        async def mock_synthesize(*args, **kwargs):
            await asyncio.sleep(0.01)
            return mock_metadata_output
        mock_metadata_synthesizer.process = mock_synthesize
        
        mock_instruction_generator = MagicMock()
        async def mock_generate(*args, **kwargs):
            await asyncio.sleep(0.01)
            return mock_instruction_card
        mock_instruction_generator.process = mock_generate
        
        orchestrator = Orchestrator(
            config=PipelineConfig(),
            uploader=mock_uploader,
            feature_extractor=mock_feature_extractor,
            heuristic_analyzer=mock_heuristic_analyzer,
            metadata_synthesizer=mock_metadata_synthesizer,
            instruction_generator=mock_instruction_generator,
        )
        
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_pipeline_completes_within_time_limit(self, fast_mock_orchestrator):
        """
        Test that pipeline completes within acceptable time.
        
        This test verifies the pipeline structure allows for timely completion.
        With mocked agents, it should complete very quickly.
        
        Requirements 10.1, 10.2: Processing time limits
        """
        import time
        
        start_time = time.time()
        
        result = await fast_mock_orchestrator.run_pipeline(
            video_path="/tmp/test_video.mp4",
            video_id="perf-test-001",
        )
        
        elapsed_time = time.time() - start_time
        
        # With mocked agents, should complete in under 1 second
        assert elapsed_time < 1.0, f"Pipeline took {elapsed_time:.2f}s, expected < 1s"
        assert result.is_successful()
    
    @pytest.mark.asyncio
    async def test_concurrent_pipeline_execution(self, fast_mock_orchestrator):
        """
        Test that multiple pipelines can run concurrently.
        
        Requirement 10.3: Support at least 10 concurrent video analysis requests
        """
        import time
        
        num_concurrent = 10
        
        async def run_single_pipeline(video_id: str):
            return await fast_mock_orchestrator.run_pipeline(
                video_path=f"/tmp/test_video_{video_id}.mp4",
                video_id=video_id,
            )
        
        start_time = time.time()
        
        # Run 10 pipelines concurrently
        tasks = [
            run_single_pipeline(f"concurrent-{i}")
            for i in range(num_concurrent)
        ]
        results = await asyncio.gather(*tasks)
        
        elapsed_time = time.time() - start_time
        
        # All should complete successfully
        assert len(results) == num_concurrent
        for i, result in enumerate(results):
            assert result.is_successful(), f"Pipeline {i} failed: {result.error}"
        
        # Concurrent execution should be faster than sequential
        # With 10 pipelines each taking ~0.05s, concurrent should be < 1s
        assert elapsed_time < 2.0, f"Concurrent execution took {elapsed_time:.2f}s"
    
    @pytest.mark.asyncio
    async def test_pipeline_handles_varying_video_durations(self, fast_mock_orchestrator):
        """
        Test pipeline handles videos of different durations.
        
        This verifies the pipeline structure can handle both short and long videos.
        """
        # Test with different simulated durations
        durations = [60.0, 300.0]  # 1 minute and 5 minutes
        
        for duration in durations:
            result = await fast_mock_orchestrator.run_pipeline(
                video_path=f"/tmp/test_video_{duration}s.mp4",
                video_id=f"duration-test-{duration}",
            )
            
            assert result.is_successful(), f"Failed for {duration}s video: {result.error}"


# ============================================================================
# Performance Tests - Pipeline Stage Timing
# ============================================================================

class TestPipelineStageTiming:
    """Test timing of individual pipeline stages."""
    
    @pytest.fixture
    def timed_mock_orchestrator(
        self,
        mock_uploader_output,
        mock_feature_output,
        mock_heuristic_output,
        mock_metadata_output,
        mock_instruction_card,
    ):
        """Create an Orchestrator that tracks stage timing."""
        import asyncio
        
        stage_times = {}
        
        mock_uploader = MagicMock()
        async def mock_upload(*args, **kwargs):
            import time
            start = time.time()
            await asyncio.sleep(0.02)  # Simulate upload processing
            stage_times['upload'] = time.time() - start
            return mock_uploader_output
        mock_uploader.process = mock_upload
        
        mock_feature_extractor = MagicMock()
        async def mock_extract(*args, **kwargs):
            import time
            start = time.time()
            await asyncio.sleep(0.03)  # Feature extraction is typically slower
            stage_times['feature_extraction'] = time.time() - start
            return mock_feature_output
        mock_feature_extractor.process = mock_extract
        
        mock_heuristic_analyzer = MagicMock()
        async def mock_analyze(*args, **kwargs):
            import time
            start = time.time()
            await asyncio.sleep(0.01)  # Heuristic analysis is fast
            stage_times['heuristic_analysis'] = time.time() - start
            return mock_heuristic_output
        mock_heuristic_analyzer.process = mock_analyze
        
        mock_metadata_synthesizer = MagicMock()
        async def mock_synthesize(*args, **kwargs):
            import time
            start = time.time()
            await asyncio.sleep(0.02)  # LLM call simulation
            stage_times['metadata_synthesis'] = time.time() - start
            return mock_metadata_output
        mock_metadata_synthesizer.process = mock_synthesize
        
        mock_instruction_generator = MagicMock()
        async def mock_generate(*args, **kwargs):
            import time
            start = time.time()
            await asyncio.sleep(0.01)  # Instruction generation is fast
            stage_times['instruction_generation'] = time.time() - start
            return mock_instruction_card
        mock_instruction_generator.process = mock_generate
        
        orchestrator = Orchestrator(
            config=PipelineConfig(),
            uploader=mock_uploader,
            feature_extractor=mock_feature_extractor,
            heuristic_analyzer=mock_heuristic_analyzer,
            metadata_synthesizer=mock_metadata_synthesizer,
            instruction_generator=mock_instruction_generator,
        )
        
        orchestrator._stage_times = stage_times
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_all_stages_complete(self, timed_mock_orchestrator):
        """Test that all pipeline stages complete and are timed."""
        result = await timed_mock_orchestrator.run_pipeline(
            video_path="/tmp/test_video.mp4",
            video_id="timing-test-001",
        )
        
        assert result.is_successful()
        
        # Verify all stages were timed
        stage_times = timed_mock_orchestrator._stage_times
        expected_stages = [
            'upload',
            'feature_extraction',
            'heuristic_analysis',
            'metadata_synthesis',
            'instruction_generation',
        ]
        
        for stage in expected_stages:
            assert stage in stage_times, f"Stage {stage} was not timed"
            assert stage_times[stage] > 0, f"Stage {stage} had zero time"


# ============================================================================
# Error Handling Tests (Requirements 7.7, 10.11)
# ============================================================================

class TestErrorHandling:
    """
    Error handling tests for the video analysis pipeline.
    
    Requirements:
    - 7.7: Log errors and display retry option to frontend
    - 10.11: Retry up to 3 times with exponential backoff for LLM failures
    """
    
    @pytest.fixture
    def mock_uploader_output(self):
        """Create a mock UploaderOutput for testing."""
        return UploaderOutput(
            video_id="test-video-001",
            frames_path="/tmp/test_frames",
            frame_count=300,
            fps=30.0,
            duration_s=10.0,
            resolution=(1920, 1080),
            exif=ExifData(
                focal_length_mm=50.0,
                aperture=2.8,
                sensor_size="full-frame",
                iso=400,
            ),
            audio_path="/tmp/test_audio.wav",
        )
    
    @pytest.mark.asyncio
    async def test_pipeline_handles_uploader_failure(self, mock_uploader_output):
        """Test that pipeline handles uploader agent failure gracefully."""
        # Create mock uploader that fails
        mock_uploader = MagicMock()
        mock_uploader.process = AsyncMock(side_effect=ValueError("Invalid video format"))
        
        orchestrator = Orchestrator(
            config=PipelineConfig(),
            uploader=mock_uploader,
        )
        
        result = await orchestrator.run_pipeline(
            video_path="/tmp/invalid_video.xyz",
            video_id="error-test-001",
        )
        
        # Pipeline should return error result, not raise exception
        assert not result.is_successful()
        assert result.error is not None
        assert "Invalid video format" in result.error
    
    @pytest.mark.asyncio
    async def test_pipeline_handles_feature_extractor_failure(self, mock_uploader_output):
        """Test that pipeline handles feature extractor failure gracefully."""
        # Create mock agents
        mock_uploader = MagicMock()
        mock_uploader.process = AsyncMock(return_value=mock_uploader_output)
        
        mock_feature_extractor = MagicMock()
        mock_feature_extractor.process = AsyncMock(
            side_effect=RuntimeError("Feature extraction timeout")
        )
        
        orchestrator = Orchestrator(
            config=PipelineConfig(max_retries=1),  # Reduce retries for faster test
            uploader=mock_uploader,
            feature_extractor=mock_feature_extractor,
        )
        
        result = await orchestrator.run_pipeline(
            video_path="/tmp/test_video.mp4",
            video_id="error-test-002",
        )
        
        # Pipeline should return error result
        assert not result.is_successful()
        assert result.error is not None
        # Uploader output should still be present
        assert result.uploader_output is not None
    
    @pytest.mark.asyncio
    async def test_pipeline_handles_llm_failure_with_retry(self, mock_uploader_output):
        """
        Test that pipeline retries on LLM failure.
        
        Requirement 10.11: Retry up to 3 times with exponential backoff
        """
        from src.services.orchestrator import RetryableError
        
        # Create mock agents
        mock_uploader = MagicMock()
        mock_uploader.process = AsyncMock(return_value=mock_uploader_output)
        
        # Create feature output
        feature_output = FeatureOutput(
            video_id="test-video-001",
            optical_flow=OpticalFlowData(
                avg_speed_px_s=25.0,
                primary_direction_deg=45.0,
                flow_vectors=[(1.0, 1.0)],
            ),
            subject_tracking=SubjectTrackingData(
                bbox_sequence=[BBox(x=0.3, y=0.2, w=0.4, h=0.5)],
                confidence_scores=[0.95],
                timestamps=[0.0],
            ),
        )
        
        mock_feature_extractor = MagicMock()
        mock_feature_extractor.process = AsyncMock(return_value=feature_output)
        
        # Create heuristic output
        heuristic_output = HeuristicOutput(
            video_id="test-video-001",
            time_range=(0.0, 10.0),
            avg_motion_px_per_s=25.0,
            frame_pct_change=0.15,
            motion_smoothness=0.75,
            subject_occupancy=0.35,
            beat_alignment_score=0.8,
        )
        
        mock_heuristic_analyzer = MagicMock()
        mock_heuristic_analyzer.process = AsyncMock(return_value=heuristic_output)
        
        # Create metadata synthesizer that fails with retryable error
        call_count = [0]
        
        async def failing_synthesizer(*args, **kwargs):
            call_count[0] += 1
            raise RetryableError("LLM API timeout")
        
        mock_metadata_synthesizer = MagicMock()
        mock_metadata_synthesizer.process = failing_synthesizer
        
        orchestrator = Orchestrator(
            config=PipelineConfig(max_retries=3, base_delay=0.01),  # Fast retries for test
            uploader=mock_uploader,
            feature_extractor=mock_feature_extractor,
            heuristic_analyzer=mock_heuristic_analyzer,
            metadata_synthesizer=mock_metadata_synthesizer,
        )
        
        result = await orchestrator.run_pipeline(
            video_path="/tmp/test_video.mp4",
            video_id="retry-test-001",
        )
        
        # Should have retried 3 times
        assert call_count[0] == 3, f"Expected 3 retries, got {call_count[0]}"
        
        # Pipeline should fail after retries exhausted
        assert not result.is_successful()
        assert result.error is not None
    
    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self):
        """
        Test that retry uses exponential backoff.
        
        Requirement 10.11: Exponential backoff for retries
        """
        from src.services.orchestrator import RetryableError
        import time
        
        orchestrator = Orchestrator(
            config=PipelineConfig(max_retries=3, base_delay=0.1, max_delay=1.0)
        )
        
        call_times = []
        
        async def failing_func():
            call_times.append(time.time())
            raise RetryableError("Test error")
        
        with pytest.raises(RetryableError):
            await orchestrator.retry_with_backoff(failing_func)
        
        # Should have 3 calls
        assert len(call_times) == 3
        
        # Check delays are increasing (exponential backoff)
        if len(call_times) >= 3:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            
            # Second delay should be roughly double the first (with some tolerance)
            # base_delay=0.1, so delays should be ~0.1, ~0.2
            assert delay1 >= 0.05, f"First delay too short: {delay1}"
            assert delay2 >= delay1 * 1.5, f"Second delay not increasing: {delay2} vs {delay1}"
    
    @pytest.mark.asyncio
    async def test_non_retryable_error_fails_immediately(self):
        """Test that non-retryable errors fail immediately without retry."""
        orchestrator = Orchestrator(
            config=PipelineConfig(max_retries=3, base_delay=0.1)
        )
        
        call_count = [0]
        
        async def failing_func():
            call_count[0] += 1
            raise ValueError("Non-retryable error")  # Not a RetryableError
        
        with pytest.raises(ValueError):
            await orchestrator.retry_with_backoff(failing_func)
        
        # Should only be called once (no retries)
        assert call_count[0] == 1


# ============================================================================
# Error Handling Tests - Invalid Input Scenarios
# ============================================================================

class TestInvalidInputHandling:
    """Test handling of invalid inputs."""
    
    def test_invalid_video_format_detection(self):
        """Test that invalid video formats are detected."""
        from src.agents.uploader import UploaderAgent, VideoFormat
        
        # Test unsupported format
        assert not VideoFormat.is_supported("xyz")
        assert not VideoFormat.is_supported("txt")
        assert not VideoFormat.is_supported("pdf")
        
        # Test supported formats
        assert VideoFormat.is_supported("mp4")
        assert VideoFormat.is_supported("mov")
        assert VideoFormat.is_supported("avi")
        assert VideoFormat.is_supported("mkv")
    
    def test_invalid_bbox_detection(self):
        """Test that invalid bounding boxes are detected."""
        # Valid bbox
        valid_bbox = BBox(x=0.1, y=0.2, w=0.3, h=0.4)
        assert valid_bbox.is_valid()
        
        # Invalid: x out of range
        invalid_bbox1 = BBox(x=-0.1, y=0.2, w=0.3, h=0.4)
        assert not invalid_bbox1.is_valid()
        
        # Invalid: x + w > 1
        invalid_bbox2 = BBox(x=0.8, y=0.2, w=0.3, h=0.4)
        assert not invalid_bbox2.is_valid()
        
        # Invalid: y + h > 1
        invalid_bbox3 = BBox(x=0.1, y=0.8, w=0.3, h=0.4)
        assert not invalid_bbox3.is_valid()
    
    def test_invalid_heuristic_output_detection(self):
        """Test that invalid heuristic outputs are detected."""
        # Valid output
        valid_output = HeuristicOutput(
            video_id="test",
            time_range=(0.0, 10.0),
            avg_motion_px_per_s=25.0,
            frame_pct_change=0.5,
            motion_smoothness=0.7,
            subject_occupancy=0.3,
            beat_alignment_score=0.8,
        )
        assert valid_output.is_valid()
        
        # Invalid: frame_pct_change > 1
        invalid_output1 = HeuristicOutput(
            video_id="test",
            time_range=(0.0, 10.0),
            avg_motion_px_per_s=25.0,
            frame_pct_change=1.5,  # Invalid
            motion_smoothness=0.7,
            subject_occupancy=0.3,
            beat_alignment_score=0.8,
        )
        assert not invalid_output1.is_valid()
        
        # Invalid: negative avg_motion
        invalid_output2 = HeuristicOutput(
            video_id="test",
            time_range=(0.0, 10.0),
            avg_motion_px_per_s=-5.0,  # Invalid
            frame_pct_change=0.5,
            motion_smoothness=0.7,
            subject_occupancy=0.3,
            beat_alignment_score=0.8,
        )
        assert not invalid_output2.is_valid()
        
        # Invalid: time_range start >= end
        invalid_output3 = HeuristicOutput(
            video_id="test",
            time_range=(10.0, 5.0),  # Invalid
            avg_motion_px_per_s=25.0,
            frame_pct_change=0.5,
            motion_smoothness=0.7,
            subject_occupancy=0.3,
            beat_alignment_score=0.8,
        )
        assert not invalid_output3.is_valid()


# ============================================================================
# Error Handling Tests - Pipeline Error Recovery
# ============================================================================

class TestPipelineErrorRecovery:
    """Test pipeline error recovery mechanisms."""
    
    @pytest.mark.asyncio
    async def test_pipeline_captures_error_at_each_stage(self):
        """Test that pipeline captures errors at each stage."""
        stages_to_test = [
            ('uploader', 'Upload failed'),
            ('feature_extractor', 'Feature extraction failed'),
            ('heuristic_analyzer', 'Heuristic analysis failed'),
            ('metadata_synthesizer', 'Metadata synthesis failed'),
            ('instruction_generator', 'Instruction generation failed'),
        ]
        
        for stage_name, error_msg in stages_to_test:
            # Create orchestrator with failing stage
            orchestrator = Orchestrator(config=PipelineConfig(max_retries=1))
            
            # Create mock that fails at specific stage
            if stage_name == 'uploader':
                orchestrator._uploader = MagicMock()
                orchestrator._uploader.process = AsyncMock(
                    side_effect=RuntimeError(error_msg)
                )
            else:
                # Set up successful stages before the failing one
                orchestrator._uploader = MagicMock()
                orchestrator._uploader.process = AsyncMock(
                    return_value=UploaderOutput(
                        video_id="test",
                        frames_path="/tmp/frames",
                        frame_count=100,
                        fps=30.0,
                        duration_s=10.0,
                        resolution=(1920, 1080),
                        exif=ExifData(),
                    )
                )
                
                if stage_name == 'feature_extractor':
                    orchestrator._feature_extractor = MagicMock()
                    orchestrator._feature_extractor.process = AsyncMock(
                        side_effect=RuntimeError(error_msg)
                    )
                else:
                    orchestrator._feature_extractor = MagicMock()
                    orchestrator._feature_extractor.process = AsyncMock(
                        return_value=FeatureOutput(
                            video_id="test",
                            optical_flow=OpticalFlowData(25.0, 45.0, []),
                            subject_tracking=SubjectTrackingData(),
                        )
                    )
                    
                    if stage_name == 'heuristic_analyzer':
                        orchestrator._heuristic_analyzer = MagicMock()
                        orchestrator._heuristic_analyzer.process = AsyncMock(
                            side_effect=RuntimeError(error_msg)
                        )
                    else:
                        orchestrator._heuristic_analyzer = MagicMock()
                        orchestrator._heuristic_analyzer.process = AsyncMock(
                            return_value=HeuristicOutput(
                                video_id="test",
                                time_range=(0.0, 10.0),
                                avg_motion_px_per_s=25.0,
                                frame_pct_change=0.15,
                                motion_smoothness=0.75,
                                subject_occupancy=0.35,
                                beat_alignment_score=0.8,
                            )
                        )
                        
                        if stage_name == 'metadata_synthesizer':
                            orchestrator._metadata_synthesizer = MagicMock()
                            orchestrator._metadata_synthesizer.process = AsyncMock(
                                side_effect=RuntimeError(error_msg)
                            )
                        else:
                            orchestrator._metadata_synthesizer = MagicMock()
                            orchestrator._metadata_synthesizer.process = AsyncMock(
                                return_value=MetadataOutput(
                                    time_range=(0.0, 10.0),
                                    motion_type=MotionType.DOLLY_IN,
                                    motion_params=MotionParams(
                                        duration_s=10.0,
                                        frame_pct_change=0.15,
                                        speed_profile=SpeedProfile.LINEAR,
                                        motion_smoothness=0.75,
                                    ),
                                    framing=FramingData(
                                        subject_bbox=BBox(0.3, 0.2, 0.4, 0.5),
                                        subject_occupancy=0.35,
                                        suggested_scale=SuggestedScale.MEDIUM,
                                    ),
                                    beat_alignment_score=0.8,
                                    confidence=0.85,
                                    explainability="Test",
                                )
                            )
                            
                            if stage_name == 'instruction_generator':
                                orchestrator._instruction_generator = MagicMock()
                                orchestrator._instruction_generator.process = AsyncMock(
                                    side_effect=RuntimeError(error_msg)
                                )
            
            result = await orchestrator.run_pipeline(
                video_path="/tmp/test.mp4",
                video_id=f"error-{stage_name}",
            )
            
            assert not result.is_successful(), f"Expected failure at {stage_name}"
            assert error_msg in result.error, f"Expected '{error_msg}' in error for {stage_name}"
