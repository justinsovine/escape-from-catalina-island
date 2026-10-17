"""Bake the representation products the design spec relies on, and print the numbers it quotes.

- flood threshold ("spill level") raster: for every cell, the lowest sea level at which the cell is wet through a
  connected path from the sea. One 16-bit raster replaces a stack of flood masks: wet(L) = threshold <= L.
- slope and movement-cost classes at 30 m.
- travel graph statistics from the OSM roads and trails (nodes, edges, junctions, length).
- grid and file-size budget at 10, 30 and 100 m.
Outputs go to data/bake/ (gitignored). Run: python atlas/bake.py
"""
import os, sys, json, math, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.morphology import reconstruction
from shapely.ops import unary_union
from shapely.geometry import LineString, MultiLineString
from scenario.common import island
OUT = os.path.join(ROOT, "data", "bake"); os.makedirs(OUT, exist_ok=True)
t0 = time.time()
A, Z, land, L, els = island(res=10)
H, W = Z.shape; res = A.res
print(f"grid {W}x{H} at {res:g} m, land cells {int(land.sum())} ({land.sum() * res * res / 1e6:.1f} km2), keys {sorted(L.keys())}")
Z = np.nan_to_num(Z.astype("float64"), nan=0.0); Zl = np.where(land, Z, np.minimum(Z, 0.0))      # sea cells are NaN in the DEM: set to 0 and never above the datum

# 1. flood threshold by morphological reconstruction (priority flood from the sea)
big = float(np.nanmax(Zl)) + 100.0
seed = np.where(land, big, Zl)
thr = reconstruction(seed, Zl, method="erosion")   # min over paths from the sea of the max elevation
thr_land = thr[land]
print(f"threshold raster: {time.time() - t0:.0f} s; land cells wet at 5 m {(thr_land <= 5).mean() * 100:.1f}%, 10 m {(thr_land <= 10).mean() * 100:.1f}%, 20 m {(thr_land <= 20).mean() * 100:.1f}%, 30 m {(thr_land <= 30).mean() * 100:.1f}%")
# check against the earlier flood fill: the isthmus joins the two harbors at 10.5 m.
# North of the split row is Isthmus Cove water, south of it Cat Harbor water (rows grow southward).
def rc(lon, lat):
    r, c = A.rc(*A.xy(lon, lat)); return int(np.asarray(r).ravel()[0]), int(np.asarray(c).ravel()[0])
(ri, ci), (rcat, ccat) = rc(-118.4985, 33.4445), rc(-118.5075, 33.4325); split = (ri + rcat) // 2
box = np.zeros_like(land); box[max(min(ri, rcat) - 150, 0):max(ri, rcat) + 150, max(min(ci, ccat) - 150, 0):max(ci, ccat) + 150] = True
rows = np.arange(H)[:, None] * np.ones((1, W), int)
sea_n = box & ~land & (rows < split); sea_s = box & ~land & (rows > split)
print(f"  isthmus check: Isthmus Cove water cells {int(sea_n.sum())}, Cat Harbor water cells {int(sea_s.sum())}")
for Lv in (9.5, 10.0, 10.5, 11.0, 12.0):
    wet_land = land & (thr <= Lv); lab, n = ndimage.label(wet_land)
    touch_n = set(np.unique(lab[ndimage.binary_dilation(sea_n) & wet_land])) - {0}; touch_s = set(np.unique(lab[ndimage.binary_dilation(sea_s) & wet_land])) - {0}
    print(f"  level {Lv:4.1f} m: a wet land body touches both harbors: {bool(touch_n & touch_s)}")
# pass level directly: reconstruction seeded from Isthmus Cove water only, other water blocked
mask = np.where(land, Zl, np.where(sea_n, Zl, big)); seed2 = np.where(sea_n, Zl, big)
hI = reconstruction(seed2, mask, method="erosion")
coast_s = land & ndimage.binary_dilation(sea_s)
print(f"  pass level across the isthmus (lowest max-elevation path from Isthmus Cove water to the Cat Harbor shore): {hI[coast_s].min():.1f} m")
# save: 16-bit PNG in 0.1 m units, plus a 30 m block-mean version for the simulation tier
Image.fromarray(np.clip(np.round(thr * 10), 0, 65535).astype("uint16")).save(os.path.join(OUT, "flood_threshold_10m.png"))
k = 3; H3, W3 = H // k, W // k
thr30 = thr[:H3 * k, :W3 * k].reshape(H3, k, W3, k).mean(axis=(1, 3))
Image.fromarray(np.clip(np.round(thr30 * 10), 0, 65535).astype("uint16")).save(os.path.join(OUT, "flood_threshold_30m.png"))
json.dump(dict(crs=f"EPSG:{A.epsg}", origin_xy=[A.x0, A.y1] if hasattr(A, "x0") else None, res_m=res, size=[W, H], units="0.1 m, sea level datum NAVD88", lonlat_bbox=A.lonlat if hasattr(A, "lonlat") else None), open(os.path.join(OUT, "flood_threshold_10m.json"), "w"))

# 2. slope and cost classes
gy, gx = np.gradient(Z, res); slope = np.degrees(np.arctan(np.hypot(gx, gy))); sl = slope[land]
print(f"slope on land: over 20 deg {(sl > 20).mean() * 100:.1f}%, over 30 {(sl > 30).mean() * 100:.1f}%, over 35 {(sl > 35).mean() * 100:.1f}%, over 45 {(sl > 45).mean() * 100:.1f}%")
Z30 = Z[:H3 * k, :W3 * k].reshape(H3, k, W3, k).mean(axis=(1, 3)); land30 = land[:H3 * k, :W3 * k].reshape(H3, k, W3, k).mean(axis=(1, 3)) > 0.5
gy, gx = np.gradient(Z30, res * k); s30 = np.degrees(np.arctan(np.hypot(gx, gy)))
cls = np.select([~land30, s30 > 35, s30 > 30, s30 > 20, s30 > 10], [255, 200, 150, 100, 50], 10).astype("uint8")   # 255 water, 200 impassable, 150 treacherous, 100 steep, 50 moderate, 10 easy
Image.fromarray(cls).save(os.path.join(OUT, "cost_class_30m.png"))
print(f"30 m cost classes: easy {(cls == 10).sum()}, moderate {(cls == 50).sum()}, steep {(cls == 100).sum()}, treacherous {(cls == 150).sum()}, impassable {(cls == 200).sum()} cells of {int(land30.sum())} land")

# 3. travel graph from OSM roads and trails
lines = []
for key in ("roads", "trails", "service", "paths", "tracks"):
    for g in L.get(key, []) or []:
        if g is None: continue
        if g.geom_type == "LineString": lines.append(g)
        elif g.geom_type == "MultiLineString": lines.extend(list(g.geoms))
u = unary_union(lines) if lines else None
segs = list(u.geoms) if u is not None and u.geom_type == "MultiLineString" else ([u] if u is not None else [])
ends = {}
for s in segs:
    for p in (s.coords[0], s.coords[-1]): ends[(round(p[0], 1), round(p[1], 1))] = ends.get((round(p[0], 1), round(p[1], 1)), 0) + 1
junctions = sum(1 for v in ends.values() if v >= 3); deadends = sum(1 for v in ends.values() if v == 1)
print(f"graph: {len(segs)} edges, {len(ends)} nodes ({junctions} junctions, {deadends} dead ends), {sum(s.length for s in segs) / 1000:.0f} km, mean edge {np.mean([s.length for s in segs]) if segs else 0:.0f} m")

# 4. budgets
print("grid budget:")
for r in (10, 30, 100):
    w, h = math.ceil(W * res / r), math.ceil(H * res / r); n = w * h
    print(f"  {r:>3} m: {w}x{h} = {n / 1e6:.2f} M cells; 16-bit raster {2 * n / 1e6:.1f} MB, 8-bit {n / 1e6:.1f} MB, bit mask {n / 8 / 1e6:.2f} MB")
for r, rad in ((30, 3000), (30, 5000), (60, 5000), (100, 10000)):
    print(f"  viewshed radius {rad} m at {r} m: {math.pi * (rad / r) ** 2 / 1e3:.0f} k cells")
print(f"done in {time.time() - t0:.0f} s")
