"""
Unit tests for the Instruction Generator Agent.
"""
import pytest
from src.models.data_types import (
    BBox,
    FramingData,
    MetadataOutput,
    MotionParams,
    AdvancedParams,
    InstructionCard,
)
from src.models.enums import MotionType, SpeedProfile, SuggestedScale
from src.agents.instruction_generator import (
    InstructionGeneratorAgent,
    InstructionGeneratorConfig,
)


class TestInstructionGeneratorAgent:
    """Tests for InstructionGeneratorAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create an InstructionGeneratorAgent instance."""
        return InstructionGeneratorAgent()
    
    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata output."""
        return MetadataOutput(
            time_range=(0.0, 5.0),
            motion_type=MotionType.DOLLY_IN,
            motion_params=MotionParams(
                duration_s=5.0,
                frame_pct_change=0.15,
                speed_profile=SpeedProfile.EASE_IN_OUT,
                motion_smoothness=0.75,
            ),
            framing=FramingData(
                subject_bbox=BBox(x=0.3, y=0.3, w=0.4, h=0.4),
                subject_occupancy=0.35,
                suggested_scale=SuggestedScale.MEDIUM,
            ),
            beat_alignment_score=0.6,
            confidence=0.8,
            explainability="测试说明文字。这是第二句。",
        )


class TestSpeedDescriptionMapping(TestInstructionGeneratorAgent):
    """Tests for speed description mapping (Requirements 5.5, 5.6, 5.7)."""
    
    def test_slow_speed_description(self, agent):
        """Test that frame_pct_change < 0.1 returns '缓慢' description."""
        # Requirement 5.5
        result = agent.map_speed_description(0.05, MotionType.DOLLY_IN)
        assert "缓慢" in result
    
    def test_medium_speed_description(self, agent):
        """Test that 0.1 <= frame_pct_change <= 0.25 returns '中速' description."""
        # Requirement 5.6
        result = agent.map_speed_description(0.15, MotionType.DOLLY_IN)
        assert "中速" in result
    
    def test_fast_speed_description(self, agent):
        """Test that frame_pct_change > 0.25 returns '快速' description."""
        # Requirement 5.7
        result = agent.map_speed_description(0.3, MotionType.DOLLY_IN)
        assert "快速" in result
    
    def test_boundary_slow_medium(self, agent):
        """Test boundary between slow and medium (0.1)."""
        # At exactly 0.1, should be medium
        result = agent.map_speed_description(0.1, MotionType.DOLLY_IN)
        assert "中速" in result
    
    def test_boundary_medium_fast(self, agent):
        """Test boundary between medium and fast (0.25)."""
        # At exactly 0.25, should still be medium
        result = agent.map_speed_description(0.25, MotionType.DOLLY_IN)
        assert "中速" in result
        
        # Just above 0.25, should be fast
        result = agent.map_speed_description(0.26, MotionType.DOLLY_IN)
        assert "快速" in result
    
    def test_static_motion_type(self, agent):
        """Test that static motion type returns '静止'."""
        result = agent.map_speed_description(0.15, MotionType.STATIC)
        assert result == "静止"
    
    def test_dolly_out_direction(self, agent):
        """Test that dolly_out uses '拉远' direction."""
        result = agent.map_speed_description(0.15, MotionType.DOLLY_OUT)
        assert "拉远" in result
    
    def test_pan_direction(self, agent):
        """Test that pan uses '横移' direction."""
        result = agent.map_speed_description(0.15, MotionType.PAN)
        assert "横移" in result


class TestEquipmentRecommendationMapping(TestInstructionGeneratorAgent):
    """Tests for equipment recommendation mapping (Requirements 5.8, 5.9, 5.10)."""
    
    def test_high_smoothness_equipment(self, agent):
        """Test that motion_smoothness > 0.7 recommends slider/dolly/gimbal."""
        # Requirement 5.8
        result = agent.map_equipment_suggestion(0.8)
        assert any(word in result for word in ["滑轨", "稳定器"])
    
    def test_medium_smoothness_equipment(self, agent):
        """Test that 0.4 <= motion_smoothness <= 0.7 recommends handheld with gimbal."""
        # Requirement 5.9
        result = agent.map_equipment_suggestion(0.5)
        assert any(word in result for word in ["手持", "云台", "稳定器"])
    
    def test_low_smoothness_equipment(self, agent):
        """Test that motion_smoothness < 0.4 recommends static or minimal."""
        # Requirement 5.10
        result = agent.map_equipment_suggestion(0.3)
        assert any(word in result for word in ["三脚架", "静态", "减少"])
    
    def test_boundary_high_medium(self, agent):
        """Test boundary between high and medium smoothness (0.7)."""
        # At exactly 0.7, should be medium
        result = agent.map_equipment_suggestion(0.7)
        assert any(word in result for word in ["手持", "云台"])
        
        # Just above 0.7, should be high
        result = agent.map_equipment_suggestion(0.71)
        assert any(word in result for word in ["滑轨", "稳定器"])
    
    def test_boundary_medium_low(self, agent):
        """Test boundary between medium and low smoothness (0.4)."""
        # At exactly 0.4, should be medium
        result = agent.map_equipment_suggestion(0.4)
        assert any(word in result for word in ["手持", "云台"])
        
        # Just below 0.4, should be low
        result = agent.map_equipment_suggestion(0.39)
        assert any(word in result for word in ["三脚架", "静态", "减少"])


class TestGeneratePrimary(TestInstructionGeneratorAgent):
    """Tests for Layer1 Primary generation (Requirements 5.1, 5.2)."""
    
    def test_returns_list_of_strings(self, agent, sample_metadata):
        """Test that generate_primary returns a list of strings."""
        result = agent.generate_primary(sample_metadata)
        assert isinstance(result, list)
        assert all(isinstance(item, str) for item in result)
    
    def test_returns_1_to_4_lines(self, agent, sample_metadata):
        """Test that generate_primary returns 1-4 lines."""
        result = agent.generate_primary(sample_metadata)
        assert 1 <= len(result) <= 4
    
    def test_includes_time_range(self, agent, sample_metadata):
        """Test that primary includes time range."""
        result = agent.generate_primary(sample_metadata)
        # Check that time range is mentioned
        combined = " ".join(result)
        assert "0.0" in combined or "0" in combined
        assert "5.0" in combined or "5" in combined
    
    def test_includes_action_type(self, agent, sample_metadata):
        """Test that primary includes action type."""
        result = agent.generate_primary(sample_metadata)
        combined = " ".join(result)
        assert "推镜头" in combined
    
    def test_includes_equipment_suggestion(self, agent, sample_metadata):
        """Test that primary includes equipment suggestion."""
        result = agent.generate_primary(sample_metadata)
        combined = " ".join(result)
        # Should have some equipment-related text
        assert any(word in combined for word in ["滑轨", "稳定器", "云台", "三脚架"])
    
    def test_includes_confidence(self, agent, sample_metadata):
        """Test that primary includes confidence."""
        result = agent.generate_primary(sample_metadata)
        combined = " ".join(result)
        assert "置信度" in combined


class TestGenerateExplain(TestInstructionGeneratorAgent):
    """Tests for Layer2 Explain generation (Requirement 5.3)."""
    
    def test_returns_string(self, agent, sample_metadata):
        """Test that generate_explain returns a string."""
        result = agent.generate_explain(sample_metadata)
        assert isinstance(result, str)
    
    def test_returns_non_empty(self, agent, sample_metadata):
        """Test that generate_explain returns non-empty string."""
        result = agent.generate_explain(sample_metadata)
        assert len(result) > 0
    
    def test_contains_motion_explanation(self, agent, sample_metadata):
        """Test that explain contains motion-related explanation."""
        result = agent.generate_explain(sample_metadata)
        # Should mention something about the motion
        assert any(word in result for word in ["推进", "运动", "镜头", "画面"])
    
    def test_contains_framing_explanation(self, agent, sample_metadata):
        """Test that explain contains framing-related explanation."""
        result = agent.generate_explain(sample_metadata)
        # Should mention something about composition
        assert any(word in result for word in ["主体", "构图", "画面", "占"])


class TestGenerateAdvanced(TestInstructionGeneratorAgent):
    """Tests for Layer3 Advanced generation (Requirement 5.4)."""
    
    def test_returns_advanced_params(self, agent, sample_metadata):
        """Test that generate_advanced returns AdvancedParams."""
        result = agent.generate_advanced(sample_metadata)
        assert isinstance(result, AdvancedParams)
    
    def test_includes_target_occupancy(self, agent, sample_metadata):
        """Test that advanced includes target occupancy."""
        result = agent.generate_advanced(sample_metadata)
        assert result.target_occupancy is not None
        assert len(result.target_occupancy) > 0
    
    def test_includes_duration(self, agent, sample_metadata):
        """Test that advanced includes duration."""
        result = agent.generate_advanced(sample_metadata)
        assert result.duration_s == 5.0
    
    def test_includes_speed_curve(self, agent, sample_metadata):
        """Test that advanced includes speed curve."""
        result = agent.generate_advanced(sample_metadata)
        assert result.speed_curve is not None
        assert len(result.speed_curve) > 0
    
    def test_includes_stabilization(self, agent, sample_metadata):
        """Test that advanced includes stabilization recommendation."""
        result = agent.generate_advanced(sample_metadata)
        assert result.stabilization is not None
        assert len(result.stabilization) > 0
    
    def test_includes_notes(self, agent, sample_metadata):
        """Test that advanced includes professional notes."""
        result = agent.generate_advanced(sample_metadata)
        assert isinstance(result.notes, list)
        # Should have at least one note
        assert len(result.notes) >= 1


class TestProcess(TestInstructionGeneratorAgent):
    """Tests for process method."""
    
    @pytest.mark.asyncio
    async def test_process_returns_instruction_card(self, agent, sample_metadata):
        """Test that process returns InstructionCard."""
        result = await agent.process(sample_metadata)
        assert isinstance(result, InstructionCard)
    
    @pytest.mark.asyncio
    async def test_process_card_is_complete(self, agent, sample_metadata):
        """Test that generated card is complete."""
        result = await agent.process(sample_metadata)
        assert result.is_complete()
    
    @pytest.mark.asyncio
    async def test_process_has_all_layers(self, agent, sample_metadata):
        """Test that card has all three layers."""
        result = await agent.process(sample_metadata)
        assert len(result.primary) > 0
        assert len(result.explain) > 0
        assert result.advanced is not None
    
    def test_process_sync(self, agent, sample_metadata):
        """Test synchronous process method."""
        result = agent.process_sync(sample_metadata)
        assert isinstance(result, InstructionCard)
        assert result.is_complete()
    
    def test_generate_instruction_card(self, agent, sample_metadata):
        """Test generate_instruction_card method."""
        result = agent.generate_instruction_card(sample_metadata, video_id="test-001")
        assert isinstance(result, InstructionCard)
        assert result.video_id == "test-001"
        assert result.is_complete()


class TestInstructionCardCompleteness(TestInstructionGeneratorAgent):
    """Tests for instruction card completeness (Property 10)."""
    
    @pytest.mark.asyncio
    async def test_all_motion_types_produce_complete_cards(self, agent):
        """Test that all motion types produce complete instruction cards."""
        for motion_type in MotionType:
            metadata = MetadataOutput(
                time_range=(0.0, 5.0),
                motion_type=motion_type,
                motion_params=MotionParams(
                    duration_s=5.0,
                    frame_pct_change=0.15,
                    speed_profile=SpeedProfile.LINEAR,
                    motion_smoothness=0.5,
                ),
                framing=FramingData(
                    subject_bbox=BBox(x=0.3, y=0.3, w=0.4, h=0.4),
                    subject_occupancy=0.35,
                    suggested_scale=SuggestedScale.MEDIUM,
                ),
                beat_alignment_score=0.5,
                confidence=0.7,
                explainability="测试说明。",
            )
            result = await agent.process(metadata)
            assert result.is_complete(), f"Card incomplete for motion type: {motion_type}"
