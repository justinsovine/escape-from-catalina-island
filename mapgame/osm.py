"""OpenStreetMap for a bbox: fetched from the plain OSM API in small tiles (no Overpass needed), cached,
parsed into the layers the styles use, with the trail pulled out of its route relation."""
import hashlib, json, os, re, time, urllib.request, urllib.error
import numpy as np
from shapely.geometry import LineString, Polygon, Point, MultiLineString
from shapely.ops import linemerge
from . import DATA

UA = "mapgame (github.com/justinsovine/mapgame)"
API = "https://api.openstreetmap.org/api/0.6/map.json?bbox={lon0},{lat0},{lon1},{lat1}"


def _fetch_tile(bbox, depth=0):
    """One map call; if the server refuses (too big or too many nodes), split in four."""
    url = API.format(lon0=bbox[0], lat0=bbox[1], lon1=bbox[2], lat1=bbox[3])
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=240) as r:
            return json.loads(r.read())["elements"]
    except urllib.error.HTTPError as e:
        if e.code in (400, 509) and depth < 4:
            lon0, lat0, lon1, lat1 = bbox; mx, my = (lon0 + lon1) / 2, (lat0 + lat1) / 2
            out = []
            for b in ((lon0, lat0, mx, my), (mx, lat0, lon1, my), (lon0, my, mx, lat1), (mx, my, lon1, lat1)):
                out += _fetch_tile(b, depth + 1); time.sleep(1)
            return out
        raise


def fetch(bbox, tile=0.1):
    """All OSM elements in a lon/lat bbox, merged from tiles no bigger than `tile` degrees on a side."""
    key = hashlib.md5(("%.5f,%.5f,%.5f,%.5f" % tuple(bbox)).encode()).hexdigest()[:12]
    cache = os.path.join(DATA, "osm"); os.makedirs(cache, exist_ok=True)
    f = os.path.join(cache, f"{key}.json")
    if os.path.exists(f):
        return json.load(open(f))["elements"]
    lon0, lat0, lon1, lat1 = bbox; seen = {}
    lons = np.arange(lon0, lon1, tile).tolist() + [lon1]; lats = np.arange(lat0, lat1, tile).tolist() + [lat1]
    for i in range(len(lons) - 1):
        for j in range(len(lats) - 1):
            for e in _fetch_tile((lons[i], lats[j], lons[i + 1], lats[j + 1])):
                seen[(e["type"], e["id"])] = e
            time.sleep(1)
    els = list(seen.values())
    json.dump({"elements": els}, open(f, "w"))
    return els


def layers(area, elements):
    """Shapely geometries in the area's CRS, grouped by what the styles draw."""
    nodes = {e["id"]: (e["lon"], e["lat"]) for e in elements if e["type"] == "node"}
    ways = {e["id"]: e for e in elements if e["type"] == "way"}
    out = dict(buildings=[], streams=[], roads=[], service=[], trails=[], coast=[], water=[], wood=[], piers=[], peaks=[], camps=[], places=[], springs=[])
    RANK = {"city": 0, "town": 1, "village": 2, "hamlet": 3, "locality": 4, "neighbourhood": 5, "isolated_dwelling": 6, "farm": 7}
    def ring(w):
        pts = [area.xy(*nodes[n]) for n in w["nodes"] if n in nodes]
        return Polygon(pts) if len(pts) >= 4 and pts[0] == pts[-1] else None
    for e in elements:
        t = e.get("tags", {})
        if e["type"] == "way":
            pts = [area.xy(*nodes[n]) for n in e["nodes"] if n in nodes]
            if len(pts) < 2: continue
            closed = len(pts) >= 4 and pts[0] == pts[-1]
            if "building" in t and closed: out["buildings"].append(Polygon(pts))
            elif t.get("waterway") in ("stream", "river"): out["streams"].append(LineString(pts))
            elif t.get("natural") == "coastline": out["coast"].append(LineString(pts))
            elif t.get("man_made") == "pier": out["piers"].append(LineString(pts))
            elif t.get("natural") == "water" and closed: out["water"].append(Polygon(pts))
            elif (t.get("natural") == "wood" or t.get("landuse") == "forest") and closed: out["wood"].append(Polygon(pts))
            elif t.get("highway") in ("path", "footway", "track", "bridleway"): out["trails"].append(LineString(pts))
            elif t.get("highway") in ("service", "driveway", "parking_aisle"): out["service"].append(LineString(pts))
            elif "highway" in t: out["roads"].append(LineString(pts))
        elif e["type"] == "relation" and t.get("type") == "multipolygon" and (t.get("natural") == "wood" or t.get("landuse") == "forest"):
            for m in e.get("members", []):      # outer rings only; good enough for tree placement
                if m["type"] == "way" and m.get("role", "outer") == "outer" and m["ref"] in ways:
                    p = ring(ways[m["ref"]])
                    if p is not None: out["wood"].append(p)
        elif e["type"] == "node" and t:
            p = (*area.xy(e["lon"], e["lat"]), t.get("name", ""))
            if t.get("natural") == "peak": out["peaks"].append(p)
            elif t.get("tourism") in ("camp_site", "alpine_hut", "wilderness_hut") or t.get("amenity") == "shelter": out["camps"].append(p)
            elif t.get("natural") == "spring" or t.get("amenity") == "drinking_water" or t.get("man_made") == "water_tap": out["springs"].append(p)
            elif "place" in t and t.get("name") and not re.search(r"post office", t["name"], re.I):
                out["places"].append((RANK.get(t["place"], 9), p))
    out["places"] = [p for _, p in sorted(out["places"], key=lambda r: r[0])]   # biggest places first
    return out


def route(area, elements, name_regex):
    """The trail: member ways of hiking route relations whose name matches, else ways named like it."""
    rx = re.compile(name_regex, re.I)
    nodes = {e["id"]: (e["lon"], e["lat"]) for e in elements if e["type"] == "node"}
    ways = {e["id"]: e for e in elements if e["type"] == "way"}
    picked = set()
    for e in elements:
        t = e.get("tags", {})
        if e["type"] == "relation" and t.get("route") in ("hiking", "foot") and rx.search(t.get("name", "") + " " + t.get("ref", "")):
            picked |= {m["ref"] for m in e.get("members", []) if m["type"] == "way"}
    if not picked:
        picked = {w["id"] for w in ways.values() if rx.search(w.get("tags", {}).get("name", ""))}
    lines = []
    for wid in picked:
        w = ways.get(wid)
        if not w: continue
        pts = [area.xy(*nodes[n]) for n in w["nodes"] if n in nodes]
        if len(pts) > 1: lines.append(LineString(pts))
    if not lines: return None
    merged = linemerge(lines)
    return merged if merged.geom_type != "GeometryCollection" else MultiLineString(lines)


def land_mask(area, osm):
    """True where there is land, from OSM coastline ways (land is on the left of each). No coastline: all land.
    Terrain tiles blend bathymetry near shore, so a height threshold alone misplaces the sea."""
    from shapely.ops import unary_union, polygonize
    from rasterio import features
    plate = area.plate
    coast = [c for g in osm["coast"] for c in ((g.intersection(plate)).geoms if hasattr(g.intersection(plate), "geoms") else [g.intersection(plate)]) if c.geom_type == "LineString" and c.length > 0]
    if not coast:
        return np.ones((area.H, area.W), bool)
    polys = list(polygonize(unary_union(coast + [plate.exterior])))
    votes = np.zeros((len(polys), 2), int)           # per polygon: land votes, sea votes
    for c in coast:                                  # a point just left of the way is land, just right is sea
        xy = np.array(c.coords); i = len(xy) // 2 - 1
        (x0, y0), (x1, y1) = xy[i], xy[i + 1]; dx, dy = x1 - x0, y1 - y0; n = np.hypot(dx, dy) or 1
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2; lx, ly = -dy / n * 8, dx / n * 8
        for j, p in enumerate(polys):
            if p.contains(Point(mx + lx, my + ly)): votes[j, 0] += 1
            if p.contains(Point(mx - lx, my - ly)): votes[j, 1] += 1
    keep = [p for j, p in enumerate(polys) if votes[j, 0] > votes[j, 1]]
    if not keep:
        return np.ones((area.H, area.W), bool)
    return features.rasterize(((p, 1) for p in keep), out_shape=(area.H, area.W), transform=area.transform, fill=0, dtype="uint8").astype(bool)


def clip(osm, poly):
    """Keep only the parts of each layer inside a polygon."""
    out = {}
    for k, v in osm.items():
        if v and isinstance(v[0], tuple):
            out[k] = [p for p in v if poly.contains(Point(p[0], p[1]))]
        else:
            kept = []
            for g in v:
                c = g.intersection(poly)
                if c.is_empty: continue
                kept += list(c.geoms) if hasattr(c, "geoms") else [c]
            out[k] = [g for g in kept if g.geom_type in ("Polygon", "LineString")]
    return out
