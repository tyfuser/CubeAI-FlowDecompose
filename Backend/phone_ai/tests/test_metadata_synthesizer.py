"""
Tests for the Metadata Synthesizer Agent.
"""
import json
import pytest

from src.models.data_types import (
    BBox,
    ExifData,
    HeuristicOutput,
    MetadataOutput,
)
from src.models.enums import MotionType, SpeedProfile, SuggestedScale
from src.schemas.validator import (
    SchemaValidator,
    validate_metadata_output,
    load_metadata_schema,
)
from src.agents.motion_rules import (
    MotionTypeInferrer,
    infer_motion_type_from_heuristics,
)
from src.agents.prompt_templates import (
    build_few_shot_prompt,
    build_simple_prompt,
    parse_llm_response,
)
from src.agents.metadata_synthesizer import (
    MetadataSynthesizerAgent,
    MetadataSynthesizerConfig,
)


@pytest.fixture
def sample_heuristic():
    return HeuristicOutput(
        video_id="test_video_001",
        time_range=(0.0, 10.0),
        avg_motion_px_per_s=50.0,
        frame_pct_change=0.15,
        motion_smoothness=0.75,
        subject_occupancy=0.35,
        beat_alignment_score=0.6,
    )


@pytest.fixture
def sample_exif():
    return ExifData(
        focal_length_mm=50.0,
        aperture=2.8,
        sensor_size="full_frame",
        iso=400,
    )


@pytest.fixture
def static_heuristic():
    return HeuristicOutput(
        video_id="test_static",
        time_range=(0.0, 5.0),
        avg_motion_px_per_s=2.0,
        frame_pct_change=0.01,
        motion_smoothness=0.95,
        subject_occupancy=0.4,
        beat_alignment_score=0.5,
    )


@pytest.fixture
def handheld_heuristic():
    return HeuristicOutput(
        video_id="test_handheld",
        time_range=(0.0, 8.0),
        avg_motion_px_per_s=150.0,
        frame_pct_change=0.08,
        motion_smoothness=0.35,
        subject_occupancy=0.25,
        beat_alignment_score=0.4,
    )


@pytest.fixture
def validator():
    return SchemaValidator()


@pytest.fixture
def synthesizer():
    config = MetadataSynthesizerConfig(
        use_llm=False,
        validate_output=True,
        auto_fix_invalid=True,
    )
    return MetadataSynthesizerAgent(config=config)


class TestSchemaValidation:
    def test_load_metadata_schema(self):
        schema = load_metadata_schema()
        assert schema is not None
        assert schema["title"] == "MetadataOutput"

    def test_valid_metadata_passes(self, validator):
        valid = {
            "time_range": [0.0, 10.0],
            "motion": {
                "type": "dolly_in",
                "params": {
                    "duration_s": 10.0,
                    "frame_pct_change": 0.15,
                    "speed_profile": "ease_in_out",
                    "motion_smoothness": 0.75,
                }
            },
            "framing": {
                "subject_bbox": [0.2, 0.2, 0.4, 0.4],
                "subject_occupancy": 0.35,
                "suggested_scale": "medium",
            },
            "beat_alignment_score": 0.6,
            "confidence": 0.85,
            "explainability": "Test explanation in Chinese.",
        }
        is_valid, errors = validator.validate_metadata(valid)
        assert is_valid, f"Errors: {errors}"


class TestMotionTypeInference:
    def test_static_shot(self, static_heuristic):
        motion_type, _, _, _ = infer_motion_type_from_heuristics(static_heuristic)
        assert motion_type == MotionType.STATIC

    def test_handheld_shot(self, handheld_heuristic):
        motion_type, _, _, _ = infer_motion_type_from_heuristics(handheld_heuristic)
        assert motion_type == MotionType.HANDHELD

    def test_suggested_scale(self):
        inferrer = MotionTypeInferrer()
        assert inferrer.infer_suggested_scale(0.6) == SuggestedScale.EXTREME_CLOSEUP
        assert inferrer.infer_suggested_scale(0.3) == SuggestedScale.CLOSEUP
        assert inferrer.infer_suggested_scale(0.15) == SuggestedScale.MEDIUM
        assert inferrer.infer_suggested_scale(0.05) == SuggestedScale.WIDE


class TestPromptTemplates:
    def test_few_shot_prompt(self, sample_heuristic, sample_exif):
        prompt = build_few_shot_prompt(sample_heuristic, sample_exif, num_examples=3)
        assert "avg_motion_px_per_s" in prompt

    def test_parse_json_response(self):
        response = '{"motion": {"type": "static"}, "confidence": 0.9}'
        result = parse_llm_response(response)
        assert result["motion"]["type"] == "static"


class TestMetadataGenerationPipeline:
    @pytest.mark.asyncio
    async def test_generates_valid_metadata(self, synthesizer, sample_heuristic):
        metadata = await synthesizer.process(sample_heuristic)
        assert metadata is not None
        assert isinstance(metadata, MetadataOutput)

    @pytest.mark.asyncio
    async def test_generates_confidence(self, synthesizer, sample_heuristic):
        metadata = await synthesizer.process(sample_heuristic)
        assert 0.0 <= metadata.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_generates_explainability(self, synthesizer, sample_heuristic):
        metadata = await synthesizer.process(sample_heuristic)
        assert metadata.explainability is not None
        assert len(metadata.explainability) > 0

    @pytest.mark.asyncio
    async def test_output_passes_validation(self, synthesizer, sample_heuristic, validator):
        metadata = await synthesizer.process(sample_heuristic)
        is_valid, errors = validator.validate_metadata(metadata.to_dict())
        assert is_valid, f"Errors: {errors}"

    @pytest.mark.asyncio
    async def test_static_shot_metadata(self, synthesizer, static_heuristic):
        metadata = await synthesizer.process(static_heuristic)
        assert metadata.motion_type == MotionType.STATIC

    @pytest.mark.asyncio
    async def test_handheld_shot_metadata(self, synthesizer, handheld_heuristic):
        metadata = await synthesizer.process(handheld_heuristic)
        assert metadata.motion_type == MotionType.HANDHELD

    def test_sync_pipeline(self, synthesizer, sample_heuristic):
        metadata = synthesizer.generate_metadata_sync(sample_heuristic)
        assert metadata is not None
        assert 0.0 <= metadata.confidence <= 1.0


class TestConfidenceScore:
    @pytest.mark.asyncio
    async def test_smoothness_affects_confidence(self, synthesizer):
        high = HeuristicOutput(
            video_id="test", time_range=(0.0, 5.0),
            avg_motion_px_per_s=2.0, frame_pct_change=0.01,
            motion_smoothness=0.9, subject_occupancy=0.4,
            beat_alignment_score=0.5,
        )
        low = HeuristicOutput(
            video_id="test", time_range=(0.0, 5.0),
            avg_motion_px_per_s=2.0, frame_pct_change=0.01,
            motion_smoothness=0.3, subject_occupancy=0.4,
            beat_alignment_score=0.5,
        )
        high_meta = await synthesizer.process(high)
        low_meta = await synthesizer.process(low)
        assert high_meta.confidence > low_meta.confidence


class TestExplainability:
    @pytest.mark.asyncio
    async def test_contains_motion_description(self, synthesizer, sample_heuristic):
        metadata = await synthesizer.process(sample_heuristic)
        keywords = ["镜头", "运动", "推", "拉", "摇", "静态", "手持"]
        assert any(kw in metadata.explainability for kw in keywords)

    @pytest.mark.asyncio
    async def test_max_length(self, synthesizer, sample_heuristic):
        metadata = await synthesizer.process(sample_heuristic)
        assert len(metadata.explainability) <= 500
