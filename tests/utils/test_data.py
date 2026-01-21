"""
Test utilities for generating synthetic satellite data and test objects.
"""
import numpy as np
import xarray as xr
import pandas as pd
from datetime import datetime, timedelta
from sits import sits


def create_synthetic_satellite_cube(
    width=10, 
    height=10, 
    time_steps=3, 
    bands=None,
    crs="EPSG:3035",
    start_date=datetime(2023, 1, 1)
):
    """
    Create a synthetic satellite data cube for testing.
    
    Args:
        width: Width of the cube in pixels
        height: Height of the cube in pixels  
        time_steps: Number of time steps
        bands: List of band names (default: ['B03', 'B04', 'B08', 'SCL'])
        crs: Coordinate reference system
        start_date: Starting date for time dimension
    
    Returns:
        xarray.Dataset with synthetic satellite data
    """
    if bands is None:
        bands = ['B03', 'B04', 'B08', 'SCL']
    
    # Create coordinates
    x_coords = np.linspace(4010426, 4010426 + width * 10, width)
    y_coords = np.linspace(2794557, 2794557 + height * 10, height)
    time_coords = [start_date + timedelta(days=i*10) for i in range(time_steps)]
    
    # Create data arrays for each band
    data_vars = {}
    
    for band in bands:
        if band == 'SCL':  # Scene Classification Layer
            # Generate classification values (0-11)
            data = np.random.randint(0, 12, (time_steps, height, width), dtype=np.uint16)
        else:  # Spectral bands
            # Generate realistic reflectance values (scaled to 0-10000 range)
            if band == 'B03':  # Green
                data = np.random.randint(500, 3000, (time_steps, height, width), dtype=np.uint16)
            elif band == 'B04':  # Red  
                data = np.random.randint(300, 2500, (time_steps, height, width), dtype=np.uint16)
            elif band == 'B08':  # NIR
                data = np.random.randint(1000, 6000, (time_steps, height, width), dtype=np.uint16)
            else:
                data = np.random.randint(100, 8000, (time_steps, height, width), dtype=np.uint16)
        
        data_vars[band] = xr.DataArray(
            data,
            dims=['time', 'y', 'x'],
            coords={
                'time': time_coords,
                'y': y_coords,
                'x': x_coords
            },
            attrs={'long_name': f'Synthetic {band} band'}
        )
    
    # Create dataset
    ds = xr.Dataset(data_vars, attrs={'crs': crs})
    
    return ds


def create_synthetic_stac_items(n_items=3, collection='sentinel-2-l2a'):
    """
    Create synthetic STAC items for testing.
    
    Args:
        n_items: Number of STAC items to create
        collection: Collection name
    
    Returns:
        List of STAC-like item objects with properties attribute
    """
    class MockSTACItem:
        def __init__(self, item_dict):
            self.__dict__.update(item_dict)
            self.properties = item_dict['properties']
            self.datetime = datetime.fromisoformat(item_dict['datetime'].replace('Z', ''))
            self.id = item_dict['id']
        
        def __iter__(self):
            """Make the MockSTACItem iterable for compatibility"""
            return iter([self])
    
    items = []
    base_date = datetime(2023, 2, 20)
    
    for i in range(n_items):
        item_dict = {
            'id': f'S2A_MSIL2A_{base_date.strftime("%Y%m%dT%H%M%S")}_R008_T31UGP_{(base_date + timedelta(days=6)).strftime("%Y%m%dT%H%M%S")}',
            'collection': collection,
            'datetime': (base_date + timedelta(days=i*10)).isoformat() + 'Z',
            'bbox': [5.81368624750606, 48.176553908146694, 5.823686247506059, 48.18655390814669],
            'geometry': {
                'type': 'Polygon',
                'coordinates': [[
                    [5.81368624750606, 48.176553908146694],
                    [5.823686247506059, 48.176553908146694],
                    [5.823686247506059, 48.18655390814669],
                    [5.81368624750606, 48.18655390814669],
                    [5.81368624750606, 48.176553908146694]
                ]]
            },
            'properties': {
                'eo:cloud_cover': np.random.uniform(0, 15),
                'sentinel:tile_id': '31UGP',
                'sentinel:product_type': 'S2MSI2A',
                's2:processing_baseline': 4.0  # For fixS2shift compatibility
            }
        }
        items.append(MockSTACItem(item_dict))
    
    return items


def create_mock_stac_object():
    """
    Create a mock StacAttack object with synthetic data for testing.
    
    Returns:
        StacAttack object with synthetic satellite data
    """
    # Create object with valid provider
    stac_obj = sits.StacAttack(provider='mpc', collection='sentinel-2-l2a', bands=['B03', 'B04', 'B08', 'SCL'])
    
    # Set synthetic data directly (bypassing STAC loading)
    stac_obj.cube = create_synthetic_satellite_cube(width=9, height=9, time_steps=3)
    stac_obj.items = create_synthetic_stac_items()
    
    # Create synthetic items properties DataFrame
    items_data = []
    for item in stac_obj.items:
        items_data.append({
                'id': item.id,
                'datetime': item.datetime,
                'cloud_cover': item.properties['eo:cloud_cover']
            })
    stac_obj.items_prop = pd.DataFrame(items_data)
    
    return stac_obj


def create_synthetic_geodataframe(n_points=10, crs="EPSG:4326"):
    """
    Create synthetic GeoDataFrame for testing vector operations.
    
    Args:
        n_points: Number of point features to create
        crs: Coordinate reference system
    
    Returns:
        GeoDataFrame with synthetic point data
    """
    import geopandas as gpd
    from shapely.geometry import Point
    
    # Generate random points around Europe
    np.random.seed(42)  # For reproducible tests
    lons = np.random.uniform(-10, 30, n_points)
    lats = np.random.uniform(35, 65, n_points)
    
    geometries = [Point(lon, lat) for lon, lat in zip(lons, lats)]
    
    gdf = gpd.GeoDataFrame({
        'id': range(1, n_points + 1),
        'pt_id': range(1, n_points + 1),
        'geometry': geometries
    }, crs=crs)
    
    return gdf


def validate_spectral_index_values(index_name, index_values):
    """
    Validate that spectral index values are in expected ranges.
    
    Args:
        index_name: Name of the spectral index
        index_values: Array-like of index values
    
    Returns:
        bool: True if values are valid for the index type
    """
    index_values = np.array(index_values)
    
    # Remove NaN values for validation
    valid_values = index_values[~np.isnan(index_values)]
    
    if len(valid_values) == 0:
        return True  # All NaN is valid for masked areas
    
    if index_name in ['NDVI', 'NDWI', 'EVI', 'GNDVI']:
        # Vegetation/water indices should be in [-1, 1]
        return np.all((valid_values >= -1.0) & (valid_values <= 1.0))
    elif index_name in ['NBR', 'NBR2']:
        # Burn indices should be in [-1, 1]
        return np.all((valid_values >= -1.0) & (valid_values <= 1.0))
    else:
        # Generic check - values should be reasonable
        return np.all(np.abs(valid_values) <= 10)  # Allow some flexibility


def assert_valid_spectral_index(index_name, index_values):
    """
    Assert that spectral index values are valid.
    
    Args:
        index_name: Name of the spectral index
        index_values: Array-like of index values
    
    Raises:
        AssertionError: If values are invalid
    """
    index_values = np.array(index_values)
    valid_values = index_values[~np.isnan(index_values)]
    
    if len(valid_values) > 0:
        assert validate_spectral_index_values(index_name, valid_values), \
            f"Spectral index '{index_name}' has invalid values: min={valid_values.min()}, max={valid_values.max()}"