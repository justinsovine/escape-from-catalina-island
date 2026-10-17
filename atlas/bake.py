"""Bake the representation products the design spec relies on, and print the numbers it quotes.

- flood thresholds ("spill levels") per cove: for every cell and every cove, the lowest level of THAT cove's water
  at which the cell is wet through a connected path from that cove. Two (cove, threshold) pairs per cell are
  kept: the lowest-threshold cove on the north-east coast (the side facing the source) and the lowest on the
  south-west coast, so wet(cell, t) = thr_ne < level(cove_ne) or thr_sw < level(cove_sw). Coves on one coast
  share exposure and therefore levels; the two coasts meet only at the isthmus, which the pair rule covers from
  both directions. Sea cells carry the seabed (NOAA 1 m topobathy where fetched, else a deep default), so a
  drawdown below the datum exposes the shallows.
- slope and movement-cost classes at 30 m; the 30 m thresholds as block min and max.
- travel graph statistics from the OSM roads, trails and service roads.
- grid, raw and compressed size budget.
Outputs go to data/bake/ (gitignored) as raw little-endian uint16 and uint8 arrays with a JSON sidecar, plus
PNG copies of the 8-bit products. Run: python atlas/bake.py
"""
import os, sys, json, math, time, gzip, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.morphology import reconstruction
from shapely.ops import unary_union
from scenario.common import island
OUT = os.path.join(ROOT, "data", "bake"); os.makedirs(OUT, exist_ok=True)
OFFSET_M, UNIT_M, DEEP_M = 50.0, 0.1, -30.0          # encoding: uint16 = (threshold + 50 m) / 0.1 m; unknown seabed = -30 m
t0 = time.time()
A, Z, land, L, els = island(res=10)
H, W = Z.shape; res = A.res; sea = ~land
print(f"grid {W}x{H} at {res:g} m, land cells {int(land.sum())} ({land.sum() * res * res / 1e6:.1f} km2)")

# 0. the seabed: NOAA CoNED 1 m topobathy tiles (windowed harbor extracts from atlas/sources.py) resampled onto the grid
Zb = np.full((H, W), np.nan, "float32")
try:
    import rasterio
    from rasterio.warp import reproject, Resampling
    tiles = sorted(glob.glob(os.path.join(ROOT, "data", "dem", "topobathy", "coned_*.tif")))
    for f in tiles:
        with rasterio.open(f) as s:
            dst = np.full((H, W), np.nan, "float32")
            reproject(s.read(1), dst, src_transform=s.transform, src_crs=s.crs, src_nodata=s.nodata, dst_transform=A.transform, dst_crs=f"EPSG:{A.epsg}", dst_nodata=np.nan, resampling=Resampling.average)
            Zb = np.where(np.isnan(Zb), dst, Zb)
    print(f"seabed from topobathy on {int((~np.isnan(Zb) & sea).sum())} sea cells ({len(tiles)} tiles)")
except Exception as e: print("topobathy skipped:", e)
Zl = np.where(land, np.nan_to_num(Z.astype("float64"), nan=0.0), np.minimum(np.nan_to_num(Zb.astype("float64"), nan=DEEP_M), 0.0))
big = float(Zl.max()) + 100.0

# 1. coves: a partition of the sea by nearest named bay (the pack builder can replace this with drawn polygons)
COVES = [("Avalon", -118.3235, 33.3455, "ne"), ("Descanso and Hamilton", -118.3325, 33.3515, "ne"), ("Pebbly Beach", -118.3140, 33.3340, "sw"), ("East End", -118.3050, 33.3080, "sw"),
         ("Toyon and White's", -118.3560, 33.3765, "ne"), ("Long Point and Goat Harbor", -118.3700, 33.4050, "ne"), ("Empire Landing", -118.4600, 33.4380, "ne"), ("Big Fisherman Cove", -118.4870, 33.4440, "ne"),
         ("Isthmus Cove", -118.4985, 33.4460, "ne"), ("Fourth of July and Cherry", -118.5070, 33.4505, "ne"), ("Howlands and Emerald Bay", -118.5300, 33.4700, "ne"), ("Parsons Landing", -118.5520, 33.4770, "ne"),
         ("West End", -118.6020, 33.4790, "ne"), ("Catalina Harbor", -118.5075, 33.4300, "sw"), ("Little Harbor", -118.4790, 33.3880, "sw"), ("Ben Weston", -118.4830, 33.3700, "sw"),
         ("Cottonwood and Salta Verde", -118.4500, 33.3450, "sw"), ("Silver Canyon and Jewfish Point", -118.3500, 33.3150, "sw")]
SIDE = {i: side for i, (_, _, _, side) in enumerate(COVES, start=1)}
def rc(lon, lat):
    r, c = A.rc(*A.xy(lon, lat)); return int(np.asarray(r).ravel()[0]), int(np.asarray(c).ravel()[0])
anchors = np.array([rc(lo, la) for _, lo, la, _ in COVES], float)
rr, cc = np.mgrid[0:H, 0:W]
d2 = np.full((H, W), np.inf); cove = np.zeros((H, W), "uint8")
for i, (ar, ac) in enumerate(anchors, start=1):
    di = (rr - ar) ** 2 + (cc - ac) ** 2; better = di < d2; d2[better] = di[better]; cove[better] = i
cove[land] = 0
print(f"coves: {len(COVES)}; sea cells per cove min {int(np.bincount(cove[sea])[1:].min())} max {int(np.bincount(cove[sea])[1:].max())}")

# 2. per-cove thresholds; keep the lowest (cove, threshold) pair per coast side
best = {"ne": np.full((H, W), np.inf), "sw": np.full((H, W), np.inf)}; ids = {"ne": np.zeros((H, W), "uint8"), "sw": np.zeros((H, W), "uint8")}
for i, (name, _, _, side) in enumerate(COVES, start=1):
    mine = sea & (cove == i)
    seed = np.where(mine, Zl, big); mask = np.where(land | mine, Zl, big)       # other coves' water is blocked
    hk = reconstruction(seed, mask, method="erosion")
    b = hk < best[side]; best[side][b] = hk[b]; ids[side][b] = i
    print(f"  cove {i:2d} {name:32s} ({side}) done at {time.time() - t0:.0f} s", flush=True)
best1, best2, id1, id2 = best["ne"], best["sw"], ids["ne"], ids["sw"]
thr_global = np.minimum(best1, best2)                                         # the lowest of all coves = the single-seed result
tl = thr_global[land]
print(f"land wet at 5 m {(tl < 5).mean() * 100:.1f}%, 10 m {(tl < 10).mean() * 100:.1f}%, 20 m {(tl < 20).mean() * 100:.1f}%, 30 m {(tl < 30).mean() * 100:.1f}%; land cells at or below the datum {(tl <= 0).sum()}")

def wet_at(levels):
    """levels: dict cove id -> water level (m); the two-pair rule."""
    lv = np.full(len(COVES) + 1, -1e9)
    for k, v in levels.items(): lv[k] = v
    return (best1 < lv[id1]) | (best2 < lv[id2])
NAMES = [n for n, _, _, _ in COVES]; kI = NAMES.index("Isthmus Cove") + 1; kC = NAMES.index("Catalina Harbor") + 1
NORTH = [NAMES.index(n) + 1 for n in ("Isthmus Cove", "Fourth of July and Cherry", "Big Fisherman Cove")]
(ri, ci), (rcat, ccat) = rc(-118.4985, 33.4445), rc(-118.5075, 33.4325); split = (ri + rcat) // 2
box = np.zeros_like(land); box[max(min(ri, rcat) - 150, 0):max(ri, rcat) + 150, max(min(ci, ccat) - 150, 0):max(ci, ccat) + 150] = True
sea_n = box & sea & (rr < split); sea_s = box & sea & (rr > split)
def joined(wet):
    wl = land & wet; lab, n = ndimage.label(wl)
    tn = set(np.unique(lab[ndimage.binary_dilation(sea_n) & wl])) - {0}; ts = set(np.unique(lab[ndimage.binary_dilation(sea_s) & wl])) - {0}
    return bool(tn & ts)
coast_s = land & ndimage.binary_dilation(sea_s)
print(f"lowest path from the north-east coast water to the Cat Harbor shore: {best1[coast_s].min():.1f} m")
for Lv in (10.0, 10.5, 11.0):
    lv = {k: Lv for k in NORTH}; lv[kC] = Lv; print(f"  all isthmus coves at {Lv:4.1f} m: wet land body touches both harbors: {joined(wet_at(lv))}")
for LN, LC in ((12.0, 6.0), (6.0, 12.0), (10.5, 0.0), (0.0, 10.5), (12.0, 0.0), (0.0, 12.0)):
    lv = {k: LN for k in NORTH}; lv[kC] = LC; w = wet_at(lv); print(f"  north coves {LN:4.1f} m, Cat Harbor {LC:4.1f} m: wet land in the isthmus box {int((w & land & box).sum()) * res * res / 1e4:.1f} ha, harbors joined {joined(w)}")
print(f"  lowest path from Cat Harbor water to the Isthmus Cove shore: {np.where(id2 == kC, best2, np.inf)[land & ndimage.binary_dilation(sea_n)].min():.1f} m")
mineI = sea & (cove == kI); w = wet_at({kI: -2.0}); print(f"  drawdown to -2 m at Isthmus Cove exposes {int((mineI & ~w).sum()) * res * res / 1e4:.1f} ha of seabed")

# 3. encode and save: 10 m pairs, 30 m block min and max
def enc(a): return np.clip(np.round((a + OFFSET_M) / UNIT_M), 0, 65535).astype("<u2")
k = 3; H3, W3 = H // k, W // k
def blocks(a): return a[:H3 * k, :W3 * k].reshape(H3, k, W3, k).transpose(0, 2, 1, 3).reshape(H3, W3, k * k)
b1, b2, i1, i2 = blocks(best1), blocks(best2), blocks(id1), blocks(id2)
am = b1.argmin(axis=2); thr30_min = np.take_along_axis(b1, am[..., None], 2)[..., 0]; id30_1 = np.take_along_axis(i1, am[..., None], 2)[..., 0]; thr30_max = b1.max(axis=2)
am2 = b2.argmin(axis=2); thr30_2 = np.take_along_axis(b2, am2[..., None], 2)[..., 0]; id30_2 = np.take_along_axis(i2, am2[..., None], 2)[..., 0]
products = {"thr_ne_10m.u16": enc(best1), "thr_sw_10m.u16": enc(best2), "cove_ne_10m.u8": id1, "cove_sw_10m.u8": id2, "cove_10m.u8": cove,
            "thr_ne_min_30m.u16": enc(thr30_min), "thr_ne_max_30m.u16": enc(thr30_max), "thr_sw_min_30m.u16": enc(thr30_2), "cove_ne_30m.u8": id30_1, "cove_sw_30m.u8": id30_2}
sizes = {}
for name, a in products.items():
    raw = np.ascontiguousarray(a).tobytes(); open(os.path.join(OUT, name), "wb").write(raw); sizes[name] = (len(raw), len(gzip.compress(raw, 6)))
json.dump(dict(crs=f"EPSG:{A.epsg}", res_m=res, size_10m=[W, H], size_30m=[W3, H3], encoding=f"uint16 = (threshold_m + {OFFSET_M}) / {UNIT_M}; 0 = none; little endian", deep_default_m=DEEP_M,
               coves=[dict(id=i, name=n, lon=lo, lat=la, side=sd) for i, (n, lo, la, sd) in enumerate(COVES, start=1)], rule="wet(cell) = thr_ne < level[cove_ne] or thr_sw < level[cove_sw]"), open(os.path.join(OUT, "thresholds.json"), "w"), indent=1)
Image.fromarray(cove).save(os.path.join(OUT, "cove_10m.png"))
print("sizes (raw MB, gzip MB):", {n: (round(r / 1e6, 1), round(g / 1e6, 1)) for n, (r, g) in sizes.items()})
print(f"10 m pair set raw {sum(r for n, (r, g) in sizes.items() if '10m' in n) / 1e6:.1f} MB, gzip {sum(g for n, (r, g) in sizes.items() if '10m' in n) / 1e6:.1f} MB; 30 m set raw {sum(r for n, (r, g) in sizes.items() if '30m' in n) / 1e6:.1f} MB, gzip {sum(g for n, (r, g) in sizes.items() if '30m' in n) / 1e6:.1f} MB")

# 4. slope and cost classes (slope only here; the land-cover modifier is a pack-builder step)
Zf = np.nan_to_num(Z.astype("float64"), nan=0.0)
gy, gx = np.gradient(Zf, res); slope = np.degrees(np.arctan(np.hypot(gx, gy))); sl = slope[land]
print(f"slope on land: over 20 deg {(sl > 20).mean() * 100:.1f}%, over 30 {(sl > 30).mean() * 100:.1f}%, over 35 {(sl > 35).mean() * 100:.1f}%, over 45 {(sl > 45).mean() * 100:.1f}%")
Z30 = Zf[:H3 * k, :W3 * k].reshape(H3, k, W3, k).mean(axis=(1, 3)); land30 = land[:H3 * k, :W3 * k].reshape(H3, k, W3, k).mean(axis=(1, 3)) > 0.5
gy, gx = np.gradient(Z30, res * k); s30 = np.degrees(np.arctan(np.hypot(gx, gy)))
cls = np.select([~land30, s30 > 35, s30 > 30, s30 > 20, s30 > 10], [255, 200, 150, 100, 50], 10).astype("uint8")
Image.fromarray(cls).save(os.path.join(OUT, "cost_class_30m.png")); open(os.path.join(OUT, "cost_class_30m.u8"), "wb").write(cls.tobytes())
n30 = int(land30.sum()); print(f"30 m cost classes of {n30} land cells: easy {(cls == 10).sum() / n30 * 100:.1f}%, moderate {(cls == 50).sum() / n30 * 100:.1f}%, steep {(cls == 100).sum() / n30 * 100:.1f}%, treacherous {(cls == 150).sum() / n30 * 100:.1f}%, impassable {(cls == 200).sum() / n30 * 100:.1f}%")

# 5. travel graph from OSM roads, trails and service roads
lines = []
for key in ("roads", "trails", "service"):
    for g in L.get(key, []) or []:
        if g is None: continue
        if g.geom_type == "LineString": lines.append(g)
        elif g.geom_type == "MultiLineString": lines.extend(list(g.geoms))
u = unary_union(lines); segs = list(u.geoms) if u.geom_type == "MultiLineString" else [u]
ends = {}
for s in segs:
    for p in (s.coords[0], s.coords[-1]):
        kk = (round(p[0], 1), round(p[1], 1)); ends[kk] = ends.get(kk, 0) + 1
print(f"graph: {len(segs)} edges, {len(ends)} nodes ({sum(1 for v in ends.values() if v >= 3)} junctions, {sum(1 for v in ends.values() if v == 1)} dead ends), {sum(s.length for s in segs) / 1000:.0f} km, mean edge {np.mean([s.length for s in segs]):.0f} m, {sum(len(s.coords) for s in segs)} vertices")

# 6. budgets
print("grid budget:")
for r in (10, 30, 100):
    w, h = math.ceil(W * res / r), math.ceil(H * res / r); n = w * h
    print(f"  {r:>3} m: {w}x{h} = {n / 1e6:.2f} M cells; 16-bit raster {2 * n / 1e6:.1f} MB, 8-bit {n / 1e6:.1f} MB, bit mask {n / 8 / 1e6:.2f} MB")
for r, rad in ((30, 3000), (30, 5000), (60, 5000)):
    print(f"  viewshed radius {rad} m at {r} m: {math.pi * (rad / r) ** 2 / 1e3:.0f} k cells")
print(f"done in {time.time() - t0:.0f} s")
