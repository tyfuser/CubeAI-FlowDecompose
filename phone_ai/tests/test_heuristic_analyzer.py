"""
Unit tests for the Heuristic Analyzer Agent.
"""
import pytest
from src.models.data_types import (
    BBox,
    OpticalFlowData,
    SubjectTrackingData,
    FeatureOutput,
    HeuristicOutput,
)
from src.agents.heuristic_analyzer import (
    HeuristicAnalyzerAgent,
    HeuristicAnalyzerConfig,
)


class TestHeuristicAnalyzerAgent:
    """Tests for HeuristicAnalyzerAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create a HeuristicAnalyzerAgent instance."""
        return HeuristicAnalyzerAgent()
    
    @pytest.fixture
    def sample_optical_flow(self):
        """Create sample optical flow data."""
        return OpticalFlowData(
            avg_speed_px_s=50.0,
            primary_direction_deg=45.0,
            flow_vectors=[
                (1.0, 1.0), (1.2, 1.1), (1.1, 1.0),
                (1.3, 1.2), (1.0, 0.9), (1.1, 1.1),
            ]
        )
    
    @pytest.fixture
    def sample_bbox_sequence(self):
        """Create sample bounding box sequence."""
        return [
            BBox(x=0.3, y=0.3, w=0.2, h=0.3),
            BBox(x=0.29, y=0.29, w=0.22, h=0.32),
            BBox(x=0.28, y=0.28, w=0.24, h=0.34),
            BBox(x=0.27, y=0.27, w=0.26, h=0.36),
        ]
    
    @pytest.fixture
    def sample_feature_output(self, sample_optical_flow, sample_bbox_sequence):
        """Create sample feature output."""
        return FeatureOutput(
            video_id="test-001",
            optical_flow=sample_optical_flow,
            subject_tracking=SubjectTrackingData(
                bbox_sequence=sample_bbox_sequence,
                confidence_scores=[0.9, 0.88, 0.86, 0.84],
                timestamps=[0.0, 0.5, 1.0, 1.5],
            ),
            audio_beats=[0.5, 1.0, 1.5, 2.0],
        )


class TestCalculateAvgMotion(TestHeuristicAnalyzerAgent):
    """Tests for calculate_avg_motion method."""
    
    def test_returns_avg_speed_from_optical_flow(self, agent, sample_optical_flow):
        """Test that avg motion is extracted from optical flow data."""
        result = agent.calculate_avg_motion(sample_optical_flow, duration=10.0)
        assert result == 50.0
    
    def test_returns_non_negative(self, agent):
        """Test that result is always non-negative."""
        optical_flow = OpticalFlowData(
            avg_speed_px_s=-10.0,  # Invalid negative value
            primary_direction_deg=0.0,
            flow_vectors=[],
        )
        result = agent.calculate_avg_motion(optical_flow, duration=10.0)
        assert result >= 0.0


class TestCalculateFramePctChange(TestHeuristicAnalyzerAgent):
    """Tests for calculate_frame_pct_change method."""
    
    def test_returns_zero_for_empty_sequence(self, agent):
        """Test that empty sequence returns 0."""
        result = agent.calculate_frame_pct_change([])
        assert result == 0.0
    
    def test_returns_zero_for_single_bbox(self, agent):
        """Test that single bbox returns 0."""
        result = agent.calculate_frame_pct_change([BBox(0.1, 0.1, 0.2, 0.2)])
        assert result == 0.0
    
    def test_returns_value_in_range(self, agent, sample_bbox_sequence):
        """Test that result is in [0, 1] range."""
        result = agent.calculate_frame_pct_change(sample_bbox_sequence)
        assert 0.0 <= result <= 1.0
    
    def test_detects_area_change(self, agent):
        """Test that area changes are detected."""
        # Sequence with increasing area
        bboxes = [
            BBox(x=0.3, y=0.3, w=0.1, h=0.1),  # area = 0.01
            BBox(x=0.3, y=0.3, w=0.2, h=0.2),  # area = 0.04
            BBox(x=0.3, y=0.3, w=0.3, h=0.3),  # area = 0.09
        ]
        result = agent.calculate_frame_pct_change(bboxes)
        assert result > 0.0


class TestCalculateMotionSmoothness(TestHeuristicAnalyzerAgent):
    """Tests for calculate_motion_smoothness method."""
    
    def test_returns_default_for_insufficient_data(self, agent):
        """Test that insufficient data returns default value."""
        optical_flow = OpticalFlowData(
            avg_speed_px_s=50.0,
            primary_direction_deg=0.0,
            flow_vectors=[(1.0, 1.0)],  # Only one vector
        )
        result = agent.calculate_motion_smoothness(optical_flow)
        assert result == 0.5
    
    def test_returns_value_in_range(self, agent, sample_optical_flow):
        """Test that result is in [0, 1] range."""
        result = agent.calculate_motion_smoothness(sample_optical_flow)
        assert 0.0 <= result <= 1.0
    
    def test_smooth_motion_has_high_score(self, agent):
        """Test that smooth motion (constant velocity) has high score."""
        # Constant velocity vectors
        optical_flow = OpticalFlowData(
            avg_speed_px_s=50.0,
            primary_direction_deg=0.0,
            flow_vectors=[(1.0, 0.0)] * 10,  # Constant motion
        )
        result = agent.calculate_motion_smoothness(optical_flow)
        assert result > 0.8
    
    def test_jerky_motion_has_lower_score(self, agent):
        """Test that jerky motion has lower score."""
        # Highly variable velocity vectors
        optical_flow = OpticalFlowData(
            avg_speed_px_s=50.0,
            primary_direction_deg=0.0,
            flow_vectors=[
                (10.0, 0.0), (0.1, 0.0), (10.0, 0.0),
                (0.1, 0.0), (10.0, 0.0), (0.1, 0.0),
            ],
        )
        result = agent.calculate_motion_smoothness(optical_flow)
        # Should be lower than smooth motion
        assert result < 0.8


class TestCalculateSubjectOccupancy(TestHeuristicAnalyzerAgent):
    """Tests for calculate_subject_occupancy method."""
    
    def test_returns_zero_for_empty_sequence(self, agent):
        """Test that empty sequence returns 0."""
        result = agent.calculate_subject_occupancy([])
        assert result == 0.0
    
    def test_returns_value_in_range(self, agent, sample_bbox_sequence):
        """Test that result is in [0, 1] range."""
        result = agent.calculate_subject_occupancy(sample_bbox_sequence)
        assert 0.0 <= result <= 1.0
    
    def test_calculates_average_area(self, agent):
        """Test that average area is calculated correctly."""
        bboxes = [
            BBox(x=0.0, y=0.0, w=0.5, h=0.5),  # area = 0.25
            BBox(x=0.0, y=0.0, w=0.5, h=0.5),  # area = 0.25
        ]
        result = agent.calculate_subject_occupancy(bboxes)
        assert abs(result - 0.25) < 0.001


class TestCalculateBeatAlignment(TestHeuristicAnalyzerAgent):
    """Tests for calculate_beat_alignment method."""
    
    def test_returns_default_for_empty_motion(self, agent):
        """Test that empty motion timestamps returns default."""
        result = agent.calculate_beat_alignment([], [0.5, 1.0, 1.5])
        assert result == 0.5
    
    def test_returns_default_for_empty_beats(self, agent):
        """Test that empty beat timestamps returns default."""
        result = agent.calculate_beat_alignment([0.5, 1.0], [])
        assert result == 0.5
    
    def test_returns_value_in_range(self, agent):
        """Test that result is in [0, 1] range."""
        result = agent.calculate_beat_alignment(
            [0.5, 1.0, 1.5],
            [0.5, 1.0, 1.5, 2.0]
        )
        assert 0.0 <= result <= 1.0
    
    def test_perfect_alignment_has_high_score(self, agent):
        """Test that perfect alignment has high score."""
        # Motion exactly on beats
        result = agent.calculate_beat_alignment(
            [0.5, 1.0, 1.5],
            [0.5, 1.0, 1.5]
        )
        assert result > 0.9
    
    def test_poor_alignment_has_lower_score(self, agent):
        """Test that poor alignment has lower score."""
        # Motion far from beats
        result = agent.calculate_beat_alignment(
            [0.25, 0.75, 1.25],  # Off-beat
            [0.5, 1.0, 1.5]
        )
        # Should be lower than perfect alignment
        assert result < 0.9


class TestProcess(TestHeuristicAnalyzerAgent):
    """Tests for process method."""
    
    @pytest.mark.asyncio
    async def test_process_returns_valid_output(self, agent, sample_feature_output):
        """Test that process returns valid HeuristicOutput."""
        result = await agent.process(
            sample_feature_output,
            time_range=(0.0, 10.0)
        )
        
        assert isinstance(result, HeuristicOutput)
        assert result.video_id == "test-001"
        assert result.time_range == (0.0, 10.0)
        assert result.is_valid()
    
    @pytest.mark.asyncio
    async def test_process_all_indicators_in_range(self, agent, sample_feature_output):
        """Test that all indicators are in valid ranges."""
        result = await agent.process(
            sample_feature_output,
            time_range=(0.0, 10.0)
        )
        
        assert result.avg_motion_px_per_s >= 0
        assert 0.0 <= result.frame_pct_change <= 1.0
        assert 0.0 <= result.motion_smoothness <= 1.0
        assert 0.0 <= result.subject_occupancy <= 1.0
        assert 0.0 <= result.beat_alignment_score <= 1.0
    
    def test_process_sync(self, agent, sample_feature_output):
        """Test synchronous process method."""
        result = agent.process_sync(
            sample_feature_output,
            time_range=(0.0, 10.0)
        )
        
        assert isinstance(result, HeuristicOutput)
        assert result.is_valid()
