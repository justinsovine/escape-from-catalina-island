"""Contour terrain on a compass disc, the route draped over it, pins at the stops, in a dark card.

Readability rules: the mountain is a solid body (each band is filled before its contour is drawn, far to
near, so lines behind a ridge are hidden); contours are sparse with a heavier index line every fourth;
the route has a dark casing; only the highest named summits get pins."""
import numpy as np
from rasterio import features
from scipy.ndimage import gaussian_filter
from shapely.geometry import shape, Point, LineString
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, PathPatch
from matplotlib.path import Path

CARD, BODY, RIM, INK, MUTED = "#141618", "#17191c", "#7fa6b4", "#eef1f2", "#8b9499"


def nice_interval(relief_m, target=12):
    """A contour interval from a short list of round numbers, giving about `target` bands."""
    raw = relief_m / target
    return min((10, 20, 25, 50, 100, 200, 500), key=lambda v: abs(v - raw))


def render(S, out, size=(9, 9), dpi=170, exag=1.6, az=-35, el=32, interval_m=None, index_every=4):
    A, Z, osm = S["area"], S["Z"], S["osm"]
    route = S["route"]
    if route is None: raise SystemExit("the wire card needs a route (give the scene a trail)")
    if hasattr(route, "geoms"): route = max(route.geoms, key=lambda g: g.length)
    if S.get("focus"):                                 # one leg of the trail: a disc around a point
        cx, cy, R = S["focus"]
        disc = Point(cx, cy).buffer(R, 96)
        seg = route.intersection(disc)
        if not seg.is_empty:
            route = max(seg.geoms, key=lambda g: g.length) if hasattr(seg, "geoms") else seg
    else:
        cx, cy = route.centroid.x, route.centroid.y
        R = max(route.bounds[2] - route.bounds[0], route.bounds[3] - route.bounds[1]) * 0.62
        disc = Point(cx, cy).buffer(R, 96)
    AZ, EL = np.radians(az), np.radians(el)

    def proj(x, y, z):
        x = np.asarray(x, float) - cx; y = np.asarray(y, float) - cy; z = np.asarray(z, float) * exag
        xr = x * np.cos(AZ) - y * np.sin(AZ); yr = x * np.sin(AZ) + y * np.cos(AZ)
        return xr, yr * np.sin(EL) + z * np.cos(EL)

    land = S["land"] if S.get("land") is not None else np.ones(Z.shape, bool)
    Zs = gaussian_filter(np.nan_to_num(np.where(land, Z, 0.0), nan=0.0), 2.0)      # smooth before contouring
    Zs = np.where(land, np.maximum(Zs, 0.0), 0.0)
    rr_, cc_ = np.mgrid[0:A.H, 0:A.W]; inside = ((A.E0 + (cc_ + .5) * A.res - cx) ** 2 + (A.N0 + (A.H - rr_ - .5) * A.res - cy) ** 2) <= R * R
    z0 = max(0.0, float(Zs[inside & land].min())) if (inside & land).any() else 0.0
    ztop = float(Zs[inside].max()) if inside.any() else float(Zs.max())
    interval_m = interval_m or nice_interval(ztop - z0)
    levels = np.arange(np.floor(z0 / interval_m) * interval_m, ztop + 1, interval_m)
    fig = plt.figure(figsize=size, dpi=dpi, facecolor="#1e2124"); ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor("#1e2124"); ax.axis("off")
    ax.add_patch(FancyBboxPatch((-R * 1.25, -R * 1.05), R * 2.5, R * 2.45, boxstyle=f"round,pad=0,rounding_size={R * 0.12}", fc=CARD, ec="none", zorder=0))
    th = np.linspace(0, 2 * np.pi, 361); ex, ey = proj(cx + R * np.cos(th), cy + R * np.sin(th), z0)
    ax.fill(ex, ey, color=BODY, zorder=1); ax.plot(ex, ey, color=RIM, lw=1.2, zorder=2)
    for k in range(0, 360, 5):
        a = np.radians(k); r0 = R * (1.04 if k % 45 else 1.0); r1 = R * (1.08 if k % 45 else 1.14)
        x, y = proj([cx + r0 * np.cos(a), cx + r1 * np.cos(a)], [cy + r0 * np.sin(a), cy + r1 * np.sin(a)], z0)
        ax.plot(x, y, color="#5f6b70", lw=0.7 if k % 45 else 1.2, zorder=2)
    for name, ang in (("N", 90), ("E", 0), ("S", 270), ("W", 180)):
        a = np.radians(ang); x, y = proj(cx + R * 1.24 * np.cos(a), cy + R * 1.24 * np.sin(a), z0)
        ax.text(x, y, name, color="#cfd6d9", fontsize=10, ha="center", va="center", family="monospace", zorder=3)

    def band_patch(g, lv, **kw):
        verts, codes = [], []
        for ring in [g.exterior] + list(g.interiors):
            x, y = proj(*np.array(ring.coords).T, lv); pts = np.c_[x, y]
            verts += pts.tolist(); codes += [Path.MOVETO] + [Path.LINETO] * (len(pts) - 2) + [Path.CLOSEPOLY]
        return PathPatch(Path(verts, codes), **kw)
    zmax = levels[-1]
    for k, lv in enumerate(levels):                  # bands from the bottom up: each fill hides what is behind it
        mask = Zs >= lv if k else land
        t = (lv - z0) / max(1, zmax - z0); idx = (k % index_every == 0)
        col = (0.5 + 0.45 * t, 0.56 + 0.4 * t, 0.62 + 0.35 * t, 0.95 if idx else 0.3)
        for geom, v in features.shapes(mask.astype("uint8"), mask=mask, transform=A.transform):
            if v != 1: continue
            g = shape(geom).simplify(A.res * 0.8).intersection(disc)
            for part in (g.geoms if hasattr(g, "geoms") else [g]):
                if part.geom_type != "Polygon" or part.area < 400: continue
                ax.add_patch(band_patch(part, lv, fc=BODY, ec=col, lw=0.95 if idx else 0.35, zorder=5 + k * 1e-3))   # all bands stay below the route and pins
    rp = np.array([route.interpolate(d).coords[0] for d in np.arange(0, route.length, 25)])
    rz = A.sample(Zs, rp[:, 0], rp[:, 1]); x, y = proj(rp[:, 0], rp[:, 1], rz)
    ax.plot(x, y, color=CARD, lw=3.4, solid_capstyle="round", zorder=8)
    ax.plot(x, y, color="#f4f4f4", lw=1.6, ls=(0, (2.2, 2.0)), zorder=8.5)

    placed = []
    def pin(px, py, glyph, col, label=None, dy=R * 0.28):
        z = A.sample(Zs, px, py); x, y = proj(px, py, z)
        while any(abs(x - qx) < R * 0.16 and abs((y + dy) - qy) < R * 0.14 for qx, qy in placed): dy += R * 0.16   # stagger heads that would collide
        placed.append((x, y + dy))
        ax.plot([x, x], [y, y + dy], color="#cfd6d9", lw=1.0, zorder=9); ax.plot(x, y, "o", ms=3, color="#cfd6d9", zorder=9)
        ax.add_patch(Circle((x, y + dy), R * 0.06, fc=col, ec="none", zorder=10))
        ax.text(x, y + dy, glyph, ha="center", va="center", fontsize=9, color="#fff" if col == "#e05a3a" else "#111", family="DejaVu Sans", zorder=11)
        if label: ax.text(x, y + dy + R * 0.1, label, ha="center", va="bottom", fontsize=8, color="#cfd6d9", family="monospace", zorder=11)
    camps = [(x, y, n) for x, y, n in osm["camps"] if disc.contains(Point(x, y))]
    named = [c for c in camps if c[2]][:2] or camps[:1]                 # named camps, else one unnamed
    pins = S["pins"] or [(*route.coords[0], "S", INK, "start"), (*route.coords[-1], "F", INK, "finish")] + \
        [(x, y, "▲", "#e05a3a", n or "camp") for x, y, n in named]
    for p in pins: pin(*p)
    peaks = [(A.sample(Zs, x, y), x, y, n) for x, y, n in osm["peaks"] if n and disc.contains(Point(x, y))]
    for z, x, y, name in sorted(peaks, reverse=True)[:3]:          # the three highest named summits in the disc
        pin(x, y, "▲", "#8fd3e8", name, dy=R * 0.36)
    ax.text(-R * 1.1, R * 1.26, S["card_title"], color=INK, fontsize=12, family="monospace", va="center")
    ax.text(-R * 1.1, R * 1.14, S["card_sub"], color=MUTED, fontsize=8, family="monospace", va="center")
    ax.set_xlim(-R * 1.3, R * 1.3); ax.set_ylim(-R * 1.1, R * 1.45); ax.set_aspect("equal")
    fig.savefig(out, facecolor=fig.get_facecolor()); plt.close(fig)
