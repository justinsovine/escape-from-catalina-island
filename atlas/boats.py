"""Boats on the moorings and at the docks, counted from USDA NAIP 0.6 m aerial imagery (public domain) served by
the Microsoft Planetary Computer. A boat is a compact bright hull on the water; kelp (bright only in infrared),
surf and glint are rejected by shape and by colour. Writes atlas/out/boats.geojson, boats.md and a check image
per cove under atlas/out/boats_check_*.png.  Run: python atlas/boats.py [--year 2022] [--cove NAME]"""
import os, sys, json, argparse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
import numpy as np, rasterio
from rasterio.warp import reproject, Resampling
from rasterio import features
from scipy import ndimage
from skimage.measure import label, regionprops
from PIL import Image, ImageDraw
from pyproj import Transformer
from mapgame import osm as O
from mapgame.area import Area
from mapgame.dem import UA
from scenario.common import osm_elements

ap = argparse.ArgumentParser(); ap.add_argument("--year", default="2022"); ap.add_argument("--cove", default=None); args = ap.parse_args()
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
AREAS = {"Avalon harbor": (-118.3345, 33.3385, -118.3165, 33.3525), "Descanso Bay / Hamilton Cove": (-118.3340, 33.3505, -118.3200, 33.3600),
         "Isthmus Cove / Two Harbors": (-118.5075, 33.4385, -118.4820, 33.4520), "Fourth of July / Cherry Cove": (-118.5120, 33.4480, -118.4985, 33.4600),
         "Catalina Harbor": (-118.5195, 33.4200, -118.5010, 33.4370), "Emerald Bay": (-118.5390, 33.4640, -118.5230, 33.4760), "Howlands Landing": (-118.5290, 33.4470, -118.5190, 33.4560),
         "Toyon Bay / White's Landing": (-118.3760, 33.3700, -118.3480, 33.3940), "Little Harbor": (-118.4780, 33.3820, -118.4660, 33.3920), "Big Fisherman Cove (USC)": (-118.4880, 33.4420, -118.4780, 33.4480),
         "Long Point / Italian Gardens / Goat Harbor": (-118.4000, 33.4020, -118.3640, 33.4210), "Empire Landing / Ripper's / Cabrillo": (-118.4520, 33.4180, -118.3990, 33.4310)}
if args.cove: AREAS = {k: v for k, v in AREAS.items() if args.cove.lower() in k.lower()}
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120).read()
token = json.loads(get("https://planetarycomputer.microsoft.com/api/sas/v1/token/naip"))["token"]
els = osm_elements(); inv = None
boats = []; md = ["# Boats on the water, from NAIP aerial imagery\n", "Compact bright hulls on the sea inside each cove, 0.6 m pixels; length is the long axis. Mooring buoys, kelp, surf and glint are rejected by size, shape and colour; piers and the shore are masked. Check images: atlas/out/boats_check_*.png.\n",
                  "| cove | image date | boats | under 6 m | 6 to 12 m | 12 to 20 m | 20 to 35 m | over 35 m | longest |", "|---|---|---|---|---|---|---|---|---|"]
for name, bbox in AREAS.items():
    A = Area(*bbox, res=0.6)
    L = O.layers(A, els); land = O.land_mask(A, L)
    if inv is None: inv = Transformer.from_crs(A.epsg, 4326, always_xy=True)
    body = json.dumps({"collections": ["naip"], "bbox": list(bbox), "datetime": f"{args.year}-01-01T00:00:00Z/{args.year}-12-31T23:59:59Z", "limit": 10}).encode()
    req = urllib.request.Request("https://planetarycomputer.microsoft.com/api/stac/v1/search", data=body, headers={"Content-Type": "application/json", "User-Agent": UA})
    items = json.loads(urllib.request.urlopen(req, timeout=120).read())["features"]
    if not items: md.append(f"| {name} | none | | | | | | | |"); continue
    img = np.zeros((4, A.H, A.W), "float32"); got = np.zeros((A.H, A.W), bool); dates = set()
    for it in items:
        href = it["assets"]["image"]["href"] + "?" + token; dates.add(it["properties"]["datetime"][:10])
        with rasterio.open("/vsicurl/" + href) as s:
            tmp = np.zeros((4, A.H, A.W), "float32")
            reproject(rasterio.band(s, [1, 2, 3, 4]), tmp, dst_transform=A.transform, dst_crs=f"EPSG:{A.epsg}", resampling=Resampling.bilinear, dst_nodata=0)
        m = tmp.sum(0) > 0; img[:, m & ~got] = tmp[:, m & ~got]; got |= m
    sea = (~land) & got
    shore = ndimage.distance_transform_edt(~land | ~got) * A.res          # distance from the shoreline, metres
    sea &= (shore > 20) & (shore < 450)                                     # surf is bright; moorings are near shore
    masks = [g.buffer(6) for g in L["piers"]] + [b.buffer(3) for b in L["buildings"]]
    if masks: sea &= ~features.rasterize(((g, 1) for g in masks), out_shape=(A.H, A.W), transform=A.transform, fill=0, dtype="uint8").astype(bool)
    if sea.sum() < 1000: md.append(f"| {name} | {','.join(sorted(dates))} | no water in image | | | | | | |"); continue
    R, G, B, N = img; bright = (R + G + B) / 3
    wb = np.median(bright[sea]); wn = np.median(N[sea])
    # the sea's own texture: where the water is choppy (whitecaps), demand more contrast
    sea_b = np.where(sea, bright, np.nan)
    filled = np.nan_to_num(sea_b, nan=wb)
    loc_med = ndimage.uniform_filter(filled, size=61)                                          # local mean, 36 m window
    rough = ndimage.uniform_filter(np.abs(filled - loc_med), size=61)                          # local mean absolute deviation
    thresh = loc_med + np.maximum(50, 5.0 * rough)
    cand = sea & (bright > thresh) & (bright > 105) & (N > wn + 10) & ((R - B) > -25)
    cand = ndimage.binary_opening(cand, structure=np.ones((2, 2)))
    lab = label(cand, connectivity=2); px = A.res; sizes = []; kept = []
    for rp in regionprops(lab):
        length, width = rp.axis_major_length * px, rp.axis_minor_length * px
        area = rp.area * px * px
        if area < 8 or length < 5 or length > 130: continue
        if rp.solidity < 0.55: continue                                  # ragged = foam or glint
        if width > 0 and length / width > 7: continue                    # a streak, not a hull
        if length < 8 and width > 0 and length / width < 1.4: continue   # round and small: a buoy or a crest
        r, c = rp.centroid; x = A.E0 + (c + 0.5) * px; y = A.N0 + A.H * px - (r + 0.5) * px; lon, lat = inv.transform(x, y)
        boats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]}, "properties": {"cove": name, "length_m": round(length, 1), "width_m": round(width, 1), "date": sorted(dates)[0]}})
        sizes.append(length); kept.append(rp.bbox)
    s_ = np.array(sizes); n = len(sizes)
    md.append(f"| {name} | {','.join(sorted(dates))} | {n} | {int((s_ < 6).sum())} | {int(((s_ >= 6) & (s_ < 12)).sum())} | {int(((s_ >= 12) & (s_ < 20)).sum())} | {int(((s_ >= 20) & (s_ < 35)).sum())} | {int((s_ >= 35).sum())} | {s_.max() if n else 0:.0f} m |")
    print(md[-1], flush=True)
    # check image: the true-colour crop with each kept detection boxed
    rgb = np.clip(np.stack([R, G, B], -1), 0, 255).astype("uint8"); im = Image.fromarray(rgb); d = ImageDraw.Draw(im)
    for r0, c0, r1, c1 in kept: d.rectangle([c0 - 2, r0 - 2, c1 + 2, r1 + 2], outline=(255, 60, 60), width=2)
    d.text((8, 8), f"{name} {sorted(dates)[0]} boats={n}", fill=(255, 255, 0))
    im.save(os.path.join(OUT, "boats_check_" + "".join(ch if ch.isalnum() else "_" for ch in name) + ".png"))
if not args.cove:
    json.dump({"type": "FeatureCollection", "features": boats}, open(os.path.join(OUT, "boats.geojson"), "w"))
    open(os.path.join(OUT, "boats.md"), "w").write("\n".join(md) + "\n")
print("boats", len(boats))
