"""The interactive atlas: one HTML page (Leaflet over a hillshade image, all layers embedded) for publishing.
Run: python atlas/web.py  -> atlas/out/web/index.html (+ basemap jpgs). Needs atlas/build.py outputs."""
import os, sys, json, csv, base64
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
import numpy as np
from PIL import Image
from matplotlib.colors import LightSource, to_rgb
from scipy.ndimage import gaussian_filter, label
from shapely.geometry import shape
from mapgame import dem, osm as O
from mapgame.area import Area
from mapgame.palette import get
from scenario.common import island, dem_path, lidar_mosaic, osm_elements

OUT = os.path.join(HERE, "out"); WEB = os.path.join(OUT, "web"); os.makedirs(WEB, exist_ok=True); P = get("night")
A, Z, land, L, els = island()
Zf = np.nan_to_num(Z, nan=0.0).astype("float32"); H, W = Zf.shape
def flooded(h):
    lab, _ = label((~land) | (Zf < h)); sea = np.bincount(lab[~land].ravel()).argmax(); return (lab == sea) & land
def picture(Zw, landw, res, zmax=600.0):
    k = max(1.0, 3.0 / res)
    hs = LightSource(azdeg=315, altdeg=42).hillshade(gaussian_filter(Zw, k * 0.5), vert_exag=1.8, dx=res, dy=res)
    t = np.clip(gaussian_filter(Zw, k * 2) / zmax, 0, 1)[..., None]
    lo, hi = np.array(P["slab_lo"]), np.array(P["slab_hi"])
    img = (lo + (hi - lo) * t) * (0.55 + 0.9 * hs)[..., None]; img[~landw] = to_rgb(P["plate"])
    blue = np.array(to_rgb(P["days"]["tue"]))
    for h, a in ((20.0, 0.30), (10.5, 0.60)):
        lab, _ = label((~landw) | (Zw < h)); sea = np.bincount(lab[~landw].ravel()).argmax() if (~landw).any() else -1
        m = (lab == sea) & landw; img[m] = img[m] * (1 - a) + blue * a
    return (np.clip(img, 0, 1) * 255).astype("uint8")
Image.fromarray(picture(Zf, land, A.res)).save(os.path.join(WEB, "basemap.jpg"), quality=82)
def px(x, y): return [round((x - A.E0) / A.res, 1), round((A.N0 + A.H * A.res - y) / A.res, 1)]
towns = {}
for key, bbox in (("avalon", (-118.345, 33.328, -118.300, 33.358)), ("twoharbors", (-118.532, 33.418, -118.468, 33.462))):
    B = Area(*bbox, res=2.0); Lb = O.layers(B, els); landb = O.land_mask(B, Lb)
    Zb = dem.from_geotiff(B, dem_path()); Z1 = lidar_mosaic(B); Zb = np.where(np.isnan(Z1), Zb, Z1); Zb = np.nan_to_num(Zb, nan=0.0).astype("float32")
    Image.fromarray(picture(Zb, landb, B.res)).save(os.path.join(WEB, f"{key}.jpg"), quality=82)
    towns[key] = dict(file=f"{key}.jpg", nw=px(B.E0, B.N0 + B.H * B.res), se=px(B.E0 + B.W * B.res, B.N0))

# vector data in image pixel coordinates
def conv(coords):
    return [px(*A.xy(c[0], c[1])) for c in coords]
def gj_lines(name, keep):
    out = []
    for ft in json.load(open(os.path.join(OUT, name)))["features"]:
        g = ft["geometry"]; parts = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
        for part in parts: out.append({"p": conv(part), **{k: ft["properties"].get(k) for k in keep if ft["properties"].get(k) is not None}})
    return out
def gj_polys(name, keep):
    out = []
    for ft in json.load(open(os.path.join(OUT, name)))["features"]:
        g = ft["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for rings in polys: out.append({"p": [conv(r) for r in rings], **{k: ft["properties"].get(k) for k in keep if ft["properties"].get(k) is not None}})
    return out
feats = []
for r in csv.DictReader(open(os.path.join(OUT, "features.csv"))):
    x, y = A.xy(float(r["lon"]), float(r["lat"])); d = {k: v for k, v in r.items() if v not in ("", None) and k not in ("lon", "lat")}
    d["xy"] = px(x, y); d["lon"], d["lat"] = float(r["lon"]), float(r["lat"]); feats.append(d)
boats = []
bf = os.path.join(OUT, "boats.geojson")
if os.path.exists(bf):
    for ft in json.load(open(bf))["features"]:
        lon, lat = ft["geometry"]["coordinates"]; boats.append({"xy": px(*A.xy(lon, lat)), **ft["properties"]})
hazard = [p for p in gj_polys("hazard.geojson", ("zone",)) if p.get("zone") == "CGS tsunami hazard area"]
DATA = dict(W=W, H=H, res=A.res, lonlat=A.lonlat, towns=towns, features=feats, boats=boats,
            roads=gj_lines("roads.geojson", ("name", "highway")), trails=gj_lines("trails.geojson", ("name", "highway", "sac_scale")), tct=gj_lines("tct.geojson", ("name",)),
            piers=gj_lines("piers.geojson", ("name",)), streams=gj_lines("streams.geojson", ("name",)), buildings=gj_polys("buildings.geojson", ("name", "building", "elev_m", "cgs_zone", "runup_10m")),
            waters=gj_polys("waters.geojson", ("name", "water")), camps=gj_polys("camps.geojson", ("name",)), hazard=hazard)
facts = open(os.path.join(HERE, "FACTS.md")).read() if os.path.exists(os.path.join(HERE, "FACTS.md")) else ""
gaps = open(os.path.join(HERE, "GAPS.md")).read() if os.path.exists(os.path.join(HERE, "GAPS.md")) else ""
boats_md = open(os.path.join(OUT, "boats.md")).read() if os.path.exists(os.path.join(OUT, "boats.md")) else ""
tpl = open(os.path.join(HERE, "web_template.html")).read()
css = open(os.path.join(HERE, "leaflet.css")).read()
html = tpl.replace("/*LEAFLET_CSS*/", css).replace("/*DATA*/", "window.ATLAS=" + json.dumps(DATA, separators=(",", ":")) + ";").replace("/*TEXT*/", "window.TEXT=" + json.dumps({"facts": facts, "gaps": gaps, "boats": boats_md}) + ";")
open(os.path.join(WEB, "index.html"), "w").write(html)
# the artifact variant: the publisher wraps the page in its own document skeleton, so strip ours and keep title, metas, style and body
import re as _re
art = html
for tag in ("<!doctype html>", '<html lang="en">', "<head>", "</head>", "<body>", "</body>", "</html>", '<meta charset="utf-8">', '<meta name="viewport" content="width=device-width, initial-scale=1">'):
    art = art.replace(tag, "")
art = art.replace("<title>Catalina Atlas</title>", '<title>Catalina Atlas</title>\n<meta name="claude:viewport-fit-sides" content="cover">')
open(os.path.join(WEB, "artifact.html"), "w").write(art.strip() + "\n")
print("features", len(feats), "boats", len(boats), "buildings", len(DATA["buildings"]), "html MB", round(len(html) / 1e6, 2), "towns", towns)
