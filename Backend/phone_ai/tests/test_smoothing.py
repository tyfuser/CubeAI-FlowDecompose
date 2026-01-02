"""
Tests for the Smoothing Filter Module.

Property-based tests using Hypothesis to verify smoothing behavior.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume

from src.realtime.smoothing import (
    SmoothingFilter,
    SmoothingFilterConfig,
    IndicatorValues,
)


# Strategies for generating test data
indicator_value_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
speed_strategy = st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
direction_strategy = st.floats(min_value=0.0, max_value=360.0, allow_nan=False, allow_infinity=False)


@st.composite
def indicator_values_strategy(draw):
    """Generate random IndicatorValues."""
    return IndicatorValues(
        motion_smoothness=draw(indicator_value_strategy),
        avg_speed=draw(speed_strategy),
        speed_variance=draw(st.floats(min_value=0.0, max_value=50.0, allow_nan=False, allow_infinity=False)),
        primary_direction_deg=draw(direction_strategy),
        subject_occupancy=draw(indicator_value_strategy),
        confidence=draw(indicator_value_strategy),
    )


@st.composite
def noisy_sequence_strategy(draw, min_length=10, max_length=50):
    """
    Generate a sequence of noisy indicator values.
    
    Creates a base value with added noise to simulate real sensor data.
    """
    length = draw(st.integers(min_value=min_length, max_value=max_length))
    
    # Base values
    base_smoothness = draw(st.floats(min_value=0.2, max_value=0.8, allow_nan=False, allow_infinity=False))
    base_speed = draw(st.floats(min_value=5.0, max_value=50.0, allow_nan=False, allow_infinity=False))
    base_direction = draw(st.floats(min_value=0.0, max_value=360.0, allow_nan=False, allow_infinity=False))
    
    # Noise level (standard deviation)
    noise_level = draw(st.floats(min_value=0.05, max_value=0.3, allow_nan=False, allow_infinity=False))
    
    sequence = []
    for _ in range(length):
        # Add noise to base values
        noisy_smoothness = max(0.0, min(1.0, base_smoothness + draw(
            st.floats(min_value=-noise_level, max_value=noise_level, allow_nan=False, allow_infinity=False)
        )))
        noisy_speed = max(0.0, base_speed + draw(
            st.floats(min_value=-noise_level * 20, max_value=noise_level * 20, allow_nan=False, allow_infinity=False)
        ))
        noisy_direction = (base_direction + draw(
            st.floats(min_value=-noise_level * 30, max_value=noise_level * 30, allow_nan=False, allow_infinity=False)
        )) % 360
        
        sequence.append(IndicatorValues(
            motion_smoothness=noisy_smoothness,
            avg_speed=noisy_speed,
            speed_variance=draw(st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False)),
            primary_direction_deg=noisy_direction,
            subject_occupancy=draw(indicator_value_strategy),
            confidence=draw(indicator_value_strategy),
        ))
    
    return sequence, noise_level


class TestSmoothingFilterProperty:
    """
    Property-based tests for SmoothingFilter.
    
    **Feature: realtime-shooting-advisor, Property 12: Smoothing Filter Effect**
    **Validates: Requirements 13.1**
    """
    
    @given(noisy_sequence_strategy(min_length=10, max_length=30))
    @settings(max_examples=100, deadline=5000)
    def test_smoothing_reduces_variance(self, sequence_and_noise):
        """
        **Property 12: Smoothing Filter Effect**
        
        For any sequence of raw indicator values, the smoothed output 
        SHALL have lower variance than the raw input.
        
        **Validates: Requirements 13.1**
        """
        sequence, noise_level = sequence_and_noise
        
        # Skip sequences with very low noise (nothing to smooth)
        assume(noise_level > 0.05)
        assume(len(sequence) >= 10)
        
        # Test with Kalman filter
        kalman_filter = SmoothingFilter(SmoothingFilterConfig(use_kalman=True))
        
        raw_values = []
        smoothed_values = []
        
        for indicators in sequence:
            raw_values.append(indicators.motion_smoothness)
            smoothed = kalman_filter.update(indicators)
            smoothed_values.append(smoothed.motion_smoothness)
        
        # Calculate variances (skip first few values for filter warm-up)
        warmup = 3
        raw_subset = raw_values[warmup:]
        smoothed_subset = smoothed_values[warmup:]
        
        if len(raw_subset) < 5:
            return  # Not enough data after warmup
        
        raw_mean = sum(raw_subset) / len(raw_subset)
        raw_variance = sum((v - raw_mean) ** 2 for v in raw_subset) / len(raw_subset)
        
        smoothed_mean = sum(smoothed_subset) / len(smoothed_subset)
        smoothed_variance = sum((v - smoothed_mean) ** 2 for v in smoothed_subset) / len(smoothed_subset)
        
        # Smoothed variance should be less than or equal to raw variance
        # Allow small tolerance for numerical precision
        assert smoothed_variance <= raw_variance + 1e-6, (
            f"Smoothed variance ({smoothed_variance:.6f}) should be <= "
            f"raw variance ({raw_variance:.6f})"
        )


class TestSmoothingFilterUnit:
    """Unit tests for SmoothingFilter."""
    
    def test_kalman_filter_initialization(self):
        """Test that Kalman filter initializes correctly."""
        filter = SmoothingFilter(SmoothingFilterConfig(use_kalman=True))
        
        indicators = IndicatorValues(
            motion_smoothness=0.5,
            avg_speed=10.0,
            speed_variance=2.0,
            primary_direction_deg=90.0,
            subject_occupancy=0.3,
            confidence=0.8,
        )
        
        # First update should return close to input
        result = filter.update(indicators)
        assert abs(result.motion_smoothness - 0.5) < 0.01
        assert abs(result.avg_speed - 10.0) < 0.1
    
    def test_sliding_window_average(self):
        """Test sliding window average fallback."""
        filter = SmoothingFilter(SmoothingFilterConfig(
            use_kalman=False,
            window_size=3,
        ))
        
        # Add three values
        filter.update(IndicatorValues(0.3, 10.0, 1.0, 90.0, 0.2, 0.7))
        filter.update(IndicatorValues(0.5, 15.0, 2.0, 90.0, 0.3, 0.8))
        result = filter.update(IndicatorValues(0.7, 20.0, 3.0, 90.0, 0.4, 0.9))
        
        # Should be average of all three
        assert abs(result.motion_smoothness - 0.5) < 0.01
        assert abs(result.avg_speed - 15.0) < 0.1
    
    def test_anomaly_detection_triggers_suppression(self):
        """Test that anomaly detection triggers suppression."""
        filter = SmoothingFilter(SmoothingFilterConfig(
            anomaly_threshold=2.0,
            anomaly_suppress_cycles=2,
        ))
        
        # Build up history with stable values
        for _ in range(5):
            filter.update(IndicatorValues(0.5, 10.0, 1.0, 90.0, 0.3, 0.8))
        
        assert not filter.is_suppressed()
        
        # Introduce anomaly (sudden large change)
        filter.update(IndicatorValues(0.1, 100.0, 1.0, 90.0, 0.3, 0.8))
        
        # Should be suppressed
        assert filter.is_suppressed()
    
    def test_suppression_countdown(self):
        """Test that suppression countdown decrements correctly."""
        filter = SmoothingFilter(SmoothingFilterConfig(
            anomaly_threshold=1.5,
            anomaly_suppress_cycles=2,
        ))
        
        # Build up history
        for _ in range(5):
            filter.update(IndicatorValues(0.5, 10.0, 1.0, 90.0, 0.3, 0.8))
        
        # Trigger anomaly
        filter.update(IndicatorValues(0.05, 100.0, 1.0, 90.0, 0.3, 0.8))
        assert filter.is_suppressed()
        
        # First normal update - still suppressed (countdown = 1)
        filter.update(IndicatorValues(0.5, 10.0, 1.0, 90.0, 0.3, 0.8))
        assert filter.is_suppressed()
        
        # Second normal update - no longer suppressed (countdown = 0)
        filter.update(IndicatorValues(0.5, 10.0, 1.0, 90.0, 0.3, 0.8))
        assert not filter.is_suppressed()
    
    def test_reset_clears_state(self):
        """Test that reset clears all filter state."""
        filter = SmoothingFilter()
        
        # Add some data
        for _ in range(5):
            filter.update(IndicatorValues(0.5, 10.0, 1.0, 90.0, 0.3, 0.8))
        
        # Reset
        filter.reset()
        
        # Should be back to initial state
        assert len(filter._history) == 0
        assert not filter._initialized
        assert filter._anomaly_countdown == 0
    
    def test_direction_averaging_handles_wraparound(self):
        """Test that direction averaging handles 0/360 wraparound."""
        filter = SmoothingFilter(SmoothingFilterConfig(
            use_kalman=False,
            window_size=3,
        ))
        
        # Add values around 0/360 boundary
        filter.update(IndicatorValues(0.5, 10.0, 1.0, 350.0, 0.3, 0.8))
        filter.update(IndicatorValues(0.5, 10.0, 1.0, 0.0, 0.3, 0.8))
        result = filter.update(IndicatorValues(0.5, 10.0, 1.0, 10.0, 0.3, 0.8))
        
        # Average should be around 0 degrees, not 120 degrees
        assert result.primary_direction_deg < 30 or result.primary_direction_deg > 330
