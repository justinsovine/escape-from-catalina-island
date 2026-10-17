"""Boats, mooring buoys and vehicles on the 2023 county aerial mosaics (Web Mercator, ~0.25 m at z19).
Water comes from the OSM coastline mask; piers and buildings are masked; detections are sized by long axis."""
import os, sys, json, math
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.environ.setdefault("MAPGAME_DATA", os.path.join(ROOT, "data"))
import numpy as np
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS = None
from scipy import ndimage
from skimage.measure import label, regionprops
from rasterio import features
from rasterio.transform import from_bounds
from shapely import transform as sh_t
from pyproj import Transformer
from mapgame import osm as O
from mapgame.area import Area
from scenario.common import osm_elements
SP = os.path.join(ROOT, "data", "lariac")  # mosaics from tiles.py and the detections live here (gitignored)
els = osm_elements()
def run(name):
    meta = json.load(open(f"{SP}/{name}_z{meta_z(name)}.json")); x0, y0, x1, y1 = meta["mercator_bounds"]; W, H = meta["size"]; res = meta["res_m"]
    im = np.asarray(Image.open(f"{SP}/{name}_z{meta['z']}.png").convert("RGB")).astype("float32")
    # land mask: build OSM layers in UTM on a matching bbox, then rasterize the land polygons into the mercator grid
    to_ll = Transformer.from_crs(3857, 4326, always_xy=True); lon0, lat0 = to_ll.transform(x0, y0); lon1, lat1 = to_ll.transform(x1, y1)
    A = Area(lon0, lat0, lon1, lat1, res=2.0); L = O.layers(A, els)
    from mapgame.osm import land_mask
    landA = land_mask(A, L)
    # polygons of land in UTM -> mercator
    from rasterio.features import shapes
    from shapely.geometry import shape
    to_merc = Transformer.from_crs(A.epsg, 3857, always_xy=True)
    polys = [sh_t(shape(g), lambda c: np.c_[to_merc.transform(c[:, 0], c[:, 1])]) for g, v in shapes(landA.astype("uint8"), mask=landA, transform=A.transform) if v == 1]
    tr = from_bounds(x0, y0, x1, y1, W, H)
    land = features.rasterize(((p, 1) for p in polys), out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool) if polys else np.zeros((H, W), bool)
    masks = [sh_t(g.buffer(6), lambda c: np.c_[to_merc.transform(c[:, 0], c[:, 1])]) for g in L["piers"]] + [sh_t(b.buffer(3), lambda c: np.c_[to_merc.transform(c[:, 0], c[:, 1])]) for b in L["buildings"]]
    pm = features.rasterize(((p, 1) for p in masks), out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool) if masks else np.zeros((H, W), bool)
    shore = ndimage.distance_transform_edt((~land) & (im.sum(2) > 0)) * res      # distance of each sea pixel to land or to the mosaic edge
    sea = (~land) & (im.sum(2) > 0) & (shore > 12) & ~pm
    R, G, B = im[..., 0], im[..., 1], im[..., 2]; bright = (R + G + B) / 3
    wb = np.median(bright[sea]) if sea.any() else 100
    filled = np.where(sea, bright, wb); loc = ndimage.uniform_filter(filled, size=int(40 / res) | 1); rough = ndimage.uniform_filter(np.abs(filled - loc), size=int(40 / res) | 1)
    cand = sea & (bright > loc + np.maximum(40, 4.0 * rough)) & (bright > 110)
    cand = ndimage.binary_opening(cand, structure=np.ones((2, 2)))
    lab = label(cand, connectivity=2); boats, buoys = [], []
    def ll(r, c):
        mx = x0 + (c + 0.5) / W * (x1 - x0); my = y1 - (r + 0.5) / H * (y1 - y0); lon, lat = to_ll.transform(mx, my); return round(lon, 6), round(lat, 6)
    for rp in regionprops(lab):
        length, width, area = rp.axis_major_length * res, rp.axis_minor_length * res, rp.area * res * res
        r, c = rp.centroid
        if 0.5 <= length <= 2.2 and area <= 3.0: buoys.append((ll(r, c), rp.bbox)); continue
        if area < 6 or length < 4 or length > 130 or rp.solidity < 0.5 or (width > 0 and length / width > 7) or (length < 8 and width > 0 and length / width < 1.4): continue
        boats.append((ll(r, c), round(length, 1), round(width, 1), rp.bbox))
    sizes = np.array([b[1] for b in boats]) if boats else np.array([])
    line = f"| {name} (2023 county aerial, {res:.2f} m) | {len(boats)} boats | under 6 m {int((sizes < 6).sum())} | 6 to 12 m {int(((sizes >= 6) & (sizes < 12)).sum())} | 12 to 20 m {int(((sizes >= 12) & (sizes < 20)).sum())} | 20 to 35 m {int(((sizes >= 20) & (sizes < 35)).sum())} | over 35 m {int((sizes >= 35).sum())} | buoy-sized dots {len(buoys)} |"
    print(line, flush=True)
    out = Image.fromarray(im.astype("uint8")); d = ImageDraw.Draw(out)
    for _, _, _, (r0, c0, r1, c1) in boats: d.rectangle([c0 - 3, r0 - 3, c1 + 3, r1 + 3], outline=(255, 60, 60), width=3)
    for _, (r0, c0, r1, c1) in buoys: d.ellipse([c0 - 6, r0 - 6, c1 + 6, r1 + 6], outline=(255, 255, 0), width=2)
    out.save(f"{SP}/check_{name}.png")
    json.dump({"boats": [{"lon": b[0][0], "lat": b[0][1], "length_m": b[1], "width_m": b[2]} for b in boats], "buoys": [{"lon": b[0][0], "lat": b[0][1]} for b in buoys], "line": line}, open(f"{SP}/detect_{name}.json", "w"))
def meta_z(name):
    for f in os.listdir(SP):
        if f.startswith(name + "_z") and f.endswith(".json"): return int(f.split("_z")[1].split(".")[0])
    raise SystemExit("no mosaic " + name)
for name in sys.argv[1:]: run(name)
feats = []
for f in sorted(os.listdir(SP)):
    if f.startswith("detect_") and f.endswith(".json"):
        j = json.load(open(os.path.join(SP, f))); cove = f[7:-5]
        feats += [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [b["lon"], b["lat"]]}, "properties": {"kind": "boat", "cove": cove, "length_m": b["length_m"], "width_m": b["width_m"]}} for b in j["boats"]]
        feats += [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [b["lon"], b["lat"]]}, "properties": {"kind": "buoy", "cove": cove}} for b in j["buoys"]]
out = os.path.join(ROOT, "atlas", "out", "boats_2023.geojson"); json.dump({"type": "FeatureCollection", "features": feats}, open(out, "w")); print(out, len(feats), "features")
