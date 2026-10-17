"""Contour-wireframe terrain on a compass disc, the route draped over it, pins at the stops, in a dark card."""
import numpy as np
from skimage import measure
from shapely.geometry import LineString, Point
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle


def render(S, out, size=(9, 9), dpi=170, exag=1.6, az=-35, el=32, interval_m=20):
    A, Z, osm = S["area"], S["Z"], S["osm"]
    route = S["route"]
    if route is None: raise SystemExit("the wire card needs a route (give the scene a trail)")
    if hasattr(route, "geoms"): route = max(route.geoms, key=lambda g: g.length)
    cx, cy = route.centroid.x, route.centroid.y
    R = max(route.bounds[2] - route.bounds[0], route.bounds[3] - route.bounds[1]) * 0.56
    disc = Point(cx, cy).buffer(R, 96)
    AZ, EL = np.radians(az), np.radians(el)

    def proj(x, y, z):
        x = np.asarray(x, float) - cx; y = np.asarray(y, float) - cy; z = np.asarray(z, float) * exag
        xr = x * np.cos(AZ) - y * np.sin(AZ); yr = x * np.sin(AZ) + y * np.cos(AZ)
        return xr, yr * np.sin(EL) + z * np.cos(EL), yr

    Zm = np.nan_to_num(np.where(S["land"], Z, 0.0) if S.get("land") is not None else Z, nan=0.0)
    z0 = max(0.0, float(np.nanmin(A.sample(Z, *np.array(disc.exterior.coords).T))))
    fig = plt.figure(figsize=size, dpi=dpi, facecolor="#1e2124"); ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor("#1e2124"); ax.axis("off")
    ax.add_patch(FancyBboxPatch((-R * 1.25, -R * 1.05), R * 2.5, R * 2.45, boxstyle=f"round,pad=0,rounding_size={R * 0.12}", fc="#141618", ec="none", zorder=0))
    th = np.linspace(0, 2 * np.pi, 361); ex, ey, _ = proj(cx + R * np.cos(th), cy + R * np.sin(th), z0)
    ax.fill(ex, ey, color="#17191c", zorder=1); ax.plot(ex, ey, color="#7fa6b4", lw=1.2, zorder=2)
    for k in range(0, 360, 5):
        a = np.radians(k); r0 = R * (1.04 if k % 45 else 1.0); r1 = R * (1.08 if k % 45 else 1.14)
        x, y, _ = proj([cx + r0 * np.cos(a), cx + r1 * np.cos(a)], [cy + r0 * np.sin(a), cy + r1 * np.sin(a)], z0)
        ax.plot(x, y, color="#5f6b70", lw=0.7 if k % 45 else 1.2, zorder=2)
    for name, ang in (("N", 90), ("E", 0), ("S", 270), ("W", 180)):
        a = np.radians(ang); x, y, _ = proj(cx + R * 1.24 * np.cos(a), cy + R * 1.24 * np.sin(a), z0)
        ax.text(x, y, name, color="#cfd6d9", fontsize=10, ha="center", va="center", family="monospace", zorder=3)
    levels = np.arange(np.floor(z0 / interval_m) * interval_m, np.nanmax(Zm) + 1, interval_m)
    segs = []
    for lv in levels:
        for c in measure.find_contours(Zm, lv):
            if len(c) < 6: continue
            xs = A.E0 + (c[:, 1] + 0.5) * A.res; ys = A.N0 + (A.H - c[:, 0] - 0.5) * A.res
            g = LineString(np.c_[xs, ys]).intersection(disc)
            for part in (g.geoms if hasattr(g, "geoms") else [g]):
                if part.geom_type != "LineString" or part.length < 60: continue
                xy = np.array(part.coords); x, y, d = proj(xy[:, 0], xy[:, 1], lv); segs.append((d.mean(), x, y, lv))
    segs.sort(key=lambda s: -s[0])                       # far to near
    zmax = levels[-1]
    for d, x, y, lv in segs:
        t = (lv - z0) / max(1, zmax - z0)
        ax.plot(x, y, color=(0.55 + 0.4 * t, 0.6 + 0.35 * t, 0.65 + 0.3 * t), lw=0.45 + 0.3 * t, alpha=0.75, zorder=5)
    rp = np.array([route.interpolate(d).coords[0] for d in np.arange(0, route.length, 25)])
    rz = A.sample(Z, rp[:, 0], rp[:, 1]); x, y, _ = proj(rp[:, 0], rp[:, 1], rz)
    ax.plot(x, y, color="#f4f4f4", lw=1.6, ls=(0, (2.2, 2.0)), zorder=8)

    def pin(px, py, glyph, col, label=None, dy=R * 0.28):
        z = A.sample(Z, px, py); x, y, _ = proj(px, py, z)
        ax.plot([x, x], [y, y + dy], color="#cfd6d9", lw=1.0, zorder=9); ax.plot(x, y, "o", ms=3, color="#cfd6d9", zorder=9)
        ax.add_patch(Circle((x, y + dy), R * 0.06, fc=col, ec="none", zorder=10))
        ax.text(x, y + dy, glyph, ha="center", va="center", fontsize=9, color="#fff" if col == "#e05a3a" else "#111", family="DejaVu Sans", zorder=11)
        if label: ax.text(x, y + dy + R * 0.1, label, ha="center", va="bottom", fontsize=7.5, color="#cfd6d9", family="monospace", zorder=11)
    pins = S["pins"] or [(*route.coords[0], "S", "#eef1f2", "start"), (*route.coords[-1], "F", "#eef1f2", "finish")] + \
        [(x, y, "▲", "#e05a3a", n or "camp") for x, y, n in osm["camps"] if disc.contains(Point(x, y))][:3]
    for p in pins: pin(*p)
    peaks = [(A.sample(Z, x, y), x, y, n) for x, y, n in osm["peaks"] if n and disc.contains(Point(x, y))]
    for z, x, y, name in sorted(peaks, reverse=True)[:5]:          # the five highest named summits in the disc
        pin(x, y, "▲", "#8fd3e8", name, dy=R * 0.36)
    ax.text(-R * 1.1, R * 1.26, S["card_title"], color="#eef1f2", fontsize=12, family="monospace", va="center")
    ax.text(-R * 1.1, R * 1.14, S["card_sub"], color="#8b9499", fontsize=8, family="monospace", va="center")
    ax.set_xlim(-R * 1.3, R * 1.3); ax.set_ylim(-R * 1.1, R * 1.45); ax.set_aspect("equal")
    fig.savefig(out, facecolor=fig.get_facecolor()); plt.close(fig)
