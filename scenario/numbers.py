"""The numbers behind the scenario, from the 10 m DEM, OSM, Terrarium/ETOPO bathymetry and the state's tsunami map.
Run: python scenario/numbers.py   (writes scenario/numbers.txt)"""
import os, sys, re, math, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, label, map_coordinates
from shapely.geometry import Point
from shapely.ops import unary_union
from rasterio import features
from mapgame import DATA
from mapgame.dem import _get
from scenario.common import island, cgs_hazard

R_EARTH = 6371000.0
def hav(lon0, lat0, lon1, lat1):
    p0, p1 = math.radians(lat0), math.radians(lat1); dl = math.radians(lon1 - lon0)
    a = math.sin((p1 - p0) / 2) ** 2 + math.cos(p0) * math.cos(p1) * math.sin(dl / 2) ** 2
    return 2 * R_EARTH * math.asin(math.sqrt(a))

out = open(os.path.join(HERE, "numbers.txt"), "w")
def say(s=""): print(s); out.write(s + "\n")

A, Z, land, L, els = island()
Zl = np.where(land, np.nan_to_num(Z, nan=0), -1.0)
say(f"grid {A.W}x{A.H} at {A.res:g} m; land {land.sum() * A.res ** 2 / 1e6:.1f} km2")

# ---- tsunami travel: shallow-water speed sqrt(g*depth) along a straight line, Terrarium z10 bathymetry (ETOPO) ----
z, x0, x1, y0, y1 = 10, 174, 176, 409, 411
cache = os.path.join(DATA, "terrarium"); os.makedirs(cache, exist_ok=True)
M = np.zeros(((y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256), "float32")
for ty in range(y0, y1 + 1):
    for tx in range(x0, x1 + 1):
        f = os.path.join(cache, f"{z}_{tx}_{ty}.png")
        if not os.path.exists(f): _get(f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{tx}/{ty}.png", f)
        a = np.asarray(Image.open(f).convert("RGB"), "float32")
        M[(ty - y0) * 256:(ty - y0 + 1) * 256, (tx - x0) * 256:(tx - x0 + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
def px(lon, lat):
    n = 2 ** z
    return (lon + 180) / 360 * n * 256 - x0 * 256, (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n * 256 - y0 * 256
def travel(p, q, name, n=600):
    lons = np.linspace(p[0], q[0], n); lats = np.linspace(p[1], q[1], n)
    xs, ys = zip(*[px(lo, la) for lo, la in zip(lons, lats)])
    d = -map_coordinates(M, [ys, xs], order=1)                                    # depth, positive down
    ds = np.array([hav(lons[i], lats[i], lons[i + 1], lats[i + 1]) for i in range(n - 1)])
    dm = np.maximum((d[:-1] + d[1:]) / 2, 3.0); t = (ds / np.sqrt(9.81 * dm)).sum(); dist = ds.sum()
    say(f"  {name}: {dist / 1609.34:.1f} mi, max depth {d.max():.0f} m, wave {t / 60:.1f} min, sound {dist / 343 / 60:.1f} min after the flash")
    return lons, lats, d, ds
say("\nTSUNAMI TRAVEL TIME")
LAH, LBH = (-118.2467, 33.7067), (-118.1850, 33.7200)        # Angels Gate (Port of LA), Queen's Gate (Long Beach)
TH, AV = (-118.4963, 33.4447), (-118.3240, 33.3450)          # Isthmus Cove pier, Avalon pier
lons, lats, d, ds = travel(LAH, TH, "Port of LA to Two Harbors")
travel(LBH, TH, "Long Beach to Two Harbors"); travel(LAH, AV, "Port of LA to Avalon"); travel(LBH, AV, "Long Beach to Avalon")
cum = np.concatenate([[0], np.cumsum(ds)])
i = int(np.argmax(d > 500)); rem = cum[-1] - cum[i]; tt = (ds[i:] / np.sqrt(9.81 * np.maximum((d[i:-1] + d[i + 1:]) / 2, 3.0))).sum()
say(f"  shelf break (depth passes 500 m) {cum[i] / 1609.34:.1f} mi out from LA, {rem / 1609.34:.1f} mi from Two Harbors: a slide there arrives in {tt / 60:.1f} min")

# ---- the isthmus: the sea level at which Isthmus Cove joins Catalina Harbor ----
say("\nISTHMUS")
cx, cy = A.xy(-118.5015, 33.4375); r0, c0 = map(int, A.rc(cx, cy)); hh, ww = int(1800 / A.res), int(1500 / A.res)
win = (slice(r0 - hh, r0 + hh), slice(c0 - ww, c0 + ww)); Zw, Lw = np.nan_to_num(Z[win], nan=0), land[win]
def rc_in(lon, lat):
    r, c = A.rc(*A.xy(lon, lat)); return int(r) - (r0 - hh), int(c) - (c0 - ww)
sNE, sSW = rc_in(-118.4935, 33.4490), rc_in(-118.5105, 33.4245)
assert not Lw[sNE] and not Lw[sSW] and label(~Lw)[0][sNE] != label(~Lw)[0][sSW]
over = next(h for h in np.arange(0.5, 80, 0.5) if (lambda lab: lab[sNE] == lab[sSW])(label((~Lw) | (Zw < h))[0]))
say(f"  run-up that joins the two harbors: {over:g} m ({over * 3.28084:.0f} ft)")
zl = np.where(Lw, Zw, np.nan)
say(f"  isthmus land below 10 m: {np.nansum(zl < 10) * A.res ** 2 / 1e4:.0f} ha; below 20 m: {np.nansum(zl < 20) * A.res ** 2 / 1e4:.0f} ha")

# ---- nearest ground at or above a height (straight line; paths are longer) ----
say("\nNEAREST HIGH GROUND (straight line)")
spots = {"Two Harbors town": (-118.4979, 33.4423), "Avalon, Crescent Ave": (-118.3258, 33.3425), "Little Harbor camp": (-118.4708, 33.3861),
         "Parsons Landing": (-118.5492, 33.4731), "Emerald Bay camp": (-118.5285, 33.4672)}
for thr in (30, 100):
    dist, idx = distance_transform_edt(~(land & (Zl >= thr)), return_distances=True, return_indices=True)
    for name, (lon, lat) in spots.items():
        r, c = map(int, A.rc(*A.xy(lon, lat))); dd = dist[r, c] * A.res
        brg = (math.degrees(math.atan2(idx[1][r, c] - c, -(idx[0][r, c] - r))) + 360) % 360
        say(f"  {thr:3d} m ground from {name:22s} {dd:4.0f} m, bearing {brg:3.0f}, run {dd / 3 / 60:.1f} min, walk {dd / 1.4 / 60:.1f} min")

# ---- the state's own line: CGS tsunami hazard area ----
say("\nCGS TSUNAMI HAZARD AREA (the state's evacuation planning line) VS THE ELEVATION BANDS")
haz = unary_union(cgs_hazard(A)).intersection(A.plate)
hz = features.rasterize(((g, 1) for g in (haz.geoms if hasattr(haz, "geoms") else [haz])), out_shape=(A.H, A.W), transform=A.transform, fill=0, dtype="uint8").astype(bool)
zz = Zl[hz & land]
say(f"  hazard area on the island: {np.sum(hz & land) * A.res ** 2 / 1e6:.1f} km2 of land; height p50 {np.percentile(zz, 50):.1f} m, p90 {np.percentile(zz, 90):.1f} m, p99 {np.percentile(zz, 99):.1f} m, max {zz.max():.1f} m")
labw, _ = label((~Lw) | hz[win]); say(f"  hazard area joins the two harbors across the isthmus: {labw[sNE] == labw[sSW]}")
for name, (lon, lat), rad in (("Two Harbors", (-118.4979, 33.4423), 1200), ("Avalon", (-118.3258, 33.3425), 2200)):
    cx, cy = A.xy(lon, lat); bs = [b for b in L["buildings"] if b.centroid.distance(Point(cx, cy)) <= rad]
    bz = np.array([float(Zl[int(r), int(c)]) for b in bs for r, c in [A.rc(b.centroid.x, b.centroid.y)]])
    say(f"  {name}: {len(bs)} buildings within {rad} m; below 10 m {np.sum(bz < 10)}, below 20 m {np.sum(bz < 20)}, below 30 m {np.sum(bz < 30)}; inside the hazard area {sum(haz.contains(b.centroid) for b in bs)}")

# ---- shelter and resource candidates in OSM, high to low ----
say("\nSHELTER / RESOURCE CANDIDATES IN OSM (height, name, tags)")
nodes = {e["id"]: (e["lon"], e["lat"]) for e in els if e["type"] == "node"}
PAT = re.compile(r"science|marine|lab|conserv|ranch|airport|aerodrome|reservoir|tank|water|desal|quarry|mine|tunnel|bunker|cave|shelter|hospital|clinic|fire|sheriff|ranger|lodge|hangar|warehouse|power|generator|fuel|harbor master|school|camp|institute|pump", re.I)
KEYS = {"man_made": {"bunker", "adit", "mineshaft", "storage_tank", "water_tower", "reservoir_covered", "works", "lighthouse", "silo", "water_works", "pumping_station"},
        "natural": {"cave_entrance"}, "historic": {"mine", "bunker", "ruins", "fort"}, "landuse": {"quarry", "reservoir", "industrial", "military"},
        "amenity": {"shelter", "hospital", "clinic", "fire_station", "police", "fuel", "school", "research_institute"}, "aeroway": {"aerodrome", "helipad", "hangar"},
        "power": {"plant", "generator", "substation"}, "building": {"warehouse", "hangar", "hospital", "school", "bunker", "silo"}, "emergency": {"water_tank", "assembly_point"},
        "military": None, "tourism": {"camp_site"}}
rows = []
for e in els:
    t = e.get("tags", {}); nm = t.get("name", "")
    if not t or not (any(k in t and (v is None or t[k] in v) for k, v in KEYS.items()) or (nm and PAT.search(nm))): continue
    if e["type"] == "node": lon, lat = e["lon"], e["lat"]
    elif e["type"] == "way" and [n for n in e["nodes"] if n in nodes]:
        pts = [nodes[n] for n in e["nodes"] if n in nodes]; lon, lat = np.mean([p[0] for p in pts]), np.mean([p[1] for p in pts])
    else: continue
    if not nm and t.get("building") == "industrial": continue
    r, c = map(int, A.rc(*A.xy(lon, lat))); zz = float(Zl[r, c])
    desc = ", ".join(f"{k}={t[k]}" for k in ("man_made", "natural", "historic", "landuse", "amenity", "aeroway", "power", "building", "military", "tourism", "emergency", "office", "leisure") if k in t)
    rows.append((zz, nm, desc, lon, lat))
for zz, nm, desc, lon, lat in sorted(rows, key=lambda r: -r[0]):
    say(f"  {zz:5.0f} m  {nm[:38]:38s} {desc[:46]:46s} {lon:.4f},{lat:.4f}")

# ---- escape distances ----
say("\nESCAPE DISTANCES (great circle, from the Catalina Harbor mouth)")
CAT = (-118.5135, 33.4225)
dests = {"San Clemente I. (Wilson Cove, Navy)": (-118.5550, 33.0050), "Santa Barbara I.": (-119.0370, 33.4750), "Dana Point": (-117.6980, 33.4600),
         "Newport": (-117.8820, 33.5960), "Oceanside": (-117.3960, 33.2060), "San Diego, Point Loma": (-117.2420, 32.6650),
         "Channel Islands Harbor, Oxnard": (-119.2230, 34.1600), "Marina del Rey": (-118.4550, 33.9650), "Port of LA": LAH}
for name, p in dests.items():
    d1 = hav(*CAT, *p); say(f"  {name:34s} {d1 / 1852:5.1f} nm   6 kn {d1 / 1852 / 6:4.1f} h   20 kn {d1 / 1852 / 20:4.1f} h")
out.close()
