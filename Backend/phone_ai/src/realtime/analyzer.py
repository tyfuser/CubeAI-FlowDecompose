"""
Realtime Analyzer Module

实时分析模块，负责低延迟采样和光流计算。
Performs low-latency optical flow and heuristic analysis on frame buffers.

Requirements: 1.1, 1.2, 1.3, 4.5, 4.6, 11.5, 11.6
"""
import base64
import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np

from src.models.data_types import BBox, OpticalFlowData
from src.realtime.types import RealtimeAnalysisResult
from src.realtime.smoothing import SmoothingFilter, IndicatorValues


@dataclass
class RealtimeAnalyzerConfig:
    """Configuration for realtime analysis."""
    sampling_interval_s: float = 0.5  # Sample every 0.5 seconds
    buffer_size: int = 8  # Number of frames per buffer (5-10 per requirements)
    buffer_overlap_s: float = 0.3  # Overlap with previous buffer
    target_resolution: tuple[int, int] = (320, 240)  # Low-res for speed
    use_sparse_flow: bool = False  # Switch to Lucas-Kanade when needed
    center_region_only: bool = False  # Analyze only center when constrained
    latency_threshold_ms: float = 500  # Switch to sparse flow above this
    jpeg_quality: int = 75  # JPEG compression quality
    
    # Optical flow parameters (Farneback)
    optical_flow_pyr_scale: float = 0.5
    optical_flow_levels: int = 3
    optical_flow_winsize: int = 15
    optical_flow_iterations: int = 3
    optical_flow_poly_n: int = 5
    optical_flow_poly_sigma: float = 1.2
    
    # Lucas-Kanade parameters (sparse flow for degraded mode)
    lk_max_corners: int = 100
    lk_quality_level: float = 0.3
    lk_min_distance: int = 7
    lk_block_size: int = 7
    lk_win_size: tuple[int, int] = (21, 21)
    
    # Subject tracking
    subject_lost_threshold_frames: int = 3  # Frames without subject to trigger lost state
    
    # Smoothness calculation
    smoothness_normalization_factor: float = 100.0


@dataclass
class FrameBuffer:
    """
    帧缓冲区
    Sliding window buffer for frame storage with overlap support.
    """
    frames: deque = field(default_factory=lambda: deque(maxlen=10))
    timestamps: deque = field(default_factory=lambda: deque(maxlen=10))
    
    def add_frame(self, frame: np.ndarray, timestamp: float) -> None:
        """Add a frame to the buffer."""
        self.frames.append(frame)
        self.timestamps.append(timestamp)
    
    def get_frames(self) -> list[np.ndarray]:
        """Get all frames in the buffer."""
        return list(self.frames)
    
    def get_timestamps(self) -> list[float]:
        """Get all timestamps in the buffer."""
        return list(self.timestamps)
    
    def size(self) -> int:
        """Get current buffer size."""
        return len(self.frames)
    
    def clear(self) -> None:
        """Clear the buffer."""
        self.frames.clear()
        self.timestamps.clear()


class RealtimeAnalyzer:
    """
    实时分析模块
    Performs low-latency optical flow and heuristic analysis on frame buffers.
    
    This class reuses optical flow computation patterns from FeatureExtractorAgent
    but optimized for real-time performance with adaptive degradation.
    
    Property 1: Frame Buffer Size Validity - All buffers contain 5-10 frames
    Property 2: Analysis Latency Bound - Analysis completes within 200ms
    """
    
    def __init__(self, config: Optional[RealtimeAnalyzerConfig] = None):
        self.config = config or RealtimeAnalyzerConfig()
        self._frame_buffer = FrameBuffer()
        self._last_analysis_time = 0.0
        self._last_latency_ms = 0.0
        self._smoothing_filter = SmoothingFilter()
        
        # Subject tracking state
        self._last_subject_bbox: Optional[BBox] = None
        self._frames_without_subject = 0
        self._subject_lost = False
        
        # Adaptive degradation state
        self._degraded_mode = False
        self._latency_history: deque = deque(maxlen=5)
    
    def decode_base64_jpeg(self, base64_jpeg: str) -> Optional[np.ndarray]:
        """
        Decode a Base64-encoded JPEG image to numpy array.
        
        Args:
            base64_jpeg: Base64-encoded JPEG string
            
        Returns:
            Decoded frame as numpy array (BGR format), or None if decoding fails
        """
        try:
            jpeg_bytes = base64.b64decode(base64_jpeg)
            nparr = np.frombuffer(jpeg_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return frame
        except Exception:
            return None
    
    def decode_frame_buffer(self, base64_frames: list[str]) -> list[np.ndarray]:
        """
        Decode a list of Base64-encoded JPEG frames.
        
        Args:
            base64_frames: List of Base64-encoded JPEG strings
            
        Returns:
            List of decoded frames as numpy arrays (BGR format)
        """
        frames = []
        for b64_jpeg in base64_frames:
            frame = self.decode_base64_jpeg(b64_jpeg)
            if frame is not None:
                frames.append(frame)
        return frames
    
    def add_frames_to_buffer(
        self,
        frames: list[np.ndarray],
        fps: float,
        start_timestamp: Optional[float] = None
    ) -> None:
        """
        Add frames to the sliding window buffer.
        
        Args:
            frames: List of frames to add
            fps: Frames per second for timestamp calculation
            start_timestamp: Starting timestamp (defaults to current time)
        """
        if start_timestamp is None:
            start_timestamp = time.time()
        
        frame_interval = 1.0 / fps if fps > 0 else 0.033  # Default to ~30fps
        
        for i, frame in enumerate(frames):
            timestamp = start_timestamp + (i * frame_interval)
            
            # Resize to target resolution for faster processing
            if frame.shape[:2] != self.config.target_resolution[::-1]:
                frame = cv2.resize(
                    frame,
                    self.config.target_resolution,
                    interpolation=cv2.INTER_LINEAR
                )
            
            self._frame_buffer.add_frame(frame, timestamp)
    
    def get_buffer_for_analysis(self) -> tuple[list[np.ndarray], list[float]]:
        """
        Get frames from buffer for analysis.
        
        Returns:
            Tuple of (frames, timestamps) for analysis
        """
        frames = self._frame_buffer.get_frames()
        timestamps = self._frame_buffer.get_timestamps()
        return frames, timestamps
    
    def is_buffer_ready(self) -> bool:
        """
        Check if buffer has enough frames for analysis.
        
        Per requirements 1.2, buffer should have 5-10 frames.
        
        Returns:
            True if buffer has at least 5 frames
        """
        return self._frame_buffer.size() >= 5
    
    def compute_optical_flow_farneback(
        self,
        frames: list[np.ndarray]
    ) -> OpticalFlowData:
        """
        Compute dense optical flow using Farneback algorithm.
        
        This is the default high-quality mode, reusing patterns from
        FeatureExtractorAgent.compute_optical_flow().
        
        Args:
            frames: List of frames (BGR format)
            
        Returns:
            OpticalFlowData with speed, direction, and flow vectors
        """
        if len(frames) < 2:
            return OpticalFlowData(
                avg_speed_px_s=0.0,
                primary_direction_deg=0.0,
                flow_vectors=[]
            )
        
        # Convert to grayscale
        gray_frames = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
        
        # Apply center region only if configured
        if self.config.center_region_only:
            h, w = gray_frames[0].shape
            cy, cx = h // 2, w // 2
            crop_h, crop_w = h // 2, w // 2
            y1, y2 = cy - crop_h // 2, cy + crop_h // 2
            x1, x2 = cx - crop_w // 2, cx + crop_w // 2
            gray_frames = [f[y1:y2, x1:x2] for f in gray_frames]
        
        all_magnitudes = []
        all_angles = []
        sampled_vectors = []
        
        for i in range(len(gray_frames) - 1):
            prev_frame = gray_frames[i]
            next_frame = gray_frames[i + 1]
            
            # Compute dense optical flow using Farneback
            flow = cv2.calcOpticalFlowFarneback(
                prev_frame,
                next_frame,
                None,
                pyr_scale=self.config.optical_flow_pyr_scale,
                levels=self.config.optical_flow_levels,
                winsize=self.config.optical_flow_winsize,
                iterations=self.config.optical_flow_iterations,
                poly_n=self.config.optical_flow_poly_n,
                poly_sigma=self.config.optical_flow_poly_sigma,
                flags=0
            )
            
            # Calculate magnitude and angle
            mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            
            # Store mean magnitude and dominant angle
            all_magnitudes.append(np.mean(mag))
            
            # Weight angles by magnitude for dominant direction
            weighted_angles = ang * mag
            if np.sum(mag) > 0:
                dominant_angle = np.sum(weighted_angles) / np.sum(mag)
            else:
                dominant_angle = 0.0
            all_angles.append(dominant_angle)
            
            # Sample flow vector from center
            h, w = flow.shape[:2]
            cy, cx = h // 2, w // 2
            sample_flow = flow[cy, cx]
            sampled_vectors.append((float(sample_flow[0]), float(sample_flow[1])))
        
        # Calculate average speed in pixels per frame
        avg_magnitude_per_frame = np.mean(all_magnitudes) if all_magnitudes else 0.0
        
        # Calculate primary direction in degrees (0-360)
        if all_angles:
            sin_sum = np.sum([np.sin(a) for a in all_angles])
            cos_sum = np.sum([np.cos(a) for a in all_angles])
            primary_direction_rad = np.arctan2(sin_sum, cos_sum)
            primary_direction_deg = np.degrees(primary_direction_rad) % 360
        else:
            primary_direction_deg = 0.0
        
        return OpticalFlowData(
            avg_speed_px_s=float(avg_magnitude_per_frame),  # Per frame, not per second
            primary_direction_deg=float(primary_direction_deg),
            flow_vectors=sampled_vectors
        )
    
    def compute_optical_flow_lucas_kanade(
        self,
        frames: list[np.ndarray]
    ) -> OpticalFlowData:
        """
        Compute sparse optical flow using Lucas-Kanade algorithm.
        
        This is the degraded mode for when latency is too high.
        Faster but less accurate than Farneback.
        
        Args:
            frames: List of frames (BGR format)
            
        Returns:
            OpticalFlowData with speed, direction, and flow vectors
        """
        if len(frames) < 2:
            return OpticalFlowData(
                avg_speed_px_s=0.0,
                primary_direction_deg=0.0,
                flow_vectors=[]
            )
        
        # Convert to grayscale
        gray_frames = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
        
        # Parameters for corner detection
        feature_params = dict(
            maxCorners=self.config.lk_max_corners,
            qualityLevel=self.config.lk_quality_level,
            minDistance=self.config.lk_min_distance,
            blockSize=self.config.lk_block_size
        )
        
        # Parameters for Lucas-Kanade optical flow
        lk_params = dict(
            winSize=self.config.lk_win_size,
            maxLevel=2,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
        )
        
        all_magnitudes = []
        all_angles = []
        sampled_vectors = []
        
        for i in range(len(gray_frames) - 1):
            prev_frame = gray_frames[i]
            next_frame = gray_frames[i + 1]
            
            # Find corners to track
            p0 = cv2.goodFeaturesToTrack(prev_frame, mask=None, **feature_params)
            
            if p0 is None or len(p0) == 0:
                continue
            
            # Calculate optical flow
            p1, st, err = cv2.calcOpticalFlowPyrLK(
                prev_frame, next_frame, p0, None, **lk_params
            )
            
            if p1 is None:
                continue
            
            # Select good points
            good_new = p1[st == 1]
            good_old = p0[st == 1]
            
            if len(good_new) == 0:
                continue
            
            # Calculate flow vectors
            flow_vectors = good_new - good_old
            
            # Calculate magnitudes and angles
            magnitudes = np.sqrt(flow_vectors[:, 0]**2 + flow_vectors[:, 1]**2)
            angles = np.arctan2(flow_vectors[:, 1], flow_vectors[:, 0])
            
            all_magnitudes.append(np.mean(magnitudes))
            
            # Weighted average angle
            if np.sum(magnitudes) > 0:
                weighted_angle = np.sum(angles * magnitudes) / np.sum(magnitudes)
            else:
                weighted_angle = 0.0
            all_angles.append(weighted_angle)
            
            # Sample a flow vector
            if len(flow_vectors) > 0:
                mid_idx = len(flow_vectors) // 2
                sampled_vectors.append((
                    float(flow_vectors[mid_idx, 0]),
                    float(flow_vectors[mid_idx, 1])
                ))
        
        # Calculate average speed
        avg_magnitude_per_frame = np.mean(all_magnitudes) if all_magnitudes else 0.0
        
        # Calculate primary direction
        if all_angles:
            sin_sum = np.sum([np.sin(a) for a in all_angles])
            cos_sum = np.sum([np.cos(a) for a in all_angles])
            primary_direction_rad = np.arctan2(sin_sum, cos_sum)
            primary_direction_deg = np.degrees(primary_direction_rad) % 360
        else:
            primary_direction_deg = 0.0
        
        return OpticalFlowData(
            avg_speed_px_s=float(avg_magnitude_per_frame),
            primary_direction_deg=float(primary_direction_deg),
            flow_vectors=sampled_vectors
        )
    
    def compute_optical_flow_fast(
        self,
        frames: list[np.ndarray]
    ) -> tuple[OpticalFlowData, float]:
        """
        Compute optical flow with performance optimization.
        
        Uses Farneback by default, switches to Lucas-Kanade if latency is high.
        Implements adaptive degradation per requirements 11.5, 11.6.
        
        Args:
            frames: List of frames (BGR format)
            
        Returns:
            Tuple of (OpticalFlowData, latency_ms)
        """
        start_time = time.time()
        
        # Check if we should use degraded mode
        if self._degraded_mode or self.config.use_sparse_flow:
            flow_data = self.compute_optical_flow_lucas_kanade(frames)
        else:
            flow_data = self.compute_optical_flow_farneback(frames)
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Update latency history and check for degradation
        self._latency_history.append(latency_ms)
        self._check_degradation()
        
        return flow_data, latency_ms
    
    def _check_degradation(self) -> None:
        """
        Check if we should switch to degraded mode based on latency.
        
        Per requirement 11.5: If latency exceeds 500ms, switch to sparse flow.
        """
        if len(self._latency_history) < 2:
            return
        
        avg_latency = sum(self._latency_history) / len(self._latency_history)
        
        if avg_latency > self.config.latency_threshold_ms:
            if not self._degraded_mode:
                self._degraded_mode = True
        elif avg_latency < self.config.latency_threshold_ms * 0.5:
            # Recover from degraded mode if latency is well below threshold
            if self._degraded_mode:
                self._degraded_mode = False
    
    def should_degrade(self) -> bool:
        """Check if we should switch to degraded mode based on latency."""
        return self._degraded_mode
    
    def calculate_motion_smoothness(
        self,
        flow_data: OpticalFlowData
    ) -> float:
        """
        Calculate motion smoothness based on acceleration variance.
        
        Reuses logic from HeuristicAnalyzerAgent.calculate_motion_smoothness().
        
        Args:
            flow_data: Optical flow data with flow vectors
            
        Returns:
            Motion smoothness in range [0, 1] (higher = smoother)
        """
        flow_vectors = flow_data.flow_vectors
        
        if len(flow_vectors) < 3:
            return 0.5  # Default moderate smoothness
        
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
        normalization_factor = self.config.smoothness_normalization_factor
        smoothness = math.exp(-variance / normalization_factor)
        
        return max(0.0, min(1.0, smoothness))
    
    def calculate_speed_variance(
        self,
        flow_data: OpticalFlowData
    ) -> float:
        """
        Calculate variance of motion speed.
        
        Args:
            flow_data: Optical flow data with flow vectors
            
        Returns:
            Speed variance
        """
        flow_vectors = flow_data.flow_vectors
        
        if len(flow_vectors) < 2:
            return 0.0
        
        # Calculate magnitudes
        magnitudes = [math.sqrt(vx*vx + vy*vy) for vx, vy in flow_vectors]
        
        if not magnitudes:
            return 0.0
        
        mean_mag = sum(magnitudes) / len(magnitudes)
        variance = sum((m - mean_mag) ** 2 for m in magnitudes) / len(magnitudes)
        
        return variance
    
    def detect_subject(
        self,
        frame: np.ndarray
    ) -> Optional[BBox]:
        """
        Detect subject in a single frame.
        
        Uses simple heuristics for fast detection. For production,
        this would integrate with YOLOv8 from FeatureExtractorAgent.
        
        Args:
            frame: Frame to analyze (BGR format)
            
        Returns:
            Detected subject BBox or None
        """
        # Simple center-weighted detection using edge density
        # This is a placeholder - production would use YOLO
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        h, w = edges.shape
        
        # Divide into grid and find region with most edges
        grid_h, grid_w = 3, 3
        cell_h, cell_w = h // grid_h, w // grid_w
        
        max_density = 0
        best_cell = (1, 1)  # Default to center
        
        for i in range(grid_h):
            for j in range(grid_w):
                y1, y2 = i * cell_h, (i + 1) * cell_h
                x1, x2 = j * cell_w, (j + 1) * cell_w
                cell = edges[y1:y2, x1:x2]
                density = np.sum(cell) / (cell_h * cell_w)
                
                # Weight center cells higher
                center_weight = 1.0 + 0.5 * (1.0 - abs(i - 1) / 1.5) * (1.0 - abs(j - 1) / 1.5)
                weighted_density = density * center_weight
                
                if weighted_density > max_density:
                    max_density = weighted_density
                    best_cell = (i, j)
        
        # If edge density is too low, no subject detected
        if max_density < 10:
            return None
        
        # Create bbox for detected region
        i, j = best_cell
        x = j * cell_w / w
        y = i * cell_h / h
        bbox_w = cell_w / w
        bbox_h = cell_h / h
        
        return BBox(x=x, y=y, w=bbox_w, h=bbox_h)
    
    def update_subject_tracking(
        self,
        frames: list[np.ndarray]
    ) -> tuple[Optional[BBox], float, bool]:
        """
        Update subject tracking state across frames.
        
        Implements Subject_Lost state detection per requirements 4.5, 4.6.
        
        Args:
            frames: List of frames to analyze
            
        Returns:
            Tuple of (current_bbox, occupancy, subject_lost)
        """
        if not frames:
            return None, 0.0, self._subject_lost
        
        # Detect subject in last frame
        current_bbox = self.detect_subject(frames[-1])
        
        if current_bbox is not None:
            self._last_subject_bbox = current_bbox
            self._frames_without_subject = 0
            
            # Exit Subject_Lost state if we were in it
            if self._subject_lost:
                self._subject_lost = False
            
            occupancy = current_bbox.area()
        else:
            self._frames_without_subject += 1
            
            # Enter Subject_Lost state after threshold
            if self._frames_without_subject >= self.config.subject_lost_threshold_frames:
                self._subject_lost = True
            
            # Use last known bbox for occupancy
            if self._last_subject_bbox is not None:
                occupancy = self._last_subject_bbox.area()
            else:
                occupancy = 0.0
        
        return current_bbox, occupancy, self._subject_lost
    
    def analyze_buffer(
        self,
        frames: list[np.ndarray],
        fps: float = 30.0
    ) -> RealtimeAnalysisResult:
        """
        Analyze a buffer of frames and return analysis result.
        
        This is the main entry point for realtime analysis.
        
        Args:
            frames: List of 5-10 consecutive frames (BGR format)
            fps: Frames per second of the source video
            
        Returns:
            RealtimeAnalysisResult with all indicators
        """
        start_time = time.time()
        
        # Validate buffer size (Property 1: 5-10 frames)
        if len(frames) < 5:
            # Return low-confidence result for insufficient frames
            return RealtimeAnalysisResult(
                avg_speed_px_frame=0.0,
                speed_variance=0.0,
                motion_smoothness=0.5,
                primary_direction_deg=0.0,
                confidence=0.0,
                analysis_latency_ms=0.0,
            )
        
        # Resize frames if needed
        resized_frames = []
        for frame in frames:
            if frame.shape[:2] != self.config.target_resolution[::-1]:
                frame = cv2.resize(
                    frame,
                    self.config.target_resolution,
                    interpolation=cv2.INTER_LINEAR
                )
            resized_frames.append(frame)
        
        # Compute optical flow with adaptive degradation
        flow_data, flow_latency_ms = self.compute_optical_flow_fast(resized_frames)
        
        # Calculate motion smoothness
        motion_smoothness = self.calculate_motion_smoothness(flow_data)
        
        # Calculate speed variance
        speed_variance = self.calculate_speed_variance(flow_data)
        
        # Update subject tracking
        subject_bbox, subject_occupancy, subject_lost = self.update_subject_tracking(resized_frames)

        # Calculate environment features
        env_features = self.calculate_environment_features(resized_frames[-1])  # Use latest frame

        # Calculate total latency
        total_latency_ms = (time.time() - start_time) * 1000
        self._last_latency_ms = total_latency_ms
        self._last_analysis_time = time.time()

        # Calculate confidence based on data quality
        confidence = self._calculate_confidence(
            len(frames),
            len(flow_data.flow_vectors),
            subject_bbox is not None
        )
        
        return RealtimeAnalysisResult(
            avg_speed_px_frame=flow_data.avg_speed_px_s,  # Actually per frame
            speed_variance=speed_variance,
            motion_smoothness=motion_smoothness,
            primary_direction_deg=flow_data.primary_direction_deg,
            subject_bbox=subject_bbox,
            subject_occupancy=subject_occupancy,
            subject_lost=subject_lost,
            brightness=env_features.get('brightness', 0.5),
            contrast=env_features.get('contrast', 0.5),
            sharpness=env_features.get('sharpness', 0.5),
            saturation=env_features.get('saturation', 0.5),
            dominant_light=env_features.get('dominant_light', 'neutral'),
            composition_score=env_features.get('composition_score', 0.5),
            analysis_latency_ms=total_latency_ms,
            confidence=confidence,
        )
    
    def _calculate_confidence(
        self,
        frame_count: int,
        flow_vector_count: int,
        has_subject: bool
    ) -> float:
        """
        Calculate confidence score for analysis result.
        
        Args:
            frame_count: Number of frames analyzed
            flow_vector_count: Number of flow vectors computed
            has_subject: Whether subject was detected
            
        Returns:
            Confidence score in [0, 1]
        """
        # Base confidence from frame count (5-10 frames optimal)
        if frame_count < 5:
            frame_conf = frame_count / 5.0
        elif frame_count <= 10:
            frame_conf = 1.0
        else:
            frame_conf = 0.9  # Slightly lower for too many frames
        
        # Flow vector confidence
        if flow_vector_count < 2:
            flow_conf = 0.3
        elif flow_vector_count < 5:
            flow_conf = 0.7
        else:
            flow_conf = 1.0
        
        # Subject detection bonus
        subject_conf = 1.0 if has_subject else 0.8
        
        # Combined confidence
        confidence = (frame_conf * 0.4 + flow_conf * 0.4 + subject_conf * 0.2)
        
        return max(0.0, min(1.0, confidence))
    
    def reset(self) -> None:
        """Reset analyzer state."""
        self._frame_buffer.clear()
        self._last_analysis_time = 0.0
        self._last_latency_ms = 0.0
        self._smoothing_filter.reset()
        self._last_subject_bbox = None
        self._frames_without_subject = 0
        self._subject_lost = False
        self._degraded_mode = False
        self._latency_history.clear()

    def calculate_environment_features(self, frame: np.ndarray) -> dict[str, any]:
        """
        Calculate environment features from a single frame.

        Args:
            frame: BGR frame image

        Returns:
            Dictionary containing environment feature measurements
        """
        try:
            # Convert to different color spaces for analysis
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

            # Brightness (from LAB L channel)
            brightness = float(np.mean(lab[:, :, 0]) / 255.0)

            # Contrast (coefficient of variation of grayscale)
            contrast = float(np.std(gray) / (np.mean(gray) + 1e-6))
            contrast = min(contrast * 2.0, 1.0)  # Normalize to 0-1

            # Sharpness (Laplacian variance)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness = min(laplacian_var / 500.0, 1.0)  # Normalize based on typical values

            # Saturation (from HSV S channel)
            saturation = float(np.mean(hsv[:, :, 1]) / 255.0)

            # Dominant lighting (based on color temperature estimate)
            dominant_light = self._estimate_dominant_lighting(frame, hsv)

            # Composition score (rule of thirds approximation)
            composition_score = self._calculate_composition_score(gray)

            return {
                'brightness': brightness,
                'contrast': contrast,
                'sharpness': sharpness,
                'saturation': saturation,
                'dominant_light': dominant_light,
                'composition_score': composition_score,
            }

        except Exception as e:
            # Return neutral values on error
            print(f"Environment feature calculation failed: {e}")
            return {
                'brightness': 0.5,
                'contrast': 0.5,
                'sharpness': 0.5,
                'saturation': 0.5,
                'dominant_light': 'neutral',
                'composition_score': 0.5,
            }

    def _estimate_dominant_lighting(self, bgr_frame: np.ndarray, hsv_frame: np.ndarray) -> str:
        """
        Estimate dominant lighting condition based on color analysis.

        Args:
            bgr_frame: BGR color frame
            hsv_frame: HSV color frame

        Returns:
            'warm', 'cool', or 'neutral'
        """
        try:
            # Calculate average color temperature proxy
            b, g, r = cv2.split(bgr_frame.astype(np.float32))

            # Simple color temperature estimation
            # Warm light has more red/yellow, cool light has more blue
            red_avg = np.mean(r)
            blue_avg = np.mean(b)
            green_avg = np.mean(g)

            # Color temperature ratio (higher = warmer)
            temp_ratio = (red_avg + 0.5 * green_avg) / (blue_avg + 1e-6)

            if temp_ratio > 1.3:
                return 'warm'
            elif temp_ratio < 0.8:
                return 'cool'
            else:
                return 'neutral'

        except Exception:
            return 'neutral'

    def _calculate_composition_score(self, gray_frame: np.ndarray) -> float:
        """
        Calculate composition score based on rule of thirds approximation.

        Args:
            gray_frame: Grayscale frame

        Returns:
            Composition score 0-1 (higher = better composition)
        """
        try:
            h, w = gray_frame.shape
            third_h, third_w = h // 3, w // 3

            # Define rule of thirds points
            points = [
                (third_h, third_w),      # Top-left
                (third_h, 2*third_w),    # Top-center
                (2*third_h, third_w),    # Center-left
                (2*third_h, 2*third_w),  # Center
            ]

            # Calculate entropy at each point
            entropies = []
            window_size = min(32, third_h // 2, third_w // 2)

            for y, x in points:
                if y >= window_size and x >= window_size and \
                   y < h - window_size and x < w - window_size:

                    window = gray_frame[y-window_size:y+window_size,
                                      x-window_size:x+window_size]

                    # Calculate local entropy (proxy for visual interest)
                    hist = cv2.calcHist([window], [0], None, [32], [0, 256])
                    hist = hist / hist.sum()
                    entropy = -np.sum(hist * np.log2(hist + 1e-6))
                    entropies.append(entropy)

            if entropies:
                # Average entropy normalized to 0-1
                avg_entropy = np.mean(entropies)
                return min(avg_entropy / 4.0, 1.0)  # Normalize based on max expected entropy
            else:
                return 0.5

        except Exception:
            return 0.5
