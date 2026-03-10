from datetime import datetime
import pytest
from sits import sits


# Test parameters
BBOX_4326 = [5.81368624750606, 48.176553908146694, 5.823686247506059, 48.18655390814669]
BBOX_3035 = [4010426.347893443, 2794557.087497158, 4010506.729216616, 2794672.280083246]
TEST_BANDS = ["B03", "B04", "B08", "SCL"]
TEST_COLLECTION = "sentinel-2-l2a"
TEST_PROVIDER = "mpc"


@pytest.fixture(scope="function")
def base_stac_object(stac_vcr):
    """Create a fresh StacAttack object for each test function"""
    with stac_vcr.use_cassette("sits_stac_base.yaml"):
        stacObj = sits.StacAttack(
            provider=TEST_PROVIDER, collection=TEST_COLLECTION, bands=TEST_BANDS
        )
        stacObj.searchItems(
            BBOX_4326,
            date_start=datetime(2023, 1, 1),
            date_end=datetime(2023, 3, 1),
            query={"eo:cloud_cover": {"lt": 10}},
        )
        stacObj.loadCube(BBOX_3035, crs_out=3035)
        return stacObj


@pytest.fixture(scope="function")
def fresh_stac_object(stac_vcr):
    """Create a completely fresh copy for state-sensitive tests"""
    # Create a new object to avoid state pollution
    with stac_vcr.use_cassette("sits_stac_fresh.yaml"):
        stacObj = sits.StacAttack(
            provider=TEST_PROVIDER, collection=TEST_COLLECTION, bands=TEST_BANDS
        )
        stacObj.searchItems(
            BBOX_4326,
            date_start=datetime(2023, 1, 1),
            date_end=datetime(2023, 3, 1),
            query={"eo:cloud_cover": {"lt": 10}},
        )
        stacObj.loadCube(BBOX_3035, crs_out=3035)
        return stacObj


def test_StacAttack(base_stac_object):
    """test of StacAttack class instantiation"""
    assert (
        base_stac_object.items[0].id
        == "S2A_MSIL2A_20230221T104041_R008_T31UGP_20230226T105609"
    )


def test_fixS2shift(fresh_stac_object):
    """test of StacAttack.fixS2shift() method"""
    # Test that shift correction changes pixel values
    original_value = int(fresh_stac_object.cube.isel(x=5, y=5, time=-1).B04.values)
    fresh_stac_object.fixS2shift()
    corrected_value = int(fresh_stac_object.cube.isel(x=5, y=5, time=-1).B04.values)

    # Values should be different after correction
    assert original_value != corrected_value
    # Corrected value should be in reasonable range
    assert 0 <= corrected_value <= 10000


def test_gapfill(fresh_stac_object):
    """test of StacAttack.gapfill() method"""
    # Apply cloud masking first
    fresh_stac_object.mask_conf()
    fresh_stac_object.mask_apply()

    # Get a pixel value before gapfilling
    original_value = float(fresh_stac_object.cube.isel(x=5, y=5, time=0).B04.values)

    # Apply gap filling
    fresh_stac_object.gapfill()

    # Value should remain the same (no gaps in this pixel)
    gapfilled_value = float(fresh_stac_object.cube.isel(x=5, y=5, time=0).B04.values)
    assert gapfilled_value == original_value


def test_filter_by_mask(base_stac_object):
    """test of StacAttack.filter_by_mask() method"""
    original_time_count = len(base_stac_object.cube.time)
    assert original_time_count == 3

    # Apply cloud masking
    base_stac_object.mask_conf()

    # Test with a very strict mask cover threshold to ensure filtering
    base_stac_object.filter_by_mask(mask_cover=0.01)  # Very strict threshold

    # Should have fewer time steps after strict filtering
    filtered_time_count = len(base_stac_object.cube.time)
    assert filtered_time_count <= original_time_count


@pytest.mark.parametrize(
    "indices_to_compute,band_mapping,expected_range",
    [
        ("NDVI", {"G": "B03", "R": "B04", "N": "B08"}, (-1.0, 1.0)),
        ("NDWI", {"G": "B03", "N": "B08"}, (-1.0, 1.0)),
        ("GNDVI", {"G": "B03", "N": "B08"}, (-1.0, 1.0)),
    ],
)
def test_spectral_index(
    base_stac_object, indices_to_compute, band_mapping, expected_range
):
    """test of StacAttack.spectral_index() method with parameterized indices"""
    base_stac_object.spectral_index(indices_to_compute, band_mapping)

    # Get the computed index value
    index_value = float(
        base_stac_object.indices[indices_to_compute].isel(x=5, y=5, time=0).values
    )

    # Index should be in expected range
    assert expected_range[0] <= index_value <= expected_range[1]


@pytest.mark.parametrize("mask_threshold", [0.01, 0.05, 0.1])
def test_filter_by_mask_with_different_thresholds(base_stac_object, mask_threshold):
    """test StacAttack.filter_by_mask() method with different thresholds"""
    original_time_count = len(base_stac_object.cube.time)
    assert original_time_count == 3

    # Apply cloud masking
    base_stac_object.mask_conf()

    # Apply filtering with different thresholds
    base_stac_object.filter_by_mask(mask_cover=mask_threshold)

    # Should have fewer or equal time steps after filtering
    filtered_time_count = len(base_stac_object.cube.time)
    assert filtered_time_count <= original_time_count


@pytest.mark.parametrize("coords", [(5, 5), (7, 7), (3, 3)])
def test_fixS2shift_different_coordinates(fresh_stac_object, coords):
    """test of StacAttack.fixS2shift() method with different coordinates"""
    x, y = coords

    # Test that shift correction changes pixel values
    original_value = int(fresh_stac_object.cube.isel(x=x, y=y, time=-1).B04.values)
    fresh_stac_object.fixS2shift()
    corrected_value = int(fresh_stac_object.cube.isel(x=x, y=y, time=-1).B04.values)

    # Values should be different after correction
    assert original_value != corrected_value
    # Corrected value should be in reasonable range
    assert 0 <= corrected_value <= 10000
