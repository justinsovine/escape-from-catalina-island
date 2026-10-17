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

# extra layers from the outside sources fetched by atlas/sources.py (each is optional: missing files are skipped)
DATA_DIR = os.path.join(ROOT, "data")
def load(path):
    f = os.path.join(DATA_DIR, path); return json.load(open(f))["features"] if os.path.exists(f) else []
def px_geom(g):
    if g is None: return None
    if g["type"] == "Point": return conv([g["coordinates"]])[0]
    if g["type"] == "LineString": return [conv(g["coordinates"])]
    if g["type"] == "MultiLineString": return [conv(c) for c in g["coordinates"]]
    if g["type"] == "Polygon": return [conv(r) for r in g["coordinates"]]
    if g["type"] == "MultiPolygon": return [conv(r) for poly in g["coordinates"] for r in poly]
    return None
extra = []
def add_extra(id, name, kind, color, items, on=False, radius=3, weight=1.2, dash=None, fill=0.12, source=""):
    if items: extra.append(dict(id=id, name=name, kind=kind, color=color, items=items, on=on, radius=radius, weight=weight, dash=dash, fill=fill, source=source))
# Conservancy roads and trails with names
items = [{"p": px_geom(f["geometry"]), "props": {k: f["properties"].get(k) for k in ("NAME", "TYPE", "Miles", "width_ft", "Comment") if f["properties"].get(k)}} for f in load("conservancy/roads_trails_2017.geojson") if f["geometry"]]
add_extra("cons_trails", "Conservancy roads and trails 2017, with names", "lines", "#9ad0a8", [i for i in items if i["p"]], source="Catalina Island Conservancy ArcGIS Online")
# LA County building outlines with heights
items = []
for f in load("lacounty/buildings_2020.geojson"):
    if not f["geometry"]: continue
    pr = f["properties"]; items.append({"p": px_geom(f["geometry"]), "props": {"height_ft": pr.get("HEIGHT"), "ground_ft": pr.get("ELEV"), "code": pr.get("CODE"), "source": pr.get("SOURCE"), "year": pr.get("DATE_")}})
add_extra("county_bldg", "county building outlines with heights (LARIAC 2020)", "polys", "#dfe6ea", items, fill=0.0, weight=0.7, source="LA County GIS, Countywide Building Outlines (2020)")
# the 2009 state tsunami inundation mapping as the county serves it
items = [{"p": px_geom(f["geometry"]), "props": {"layer": "2009 tsunami inundation run-up line"}} for f in load("lacounty/tsunami_runup_line.geojson") if f["geometry"]]
add_extra("tsu2009", "2009 tsunami inundation line (CGS, county copy)", "lines", "#ffb3a8", items, on=True, weight=1.4, dash="2 3", source="LA County GIS Hazards service, layers 6 and 7")
# wildlife observations (iNaturalist, research grade)
for key, name, col, on in (("bison", "bison sightings", "#d08b3c", True), ("mule_deer", "mule deer sightings", "#e0c08a", False), ("island_fox", "island fox sightings", "#f29a4b", False), ("bald_eagle", "bald eagle sightings", "#f3f6f8", False),
                           ("rattlesnake", "rattlesnake sightings", "#b5e853", False), ("sea_lion", "sea lion sightings", "#8ab4f8", False), ("harbor_seal", "harbor seal sightings", "#b9a6ff", False)):
    items = [{"xy": px_geom(f["geometry"]), "props": {"date": f["properties"].get("date"), "taxon": f["properties"].get("taxon"), "accuracy_m": f["properties"].get("accuracy_m"), "obscured": f["properties"].get("obscured")}} for f in load(f"inat/{key}.geojson") if f["geometry"]]
    add_extra("inat_" + key, f"{name} ({len(items)}, iNaturalist)", "points", col, items, on=on, radius=2.6, source="iNaturalist API, research grade, 1984 to 2026")
# hotels with room counts from the assessor roll
items = []
for f in load("lacounty/assessor_2025_90704.geojson"):
    pr = f["properties"]
    if f["geometry"] and "hotel" in (pr.get("UseCodeDescChar2") or "").lower() and int(pr.get("Units") or 0) > 0:
        items.append({"xy": px_geom(f["geometry"]), "props": {"address": (pr.get("PropertyLocation") or "").split("  AVALON")[0].strip(), "rooms": pr.get("Units"), "floor_sqft": pr.get("SQFTmain"), "built": pr.get("YearBuilt")}})
add_extra("hotels", f"hotels by room count ({sum(i['props']['rooms'] for i in items)} rooms, assessor 2025)", "points", "#c9a6ff", items, radius=4, source="LA County Assessor parcel roll 2025")
# mines and quarries: USGS MRDS, the state's Mines Online, and symbols read off the 1950 USGS quads
mines = [("Black Jack Mine, shaft (1950 quad symbol; USGS ore body)", -118.40259, 33.38924), ("Black Jack Mine (USGS MRDS record)", -118.40617, 33.38532), ("Renton Mine (1950 quad symbol; USGS ore body)", -118.3141, 33.3236),
         ("Renton adit, upper (1950 quad)", -118.3141, 33.3245), ("prospect above Renton (1950 quad)", -118.3152, 33.3275), ("adit by Pebbly Beach road (1950 quad)", -118.3091, 33.3298), ("Jewfish Point workings (1950 quad)", -118.3044, 33.3197),
         ("Santa Catalina copper-silver mine, Cherry Valley (USGS MRDS)", -118.51257, 33.45003), ("Empire Landing Quarry (USGS MRDS, Connolly-Pacific)", -118.4659, 33.43973), ("Empire Quarry, Graham Bros (USGS MRDS)", -118.4737, 33.43033), ("moonstone diggings (USGS MRDS)", -118.36729, 33.38834)]
for f in load("lacounty/mol_mines.geojson"):
    if f["geometry"]: mines.append((f["properties"].get("MineName", "quarry") + " (state Mines Online, active)", *f["geometry"]["coordinates"]))
add_extra("mines", "mines, adits and quarries", "points", "#d6a3ff", [{"xy": conv([(lo, la)])[0], "props": {"what": n, "lat": round(la, 5), "lon": round(lo, 5)}} for n, lo, la in mines], on=True, radius=5, source="USGS MRDS, CA Mines Online, USGS 1950 7.5-minute quads")
# harbor depth contours from NOAA's 1 m topobathy
try:
    import glob, rasterio
    from skimage.measure import find_contours
    from pyproj import Transformer as _T
    tr = _T.from_crs(26911, 4326, always_xy=True); items = []
    for f in glob.glob(os.path.join(DATA_DIR, "dem", "topobathy", "coned_*.tif")):
        with rasterio.open(f) as s:
            a = s.read(1, out_shape=(s.height // 4, s.width // 4)).astype("float32"); a[a == s.nodata] = np.nan
            for lv in (-5, -10, -20, -30, -50):
                for c in find_contours(np.nan_to_num(a, nan=1000.0), lv):
                    if len(c) < 20: continue
                    xs, ys = rasterio.transform.xy(s.transform, c[::3, 0] * 4, c[::3, 1] * 4); lons, lats = tr.transform(xs, ys)
                    items.append({"p": [conv(list(zip(lons, lats)))], "props": {"depth_m": -lv}})
    add_extra("depths", "harbor depth contours 5 to 50 m (NOAA 1 m topobathy)", "lines", "#5fb3e6", items, weight=0.9, source="NOAA CoNED Southern California 1 m topobathy 2016")
except Exception as e: print("depth contours skipped:", e)
print("extra layers:", [(e["id"], len(e["items"])) for e in extra])
DATA = dict(W=W, H=H, res=A.res, lonlat=A.lonlat, towns=towns, features=feats, boats=boats,
            roads=gj_lines("roads.geojson", ("name", "highway")), trails=gj_lines("trails.geojson", ("name", "highway", "sac_scale")), tct=gj_lines("tct.geojson", ("name",)),
            piers=gj_lines("piers.geojson", ("name",)), streams=gj_lines("streams.geojson", ("name",)), buildings=gj_polys("buildings.geojson", ("name", "building", "elev_m", "cgs_zone", "runup_10m")),
            waters=gj_polys("waters.geojson", ("name", "water")), camps=gj_polys("camps.geojson", ("name",)), hazard=hazard, extra=extra)
facts = open(os.path.join(HERE, "FACTS.md")).read() if os.path.exists(os.path.join(HERE, "FACTS.md")) else ""
gaps = open(os.path.join(HERE, "GAPS.md")).read() if os.path.exists(os.path.join(HERE, "GAPS.md")) else ""
boats_md = open(os.path.join(OUT, "boats.md")).read() if os.path.exists(os.path.join(OUT, "boats.md")) else ""
sources = open(os.path.join(HERE, "SOURCES.md")).read() if os.path.exists(os.path.join(HERE, "SOURCES.md")) else ""
tpl = open(os.path.join(HERE, "web_template.html")).read()
css = open(os.path.join(HERE, "leaflet.css")).read()
html = tpl.replace("/*LEAFLET_CSS*/", css).replace("/*DATA*/", "window.ATLAS=" + json.dumps(DATA, separators=(",", ":")) + ";").replace("/*TEXT*/", "window.TEXT=" + json.dumps({"facts": facts, "gaps": gaps, "boats": boats_md, "sources": sources}) + ";")
open(os.path.join(WEB, "index.html"), "w").write(html)
# the artifact variant: the publisher wraps the page in its own document skeleton, so strip ours and keep title, metas, style and body
import re as _re
art = html
for tag in ("<!doctype html>", '<html lang="en">', "<head>", "</head>", "<body>", "</body>", "</html>", '<meta charset="utf-8">', '<meta name="viewport" content="width=device-width, initial-scale=1">'):
    art = art.replace(tag, "")
art = art.replace("<title>Catalina Atlas</title>", '<title>Catalina Atlas</title>\n<meta name="claude:viewport-fit-sides" content="cover">')
open(os.path.join(WEB, "artifact.html"), "w").write(art.strip() + "\n")
print("features", len(feats), "boats", len(boats), "buildings", len(DATA["buildings"]), "html MB", round(len(html) / 1e6, 2), "towns", towns)
