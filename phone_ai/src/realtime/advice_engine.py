"""
Advice Engine Module

建议引擎，根据分析指标生成分级建议。
Generates prioritized advice based on smoothed indicators.

Requirements: 2.1-2.4, 3.1-3.3, 4.1-4.6, 5.1-5.3, 6.1-6.3, 7.1-7.2, 8.1-8.5, 13.1-13.5
"""
import time
from dataclasses import dataclass
from typing import Optional

from src.models.data_types import BBox, HeuristicOutput
from src.models.enums import MotionType

from .types import (
    AdvicePayload,
    AdvicePriority,
    AdviceCategory,
    RealtimeAnalysisResult,
)
from .templates import (
    STABILITY_CRITICAL,
    STABILITY_WARNING,
    STABILITY_POSITIVE,
    SPEED_TOO_FAST,
    SPEED_UNEVEN,
    SPEED_PERFECT,
    SUBJECT_OFF_CENTER,
    SUBJECT_TOO_LARGE,
    SUBJECT_TOO_SMALL,
    SUBJECT_LOST,
    DIRECTION_HINT,
    DIRECTION_NAMES,
    AVOID_DIRECTIONS,
    BEAT_UPCOMING,
    BEAT_NOW,
    MOTION_BLUR,
    TELEPHOTO_SHAKE,
    STABILIZATION_SUGGESTION,
    LOW_CONFIDENCE_STATUS,
)
from .state_machine import MotionStateMachine
from .hysteresis import HysteresisController, HysteresisConfig
from .smoothing import SmoothingFilter, IndicatorValues


@dataclass
class AdviceEngineConfig:
    """Configuration for the advice engine."""
    # Stability thresholds (Requirements 2.1-2.4)
    stability_critical_threshold: float = 0.4
    stability_warning_threshold: float = 0.7
    
    # Speed thresholds (Requirements 3.1-3.3)
    speed_warning_threshold: float = 20.0  # px/frame
    speed_cv_warning_threshold: float = 0.5  # coefficient of variation
    speed_optimal_min: float = 5.0  # px/frame
    speed_optimal_max: float = 15.0  # px/frame
    
    # Composition thresholds (Requirements 4.1-4.4)
    subject_deviation_threshold: float = 0.2  # 20% from center/thirds
    subject_occupancy_max: float = 0.8
    subject_occupancy_min: float = 0.1
    
    # Beat timing (Requirements 5.1-5.2)
    beat_upcoming_window_s: float = 0.5
    beat_now_window_s: float = 0.1
    
    # Equipment thresholds (Requirements 6.1-6.3)
    telephoto_focal_length_mm: float = 50.0
    telephoto_smoothness_threshold: float = 0.5
    
    # Confidence threshold (Requirement 13.5)
    min_confidence: float = 0.5


class AdviceEngine:
    """
    建议引擎
    Generates prioritized advice based on smoothed indicators.
    
    The engine:
    1. Applies smoothing filter to raw indicators
    2. Uses hysteresis to prevent rapid toggling
    3. Checks motion type for suppression rules
    4. Generates prioritized advice based on thresholds
    5. Applies category cooldown to avoid repetitive advice
    
    Requirements:
    - 2.1-2.4: Stability advice generation
    - 3.1-3.3: Speed advice generation
    - 4.1-4.6: Composition advice generation
    - 5.1-5.3: Beat advice generation
    - 6.1-6.3: Equipment advice generation
    - 7.1-7.2: Priority classification and haptic trigger
    - 8.1-8.5: Motion type suppression
    - 13.1-13.5: Filtering and noise reduction
    """
    
    def __init__(
        self,
        config: Optional[AdviceEngineConfig] = None,
        hysteresis_config: Optional[HysteresisConfig] = None
    ):
        """
        Initialize the advice engine.
        
        Args:
            config: Configuration for advice thresholds
            hysteresis_config: Configuration for hysteresis controller
        """
        self.config = config or AdviceEngineConfig()
        self.state_machine = MotionStateMachine()
        self._hysteresis = HysteresisController(hysteresis_config)
        self._smoothing_filter = SmoothingFilter()
        self._last_advice: dict[str, AdvicePayload] = {}
        self._subject_lost_since: Optional[float] = None
    
    def generate_advice(
        self,
        analysis_result: RealtimeAnalysisResult,
        beat_timestamps: Optional[list[float]] = None,
        current_time: float = 0.0,
        device_type: str = "consumer",
        focal_length_mm: Optional[float] = None,
        apply_smoothing: bool = True,
    ) -> list[AdvicePayload]:
        """
        Generate advice based on current analysis result.
        
        Args:
            analysis_result: Realtime analysis result with indicators
            beat_timestamps: Upcoming beat timestamps (optional)
            current_time: Current video timestamp in seconds
            device_type: "consumer" or "professional"
            focal_length_mm: Current focal length (optional)
            apply_smoothing: Whether to apply smoothing filter
            
        Returns:
            List of advice payloads to send to client
        """
        if current_time == 0.0:
            current_time = time.time()
        
        # Check confidence threshold (Requirement 13.5)
        if analysis_result.confidence < self.config.min_confidence:
            return [LOW_CONFIDENCE_STATUS]
        
        # Apply smoothing filter if enabled (Requirement 13.1)
        if apply_smoothing:
            indicators = IndicatorValues(
                motion_smoothness=analysis_result.motion_smoothness,
                avg_speed=analysis_result.avg_speed_px_frame,
                speed_variance=analysis_result.speed_variance,
                primary_direction_deg=analysis_result.primary_direction_deg,
                subject_occupancy=analysis_result.subject_occupancy,
                confidence=analysis_result.confidence,
            )
            smoothed = self._smoothing_filter.update(indicators)
            
            # Check if suppressed due to anomaly (Requirement 13.2)
            if self._smoothing_filter.is_suppressed():
                return []
            
            # Use smoothed values
            motion_smoothness = smoothed.motion_smoothness
            avg_speed = smoothed.avg_speed
            speed_variance = smoothed.speed_variance
            primary_direction_deg = smoothed.primary_direction_deg
            subject_occupancy = smoothed.subject_occupancy
        else:
            motion_smoothness = analysis_result.motion_smoothness
            avg_speed = analysis_result.avg_speed_px_frame
            speed_variance = analysis_result.speed_variance
            primary_direction_deg = analysis_result.primary_direction_deg
            subject_occupancy = analysis_result.subject_occupancy
        
        # Update motion state machine (Requirements 8.4, 8.5)
        heuristic_output = HeuristicOutput(
            video_id="realtime",
            time_range=(current_time, current_time + 0.5),
            avg_motion_px_per_s=avg_speed * 30,  # Convert to px/s assuming 30fps
            frame_pct_change=0.0,  # Not used for motion type inference
            motion_smoothness=motion_smoothness,
            subject_occupancy=subject_occupancy,
            beat_alignment_score=0.0,
        )
        self.state_machine.update(heuristic_output, primary_direction_deg)
        
        # Generate advice from each category
        advice_list: list[AdvicePayload] = []
        
        # Stability advice (Requirements 2.1-2.4)
        stability_advice = self._generate_stability_advice(
            motion_smoothness, device_type, current_time
        )
        if stability_advice:
            advice_list.append(stability_advice)
        
        # Speed advice (Requirements 3.1-3.3)
        speed_advice = self._generate_speed_advice(
            avg_speed, speed_variance, current_time
        )
        if speed_advice:
            advice_list.append(speed_advice)
        
        # Composition advice (Requirements 4.1-4.6)
        composition_advice = self._generate_composition_advice(
            analysis_result.subject_bbox,
            subject_occupancy,
            primary_direction_deg,
            analysis_result.subject_lost,
            current_time,
        )
        advice_list.extend(composition_advice)
        
        # Beat advice (Requirements 5.1-5.3)
        if beat_timestamps:
            beat_advice = self._generate_beat_advice(
                beat_timestamps, current_time
            )
            if beat_advice:
                advice_list.append(beat_advice)
        
        # Equipment advice (Requirements 6.1-6.3)
        equipment_advice = self._generate_equipment_advice(
            motion_smoothness, focal_length_mm, current_time
        )
        if equipment_advice:
            advice_list.append(equipment_advice)
        
        return advice_list

    
    def _generate_stability_advice(
        self,
        motion_smoothness: float,
        device_type: str,
        current_time: float,
    ) -> Optional[AdvicePayload]:
        """
        Generate stability-related advice.
        
        Requirements:
        - 2.1: motion_smoothness < 0.4 → critical advice
        - 2.2: professional device → advanced message
        - 2.3: 0.4 <= motion_smoothness <= 0.7 → warning advice
        - 2.4: motion_smoothness > 0.7 → positive advice
        
        Args:
            motion_smoothness: Smoothed motion smoothness value (0-1)
            device_type: "consumer" or "professional"
            current_time: Current timestamp for cooldown tracking
            
        Returns:
            AdvicePayload or None if suppressed
        """
        category = AdviceCategory.STABILITY.value
        
        # Check if on cooldown
        if self._hysteresis.is_on_cooldown(category, current_time):
            return None
        
        # Check motion type suppression (not typically suppressed for stability)
        if self.state_machine.should_suppress(category):
            return None
        
        # Use hysteresis to determine state
        state = self._hysteresis.check_threshold_multi_level(
            category=category,
            value=motion_smoothness,
            critical_enter=self.config.stability_critical_threshold - 0.05,  # 0.35
            critical_exit=self.config.stability_critical_threshold + 0.05,   # 0.45
            warning_enter=self.config.stability_warning_threshold - 0.05,    # 0.65
            warning_exit=self.config.stability_warning_threshold + 0.05,     # 0.75
            lower_is_worse=True,
        )
        
        # Check consistency for non-critical advice (Requirement 13.3)
        if state != "critical":
            should_trigger = state == "warning"
            if not self._hysteresis.is_consistent(category, should_trigger):
                # For positive feedback, we can be more lenient
                if state != "normal" or motion_smoothness <= self.config.stability_warning_threshold:
                    return None
        
        # Generate advice based on state
        if state == "critical":
            # Critical stability issue (Requirement 2.1)
            advice = AdvicePayload(
                priority=AdvicePriority.CRITICAL,
                category=AdviceCategory.STABILITY,
                message=STABILITY_CRITICAL.message,
                advanced_message=STABILITY_CRITICAL.advanced_message if device_type == "professional" else None,
                trigger_haptic=True,
                suppress_duration_s=5.0,
            )
            self._hysteresis.record_advice(category, current_time)
            return advice
        
        elif state == "warning":
            # Warning level stability (Requirement 2.3)
            advice = AdvicePayload(
                priority=AdvicePriority.WARNING,
                category=AdviceCategory.STABILITY,
                message=STABILITY_WARNING.message,
                trigger_haptic=False,
                suppress_duration_s=3.0,
            )
            self._hysteresis.record_advice(category, current_time)
            return advice
        
        else:  # normal state with good stability
            # Positive feedback (Requirement 2.4)
            if motion_smoothness > self.config.stability_warning_threshold:
                # Only give positive feedback occasionally
                if not self._hysteresis.is_on_cooldown(f"{category}_positive", current_time):
                    advice = AdvicePayload(
                        priority=AdvicePriority.POSITIVE,
                        category=AdviceCategory.STABILITY,
                        message=STABILITY_POSITIVE.message,
                        trigger_haptic=False,
                        suppress_duration_s=3.0,
                    )
                    self._hysteresis.record_advice(f"{category}_positive", current_time)
                    return advice
        
        return None

    
    def _generate_speed_advice(
        self,
        avg_speed: float,
        speed_variance: float,
        current_time: float,
    ) -> Optional[AdvicePayload]:
        """
        Generate speed-related advice.
        
        Requirements:
        - 3.1: avg_speed > 20 px/frame → warning (too fast)
        - 3.2: coefficient of variation > 0.5 → warning (uneven)
        - 3.3: 5-15 px/frame with low variance → positive
        
        Args:
            avg_speed: Average speed in px/frame
            speed_variance: Speed variance
            current_time: Current timestamp for cooldown tracking
            
        Returns:
            AdvicePayload or None if suppressed
        """
        category = AdviceCategory.SPEED.value
        
        # Check if on cooldown
        if self._hysteresis.is_on_cooldown(category, current_time):
            return None
        
        # Check motion type suppression
        if self.state_machine.should_suppress(category):
            return None
        
        # Calculate coefficient of variation
        cv = (speed_variance ** 0.5) / avg_speed if avg_speed > 0 else 0
        
        # Check for too fast (Requirement 3.1)
        is_too_fast = self._hysteresis.check_threshold(
            category=f"{category}_fast",
            value=avg_speed,
            enter_threshold=self.config.speed_warning_threshold + 2,  # 22
            exit_threshold=self.config.speed_warning_threshold - 2,   # 18
            lower_is_worse=False,  # Higher speed is worse
        )
        
        if is_too_fast:
            if self._hysteresis.is_consistent(f"{category}_fast", True):
                advice = AdvicePayload(
                    priority=AdvicePriority.WARNING,
                    category=AdviceCategory.SPEED,
                    message=SPEED_TOO_FAST.message,
                    trigger_haptic=False,
                    suppress_duration_s=3.0,
                )
                self._hysteresis.record_advice(category, current_time)
                return advice
            return None
        
        # Check for uneven speed (Requirement 3.2)
        is_uneven = cv > self.config.speed_cv_warning_threshold
        
        if is_uneven:
            if self._hysteresis.is_consistent(f"{category}_uneven", True):
                advice = AdvicePayload(
                    priority=AdvicePriority.WARNING,
                    category=AdviceCategory.SPEED,
                    message=SPEED_UNEVEN.message,
                    trigger_haptic=False,
                    suppress_duration_s=3.0,
                )
                self._hysteresis.record_advice(category, current_time)
                return advice
            return None
        
        # Check for optimal speed (Requirement 3.3)
        is_optimal = (
            self.config.speed_optimal_min <= avg_speed <= self.config.speed_optimal_max
            and cv < self.config.speed_cv_warning_threshold
        )
        
        if is_optimal:
            if not self._hysteresis.is_on_cooldown(f"{category}_positive", current_time):
                advice = AdvicePayload(
                    priority=AdvicePriority.POSITIVE,
                    category=AdviceCategory.SPEED,
                    message=SPEED_PERFECT.message,
                    trigger_haptic=False,
                    suppress_duration_s=3.0,
                )
                self._hysteresis.record_advice(f"{category}_positive", current_time)
                return advice
        
        return None

    
    def _generate_composition_advice(
        self,
        subject_bbox: Optional[BBox],
        subject_occupancy: float,
        primary_direction_deg: float,
        subject_lost: bool,
        current_time: float,
    ) -> list[AdvicePayload]:
        """
        Generate composition-related advice.
        
        Requirements:
        - 4.1: Direction hint for consistent motion
        - 4.2: Subject deviation > 20% from center/thirds → warning
        - 4.3: Occupancy > 0.8 → too large warning
        - 4.4: Occupancy < 0.1 → too small warning
        - 4.5: Subject lost → enter Subject_Lost state
        - 4.6: Subject reappears → exit Subject_Lost state
        
        Args:
            subject_bbox: Subject bounding box (normalized)
            subject_occupancy: Subject occupancy ratio (0-1)
            primary_direction_deg: Primary motion direction in degrees
            subject_lost: Whether subject is currently lost
            current_time: Current timestamp for cooldown tracking
            
        Returns:
            List of AdvicePayload (may be empty)
        """
        advice_list: list[AdvicePayload] = []
        category = AdviceCategory.COMPOSITION.value
        
        # Handle subject lost state (Requirements 4.5, 4.6)
        if subject_lost:
            if self._subject_lost_since is None:
                # Just entered Subject_Lost state
                self._subject_lost_since = current_time
                
                if not self._hysteresis.is_on_cooldown(f"{category}_lost", current_time):
                    advice = AdvicePayload(
                        priority=AdvicePriority.WARNING,
                        category=AdviceCategory.COMPOSITION,
                        message=SUBJECT_LOST.message,
                        trigger_haptic=False,
                        suppress_duration_s=5.0,
                    )
                    self._hysteresis.record_advice(f"{category}_lost", current_time)
                    advice_list.append(advice)
            return advice_list
        else:
            # Subject found - exit Subject_Lost state if we were in it
            self._subject_lost_since = None
        
        # Generate direction hint (Requirement 4.1)
        direction_advice = self._generate_direction_hint(
            primary_direction_deg, current_time
        )
        if direction_advice:
            advice_list.append(direction_advice)
        
        # Check subject position deviation (Requirement 4.2)
        if subject_bbox and not self.state_machine.should_suppress("horizontal_drift") and not self.state_machine.should_suppress("vertical_drift"):
            position_advice = self._check_subject_position(
                subject_bbox, current_time
            )
            if position_advice:
                advice_list.append(position_advice)
        
        # Check occupancy thresholds (Requirements 4.3, 4.4)
        if not self.state_machine.should_suppress("subject_size_change"):
            occupancy_advice = self._check_occupancy(
                subject_occupancy, current_time
            )
            if occupancy_advice:
                advice_list.append(occupancy_advice)
        
        return advice_list
    
    def _generate_direction_hint(
        self,
        primary_direction_deg: float,
        current_time: float,
    ) -> Optional[AdvicePayload]:
        """
        Generate direction hint for consistent motion.
        
        Requirement 4.1: Indicate direction and advise to maintain it.
        
        Args:
            primary_direction_deg: Primary motion direction (0-360)
            current_time: Current timestamp
            
        Returns:
            AdvicePayload or None
        """
        category = f"{AdviceCategory.COMPOSITION.value}_direction"
        
        if self._hysteresis.is_on_cooldown(category, current_time):
            return None
        
        # Determine direction name based on angle
        direction_key = self._angle_to_direction_key(primary_direction_deg)
        if direction_key is None:
            return None
        
        direction_name = DIRECTION_NAMES.get(direction_key, direction_key)
        avoid_direction = AVOID_DIRECTIONS.get(direction_key, "其他方向")
        
        # Only generate if we have a clear direction
        motion_type = self.state_machine.get_current_state()
        if motion_type in (MotionType.STATIC, MotionType.HANDHELD):
            return None
        
        advice = AdvicePayload(
            priority=AdvicePriority.INFO,
            category=AdviceCategory.COMPOSITION,
            message=DIRECTION_HINT.message.format(
                direction=direction_name,
                avoid=avoid_direction,
            ),
            trigger_haptic=False,
            suppress_duration_s=3.0,
        )
        self._hysteresis.record_advice(category, current_time)
        return advice
    
    def _angle_to_direction_key(self, angle_deg: float) -> Optional[str]:
        """
        Convert angle to direction key.
        
        Args:
            angle_deg: Angle in degrees (0-360)
            
        Returns:
            Direction key or None if ambiguous
        """
        # Normalize angle to 0-360
        angle = angle_deg % 360
        
        # Define direction ranges (with some tolerance)
        if 45 <= angle < 135:
            return "down"  # Moving down
        elif 135 <= angle < 225:
            return "left"  # Moving left
        elif 225 <= angle < 315:
            return "up"  # Moving up
        elif angle >= 315 or angle < 45:
            return "right"  # Moving right
        
        return None
    
    def _check_subject_position(
        self,
        subject_bbox: BBox,
        current_time: float,
    ) -> Optional[AdvicePayload]:
        """
        Check if subject deviates from center or rule-of-thirds.
        
        Requirement 4.2: Deviation > 20% → warning with direction hint.
        
        Args:
            subject_bbox: Subject bounding box (normalized 0-1)
            current_time: Current timestamp
            
        Returns:
            AdvicePayload or None
        """
        category = f"{AdviceCategory.COMPOSITION.value}_position"
        
        if self._hysteresis.is_on_cooldown(category, current_time):
            return None
        
        # Calculate subject center
        center_x = subject_bbox.x + subject_bbox.w / 2
        center_y = subject_bbox.y + subject_bbox.h / 2
        
        # Frame center is at (0.5, 0.5)
        # Rule of thirds lines are at 1/3 and 2/3
        thirds_x = [1/3, 2/3]
        thirds_y = [1/3, 2/3]
        
        # Calculate minimum distance to center or thirds
        dist_to_center = ((center_x - 0.5) ** 2 + (center_y - 0.5) ** 2) ** 0.5
        
        # Distance to nearest thirds intersection
        min_thirds_dist = float('inf')
        for tx in thirds_x:
            for ty in thirds_y:
                dist = ((center_x - tx) ** 2 + (center_y - ty) ** 2) ** 0.5
                min_thirds_dist = min(min_thirds_dist, dist)
        
        # Use the smaller of center or thirds distance
        min_dist = min(dist_to_center, min_thirds_dist)
        
        # Check if deviation exceeds threshold
        if min_dist > self.config.subject_deviation_threshold:
            # Determine direction to adjust
            if center_x < 0.4:
                direction = "右"
            elif center_x > 0.6:
                direction = "左"
            elif center_y < 0.4:
                direction = "下"
            elif center_y > 0.6:
                direction = "上"
            else:
                return None  # Close enough
            
            if self._hysteresis.is_consistent(category, True):
                advice = AdvicePayload(
                    priority=AdvicePriority.WARNING,
                    category=AdviceCategory.COMPOSITION,
                    message=SUBJECT_OFF_CENTER.message.format(direction=direction),
                    trigger_haptic=False,
                    suppress_duration_s=3.0,
                )
                self._hysteresis.record_advice(category, current_time)
                return advice
        
        return None
    
    def _check_occupancy(
        self,
        subject_occupancy: float,
        current_time: float,
    ) -> Optional[AdvicePayload]:
        """
        Check subject occupancy thresholds.
        
        Requirements:
        - 4.3: Occupancy > 0.8 → too large
        - 4.4: Occupancy < 0.1 → too small
        
        Args:
            subject_occupancy: Subject occupancy ratio (0-1)
            current_time: Current timestamp
            
        Returns:
            AdvicePayload or None
        """
        category = f"{AdviceCategory.COMPOSITION.value}_occupancy"
        
        if self._hysteresis.is_on_cooldown(category, current_time):
            return None
        
        if subject_occupancy > self.config.subject_occupancy_max:
            if self._hysteresis.is_consistent(f"{category}_large", True):
                advice = AdvicePayload(
                    priority=AdvicePriority.WARNING,
                    category=AdviceCategory.COMPOSITION,
                    message=SUBJECT_TOO_LARGE.message,
                    trigger_haptic=False,
                    suppress_duration_s=3.0,
                )
                self._hysteresis.record_advice(category, current_time)
                return advice
        
        elif subject_occupancy < self.config.subject_occupancy_min:
            if self._hysteresis.is_consistent(f"{category}_small", True):
                advice = AdvicePayload(
                    priority=AdvicePriority.WARNING,
                    category=AdviceCategory.COMPOSITION,
                    message=SUBJECT_TOO_SMALL.message,
                    trigger_haptic=False,
                    suppress_duration_s=3.0,
                )
                self._hysteresis.record_advice(category, current_time)
                return advice
        
        return None

    
    def _generate_beat_advice(
        self,
        beat_timestamps: list[float],
        current_time: float,
    ) -> Optional[AdvicePayload]:
        """
        Generate beat synchronization advice.
        
        Requirements:
        - 5.1: Beat within 0.5s → upcoming beat advice
        - 5.2: Beat at current time → beat now advice
        - 5.3: Handle missing audio gracefully (caller handles this)
        
        Args:
            beat_timestamps: List of upcoming beat timestamps
            current_time: Current video timestamp
            
        Returns:
            AdvicePayload or None
        """
        category = AdviceCategory.BEAT.value
        
        if self._hysteresis.is_on_cooldown(category, current_time):
            return None
        
        if not beat_timestamps:
            return None
        
        # Find the nearest upcoming beat
        upcoming_beats = [t for t in beat_timestamps if t >= current_time]
        if not upcoming_beats:
            return None
        
        nearest_beat = min(upcoming_beats)
        time_to_beat = nearest_beat - current_time
        
        # Check if beat is happening now (Requirement 5.2)
        if time_to_beat <= self.config.beat_now_window_s:
            advice = AdvicePayload(
                priority=AdvicePriority.INFO,
                category=AdviceCategory.BEAT,
                message=BEAT_NOW.message,
                trigger_haptic=False,
                suppress_duration_s=2.0,
            )
            self._hysteresis.record_advice(category, current_time)
            return advice
        
        # Check if beat is upcoming (Requirement 5.1)
        if time_to_beat <= self.config.beat_upcoming_window_s:
            advice = AdvicePayload(
                priority=AdvicePriority.INFO,
                category=AdviceCategory.BEAT,
                message=BEAT_UPCOMING.message,
                trigger_haptic=False,
                suppress_duration_s=2.0,
            )
            self._hysteresis.record_advice(category, current_time)
            return advice
        
        return None

    
    def _generate_equipment_advice(
        self,
        motion_smoothness: float,
        focal_length_mm: Optional[float],
        current_time: float,
    ) -> Optional[AdvicePayload]:
        """
        Generate equipment and parameter suggestions.
        
        Requirements:
        - 6.1: Motion blur detected → suggest higher shutter speed
        - 6.2: Telephoto + low smoothness → suggest wide angle
        - 6.3: Low smoothness → suggest stabilization equipment
        
        Args:
            motion_smoothness: Smoothed motion smoothness value
            focal_length_mm: Current focal length (optional)
            current_time: Current timestamp
            
        Returns:
            AdvicePayload or None
        """
        category = AdviceCategory.EQUIPMENT.value
        
        if self._hysteresis.is_on_cooldown(category, current_time):
            return None
        
        # Check telephoto + low smoothness (Requirement 6.2)
        if focal_length_mm is not None:
            if (focal_length_mm > self.config.telephoto_focal_length_mm and
                motion_smoothness < self.config.telephoto_smoothness_threshold):
                if self._hysteresis.is_consistent(f"{category}_telephoto", True):
                    advice = AdvicePayload(
                        priority=AdvicePriority.WARNING,
                        category=AdviceCategory.EQUIPMENT,
                        message=TELEPHOTO_SHAKE.message,
                        trigger_haptic=False,
                        suppress_duration_s=5.0,
                    )
                    self._hysteresis.record_advice(category, current_time)
                    return advice
        
        # Check for general low smoothness → suggest stabilization (Requirement 6.3)
        if motion_smoothness < self.config.stability_critical_threshold:
            if self._hysteresis.is_consistent(f"{category}_stabilization", True):
                advice = AdvicePayload(
                    priority=AdvicePriority.INFO,
                    category=AdviceCategory.EQUIPMENT,
                    message=STABILIZATION_SUGGESTION.message,
                    trigger_haptic=False,
                    suppress_duration_s=5.0,
                )
                self._hysteresis.record_advice(category, current_time)
                return advice
        
        return None

    
    def reset(self) -> None:
        """
        Reset the advice engine state.
        
        Clears all internal state including:
        - Smoothing filter
        - Hysteresis controller
        - Motion state machine
        - Subject lost tracking
        """
        self._smoothing_filter.reset()
        self._hysteresis.reset()
        self.state_machine.reset()
        self._subject_lost_since = None
        self._last_advice.clear()
    
    def get_motion_type(self) -> MotionType:
        """
        Get the current detected motion type.
        
        Returns:
            Current MotionType from state machine
        """
        return self.state_machine.get_current_state()
    
    def get_suppression_rules(self) -> set[str]:
        """
        Get current suppression rules based on motion type.
        
        Returns:
            Set of advice categories being suppressed
        """
        return self.state_machine.get_suppression_rules()
    
    def is_subject_lost(self) -> bool:
        """
        Check if subject is currently in lost state.
        
        Returns:
            True if subject has been lost
        """
        return self._subject_lost_since is not None
    
    def get_subject_lost_duration(self, current_time: float) -> Optional[float]:
        """
        Get how long the subject has been lost.
        
        Args:
            current_time: Current timestamp
            
        Returns:
            Duration in seconds, or None if subject is not lost
        """
        if self._subject_lost_since is None:
            return None
        return current_time - self._subject_lost_since
    
    def generate_advice_from_indicators(
        self,
        motion_smoothness: float,
        avg_speed: float,
        speed_variance: float,
        primary_direction_deg: float,
        subject_bbox: Optional[BBox] = None,
        subject_occupancy: float = 0.0,
        subject_lost: bool = False,
        confidence: float = 0.5,
        beat_timestamps: Optional[list[float]] = None,
        current_time: float = 0.0,
        device_type: str = "consumer",
        focal_length_mm: Optional[float] = None,
        apply_smoothing: bool = True,
    ) -> list[AdvicePayload]:
        """
        Convenience method to generate advice from raw indicator values.
        
        This is a simpler interface that doesn't require creating a
        RealtimeAnalysisResult object.
        
        Args:
            motion_smoothness: Motion smoothness (0-1)
            avg_speed: Average speed in px/frame
            speed_variance: Speed variance
            primary_direction_deg: Primary motion direction (0-360)
            subject_bbox: Subject bounding box (optional)
            subject_occupancy: Subject occupancy ratio (0-1)
            subject_lost: Whether subject is lost
            confidence: Analysis confidence (0-1)
            beat_timestamps: Upcoming beat timestamps
            current_time: Current timestamp
            device_type: "consumer" or "professional"
            focal_length_mm: Current focal length
            apply_smoothing: Whether to apply smoothing
            
        Returns:
            List of AdvicePayload
        """
        result = RealtimeAnalysisResult(
            avg_speed_px_frame=avg_speed,
            speed_variance=speed_variance,
            motion_smoothness=motion_smoothness,
            primary_direction_deg=primary_direction_deg,
            subject_bbox=subject_bbox,
            subject_occupancy=subject_occupancy,
            subject_lost=subject_lost,
            confidence=confidence,
        )
        
        return self.generate_advice(
            analysis_result=result,
            beat_timestamps=beat_timestamps,
            current_time=current_time,
            device_type=device_type,
            focal_length_mm=focal_length_mm,
            apply_smoothing=apply_smoothing,
        )
