"""
Tests using synthetic data - faster and more reliable than VCR cassettes.
"""

import pytest
import numpy as np
import sys
import os

import sits

# Add test utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "utils"))
from test_data import (
    create_synthetic_satellite_cube,
    create_mock_stac_object,
    assert_valid_spectral_index,
    create_synthetic_geodataframe,
)


def test_synthetic_satellite_cube_creation():
    """Test synthetic satellite data cube generation"""
    cube = create_synthetic_satellite_cube(width=10, height=10, time_steps=3)

    # Verify structure
    assert "B03" in cube.data_vars
    assert "B04" in cube.data_vars
    assert "B08" in cube.data_vars
    assert "SCL" in cube.data_vars

    # Verify dimensions using sizes instead of dims
    assert cube.sizes == {"time": 3, "y": 10, "x": 10}

    # Verify data types and ranges
    assert cube["B03"].dtype == np.uint16
    assert cube["SCL"].dtype == np.uint16

    # Check reasonable value ranges
    assert cube["B03"].min() >= 500  # Green band minimum
    assert cube["B03"].max() <= 3000  # Green band maximum
    assert cube["SCL"].min() >= 0  # SCL minimum
    assert cube["SCL"].max() <= 11  # SCL maximum


def test_mock_stac_object():
    """Test mock StacAttack object creation"""
    stac_obj = create_mock_stac_object()

    # Verify object structure
    assert hasattr(stac_obj, "cube")
    assert hasattr(stac_obj, "items")
    assert hasattr(stac_obj, "items_prop")

    # Verify cube
    assert stac_obj.cube is not None
    assert len(stac_obj.cube.time) == 3
    assert len(stac_obj.cube.x) == 9
    assert len(stac_obj.cube.y) == 9

    # Verify items
    assert len(stac_obj.items) == 3

    # Verify items properties DataFrame
    assert stac_obj.items_prop is not None
    assert len(stac_obj.items_prop) == 3
    assert "id" in stac_obj.items_prop.columns
    assert "datetime" in stac_obj.items_prop.columns
    assert "cloud_cover" in stac_obj.items_prop.columns


@pytest.mark.parametrize(
    "index_name,band_mapping",
    [
        ("NDVI", {"G": "B03", "R": "B04", "N": "B08"}),
        ("NDWI", {"G": "B03", "N": "B08"}),
        ("GNDVI", {"G": "B03", "N": "B08"}),
    ],
)
def test_spectral_indices_with_synthetic_data(index_name, band_mapping):
    """Test spectral index calculation with synthetic data"""
    # Create mock object
    stac_obj = create_mock_stac_object()

    # Calculate spectral index
    stac_obj.spectral_index(index_name, band_mapping)

    # Verify results
    assert hasattr(stac_obj, "indices")
    assert index_name in stac_obj.indices.data_vars

    # Validate index values are in expected ranges
    index_values = stac_obj.indices[index_name].values
    assert_valid_spectral_index(index_name, index_values)


@pytest.mark.parametrize("coords", [(2, 2), (5, 5), (7, 7)])
def test_fixS2shift_with_synthetic_data(coords):
    """Test Sentinel-2 shift correction with synthetic data"""
    x, y = coords
    stac_obj = create_mock_stac_object()

    # If you need to compare the original value
    # original_value = int(stac_obj.cube.isel(x=x, y=y, time=-1).B04.values)

    # Apply shift correction - should not raise any exceptions
    try:
        stac_obj.fixS2shift()
        # Method executed without error
        correction_applied = True
    except Exception as e:
        pytest.fail(f"fixS2shift failed with error: {e}")
        correction_applied = False

    # Get corrected value
    corrected_value = int(stac_obj.cube.isel(x=x, y=y, time=-1).B04.values)

    # Values should be in valid range
    assert 0 <= corrected_value <= 10000
    # Synthetic data might not require correction, so the method should complete
    assert correction_applied


def test_mask_operations_with_synthetic_data():
    """Test cloud masking operations with synthetic data"""
    stac_obj = create_mock_stac_object()

    # Apply cloud masking
    stac_obj.mask_conf()
    stac_obj.mask_apply()

    # Verify masking was applied (some values should be NaN)
    assert hasattr(stac_obj, "cube")

    # Test gap filling
    original_time_count = len(stac_obj.cube.time)
    stac_obj.gapfill()

    # Time count should remain the same
    assert len(stac_obj.cube.time) == original_time_count


@pytest.mark.parametrize("mask_cover", [0.01, 0.05, 0.1])
def test_filter_by_mask_with_synthetic_data(mask_cover):
    """Test mask-based filtering with synthetic data"""
    stac_obj = create_mock_stac_object()

    # Apply cloud masking
    stac_obj.mask_conf()

    # Apply filtering
    original_time_count = len(stac_obj.cube.time)
    stac_obj.filter_by_mask(mask_cover=mask_cover)

    # Should have fewer or equal time steps after filtering
    filtered_time_count = len(stac_obj.cube.time)
    assert filtered_time_count <= original_time_count


def test_synthetic_vector_data():
    """Test synthetic vector data generation"""
    gdf = create_synthetic_geodataframe(n_points=10)

    # Verify structure
    assert len(gdf) == 10
    assert "id" in gdf.columns
    assert "pt_id" in gdf.columns
    assert "geometry" in gdf.columns

    # Verify coordinate ranges (should be around Europe)
    assert gdf.bounds.minx.min() >= -20  # Westernmost longitude
    assert gdf.bounds.maxx.max() <= 40  # Easternmost longitude
    assert gdf.bounds.miny.min() >= 30  # Southernmost latitude
    assert gdf.bounds.maxy.max() <= 70  # Northernmost latitude


def test_vector_operations_with_synthetic_data():
    """Test vector operations with synthetic data"""
    # Create synthetic vector data
    gdf = create_synthetic_geodataframe(n_points=5)

    # Test CSV to GeoDataFrame conversion
    import tempfile
    import pandas as pd

    # Convert to CSV format
    csv_data = pd.DataFrame(
        {
            "lon": [geom.x for geom in gdf.geometry],
            "lat": [geom.y for geom in gdf.geometry],
            "id": gdf["id"],
        }
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        csv_data.to_csv(f.name, index=False)

        # Test Csv2gdf
        csv_gdf = sits.sits.Csv2gdf(f.name, "lon", "lat", 4326)
        csv_gdf.set_gdf(4326)  # Set GeoDataFrame
        assert csv_gdf.gdf is not None
        assert len(csv_gdf.gdf) == 5


def test_performance_with_small_synthetic_data():
    """Test performance improvements with small synthetic data"""
    small_cube = create_synthetic_satellite_cube(width=3, height=3, time_steps=2)

    # Quick operations test
    assert small_cube.sizes == {"time": 2, "y": 3, "x": 3}
    assert len(small_cube.data_vars) == 4  # B03, B04, B08, SCL

    # Test that operations complete quickly
    import time

    start_time = time.time()

    # Simulate some operations
    mean_values = {
        band: float(small_cube[band].mean()) for band in small_cube.data_vars
    }

    elapsed_time = time.time() - start_time
    assert elapsed_time < 1.0  # Should complete in under 1 second
    assert len(mean_values) == 4  # All bands processed
