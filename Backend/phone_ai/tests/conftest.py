"""
Pytest configuration and fixtures.
"""
import pytest
from hypothesis import settings as hypothesis_settings, Verbosity


# Configure Hypothesis for property-based testing
hypothesis_settings.register_profile(
    "default",
    max_examples=100,
    deadline=5000,
    verbosity=Verbosity.normal,
)

hypothesis_settings.register_profile(
    "ci",
    max_examples=200,
    deadline=10000,
    verbosity=Verbosity.verbose,
)

hypothesis_settings.register_profile(
    "dev",
    max_examples=10,
    deadline=None,
    verbosity=Verbosity.verbose,
)

hypothesis_settings.load_profile("default")


@pytest.fixture
def sample_video_params():
    """Sample video parameters for testing."""
    return {
        "video_id": "test-video-001",
        "fps": 30.0,
        "duration_s": 60.0,
        "resolution": (1920, 1080),
    }


@pytest.fixture
def sample_bbox():
    """Sample bounding box for testing."""
    from src.models.data_types import BBox
    return BBox(x=0.1, y=0.2, w=0.3, h=0.4)


@pytest.fixture
def sample_exif_data():
    """Sample EXIF data for testing."""
    from src.models.data_types import ExifData
    return ExifData(
        focal_length_mm=50.0,
        aperture=2.8,
        sensor_size="full-frame",
        iso=400,
    )


@pytest.fixture
def sample_heuristic_output():
    """Sample heuristic output for testing."""
    from src.models.data_types import HeuristicOutput
    return HeuristicOutput(
        video_id="test-video-001",
        time_range=(0.0, 10.0),
        avg_motion_px_per_s=50.0,
        frame_pct_change=0.15,
        motion_smoothness=0.75,
        subject_occupancy=0.35,
        beat_alignment_score=0.8,
    )
