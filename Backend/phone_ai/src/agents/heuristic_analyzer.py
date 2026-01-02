"""
Heuristic Analyzer Agent for the Video Shooting Assistant.

Calculates numerical indicators from extracted features:
- Average motion speed (px/s)
- Frame percentage change (subject area change ratio)
- Motion smoothness (based on acceleration variance)
- Subject occupancy (average subject area ratio)
- Beat alignment score (motion-beat synchronization)
"""
import math
from dataclasses import dataclass
from typing import Optional

from src.models.data_types import (
    BBox,
    FeatureOutput,
    HeuristicOutput,
    OpticalFlowData,
    SubjectTrackingData,
)


@dataclass
class HeuristicAnalyzerConfig:
    """Configuration for the Heuristic Analyzer Agent."""
    # Beat alignment settings
    beat_alignment_window_s: float = 0.1  # Time window for beat alignment (seconds)
    
    # Motion smoothness settings
    smoothness_normalization_factor: float = 100.0  # For normalizing acceleration variance


class HeuristicAnalyzerAgent:
    """
    启发式分析模块
    Calculates numerical indicators from extracted features.
    """
    
    def __init__(self, config: Optional[HeuristicAnalyzerConfig] = None):
        """
        Initialize the Heuristic Analyzer Agent.
        
        Args:
            config: Configuration options for heuristic analysis
        """
        self.config = config or HeuristicAnalyzerConfig()

    def calculate_avg_motion(
        self,
        optical_flow: OpticalFlowData,
        duration: float
    ) -> float:
        """
        Calculate average motion speed in pixels per second.
        
        The optical flow data already contains avg_speed_px_s computed
        from the Farneback algorithm. This method validates and returns it.
        
        Args:
            optical_flow: Optical flow data from Feature Extractor
            duration: Video duration in seconds (for validation)
            
        Returns:
            Average motion speed in pixels per second (non-negative)
        """
        # The Feature Extractor already computes avg_speed_px_s
        # We validate and return it
        avg_speed = optical_flow.avg_speed_px_s
        
        # Ensure non-negative
        return max(0.0, avg_speed)


    def calculate_frame_pct_change(
        self,
        bbox_sequence: list[BBox]
    ) -> float:
        """
        Calculate subject area change ratio (frame percentage change).
        
        Measures how much the subject's bounding box area changes over time,
        normalized to [0, 1] range. Higher values indicate more dramatic
        changes in subject size (e.g., dolly in/out movements).
        
        Args:
            bbox_sequence: Sequence of normalized bounding boxes
            
        Returns:
            Frame percentage change in range [0, 1]
        """
        if len(bbox_sequence) < 2:
            return 0.0
        
        # Calculate areas for all bounding boxes
        areas = [bbox.area() for bbox in bbox_sequence]
        
        if not areas:
            return 0.0
        
        # Calculate relative changes between consecutive frames
        changes = []
        for i in range(1, len(areas)):
            prev_area = areas[i - 1]
            curr_area = areas[i]
            
            # Avoid division by zero
            if prev_area > 0:
                # Relative change: |curr - prev| / prev
                relative_change = abs(curr_area - prev_area) / prev_area
                changes.append(relative_change)
            elif curr_area > 0:
                # If previous was 0 but current is not, consider it a full change
                changes.append(1.0)
        
        if not changes:
            return 0.0
        
        # Average relative change
        avg_change = sum(changes) / len(changes)
        
        # Normalize to [0, 1] range
        # Typical relative changes are small, so we scale up and clamp
        # A change of 0.5 (50% area change per frame) is considered maximum
        normalized = min(1.0, avg_change / 0.5)
        
        return max(0.0, min(1.0, normalized))


    def calculate_motion_smoothness(
        self,
        optical_flow: OpticalFlowData
    ) -> float:
        """
        Calculate motion smoothness based on acceleration variance.
        
        Smoothness is inversely related to the variance of motion changes
        (acceleration). Lower acceleration variance means smoother motion.
        Result is normalized to [0, 1] where higher values indicate smoother motion.
        
        Args:
            optical_flow: Optical flow data containing flow vectors
            
        Returns:
            Motion smoothness in range [0, 1] (higher = smoother)
        """
        flow_vectors = optical_flow.flow_vectors
        
        if len(flow_vectors) < 3:
            # Not enough data to calculate acceleration
            # Return moderate smoothness as default
            return 0.5
        
        # Calculate velocities (magnitude of flow vectors)
        velocities = []
        for vx, vy in flow_vectors:
            magnitude = math.sqrt(vx * vx + vy * vy)
            velocities.append(magnitude)
        
        if len(velocities) < 3:
            return 0.5
        
        # Calculate accelerations (change in velocity)
        accelerations = []
        for i in range(1, len(velocities)):
            accel = velocities[i] - velocities[i - 1]
            accelerations.append(accel)
        
        if not accelerations:
            return 0.5
        
        # Calculate variance of accelerations
        mean_accel = sum(accelerations) / len(accelerations)
        variance = sum((a - mean_accel) ** 2 for a in accelerations) / len(accelerations)
        
        # Normalize variance to smoothness score
        # Higher variance = lower smoothness
        # Use exponential decay for normalization
        normalization_factor = self.config.smoothness_normalization_factor
        smoothness = math.exp(-variance / normalization_factor)
        
        return max(0.0, min(1.0, smoothness))


    def calculate_subject_occupancy(
        self,
        bbox_sequence: list[BBox]
    ) -> float:
        """
        Calculate average subject area ratio (occupancy).
        
        Measures what fraction of the frame the subject occupies on average.
        Since bounding boxes are normalized to [0, 1], the area directly
        represents the fraction of the frame.
        
        Args:
            bbox_sequence: Sequence of normalized bounding boxes
            
        Returns:
            Subject occupancy in range [0, 1]
        """
        if not bbox_sequence:
            return 0.0
        
        # Calculate areas for all bounding boxes
        areas = [bbox.area() for bbox in bbox_sequence]
        
        if not areas:
            return 0.0
        
        # Average area across all frames
        avg_occupancy = sum(areas) / len(areas)
        
        # Ensure result is in [0, 1] range
        return max(0.0, min(1.0, avg_occupancy))


    def calculate_beat_alignment(
        self,
        motion_timestamps: list[float],
        beat_timestamps: list[float]
    ) -> float:
        """
        Calculate beat alignment score (motion-beat synchronization).
        
        Measures how well motion events align with audio beats.
        For each motion event, finds the closest beat and calculates
        the time difference. Lower differences indicate better alignment.
        
        Args:
            motion_timestamps: Timestamps of significant motion events (seconds)
            beat_timestamps: Timestamps of audio beats (seconds)
            
        Returns:
            Beat alignment score in range [0, 1] (higher = better alignment)
        """
        if not motion_timestamps or not beat_timestamps:
            # No data to compare, return neutral score
            return 0.5
        
        window = self.config.beat_alignment_window_s
        alignment_scores = []
        
        for motion_time in motion_timestamps:
            # Find the closest beat to this motion event
            min_distance = float('inf')
            
            for beat_time in beat_timestamps:
                distance = abs(motion_time - beat_time)
                if distance < min_distance:
                    min_distance = distance
            
            # Convert distance to alignment score
            # Perfect alignment (distance = 0) -> score = 1
            # Distance >= window -> score = 0
            if min_distance <= window:
                score = 1.0 - (min_distance / window)
            else:
                score = 0.0
            
            alignment_scores.append(score)
        
        if not alignment_scores:
            return 0.5
        
        # Average alignment score
        avg_alignment = sum(alignment_scores) / len(alignment_scores)
        
        return max(0.0, min(1.0, avg_alignment))

    def _extract_motion_timestamps(
        self,
        optical_flow: OpticalFlowData,
        bbox_sequence: list[BBox],
        timestamps: list[float],
        threshold_factor: float = 1.5
    ) -> list[float]:
        """
        Extract timestamps of significant motion events.
        
        Identifies frames where motion magnitude exceeds a threshold
        based on the average motion.
        
        Args:
            optical_flow: Optical flow data
            bbox_sequence: Sequence of bounding boxes
            timestamps: Timestamps for each frame
            threshold_factor: Multiplier for average to determine threshold
            
        Returns:
            List of timestamps where significant motion occurs
        """
        motion_timestamps = []
        
        # Use flow vectors to detect motion peaks
        flow_vectors = optical_flow.flow_vectors
        
        if len(flow_vectors) < 2:
            return motion_timestamps
        
        # Calculate magnitudes
        magnitudes = [math.sqrt(vx*vx + vy*vy) for vx, vy in flow_vectors]
        
        if not magnitudes:
            return motion_timestamps
        
        avg_magnitude = sum(magnitudes) / len(magnitudes)
        threshold = avg_magnitude * threshold_factor
        
        # Find peaks above threshold
        # Map flow vector indices to timestamps
        if timestamps and len(timestamps) > 0:
            # Sample timestamps to match flow vectors
            step = max(1, len(timestamps) // len(magnitudes))
            
            for i, mag in enumerate(magnitudes):
                if mag > threshold:
                    # Map to timestamp
                    ts_idx = min(i * step, len(timestamps) - 1)
                    motion_timestamps.append(timestamps[ts_idx])
        
        return motion_timestamps


    async def process(
        self,
        feature_output: FeatureOutput,
        time_range: tuple[float, float],
        config: Optional[HeuristicAnalyzerConfig] = None
    ) -> HeuristicOutput:
        """
        Calculate all numerical indicators from feature data.
        
        This is the main entry point for the Heuristic Analyzer Agent.
        
        Args:
            feature_output: Output from the Feature Extractor Agent
            time_range: Analysis time range (start_s, end_s)
            config: Optional config override
            
        Returns:
            HeuristicOutput with all calculated indicators
        """
        if config is not None:
            self.config = config
        
        video_id = feature_output.video_id
        optical_flow = feature_output.optical_flow
        subject_tracking = feature_output.subject_tracking
        audio_beats = feature_output.audio_beats or []
        
        # Calculate duration from time range
        duration = time_range[1] - time_range[0]
        
        # Calculate average motion speed
        avg_motion_px_per_s = self.calculate_avg_motion(optical_flow, duration)
        
        # Calculate frame percentage change
        frame_pct_change = self.calculate_frame_pct_change(
            subject_tracking.bbox_sequence
        )
        
        # Calculate motion smoothness
        motion_smoothness = self.calculate_motion_smoothness(optical_flow)
        
        # Calculate subject occupancy
        subject_occupancy = self.calculate_subject_occupancy(
            subject_tracking.bbox_sequence
        )
        
        # Extract motion timestamps and calculate beat alignment
        motion_timestamps = self._extract_motion_timestamps(
            optical_flow,
            subject_tracking.bbox_sequence,
            subject_tracking.timestamps
        )
        beat_alignment_score = self.calculate_beat_alignment(
            motion_timestamps,
            audio_beats
        )
        
        # Create and validate output
        output = HeuristicOutput(
            video_id=video_id,
            time_range=time_range,
            avg_motion_px_per_s=avg_motion_px_per_s,
            frame_pct_change=frame_pct_change,
            motion_smoothness=motion_smoothness,
            subject_occupancy=subject_occupancy,
            beat_alignment_score=beat_alignment_score
        )
        
        # Validate output structure
        if not output.is_valid():
            raise ValueError(
                f"Invalid HeuristicOutput: indicators out of valid ranges. "
                f"avg_motion={avg_motion_px_per_s}, "
                f"frame_pct_change={frame_pct_change}, "
                f"motion_smoothness={motion_smoothness}, "
                f"subject_occupancy={subject_occupancy}, "
                f"beat_alignment={beat_alignment_score}"
            )
        
        return output

    def process_sync(
        self,
        feature_output: FeatureOutput,
        time_range: tuple[float, float],
        config: Optional[HeuristicAnalyzerConfig] = None
    ) -> HeuristicOutput:
        """
        Synchronous version of process() for non-async contexts.
        
        Args:
            feature_output: Output from the Feature Extractor Agent
            time_range: Analysis time range (start_s, end_s)
            config: Optional config override
            
        Returns:
            HeuristicOutput with all calculated indicators
        """
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.process(feature_output, time_range, config)
        )
