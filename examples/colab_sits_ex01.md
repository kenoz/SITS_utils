# **Example of use of SITS Package - The basics**

---

We aim to follow the **geomorphological evolution** of the **Banc d'Arguin**.

> _"The Banc d'Arguin is a sandbank about 4 km long and 2 km wide at low tide. The bank is more or less visible depending on the state of the tide. In addition, under the action of sea currents, tides and wind, it continually changes shape and location. It is located opposite the entrance to the Arcachon basin, between the Dune du Pilat and the tip of Cap Ferret"_ (source: [wikipedia](https://fr.wikipedia.org/wiki/R%C3%A9serve_naturelle_nationale_du_Banc-d%27Arguin)).

<p align="center"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Parc_naturel_marin_du_bassin_d%27Arcachon_vu_du_ciel_-_Banc_d%27Arguin_%281%29.JPG/1280px-Parc_naturel_marin_du_bassin_d%27Arcachon_vu_du_ciel_-_Banc_d%27Arguin_%281%29.JPG" alt="Banc d'Arguin" width="600"></p>
<p align="center"><sup>Arcachon Basin Marine Natural Park seen from the sky, from a light aircraft Tecnam P2002 (&copy; Dorian Bentejac)</sup></p>
We have a vector file that gives the position of this sandy shape. We will use it to retrieve a time series of satellite images, i.e. Sentinel-2, made available through a STAC catalog (i.e. Microsoft Planetary).
Then we will apply a cloud mask on each frame and replace the nodata values by temporal interpolation (i.e. gap-filling).
Finally we will export the results in the form of animated gif.

---

### 1. Installation of SITS package and its depedencies

First, install `sits` package with [pip](https://pypi.org/project/SITS/). We also need some other packages for displaying data.


```python
# SITS package
!pip install --upgrade sits

# other packages
!pip install folium
!pip install mapclassify
!pip install matplotlib
```

Now we can import `sits` and some other libraries.


```python
import os
# sits lib
import sits
# geospatial libs
import geopandas as gpd
import pandas as pd
# date format
from datetime import datetime
# ignore warnings messages
import warnings
warnings.filterwarnings('ignore') 
```

## 2. Handling the input vector file

### 2.1. Data loading

The geojson vector file describing the position of the sandbank is stored in the [Github repository](https://github.com/kenoz/SITS_utils). We download it into our current workspace.  


```python
!mkdir -p test_data
![ ! -f test_data/banc_arguin.geojson ] && wget https://raw.githubusercontent.com/kenoz/SITS_utils/refs/heads/main/data/banc_arguin.geojson -P test_data
```

    --2025-01-28 10:50:28--  https://raw.githubusercontent.com/kenoz/SITS_utils/refs/heads/main/data/banc_arguin.geojson
    Resolving proxy.cidsn.jrc.it (proxy.cidsn.jrc.it)... 139.191.240.208
    Connecting to proxy.cidsn.jrc.it (proxy.cidsn.jrc.it)|139.191.240.208|:8888... connected.
    Proxy request sent, awaiting response... 200 OK
    Length: 512 [text/plain]
    Saving to: ‘test_data/banc_arguin.geojson’
    
    banc_arguin.geojson 100%[===================>]     512  --.-KB/s    in 0s      
    
    2025-01-28 10:50:29 (14.5 MB/s) - ‘test_data/banc_arguin.geojson’ saved [512/512]
    


We load the vector file, named `banc_arguin.geojson`, as a geoDataFrame object with the `sits` method: `sits.Vec2gdf()`.


```python
data_dir = 'test_data'
v_arguin = sits.Vec2gdf(os.path.join(data_dir, 'banc_arguin.geojson'))
v_arguin.gdf
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>id</th>
      <th>id_poly</th>
      <th>geometry</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>1</td>
      <td>MULTIPOLYGON (((-1.27422 44.63147, -1.19528 44...</td>
    </tr>
  </tbody>
</table>
</div>



### 2.1. Bounding box calculation

We check the coordinate reference system (CRS) and calculate the bounding box with the method `set_bbox()` of class `sits.Vec2gdf`.


```python
# check epsg
print(f"epsg code for 'v_arguin.gdf':  {v_arguin.gdf.crs.to_epsg()}")

# calculates the bounding box for each feature.
v_arguin.set_bbox('gdf')
print(f"epsg code for 'v_arguin.bbox': {v_arguin.bbox.crs.to_epsg()}")
```

    epsg code for 'v_arguin.gdf':  4326
    epsg code for 'v_arguin.bbox': 4326


We display the `sits.Vec2gdf` objects (`.gdf` and _in green_ `.bbox` _in blue_) on an interactive map.


```python
import folium

f = folium.Figure(height=300)
m = folium.Map(location=[44.6, -1.2], zoom_start=11).add_to(f)
v_arguin.gdf.explore(m=m, height=400, color='green')
v_arguin.bbox.explore(m=m, height=400)
```




<iframe srcdoc="&lt;!DOCTYPE html&gt;
&lt;html&gt;
&lt;head&gt;

    &lt;meta http-equiv=&quot;content-type&quot; content=&quot;text/html; charset=UTF-8&quot; /&gt;

        &lt;script&gt;
            L_NO_TOUCH = false;
            L_DISABLE_3D = false;
        &lt;/script&gt;

    &lt;style&gt;html, body {width: 100%;height: 100%;margin: 0;padding: 0;}&lt;/style&gt;
    &lt;style&gt;#map {position:absolute;top:0;bottom:0;right:0;left:0;}&lt;/style&gt;
    &lt;script src=&quot;https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.js&quot;&gt;&lt;/script&gt;
    &lt;script src=&quot;https://code.jquery.com/jquery-3.7.1.min.js&quot;&gt;&lt;/script&gt;
    &lt;script src=&quot;https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.bundle.min.js&quot;&gt;&lt;/script&gt;
    &lt;script src=&quot;https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.js&quot;&gt;&lt;/script&gt;
    &lt;link rel=&quot;stylesheet&quot; href=&quot;https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.css&quot;/&gt;
    &lt;link rel=&quot;stylesheet&quot; href=&quot;https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css&quot;/&gt;
    &lt;link rel=&quot;stylesheet&quot; href=&quot;https://netdna.bootstrapcdn.com/bootstrap/3.0.0/css/bootstrap.min.css&quot;/&gt;
    &lt;link rel=&quot;stylesheet&quot; href=&quot;https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.2.0/css/all.min.css&quot;/&gt;
    &lt;link rel=&quot;stylesheet&quot; href=&quot;https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.css&quot;/&gt;
    &lt;link rel=&quot;stylesheet&quot; href=&quot;https://cdn.jsdelivr.net/gh/python-visualization/folium/folium/templates/leaflet.awesome.rotate.min.css&quot;/&gt;

            &lt;meta name=&quot;viewport&quot; content=&quot;width=device-width,
                initial-scale=1.0, maximum-scale=1.0, user-scalable=no&quot; /&gt;
            &lt;style&gt;
                #map_1f13cbd28a5ef370203fd893a946aaa8 {
                    position: relative;
                    width: 100.0%;
                    height: 100.0%;
                    left: 0.0%;
                    top: 0.0%;
                }
                .leaflet-container { font-size: 1rem; }
            &lt;/style&gt;


                    &lt;style&gt;
                        .foliumtooltip {

                        }
                       .foliumtooltip table{
                            margin: auto;
                        }
                        .foliumtooltip tr{
                            text-align: left;
                        }
                        .foliumtooltip th{
                            padding: 2px; padding-right: 8px;
                        }
                    &lt;/style&gt;


                    &lt;style&gt;
                        .foliumtooltip {

                        }
                       .foliumtooltip table{
                            margin: auto;
                        }
                        .foliumtooltip tr{
                            text-align: left;
                        }
                        .foliumtooltip th{
                            padding: 2px; padding-right: 8px;
                        }
                    &lt;/style&gt;

&lt;/head&gt;
&lt;body&gt;


            &lt;div class=&quot;folium-map&quot; id=&quot;map_1f13cbd28a5ef370203fd893a946aaa8&quot; &gt;&lt;/div&gt;

&lt;/body&gt;
&lt;script&gt;


            var map_1f13cbd28a5ef370203fd893a946aaa8 = L.map(
                &quot;map_1f13cbd28a5ef370203fd893a946aaa8&quot;,
                {
                    center: [44.6, -1.2],
                    crs: L.CRS.EPSG3857,
                    zoom: 11,
                    zoomControl: true,
                    preferCanvas: false,
                }
            );





            var tile_layer_7f1074b465fba3c8d563ac583e968e55 = L.tileLayer(
                &quot;https://tile.openstreetmap.org/{z}/{x}/{y}.png&quot;,
                {&quot;attribution&quot;: &quot;\u0026copy; \u003ca href=\&quot;https://www.openstreetmap.org/copyright\&quot;\u003eOpenStreetMap\u003c/a\u003e contributors&quot;, &quot;detectRetina&quot;: false, &quot;maxNativeZoom&quot;: 19, &quot;maxZoom&quot;: 19, &quot;minZoom&quot;: 0, &quot;noWrap&quot;: false, &quot;opacity&quot;: 1, &quot;subdomains&quot;: &quot;abc&quot;, &quot;tms&quot;: false}
            );


            tile_layer_7f1074b465fba3c8d563ac583e968e55.addTo(map_1f13cbd28a5ef370203fd893a946aaa8);


        function geo_json_e67393144447d2f392c6e28a4c871402_styler(feature) {
            switch(feature.id) {
                default:
                    return {&quot;color&quot;: &quot;green&quot;, &quot;fillColor&quot;: &quot;green&quot;, &quot;fillOpacity&quot;: 0.5, &quot;weight&quot;: 2};
            }
        }
        function geo_json_e67393144447d2f392c6e28a4c871402_highlighter(feature) {
            switch(feature.id) {
                default:
                    return {&quot;fillOpacity&quot;: 0.75};
            }
        }
        function geo_json_e67393144447d2f392c6e28a4c871402_pointToLayer(feature, latlng) {
            var opts = {&quot;bubblingMouseEvents&quot;: true, &quot;color&quot;: &quot;#3388ff&quot;, &quot;dashArray&quot;: null, &quot;dashOffset&quot;: null, &quot;fill&quot;: true, &quot;fillColor&quot;: &quot;#3388ff&quot;, &quot;fillOpacity&quot;: 0.2, &quot;fillRule&quot;: &quot;evenodd&quot;, &quot;lineCap&quot;: &quot;round&quot;, &quot;lineJoin&quot;: &quot;round&quot;, &quot;opacity&quot;: 1.0, &quot;radius&quot;: 2, &quot;stroke&quot;: true, &quot;weight&quot;: 3};

            let style = geo_json_e67393144447d2f392c6e28a4c871402_styler(feature)
            Object.assign(opts, style)

            return new L.CircleMarker(latlng, opts)
        }

        function geo_json_e67393144447d2f392c6e28a4c871402_onEachFeature(feature, layer) {
            layer.on({
                mouseout: function(e) {
                    if(typeof e.target.setStyle === &quot;function&quot;){
                            geo_json_e67393144447d2f392c6e28a4c871402.resetStyle(e.target);
                    }
                },
                mouseover: function(e) {
                    if(typeof e.target.setStyle === &quot;function&quot;){
                        const highlightStyle = geo_json_e67393144447d2f392c6e28a4c871402_highlighter(e.target.feature)
                        e.target.setStyle(highlightStyle);
                    }
                },
            });
        };
        var geo_json_e67393144447d2f392c6e28a4c871402 = L.geoJson(null, {
                onEachFeature: geo_json_e67393144447d2f392c6e28a4c871402_onEachFeature,

                style: geo_json_e67393144447d2f392c6e28a4c871402_styler,
                pointToLayer: geo_json_e67393144447d2f392c6e28a4c871402_pointToLayer,
        });

        function geo_json_e67393144447d2f392c6e28a4c871402_add (data) {
            geo_json_e67393144447d2f392c6e28a4c871402
                .addData(data);
        }
            geo_json_e67393144447d2f392c6e28a4c871402_add({&quot;bbox&quot;: [-1.283356958716803, 44.54723753300113, -1.195282436226136, 44.63147049370678], &quot;features&quot;: [{&quot;bbox&quot;: [-1.283356958716803, 44.54723753300113, -1.195282436226136, 44.63147049370678], &quot;geometry&quot;: {&quot;coordinates&quot;: [[[[-1.274219544279732, 44.63147049370678], [-1.195282436226136, 44.6303867249064], [-1.200358777580065, 44.54723753300113], [-1.283356958716803, 44.54850373805724], [-1.274219544279732, 44.63147049370678]]]], &quot;type&quot;: &quot;MultiPolygon&quot;}, &quot;id&quot;: &quot;0&quot;, &quot;properties&quot;: {&quot;__folium_color&quot;: &quot;green&quot;, &quot;id&quot;: 1, &quot;id_poly&quot;: 1}, &quot;type&quot;: &quot;Feature&quot;}], &quot;type&quot;: &quot;FeatureCollection&quot;});



    geo_json_e67393144447d2f392c6e28a4c871402.bindTooltip(
    function(layer){
    let div = L.DomUtil.create(&#x27;div&#x27;);

    let handleObject = feature=&gt;typeof(feature)==&#x27;object&#x27; ? JSON.stringify(feature) : feature;
    let fields = [&quot;id&quot;, &quot;id_poly&quot;];
    let aliases = [&quot;id&quot;, &quot;id_poly&quot;];
    let table = &#x27;&lt;table&gt;&#x27; +
        String(
        fields.map(
        (v,i)=&gt;
        `&lt;tr&gt;
            &lt;th&gt;${aliases[i]}&lt;/th&gt;

            &lt;td&gt;${handleObject(layer.feature.properties[v])}&lt;/td&gt;
        &lt;/tr&gt;`).join(&#x27;&#x27;))
    +&#x27;&lt;/table&gt;&#x27;;
    div.innerHTML=table;

    return div
    }
    ,{&quot;className&quot;: &quot;foliumtooltip&quot;, &quot;sticky&quot;: true});


            geo_json_e67393144447d2f392c6e28a4c871402.addTo(map_1f13cbd28a5ef370203fd893a946aaa8);


        function geo_json_e848ed1be036a568aeb59e62c049d296_styler(feature) {
            switch(feature.id) {
                default:
                    return {&quot;fillOpacity&quot;: 0.5, &quot;weight&quot;: 2};
            }
        }
        function geo_json_e848ed1be036a568aeb59e62c049d296_highlighter(feature) {
            switch(feature.id) {
                default:
                    return {&quot;fillOpacity&quot;: 0.75};
            }
        }
        function geo_json_e848ed1be036a568aeb59e62c049d296_pointToLayer(feature, latlng) {
            var opts = {&quot;bubblingMouseEvents&quot;: true, &quot;color&quot;: &quot;#3388ff&quot;, &quot;dashArray&quot;: null, &quot;dashOffset&quot;: null, &quot;fill&quot;: true, &quot;fillColor&quot;: &quot;#3388ff&quot;, &quot;fillOpacity&quot;: 0.2, &quot;fillRule&quot;: &quot;evenodd&quot;, &quot;lineCap&quot;: &quot;round&quot;, &quot;lineJoin&quot;: &quot;round&quot;, &quot;opacity&quot;: 1.0, &quot;radius&quot;: 2, &quot;stroke&quot;: true, &quot;weight&quot;: 3};

            let style = geo_json_e848ed1be036a568aeb59e62c049d296_styler(feature)
            Object.assign(opts, style)

            return new L.CircleMarker(latlng, opts)
        }

        function geo_json_e848ed1be036a568aeb59e62c049d296_onEachFeature(feature, layer) {
            layer.on({
                mouseout: function(e) {
                    if(typeof e.target.setStyle === &quot;function&quot;){
                            geo_json_e848ed1be036a568aeb59e62c049d296.resetStyle(e.target);
                    }
                },
                mouseover: function(e) {
                    if(typeof e.target.setStyle === &quot;function&quot;){
                        const highlightStyle = geo_json_e848ed1be036a568aeb59e62c049d296_highlighter(e.target.feature)
                        e.target.setStyle(highlightStyle);
                    }
                },
            });
        };
        var geo_json_e848ed1be036a568aeb59e62c049d296 = L.geoJson(null, {
                onEachFeature: geo_json_e848ed1be036a568aeb59e62c049d296_onEachFeature,

                style: geo_json_e848ed1be036a568aeb59e62c049d296_styler,
                pointToLayer: geo_json_e848ed1be036a568aeb59e62c049d296_pointToLayer,
        });

        function geo_json_e848ed1be036a568aeb59e62c049d296_add (data) {
            geo_json_e848ed1be036a568aeb59e62c049d296
                .addData(data);
        }
            geo_json_e848ed1be036a568aeb59e62c049d296_add({&quot;bbox&quot;: [-1.283356958716803, 44.54723753300113, -1.195282436226136, 44.63147049370678], &quot;features&quot;: [{&quot;bbox&quot;: [-1.283356958716803, 44.54723753300113, -1.195282436226136, 44.63147049370678], &quot;geometry&quot;: {&quot;coordinates&quot;: [[[-1.195282436226136, 44.54723753300113], [-1.195282436226136, 44.63147049370678], [-1.283356958716803, 44.63147049370678], [-1.283356958716803, 44.54723753300113], [-1.195282436226136, 44.54723753300113]]], &quot;type&quot;: &quot;Polygon&quot;}, &quot;id&quot;: &quot;0&quot;, &quot;properties&quot;: {&quot;id&quot;: 1, &quot;id_poly&quot;: 1}, &quot;type&quot;: &quot;Feature&quot;}], &quot;type&quot;: &quot;FeatureCollection&quot;});



    geo_json_e848ed1be036a568aeb59e62c049d296.bindTooltip(
    function(layer){
    let div = L.DomUtil.create(&#x27;div&#x27;);

    let handleObject = feature=&gt;typeof(feature)==&#x27;object&#x27; ? JSON.stringify(feature) : feature;
    let fields = [&quot;id&quot;, &quot;id_poly&quot;];
    let aliases = [&quot;id&quot;, &quot;id_poly&quot;];
    let table = &#x27;&lt;table&gt;&#x27; +
        String(
        fields.map(
        (v,i)=&gt;
        `&lt;tr&gt;
            &lt;th&gt;${aliases[i]}&lt;/th&gt;

            &lt;td&gt;${handleObject(layer.feature.properties[v])}&lt;/td&gt;
        &lt;/tr&gt;`).join(&#x27;&#x27;))
    +&#x27;&lt;/table&gt;&#x27;;
    div.innerHTML=table;

    return div
    }
    ,{&quot;className&quot;: &quot;foliumtooltip&quot;, &quot;sticky&quot;: true});


            geo_json_e848ed1be036a568aeb59e62c049d296.addTo(map_1f13cbd28a5ef370203fd893a946aaa8);

&lt;/script&gt;
&lt;/html&gt;" width="100%" height="300"style="border:none !important;" "allowfullscreen" "webkitallowfullscreen" "mozallowfullscreen"></iframe>



### 2.3. CRS management

In order to request data on a STAC catalog, we need to provide the bounding box coordinates in Lat/Long, i.e the EPSG:4326. Then we also need to specify in which CRS we want to obtain the satellite time series. As we are working in France, it can be the EPSG 2154 (RGF-93, Lambert-93) or the EPSG 3035 (ETRS89-extended), valid at the European scale.

Here we calculate the coordinates in EPSG:4326 and EPSG:3035. Since there is only one polygon, we keep the coordinates into two lists.


```python
bbox_4326 = list(v_arguin.bbox.iloc[0]['geometry'].bounds)
bbox_3035 = list(v_arguin.bbox.to_crs(3035).iloc[0]['geometry'].bounds)

print(f'bbox in EPSG:4326: {bbox_4326}')
print(f'bbox in EPSG:3035: {bbox_3035}')
```

    bbox in EPSG:4326: [-1.283356958716803, 44.54723753300113, -1.195282436226136, 44.63147049370678]
    bbox in EPSG:3035: [3426472.0201418595, 2448438.7064564982, 3434719.22278734, 2458751.114093349]


## 3. Loading and preprocessing of a Satellite Image Time-Series (SITS)

In this example, we have only one area (one polygon) to process. We use the class `sits.StacAttack` to request and preprocess the data. In case you need to distribute the processing, take a look on the `sits.Multiproc()` approach, using `Dask`.

### 3.1. Creation of a Datacube from STAC catalog

The request consists in retrieving Sentinel-2 images (level 2A) acquired from January 1, 2016 to January 1, 2025 with cloud cover less than 10%. Then we build a 4 bands geo-datacube ('B03', 'B04', 'B08' and 'SCL') in EPSG:3035 with a 20m spatial resolution.


```python
# instance of the class sits.StacAttack()
ts_S2 = sits.StacAttack(provider='mpc',
                        collection='sentinel-2-l2a',
                        bands=['B03', 'B04', 'B08', 'SCL'])

# search of items based on bbox coordinates and time interval criteria
ts_S2.searchItems(bbox_4326,
                  date_start=datetime(2016, 1, 1),
                  date_end=datetime(2025, 1, 1),
                  query={"eo:cloud_cover": {"lt": 10}}
                 )
# load of the time series in a lazy way
ts_S2.loadCube(bbox_3035, resolution=20, crs_out=3035)
```

The method `StacAttack.loadCube()` returns an object `StacAttack.cube` i.e. an `xarray.Dataset()`. If necessary, you can modify it using the methods of `xarray.Dataset()` (not really recommended).


```python
type(ts_S2.cube)
```




    xarray.core.dataset.Dataset



### 3.2. Create and apply a mask

We want to mask the defective and cloudy pixels in the Datacube (`StacAttack.cube`). To do this, we use the SCL band provided with the Sentinel-2 images. SCL refers to "Scene Classification Layer" and has been developed to developed to distinguish between cloudy pixels, clear pixels and water pixels. It consists of 12 classes.

In this example we create a mask based on the following classes:
- 0: No Data (Missing data)
- 1: Saturated or defective pixel
- 3: Cloud shadows
- 8: Cloud medium probability
- 9: Cloud high probability
- 10: Thin cirrus




```python
# classes used to mask
SCL_mask = [0, 1, 3, 8, 9, 10]
# creation of the SCL mask
ts_S2.mask(mask_band='SCL', mask_values=[SCL_mask])
```

The method `StacAttack.mask()` returns an object `StacAttack.mask` i.e. an `xarray.Dataaarray()`.


```python
ts_S2.mask
```




<div><svg style="position: absolute; width: 0; height: 0; overflow: hidden">
<defs>
<symbol id="icon-database" viewBox="0 0 32 32">
<path d="M16 0c-8.837 0-16 2.239-16 5v4c0 2.761 7.163 5 16 5s16-2.239 16-5v-4c0-2.761-7.163-5-16-5z"></path>
<path d="M16 17c-8.837 0-16-2.239-16-5v6c0 2.761 7.163 5 16 5s16-2.239 16-5v-6c0 2.761-7.163 5-16 5z"></path>
<path d="M16 26c-8.837 0-16-2.239-16-5v6c0 2.761 7.163 5 16 5s16-2.239 16-5v-6c0 2.761-7.163 5-16 5z"></path>
</symbol>
<symbol id="icon-file-text2" viewBox="0 0 32 32">
<path d="M28.681 7.159c-0.694-0.947-1.662-2.053-2.724-3.116s-2.169-2.030-3.116-2.724c-1.612-1.182-2.393-1.319-2.841-1.319h-15.5c-1.378 0-2.5 1.121-2.5 2.5v27c0 1.378 1.122 2.5 2.5 2.5h23c1.378 0 2.5-1.122 2.5-2.5v-19.5c0-0.448-0.137-1.23-1.319-2.841zM24.543 5.457c0.959 0.959 1.712 1.825 2.268 2.543h-4.811v-4.811c0.718 0.556 1.584 1.309 2.543 2.268zM28 29.5c0 0.271-0.229 0.5-0.5 0.5h-23c-0.271 0-0.5-0.229-0.5-0.5v-27c0-0.271 0.229-0.5 0.5-0.5 0 0 15.499-0 15.5 0v7c0 0.552 0.448 1 1 1h7v19.5z"></path>
<path d="M23 26h-14c-0.552 0-1-0.448-1-1s0.448-1 1-1h14c0.552 0 1 0.448 1 1s-0.448 1-1 1z"></path>
<path d="M23 22h-14c-0.552 0-1-0.448-1-1s0.448-1 1-1h14c0.552 0 1 0.448 1 1s-0.448 1-1 1z"></path>
<path d="M23 18h-14c-0.552 0-1-0.448-1-1s0.448-1 1-1h14c0.552 0 1 0.448 1 1s-0.448 1-1 1z"></path>
</symbol>
</defs>
</svg>
<style>/* CSS stylesheet for displaying xarray objects in jupyterlab.
 *
 */

:root {
  --xr-font-color0: var(--jp-content-font-color0, rgba(0, 0, 0, 1));
  --xr-font-color2: var(--jp-content-font-color2, rgba(0, 0, 0, 0.54));
  --xr-font-color3: var(--jp-content-font-color3, rgba(0, 0, 0, 0.38));
  --xr-border-color: var(--jp-border-color2, #e0e0e0);
  --xr-disabled-color: var(--jp-layout-color3, #bdbdbd);
  --xr-background-color: var(--jp-layout-color0, white);
  --xr-background-color-row-even: var(--jp-layout-color1, white);
  --xr-background-color-row-odd: var(--jp-layout-color2, #eeeeee);
}

html[theme=dark],
body[data-theme=dark],
body.vscode-dark {
  --xr-font-color0: rgba(255, 255, 255, 1);
  --xr-font-color2: rgba(255, 255, 255, 0.54);
  --xr-font-color3: rgba(255, 255, 255, 0.38);
  --xr-border-color: #1F1F1F;
  --xr-disabled-color: #515151;
  --xr-background-color: #111111;
  --xr-background-color-row-even: #111111;
  --xr-background-color-row-odd: #313131;
}

.xr-wrap {
  display: block !important;
  min-width: 300px;
  max-width: 700px;
}

.xr-text-repr-fallback {
  /* fallback to plain text repr when CSS is not injected (untrusted notebook) */
  display: none;
}

.xr-header {
  padding-top: 6px;
  padding-bottom: 6px;
  margin-bottom: 4px;
  border-bottom: solid 1px var(--xr-border-color);
}

.xr-header > div,
.xr-header > ul {
  display: inline;
  margin-top: 0;
  margin-bottom: 0;
}

.xr-obj-type,
.xr-array-name {
  margin-left: 2px;
  margin-right: 10px;
}

.xr-obj-type {
  color: var(--xr-font-color2);
}

.xr-sections {
  padding-left: 0 !important;
  display: grid;
  grid-template-columns: 150px auto auto 1fr 20px 20px;
}

.xr-section-item {
  display: contents;
}

.xr-section-item input {
  display: none;
}

.xr-section-item input + label {
  color: var(--xr-disabled-color);
}

.xr-section-item input:enabled + label {
  cursor: pointer;
  color: var(--xr-font-color2);
}

.xr-section-item input:enabled + label:hover {
  color: var(--xr-font-color0);
}

.xr-section-summary {
  grid-column: 1;
  color: var(--xr-font-color2);
  font-weight: 500;
}

.xr-section-summary > span {
  display: inline-block;
  padding-left: 0.5em;
}

.xr-section-summary-in:disabled + label {
  color: var(--xr-font-color2);
}

.xr-section-summary-in + label:before {
  display: inline-block;
  content: '►';
  font-size: 11px;
  width: 15px;
  text-align: center;
}

.xr-section-summary-in:disabled + label:before {
  color: var(--xr-disabled-color);
}

.xr-section-summary-in:checked + label:before {
  content: '▼';
}

.xr-section-summary-in:checked + label > span {
  display: none;
}

.xr-section-summary,
.xr-section-inline-details {
  padding-top: 4px;
  padding-bottom: 4px;
}

.xr-section-inline-details {
  grid-column: 2 / -1;
}

.xr-section-details {
  display: none;
  grid-column: 1 / -1;
  margin-bottom: 5px;
}

.xr-section-summary-in:checked ~ .xr-section-details {
  display: contents;
}

.xr-array-wrap {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: 20px auto;
}

.xr-array-wrap > label {
  grid-column: 1;
  vertical-align: top;
}

.xr-preview {
  color: var(--xr-font-color3);
}

.xr-array-preview,
.xr-array-data {
  padding: 0 5px !important;
  grid-column: 2;
}

.xr-array-data,
.xr-array-in:checked ~ .xr-array-preview {
  display: none;
}

.xr-array-in:checked ~ .xr-array-data,
.xr-array-preview {
  display: inline-block;
}

.xr-dim-list {
  display: inline-block !important;
  list-style: none;
  padding: 0 !important;
  margin: 0;
}

.xr-dim-list li {
  display: inline-block;
  padding: 0;
  margin: 0;
}

.xr-dim-list:before {
  content: '(';
}

.xr-dim-list:after {
  content: ')';
}

.xr-dim-list li:not(:last-child):after {
  content: ',';
  padding-right: 5px;
}

.xr-has-index {
  font-weight: bold;
}

.xr-var-list,
.xr-var-item {
  display: contents;
}

.xr-var-item > div,
.xr-var-item label,
.xr-var-item > .xr-var-name span {
  background-color: var(--xr-background-color-row-even);
  margin-bottom: 0;
}

.xr-var-item > .xr-var-name:hover span {
  padding-right: 5px;
}

.xr-var-list > li:nth-child(odd) > div,
.xr-var-list > li:nth-child(odd) > label,
.xr-var-list > li:nth-child(odd) > .xr-var-name span {
  background-color: var(--xr-background-color-row-odd);
}

.xr-var-name {
  grid-column: 1;
}

.xr-var-dims {
  grid-column: 2;
}

.xr-var-dtype {
  grid-column: 3;
  text-align: right;
  color: var(--xr-font-color2);
}

.xr-var-preview {
  grid-column: 4;
}

.xr-index-preview {
  grid-column: 2 / 5;
  color: var(--xr-font-color2);
}

.xr-var-name,
.xr-var-dims,
.xr-var-dtype,
.xr-preview,
.xr-attrs dt {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 10px;
}

.xr-var-name:hover,
.xr-var-dims:hover,
.xr-var-dtype:hover,
.xr-attrs dt:hover {
  overflow: visible;
  width: auto;
  z-index: 1;
}

.xr-var-attrs,
.xr-var-data,
.xr-index-data {
  display: none;
  background-color: var(--xr-background-color) !important;
  padding-bottom: 5px !important;
}

.xr-var-attrs-in:checked ~ .xr-var-attrs,
.xr-var-data-in:checked ~ .xr-var-data,
.xr-index-data-in:checked ~ .xr-index-data {
  display: block;
}

.xr-var-data > table {
  float: right;
}

.xr-var-name span,
.xr-var-data,
.xr-index-name div,
.xr-index-data,
.xr-attrs {
  padding-left: 25px !important;
}

.xr-attrs,
.xr-var-attrs,
.xr-var-data,
.xr-index-data {
  grid-column: 1 / -1;
}

dl.xr-attrs {
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: 125px auto;
}

.xr-attrs dt,
.xr-attrs dd {
  padding: 0;
  margin: 0;
  float: left;
  padding-right: 10px;
  width: auto;
}

.xr-attrs dt {
  font-weight: normal;
  grid-column: 1;
}

.xr-attrs dt:hover span {
  display: inline-block;
  background: var(--xr-background-color);
  padding-right: 10px;
}

.xr-attrs dd {
  grid-column: 2;
  white-space: pre-wrap;
  word-break: break-all;
}

.xr-icon-database,
.xr-icon-file-text2,
.xr-no-icon {
  display: inline-block;
  vertical-align: middle;
  width: 1em;
  height: 1.5em !important;
  stroke-width: 0;
  stroke: currentColor;
  fill: currentColor;
}
</style><pre class='xr-text-repr-fallback'>&lt;xarray.DataArray &#x27;SCL&#x27; (time: 108, y: 259, x: 207)&gt; Size: 6MB
dask.array&lt;any-aggregate, shape=(108, 259, 207), dtype=bool, chunksize=(1, 259, 207), chunktype=numpy.ndarray&gt;
Coordinates:
  * y            (y) float64 2kB 2.459e+06 2.459e+06 ... 2.448e+06 2.448e+06
  * x            (x) float64 2kB 3.426e+06 3.426e+06 ... 3.435e+06 3.435e+06
    spatial_ref  int32 4B 3035
  * time         (time) datetime64[ns] 864B 2016-03-18T11:11:02.030000 ... 20...</pre><div class='xr-wrap' style='display:none'><div class='xr-header'><div class='xr-obj-type'>xarray.DataArray</div><div class='xr-array-name'>'SCL'</div><ul class='xr-dim-list'><li><span class='xr-has-index'>time</span>: 108</li><li><span class='xr-has-index'>y</span>: 259</li><li><span class='xr-has-index'>x</span>: 207</li></ul></div><ul class='xr-sections'><li class='xr-section-item'><div class='xr-array-wrap'><input id='section-a1f524f6-5312-426e-89d1-e6121bbed231' class='xr-array-in' type='checkbox' checked><label for='section-a1f524f6-5312-426e-89d1-e6121bbed231' title='Show/hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-array-preview xr-preview'><span>dask.array&lt;chunksize=(1, 259, 207), meta=np.ndarray&gt;</span></div><div class='xr-array-data'><table>
    <tr>
        <td>
            <table style="border-collapse: collapse;">
                <thead>
                    <tr>
                        <td> </td>
                        <th> Array </th>
                        <th> Chunk </th>
                    </tr>
                </thead>
                <tbody>

                    <tr>
                        <th> Bytes </th>
                        <td> 5.52 MiB </td>
                        <td> 52.36 kiB </td>
                    </tr>

                    <tr>
                        <th> Shape </th>
                        <td> (108, 259, 207) </td>
                        <td> (1, 259, 207) </td>
                    </tr>
                    <tr>
                        <th> Dask graph </th>
                        <td colspan="2"> 108 chunks in 7 graph layers </td>
                    </tr>
                    <tr>
                        <th> Data type </th>
                        <td colspan="2"> bool numpy.ndarray </td>
                    </tr>
                </tbody>
            </table>
        </td>
        <td>
        <svg width="185" height="199" style="stroke:rgb(0,0,0);stroke-width:1" >

  <!-- Horizontal lines -->
  <line x1="10" y1="0" x2="39" y2="29" style="stroke-width:2" />
  <line x1="10" y1="120" x2="39" y2="149" style="stroke-width:2" />

  <!-- Vertical lines -->
  <line x1="10" y1="0" x2="10" y2="120" style="stroke-width:2" />
  <line x1="11" y1="1" x2="11" y2="121" />
  <line x1="12" y1="2" x2="12" y2="122" />
  <line x1="14" y1="4" x2="14" y2="124" />
  <line x1="15" y1="5" x2="15" y2="125" />
  <line x1="17" y1="7" x2="17" y2="127" />
  <line x1="19" y1="9" x2="19" y2="129" />
  <line x1="20" y1="10" x2="20" y2="130" />
  <line x1="22" y1="12" x2="22" y2="132" />
  <line x1="23" y1="13" x2="23" y2="133" />
  <line x1="25" y1="15" x2="25" y2="135" />
  <line x1="26" y1="16" x2="26" y2="136" />
  <line x1="28" y1="18" x2="28" y2="138" />
  <line x1="29" y1="19" x2="29" y2="139" />
  <line x1="31" y1="21" x2="31" y2="141" />
  <line x1="33" y1="23" x2="33" y2="143" />
  <line x1="34" y1="24" x2="34" y2="144" />
  <line x1="36" y1="26" x2="36" y2="146" />
  <line x1="37" y1="27" x2="37" y2="147" />
  <line x1="39" y1="29" x2="39" y2="149" style="stroke-width:2" />

  <!-- Colored Rectangle -->
  <polygon points="10.0,0.0 39.43447649330002,29.434476493300018 39.43447649330002,149.43447649330002 10.0,120.0" style="fill:#8B4903A0;stroke-width:0"/>

  <!-- Horizontal lines -->
  <line x1="10" y1="0" x2="105" y2="0" style="stroke-width:2" />
  <line x1="11" y1="1" x2="107" y2="1" />
  <line x1="12" y1="2" x2="108" y2="2" />
  <line x1="14" y1="4" x2="110" y2="4" />
  <line x1="15" y1="5" x2="111" y2="5" />
  <line x1="17" y1="7" x2="113" y2="7" />
  <line x1="19" y1="9" x2="115" y2="9" />
  <line x1="20" y1="10" x2="116" y2="10" />
  <line x1="22" y1="12" x2="118" y2="12" />
  <line x1="23" y1="13" x2="119" y2="13" />
  <line x1="25" y1="15" x2="121" y2="15" />
  <line x1="26" y1="16" x2="122" y2="16" />
  <line x1="28" y1="18" x2="124" y2="18" />
  <line x1="29" y1="19" x2="125" y2="19" />
  <line x1="31" y1="21" x2="127" y2="21" />
  <line x1="33" y1="23" x2="129" y2="23" />
  <line x1="34" y1="24" x2="130" y2="24" />
  <line x1="36" y1="26" x2="132" y2="26" />
  <line x1="37" y1="27" x2="133" y2="27" />
  <line x1="39" y1="29" x2="135" y2="29" style="stroke-width:2" />

  <!-- Vertical lines -->
  <line x1="10" y1="0" x2="39" y2="29" style="stroke-width:2" />
  <line x1="105" y1="0" x2="135" y2="29" style="stroke-width:2" />

  <!-- Colored Rectangle -->
  <polygon points="10.0,0.0 105.9073359073359,0.0 135.34181240063592,29.434476493300018 39.43447649330002,29.434476493300018" style="fill:#8B4903A0;stroke-width:0"/>

  <!-- Horizontal lines -->
  <line x1="39" y1="29" x2="135" y2="29" style="stroke-width:2" />
  <line x1="39" y1="149" x2="135" y2="149" style="stroke-width:2" />

  <!-- Vertical lines -->
  <line x1="39" y1="29" x2="39" y2="149" style="stroke-width:2" />
  <line x1="135" y1="29" x2="135" y2="149" style="stroke-width:2" />

  <!-- Colored Rectangle -->
  <polygon points="39.43447649330002,29.434476493300018 135.34181240063592,29.434476493300018 135.34181240063592,149.43447649330002 39.43447649330002,149.43447649330002" style="fill:#ECB172A0;stroke-width:0"/>

  <!-- Text -->
  <text x="87.388144" y="169.434476" font-size="1.0rem" font-weight="100" text-anchor="middle" >207</text>
  <text x="155.341812" y="89.434476" font-size="1.0rem" font-weight="100" text-anchor="middle" transform="rotate(-90,155.341812,89.434476)">259</text>
  <text x="14.717238" y="154.717238" font-size="1.0rem" font-weight="100" text-anchor="middle" transform="rotate(45,14.717238,154.717238)">108</text>
</svg>
        </td>
    </tr>
</table></div></div></li><li class='xr-section-item'><input id='section-0ba99d8b-bb40-47cd-aa49-a1e952f82498' class='xr-section-summary-in' type='checkbox'  checked><label for='section-0ba99d8b-bb40-47cd-aa49-a1e952f82498' class='xr-section-summary' >Coordinates: <span>(4)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><ul class='xr-var-list'><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>y</span></div><div class='xr-var-dims'>(y)</div><div class='xr-var-dtype'>float64</div><div class='xr-var-preview xr-preview'>2.459e+06 2.459e+06 ... 2.448e+06</div><input id='attrs-8ee10fca-07a2-4e40-a810-df696325b56e' class='xr-var-attrs-in' type='checkbox' ><label for='attrs-8ee10fca-07a2-4e40-a810-df696325b56e' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-74cd03b4-36fe-4a8d-9663-efb257af823f' class='xr-var-data-in' type='checkbox'><label for='data-74cd03b4-36fe-4a8d-9663-efb257af823f' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'><dt><span>units :</span></dt><dd>metre</dd><dt><span>resolution :</span></dt><dd>-40.0</dd><dt><span>crs :</span></dt><dd>PROJCS[&quot;ETRS89-extended / LAEA Europe&quot;,GEOGCS[&quot;ETRS89&quot;,DATUM[&quot;European_Terrestrial_Reference_System_1989&quot;,SPHEROID[&quot;GRS 1980&quot;,6378137,298.257222101,AUTHORITY[&quot;EPSG&quot;,&quot;7019&quot;]],AUTHORITY[&quot;EPSG&quot;,&quot;6258&quot;]],PRIMEM[&quot;Greenwich&quot;,0,AUTHORITY[&quot;EPSG&quot;,&quot;8901&quot;]],UNIT[&quot;degree&quot;,0.0174532925199433,AUTHORITY[&quot;EPSG&quot;,&quot;9122&quot;]],AUTHORITY[&quot;EPSG&quot;,&quot;4258&quot;]],PROJECTION[&quot;Lambert_Azimuthal_Equal_Area&quot;],PARAMETER[&quot;latitude_of_center&quot;,52],PARAMETER[&quot;longitude_of_center&quot;,10],PARAMETER[&quot;false_easting&quot;,4321000],PARAMETER[&quot;false_northing&quot;,3210000],UNIT[&quot;metre&quot;,1,AUTHORITY[&quot;EPSG&quot;,&quot;9001&quot;]],AXIS[&quot;Northing&quot;,NORTH],AXIS[&quot;Easting&quot;,EAST],AUTHORITY[&quot;EPSG&quot;,&quot;3035&quot;]]</dd></dl></div><div class='xr-var-data'><pre>array([2458740., 2458700., 2458660., ..., 2448500., 2448460., 2448420.])</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>x</span></div><div class='xr-var-dims'>(x)</div><div class='xr-var-dtype'>float64</div><div class='xr-var-preview xr-preview'>3.426e+06 3.426e+06 ... 3.435e+06</div><input id='attrs-9fcbab86-fc52-4434-a8c9-8045862280c7' class='xr-var-attrs-in' type='checkbox' ><label for='attrs-9fcbab86-fc52-4434-a8c9-8045862280c7' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-2f264d6a-838b-40d0-96ed-77a8b40ede50' class='xr-var-data-in' type='checkbox'><label for='data-2f264d6a-838b-40d0-96ed-77a8b40ede50' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'><dt><span>units :</span></dt><dd>metre</dd><dt><span>resolution :</span></dt><dd>40.0</dd><dt><span>crs :</span></dt><dd>PROJCS[&quot;ETRS89-extended / LAEA Europe&quot;,GEOGCS[&quot;ETRS89&quot;,DATUM[&quot;European_Terrestrial_Reference_System_1989&quot;,SPHEROID[&quot;GRS 1980&quot;,6378137,298.257222101,AUTHORITY[&quot;EPSG&quot;,&quot;7019&quot;]],AUTHORITY[&quot;EPSG&quot;,&quot;6258&quot;]],PRIMEM[&quot;Greenwich&quot;,0,AUTHORITY[&quot;EPSG&quot;,&quot;8901&quot;]],UNIT[&quot;degree&quot;,0.0174532925199433,AUTHORITY[&quot;EPSG&quot;,&quot;9122&quot;]],AUTHORITY[&quot;EPSG&quot;,&quot;4258&quot;]],PROJECTION[&quot;Lambert_Azimuthal_Equal_Area&quot;],PARAMETER[&quot;latitude_of_center&quot;,52],PARAMETER[&quot;longitude_of_center&quot;,10],PARAMETER[&quot;false_easting&quot;,4321000],PARAMETER[&quot;false_northing&quot;,3210000],UNIT[&quot;metre&quot;,1,AUTHORITY[&quot;EPSG&quot;,&quot;9001&quot;]],AXIS[&quot;Northing&quot;,NORTH],AXIS[&quot;Easting&quot;,EAST],AUTHORITY[&quot;EPSG&quot;,&quot;3035&quot;]]</dd></dl></div><div class='xr-var-data'><pre>array([3426460., 3426500., 3426540., ..., 3434620., 3434660., 3434700.])</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span>spatial_ref</span></div><div class='xr-var-dims'>()</div><div class='xr-var-dtype'>int32</div><div class='xr-var-preview xr-preview'>3035</div><input id='attrs-5f7bf0c7-57c0-4e60-9d5f-98fe86db616a' class='xr-var-attrs-in' type='checkbox' ><label for='attrs-5f7bf0c7-57c0-4e60-9d5f-98fe86db616a' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-7dd40c99-b7cd-4cbc-83f9-6c91f19be704' class='xr-var-data-in' type='checkbox'><label for='data-7dd40c99-b7cd-4cbc-83f9-6c91f19be704' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'><dt><span>spatial_ref :</span></dt><dd>PROJCRS[&quot;ETRS89-extended / LAEA Europe&quot;,BASEGEOGCRS[&quot;ETRS89&quot;,DATUM[&quot;European Terrestrial Reference System 1989&quot;,ELLIPSOID[&quot;GRS 1980&quot;,6378137,298.257222101,LENGTHUNIT[&quot;metre&quot;,1]]],PRIMEM[&quot;Greenwich&quot;,0,ANGLEUNIT[&quot;degree&quot;,0.0174532925199433]],ID[&quot;EPSG&quot;,4258]],CONVERSION[&quot;unnamed&quot;,METHOD[&quot;Lambert Azimuthal Equal Area&quot;,ID[&quot;EPSG&quot;,9820]],PARAMETER[&quot;Latitude of natural origin&quot;,52,ANGLEUNIT[&quot;degree&quot;,0.0174532925199433],ID[&quot;EPSG&quot;,8801]],PARAMETER[&quot;Longitude of natural origin&quot;,10,ANGLEUNIT[&quot;degree&quot;,0.0174532925199433],ID[&quot;EPSG&quot;,8802]],PARAMETER[&quot;False easting&quot;,4321000,LENGTHUNIT[&quot;metre&quot;,1],ID[&quot;EPSG&quot;,8806]],PARAMETER[&quot;False northing&quot;,3210000,LENGTHUNIT[&quot;metre&quot;,1],ID[&quot;EPSG&quot;,8807]]],CS[Cartesian,2],AXIS[&quot;northing&quot;,north,ORDER[1],LENGTHUNIT[&quot;metre&quot;,1]],AXIS[&quot;easting&quot;,east,ORDER[2],LENGTHUNIT[&quot;metre&quot;,1]],ID[&quot;EPSG&quot;,3035]]</dd><dt><span>crs_wkt :</span></dt><dd>PROJCRS[&quot;ETRS89-extended / LAEA Europe&quot;,BASEGEOGCRS[&quot;ETRS89&quot;,DATUM[&quot;European Terrestrial Reference System 1989&quot;,ELLIPSOID[&quot;GRS 1980&quot;,6378137,298.257222101,LENGTHUNIT[&quot;metre&quot;,1]]],PRIMEM[&quot;Greenwich&quot;,0,ANGLEUNIT[&quot;degree&quot;,0.0174532925199433]],ID[&quot;EPSG&quot;,4258]],CONVERSION[&quot;unnamed&quot;,METHOD[&quot;Lambert Azimuthal Equal Area&quot;,ID[&quot;EPSG&quot;,9820]],PARAMETER[&quot;Latitude of natural origin&quot;,52,ANGLEUNIT[&quot;degree&quot;,0.0174532925199433],ID[&quot;EPSG&quot;,8801]],PARAMETER[&quot;Longitude of natural origin&quot;,10,ANGLEUNIT[&quot;degree&quot;,0.0174532925199433],ID[&quot;EPSG&quot;,8802]],PARAMETER[&quot;False easting&quot;,4321000,LENGTHUNIT[&quot;metre&quot;,1],ID[&quot;EPSG&quot;,8806]],PARAMETER[&quot;False northing&quot;,3210000,LENGTHUNIT[&quot;metre&quot;,1],ID[&quot;EPSG&quot;,8807]]],CS[Cartesian,2],AXIS[&quot;northing&quot;,north,ORDER[1],LENGTHUNIT[&quot;metre&quot;,1]],AXIS[&quot;easting&quot;,east,ORDER[2],LENGTHUNIT[&quot;metre&quot;,1]],ID[&quot;EPSG&quot;,3035]]</dd><dt><span>semi_major_axis :</span></dt><dd>6378137.0</dd><dt><span>semi_minor_axis :</span></dt><dd>6356752.314140356</dd><dt><span>inverse_flattening :</span></dt><dd>298.257222101</dd><dt><span>reference_ellipsoid_name :</span></dt><dd>GRS 1980</dd><dt><span>longitude_of_prime_meridian :</span></dt><dd>0.0</dd><dt><span>prime_meridian_name :</span></dt><dd>Greenwich</dd><dt><span>geographic_crs_name :</span></dt><dd>ETRS89</dd><dt><span>horizontal_datum_name :</span></dt><dd>European Terrestrial Reference System 1989</dd><dt><span>projected_crs_name :</span></dt><dd>ETRS89-extended / LAEA Europe</dd><dt><span>grid_mapping_name :</span></dt><dd>lambert_azimuthal_equal_area</dd><dt><span>latitude_of_projection_origin :</span></dt><dd>52.0</dd><dt><span>longitude_of_projection_origin :</span></dt><dd>10.0</dd><dt><span>false_easting :</span></dt><dd>4321000.0</dd><dt><span>false_northing :</span></dt><dd>3210000.0</dd><dt><span>GeoTransform :</span></dt><dd>3426440 40 0 2458760 0 -40</dd></dl></div><div class='xr-var-data'><pre>array(3035, dtype=int32)</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>time</span></div><div class='xr-var-dims'>(time)</div><div class='xr-var-dtype'>datetime64[ns]</div><div class='xr-var-preview xr-preview'>2016-03-18T11:11:02.030000 ... 2...</div><input id='attrs-9ba6bf49-30f6-46db-83f7-133e2595fcb9' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-9ba6bf49-30f6-46db-83f7-133e2595fcb9' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-ab2d987c-362b-4608-afd5-6af57ab7e33d' class='xr-var-data-in' type='checkbox'><label for='data-ab2d987c-362b-4608-afd5-6af57ab7e33d' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([&#x27;2016-03-18T11:11:02.030000000&#x27;, &#x27;2016-03-22T10:50:42.030000000&#x27;,
       &#x27;2016-04-27T11:06:22.028000000&#x27;, &#x27;2016-05-01T10:50:32.029000000&#x27;,
       &#x27;2016-05-04T10:56:22.027000000&#x27;, &#x27;2016-07-06T11:06:52.026000000&#x27;,
       &#x27;2016-07-16T11:06:22.026000000&#x27;, &#x27;2016-08-12T10:56:22.026000000&#x27;,
       &#x27;2016-08-22T10:56:52.026000000&#x27;, &#x27;2016-10-21T11:01:02.027000000&#x27;,
       &#x27;2016-10-31T11:02:02.026000000&#x27;, &#x27;2016-11-30T11:04:22.026000000&#x27;,
       &#x27;2017-02-18T11:01:11.026000000&#x27;, &#x27;2017-03-10T10:58:41.026000000&#x27;,
       &#x27;2017-04-09T10:56:51.026000000&#x27;, &#x27;2017-04-19T10:56:21.026000000&#x27;,
       &#x27;2017-06-18T10:56:21.026000000&#x27;, &#x27;2017-08-02T10:56:49.027000000&#x27;,
       &#x27;2017-10-06T10:59:41.026000000&#x27;, &#x27;2017-10-16T11:00:31.026000000&#x27;,
       &#x27;2017-10-31T11:01:49.027000000&#x27;, &#x27;2018-04-19T10:56:19.027000000&#x27;,
       &#x27;2018-04-24T10:56:51.024000000&#x27;, &#x27;2018-05-04T10:56:21.024000000&#x27;,
       &#x27;2018-06-23T10:56:21.024000000&#x27;, &#x27;2018-07-08T10:56:19.024000000&#x27;,
       &#x27;2018-07-13T10:56:21.024000000&#x27;, &#x27;2018-07-23T10:56:21.024000000&#x27;,
       &#x27;2018-08-02T10:56:21.024000000&#x27;, &#x27;2018-08-12T10:56:21.024000000&#x27;,
       &#x27;2018-08-22T10:56:21.024000000&#x27;, &#x27;2018-09-01T10:56:21.024000000&#x27;,
       &#x27;2018-09-11T10:56:21.024000000&#x27;, &#x27;2018-09-26T11:00:29.024000000&#x27;,
       &#x27;2018-10-16T11:00:29.024000000&#x27;, &#x27;2018-11-15T11:03:19.024000000&#x27;,
       &#x27;2019-02-03T11:02:49.024000000&#x27;, &#x27;2019-02-13T11:01:49.024000000&#x27;,
       &#x27;2019-02-23T11:00:39.024000000&#x27;, &#x27;2019-03-20T10:57:41.024000000&#x27;,
       &#x27;2019-03-25T10:57:09.024000000&#x27;, &#x27;2019-03-30T10:56:31.024000000&#x27;,
       &#x27;2019-04-09T10:56:21.024000000&#x27;, &#x27;2019-06-13T10:56:29.024000000&#x27;,
       &#x27;2019-07-08T10:56:21.024000000&#x27;, &#x27;2019-07-13T10:56:29.024000000&#x27;,
       &#x27;2019-07-23T10:56:29.024000000&#x27;, &#x27;2019-08-02T10:56:29.024000000&#x27;,
       &#x27;2019-08-22T10:56:29.024000000&#x27;, &#x27;2019-09-16T10:57:01.024000000&#x27;,
       &#x27;2019-10-11T10:59:59.024000000&#x27;, &#x27;2019-12-05T11:04:31.024000000&#x27;,
       &#x27;2019-12-30T11:03:49.024000000&#x27;, &#x27;2020-01-19T11:02:59.024000000&#x27;,
       &#x27;2020-02-03T11:02:41.024000000&#x27;, &#x27;2020-03-24T10:57:11.024000000&#x27;,
       &#x27;2020-04-03T10:56:21.025000000&#x27;, &#x27;2020-05-18T10:56:19.024000000&#x27;,
       &#x27;2020-05-28T10:56:19.024000000&#x27;, &#x27;2020-06-22T10:56:31.024000000&#x27;,
       &#x27;2020-07-27T10:56:19.024000000&#x27;, &#x27;2020-08-06T10:56:19.024000000&#x27;,
       &#x27;2020-09-10T10:56:31.025000000&#x27;, &#x27;2020-10-30T11:02:11.024000000&#x27;,
       &#x27;2020-11-29T11:04:21.024000000&#x27;, &#x27;2021-01-08T11:04:31.024000000&#x27;,
       &#x27;2021-02-17T11:01:21.024000000&#x27;, &#x27;2021-02-27T11:00:11.024000000&#x27;,
       &#x27;2021-03-04T10:58:39.024000000&#x27;, &#x27;2021-03-24T10:56:39.024000000&#x27;,
       &#x27;2021-03-29T10:56:31.024000000&#x27;, &#x27;2021-04-03T10:56:19.024000000&#x27;,
       &#x27;2021-04-08T10:56:21.024000000&#x27;, &#x27;2021-04-23T10:56:19.024000000&#x27;,
       &#x27;2021-05-03T10:56:19.024000000&#x27;, &#x27;2021-07-17T10:56:21.024000000&#x27;,
       &#x27;2021-08-11T10:56:19.024000000&#x27;, &#x27;2021-08-26T10:56:21.024000000&#x27;,
       &#x27;2021-08-31T10:56:19.024000000&#x27;, &#x27;2021-09-05T10:56:21.024000000&#x27;,
       &#x27;2021-09-30T10:57:49.024000000&#x27;, &#x27;2021-10-10T10:58:59.024000000&#x27;,
       &#x27;2021-11-09T11:01:59.024000000&#x27;, &#x27;2022-01-23T11:03:41.024000000&#x27;,
       &#x27;2022-03-24T10:57:21.024000000&#x27;, &#x27;2022-05-28T10:56:19.024000000&#x27;,
       &#x27;2022-07-02T10:56:31.024000000&#x27;, &#x27;2022-07-07T10:56:29.024000000&#x27;,
       &#x27;2022-07-12T10:56:31.024000000&#x27;, &#x27;2022-07-17T10:56:29.024000000&#x27;,
       &#x27;2022-08-01T10:56:31.024000000&#x27;, &#x27;2022-08-06T10:56:29.024000000&#x27;,
       &#x27;2022-09-05T10:56:19.024000000&#x27;, &#x27;2022-09-20T10:57:41.025000000&#x27;,
       &#x27;2023-02-12T11:00:59.024000000&#x27;, &#x27;2023-07-27T10:56:21.024000000&#x27;,
       &#x27;2023-08-21T10:56:29.024000000&#x27;, &#x27;2023-09-05T10:56:21.024000000&#x27;,
       &#x27;2023-09-25T10:58:01.024000000&#x27;, &#x27;2023-09-30T10:57:49.024000000&#x27;,
       &#x27;2023-10-10T10:58:59.024000000&#x27;, &#x27;2024-03-13T10:58:31.024000000&#x27;,
       &#x27;2024-04-12T10:56:21.024000000&#x27;, &#x27;2024-06-26T10:56:19.024000000&#x27;,
       &#x27;2024-08-05T10:56:19.024000000&#x27;, &#x27;2024-08-10T10:56:21.024000000&#x27;,
       &#x27;2024-10-24T11:00:39.024000000&#x27;, &#x27;2024-11-28T11:04:11.024000000&#x27;],
      dtype=&#x27;datetime64[ns]&#x27;)</pre></div></li></ul></div></li><li class='xr-section-item'><input id='section-da133793-d617-4851-87f0-330d014b4e84' class='xr-section-summary-in' type='checkbox'  ><label for='section-da133793-d617-4851-87f0-330d014b4e84' class='xr-section-summary' >Indexes: <span>(3)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><ul class='xr-var-list'><li class='xr-var-item'><div class='xr-index-name'><div>y</div></div><div class='xr-index-preview'>PandasIndex</div><div></div><input id='index-065ba7b1-beac-4f85-9dd3-809584f7ea60' class='xr-index-data-in' type='checkbox'/><label for='index-065ba7b1-beac-4f85-9dd3-809584f7ea60' title='Show/Hide index repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-index-data'><pre>PandasIndex(Index([2458740.0, 2458700.0, 2458660.0, 2458620.0, 2458580.0, 2458540.0,
       2458500.0, 2458460.0, 2458420.0, 2458380.0,
       ...
       2448780.0, 2448740.0, 2448700.0, 2448660.0, 2448620.0, 2448580.0,
       2448540.0, 2448500.0, 2448460.0, 2448420.0],
      dtype=&#x27;float64&#x27;, name=&#x27;y&#x27;, length=259))</pre></div></li><li class='xr-var-item'><div class='xr-index-name'><div>x</div></div><div class='xr-index-preview'>PandasIndex</div><div></div><input id='index-d838019b-1fd2-4a0d-b392-7afd4ec51000' class='xr-index-data-in' type='checkbox'/><label for='index-d838019b-1fd2-4a0d-b392-7afd4ec51000' title='Show/Hide index repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-index-data'><pre>PandasIndex(Index([3426460.0, 3426500.0, 3426540.0, 3426580.0, 3426620.0, 3426660.0,
       3426700.0, 3426740.0, 3426780.0, 3426820.0,
       ...
       3434340.0, 3434380.0, 3434420.0, 3434460.0, 3434500.0, 3434540.0,
       3434580.0, 3434620.0, 3434660.0, 3434700.0],
      dtype=&#x27;float64&#x27;, name=&#x27;x&#x27;, length=207))</pre></div></li><li class='xr-var-item'><div class='xr-index-name'><div>time</div></div><div class='xr-index-preview'>PandasIndex</div><div></div><input id='index-d216cac3-5af9-4728-85c8-aa5b36d39aa4' class='xr-index-data-in' type='checkbox'/><label for='index-d216cac3-5af9-4728-85c8-aa5b36d39aa4' title='Show/Hide index repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-index-data'><pre>PandasIndex(DatetimeIndex([&#x27;2016-03-18 11:11:02.030000&#x27;, &#x27;2016-03-22 10:50:42.030000&#x27;,
               &#x27;2016-04-27 11:06:22.028000&#x27;, &#x27;2016-05-01 10:50:32.029000&#x27;,
               &#x27;2016-05-04 10:56:22.027000&#x27;, &#x27;2016-07-06 11:06:52.026000&#x27;,
               &#x27;2016-07-16 11:06:22.026000&#x27;, &#x27;2016-08-12 10:56:22.026000&#x27;,
               &#x27;2016-08-22 10:56:52.026000&#x27;, &#x27;2016-10-21 11:01:02.027000&#x27;,
               ...
               &#x27;2023-09-25 10:58:01.024000&#x27;, &#x27;2023-09-30 10:57:49.024000&#x27;,
               &#x27;2023-10-10 10:58:59.024000&#x27;, &#x27;2024-03-13 10:58:31.024000&#x27;,
               &#x27;2024-04-12 10:56:21.024000&#x27;, &#x27;2024-06-26 10:56:19.024000&#x27;,
               &#x27;2024-08-05 10:56:19.024000&#x27;, &#x27;2024-08-10 10:56:21.024000&#x27;,
               &#x27;2024-10-24 11:00:39.024000&#x27;, &#x27;2024-11-28 11:04:11.024000&#x27;],
              dtype=&#x27;datetime64[ns]&#x27;, name=&#x27;time&#x27;, length=108, freq=None))</pre></div></li></ul></div></li><li class='xr-section-item'><input id='section-09a046cb-2254-4341-8dd5-660ecb088737' class='xr-section-summary-in' type='checkbox' disabled ><label for='section-09a046cb-2254-4341-8dd5-660ecb088737' class='xr-section-summary'  title='Expand/collapse section'>Attributes: <span>(0)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><dl class='xr-attrs'></dl></div></li></ul></div></div>



We can apply the mask on the Satellite Image Time Series with the method `StacAttack.mask()`.


```python
ts_S2.mask_apply()
```

### 3.3. Gap filling the masked pixels

We interpolate in time the masked pixels (NaN values). The method `StacAttack.gapfill()` relies on the `xarray.DataArray.interpolate_na`. By default the linear interpolation is used but you can try another one (see the related [documentation](https://docs.xarray.dev/en/stable/generated/xarray.DataArray.interpolate_na.html)). As the interpolation needs backward and forward values, the first and the last images are not processed. To avoid this, the method `StacAttack.gapfill()` also call the methods `xarray.DataArray.bfill` and `xarray.DataArray.ffill`. You can disable this by passing the argument `first_last=False`.


```python
%%time

ts_S2.gapfill()
```

    CPU times: user 71.1 ms, sys: 7.69 ms, total: 78.8 ms
    Wall time: 75 ms


## 4. Saving the Datacube as a file

### 4.1. Default export

It is possible to export the Datacube in NetCDF (Network Common Data Form) or in CSV (Comma-Separated Values).



```python
%%time

# export to NETcdf
ts_S2.to_nc(data_dir)

#export to csv
#ts_S2.to_csv(data_dir)
```

    CPU times: user 46.6 s, sys: 24.3 s, total: 1min 10s
    Wall time: 25.5 s


The output filename is automaticaly made with the following syntax:
```sh
fid-<gid>_<array type>_<start date>-<end date>.nc
```



```python
%%time

netcdf = [i for i in os.listdir(data_dir) if i.endswith('.nc')]
netcdf
```

    CPU times: user 2.41 ms, sys: 282 µs, total: 2.69 ms
    Wall time: 1.73 ms





    ['S2_fid-None_image_2016-01-01 00:00:00-2025-01-01 00:00:00.nc']



## 5. Convert NetCDF file into animated GIF

Last but not least... sits package allows you to export satellite time series as animated GIF, so you can easily show some phenoma that vary in time and space.

### 5.1. Loading NetCDF file

We load the newly created NetCDF file as an `xarray.Dataarray`, and choose to keep only three spectral bands in order to display color composites (RGB format).


```python
%%time

netcdf_path = os.path.join(data_dir, netcdf[0])

test = sits.export.Sits_ds(netcdf_path)
test.ds2da(keep_bands=['B08', 'B04', 'B03'])
```

    CPU times: user 106 ms, sys: 162 ms, total: 268 ms
    Wall time: 807 ms


### 5.2. Making a nice-looking animation

To convert the `xarray.Dataarray` object into an animated GIF, `sits` package uses in the geogif library. So it is possible to add specific arguments, not presented by default.


```python
%%time

out_gif= os.path.join(data_dir, 'banc_arguin.gif')
test.export2gif(imgfile=out_gif)
```

    CPU times: user 1.3 s, sys: 595 ms, total: 1.89 s
    Wall time: 1.95 s


Now it's time to see the result. Enjoy the movie!


```python
%%time

from IPython.display import Image, display
display(Image(filename=out_gif))
```


    <IPython.core.display.Image object>


    CPU times: user 43.4 ms, sys: 12.1 ms, total: 55.6 ms
    Wall time: 57.2 ms


<p align="center">
<img src="test_data/banc_arguin.gif" alt="banc_arguin.gif">
</p>
