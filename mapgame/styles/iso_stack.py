"""Stacked laser-cut contour model, dark. Each elevation band is a slab; buildings, streams, trails and the
route sit on the slab they belong to. The same polygons would drive a laser cutter."""
import numpy as np
from rasterio import features
from shapely.geometry import shape, Point
from shapely.ops import unary_union
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from .. import FT
from ..area import iso
from ..osm import clip


def slab_polygons(area, zf, land, levels, min_area=4000):
    """Per level: polygons (with holes) of ground at or above that height. These are the cut files."""
    out = []
    for k, lv in enumerate(levels):
        mask = (land & (zf >= lv)) if k else land
        polys = []
        for geom, v in features.shapes(mask.astype("uint8"), mask=mask, transform=area.transform):
            if v == 1:
                g = shape(geom).simplify(area.res * 0.8)
                if g.area >= min_area: polys.append(g)
        out.append(polys)
    return out


def render(S, out, size=(12, 15), dpi=160):
    A, Z, osm = S["area"], S["Z"], S["osm"]
    zf = Z * FT
    land = S["land"] if S.get("land") is not None else np.isfinite(zf) & (zf > S["sea_ft"])
    zf = np.where(land, zf, np.nan)
    STEP, T = S["step_ft"], S["slab_m"]
    levels = np.arange(0, np.nanmax(zf), STEP)
    plate = A.plate
    osm = clip(osm, plate)
    route = S["route"].intersection(plate) if S["route"] is not None else None

    def patch(g, lift=0.0, **kw):
        verts, codes = [], []
        for ring in [g.exterior] + list(g.interiors):
            xs, ys = iso(*np.array(ring.coords).T); pts = np.c_[xs, ys + lift]
            verts += pts.tolist(); codes += [Path.MOVETO] + [Path.LINETO] * (len(pts) - 2) + [Path.CLOSEPOLY]
        return PathPatch(Path(verts, codes), **kw)

    fig = plt.figure(figsize=size, dpi=dpi, facecolor="#0c0c0c"); ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor("#0c0c0c"); ax.axis("off")
    EDGE = "#b9b9b9"
    for lift in (-2 * T, -T):
        ax.add_patch(patch(plate, lift=lift, facecolor="#0f0f0f", edgecolor=EDGE, lw=0.5, zorder=0))
    ax.add_patch(patch(plate, facecolor="#141414", edgecolor=EDGE, lw=0.6, zorder=1))
    for k, polys in enumerate(slab_polygons(A, zf, land, levels)):
        lift = (k + 1) * T; shade = 0.11 + 0.01 * k
        for g in polys:
            ax.add_patch(patch(g, lift=lift - T, facecolor=(shade + .09,) * 3, edgecolor=EDGE, lw=0.5, zorder=10 + 3 * k))
            ax.add_patch(patch(g, lift=lift, facecolor=(shade,) * 3, edgecolor=EDGE, lw=0.7, zorder=11 + 3 * k))

    def lift_at(x, y):
        z = A.sample(zf, x, y); k = np.clip(np.floor(z / STEP), 0, len(levels) - 1); return (k + 1) * T

    def draw_line(geom, **kw):
        for part in (geom.geoms if hasattr(geom, "geoms") else [geom]):
            if part.geom_type != "LineString": continue
            xy = np.array(part.coords); x, y = xy[:, 0], xy[:, 1]; sx, sy = iso(x, y); ax.plot(sx, sy + lift_at(x, y), **kw)
    for ls in osm["streams"]: draw_line(ls, color="#8fa3ad", lw=0.6, alpha=.8, zorder=200)
    for ls in osm["roads"]: draw_line(ls, color="#d8d8d8", lw=0.6, zorder=201)
    for ls in osm["trails"]: draw_line(ls, color="#d8d8d8", lw=0.45, ls=(0, (2, 2)), zorder=201)
    for ls in osm["piers"]: draw_line(ls, color="#f0f0f0", lw=2.2, solid_capstyle="round", zorder=205)
    if route is not None: draw_line(route, color="#ffffff", lw=1.4, ls=(0, (3, 2)), zorder=202)
    for x, y, name in S["ports"]:        # a boat at each port, where the reference image had an airplane
        sx, sy = iso(x - 260, y + 120)
        ax.plot([sx - 26, sx + 26], [sy + 2, sy + 2], color="#f4f4f4", lw=3.5, solid_capstyle="round", zorder=206)
        ax.plot([sx - 8, sx + 10], [sy + 8, sy + 8], color="#f4f4f4", lw=3, solid_capstyle="round", zorder=206)
    for b in osm["buildings"]:           # tiny boxes, three faces
        c = b.centroid; w = max(8, min(40, np.sqrt(b.area))); x, y = c.x, c.y; h = lift_at(x, y); bh = 9
        sq = [(x - w / 2, y - w / 2), (x + w / 2, y - w / 2), (x + w / 2, y + w / 2), (x - w / 2, y + w / 2)]
        sx, sy = iso(*np.array(sq).T)
        ax.fill(sx, sy + h + bh, color="#e8e8e8", lw=0.3, ec="#333", zorder=300)
        ax.fill([sx[0], sx[1], sx[1], sx[0]], [sy[0] + h, sy[1] + h, sy[1] + h + bh, sy[0] + h + bh], color="#9a9a9a", lw=0.3, ec="#333", zorder=299)
        ax.fill([sx[1], sx[2], sx[2], sx[1]], [sy[1] + h, sy[2] + h, sy[2] + h + bh, sy[1] + h + bh], color="#c4c4c4", lw=0.3, ec="#333", zorder=299)
    rng = np.random.default_rng(3); tree_pts = []
    if osm["wood"]:                      # real forest polygons when OSM has them
        u = unary_union(osm["wood"]); minx, miny, maxx, maxy = u.bounds
        cand = np.c_[rng.uniform(minx, maxx, 6000), rng.uniform(miny, maxy, 6000)]
        tree_pts = [tuple(p) for p in cand if u.contains(Point(p))][:900]
    else:                                # stand-in: along streams below the tree line
        p_tree = .12 if S["sea_ft"] < 0 else .45
        for ls in osm["streams"]:
            for d in np.arange(0, ls.length, 90):
                p = ls.interpolate(d)
                if A.sample(zf, p.x, p.y) < S["tree_ft"] and rng.random() < p_tree: tree_pts.append((p.x + rng.normal(0, 25), p.y + rng.normal(0, 25)))
    for x, y in tree_pts:
        h = lift_at(x, y); sx, sy = iso(x, y); sy += h
        ax.plot([sx, sx], [sy, sy + 14], color="#cfcfcf", lw=0.5, zorder=310)
        ax.plot([sx - 7, sx, sx + 7, sx - 7], [sy + 6, sy + 22, sy + 6, sy + 6], color="#e6e6e6", lw=0.5, zorder=310)
    for x, y, name in osm["peaks"]:
        sx, sy = iso(x, y); ax.plot(sx, sy + lift_at(x, y) + 6, marker="^", ms=4, color="#fff", zorder=320)
        if name: ax.text(sx + 30, sy + lift_at(x, y) + 20, name, color="#dcdcdc", fontsize=7, family="monospace", zorder=320)
    for x, y, name in osm["camps"]:
        sx, sy = iso(x, y); ax.plot(sx, sy + lift_at(x, y) + 6, marker="^", ms=5, mfc="#0c0c0c", mec="#fff", mew=.8, zorder=320)
    labels = S["labels"] or [(x, y, n.upper()) for x, y, n in osm["places"][:8]]
    for x, y, name in labels:
        sx, sy = iso(x, y); ax.text(sx, sy + lift_at(x, y) + 60, name, color="#f2f2f2", fontsize=10, family="monospace", ha="center", zorder=330)
    x0, y0, x1, y1 = plate.bounds
    sx, sy = iso(np.array([x0, x1, x1, x0]), np.array([y0, y0, y1, y1]))
    ax.set_xlim(sx.min() - 300, sx.max() + 300); ax.set_ylim(sy.min() - 3 * T - 300, sy.max() + len(levels) * T + 600); ax.set_aspect("equal")
    fig.text(0.04, 0.05, S["title"], color="#e6e6e6", fontsize=14, family="monospace")
    fig.text(0.04, 0.03, f"{STEP:.0f} ft per slab · {A.res:.0f} m grid · elevation {S['dem_src']} · features OpenStreetMap", color="#8a8a8a", fontsize=8, family="monospace")
    fig.savefig(out, facecolor=fig.get_facecolor()); plt.close(fig)
