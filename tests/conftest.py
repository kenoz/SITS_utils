import pytest
import vcr
import sys
import os

# Add test utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "utils"))
from test_data import (
    create_synthetic_satellite_cube,
    create_mock_stac_object,
    create_synthetic_geodataframe,
)


@pytest.fixture(scope="module")
def vcr_cassette_dir(request):
    # put cassettes in a subdirectory of the test file's directory
    return request.module.__file__.rsplit("/", 1)[0] + "/cassettes"


@pytest.fixture(scope="module")
def stac_vcr(vcr_cassette_dir):
    return vcr.VCR(
        cassette_library_dir=vcr_cassette_dir,
        record_mode="all",  # Record once, then replay
        match_on=["uri", "method"],
    )


@pytest.fixture(scope="function")
def synthetic_satellite_data():
    """Create synthetic satellite data cube for testing"""
    return create_synthetic_satellite_cube(width=9, height=9, time_steps=3)


@pytest.fixture(scope="function")
def mock_stac_object():
    """Create mock StacAttack object with synthetic data"""
    return create_mock_stac_object()


@pytest.fixture(scope="function")
def synthetic_vector_data():
    """Create synthetic GeoDataFrame for testing"""
    return create_synthetic_geodataframe(n_points=5)


@pytest.fixture(scope="function")
def small_satellite_cube():
    """Create small satellite cube for performance testing"""
    return create_synthetic_satellite_cube(width=5, height=5, time_steps=2)
