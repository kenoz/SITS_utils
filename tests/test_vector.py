from sits import sits
import os

# parameters
in_dir = '../data'
filename1 = 'banc_arguin.geojson'
filename2 = 'rand_pts.geojson'

def test_Vec2gdf():
    v_layer = sits.Vec2gdf(os.path.join(in_dir, filename1))
    assert v_layer.gdf.crs.to_epsg() == 4326


def test_set_bbox():
    v_layer = sits.Vec2gdf(os.path.join(in_dir, filename1))
    v_layer.set_bbox('gdf')
    bbox_4326 = list(v_layer.bbox.iloc[0]['geometry'].bounds)
    bbox_3035 = list(v_layer.bbox.to_crs(3035).iloc[0]['geometry'].bounds)
    assert bbox_4326 == [-1.283356958716803, 44.54723753300113,
                         -1.195282436226136, 44.63147049370678]
    assert bbox_3035 == [3426472.0201418595, 2448438.7064564982,
                         3434719.22278734, 2458751.114093349]

def test_set_buffer():
    v_layer = sits.Vec2gdf(os.path.join(in_dir, filename2))
    v_layer.set_buffer('gdf', 0.01)
    v_layer.set_bbox('buffer')
    geom = v_layer.bbox.loc[v_layer.bbox['id'] == 35, 'geometry'].values[0]
    bounds = list(geom.bounds)
    assert bounds == [5.81368624750606, 48.176553908146694, 
                      5.833686247506059, 48.19655390814669]
    


if __name__ == "__main__":
    print("testing vector functions...")
    test_Vec2gdf()
    test_set_bbox()