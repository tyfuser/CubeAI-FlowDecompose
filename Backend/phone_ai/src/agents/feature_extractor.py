"""
Feature Extractor Agent for the Video Shooting Assistant.

Extracts shooting-related features from video frames and audio:
- Optical flow computation (Farneback algorithm)
- Subject detection and tracking (YOLOv8 + CSRT)
- Frame embeddings (ResNet50/MobileNet)
- Audio beat detection (librosa)
- Keypoint tracking (MediaPipe)
"""
import os
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import numpy as np
import cv2

from src.models.data_types import (
    BBox,
    OpticalFlowData,
    SubjectTrackingData,
    FeatureOutput,
    UploaderOutput,
)


@dataclass
class FeatureExtractorConfig:
    """Configuration for the Feature Extractor Agent."""
    # Optical flow settings
    optical_flow_pyr_scale: float = 0.5
    optical_flow_levels: int = 3
    optical_flow_winsize: int = 15
    optical_flow_iterations: int = 3
    optical_flow_poly_n: int = 5
    optical_flow_poly_sigma: float = 1.2
    
    # Subject detection settings
    yolo_model: str = "yolov8n.pt"  # nano model for speed
    detection_confidence: float = 0.5
    tracker_type: str = "CSRT"  # KCF or CSRT
    
    # Embedding settings
    embedding_model: str = "mobilenet_v2"  # mobilenet_v2 or resnet50
    embedding_batch_size: int = 16
    
    # Audio settings
    audio_sample_rate: int = 22050
    
    # Keypoint settings
    enable_keypoints: bool = False  # Optional feature
    
    # Sampling settings
    max_frames_for_flow: int = 300  # Sample frames for optical flow
    flow_vector_sample_rate: int = 10  # Sample every Nth flow vector


class FeatureExtractorAgent:
    """
    特征提取模块
    Extracts features from video frames and audio for analysis.
    """
    
    def __init__(self, config: Optional[FeatureExtractorConfig] = None):
        """
        Initialize the Feature Extractor Agent.
        
        Args:
            config: Configuration options for feature extraction
        """
        self.config = config or FeatureExtractorConfig()
        self._yolo_model = None
        self._embedding_model = None
        self._embedding_transform = None
        self._pose_detector = None

    def _load_frames(self, frames_path: str, max_frames: Optional[int] = None) -> list[np.ndarray]:
        """
        Load frames from directory.
        
        Args:
            frames_path: Path to directory containing frame images
            max_frames: Maximum number of frames to load (samples evenly if exceeded)
            
        Returns:
            List of frames as numpy arrays (BGR format)
        """
        frames_dir = Path(frames_path)
        
        # Find all frame files
        frame_files = sorted(
            [f for f in frames_dir.iterdir() 
             if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
        )
        
        if not frame_files:
            raise ValueError(f"No frame files found in {frames_path}")
        
        # Sample frames if needed
        if max_frames and len(frame_files) > max_frames:
            indices = np.linspace(0, len(frame_files) - 1, max_frames, dtype=int)
            frame_files = [frame_files[i] for i in indices]
        
        # Load frames
        frames = []
        for frame_file in frame_files:
            frame = cv2.imread(str(frame_file))
            if frame is not None:
                frames.append(frame)
        
        return frames
    
    def _load_frames_gray(self, frames_path: str, max_frames: Optional[int] = None) -> list[np.ndarray]:
        """
        Load frames as grayscale images.
        
        Args:
            frames_path: Path to directory containing frame images
            max_frames: Maximum number of frames to load
            
        Returns:
            List of grayscale frames as numpy arrays
        """
        frames = self._load_frames(frames_path, max_frames)
        return [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]

    def compute_optical_flow(
        self,
        frames_path: str,
        fps: float,
        max_frames: Optional[int] = None
    ) -> OpticalFlowData:
        """
        Compute optical flow between adjacent frames using Farneback algorithm.
        
        Args:
            frames_path: Path to directory containing frame images
            fps: Frames per second of the video
            max_frames: Maximum frames to process (samples evenly if exceeded)
            
        Returns:
            OpticalFlowData with average speed, primary direction, and sampled flow vectors
        """
        max_frames = max_frames or self.config.max_frames_for_flow
        gray_frames = self._load_frames_gray(frames_path, max_frames)
        
        if len(gray_frames) < 2:
            return OpticalFlowData(
                avg_speed_px_s=0.0,
                primary_direction_deg=0.0,
                flow_vectors=[]
            )
        
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
            
            # Sample flow vectors for storage
            if i % self.config.flow_vector_sample_rate == 0:
                h, w = flow.shape[:2]
                # Sample from center region
                cy, cx = h // 2, w // 2
                sample_flow = flow[cy, cx]
                sampled_vectors.append((float(sample_flow[0]), float(sample_flow[1])))
        
        # Calculate average speed in pixels per second
        avg_magnitude_per_frame = np.mean(all_magnitudes) if all_magnitudes else 0.0
        avg_speed_px_s = avg_magnitude_per_frame * fps
        
        # Calculate primary direction in degrees (0-360)
        if all_angles:
            # Circular mean for angles
            sin_sum = np.sum([np.sin(a) for a in all_angles])
            cos_sum = np.sum([np.cos(a) for a in all_angles])
            primary_direction_rad = np.arctan2(sin_sum, cos_sum)
            primary_direction_deg = np.degrees(primary_direction_rad) % 360
        else:
            primary_direction_deg = 0.0
        
        return OpticalFlowData(
            avg_speed_px_s=float(avg_speed_px_s),
            primary_direction_deg=float(primary_direction_deg),
            flow_vectors=sampled_vectors
        )


    def _get_yolo_model(self):
        """Lazy load YOLOv8 model."""
        if self._yolo_model is None:
            try:
                from ultralytics import YOLO
                self._yolo_model = YOLO(self.config.yolo_model)
            except ImportError:
                raise ImportError("ultralytics package required for subject detection")
        return self._yolo_model
    
    def _create_tracker(self):
        """Create OpenCV tracker based on config."""
        tracker_type = self.config.tracker_type.upper()
        if tracker_type == "CSRT":
            return cv2.TrackerCSRT_create()
        elif tracker_type == "KCF":
            return cv2.TrackerKCF_create()
        else:
            return cv2.TrackerCSRT_create()
    
    def _normalize_bbox(
        self,
        bbox: tuple[int, int, int, int],
        frame_width: int,
        frame_height: int
    ) -> BBox:
        """
        Normalize bounding box coordinates to [0, 1] range.
        
        Args:
            bbox: Bounding box as (x, y, w, h) in pixels
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels
            
        Returns:
            Normalized BBox with coordinates in [0, 1]
        """
        x, y, w, h = bbox
        return BBox(
            x=max(0.0, min(1.0, x / frame_width)),
            y=max(0.0, min(1.0, y / frame_height)),
            w=max(0.0, min(1.0, w / frame_width)),
            h=max(0.0, min(1.0, h / frame_height))
        ).normalize()

    def detect_and_track_subject(
        self,
        frames_path: str,
        fps: float
    ) -> SubjectTrackingData:
        """
        Detect and track the main subject across frames.
        
        Uses YOLOv8 for initial detection and CSRT/KCF tracker for subsequent frames.
        Tracks the largest detected object (assumed to be main subject).
        
        Args:
            frames_path: Path to directory containing frame images
            fps: Frames per second of the video
            
        Returns:
            SubjectTrackingData with bounding box sequences, confidence scores, and timestamps
        """
        frames = self._load_frames(frames_path)
        
        if not frames:
            return SubjectTrackingData()
        
        frame_height, frame_width = frames[0].shape[:2]
        
        bbox_sequence = []
        confidence_scores = []
        timestamps = []
        
        tracker = None
        tracking_active = False
        detection_interval = max(1, int(fps))  # Re-detect every second
        
        model = self._get_yolo_model()
        
        for i, frame in enumerate(frames):
            timestamp = i / fps
            
            # Perform detection at intervals or when tracking fails
            should_detect = (
                not tracking_active or 
                i % detection_interval == 0
            )
            
            if should_detect:
                # Run YOLOv8 detection
                results = model(frame, verbose=False, conf=self.config.detection_confidence)
                
                if len(results) > 0 and len(results[0].boxes) > 0:
                    boxes = results[0].boxes
                    
                    # Find largest detection (main subject)
                    largest_area = 0
                    best_box = None
                    best_conf = 0.0
                    
                    for box in boxes:
                        xyxy = box.xyxy[0].cpu().numpy()
                        x1, y1, x2, y2 = xyxy
                        area = (x2 - x1) * (y2 - y1)
                        
                        if area > largest_area:
                            largest_area = area
                            best_box = (int(x1), int(y1), int(x2 - x1), int(y2 - y1))
                            best_conf = float(box.conf[0])
                    
                    if best_box is not None:
                        # Initialize tracker with detected box
                        tracker = self._create_tracker()
                        tracker.init(frame, best_box)
                        tracking_active = True
                        
                        # Store normalized bbox
                        norm_bbox = self._normalize_bbox(best_box, frame_width, frame_height)
                        bbox_sequence.append(norm_bbox)
                        confidence_scores.append(best_conf)
                        timestamps.append(timestamp)
                        continue
            
            # Use tracker for intermediate frames
            if tracking_active and tracker is not None:
                success, box = tracker.update(frame)
                
                if success:
                    x, y, w, h = [int(v) for v in box]
                    norm_bbox = self._normalize_bbox((x, y, w, h), frame_width, frame_height)
                    bbox_sequence.append(norm_bbox)
                    # Tracker doesn't provide confidence, use decaying value
                    last_conf = confidence_scores[-1] if confidence_scores else 0.5
                    confidence_scores.append(last_conf * 0.99)
                    timestamps.append(timestamp)
                else:
                    tracking_active = False
        
        return SubjectTrackingData(
            bbox_sequence=bbox_sequence,
            confidence_scores=confidence_scores,
            timestamps=timestamps
        )


    def _get_embedding_model(self):
        """Lazy load embedding model (MobileNetV2 or ResNet50)."""
        if self._embedding_model is None:
            try:
                import torch
                import torchvision.models as models
                import torchvision.transforms as transforms
                
                device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                
                if self.config.embedding_model == "resnet50":
                    # Load ResNet50 without final classification layer
                    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
                    # Remove the final FC layer to get embeddings
                    self._embedding_model = torch.nn.Sequential(*list(model.children())[:-1])
                else:
                    # Default to MobileNetV2
                    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
                    # Remove classifier to get embeddings
                    self._embedding_model = model.features
                
                self._embedding_model = self._embedding_model.to(device)
                self._embedding_model.eval()
                
                # Standard ImageNet preprocessing
                self._embedding_transform = transforms.Compose([
                    transforms.ToPILImage(),
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225]
                    )
                ])
                
            except ImportError:
                raise ImportError("torch and torchvision required for embedding extraction")
        
        return self._embedding_model, self._embedding_transform

    def extract_frame_embeddings(
        self,
        frames_path: str,
        sample_rate: int = 1
    ) -> list[list[float]]:
        """
        Extract global feature embeddings from frames using pretrained CNN.
        
        Args:
            frames_path: Path to directory containing frame images
            sample_rate: Extract embedding every N frames (default: every frame)
            
        Returns:
            List of embedding vectors (normalized to unit length)
        """
        import torch
        
        model, transform = self._get_embedding_model()
        device = next(model.parameters()).device
        
        frames = self._load_frames(frames_path)
        
        if not frames:
            return []
        
        # Sample frames
        sampled_frames = frames[::sample_rate]
        
        embeddings = []
        batch_size = self.config.embedding_batch_size
        
        with torch.no_grad():
            for i in range(0, len(sampled_frames), batch_size):
                batch_frames = sampled_frames[i:i + batch_size]
                
                # Preprocess batch
                batch_tensors = []
                for frame in batch_frames:
                    # Convert BGR to RGB
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    tensor = transform(rgb_frame)
                    batch_tensors.append(tensor)
                
                batch = torch.stack(batch_tensors).to(device)
                
                # Extract features
                features = model(batch)
                
                # Flatten and normalize
                features = features.view(features.size(0), -1)
                
                # L2 normalize for cosine similarity
                features = torch.nn.functional.normalize(features, p=2, dim=1)
                
                # Convert to list
                for feat in features.cpu().numpy():
                    embeddings.append(feat.tolist())
        
        return embeddings


    def extract_audio_beats(
        self,
        audio_path: str,
        duration_s: Optional[float] = None
    ) -> list[float]:
        """
        Extract beat onset timestamps from audio using librosa.
        
        Args:
            audio_path: Path to audio file (WAV format preferred)
            duration_s: Video duration in seconds (for validation)
            
        Returns:
            List of beat timestamps in seconds
        """
        if audio_path is None or not Path(audio_path).exists():
            return []
        
        try:
            import librosa
            
            # Load audio file
            y, sr = librosa.load(audio_path, sr=self.config.audio_sample_rate)
            
            # Detect onset events (beats)
            onset_frames = librosa.onset.onset_detect(
                y=y,
                sr=sr,
                units='frames',
                backtrack=True
            )
            
            # Convert frames to time
            onset_times = librosa.frames_to_time(onset_frames, sr=sr)
            
            # Filter to valid range if duration provided
            if duration_s is not None:
                onset_times = onset_times[onset_times <= duration_s]
            
            # Ensure all timestamps are non-negative
            onset_times = onset_times[onset_times >= 0]
            
            return onset_times.tolist()
            
        except ImportError:
            raise ImportError("librosa package required for audio beat detection")
        except Exception as e:
            # Return empty list on audio processing errors
            print(f"Warning: Audio beat detection failed: {e}")
            return []


    def _get_pose_detector(self):
        """Lazy load MediaPipe Pose detector."""
        if self._pose_detector is None:
            try:
                import mediapipe as mp
                self._pose_detector = mp.solutions.pose.Pose(
                    static_image_mode=False,
                    model_complexity=1,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
            except ImportError:
                raise ImportError("mediapipe package required for keypoint tracking")
        return self._pose_detector

    def extract_keypoints(
        self,
        frames_path: str,
        fps: float,
        sample_rate: int = 1
    ) -> list[dict]:
        """
        Extract pose keypoint trajectories using MediaPipe.
        
        Args:
            frames_path: Path to directory containing frame images
            fps: Frames per second of the video
            sample_rate: Process every N frames
            
        Returns:
            List of keypoint dictionaries with landmarks and timestamps
        """
        if not self.config.enable_keypoints:
            return []
        
        import mediapipe as mp
        
        pose = self._get_pose_detector()
        frames = self._load_frames(frames_path)
        
        if not frames:
            return []
        
        keypoints_data = []
        
        for i, frame in enumerate(frames[::sample_rate]):
            timestamp = (i * sample_rate) / fps
            
            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame
            results = pose.process(rgb_frame)
            
            if results.pose_landmarks:
                landmarks = []
                for landmark in results.pose_landmarks.landmark:
                    landmarks.append({
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z,
                        'visibility': landmark.visibility
                    })
                
                keypoints_data.append({
                    'timestamp': timestamp,
                    'landmarks': landmarks,
                    'frame_index': i * sample_rate
                })
        
        return keypoints_data


    async def process(
        self,
        uploader_output: UploaderOutput,
        config: Optional[FeatureExtractorConfig] = None
    ) -> FeatureOutput:
        """
        Process video frames and audio to extract all features.
        
        This is the main entry point for the Feature Extractor Agent.
        
        Args:
            uploader_output: Output from the Uploader Agent
            config: Optional config override
            
        Returns:
            FeatureOutput with all extracted features
        """
        if config is not None:
            self.config = config
        
        video_id = uploader_output.video_id
        frames_path = uploader_output.frames_path
        fps = uploader_output.fps
        duration_s = uploader_output.duration_s
        audio_path = uploader_output.audio_path
        
        # Extract optical flow
        optical_flow = self.compute_optical_flow(frames_path, fps)
        
        # Detect and track subject
        subject_tracking = self.detect_and_track_subject(frames_path, fps)
        
        # Extract frame embeddings (sample every 5 frames for efficiency)
        frame_embeddings = self.extract_frame_embeddings(frames_path, sample_rate=5)
        
        # Extract audio beats if audio available
        audio_beats = None
        if audio_path:
            audio_beats = self.extract_audio_beats(audio_path, duration_s)
        
        # Extract keypoints if enabled
        keypoints = None
        if self.config.enable_keypoints:
            keypoints = self.extract_keypoints(frames_path, fps, sample_rate=3)
        
        return FeatureOutput(
            video_id=video_id,
            optical_flow=optical_flow,
            subject_tracking=subject_tracking,
            keypoints=keypoints,
            frame_embeddings=frame_embeddings,
            audio_beats=audio_beats
        )
    
    def process_sync(
        self,
        uploader_output: UploaderOutput,
        config: Optional[FeatureExtractorConfig] = None
    ) -> FeatureOutput:
        """
        Synchronous version of process() for non-async contexts.
        
        Args:
            uploader_output: Output from the Uploader Agent
            config: Optional config override
            
        Returns:
            FeatureOutput with all extracted features
        """
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.process(uploader_output, config)
        )
