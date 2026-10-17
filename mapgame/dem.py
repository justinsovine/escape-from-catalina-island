"""Elevation grids in metres on an Area: Mapzen Terrarium tiles (global, free, no key) or a local GeoTIFF."""
import math, os, time, urllib.request
import numpy as np, rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from rasterio.io import MemoryFile
from . import DATA

UA = "mapgame (github.com/justinsovine/mapgame)"


def from_geotiff(area, path):
    Z = np.full((area.H, area.W), np.nan, "float32")
    with rasterio.open(path) as s:
        reproject(rasterio.band(s, 1), Z, dst_transform=area.transform, dst_crs=f"EPSG:{area.epsg}",
                  resampling=Resampling.bilinear, dst_nodata=np.nan)
    return Z


def _tile(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return int(x), int(y)


def _get(url, path):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as f:
                f.write(r.read())
            return
        except Exception:
            if attempt == 3: raise
            time.sleep(2 ** attempt)


def from_terrarium(area, z=13):
    """height = R*256 + G + B/256 - 32768, Web Mercator tiles from s3://elevation-tiles-prod.
    z13 is about 19 m at 38 N, z14 about 10 m. Tiles are cached under data/terrarium."""
    from PIL import Image
    lon0, lat0, lon1, lat1 = area.lonlat
    x0, y1 = _tile(lon0, lat0, z); x1, y0 = _tile(lon1, lat1, z)
    cache = os.path.join(DATA, "terrarium"); os.makedirs(cache, exist_ok=True)
    mosaic = np.zeros(((y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256), "float32")
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            f = os.path.join(cache, f"{z}_{tx}_{ty}.png")
            if not os.path.exists(f):
                _get(f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{tx}/{ty}.png", f)
            a = np.asarray(Image.open(f).convert("RGB"), "float32")
            mosaic[(ty - y0) * 256:(ty - y0 + 1) * 256, (tx - x0) * 256:(tx - x0 + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    n = 2 ** z; world = 2 * math.pi * 6378137.0; px = world / n / 256
    tr = from_origin(-world / 2 + x0 * world / n, world / 2 - y0 * world / n, px, px)
    bad = mosaic < -500                              # stray nodata pixels decode to thousands of metres below sea level
    if bad.any():
        from scipy.ndimage import distance_transform_edt
        idx = distance_transform_edt(bad, return_distances=False, return_indices=True)
        mosaic = mosaic[tuple(idx)]
    Z = np.full((area.H, area.W), np.nan, "float32")
    with MemoryFile() as mem:
        with mem.open(driver="GTiff", height=mosaic.shape[0], width=mosaic.shape[1], count=1, dtype="float32", crs="EPSG:3857", transform=tr) as src:
            src.write(mosaic, 1)
            reproject(rasterio.band(src, 1), Z, dst_transform=area.transform, dst_crs=f"EPSG:{area.epsg}", resampling=Resampling.bilinear, dst_nodata=np.nan)
    return Z
