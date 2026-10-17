"""Island inventory from OpenStreetMap, the 10 m DEM and the state's tsunami hazard line.
Every feature gets: height, distance to the coast, whether it is inside the CGS tsunami hazard area, whether a
10.5 m run-up (the level that joins the two harbors) or a 20 m run-up reaches it, and a fallout note.
Writes atlas/out/*.geojson, atlas/out/features.csv and atlas/out/summary.md.  Run: python atlas/build.py"""
import os, sys, csv, json, math, re, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
import numpy as np
from pyproj import Transformer
from rasterio import features
from scipy.ndimage import label, distance_transform_edt
from shapely.geometry import Point, LineString, Polygon, mapping
from shapely.ops import unary_union
from mapgame import osm as O
from scenario.common import island, cgs_hazard

OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
RUNUP = 10.5
A, Z, land, L, els = island()
Zl = np.where(land, np.nan_to_num(Z, nan=0), -1.0).astype("float32")
inv = Transformer.from_crs(A.epsg, 4326, always_xy=True)

# hazard rasters: sea-connected cells below a level, and the state's hazard area
def flooded(h):
    lab, _ = label((~land) | (Zl < h)); sea = np.bincount(lab[~land].ravel()).argmax(); return (lab == sea) & land
F10, F20 = flooded(RUNUP), flooded(20.0)
haz_polys = cgs_hazard(A); haz = unary_union(haz_polys).intersection(A.plate)
HZ = features.rasterize(((g, 1) for g in (haz.geoms if hasattr(haz, "geoms") else [haz])), out_shape=(A.H, A.W), transform=A.transform, fill=0, dtype="uint8").astype(bool)
DC = distance_transform_edt(land) * A.res                      # distance to the coast, metres
def at(x, y):
    r, c = A.rc(x, y); r, c = int(round(r)), int(round(c)); r = min(max(r, 0), A.H - 1); c = min(max(c, 0), A.W - 1)
    return dict(elev_m=round(float(Zl[r, c]), 1), coast_m=round(float(DC[r, c])), cgs_zone=bool(HZ[r, c]), runup_10m=bool(F10[r, c]), runup_20m=bool(F20[r, c]))

# geometry per element
nodes = {e["id"]: (e["lon"], e["lat"]) for e in els if e["type"] == "node"}
ways = {e["id"]: e for e in els if e["type"] == "way"}
def geom(e):
    if e["type"] == "node": return Point(A.xy(e["lon"], e["lat"]))
    if e["type"] == "way":
        pts = [A.xy(*nodes[n]) for n in e["nodes"] if n in nodes]
        if len(pts) < 2: return None
        t = e.get("tags", {})
        closed = len(pts) >= 4 and pts[0] == pts[-1]
        if closed and (t.get("area") != "no") and not any(k in t for k in ("highway", "waterway", "barrier")) : return Polygon(pts)
        if closed and ("building" in t or "landuse" in t or "natural" in t or "leisure" in t or "amenity" in t): return Polygon(pts)
        return LineString(pts)
    if e["type"] == "relation" and e.get("tags", {}).get("type") == "multipolygon":
        outers = [Polygon([A.xy(*nodes[n]) for n in ways[m["ref"]]["nodes"] if n in nodes]) for m in e.get("members", []) if m["type"] == "way" and m.get("role", "outer") == "outer" and m["ref"] in ways and len(ways[m["ref"]]["nodes"]) >= 4]
        outers = [p for p in outers if p.is_valid and p.area > 0]
        return unary_union(outers) if outers else None
    return None

# the game's categories
FOOD = {"restaurant", "cafe", "fast_food", "bar", "pub", "ice_cream", "canteen", "food_court", "biergarten"}
CIVIC = {"townhall", "courthouse", "library", "school", "kindergarten", "place_of_worship", "community_centre", "post_office", "bank", "atm", "theatre", "cinema", "social_facility", "events_venue"}
def classify(t):
    """kind, subtype. Kind order matters: the first match wins."""
    a, s, tr, le, mm, na, aw, pw, hi, lu, ww, b = (t.get(k, "") for k in ("amenity", "shop", "tourism", "leisure", "man_made", "natural", "aeroway", "power", "historic", "landuse", "waterway", "building"))
    if a in FOOD: return "food", a
    if s in ("supermarket", "convenience", "general", "hardware", "outdoor", "bakery", "alcohol", "sports", "bicycle", "scuba_diving", "confectionery", "electronics", "variety_store", "department_store"): return "store", s
    if a == "fuel" or ww == "fuel": return "fuel", "boat" if ww == "fuel" else "road"
    if a in ("hospital", "clinic", "doctors", "dentist", "pharmacy") or t.get("healthcare"): return "medical", a or t.get("healthcare")
    if a in ("fire_station", "police", "ranger_station") or t.get("emergency") in ("ambulance_station", "lifeguard", "water_rescue", "assembly_point", "disaster_help_point"): return "emergency", a or t.get("emergency")
    if a in ("drinking_water", "water_point") or mm in ("water_tap", "water_well", "water_works", "pumping_station", "reservoir_covered", "water_tower") or na == "spring" or ww in ("dam", "weir") or (mm == "storage_tank" and t.get("content", "water") in ("water", "")) or na == "water" or lu == "reservoir": return "water", a or mm or na or ww or lu
    if tr in ("camp_site", "camp_pitch") or le in ("summer_camp", "camp_site") or t.get("camp_site"): return "camp", tr or le
    if tr in ("hotel", "motel", "guest_house", "hostel", "chalet", "apartment") or b in ("hotel", "dormitory", "cabin"): return "lodging", tr or b
    if a == "ferry_terminal" or aw in ("aerodrome", "helipad", "runway", "hangar", "apron") or mm == "pier" or le == "slipway" or a in ("boat_rental", "car_rental", "bicycle_rental") or t.get("highway") == "bus_stop" or t.get("seamark:type") in ("small_craft_facility", "harbour", "mooring", "anchorage") or t.get("mooring") or t.get("harbour"): return "transport", a or aw or mm or le or t.get("seamark:type") or "mooring"
    if pw in ("plant", "generator", "substation") or mm in ("tower", "mast", "communications_tower", "wastewater_plant", "works", "lighthouse", "storage_tank", "silo") or lu in ("industrial", "quarry", "landfill") or b in ("industrial", "warehouse", "hangar") or t.get("office") == "energy_supplier" or t.get("telecom"): return "infrastructure", pw or mm or lu or b or "telecom"
    if a == "shelter" or na in ("cave_entrance", "rock_shelter") or mm in ("mine", "adit", "mineshaft", "bunker") or hi in ("mine", "ruins", "bunker", "fort", "military") or t.get("military"): return "shelter", a or na or mm or hi or t.get("military")
    if a in CIVIC or b in ("school", "college", "church", "civic", "public", "hospital"): return "civic", a or b
    if t.get("office") or t.get("craft"): return "office", t.get("office") or t.get("craft")
    if a in ("toilets", "shower"): return "sanitation", a
    if tr in ("viewpoint", "attraction", "information", "picnic_site", "museum", "artwork", "zoo", "nature_centre", "gallery") or le in ("picnic_table", "firepit", "park", "playground", "pitch", "golf_course", "swimming_pool", "nature_reserve"): return "poi", tr or le
    if na in ("peak", "saddle", "beach", "bay", "cape", "arch", "cliff", "ridge", "valley", "waterfall") or ww == "waterfall": return "land", na or ww
    if t.get("place"): return "place", t["place"]
    if hi: return "historic", hi
    return None, None

FALLOUT = {  # a note per water subtype: how the source stands to fallout and to salt water
    "spring": "open: surface spring, fallout settles on it; needs filtering and time", "water": "open: reservoir surface collects fallout; sediment settles in days", "reservoir": "open: reservoir surface collects fallout",
    "dam": "open: impounded water", "weir": "open", "drinking_water": "piped: safe if the source is a well or covered tank, suspect if it is an open reservoir", "water_point": "piped", "water_tap": "piped",
    "storage_tank": "covered: tank water is protected from fallout; refill may not be", "reservoir_covered": "covered: protected from fallout", "water_tower": "covered", "water_works": "covered: treatment plant; needs power", "pumping_station": "covered: needs power", "water_well": "protected: groundwater"}

rows = []; lines = {"road": [], "trail": [], "stream": [], "powerline": [], "pier": [], "coast": []}; polys = {"building": [], "water": [], "wood": [], "landuse": [], "camp": []}
RANK_TOWN = [("Avalon", -118.3267, 33.3428), ("Two Harbors", -118.4979, 33.4423), ("Little Harbor", -118.4708, 33.3861), ("Airport in the Sky", -118.4150, 33.4049), ("Middle Ranch", -118.4383, 33.3553),
             ("Emerald Bay", -118.5318, 33.4692), ("Toyon Bay", -118.3545, 33.3746), ("White's Landing", -118.3700, 33.3900), ("Parsons Landing", -118.5492, 33.4731), ("Catalina Harbor", -118.5085, 33.4290),
             ("Howlands Landing", -118.5244, 33.4495), ("Black Jack", -118.4062, 33.3855), ("Pebbly Beach", -118.3115, 33.3350), ("Ben Weston", -118.4813, 33.3676), ("Rancho Escondido", -118.4507, 33.3860), ("Starlight Beach", -118.5950, 33.4790)]
TOWN_XY = [(n, *A.xy(lo, la)) for n, lo, la in RANK_TOWN]
ANCHORS = TOWN_XY + [(e["tags"]["name"], *A.xy(e["lon"], e["lat"])) for e in els if e["type"] == "node" and e.get("tags", {}).get("name") and
                     (e["tags"].get("natural") == "bay" or e["tags"].get("place") in ("hamlet", "village", "town", "locality", "neighbourhood"))]
def town_of(x, y):
    """Nearest named cove or settlement within 1.5 km, else the nearest hub within 2.5 km, else backcountry."""
    n, d = min(((n, math.hypot(x - tx, y - ty)) for n, tx, ty in ANCHORS), key=lambda r: r[1])
    if d < 1500: return n
    n, d = min(((n, math.hypot(x - tx, y - ty)) for n, tx, ty in TOWN_XY), key=lambda r: r[1])
    return n if d < 2500 else f"backcountry near {n}"

for e in els:
    t = e.get("tags", {})
    if not t: continue
    g = geom(e)
    if g is None or g.is_empty: continue
    hw, wwy, pw = t.get("highway"), t.get("waterway"), t.get("power")
    if g.geom_type == "LineString":
        if hw in ("path", "footway", "track", "bridleway", "steps", "cycleway", "pedestrian"): lines["trail"].append((g, t))
        elif hw and hw not in ("bus_stop", "street_lamp", "turning_circle", "stop", "crossing", "trailhead", "rest_area"): lines["road"].append((g, t))
        elif wwy in ("stream", "river", "canal"): lines["stream"].append((g, t))
        elif pw in ("line", "minor_line"): lines["powerline"].append((g, t))
        elif t.get("man_made") == "pier": lines["pier"].append((g, t))
        elif t.get("natural") == "coastline": lines["coast"].append((g, t))
    elif g.geom_type in ("Polygon", "MultiPolygon"):
        if "building" in t: polys["building"].append((g, t))
        elif t.get("natural") == "water" or t.get("landuse") == "reservoir": polys["water"].append((g, t))
        elif t.get("natural") == "wood" or t.get("landuse") == "forest": polys["wood"].append((g, t))
        elif t.get("landuse") in ("quarry", "industrial", "cemetery", "farmland", "farmyard", "landfill", "military", "residential"): polys["landuse"].append((g, t))
        if t.get("tourism") == "camp_site" or t.get("leisure") == "summer_camp": polys["camp"].append((g, t))
    kind, sub = classify(t)
    if kind is None: continue
    if kind == "land" and sub in ("cliff", "ridge", "valley", "arch"): continue
    p = g.centroid if g.geom_type != "Point" else g
    x, y = p.x, p.y; lon, lat = inv.transform(x, y); f = at(x, y)
    name = t.get("name", "")
    if kind == "water":
        f["fallout"] = FALLOUT.get(sub, "unknown"); f["tsunami"] = "salt water / debris" if (f["cgs_zone"] or f["runup_10m"]) else "clear"
    elif kind in ("camp", "lodging", "food", "store", "medical", "emergency", "civic", "shelter", "infrastructure", "transport", "office"):
        b = t.get("building", "")
        hard = ("industrial", "warehouse", "hangar", "hospital", "school", "college", "church", "civic", "public", "commercial", "retail") if kind != "camp" else ()
        f["fallout"] = ("open air: no shelter" if kind == "camp" else "underground" if sub in ("cave_entrance", "mine", "adit", "mineshaft", "bunker", "rock_shelter") else
                        "solid building: fair shelter" if (b in hard or sub in hard) else "light building: poor shelter" if b else "unknown structure")
        f["tsunami"] = "state hazard zone" if f["cgs_zone"] else ("below 10.5 m run-up" if f["runup_10m"] else ("below 20 m run-up" if f["runup_20m"] else "clear"))
    else:
        f["fallout"] = ""; f["tsunami"] = "state hazard zone" if f["cgs_zone"] else ("below 10.5 m run-up" if f["runup_10m"] else "clear")
    extra = {k: t[k] for k in ("capacity", "drinking_water", "toilets", "shower", "fireplace", "operator", "website", "phone", "opening_hours", "content", "cuisine", "rooms", "beds", "fee", "backcountry", "reservation", "description", "ele", "building", "building:levels", "surface", "sac_scale", "generator:source", "generator:output:electricity", "ref", "seamark:type", "length") if k in t}
    rows.append(dict(kind=kind, subtype=sub, name=name, town=town_of(x, y), lon=round(lon, 6), lat=round(lat, 6), osm=f"{e['type'][0]}{e['id']}", **f, **extra))

# write features
keys = ["kind", "subtype", "name", "town", "lon", "lat", "elev_m", "coast_m", "cgs_zone", "runup_10m", "runup_20m", "tsunami", "fallout", "osm"]
extras = sorted({k for r in rows for k in r} - set(keys))
with open(os.path.join(OUT, "features.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=keys + extras); w.writeheader()
    for r in sorted(rows, key=lambda r: (r["kind"], r["town"], r["name"])): w.writerow(r)
def fc(items, props):
    return {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": mapping(g), "properties": p} for g, p in zip(items, props)]}
def to_ll(g, tol=0.0):
    from shapely import transform as sh_t
    g2 = g.simplify(tol) if tol else g
    return sh_t(g2, lambda c: np.c_[inv.transform(c[:, 0], c[:, 1])])
json.dump({"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]}, "properties": {k: v for k, v in r.items() if k not in ("lon", "lat")}} for r in rows]}, open(os.path.join(OUT, "features.geojson"), "w"))
for name, tol, keep in (("road", 2.0, ("name", "highway", "surface", "access")), ("trail", 2.0, ("name", "highway", "surface", "sac_scale", "trail_visibility")), ("stream", 5.0, ("name", "waterway", "intermittent")), ("powerline", 5.0, ("power", "voltage")), ("pier", 0.0, ("name", "length")), ("coast", 5.0, ())):
    json.dump(fc([to_ll(g, tol) for g, t in lines[name]], [{k: t.get(k) for k in keep if k in t} for g, t in lines[name]]), open(os.path.join(OUT, f"{name}s.geojson"), "w"))
for name, tol, keep in (("building", 0.5, ("name", "building", "building:levels", "amenity", "tourism", "shop")), ("water", 2.0, ("name", "natural", "water", "landuse")), ("wood", 5.0, ("natural", "landuse")), ("landuse", 5.0, ("name", "landuse")), ("camp", 2.0, ("name", "tourism", "leisure", "capacity", "operator"))):
    props = []
    for g, t in polys[name]:
        p = {k: t.get(k) for k in keep if k in t}
        if name in ("building", "camp"): p.update(at(g.centroid.x, g.centroid.y))
        props.append(p)
    json.dump(fc([to_ll(g, tol) for g, t in polys[name]], props), open(os.path.join(OUT, f"{name}s.geojson"), "w"))
# hazard polygons: state zone, 10.5 m and 20 m run-up
hz_feats = []
for nm, mask in (("CGS tsunami hazard area", HZ & land), ("run-up 10.5 m", F10), ("run-up 20 m", F20)):
    for g, v in features.shapes(mask.astype("uint8"), mask=mask, transform=A.transform):
        if v == 1:
            from shapely.geometry import shape
            s = shape(g)
            if s.area >= 2000: hz_feats.append((to_ll(s, 5.0), {"zone": nm}))
json.dump(fc([g for g, p in hz_feats], [p for g, p in hz_feats]), open(os.path.join(OUT, "hazard.geojson"), "w"))
# the Trans-Catalina Trail
tct = O.route(A, els, r"Trans.Catalina")
if tct is not None: json.dump(fc([to_ll(tct, 2.0)], [{"name": "Trans-Catalina Trail"}]), open(os.path.join(OUT, "tct.geojson"), "w"))

# summary
S = []
def say(s=""): S.append(s)
say("# Island inventory (OpenStreetMap + USGS 3DEP + CGS)\n")
say(f"Grid {A.res:g} m, land {land.sum() * A.res ** 2 / 1e6:.0f} km2. Run-up bands are sea-connected ground below 10.5 m and 20 m; the CGS zone is the state's tsunami hazard area.\n")
say("| layer | count | length or area |\n|---|---|---|")
say(f"| roads | {len(lines['road'])} | {sum(g.length for g, t in lines['road']) / 1609.34:.0f} mi |")
say(f"| trails and tracks | {len(lines['trail'])} | {sum(g.length for g, t in lines['trail']) / 1609.34:.0f} mi |")
say(f"| streams (mapped, mostly dry) | {len(lines['stream'])} | {sum(g.length for g, t in lines['stream']) / 1609.34:.0f} mi |")
say(f"| buildings | {len(polys['building'])} | {sum(g.area for g, t in polys['building']) / 1e4:.1f} ha footprint |")
say(f"| water bodies | {len(polys['water'])} | {sum(g.area for g, t in polys['water']) / 1e4:.1f} ha |")
say(f"| piers | {len(lines['pier'])} | |")
cnt = collections.Counter(r["kind"] for r in rows)
say("\n## Features by kind\n\n| kind | n | in state hazard zone | below 10.5 m run-up |\n|---|---|---|---|")
for k, n in cnt.most_common(): say(f"| {k} | {n} | {sum(1 for r in rows if r['kind'] == k and r['cgs_zone'])} | {sum(1 for r in rows if r['kind'] == k and r['runup_10m'])} |")
bz = [(t.get("name", ""), at(g.centroid.x, g.centroid.y)) for g, t in polys["building"]]
say(f"\nBuildings inside the state hazard zone: {sum(1 for n, f in bz if f['cgs_zone'])} of {len(bz)}; below the 10.5 m run-up: {sum(1 for n, f in bz if f['runup_10m'])}; below 20 m: {sum(1 for n, f in bz if f['runup_20m'])}.")
for kind, title in (("food", "Food"), ("store", "Stores"), ("fuel", "Fuel"), ("water", "Water sources"), ("camp", "Camps"), ("lodging", "Lodging"), ("medical", "Medical"), ("emergency", "Emergency services"), ("transport", "Transport: piers, terminals, aviation"), ("infrastructure", "Infrastructure"), ("shelter", "Shelters, caves, mines, ruins"), ("civic", "Civic")):
    items = [r for r in rows if r["kind"] == kind]
    if not items: continue
    say(f"\n## {title} ({len(items)})\n\n| name | type | where | height | coast | tsunami | fallout | notes |\n|---|---|---|---|---|---|---|---|")
    for r in sorted(items, key=lambda r: (r["town"], -r["elev_m"])):
        notes = "; ".join(f"{k}={r[k]}" for k in ("capacity", "drinking_water", "toilets", "shower", "operator", "content", "cuisine", "generator:source", "generator:output:electricity", "rooms", "building") if k in r)
        say(f"| {r['name'] or '(unnamed)'} | {r['subtype']} | {r['town']} | {r['elev_m']:.0f} m | {r['coast_m']:.0f} m | {r['tsunami']} | {r['fallout']} | {notes} |")
peaks = sorted([r for r in rows if r["kind"] == "land" and r["subtype"] == "peak" and r["name"]], key=lambda r: -r["elev_m"])[:12]
say("\n## Summits\n\n| name | height |\n|---|---|"); [say(f"| {r['name']} | {r['elev_m']:.0f} m |") for r in peaks]
open(os.path.join(OUT, "summary.md"), "w").write("\n".join(S) + "\n")
print("\n".join(S[:40])); print(f"... {len(rows)} features, written to {OUT}")
