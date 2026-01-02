"""
Motion type inference rules for the Video Shooting Assistant.

Rule-based classification of camera motion types based on heuristic indicators.
Maps optical flow data and subject tracking to MotionType enum values.
"""
from dataclasses import dataclass
from typing import Optional

from src.models.enums import MotionType, SpeedProfile, SuggestedScale
from src.models.data_types import HeuristicOutput, OpticalFlowData


@dataclass
class MotionRulesConfig:
    """Configuration for motion type inference rules."""
    
    # Motion speed thresholds (pixels per second)
    static_threshold: float = 5.0  # Below this = static
    slow_motion_threshold: float = 50.0  # Below this = slow motion
    fast_motion_threshold: float = 200.0  # Above this = fast motion
    
    # Frame percentage change thresholds
    dolly_threshold: float = 0.05  # Above this suggests dolly movement
    significant_change_threshold: float = 0.15  # Significant size change
    
    # Direction thresholds (degrees)
    horizontal_tolerance: float = 30.0  # Degrees from horizontal for pan
    vertical_tolerance: float = 30.0  # Degrees from vertical for tilt
    
    # Smoothness thresholds
    handheld_smoothness_threshold: float = 0.5  # Below this = handheld
    
    # Subject occupancy thresholds for scale suggestion
    extreme_closeup_threshold: float = 0.5  # Above this = extreme closeup
    closeup_threshold: float = 0.25  # Above this = closeup
    medium_threshold: float = 0.1  # Above this = medium


class MotionTypeInferrer:
    """
    Rule-based motion type classification.
    
    Analyzes heuristic indicators to determine the most likely
    camera motion type and related parameters.
    """
    
    def __init__(self, config: Optional[MotionRulesConfig] = None):
        """
        Initialize the motion type inferrer.
        
        Args:
            config: Configuration for inference rules
        """
        self.config = config or MotionRulesConfig()
    
    def infer_motion_type(
        self,
        heuristic_output: HeuristicOutput,
        primary_direction_deg: Optional[float] = None
    ) -> MotionType:
        """
        Infer the camera motion type from heuristic indicators.
        
        Decision tree:
        1. If motion is very low -> STATIC
        2. If smoothness is low -> HANDHELD
        3. If significant frame_pct_change -> DOLLY_IN or DOLLY_OUT
        4. If horizontal motion dominant -> PAN
        5. If vertical motion dominant -> TILT
        6. If tracking subject -> TRACK
        7. Default -> HANDHELD
        
        Args:
            heuristic_output: Output from the Heuristic Analyzer
            primary_direction_deg: Primary motion direction in degrees (0-360)
                                   0/360 = right, 90 = down, 180 = left, 270 = up
            
        Returns:
            Inferred MotionType
        """
        avg_motion = heuristic_output.avg_motion_px_per_s
        frame_pct_change = heuristic_output.frame_pct_change
        motion_smoothness = heuristic_output.motion_smoothness
        subject_occupancy = heuristic_output.subject_occupancy
        
        # Rule 1: Check for static shot
        if avg_motion < self.config.static_threshold:
            return MotionType.STATIC
        
        # Rule 2: Check for handheld (low smoothness)
        if motion_smoothness < self.config.handheld_smoothness_threshold:
            return MotionType.HANDHELD
        
        # Rule 3: Check for dolly movement (significant size change)
        if frame_pct_change > self.config.dolly_threshold:
            # Determine direction based on whether subject is getting larger or smaller
            # If occupancy is increasing over time, it's dolly_in
            # For now, use frame_pct_change magnitude as a proxy
            if frame_pct_change > self.config.significant_change_threshold:
                # Significant change - likely dolly
                # Use subject occupancy to guess direction
                # Higher occupancy at end suggests dolly_in
                if subject_occupancy > 0.3:
                    return MotionType.DOLLY_IN
                else:
                    return MotionType.DOLLY_OUT
        
        # Rule 4 & 5: Check direction for pan/tilt
        if primary_direction_deg is not None:
            # Normalize direction to 0-360
            direction = primary_direction_deg % 360
            
            # Check for horizontal motion (pan)
            # Pan is around 0/180 degrees (left-right)
            if self._is_horizontal(direction):
                return MotionType.PAN
            
            # Check for vertical motion (tilt)
            # Tilt is around 90/270 degrees (up-down)
            if self._is_vertical(direction):
                return MotionType.TILT
        
        # Rule 6: Check for tracking shot
        # If there's consistent subject tracking with moderate motion
        if (subject_occupancy > 0.1 and 
            avg_motion > self.config.slow_motion_threshold and
            motion_smoothness > 0.6):
            return MotionType.TRACK
        
        # Default: If motion exists but doesn't fit other categories
        if avg_motion > self.config.slow_motion_threshold:
            return MotionType.HANDHELD
        
        return MotionType.STATIC
    
    def _is_horizontal(self, direction: float) -> bool:
        """Check if direction is primarily horizontal (pan)."""
        tolerance = self.config.horizontal_tolerance
        # Horizontal is around 0, 180, or 360 degrees
        return (
            direction < tolerance or
            direction > 360 - tolerance or
            abs(direction - 180) < tolerance
        )
    
    def _is_vertical(self, direction: float) -> bool:
        """Check if direction is primarily vertical (tilt)."""
        tolerance = self.config.vertical_tolerance
        # Vertical is around 90 or 270 degrees
        return (
            abs(direction - 90) < tolerance or
            abs(direction - 270) < tolerance
        )
    
    def infer_speed_profile(
        self,
        heuristic_output: HeuristicOutput,
        motion_type: MotionType
    ) -> SpeedProfile:
        """
        Infer the speed profile from heuristic indicators.
        
        Args:
            heuristic_output: Output from the Heuristic Analyzer
            motion_type: The inferred motion type
            
        Returns:
            Inferred SpeedProfile
        """
        motion_smoothness = heuristic_output.motion_smoothness
        frame_pct_change = heuristic_output.frame_pct_change
        
        # Static shots don't have a meaningful speed profile
        if motion_type == MotionType.STATIC:
            return SpeedProfile.LINEAR
        
        # Handheld typically has irregular speed
        if motion_type == MotionType.HANDHELD:
            return SpeedProfile.LINEAR
        
        # Smooth motion with gradual changes suggests ease curves
        if motion_smoothness > 0.8:
            # Very smooth - likely ease_in_out
            return SpeedProfile.EASE_IN_OUT
        elif motion_smoothness > 0.6:
            # Moderately smooth
            if frame_pct_change > 0.1:
                # Accelerating motion
                return SpeedProfile.EASE_IN
            else:
                return SpeedProfile.EASE_OUT
        
        # Default to linear for less smooth motion
        return SpeedProfile.LINEAR
    
    def infer_suggested_scale(
        self,
        subject_occupancy: float
    ) -> SuggestedScale:
        """
        Infer the suggested framing scale from subject occupancy.
        
        Args:
            subject_occupancy: Subject area ratio (0-1)
            
        Returns:
            Suggested framing scale
        """
        if subject_occupancy >= self.config.extreme_closeup_threshold:
            return SuggestedScale.EXTREME_CLOSEUP
        elif subject_occupancy >= self.config.closeup_threshold:
            return SuggestedScale.CLOSEUP
        elif subject_occupancy >= self.config.medium_threshold:
            return SuggestedScale.MEDIUM
        else:
            return SuggestedScale.WIDE
    
    def calculate_confidence(
        self,
        heuristic_output: HeuristicOutput,
        motion_type: MotionType
    ) -> float:
        """
        Calculate confidence score for the motion type inference.
        
        Higher confidence when:
        - Motion indicators are clear and consistent
        - Motion smoothness is high (clearer signal)
        - Subject tracking is reliable
        
        Args:
            heuristic_output: Output from the Heuristic Analyzer
            motion_type: The inferred motion type
            
        Returns:
            Confidence score in range [0, 1]
        """
        confidence = 0.5  # Base confidence
        
        # Boost confidence for clear motion patterns
        avg_motion = heuristic_output.avg_motion_px_per_s
        motion_smoothness = heuristic_output.motion_smoothness
        frame_pct_change = heuristic_output.frame_pct_change
        
        # Static shots are easy to identify
        if motion_type == MotionType.STATIC:
            if avg_motion < self.config.static_threshold:
                confidence += 0.3
        
        # Smooth motion is easier to classify
        if motion_smoothness > 0.7:
            confidence += 0.15
        elif motion_smoothness > 0.5:
            confidence += 0.1
        
        # Clear dolly movements
        if motion_type in (MotionType.DOLLY_IN, MotionType.DOLLY_OUT):
            if frame_pct_change > self.config.significant_change_threshold:
                confidence += 0.2
        
        # Penalize for ambiguous cases
        if motion_smoothness < 0.3:
            confidence -= 0.1
        
        # Clamp to valid range
        return max(0.0, min(1.0, confidence))


def infer_motion_type_from_heuristics(
    heuristic_output: HeuristicOutput,
    primary_direction_deg: Optional[float] = None,
    config: Optional[MotionRulesConfig] = None
) -> tuple[MotionType, SpeedProfile, SuggestedScale, float]:
    """
    Convenience function to infer all motion-related parameters.
    
    Args:
        heuristic_output: Output from the Heuristic Analyzer
        primary_direction_deg: Primary motion direction in degrees
        config: Optional configuration for inference rules
        
    Returns:
        Tuple of (motion_type, speed_profile, suggested_scale, confidence)
    """
    inferrer = MotionTypeInferrer(config)
    
    motion_type = inferrer.infer_motion_type(
        heuristic_output, 
        primary_direction_deg
    )
    
    speed_profile = inferrer.infer_speed_profile(
        heuristic_output,
        motion_type
    )
    
    suggested_scale = inferrer.infer_suggested_scale(
        heuristic_output.subject_occupancy
    )
    
    confidence = inferrer.calculate_confidence(
        heuristic_output,
        motion_type
    )
    
    return motion_type, speed_profile, suggested_scale, confidence
