from sits import sits
import numpy as np
from datetime import datetime
import pytest


# parameters
bbox_4326 = [5.81368624750606, 48.176553908146694,
             5.833686247506059, 48.19655390814669]
bbox_3035 = [4010426.347893443, 2794557.087497158,
             4010587.1105397893, 2794787.4926693346]


@pytest.fixture(scope="module")
def sitsStac():
    stacObj = sits.StacAttack(provider='mpc',
                              collection='sentinel-2-l2a',
                              bands=['B03', 'B04', 'B08', 'SCL'])
    stacObj.searchItems(bbox_4326,
                        date_start=datetime(2018, 1, 1),
                        date_end=datetime(2024, 1, 1),
                        query={"eo:cloud_cover": {"lt": 10}})
    stacObj.loadCube(bbox_3035, crs_out=3035)
    return stacObj


def test_StacAttack(sitsStac):
    """test of StacAttack class instanciation
    """
    assert sitsStac.items[0].id == 'S2B_MSIL2A_20231203T104319_R008_T31UGP_20231203T132848'


def test_fixS2shift(sitsStac):
    """test of StacAttack.fixS2shift() method
    """
    assert int(sitsStac.cube.isel(x=10, y=10, time=-1).B04.values) == 1422
    sitsStac.fixS2shift()
    assert int(sitsStac.cube.isel(x=10, y=10, time=-1).B04.values) == 422


def test_gapfill(sitsStac):
    """test of StacAttack.gapfill() method
    """
    sitsStac.mask()
    sitsStac.mask_apply()
    assert np.isnan(sitsStac.cube.isel(x=10,
                                       y=10,
                                       time=71).B04.values)
    sitsStac.gapfill()

    assert float(sitsStac.cube.isel(x=10,
                                    y=10,
                                    time=71).B04.values) == 131.0


def test_filter_by_mask(sitsStac):
    """test of StacAttack.filter_by_mask() method
    """
    assert len(sitsStac.cube.time) == 209
    sitsStac.filter_by_mask(mask_cover=0.05)
    assert len(sitsStac.cube.time) == 201


def test_spectral_index(sitsStac):
    """test of StacAttack.spectral_index() method
    """
    indices_to_compute = 'NDVI'
    band_mapping = {'G': 'B03', 'R': 'B04', 'N': 'B08'}
    sitsStac.spectral_index(indices_to_compute, band_mapping)
    assert float(sitsStac.indices.NDVI.isel(x=10,
                                            y=10,
                                            time=72).values) == 0.625