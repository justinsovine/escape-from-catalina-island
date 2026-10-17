"""Stacked laser-cut contour model. Each elevation band is a slab; buildings, streams, trails and the
route sit on the slab they belong to. The same polygons would drive a laser cutter.

Readability rules: the terrain is read by value (tops lighten with height), not by outlines; everything that
is not the route is one quiet tone; the route is the only saturated line, one color per day, with a glow on
dark palettes; few labels, large."""
import numpy as np
from rasterio import features
from scipy.ndimage import gaussian_filter
from shapely.geometry import shape, Point
from shapely.ops import unary_union
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from .. import FT
from ..area import iso
from ..osm import clip
from ..palette import get as get_palette, lerp


def slab_polygons(area, zf, land, levels, min_area=6000):
    """Per level: polygons (with holes) of ground at or above that height. These are the cut files."""
    out = []
    for k, lv in enumerate(levels):
        mask = (land & (zf >= lv)) if k else land
        polys = []
        for geom, v in features.shapes(mask.astype("uint8"), mask=mask, transform=area.transform):
            if v == 1:
                g = shape(geom).simplify(area.res * 1.4)
                if g.area >= min_area: polys.append(g)
        out.append(polys)
    return out


def render(S, out, size=(12, 15), dpi=160):
    A, Z, osm = S["area"], S["Z"], S["osm"]
    P = S.get("palette") or get_palette("mono")
    land = S["land"] if S.get("land") is not None else np.isfinite(Z * FT) & (Z * FT > S["sea_ft"])
    zf = gaussian_filter(np.nan_to_num(Z, nan=0.0), 1.0) * FT          # a touch of smoothing: cleaner cut lines
    zf = np.where(land, zf, np.nan)
    STEP, T = S["step_ft"], S["slab_m"]
    levels = np.arange(0, np.nanmax(zf), STEP)
    plate = A.plate
    osm = clip(osm, plate)
    route = S["route"].intersection(plate) if S["route"] is not None else None
    legs = [(l.intersection(plate), i) for l, i in S.get("legs", [])]

    def patch(g, lift=0.0, **kw):
        verts, codes = [], []
        for ring in [g.exterior] + list(g.interiors):
            xs, ys = iso(*np.array(ring.coords).T); pts = np.c_[xs, ys + lift]
            verts += pts.tolist(); codes += [Path.MOVETO] + [Path.LINETO] * (len(pts) - 2) + [Path.CLOSEPOLY]
        return PathPatch(Path(verts, codes), **kw)

    fig = plt.figure(figsize=size, dpi=dpi, facecolor=P["bg"]); ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(P["bg"]); ax.axis("off")
    for lift in (-2 * T, -T):
        ax.add_patch(patch(plate, lift=lift, facecolor=P["plate_side"], edgecolor=P["plate_edge"], lw=0.5, zorder=0))
    ax.add_patch(patch(plate, facecolor=P["plate"], edgecolor=P["plate_edge"], lw=0.6, zorder=1))
    n = max(1, len(levels) - 1)
    for k, polys in enumerate(slab_polygons(A, zf, land, levels)):
        lift = (k + 1) * T; top = lerp(P["slab_lo"], P["slab_hi"], k / n)   # tops lighten with height: the stack reads by value
        side = tuple(c * 0.6 for c in top)
        for g in polys:
            ax.add_patch(patch(g, lift=lift - T, facecolor=side, edgecolor=P["side_edge"], lw=0.35, zorder=10 + 3 * k))
            ax.add_patch(patch(g, lift=lift, facecolor=top, edgecolor=P["slab_edge"], lw=0.45, zorder=11 + 3 * k))

    def lift_at(x, y):
        z = A.sample(zf, x, y); k = np.clip(np.floor(z / STEP), 0, len(levels) - 1); return (k + 1) * T

    def draw_line(geom, **kw):
        for part in (geom.geoms if hasattr(geom, "geoms") else [geom]):
            if part.geom_type != "LineString": continue
            xy = np.array(part.coords); x, y = xy[:, 0], xy[:, 1]; sx, sy = iso(x, y); ax.plot(sx, sy + lift_at(x, y), **kw)
    for ls in osm["streams"]: draw_line(ls, color=P["stream"], lw=0.5, alpha=.7, zorder=200)
    for ls in osm["roads"]: draw_line(ls, color=P["road"], lw=0.55, alpha=.8, zorder=201)
    for ls in osm["service"]: draw_line(ls, color=P["road"], lw=0.4, alpha=.4, zorder=201)
    for ls in osm["trails"]: draw_line(ls, color=P["trail"], lw=0.4, alpha=.45, ls=(0, (2, 2)), zorder=201)
    for ls in osm["piers"]: draw_line(ls, color=P["pier"], lw=2.0, solid_capstyle="round", zorder=205)

    def draw_route(geom, color, muted=False):
        if muted:                        # trail that exists but is not on the plan
            draw_line(geom, color=P["casing"], lw=2.6, solid_capstyle="round", zorder=202)
            draw_line(geom, color=color, lw=1.1, alpha=.55, ls=(0, (3, 2)), solid_capstyle="round", zorder=203)
            return
        if P["glow"]:                    # a soft halo in the route's own hue, outside the casing
            draw_line(geom, color=color, lw=9, alpha=.14, solid_capstyle="round", zorder=201.5)
            draw_line(geom, color=color, lw=5, alpha=.28, solid_capstyle="round", zorder=201.6)
        draw_line(geom, color=P["casing"], lw=3.8, solid_capstyle="round", zorder=202)
        draw_line(geom, color=color, lw=1.9, ls=(0, (3, 2)) if P["dashed"] else "-", solid_capstyle="round", zorder=203)
    days = S.get("leg_days") or []
    for piece, i in legs:
        if i is not None and i < len(days): draw_route(piece, P["days"].get(days[i], P["route"]))
        else: draw_route(piece, P["route"], muted=bool(days))
    for x, y, name in S["ports"]:        # a boat at each port, where the reference image had an airplane
        sx, sy = iso(x - 260, y + 120)
        ax.plot([sx - 26, sx + 26], [sy + 2, sy + 2], color=P["pier"], lw=3.5, solid_capstyle="round", zorder=206)
        ax.plot([sx - 8, sx + 10], [sy + 8, sy + 8], color=P["pier"], lw=3, solid_capstyle="round", zorder=206)
    boxes = [(b.centroid.x, b.centroid.y, max(8, min(40, np.sqrt(b.area)))) for b in osm["buildings"]]
    if len(boxes) > 150:                 # scattered rural houses would read as stars: keep clusters only
        cells = {}
        for x, y, w in boxes: cells.setdefault((int(x // 200), int(y // 200)), []).append((x, y))
        boxes = [(np.mean([p[0] for p in v]), np.mean([p[1] for p in v]), min(40, 14 + 4 * len(v))) for v in cells.values() if len(v) >= 3]
    b_top, b_l, b_r = P["building"]
    for x, y, w in boxes:                # tiny boxes, three faces
        h = lift_at(x, y); bh = 9
        sq = [(x - w / 2, y - w / 2), (x + w / 2, y - w / 2), (x + w / 2, y + w / 2), (x - w / 2, y + w / 2)]
        sx, sy = iso(*np.array(sq).T)
        ax.fill(sx, sy + h + bh, color=b_top, lw=0.3, ec=P["bg"], zorder=300)
        ax.fill([sx[0], sx[1], sx[1], sx[0]], [sy[0] + h, sy[1] + h, sy[1] + h + bh, sy[0] + h + bh], color=b_l, lw=0.3, ec=P["bg"], zorder=299)
        ax.fill([sx[1], sx[2], sx[2], sx[1]], [sy[1] + h, sy[2] + h, sy[2] + h + bh, sy[1] + h + bh], color=b_r, lw=0.3, ec=P["bg"], zorder=299)
    rng = np.random.default_rng(3); tree_pts = []
    if osm["wood"]:                      # real forest polygons when OSM has them
        u = unary_union(osm["wood"]); minx, miny, maxx, maxy = u.bounds
        cand = np.c_[rng.uniform(minx, maxx, 6000), rng.uniform(miny, maxy, 6000)]
        tree_pts = [tuple(p) for p in cand if u.contains(Point(p))][:500]
    else:                                # stand-in: along streams below the tree line
        p_tree = .08 if S["sea_ft"] < 0 else .3
        for ls in osm["streams"]:
            for d in np.arange(0, ls.length, 110):
                p = ls.interpolate(d)
                if A.sample(zf, p.x, p.y) < S["tree_ft"] and rng.random() < p_tree: tree_pts.append((p.x + rng.normal(0, 25), p.y + rng.normal(0, 25)))
    t_trunk, t_crown = P["tree"]
    for x, y in tree_pts:
        h = lift_at(x, y); sx, sy = iso(x, y); sy += h
        ax.plot([sx, sx], [sy, sy + 16], color=t_trunk, lw=0.6, zorder=310)
        ax.plot([sx - 8, sx, sx + 8, sx - 8], [sy + 7, sy + 26, sy + 7, sy + 7], color=t_crown, lw=0.6, zorder=310)
    peaks = sorted([(A.sample(zf, x, y), x, y, n) for x, y, n in osm["peaks"] if n], reverse=True)[:5]
    for z, x, y, name in peaks:          # the five highest named summits only
        sx, sy = iso(x, y); ax.plot(sx, sy + lift_at(x, y) + 6, marker="^", ms=5, color=P["peak"], zorder=320)
        ax.text(sx + 34, sy + lift_at(x, y) + 24, name, color=P["label"], alpha=.85, fontsize=8, family="monospace", zorder=320)
    for x, y, name in osm["camps"]:
        sx, sy = iso(x, y); ax.plot(sx, sy + lift_at(x, y) + 6, marker="^", ms=6, mfc=P["bg"], mec=P["peak"], mew=.9, zorder=320)
    labels = S["labels"] or [(x, y, n.upper()) for x, y, n in osm["places"][:5]]
    for x, y, name in labels:
        sx, sy = iso(x, y); ax.text(sx, sy + lift_at(x, y) + 70, name, color=P["label"], fontsize=11.5, family="monospace", ha="center", zorder=330,
                                   bbox=dict(boxstyle="square,pad=0.25", fc=P["label_bg"], ec="none", alpha=.78))
    x0, y0, x1, y1 = plate.bounds
    sx, sy = iso(np.array([x0, x1, x1, x0]), np.array([y0, y0, y1, y1]))
    ax.set_xlim(sx.min() - 300, sx.max() + 300); ax.set_ylim(sy.min() - 3 * T - 300, sy.max() + len(levels) * T + 600); ax.set_aspect("equal")
    fig.text(0.04, 0.05, S["title"], color=P["title"], fontsize=14, family="monospace")
    fig.text(0.04, 0.03, f"{STEP:.0f} ft per slab · {A.res:.0f} m grid · elevation {S['dem_src']} · features OpenStreetMap", color=P["muted"], fontsize=8, family="monospace")
    fig.savefig(out, facecolor=fig.get_facecolor()); plt.close(fig)
