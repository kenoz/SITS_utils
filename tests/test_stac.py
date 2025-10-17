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
    assert sitsStac.items[0].id == 'S2B_MSIL2A_20231203T104319_R008_T31UGP_20231203T132848'


def test_fixS2shift(sitsStac):
    assert int(sitsStac.cube.isel(x=10, y=10, time=-1).B04.values) == 1422
    sitsStac.fixS2shift()
    assert int(sitsStac.cube.isel(x=10, y=10, time=-1).B04.values) == 422
    """
    sitsStac.cube = sitsStac.cube.isel(x=10, y=10)
    assert int(sitsStac.cube.isel(time=-1).B04.values) == 1422
    sitsStac.fixS2shift()
    assert int(sitsStac.cube.isel(time=-1).B04.values) == 422
    """


def test_filter_by_mask(sitsStac):
    sitsStac.mask()
    assert len(sitsStac.cube.time) == 209
    sitsStac.filter_by_mask(mask_cover=0.05)
    assert len(sitsStac.cube.time) == 201

    
"""
def test_gapfill(sitsStac):
    sitsStac.mask()
    sitsStac.mask_apply()
    assert np.isnan(sitsStac.cube.isel(x=100,
                                       y=100,
                                       time=25).B04.values) is True
    sitsStac.gapfill()

    float(sitsStac.cube.isel(x=100,
                             y=100,
                             time=25).B04.values) == 269.

"""


    
if __name__ == "__main__":
    print("testing StacAttack class...")