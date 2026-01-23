from importlib.resources import files
import pytest
from sits import sits


def load_geojson():
    """load sits data"""
    # Access the file inside .../data/file.geojson
    filename1 = files("sits.data").joinpath("banc_arguin.geojson")
    filename2 = files("sits.data").joinpath("rand_pts.geojson")
    return filename1, filename2


def test_Vec2gdf():
    """test of Vec2gdf class"""
    filename1, filename2 = load_geojson()
    v_layer = sits.Vec2gdf(filename1)
    assert v_layer.gdf.crs.to_epsg() == 4326


def test_set_bbox():
    """test of Vec2gdf.set_bbox() method"""
    filename1, filename2 = load_geojson()
    v_layer = sits.Vec2gdf(filename1)  # os.path.join(in_dir, filename1))
    v_layer.set_bbox("gdf")
    bbox_4326 = list(v_layer.bbox.iloc[0]["geometry"].bounds)
    bbox_3035 = list(v_layer.bbox.to_crs(3035).iloc[0]["geometry"].bounds)
    assert bbox_4326 == [
        -1.283356958716803,
        44.54723753300113,
        -1.195282436226136,
        44.63147049370678,
    ]
    assert bbox_3035 == [
        3426472.0201418595,
        2448438.7064564982,
        3434719.22278734,
        2458751.114093349,
    ]


@pytest.mark.parametrize("buffer_size", [0.001, 0.01, 0.1])
def test_set_buffer(buffer_size):
    """test of Vec2gdf.set_buffer() method with different buffer sizes"""
    filename1, filename2 = load_geojson()
    v_layer = sits.Vec2gdf(filename2)
    v_layer.set_buffer("gdf", buffer_size)
    v_layer.set_bbox("buffer")

    # Check that buffering was applied (buffer should increase area)
    original_geom = v_layer.gdf.loc[v_layer.gdf["id"] == 35, "geometry"].values[0]
    buffered_geom = v_layer.buffer.loc[v_layer.buffer["id"] == 35, "geometry"].values[0]

    # Buffered geometry should have larger area
    assert buffered_geom.area > original_geom.area
