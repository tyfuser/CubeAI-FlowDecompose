"""
Smoothing Filter Module

平滑滤波器，应用 Kalman 滤波或滑动窗口平均来减少噪声。
Applies Kalman filter or sliding window average to reduce noise in indicator values.

Requirements: 13.1, 13.2
"""
from collections import deque
from dataclasses import dataclass, field
from typing import Optional
import math


@dataclass
class SmoothingFilterConfig:
    """Configuration for smoothing filter."""
    window_size: int = 3  # Sliding window size
    use_kalman: bool = True  # Use Kalman filter vs simple average
    anomaly_threshold: float = 2.0  # Std devs for anomaly detection
    anomaly_suppress_cycles: int = 2  # Cycles to suppress after anomaly
    
    # Kalman filter parameters
    process_noise: float = 0.01  # Q - process noise covariance
    measurement_noise: float = 0.1  # R - measurement noise covariance
    initial_estimate_error: float = 1.0  # P - initial estimate error covariance


@dataclass
class IndicatorValues:
    """
    Container for indicator values that need smoothing.
    Simplified representation of key metrics from analysis.
    """
    motion_smoothness: float
    avg_speed: float
    speed_variance: float
    primary_direction_deg: float
    subject_occupancy: float = 0.0
    confidence: float = 0.5
    
    def to_tuple(self) -> tuple[float, ...]:
        """Convert to tuple for numerical operations."""
        return (
            self.motion_smoothness,
            self.avg_speed,
            self.speed_variance,
            self.primary_direction_deg,
            self.subject_occupancy,
            self.confidence,
        )
    
    @classmethod
    def from_tuple(cls, values: tuple[float, ...]) -> "IndicatorValues":
        """Create from tuple."""
        return cls(
            motion_smoothness=values[0],
            avg_speed=values[1],
            speed_variance=values[2],
            primary_direction_deg=values[3],
            subject_occupancy=values[4] if len(values) > 4 else 0.0,
            confidence=values[5] if len(values) > 5 else 0.5,
        )


@dataclass
class KalmanState:
    """State for a single-variable Kalman filter."""
    estimate: float = 0.0  # Current state estimate (x)
    error_covariance: float = 1.0  # Estimate error covariance (P)



class SmoothingFilter:
    """
    平滑滤波器
    Applies Kalman filter or sliding window average to reduce noise.
    
    The filter maintains state for each indicator and applies smoothing
    to reduce noise while preserving meaningful signal changes.
    
    Property 12: For any sequence of raw indicator values, the smoothed 
    output SHALL have lower variance than the raw input.
    """
    
    def __init__(self, config: Optional[SmoothingFilterConfig] = None):
        self.config = config or SmoothingFilterConfig()
        self._history: deque[IndicatorValues] = deque(maxlen=self.config.window_size)
        
        # Kalman filter states for each indicator
        self._kalman_states: dict[str, KalmanState] = {
            "motion_smoothness": KalmanState(error_covariance=self.config.initial_estimate_error),
            "avg_speed": KalmanState(error_covariance=self.config.initial_estimate_error),
            "speed_variance": KalmanState(error_covariance=self.config.initial_estimate_error),
            "primary_direction_deg": KalmanState(error_covariance=self.config.initial_estimate_error),
            "subject_occupancy": KalmanState(error_covariance=self.config.initial_estimate_error),
            "confidence": KalmanState(error_covariance=self.config.initial_estimate_error),
        }
        
        self._anomaly_countdown: int = 0
        self._initialized: bool = False
    
    def is_suppressed(self) -> bool:
        """Check if advice generation should be suppressed due to anomaly."""
        return self._anomaly_countdown > 0
    
    def update(self, indicators: IndicatorValues) -> IndicatorValues:
        """
        Apply smoothing to new indicators.
        
        Args:
            indicators: Raw indicator values
            
        Returns:
            Smoothed indicator values
        """
        # Decrement anomaly countdown first (before checking for new anomaly)
        if self._anomaly_countdown > 0:
            self._anomaly_countdown -= 1
        
        # Check for anomaly (sets countdown, overriding any decrement)
        if self._initialized and self.detect_anomaly(indicators):
            self._anomaly_countdown = self.config.anomaly_suppress_cycles
        
        # Add to history for sliding window
        self._history.append(indicators)
        
        # Apply smoothing based on configuration
        if self.config.use_kalman:
            smoothed = self._apply_kalman_filter(indicators)
        else:
            smoothed = self._apply_sliding_window_average()
        
        self._initialized = True
        return smoothed
    
    def _apply_kalman_filter(self, indicators: IndicatorValues) -> IndicatorValues:
        """
        Apply Kalman filter to each indicator.
        
        The Kalman filter equations:
        1. Predict: x_pred = x_est, P_pred = P_est + Q
        2. Update: K = P_pred / (P_pred + R)
                   x_est = x_pred + K * (measurement - x_pred)
                   P_est = (1 - K) * P_pred
        
        Args:
            indicators: Raw indicator values
            
        Returns:
            Kalman-filtered indicator values
        """
        Q = self.config.process_noise
        R = self.config.measurement_noise
        
        smoothed_values = {}
        
        for name, measurement in [
            ("motion_smoothness", indicators.motion_smoothness),
            ("avg_speed", indicators.avg_speed),
            ("speed_variance", indicators.speed_variance),
            ("primary_direction_deg", indicators.primary_direction_deg),
            ("subject_occupancy", indicators.subject_occupancy),
            ("confidence", indicators.confidence),
        ]:
            state = self._kalman_states[name]
            
            if not self._initialized:
                # Initialize with first measurement
                state.estimate = measurement
                state.error_covariance = self.config.initial_estimate_error
                smoothed_values[name] = measurement
            else:
                # Predict step
                x_pred = state.estimate
                P_pred = state.error_covariance + Q
                
                # Update step
                K = P_pred / (P_pred + R)  # Kalman gain
                state.estimate = x_pred + K * (measurement - x_pred)
                state.error_covariance = (1 - K) * P_pred
                
                smoothed_values[name] = state.estimate
        
        return IndicatorValues(
            motion_smoothness=smoothed_values["motion_smoothness"],
            avg_speed=smoothed_values["avg_speed"],
            speed_variance=smoothed_values["speed_variance"],
            primary_direction_deg=smoothed_values["primary_direction_deg"],
            subject_occupancy=smoothed_values["subject_occupancy"],
            confidence=smoothed_values["confidence"],
        )
    
    def _apply_sliding_window_average(self) -> IndicatorValues:
        """
        Apply sliding window average to indicators.
        
        Returns:
            Averaged indicator values over the window
        """
        if not self._history:
            raise ValueError("No history available for averaging")
        
        n = len(self._history)
        
        # Sum all values in history
        sum_motion_smoothness = sum(h.motion_smoothness for h in self._history)
        sum_avg_speed = sum(h.avg_speed for h in self._history)
        sum_speed_variance = sum(h.speed_variance for h in self._history)
        sum_subject_occupancy = sum(h.subject_occupancy for h in self._history)
        sum_confidence = sum(h.confidence for h in self._history)
        
        # Handle circular direction averaging properly
        sum_sin = sum(math.sin(math.radians(h.primary_direction_deg)) for h in self._history)
        sum_cos = sum(math.cos(math.radians(h.primary_direction_deg)) for h in self._history)
        avg_direction = math.degrees(math.atan2(sum_sin / n, sum_cos / n))
        if avg_direction < 0:
            avg_direction += 360
        
        return IndicatorValues(
            motion_smoothness=sum_motion_smoothness / n,
            avg_speed=sum_avg_speed / n,
            speed_variance=sum_speed_variance / n,
            primary_direction_deg=avg_direction,
            subject_occupancy=sum_subject_occupancy / n,
            confidence=sum_confidence / n,
        )
    
    def detect_anomaly(self, indicators: IndicatorValues) -> bool:
        """
        Detect sudden lighting changes or other anomalies.
        
        An anomaly is detected when the current indicators deviate
        significantly from the recent history (more than anomaly_threshold
        standard deviations).
        
        Args:
            indicators: Current indicator values
            
        Returns:
            True if current indicators are anomalous
        """
        if len(self._history) < 2:
            return False
        
        # Calculate mean and std of motion_smoothness from history
        # (motion_smoothness is most sensitive to lighting changes)
        values = [h.motion_smoothness for h in self._history]
        mean = sum(values) / len(values)
        
        if len(values) > 1:
            variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
            std = math.sqrt(variance) if variance > 0 else 0.001
        else:
            std = 0.001  # Avoid division by zero
        
        # Check if current value is anomalous
        deviation = abs(indicators.motion_smoothness - mean)
        is_anomalous = deviation > (self.config.anomaly_threshold * std)
        
        # Also check avg_speed for sudden changes
        speed_values = [h.avg_speed for h in self._history]
        speed_mean = sum(speed_values) / len(speed_values)
        
        if len(speed_values) > 1:
            speed_variance = sum((v - speed_mean) ** 2 for v in speed_values) / (len(speed_values) - 1)
            speed_std = math.sqrt(speed_variance) if speed_variance > 0 else 0.001
        else:
            speed_std = 0.001
        
        speed_deviation = abs(indicators.avg_speed - speed_mean)
        speed_anomalous = speed_deviation > (self.config.anomaly_threshold * speed_std)
        
        return is_anomalous or speed_anomalous
    
    def reset(self) -> None:
        """Reset the filter state."""
        self._history.clear()
        self._anomaly_countdown = 0
        self._initialized = False
        
        for state in self._kalman_states.values():
            state.estimate = 0.0
            state.error_covariance = self.config.initial_estimate_error
    
    def get_variance_reduction(self) -> Optional[float]:
        """
        Calculate the variance reduction achieved by the filter.
        
        Returns:
            Ratio of output variance to input variance (< 1 means reduction),
            or None if not enough data.
        """
        if len(self._history) < 3:
            return None
        
        # Calculate input variance from history
        values = [h.motion_smoothness for h in self._history]
        mean = sum(values) / len(values)
        input_variance = sum((v - mean) ** 2 for v in values) / len(values)
        
        if input_variance == 0:
            return 1.0  # No variance to reduce
        
        # For Kalman filter, output variance is approximated by error covariance
        if self.config.use_kalman:
            output_variance = self._kalman_states["motion_smoothness"].error_covariance
        else:
            # For sliding window, variance is reduced by factor of window size
            output_variance = input_variance / len(self._history)
        
        return output_variance / input_variance if input_variance > 0 else 1.0
