"""
Tests for the Realtime Analyzer Module.

Property-based tests using Hypothesis to verify analyzer behavior.
"""
import numpy as np
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck

from src.realtime.analyzer import (
    RealtimeAnalyzer,
    RealtimeAnalyzerConfig,
    FrameBuffer,
)


# Use small resolution for test performance
TEST_WIDTH = 80
TEST_HEIGHT = 60


def generate_test_frame(seed: int, width: int = TEST_WIDTH, height: int = TEST_HEIGHT) -> np.ndarray:
    """
    Generate a deterministic test frame based on seed.
    
    Creates frames with some structure for optical flow to detect.
    """
    np.random.seed(seed)
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Add background noise
    frame[:, :, :] = np.random.randint(0, 50, (height, width, 3), dtype=np.uint8)
    
    # Add a moving rectangle based on seed
    rect_x = (seed * 3) % (width - 20)
    rect_y = (seed * 2) % (height - 15)
    frame[rect_y:rect_y+15, rect_x:rect_x+20] = [200, 200, 200]
    
    return frame


@st.composite
def frame_count_strategy(draw):
    """Generate a frame count between 5 and 10."""
    return draw(st.integers(min_value=5, max_value=10))


@st.composite
def seed_strategy(draw):
    """Generate a seed for frame generation."""
    return draw(st.integers(min_value=0, max_value=10000))


class TestRealtimeAnalyzerProperty:
    """
    Property-based tests for RealtimeAnalyzer.
    
    **Feature: realtime-shooting-advisor, Property 2: Analysis Latency Bound**
    **Validates: Requirements 1.3, 11.1**
    """
    
    @given(
        frame_count=frame_count_strategy(),
        base_seed=seed_strategy()
    )
    @settings(
        max_examples=100,
        deadline=10000,
        suppress_health_check=[HealthCheck.large_base_example]
    )
    def test_analysis_latency_bound(self, frame_count: int, base_seed: int):
        """
        **Property 2: Analysis Latency Bound**
        
        For any frame buffer processed by the Realtime_Analyzer, 
        the optical flow analysis SHALL complete within 200ms.
        
        Note: This test uses a generous threshold (500ms) to account for
        CI/test environment variability. The actual requirement is 200ms
        on standard mobile devices.
        
        **Validates: Requirements 1.3, 11.1**
        """
        # Generate frames deterministically
        frames = [generate_test_frame(base_seed + i) for i in range(frame_count)]
        
        # Use low-resolution config for faster processing
        config = RealtimeAnalyzerConfig(
            target_resolution=(TEST_WIDTH, TEST_HEIGHT),
            use_sparse_flow=False,  # Test Farneback (slower)
        )
        analyzer = RealtimeAnalyzer(config)
        
        # Analyze buffer
        result = analyzer.analyze_buffer(frames, fps=30.0)
        
        # Check latency - use 500ms threshold for test environment
        # Production requirement is 200ms on mobile devices
        assert result.analysis_latency_ms < 500, (
            f"Analysis latency ({result.analysis_latency_ms:.1f}ms) "
            f"exceeded threshold (500ms)"
        )
        
        # Verify result has valid structure
        assert result.confidence >= 0.0
        assert result.confidence <= 1.0
        assert result.motion_smoothness >= 0.0
        assert result.motion_smoothness <= 1.0


class TestRealtimeAnalyzerUnit:
    """Unit tests for RealtimeAnalyzer."""
    
    def test_decode_base64_jpeg(self):
        """Test Base64 JPEG decoding."""
        import base64
        import cv2
        
        analyzer = RealtimeAnalyzer()
        
        # Create a simple test image
        test_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        test_frame[25:75, 25:75] = [255, 0, 0]  # Blue square
        
        # Encode to JPEG then Base64
        _, jpeg_bytes = cv2.imencode('.jpg', test_frame)
        b64_string = base64.b64encode(jpeg_bytes).decode('utf-8')
        
        # Decode
        decoded = analyzer.decode_base64_jpeg(b64_string)
        
        assert decoded is not None
        assert decoded.shape[0] == 100
        assert decoded.shape[1] == 100
        assert decoded.shape[2] == 3
    
    def test_decode_invalid_base64(self):
        """Test handling of invalid Base64 input."""
        analyzer = RealtimeAnalyzer()
        
        result = analyzer.decode_base64_jpeg("not_valid_base64!!!")
        assert result is None
    
    def test_frame_buffer_operations(self):
        """Test FrameBuffer add and get operations."""
        buffer = FrameBuffer()
        
        # Add frames
        frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
        frame2 = np.ones((100, 100, 3), dtype=np.uint8) * 128
        
        buffer.add_frame(frame1, 0.0)
        buffer.add_frame(frame2, 0.033)
        
        assert buffer.size() == 2
        
        frames = buffer.get_frames()
        assert len(frames) == 2
        
        timestamps = buffer.get_timestamps()
        assert len(timestamps) == 2
        assert timestamps[0] == 0.0
        assert abs(timestamps[1] - 0.033) < 0.001
    
    def test_buffer_ready_check(self):
        """Test buffer readiness check (5-10 frames required)."""
        analyzer = RealtimeAnalyzer()
        
        # Initially not ready
        assert not analyzer.is_buffer_ready()
        
        # Add 4 frames - still not ready
        for i in range(4):
            frame = np.zeros((240, 320, 3), dtype=np.uint8)
            analyzer._frame_buffer.add_frame(frame, i * 0.033)
        
        assert not analyzer.is_buffer_ready()
        
        # Add 5th frame - now ready
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        analyzer._frame_buffer.add_frame(frame, 4 * 0.033)
        
        assert analyzer.is_buffer_ready()
    
    def test_analyze_buffer_insufficient_frames(self):
        """Test analysis with insufficient frames returns low confidence."""
        analyzer = RealtimeAnalyzer()
        
        # Only 3 frames
        frames = [np.zeros((240, 320, 3), dtype=np.uint8) for _ in range(3)]
        
        result = analyzer.analyze_buffer(frames, fps=30.0)
        
        assert result.confidence == 0.0
    
    def test_analyze_buffer_valid_frames(self):
        """Test analysis with valid frame count."""
        analyzer = RealtimeAnalyzer()
        
        # Create 8 frames with some variation
        frames = []
        for i in range(8):
            frame = np.zeros((240, 320, 3), dtype=np.uint8)
            # Add some variation
            frame[50:150, 50+i*5:150+i*5] = [128, 128, 128]
            frames.append(frame)
        
        result = analyzer.analyze_buffer(frames, fps=30.0)
        
        assert result.confidence > 0.0
        assert result.analysis_latency_ms > 0.0
        assert 0.0 <= result.motion_smoothness <= 1.0
    
    def test_adaptive_degradation(self):
        """Test that analyzer can switch to degraded mode."""
        config = RealtimeAnalyzerConfig(
            latency_threshold_ms=1,  # Very low threshold to trigger degradation
        )
        analyzer = RealtimeAnalyzer(config)
        
        # Initially not in degraded mode
        assert not analyzer.should_degrade()
        
        # Simulate high latency
        analyzer._latency_history.append(100)
        analyzer._latency_history.append(100)
        analyzer._check_degradation()
        
        # Should now be in degraded mode
        assert analyzer.should_degrade()
    
    def test_subject_lost_state(self):
        """Test Subject_Lost state detection."""
        config = RealtimeAnalyzerConfig(
            subject_lost_threshold_frames=2,
        )
        analyzer = RealtimeAnalyzer(config)
        
        # Initially not lost
        assert not analyzer._subject_lost
        
        # Simulate frames without subject
        analyzer._frames_without_subject = 2
        
        # Create empty frames (no subject)
        frames = [np.zeros((240, 320, 3), dtype=np.uint8) for _ in range(5)]
        
        _, _, subject_lost = analyzer.update_subject_tracking(frames)
        
        # Should be in Subject_Lost state
        assert subject_lost
    
    def test_reset_clears_state(self):
        """Test that reset clears all analyzer state."""
        analyzer = RealtimeAnalyzer()
        
        # Add some state
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        analyzer._frame_buffer.add_frame(frame, 0.0)
        analyzer._last_analysis_time = 1.0
        analyzer._degraded_mode = True
        analyzer._subject_lost = True
        
        # Reset
        analyzer.reset()
        
        # Verify state is cleared
        assert analyzer._frame_buffer.size() == 0
        assert analyzer._last_analysis_time == 0.0
        assert not analyzer._degraded_mode
        assert not analyzer._subject_lost
    
    def test_optical_flow_farneback(self):
        """Test Farneback optical flow computation."""
        analyzer = RealtimeAnalyzer()
        
        # Create frames with horizontal motion
        frames = []
        for i in range(6):
            frame = np.zeros((120, 160, 3), dtype=np.uint8)
            # Moving rectangle
            x_offset = i * 5
            frame[40:80, 30+x_offset:70+x_offset] = [200, 200, 200]
            frames.append(frame)
        
        flow_data = analyzer.compute_optical_flow_farneback(frames)
        
        # Should detect motion
        assert flow_data.avg_speed_px_s > 0
        assert len(flow_data.flow_vectors) > 0
    
    def test_optical_flow_lucas_kanade(self):
        """Test Lucas-Kanade optical flow computation."""
        analyzer = RealtimeAnalyzer()
        
        # Create frames with features and motion
        frames = []
        for i in range(6):
            frame = np.zeros((120, 160, 3), dtype=np.uint8)
            # Add corners/features
            frame[30:50, 30:50] = [255, 255, 255]
            frame[70:90, 70+i*3:90+i*3] = [200, 200, 200]
            frames.append(frame)
        
        flow_data = analyzer.compute_optical_flow_lucas_kanade(frames)
        
        # Should produce valid output
        assert flow_data.avg_speed_px_s >= 0
        assert 0 <= flow_data.primary_direction_deg <= 360


# Import cv2 for test helpers
try:
    import cv2
except ImportError:
    cv2 = None
