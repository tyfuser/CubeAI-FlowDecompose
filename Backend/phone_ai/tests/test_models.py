"""
Unit tests for core data models and enums.
"""
import pytest
from src.models.enums import MotionType, SpeedProfile, SuggestedScale
from src.models.data_types import (
    BBox,
    ExifData,
    HeuristicOutput,
    MotionParams,
    FramingData,
    MetadataOutput,
    AdvancedParams,
    InstructionCard,
)


class TestBBox:
    """Tests for BBox dataclass."""
    
    def test_valid_bbox(self):
        """Test valid bounding box."""
        bbox = BBox(x=0.1, y=0.2, w=0.3, h=0.4)
        assert bbox.is_valid()
    
    def test_invalid_bbox_negative_x(self):
        """Test invalid bounding box with negative x."""
        bbox = BBox(x=-0.1, y=0.2, w=0.3, h=0.4)
        assert not bbox.is_valid()
    
    def test_invalid_bbox_exceeds_right(self):
        """Test invalid bounding box that exceeds right edge."""
        bbox = BBox(x=0.8, y=0.2, w=0.3, h=0.4)
        assert not bbox.is_valid()
    
    def test_invalid_bbox_exceeds_bottom(self):
        """Test invalid bounding box that exceeds bottom edge."""
        bbox = BBox(x=0.1, y=0.8, w=0.3, h=0.4)
        assert not bbox.is_valid()
    
    def test_bbox_area(self):
        """Test bounding box area calculation."""
        bbox = BBox(x=0.0, y=0.0, w=0.5, h=0.5)
        assert bbox.area() == 0.25
    
    def test_bbox_normalize(self):
        """Test bounding box normalization."""
        bbox = BBox(x=-0.1, y=0.2, w=1.5, h=0.4)
        normalized = bbox.normalize()
        assert normalized.is_valid()
        assert normalized.x == 0.0
        assert normalized.w <= 1.0 - normalized.x
    
    def test_bbox_to_list(self):
        """Test conversion to list."""
        bbox = BBox(x=0.1, y=0.2, w=0.3, h=0.4)
        assert bbox.to_list() == [0.1, 0.2, 0.3, 0.4]
    
    def test_bbox_from_list(self):
        """Test creation from list."""
        bbox = BBox.from_list([0.1, 0.2, 0.3, 0.4])
        assert bbox.x == 0.1
        assert bbox.y == 0.2
        assert bbox.w == 0.3
        assert bbox.h == 0.4
    
    def test_bbox_from_list_invalid_length(self):
        """Test creation from invalid list."""
        with pytest.raises(ValueError):
            BBox.from_list([0.1, 0.2, 0.3])


class TestEnums:
    """Tests for enum types."""
    
    def test_motion_type_values(self):
        """Test MotionType enum values."""
        assert "dolly_in" in MotionType.values()
        assert "pan" in MotionType.values()
        assert "static" in MotionType.values()
        assert len(MotionType.values()) == 7
    
    def test_speed_profile_values(self):
        """Test SpeedProfile enum values."""
        assert "ease_in" in SpeedProfile.values()
        assert "linear" in SpeedProfile.values()
        assert len(SpeedProfile.values()) == 4
    
    def test_suggested_scale_values(self):
        """Test SuggestedScale enum values."""
        assert "extreme_closeup" in SuggestedScale.values()
        assert "wide" in SuggestedScale.values()
        assert len(SuggestedScale.values()) == 4


class TestHeuristicOutput:
    """Tests for HeuristicOutput dataclass."""
    
    def test_valid_heuristic_output(self):
        """Test valid heuristic output."""
        output = HeuristicOutput(
            video_id="test-001",
            time_range=(0.0, 10.0),
            avg_motion_px_per_s=50.0,
            frame_pct_change=0.15,
            motion_smoothness=0.75,
            subject_occupancy=0.35,
            beat_alignment_score=0.8,
        )
        assert output.is_valid()
    
    def test_invalid_frame_pct_change(self):
        """Test invalid frame_pct_change."""
        output = HeuristicOutput(
            video_id="test-001",
            time_range=(0.0, 10.0),
            avg_motion_px_per_s=50.0,
            frame_pct_change=1.5,  # Invalid: > 1
            motion_smoothness=0.75,
            subject_occupancy=0.35,
            beat_alignment_score=0.8,
        )
        assert not output.is_valid()
    
    def test_invalid_time_range(self):
        """Test invalid time range."""
        output = HeuristicOutput(
            video_id="test-001",
            time_range=(10.0, 5.0),  # Invalid: start > end
            avg_motion_px_per_s=50.0,
            frame_pct_change=0.15,
            motion_smoothness=0.75,
            subject_occupancy=0.35,
            beat_alignment_score=0.8,
        )
        assert not output.is_valid()


class TestInstructionCard:
    """Tests for InstructionCard dataclass."""
    
    def test_complete_instruction_card(self):
        """Test complete instruction card."""
        card = InstructionCard(
            video_id="test-001",
            primary=["缓慢推进，保持稳定", "使用滑轨或云台"],
            explain="根据分析，当前镜头运动较为平缓，建议使用稳定器材。",
            advanced=AdvancedParams(
                target_occupancy="35%",
                duration_s=5.0,
                speed_curve="ease_in_out",
                stabilization="gimbal",
                notes=["注意保持水平"],
            ),
        )
        assert card.is_complete()
    
    def test_incomplete_instruction_card_empty_primary(self):
        """Test incomplete instruction card with empty primary."""
        card = InstructionCard(
            video_id="test-001",
            primary=[],
            explain="Some explanation",
            advanced=AdvancedParams(
                target_occupancy="35%",
                duration_s=5.0,
                speed_curve="ease_in_out",
                stabilization="gimbal",
            ),
        )
        assert not card.is_complete()
