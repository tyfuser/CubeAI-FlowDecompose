"""
Unit tests for the Uploader Agent.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.agents.uploader import (
    UploaderAgent,
    UploaderConfig,
    ValidationResult,
    VideoFormat,
)
from src.models.data_types import ExifData


class TestVideoFormat:
    """Tests for VideoFormat enum."""
    
    def test_supported_formats(self):
        """Test that all required formats are supported."""
        assert VideoFormat.is_supported("mp4")
        assert VideoFormat.is_supported("mov")
        assert VideoFormat.is_supported("avi")
        assert VideoFormat.is_supported("mkv")
    
    def test_unsupported_format(self):
        """Test unsupported format detection."""
        assert not VideoFormat.is_supported("gif")
        assert not VideoFormat.is_supported("webm")
    
    def test_case_insensitive(self):
        """Test case insensitive format checking."""
        assert VideoFormat.is_supported("MP4")
        assert VideoFormat.is_supported("MOV")
        assert VideoFormat.is_supported(".mp4")


class TestUploaderConfig:
    """Tests for UploaderConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = UploaderConfig()
        assert config.target_resolution == (640, 360)
        assert config.frame_format == "jpg"
        assert config.max_file_size_mb == 2048.0
        assert config.segment_duration_s == 60.0
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = UploaderConfig(
            target_resolution=(1280, 720),
            frame_format="png",
            max_file_size_mb=1024.0,
        )
        assert config.target_resolution == (1280, 720)
        assert config.frame_format == "png"
        assert config.max_file_size_mb == 1024.0


class TestUploaderAgentValidation:
    """Tests for UploaderAgent validation methods."""
    
    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        agent = UploaderAgent()
        result = agent.validate_video("/nonexistent/path/video.mp4")
        
        assert not result.is_valid
        assert "not found" in result.error_message.lower()
    
    def test_validate_directory_path(self):
        """Test validation of directory path."""
        agent = UploaderAgent()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = agent.validate_video(tmpdir)
            
            assert not result.is_valid
            assert "not a file" in result.error_message.lower()
    
    def test_validate_unsupported_format(self):
        """Test validation of unsupported format."""
        agent = UploaderAgent()
        with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as f:
            f.write(b"fake gif content")
            temp_path = f.name
        
        try:
            result = agent.validate_video(temp_path)
            assert not result.is_valid
            assert "unsupported format" in result.error_message.lower()
        finally:
            os.unlink(temp_path)
    
    def test_validate_file_too_large(self):
        """Test validation of file exceeding size limit."""
        config = UploaderConfig(max_file_size_mb=0.001)  # 1KB limit
        agent = UploaderAgent(config)
        
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"x" * 2048)  # 2KB file
            temp_path = f.name
        
        try:
            result = agent.validate_video(temp_path)
            assert not result.is_valid
            assert "too large" in result.error_message.lower()
        finally:
            os.unlink(temp_path)


class TestUploaderAgentFPSParsing:
    """Tests for FPS parsing utility."""
    
    def test_parse_fps_fraction(self):
        """Test parsing FPS from fraction format."""
        agent = UploaderAgent()
        assert agent._parse_fps("30/1") == 30.0
        assert abs(agent._parse_fps("30000/1001") - 29.97) < 0.01
    
    def test_parse_fps_decimal(self):
        """Test parsing FPS from decimal format."""
        agent = UploaderAgent()
        assert agent._parse_fps("29.97") == 29.97
        assert agent._parse_fps("60.0") == 60.0
    
    def test_parse_fps_invalid(self):
        """Test parsing invalid FPS values."""
        agent = UploaderAgent()
        assert agent._parse_fps("0/0") == 0.0
        assert agent._parse_fps("invalid") == 0.0


class TestExifExtraction:
    """Tests for EXIF metadata extraction helpers."""
    
    def test_extract_focal_length_mm_format(self):
        """Test focal length extraction with mm suffix."""
        agent = UploaderAgent()
        tags = {"focal_length": "4.2 mm"}
        result = agent._extract_focal_length(tags)
        assert result == 4.2
    
    def test_extract_focal_length_numeric(self):
        """Test focal length extraction with numeric value."""
        agent = UploaderAgent()
        tags = {"FocalLength": "50"}
        result = agent._extract_focal_length(tags)
        assert result == 50.0
    
    def test_extract_aperture_f_format(self):
        """Test aperture extraction with f/ prefix."""
        agent = UploaderAgent()
        tags = {"aperture": "f/2.8"}
        result = agent._extract_aperture(tags)
        assert result == 2.8
    
    def test_extract_aperture_numeric(self):
        """Test aperture extraction with numeric value."""
        agent = UploaderAgent()
        tags = {"FNumber": "1.8"}
        result = agent._extract_aperture(tags)
        assert result == 1.8
    
    def test_extract_iso(self):
        """Test ISO extraction."""
        agent = UploaderAgent()
        tags = {"ISO": "400"}
        result = agent._extract_iso(tags)
        assert result == 400
    
    def test_extract_missing_metadata(self):
        """Test extraction with missing metadata."""
        agent = UploaderAgent()
        tags = {}
        assert agent._extract_focal_length(tags) is None
        assert agent._extract_aperture(tags) is None
        assert agent._extract_iso(tags) is None
        assert agent._extract_sensor_size(tags) is None


class TestValidationResult:
    """Tests for ValidationResult dataclass."""
    
    def test_valid_result(self):
        """Test valid validation result."""
        result = ValidationResult(
            is_valid=True,
            format="mp4",
            file_size_mb=100.0,
        )
        assert result.is_valid
        assert result.format == "mp4"
        assert result.error_message is None
    
    def test_invalid_result(self):
        """Test invalid validation result."""
        result = ValidationResult(
            is_valid=False,
            error_message="File not found",
        )
        assert not result.is_valid
        assert result.error_message == "File not found"
    
    def test_segmentation_info(self):
        """Test segmentation information."""
        result = ValidationResult(
            is_valid=True,
            format="mp4",
            needs_segmentation=True,
            segment_count=5,
        )
        assert result.needs_segmentation
        assert result.segment_count == 5
