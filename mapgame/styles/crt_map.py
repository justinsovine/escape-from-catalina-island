"""Pixel map on a CRT. One elevation cell per pixel at low resolution, glyph cells for hatching and trees,
dotted roads, pixel-font labels; then scanlines, barrel distortion, bloom and a frame.

Drawn as separate ink layers (map, water, route) so a palette can print the route in a second ink, or run
the whole thing as a green phosphor terminal. The mono palette collapses the layers to the 1-bit original.

Readability rules: hatch only the real ranges (top third of the local relief, on slopes, thinned to a
checkerboard), so blank paper does the work; roads sparse, the route solid; labels never overlap; a coarse
sea checker that survives the screen curve without shimmering."""
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_erosion, map_coordinates, gaussian_filter, distance_transform_edt
from .. import FT
from ..fonts import press_start
from ..palette import get as get_palette

CARET = ["..#..", ".#.#.", "#...#"]
CARET_BIG = ["...#...", "..#.#..", ".#...#.", "#.....#"]
TREE = ["..#..", ".###.", "..#..", ".###.", "#####", "..#.."]


def render(S, out, cell=8, scale=3):
    A, Z, osm = S["area"], S["Z"], S["osm"]
    P = S.get("palette") or get_palette("mono")
    zf = Z * FT; H, W = zf.shape
    land = S["land"] if S.get("land") is not None else np.isfinite(zf) & (zf > S["sea_ft"])
    zf = np.where(land, zf, np.nan)
    rng = np.random.default_rng(7)
    base = np.zeros((H, W), bool); water = np.zeros((H, W), bool); route = np.full((H, W), -1, np.int8)
    rr, cc = np.mgrid[0:H, 0:W]
    water[~land & (((rr // 2) + (cc // 2)) % 2 == 0)] = True            # sea: 2x2 checker, coarse enough not to moiré after the warp
    base[land & ~binary_erosion(land, iterations=1)] = True             # coastline

    def stamp(glyph, x, y):
        for j, row in enumerate(glyph):
            for i, ch in enumerate(row):
                if ch == "#" and 0 <= x + i < W and 0 <= y + j < H: base[y + j, x + i] = True
    stream_mask = np.zeros((H, W), bool)
    for ls in osm["streams"]:
        for d in np.arange(0, ls.length, A.res):
            p = ls.interpolate(d); r, c = A.rc(p.x, p.y); r, c = int(round(r)), int(round(c))
            if 0 <= r < H and 0 <= c < W: stream_mask[r, c] = True
    if P["crt_streams"]:
        water |= stream_mask & land & (((rr + cc) % 3) == 0)                # streams as a sparse dotted second ink
    near_stream = distance_transform_edt(~stream_mask) * A.res < 150
    p65, p82, p92 = np.nanpercentile(zf[land], [65, 82, 92]) if land.any() else (0, 0, 0)
    gy, gx = np.gradient(np.nan_to_num(zf, nan=0)); slope = np.hypot(gx, gy) / (A.res * FT)
    p_tree = 0.25 if S["sea_ft"] < 0 else 0.5
    wm = None; wood_frac = 0.0
    if osm["wood"]:                                      # forest everywhere: thin the glyphs so blank paper survives
        from rasterio import features as _f
        wm = _f.rasterize(((w, 1) for w in osm["wood"]), out_shape=(H, W), transform=A.transform, fill=0, dtype="uint8").astype(bool)
        wood_frac = float(wm[land].mean()) if land.any() else 0.0
    p_wood = 0.6 if wood_frac < 0.5 else 0.3
    for cy in range(0, H - cell, cell):
        for cx in range(0, W - cell, cell):
            lb = land[cy:cy + cell, cx:cx + cell]
            if lb.mean() < 0.9: continue
            z = np.nanmean(zf[cy:cy + cell, cx:cx + cell]); sl = np.nanmean(slope[cy:cy + cell, cx:cx + cell])
            checker = ((cx // cell) + (cy // cell)) % 2 == 0
            if z >= p92 and sl > 0.1:
                stamp(CARET_BIG, cx + rng.integers(0, 2), cy + rng.integers(0, 4))
            elif z >= p82 and sl > 0.1:
                stamp(CARET, cx + rng.integers(0, 3), cy + rng.integers(0, 4))
            elif z >= p65 and sl > 0.12 and checker:
                stamp(CARET, cx + rng.integers(0, 3), cy + rng.integers(0, 4))
            elif wm is not None:
                if checker and rng.random() < p_wood and wm[cy + 4, cx + 4]: stamp(TREE, cx + rng.integers(0, 3), cy + rng.integers(0, 3))
            elif near_stream[cy:cy + cell, cx:cx + cell].mean() > 0.25 and z < S["tree_ft"] and rng.random() < p_tree:
                stamp(TREE, cx + rng.integers(0, 3), cy + rng.integers(0, 3))

    def line_px(geom, layer, value=True, every=2, width=1):
        for part in (geom.geoms if hasattr(geom, "geoms") else [geom]):
            if part.geom_type != "LineString": continue
            for k, d in enumerate(np.arange(0, part.length, A.res * 0.7)):
                if k % every: continue
                p = part.interpolate(d); r, c = A.rc(p.x, p.y); r, c = int(round(r)), int(round(c))
                for dr in range(width):
                    for dc in range(width):
                        if 0 <= r + dr < H and 0 <= c + dc < W: layer[r + dr, c + dc] = value
    for ls in osm["roads"]: line_px(ls, base, every=3)
    days = S.get("leg_days") or []; REST = 100
    for piece, i in (S.get("legs") or []):
        if i is not None and i < len(days): line_px(piece, route, value=i, every=1, width=2)
        elif days: line_px(piece, route, value=REST, every=2, width=1)          # trail not on the plan: thin, dotted
        else: line_px(piece, route, value=0, every=1, width=2)

    # composite the inks onto paper, route on top
    img = np.empty((H, W, 3), np.uint8); img[:] = P["paper"]
    img[water] = P["water"]; img[base] = P["cink"]
    for i in sorted(set(np.unique(route)) - {-1}):
        col = P["cdays"].get(days[i], P["croute"]) if i < len(days) else P["croute"]
        img[route == i] = col
    pil = Image.fromarray(img); font = press_start(8); draw = ImageDraw.Draw(pil); placed = []
    ink, paper = tuple(P["cink"]), tuple(P["paper"])
    def label(x, y, text, sym=None):
        r, c = A.rc(x, y); c, r = int(c), int(r)
        w = draw.textlength(text, font=font); tx, ty = int(c - w / 2), r - 14
        tx = max(2, min(W - int(w) - 2, tx)); box = (tx - 2, ty - 2, tx + w + 2, ty + 10)
        if any(not (box[2] < b[0] or box[0] > b[2] or box[3] < b[1] or box[1] > b[3]) for b in placed): return
        placed.append(box)
        if sym == "star": draw.polygon([(c, r - 4), (c + 1, r - 1), (c + 4, r - 1), (c + 2, r + 1), (c + 3, r + 4), (c, r + 2), (c - 3, r + 4), (c - 2, r + 1), (c - 4, r - 1), (c - 1, r - 1)], fill=ink)
        if sym == "box": draw.rectangle([c - 5, r - 3, c + 5, r + 3], outline=ink, fill=paper); draw.rectangle([c - 3, r - 1, c + 3, r + 1], fill=ink)
        if sym == "peak": draw.polygon([(c, r - 4), (c + 4, r + 2), (c - 4, r + 2)], outline=ink, fill=paper)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1): draw.text((tx + dx, ty + dy), text, font=font, fill=paper)
        draw.text((tx, ty), text, font=font, fill=ink)
    for x, y, name in S["ports"]: label(x, y, name, "star")
    for x, y, name in S["camps"]: label(x, y, name, "box")
    crt_labels = S["crt_labels"] or [(x, y, n.upper(), None) for x, y, n in osm["places"][:5]] + [(x, y, n.upper(), "peak") for x, y, n in osm["peaks"][:3] if n]
    for x, y, name, sym in crt_labels: label(x, y, name, sym)

    # the screen: upscale, scanlines, barrel distortion, bloom, vignette, rounded edge, bezel
    g = np.asarray(pil.resize((W * scale, H * scale), Image.NEAREST), float) / 255.0 * 0.92 + 0.04
    g[1::3, :, :] *= 0.8
    h, w = g.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]
    nx, ny = (xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2); rr2 = nx ** 2 + ny ** 2
    sx, sy = nx * (1 + 0.07 * rr2), ny * (1 + 0.07 * rr2)
    coords = [sy * (h / 2) + h / 2, sx * (w / 2) + w / 2]
    warped = np.stack([map_coordinates(g[..., i], coords, order=1, cval=0.0) for i in range(3)], -1)
    warped = warped + 0.3 * np.stack([gaussian_filter(warped[..., i], 2.0) for i in range(3)], -1)
    warped = np.clip(warped / warped.max(), 0, 1) * (1 - 0.45 * np.clip((rr2 - 0.6) / 0.6, 0, 1) ** 1.5)[..., None]
    warped[(np.abs(nx) ** 4 + np.abs(ny) ** 4) >= 0.985] = 0.0
    frame = Image.new("RGB", (w + 120, h + 120), tuple(P["bezel"])); frame.paste(Image.fromarray((warped * 255).astype("uint8")), (60, 60))
    d = ImageDraw.Draw(frame)
    d.text((64, h + 90), f"{S['title']}   {S['dem_src'].upper()} / OSM", font=press_start(10), fill=tuple(P["caption"]))
    frame.save(out)
