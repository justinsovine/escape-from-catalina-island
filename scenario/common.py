"""Shared loaders for the scenario: the island grid, OSM, the state's tsunami hazard area, USGS 1 m lidar.
Everything is fetched on first use and cached under data/ (see mapgame.DATA)."""
import os, sys, json, urllib.request, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
if ROOT not in sys.path: sys.path.insert(0, ROOT)
import numpy as np
from mapgame import DATA, dem, osm as O
from mapgame.area import Area
from mapgame.dem import _get, UA

ISLAND = (-118.63, 33.29, -118.28, 33.50)          # the whole island, with sea around it
TIF13 = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/n34w119/USGS_13_n34w119.tif"
TNM = "https://tnmaccess.nationalmap.gov/api/v1/products"
CGS = "https://gis.conservation.ca.gov/server/rest/services/CGS/IW_Tsunami_Hazard_Area/FeatureServer/0/query"


def dem_path():
    """USGS 3DEP 1/3 arc-second (10 m) tile n34w119, which covers the island. MAPGAME_DEM overrides."""
    p = os.environ.get("MAPGAME_DEM") or os.path.join(DATA, "dem", "USGS_13_n34w119.tif")
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True); print("downloading the 1/3 arc-second DEM tile (77 MB)"); _get(TIF13, p)
    return p


def osm_elements():
    """OSM for the island, fetched in four longitude strips so a failed strip can be retried alone."""
    els = {}
    lons = [-118.63, -118.53, -118.43, -118.33, -118.28]
    for a, b in zip(lons[:-1], lons[1:]):
        for e in O.fetch((a, ISLAND[1], b, ISLAND[3])): els[(e["type"], e["id"])] = e
    return list(els.values())


def island(res=10.0):
    """Area, height grid (m), land mask, OSM layers and raw elements for the whole island."""
    A = Area(*ISLAND, res=res)
    els = osm_elements(); L = O.layers(A, els)
    cache = os.path.join(DATA, f"island_{res:g}m.npz")
    if os.path.exists(cache):
        d = np.load(cache); Z, land = d["Z"], d["land"]
    else:
        Z = dem.from_geotiff(A, dem_path()); land = O.land_mask(A, L)
        np.savez_compressed(cache, Z=Z, land=land)
    return A, Z, land, L, els


def cgs_hazard(A):
    """California Geological Survey tsunami hazard area (the state's evacuation planning line, 'maximum considered'
    scenarios) as polygons in the area's map coordinates. Only the 'Yes, Tsunami Hazard Area' features."""
    from shapely.geometry import shape
    from shapely import transform
    f = os.path.join(DATA, "cgs", "tsunami_hazard_area.geojson")
    if not os.path.exists(f):
        os.makedirs(os.path.dirname(f), exist_ok=True)
        q = urllib.parse.urlencode(dict(geometry="%s,%s,%s,%s" % ISLAND, geometryType="esriGeometryEnvelope", inSR=4326,
                                        spatialRel="esriSpatialRelIntersects", outFields="*", outSR=4326, f="geojson"))
        _get(CGS + "?" + q, f)
    polys = []
    for ft in json.load(open(f)).get("features", []):
        if not str(ft["properties"].get("Evacuate", "")).startswith("Yes"): continue
        polys.append(transform(shape(ft["geometry"]), lambda c: np.c_[A.xy(c[:, 0], c[:, 1])]))
    return polys


def lidar_tiles(bbox):
    """USGS 3DEP 1 m lidar DEM tiles intersecting a lon/lat bbox, newest project per tile, downloaded to data/dem/1m."""
    url = TNM + "?" + urllib.parse.urlencode(dict(datasets="Digital Elevation Model (DEM) 1 meter", bbox="%s,%s,%s,%s" % tuple(bbox), max=100))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    items = [i for i in json.loads(urllib.request.urlopen(req, timeout=60).read()).get("items", []) if i.get("sizeInBytes")]
    best = {}
    for i in items:                                   # tiles are named by their 10 km UTM square, e.g. x36y370
        key = next((w for w in i["title"].split() if w.startswith("x") and "y" in w), i["title"])
        if key not in best or i.get("publicationDate", "") > best[key].get("publicationDate", ""): best[key] = i
    folder = os.path.join(DATA, "dem", "1m"); os.makedirs(folder, exist_ok=True); paths = []
    for i in best.values():
        p = os.path.join(folder, os.path.basename(i["downloadURL"]))
        if not os.path.exists(p): print(f"downloading {os.path.basename(p)} ({i['sizeInBytes'] // 1000000} MB)"); _get(i["downloadURL"], p)
        paths.append(p)
    return paths


def lidar_mosaic(A):
    """The 1 m lidar resampled onto an Area (NaN where no tile covers it)."""
    import rasterio
    from rasterio.warp import reproject, Resampling
    Z = np.full((A.H, A.W), np.nan, "float32")
    for p in lidar_tiles(A.lonlat):
        tmp = np.full((A.H, A.W), np.nan, "float32")
        with rasterio.open(p) as s:
            reproject(rasterio.band(s, 1), tmp, dst_transform=A.transform, dst_crs=f"EPSG:{A.epsg}", resampling=Resampling.bilinear, dst_nodata=np.nan)
        Z = np.where(np.isnan(Z), tmp, Z)
    return Z
