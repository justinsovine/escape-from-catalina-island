"""Escape from Catalina, act I: the Two Harbors isthmus with run-up bands, the state's tsunami hazard line and the
nearest high ground. Elevation from USGS 3DEP 1 m lidar when --res is under 10 (tiles fetched on demand), else 10 m.
Run: python scenario/flood_map.py [out.png] [--res 2] [--palette night]"""
import argparse, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, to_rgb
from matplotlib.patches import FancyArrowPatch, Rectangle
from scipy.ndimage import distance_transform_edt, gaussian_filter, label
from shapely.geometry import Point
from shapely.ops import unary_union
from mapgame import dem, osm as O
from mapgame.area import Area
from mapgame.palette import get
from scenario.common import osm_elements, dem_path, cgs_hazard, lidar_mosaic

ap = argparse.ArgumentParser()
ap.add_argument("out", nargs="?", default=os.path.join(ROOT, "examples", "isthmus_flood.png"))
ap.add_argument("--res", type=float, default=2.0); ap.add_argument("--palette", default="night")
args = ap.parse_args(); P = get(args.palette)

W = (-118.532, 33.418, -118.468, 33.462)
A = Area(*W, res=args.res)
L = O.layers(A, osm_elements()); land = O.land_mask(A, L)
Z = dem.from_geotiff(A, dem_path()); src = "USGS 3DEP 10 m"
if args.res < 10:
    Z1 = lidar_mosaic(A); cov = float(np.isfinite(Z1).mean())
    if cov > 0: Z = np.where(np.isnan(Z1), Z, Z1); src = f"USGS 3DEP 1 m lidar ({cov * 100:.0f}% of the window) over 10 m"
Z = np.nan_to_num(Z, nan=0.0).astype("float32"); H, Wd = Z.shape
xl, yb, xr, yt = A.E0, A.N0, A.E0 + A.W * A.res, A.N0 + A.H * A.res
def rc(lon, lat):
    r, c = A.rc(*A.xy(lon, lat)); return int(r), int(c)

# the two numbers the map is about: the run-up that joins the harbors, and the nearest safe ground from the town
sNE, sSW = rc(-118.4935, 33.4490), rc(-118.5105, 33.4245)
assert not land[sNE] and not land[sSW], "seed points must be in the sea"
OVER = next(h for h in np.arange(0.5, 80, 0.5) if (lambda lab: lab[sNE] == lab[sSW])(label((~land) | (Z < h))[0]))
town = A.xy(-118.4979, 33.4423)
def nearest(thr):
    dist, idx = distance_transform_edt(~(land & (Z >= thr)), return_distances=True, return_indices=True)
    r, c = rc(-118.4979, 33.4423); tr, tc = idx[0][r, c], idx[1][r, c]
    return dist[r, c] * A.res, (xl + (tc + 0.5) * A.res, yt - (tr + 0.5) * A.res)
d30, q30 = nearest(30); d100, q100 = nearest(100)
print(f"{src}; run-up joining the harbors {OVER:g} m; 30 m ground {d30:.0f} m from town, 100 m ground {d100:.0f} m")

# the picture: hillshaded land by height, flat sea, three run-up tints
k = max(1.0, 3.0 / A.res)
hs = LightSource(azdeg=315, altdeg=42).hillshade(gaussian_filter(Z, k * 0.5), vert_exag=1.8, dx=A.res, dy=A.res)
Zs = gaussian_filter(Z, k * 2)
t = np.clip(Zs / 320.0, 0, 1)[..., None]
lo, hi = np.array(P["slab_lo"]), np.array(P["slab_hi"])
img = (lo + (hi - lo) * t) * (0.55 + 0.9 * hs)[..., None]
img[~land] = to_rgb(P["plate"])
blue = np.array(to_rgb(P["days"]["tue"]))
for zmax, a in ((30, 0.18), (20, 0.34), (OVER, 0.62)):
    m = land & (Z < zmax); img[m] = img[m] * (1 - a) + blue * a
img = np.clip(img, 0, 1)

fig = plt.figure(figsize=(12, 9.6), dpi=170, facecolor=P["bg"]); ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(P["bg"]); ax.axis("off")
ax.imshow(img, extent=[xl, xr, yb, yt], interpolation="bilinear", zorder=1)
X = xl + (np.arange(Wd) + 0.5) * A.res; Y = yt - (np.arange(H) + 0.5) * A.res; Zc = np.where(land, Zs, -50)
ax.contour(X, Y, Zc, levels=np.arange(50, 700, 50), colors=[P["slab_edge"]], linewidths=0.3, alpha=0.55, zorder=2)
ax.contour(X, Y, Zc, levels=[OVER], colors=[P["days"]["mon"]], linewidths=1.0, zorder=3)
ax.contour(X, Y, Zc, levels=[30], colors=[P["days"]["tue"]], linewidths=0.9, linestyles="--", zorder=3)
Lc = O.clip(L, A.plate)
for g in Lc["coast"]: ax.plot(*g.xy, color=P["pier"], lw=0.5, alpha=0.6, zorder=2.5)
for g in Lc["roads"]: ax.plot(*g.xy, color=P["road"], lw=0.8, alpha=0.9, zorder=4)
for g in Lc["service"]: ax.plot(*g.xy, color=P["road"], lw=0.5, alpha=0.5, zorder=4)
for g in Lc["trails"]: ax.plot(*g.xy, color=P["road"], lw=0.6, alpha=0.7, ls=(0, (2, 1.5)), zorder=4)
for g in Lc["piers"]: ax.plot(*g.xy, color=P["pier"], lw=2.0, solid_capstyle="round", zorder=5)
for b in Lc["buildings"]: ax.fill(*b.exterior.xy, fc=P["building"][0], ec="none", alpha=0.95, zorder=5)

# the state's own line: California Geological Survey tsunami hazard area
yel = P["days"]["wed"]
haz = unary_union(cgs_hazard(A)).intersection(A.plate)
for g in (haz.geoms if hasattr(haz, "geoms") else [haz]):
    if g.geom_type != "Polygon": continue
    for ring in [g.exterior] + list(g.interiors): ax.plot(*ring.xy, color=yel, lw=1.1, alpha=0.95, zorder=6)

# the arrows to safe ground
for thr, dd, q, side in ((30, d30, q30, -1), (100, d100, q100, 1)):
    ax.add_patch(FancyArrowPatch(town, q, arrowstyle="-|>", mutation_scale=16, color=yel, lw=2.0, zorder=7, shrinkA=4, shrinkB=0))
    ax.text(q[0] - 60, q[1] + 70 * side, f"{thr} m ground\n{dd:.0f} m · run {dd / 3 / 60:.1f} min · walk {dd / 1.4 / 60:.1f} min", color=yel, fontsize=8.5, family="monospace",
            ha="right", va="center", zorder=8, bbox=dict(boxstyle="square,pad=0.3", fc=P["bg"], ec="none", alpha=0.75))
ax.plot(*town, "o", ms=7, mfc=P["days"]["mon"], mec=P["bg"], mew=1.2, zorder=8)
ax.text(town[0] + 70, town[1] - 10, "you are here\n11:15 ferry, pack on", color=P["label"], fontsize=8.5, family="monospace", va="center", zorder=8,
        bbox=dict(boxstyle="square,pad=0.3", fc=P["bg"], ec="none", alpha=0.75))
box = dict(boxstyle="square,pad=0.25", fc=P["bg"], ec="none", alpha=0.7)
for x, y, n in L["places"]:
    if A.plate.contains(Point(x, y)) and n in ("Two Harbors", "Isthmus Cove", "Catalina Harbor", "Cherry Cove", "Fourth of July Cove"):
        ax.text(x, y + 60, n.upper(), color=P["label"], fontsize=9 if n == "Two Harbors" else 7.5, family="monospace", ha="center", zorder=9, bbox=box)
ax.text(*A.xy(-118.5085, 33.4290), "CATALINA HARBOR\nlee side: do the boats survive?", color=P["label"], fontsize=7.5, family="monospace", ha="center", zorder=9, bbox=box)
ax.text(*A.xy(-118.4925, 33.4475), "ISTHMUS COVE\nfaces the mainland", color=P["label"], fontsize=7.5, family="monospace", ha="center", zorder=9, bbox=box)

# title, timeline, legend, scale, north
ax.text(0.03, 0.965, "ESCAPE FROM CATALINA", transform=ax.transAxes, color=P["title"], fontsize=17, family="monospace", weight="bold", va="top", bbox=dict(boxstyle="square,pad=0.3", fc=P["bg"], ec="none", alpha=0.75))
ax.text(0.03, 0.925, "act I · the flash · Two Harbors isthmus", transform=ax.transAxes, color=P["muted"], fontsize=9.5, family="monospace", va="top", bbox=dict(boxstyle="square,pad=0.3", fc=P["bg"], ec="none", alpha=0.75))
tl = ["00:00  flash over the LA harbor, 23 mi NE", "01:50  the sound arrives", "~03:00  harbor drains: the sea pulls back", "08-15  min  wave arrives (shelf break / harbor source)",
      f"{OVER:g} m   run-up joins the two harbors: the isthmus is sea", f"30 m   the safe line, {d30:.0f} m from the town"]
ax.text(0.03, 0.045, "\n".join(tl), transform=ax.transAxes, color=P["label"], fontsize=8.5, family="monospace", va="bottom", bbox=dict(boxstyle="square,pad=0.5", fc=P["bg"], ec=P["plate_edge"], alpha=0.85))
rows = [("swatch", 0.62, f"below {OVER:g} m: under water"), ("swatch", 0.34, f"{OVER:g} to 20 m: likely wet"), ("swatch", 0.18, "20 to 30 m: splash zone"),
        ("line", P["days"]["tue"], "30 m contour"), ("line", yel, "CGS tsunami hazard area")]
for i, (kind, v, lab) in enumerate(rows):
    y = 0.175 - i * 0.034
    if kind == "swatch": ax.add_patch(Rectangle((0.72, y - 0.011), 0.025, 0.022, transform=ax.transAxes, fc=np.clip(lo * 0.9 * (1 - v) + blue * v, 0, 1), ec="none", zorder=20))
    else: ax.plot([0.72, 0.745], [y, y], transform=ax.transAxes, color=v, lw=1.0, ls="--" if lab.startswith("30") else "-", zorder=20)
    ax.text(0.752, y, lab, transform=ax.transAxes, color=P["label"], fontsize=8, family="monospace", va="center", zorder=20)
sx = xl + (xr - xl) * 0.42; sy = yb + 250
ax.plot([sx, sx + 1000], [sy, sy], color=P["label"], lw=2, zorder=20); ax.text(sx + 500, sy + 40, "1 km", color=P["label"], fontsize=8, family="monospace", ha="center", zorder=20)
ax.annotate("N", xy=(xr - 300, yt - 250), xytext=(xr - 300, yt - 650), color=P["label"], fontsize=10, family="monospace", ha="center", arrowprops=dict(arrowstyle="-|>", color=P["label"]), zorder=20)
ax.text(0.97, 0.965, f"{src} · OpenStreetMap · CGS · bands are elevation, not a wave model", transform=ax.transAxes, color=P["muted"], fontsize=7.5, family="monospace", ha="right", va="top")
ax.set_xlim(xl, xr); ax.set_ylim(yb, yt); ax.set_aspect("equal")
os.makedirs(os.path.dirname(args.out), exist_ok=True); fig.savefig(args.out, facecolor=fig.get_facecolor()); print("wrote", args.out)
