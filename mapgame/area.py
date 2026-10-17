"""A lon/lat bbox rasterised on the local UTM zone, plus the projections the styles share."""
import numpy as np
from rasterio.warp import transform_bounds
from rasterio.transform import from_origin
from pyproj import Transformer
from scipy.ndimage import map_coordinates


class Area:
    def __init__(self, lon0, lat0, lon1, lat1, res=10.0):
        zone = int((lon0 + lon1) / 2 + 180) // 6 + 1
        self.epsg = 32600 + zone if (lat0 + lat1) / 2 >= 0 else 32700 + zone
        b = transform_bounds(4326, self.epsg, lon0, lat0, lon1, lat1)
        self.E0, self.N0, self.res = b[0], b[1], res
        self.W, self.H = int((b[2] - b[0]) / res), int((b[3] - b[1]) / res)
        self.transform = from_origin(self.E0, self.N0 + self.H * res, res, res)
        self._to = Transformer.from_crs(4326, self.epsg, always_xy=True)
        self.lonlat = (lon0, lat0, lon1, lat1)

    def xy(self, lon, lat):
        return self._to.transform(lon, lat)

    def rc(self, x, y):
        """Map coords (m) to fractional row, col."""
        return (self.N0 + self.H * self.res - y) / self.res - 0.5, (x - self.E0) / self.res - 0.5

    def sample(self, Z, x, y):
        """Bilinear sample of a grid at map coords; scalar in, scalar out."""
        scalar = np.ndim(x) == 0
        r, c = self.rc(np.atleast_1d(np.asarray(x, float)), np.atleast_1d(np.asarray(y, float)))
        v = map_coordinates(np.nan_to_num(Z, nan=0.0), [r, c], order=1)
        return float(v[0]) if scalar else v

    @property
    def plate(self):
        from shapely.geometry import Polygon
        x0, y0, x1, y1 = self.E0, self.N0, self.E0 + self.W * self.res, self.N0 + self.H * self.res
        return Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def iso(x, y, z=0.0, exag=1.0):
    """Dimetric projection of map metres to screen units; z lifts the point."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    return (x - y) * 0.8660254, (x + y) * 0.5 + np.asarray(z, float) * exag
