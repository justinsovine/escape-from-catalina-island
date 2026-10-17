"""Atlas sheets: the whole island at 10 m, and town insets from 1 m lidar. Everything from atlas/out plus the DEMs.
Run: python atlas/map.py island | avalon | twoharbors | all"""
import os, sys, csv, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, to_rgb
from matplotlib.lines import Line2D
from scipy.ndimage import gaussian_filter, label
from shapely.geometry import shape, Point
from shapely import transform as sh_t
from mapgame import dem, osm as O
from mapgame.area import Area
from mapgame.palette import get
from scenario.common import osm_elements, dem_path, cgs_hazard, lidar_mosaic
from shapely.ops import unary_union

OUT = os.path.join(HERE, "out"); P = get("night")
SHEETS = {"island": dict(bbox=(-118.625, 33.295, -118.285, 33.495), res=10.0, size=(24, 15.5), detail=0, title="SANTA CATALINA ISLAND", sub="the whole island · roads, trails, water, camps, shelter, infrastructure · tsunami zones"),
          "avalon": dict(bbox=(-118.345, 33.328, -118.300, 33.358), res=2.0, size=(16, 11.5), detail=2, title="AVALON", sub="1 m lidar · every mapped business, water source and building"),
          "twoharbors": dict(bbox=(-118.532, 33.418, -118.468, 33.462), res=2.0, size=(16, 11.5), detail=2, title="TWO HARBORS", sub="1 m lidar · the isthmus, Cat Harbor, Isthmus Cove, Fourth of July, Cherry Cove")}
KIND_STYLE = {  # marker, color, size, min detail level to draw, label at detail >=
    "water": ("v", "#49c9ff", 7, 0, 1), "camp": ("^", "#ff6b5c", 7, 0, 1), "medical": ("P", "#ff4d4d", 9, 0, 0), "emergency": ("D", "#ff4d4d", 6, 0, 1), "fuel": ("s", "#ffd23f", 7, 0, 1),
    "transport": ("*", "#ffffff", 9, 0, 1), "infrastructure": ("s", "#b9c7cf", 5, 0, 2), "shelter": ("h", "#d6a3ff", 8, 0, 0), "food": ("o", "#ffb000", 6, 1, 2), "store": ("s", "#ffd23f", 6, 1, 2),
    "lodging": ("o", "#c9a6ff", 4, 2, 2), "civic": ("o", "#dfe6ea", 4, 1, 2), "poi": (".", "#9fb0bb", 4, 2, 9), "place": ("", "", 0, 9, 9), "land": ("", "", 0, 9, 9)}

def load_points(A):
    pts = []
    for r in csv.DictReader(open(os.path.join(OUT, "features.csv"))):
        x, y = A.xy(float(r["lon"]), float(r["lat"])); r["x"], r["y"] = x, y; pts.append(r)
    return pts

def gj(name, A):
    """GeoJSON from atlas/out in map coordinates, clipped to the sheet."""
    f = os.path.join(OUT, name)
    if not os.path.exists(f): return []
    out = []
    for ft in json.load(open(f))["features"]:
        g = sh_t(shape(ft["geometry"]), lambda c: np.c_[A.xy(c[:, 0], c[:, 1])])
        if g.intersects(A.plate): out.append((g.intersection(A.plate), ft["properties"]))
    return out

def render(key):
    S = SHEETS[key]; A = Area(*S["bbox"], res=S["res"]); det = S["detail"]
    els = osm_elements(); L = O.layers(A, els); land = O.land_mask(A, L)
    Z = dem.from_geotiff(A, dem_path()); src = "USGS 3DEP 10 m"
    if S["res"] < 10:
        Z1 = lidar_mosaic(A); cov = float(np.isfinite(Z1).mean())
        if cov > 0: Z = np.where(np.isnan(Z1), Z, Z1); src = f"USGS 3DEP 1 m lidar ({cov * 100:.0f}%) over 10 m"
    Z = np.nan_to_num(Z, nan=0.0).astype("float32"); H, W = Z.shape
    xl, yb, xr, yt = A.E0, A.N0, A.E0 + A.W * A.res, A.N0 + A.H * A.res
    k = max(1.0, 3.0 / A.res)
    hs = LightSource(azdeg=315, altdeg=42).hillshade(gaussian_filter(Z, k * 0.5), vert_exag=1.6 if det else 2.2, dx=A.res, dy=A.res)
    Zs = gaussian_filter(Z, k * 2)
    t = np.clip(Zs / 600.0, 0, 1)[..., None]
    lo, hi = np.array(P["slab_lo"]), np.array(P["slab_hi"])
    img = (lo + (hi - lo) * t) * (0.55 + 0.9 * hs)[..., None]
    img[~land] = to_rgb(P["plate"])
    def flooded(h):                                     # ground below h that the sea reaches (the sea is the biggest non-land component)
        lab, _ = label((~land) | (Z < h)); sea = np.bincount(lab[~land].ravel()).argmax() if (~land).any() else -1
        return (lab == sea) & land
    F20, F10 = flooded(20.0), flooded(10.5)
    blue = np.array(to_rgb(P["days"]["tue"]))
    for m, a in ((F20, 0.30), (F10, 0.60)): img[m] = img[m] * (1 - a) + blue * a
    img = np.clip(img, 0, 1)
    fig = plt.figure(figsize=S["size"], dpi=150, facecolor=P["bg"]); ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(P["bg"]); ax.axis("off")
    ax.imshow(img, extent=[xl, xr, yb, yt], interpolation="bilinear", zorder=1)
    X = xl + (np.arange(W) + 0.5) * A.res; Y = yt - (np.arange(H) + 0.5) * A.res
    ax.contour(X, Y, np.where(land, Zs, -50), levels=np.arange(100, 700, 100) if not det else np.arange(25, 700, 25), colors=[P["slab_edge"]], linewidths=0.25, alpha=0.5, zorder=2)
    haz = unary_union(cgs_hazard(A)).intersection(A.plate)
    for g in (haz.geoms if hasattr(haz, "geoms") else [haz]):
        if g.geom_type == "Polygon":
            for ring in [g.exterior] + list(g.interiors): ax.plot(*ring.xy, color="#9fe8ff", lw=0.8, alpha=0.9, ls=(0, (3, 2)), zorder=6)
    for g, p in gj("waters.geojson", A):
        for part in (g.geoms if hasattr(g, "geoms") else [g]):
            if part.geom_type == "Polygon": ax.fill(*part.exterior.xy, fc="#2f8fd0", ec="#8fd0ff", lw=0.4, alpha=0.9, zorder=4)
    for g, p in gj("coasts.geojson", A):
        for part in (g.geoms if hasattr(g, "geoms") else [g]):
            if part.geom_type == "LineString": ax.plot(*part.xy, color=P["pier"], lw=0.4 if not det else 0.6, alpha=0.6, zorder=2.5)
    for g, p in gj("roads.geojson", A):
        for part in (g.geoms if hasattr(g, "geoms") else [g]):
            if part.geom_type == "LineString":
                major = p.get("highway") in ("secondary", "tertiary", "primary", "unclassified")
                ax.plot(*part.xy, color="#e8eef2" if major else P["road"], lw=(1.1 if major else 0.6) * (1.3 if det else 1), alpha=0.95 if major else 0.75, zorder=4.5)
    for g, p in gj("trails.geojson", A):
        for part in (g.geoms if hasattr(g, "geoms") else [g]):
            if part.geom_type == "LineString": ax.plot(*part.xy, color=P["road"], lw=0.45 * (1.4 if det else 1), alpha=0.75, ls=(0, (2, 1.5)), zorder=4.4)
    for g, p in gj("tct.geojson", A):
        for part in (g.geoms if hasattr(g, "geoms") else [g]):
            if part.geom_type == "LineString":
                ax.plot(*part.xy, color=P["bg"], lw=2.6, solid_capstyle="round", zorder=4.6); ax.plot(*part.xy, color=P["route"], lw=1.3, solid_capstyle="round", zorder=4.7)
    for g, p in gj("piers.geojson", A):
        for part in (g.geoms if hasattr(g, "geoms") else [g]):
            if part.geom_type == "LineString": ax.plot(*part.xy, color=P["pier"], lw=1.6 if det else 1.0, solid_capstyle="round", zorder=5)
    for g, p in gj("buildings.geojson", A):
        for part in (g.geoms if hasattr(g, "geoms") else [g]):
            if part.geom_type == "Polygon": ax.fill(*part.exterior.xy, fc=P["building"][0], ec="none", alpha=0.95, zorder=5)
    # points
    pts = [r for r in load_points(A) if xl < r["x"] < xr and yb < r["y"] < yt and r["subtype"] != "camp_pitch"]
    placed = []; LAB = 7.5 if det else 6.5
    def text(x, y, s, color, size=LAB, dy=0, **kw):
        if any(abs(x - px) < (len(s) * size * 0.9 + 8) * A.res / (0.45 if det else 1) * 0 + size * 0.6 * len(s) * (A.res * 1.3) and abs(y + dy - py) < size * 2.2 * A.res for px, py in placed): return
        placed.append((x, y + dy)); ax.text(x, y + dy, s, color=color, fontsize=size, family="monospace", ha="center", va="bottom", zorder=12, bbox=dict(boxstyle="square,pad=0.15", fc=P["bg"], ec="none", alpha=0.6), **kw)
    for r in sorted(pts, key=lambda r: {"medical": 0, "emergency": 1, "shelter": 2, "water": 3, "fuel": 4, "camp": 5, "transport": 6, "store": 7, "food": 8}.get(r["kind"], 9)):
        mk, col, ms, mind, labd = KIND_STYLE.get(r["kind"], ("", "", 0, 9, 9))
        if not mk or det < mind: continue
        if r["kind"] == "transport" and r["subtype"] not in ("aerodrome", "helipad", "ferry_terminal", "pier", "slipway", "hangar") and not det: continue
        if r["kind"] == "infrastructure" and not det and r["subtype"] not in ("plant", "generator", "substation", "storage_tank", "reservoir_covered", "quarry", "tower", "lighthouse", "wastewater_plant", "works"): continue
        if r["kind"] == "water" and r["subtype"] in ("water",) and not det: continue      # the reservoirs are drawn as polygons
        ax.plot(r["x"], r["y"], marker=mk, ms=ms * (1.15 if det else 1), mfc=col, mec=P["bg"], mew=0.6, ls="none", zorder=10)
        if r["name"] and det >= labd: text(r["x"], r["y"], r["name"][:28], col, dy=ms * 1.6 * A.res * (2.2 if det else 1))
    # names of places, bays and summits
    PLACE = {"town": LAB + 4, "village": LAB + 3, "hamlet": LAB + 1.5, "locality": LAB, "neighbourhood": LAB, "farm": LAB, "islet": LAB - 1}
    for r in pts:
        if r["kind"] == "place" and r["name"] and r["subtype"] in PLACE:
            big = r["subtype"] in ("town", "village", "hamlet")
            text(r["x"], r["y"], r["name"].upper() if big else r["name"], P["label"] if big else "#c7d4dc", size=PLACE[r["subtype"]], dy=0)
    for r in pts:
        if r["kind"] == "land" and r["subtype"] in ("bay", "beach", "cape") and r["name"] and (det or len(r["name"]) < 22): text(r["x"], r["y"], r["name"], "#9fb8c8", size=LAB - 0.5)
    peaks = sorted([r for r in pts if r["kind"] == "land" and r["subtype"] == "peak" and r["name"]], key=lambda r: -float(r["elev_m"]))[:10 if not det else 4]
    for r in peaks: ax.plot(r["x"], r["y"], marker="^", ms=5, mfc=P["bg"], mec=P["peak"], mew=0.8, ls="none", zorder=10); text(r["x"], r["y"], f"{r['name']} {float(r['elev_m']) * 3.281:.0f} ft", P["label"], size=LAB - 0.5, dy=60 * A.res / 10)
    # furniture
    box = dict(boxstyle="square,pad=0.35", fc=P["bg"], ec="none", alpha=0.8)
    ax.text(0.015, 0.975, S["title"], transform=ax.transAxes, color=P["title"], fontsize=20 if not det else 16, family="monospace", weight="bold", va="top", bbox=box)
    ax.text(0.015, 0.935, S["sub"], transform=ax.transAxes, color=P["muted"], fontsize=9, family="monospace", va="top", bbox=box)
    ax.text(0.985, 0.975, f"{src} · OpenStreetMap · CGS tsunami hazard area", transform=ax.transAxes, color=P["muted"], fontsize=7.5, family="monospace", ha="right", va="top", bbox=box)
    handles = [Line2D([], [], marker=KIND_STYLE[k][0], color=KIND_STYLE[k][1], ls="none", ms=7, label=lab) for k, lab in (("water", "water source"), ("camp", "campground"), ("medical", "medical"), ("emergency", "fire / sheriff / lifeguard"), ("fuel", "fuel"), ("transport", "pier / terminal / airfield"), ("infrastructure", "power, tanks, towers, quarry"), ("shelter", "shelter, cave, mine, ruin"), ("food", "food"), ("store", "store"), ("lodging", "lodging")) if det >= KIND_STYLE[k][3]]
    handles += [Line2D([], [], color=P["route"], lw=1.5, label="Trans-Catalina Trail"), Line2D([], [], color="#e8eef2", lw=1.2, label="road"), Line2D([], [], color=P["road"], lw=0.8, ls=(0, (2, 1.5)), label="trail / track"),
                Line2D([], [], color="#9fe8ff", lw=1.0, ls=(0, (3, 2)), label="CGS tsunami hazard area"), Line2D([], [], marker="s", color=np.clip(lo * 0.9 * 0.4 + blue * 0.6, 0, 1), ls="none", ms=9, label="below 10.5 m run-up"), Line2D([], [], marker="s", color=np.clip(lo * 0.9 * 0.7 + blue * 0.3, 0, 1), ls="none", ms=9, label="below 20 m run-up")]
    leg = ax.legend(handles=handles, loc="lower right", fontsize=7.5, frameon=True, facecolor=P["bg"], edgecolor=P["plate_edge"], labelcolor=P["label"], ncol=2 if not det else 1, borderpad=0.8)
    for txt in leg.get_texts(): txt.set_family("monospace")
    leg.set_zorder(40); leg.get_frame().set_alpha(0.95)
    L_km = 5000 if not det else 500; sx = xl + (xr - xl) * 0.02; sy = yb + (yt - yb) * 0.03
    ax.plot([sx, sx + L_km], [sy, sy], color=P["label"], lw=2, zorder=20); ax.text(sx + L_km / 2, sy + (yt - yb) * 0.008, f"{L_km / 1000:g} km", color=P["label"], fontsize=8, family="monospace", ha="center", zorder=20, bbox=box)
    ax.set_xlim(xl, xr); ax.set_ylim(yb, yt); ax.set_aspect("equal")
    out = os.path.join(OUT, f"atlas_{key}.png"); fig.savefig(out, facecolor=fig.get_facecolor()); plt.close(fig); print("wrote", out, src)

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    for key in (SHEETS if which == "all" else [which]): render(key)
