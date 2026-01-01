"""
Uploader Agent for the Video Shooting Assistant.

Handles video file upload, validation, preprocessing, and metadata extraction.
Supports MP4, MOV, AVI, MKV formats.
"""
import os
import uuid
import subprocess
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from enum import Enum

from src.models.data_types import ExifData, UploaderOutput


class VideoFormat(str, Enum):
    """Supported video formats."""
    MP4 = "mp4"
    MOV = "mov"
    AVI = "avi"
    MKV = "mkv"
    
    @classmethod
    def values(cls) -> list[str]:
        """Return all supported format extensions."""
        return [e.value for e in cls]
    
    @classmethod
    def is_supported(cls, extension: str) -> bool:
        """Check if a file extension is supported."""
        return extension.lower().lstrip('.') in cls.values()


@dataclass
class UploaderConfig:
    """Configuration for the Uploader Agent."""
    target_resolution: tuple[int, int] = (640, 360)  # Default low-res for analysis
    frame_format: str = "jpg"  # jpg or png
    max_file_size_mb: float = 2048.0  # 2GB default max
    segment_duration_s: float = 60.0  # Process in 60-second segments for large files
    output_dir: Optional[str] = None  # Output directory for frames


@dataclass
class ValidationResult:
    """Result of video file validation."""
    is_valid: bool
    format: Optional[str] = None
    file_size_mb: float = 0.0
    error_message: Optional[str] = None
    needs_segmentation: bool = False
    segment_count: int = 1


class UploaderAgent:
    """
    视频上传和预处理模块
    Handles video file validation, frame extraction, and metadata extraction.
    """
    
    SUPPORTED_FORMATS = VideoFormat.values()
    
    def __init__(self, config: Optional[UploaderConfig] = None):
        """
        Initialize the Uploader Agent.
        
        Args:
            config: Configuration options for the uploader
        """
        self.config = config or UploaderConfig()
    
    def validate_video(self, video_path: str) -> ValidationResult:
        """
        Validate a video file for format and size.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            ValidationResult with validation status and details
        """
        path = Path(video_path)
        
        # Check if file exists
        if not path.exists():
            return ValidationResult(
                is_valid=False,
                error_message=f"File not found: {video_path}"
            )
        
        # Check if it's a file (not directory)
        if not path.is_file():
            return ValidationResult(
                is_valid=False,
                error_message=f"Path is not a file: {video_path}"
            )
        
        # Get file extension
        extension = path.suffix.lower().lstrip('.')
        
        # Check format support
        if not VideoFormat.is_supported(extension):
            return ValidationResult(
                is_valid=False,
                format=extension,
                error_message=f"Unsupported format: {extension}. Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        # Check file size
        file_size_bytes = path.stat().st_size
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        if file_size_mb > self.config.max_file_size_mb:
            return ValidationResult(
                is_valid=False,
                format=extension,
                file_size_mb=file_size_mb,
                error_message=f"File too large: {file_size_mb:.2f}MB exceeds limit of {self.config.max_file_size_mb}MB"
            )
        
        # Verify it's a valid video file using ffprobe
        try:
            probe_result = self._probe_video(video_path)
            if probe_result is None:
                return ValidationResult(
                    is_valid=False,
                    format=extension,
                    file_size_mb=file_size_mb,
                    error_message="Invalid or corrupted video file"
                )
            
            # Check if segmentation is needed based on duration
            duration = probe_result.get("duration", 0)
            needs_segmentation = duration > self.config.segment_duration_s * 2
            segment_count = max(1, int(duration / self.config.segment_duration_s))
            
            return ValidationResult(
                is_valid=True,
                format=extension,
                file_size_mb=file_size_mb,
                needs_segmentation=needs_segmentation,
                segment_count=segment_count
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                format=extension,
                file_size_mb=file_size_mb,
                error_message=f"Error validating video: {str(e)}"
            )
    
    def _probe_video(self, video_path: str) -> Optional[dict]:
        """
        Probe video file using ffprobe to get basic info.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary with video info or None if invalid
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return None
            
            probe_data = json.loads(result.stdout)
            
            # Extract basic info
            format_info = probe_data.get('format', {})
            streams = probe_data.get('streams', [])
            
            # Find video stream
            video_stream = None
            audio_stream = None
            for stream in streams:
                if stream.get('codec_type') == 'video' and video_stream is None:
                    video_stream = stream
                elif stream.get('codec_type') == 'audio' and audio_stream is None:
                    audio_stream = stream
            
            if video_stream is None:
                return None
            
            return {
                'duration': float(format_info.get('duration', 0)),
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'fps': self._parse_fps(video_stream.get('r_frame_rate', '0/1')),
                'codec': video_stream.get('codec_name', ''),
                'has_audio': audio_stream is not None,
                'format_name': format_info.get('format_name', ''),
            }
            
        except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, ValueError):
            return None
    
    def _parse_fps(self, fps_str: str) -> float:
        """Parse FPS from ffprobe format (e.g., '30/1' or '29.97')."""
        try:
            if '/' in fps_str:
                num, den = fps_str.split('/')
                return float(num) / float(den) if float(den) != 0 else 0.0
            return float(fps_str)
        except (ValueError, ZeroDivisionError):
            return 0.0

    def extract_frames(
        self,
        video_path: str,
        output_dir: Optional[str] = None,
        target_resolution: Optional[tuple[int, int]] = None
    ) -> tuple[str, int]:
        """
        Extract frames from video using FFmpeg.
        
        Args:
            video_path: Path to the video file
            output_dir: Directory to save frames (creates temp dir if None)
            target_resolution: Target resolution (width, height), uses config default if None
            
        Returns:
            Tuple of (frames_directory_path, frame_count)
            
        Raises:
            ValueError: If video file is invalid
            RuntimeError: If frame extraction fails
        """
        # Validate video first
        validation = self.validate_video(video_path)
        if not validation.is_valid:
            raise ValueError(validation.error_message)
        
        # Set up output directory
        if output_dir is None:
            output_dir = self.config.output_dir
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="video_frames_")
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Get target resolution
        resolution = target_resolution or self.config.target_resolution
        
        # Build ffmpeg command
        frame_format = self.config.frame_format
        output_pattern = os.path.join(output_dir, f"frame_%06d.{frame_format}")
        
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f'scale={resolution[0]}:{resolution[1]}',
            '-q:v', '2',  # High quality for JPEG
            '-y',  # Overwrite output files
            output_pattern
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg frame extraction failed: {result.stderr}")
            
            # Count extracted frames
            frame_files = list(Path(output_dir).glob(f"frame_*.{frame_format}"))
            frame_count = len(frame_files)
            
            if frame_count == 0:
                raise RuntimeError("No frames were extracted from the video")
            
            return output_dir, frame_count
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Frame extraction timed out")
    
    def extract_video_params(self, video_path: str) -> dict:
        """
        Extract basic video parameters using ffprobe.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary with fps, resolution, duration
            
        Raises:
            ValueError: If video file is invalid or cannot be probed
        """
        probe_result = self._probe_video(video_path)
        
        if probe_result is None:
            raise ValueError(f"Cannot extract parameters from video: {video_path}")
        
        return {
            'fps': probe_result['fps'],
            'resolution': (probe_result['width'], probe_result['height']),
            'duration_s': probe_result['duration'],
            'codec': probe_result['codec'],
            'has_audio': probe_result['has_audio'],
        }
    
    def extract_exif(self, video_path: str) -> ExifData:
        """
        Extract EXIF metadata from video file.
        
        Uses ffprobe to extract camera metadata when available.
        Many video files don't contain EXIF data, so fields may be None.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            ExifData with extracted metadata (fields may be None if not available)
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return ExifData()
            
            probe_data = json.loads(result.stdout)
            
            # Extract metadata from format tags
            format_tags = probe_data.get('format', {}).get('tags', {})
            
            # Try to find video stream tags
            streams = probe_data.get('streams', [])
            stream_tags = {}
            for stream in streams:
                if stream.get('codec_type') == 'video':
                    stream_tags = stream.get('tags', {})
                    break
            
            # Merge tags (format tags take precedence)
            all_tags = {**stream_tags, **format_tags}
            
            # Extract EXIF-like data
            # Note: Most video formats don't have traditional EXIF data
            # We look for common metadata fields
            focal_length = self._extract_focal_length(all_tags)
            aperture = self._extract_aperture(all_tags)
            sensor_size = self._extract_sensor_size(all_tags)
            iso = self._extract_iso(all_tags)
            
            return ExifData(
                focal_length_mm=focal_length,
                aperture=aperture,
                sensor_size=sensor_size,
                iso=iso
            )
            
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
            return ExifData()
    
    def _extract_focal_length(self, tags: dict) -> Optional[float]:
        """Extract focal length from metadata tags."""
        # Common tag names for focal length
        focal_keys = ['focal_length', 'FocalLength', 'com.apple.quicktime.camera.focal_length']
        
        for key in focal_keys:
            if key in tags:
                try:
                    value = tags[key]
                    # Handle format like "4.2 mm" or "4.2"
                    if isinstance(value, str):
                        value = value.replace('mm', '').strip()
                    return float(value)
                except (ValueError, TypeError):
                    continue
        return None
    
    def _extract_aperture(self, tags: dict) -> Optional[float]:
        """Extract aperture (f-number) from metadata tags."""
        aperture_keys = ['aperture', 'FNumber', 'com.apple.quicktime.camera.aperture']
        
        for key in aperture_keys:
            if key in tags:
                try:
                    value = tags[key]
                    if isinstance(value, str):
                        # Handle format like "f/2.8" or "2.8"
                        value = value.replace('f/', '').replace('F/', '').strip()
                    return float(value)
                except (ValueError, TypeError):
                    continue
        return None
    
    def _extract_sensor_size(self, tags: dict) -> Optional[str]:
        """Extract sensor size from metadata tags."""
        sensor_keys = ['sensor_size', 'SensorSize', 'com.apple.quicktime.camera.sensor']
        
        for key in sensor_keys:
            if key in tags:
                return str(tags[key])
        return None
    
    def _extract_iso(self, tags: dict) -> Optional[int]:
        """Extract ISO value from metadata tags."""
        iso_keys = ['iso', 'ISO', 'ISOSpeedRatings', 'com.apple.quicktime.camera.iso']
        
        for key in iso_keys:
            if key in tags:
                try:
                    return int(float(tags[key]))
                except (ValueError, TypeError):
                    continue
        return None

    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Extract audio track from video as WAV format.
        
        Args:
            video_path: Path to the video file
            output_path: Path for output WAV file (auto-generated if None)
            
        Returns:
            Path to extracted audio file, or None if no audio track exists
            
        Raises:
            RuntimeError: If audio extraction fails
        """
        # Check if video has audio
        probe_result = self._probe_video(video_path)
        if probe_result is None or not probe_result.get('has_audio', False):
            return None
        
        # Generate output path if not provided
        if output_path is None:
            video_name = Path(video_path).stem
            output_dir = self.config.output_dir or tempfile.gettempdir()
            output_path = os.path.join(output_dir, f"{video_name}_audio.wav")
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Extract audio using ffmpeg
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # PCM 16-bit little-endian
            '-ar', '44100',  # 44.1kHz sample rate
            '-ac', '2',  # Stereo
            '-y',  # Overwrite output
            output_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                # Check if it's because there's no audio
                if 'does not contain any stream' in result.stderr.lower():
                    return None
                raise RuntimeError(f"Audio extraction failed: {result.stderr}")
            
            # Verify output file exists and has content
            if not Path(output_path).exists() or Path(output_path).stat().st_size == 0:
                return None
            
            return output_path
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Audio extraction timed out")
    
    async def process(
        self,
        video_path: str,
        video_id: Optional[str] = None,
        config: Optional[UploaderConfig] = None
    ) -> UploaderOutput:
        """
        Process an uploaded video file.
        
        This is the main entry point for the Uploader Agent.
        Performs validation, frame extraction, EXIF extraction, and audio extraction.
        
        Args:
            video_path: Path to the video file
            video_id: Optional video ID (generated if not provided)
            config: Optional config override
            
        Returns:
            UploaderOutput with all extracted data
            
        Raises:
            ValueError: If video validation fails
            RuntimeError: If processing fails
        """
        # Use provided config or default
        if config is not None:
            self.config = config
        
        # Generate video ID if not provided
        if video_id is None:
            video_id = str(uuid.uuid4())
        
        # Validate video
        validation = self.validate_video(video_path)
        if not validation.is_valid:
            raise ValueError(validation.error_message)
        
        # Extract video parameters
        video_params = self.extract_video_params(video_path)
        
        # Extract frames
        frames_path, frame_count = self.extract_frames(video_path)
        
        # Extract EXIF data
        exif_data = self.extract_exif(video_path)
        
        # Extract audio (optional)
        audio_path = None
        if video_params.get('has_audio', False):
            try:
                audio_path = self.extract_audio(video_path)
            except RuntimeError:
                # Audio extraction failure is not critical
                pass
        
        return UploaderOutput(
            video_id=video_id,
            frames_path=frames_path,
            frame_count=frame_count,
            fps=video_params['fps'],
            duration_s=video_params['duration_s'],
            resolution=video_params['resolution'],
            exif=exif_data,
            audio_path=audio_path
        )
    
    def process_sync(
        self,
        video_path: str,
        video_id: Optional[str] = None,
        config: Optional[UploaderConfig] = None
    ) -> UploaderOutput:
        """
        Synchronous version of process() for non-async contexts.
        
        Args:
            video_path: Path to the video file
            video_id: Optional video ID (generated if not provided)
            config: Optional config override
            
        Returns:
            UploaderOutput with all extracted data
        """
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.process(video_path, video_id, config)
        )
