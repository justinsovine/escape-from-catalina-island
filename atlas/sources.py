"""Fetch every outside dataset the atlas uses beyond OSM and the DEMs, from sources verified reachable on
2026-10-17. Each function is idempotent (skips files that exist) and writes under data/. Run: python atlas/sources.py [all|conservancy|lacounty|assessor|census|inat|winds|mines|topo|topobathy|landcover|moorings]"""
import os, sys, json, time, urllib.request, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
from mapgame import DATA
from mapgame.dem import UA, _get

ISLAND = (-118.63, 33.29, -118.28, 33.50)
def get(url):
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=180).read())
def arcgis_layer(base, out, where="1=1", bbox=None, fields="*", page=1000):
    """Every feature of an ArcGIS REST layer as GeoJSON (WGS84), paged."""
    if os.path.exists(out): return out
    feats, off = [], 0
    while True:
        p = dict(where=where, outFields=fields, outSR=4326, f="geojson", resultOffset=off, resultRecordCount=page)
        if bbox: p.update(geometry="%s,%s,%s,%s" % bbox, geometryType="esriGeometryEnvelope", inSR=4326, spatialRel="esriSpatialRelIntersects")
        d = get(base + "/query?" + urllib.parse.urlencode(p)); fs = d.get("features", []); feats += fs
        if len(fs) < page: break
        off += len(fs); time.sleep(0.3)
    os.makedirs(os.path.dirname(out), exist_ok=True); json.dump({"type": "FeatureCollection", "features": feats}, open(out, "w")); print(out, len(feats)); return out

def conservancy():
    """Catalina Island Conservancy public ArcGIS Online layers (owner ldennhardtconservancy; vegetation hosted by CSULB)."""
    S5 = "https://services5.arcgis.com/6todkfokiIaUCZfU/arcgis/rest/services/"
    for name, url in (("vegetation_2000", "https://services3.arcgis.com/vq5vGR4r1YX7ueLg/arcgis/rest/services/Catalina_vegetation_CIC/FeatureServer/0"),
                      ("roads_trails_2017", S5 + "roads_trails_all_2017/FeatureServer/0"), ("watersheds_WMU", S5 + "WMU/FeatureServer/0"),
                      ("property_boundary", S5 + "CIC_Property_Boundary/FeatureServer/7"), ("roads_ownership", S5 + "CICRoads_Ownership/FeatureServer/1"), ("trails_KI", S5 + "Trails_KI/FeatureServer/32")):
        arcgis_layer(url, os.path.join(DATA, "conservancy", name + ".geojson"))

def lacounty():
    """LA County: LARIAC building outlines with heights (2020), the 2009 tsunami inundation layers, county facilities."""
    arcgis_layer("https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines_(2020)/FeatureServer/0", os.path.join(DATA, "lacounty", "buildings_2020.geojson"), bbox=ISLAND)
    H = "https://public.gis.lacounty.gov/public/rest/services/LACounty_Dynamic/Hazards/MapServer/"
    arcgis_layer(H + "6", os.path.join(DATA, "lacounty", "tsunami_runup_line.geojson"), bbox=ISLAND)
    arcgis_layer(H + "7", os.path.join(DATA, "lacounty", "tsunami_inundation_zones.geojson"), bbox=ISLAND)
    arcgis_layer("https://gis.conservation.ca.gov/server/rest/services/MOL/MOLMines/FeatureServer/0", os.path.join(DATA, "lacounty", "mol_mines.geojson"), bbox=ISLAND)

def assessor(year=2025):
    """LA County Assessor parcel roll (table with parcel centroids) for ZIP 90704: use, units, floor area, year built."""
    out = os.path.join(DATA, "lacounty", f"assessor_{year}_90704.geojson")
    if os.path.exists(out): return
    base = "https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Parcel_Data_2021_Table/FeatureServer/0/query?"
    rows, off = [], 0
    while True:
        d = get(base + urllib.parse.urlencode(dict(where=f"SitusZIP LIKE '90704%' AND RollYear={year}", outFields="*", f="json", resultOffset=off, resultRecordCount=1000)))
        fs = [f["attributes"] for f in d.get("features", [])]; rows += fs
        if len(fs) < 1000: break
        off += len(fs); time.sleep(0.3)
    feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [r["CENTER_LON"], r["CENTER_LAT"]]} if r.get("CENTER_LON") else None, "properties": r} for r in rows]
    os.makedirs(os.path.dirname(out), exist_ok=True); json.dump({"type": "FeatureCollection", "features": feats}, open(out, "w")); print(out, len(rows))

def census():
    """2020 census blocks with population and housing units (TIGERweb carries P1 counts; no key needed)."""
    arcgis_layer("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2020/MapServer/10", os.path.join(DATA, "lacounty", "census_blocks_2020.geojson"), bbox=ISLAND, fields="GEOID,NAME,POP100,HU100,AREALAND,CENTLAT,CENTLON")

def inat():
    """iNaturalist research-grade observations on the island for the game's animals (no key; threatened taxa may be obscured)."""
    taxa = {"bison": "Bison bison", "mule_deer": "Odocoileus hemionus", "island_fox": "Urocyon littoralis", "bald_eagle": "Haliaeetus leucocephalus", "rattlesnake": "Crotalus oreganus", "sea_lion": "Zalophus californianus", "harbor_seal": "Phoca vitulina", "feral_cat": "Felis catus", "raven": "Corvus corax"}
    os.makedirs(os.path.join(DATA, "inat"), exist_ok=True)
    for key, tn in taxa.items():
        out = os.path.join(DATA, "inat", key + ".geojson")
        if os.path.exists(out): continue
        feats, page = [], 1
        while True:
            d = get("https://api.inaturalist.org/v1/observations?" + urllib.parse.urlencode(dict(taxon_name=tn, nelat=ISLAND[3], nelng=ISLAND[2], swlat=ISLAND[1], swlng=ISLAND[0], per_page=200, page=page, quality_grade="research")))
            for o in d.get("results", []):
                if o.get("geojson"): feats.append({"type": "Feature", "geometry": o["geojson"], "properties": {"date": o.get("observed_on"), "obscured": o.get("obscured"), "accuracy_m": o.get("positional_accuracy"), "taxon": (o.get("taxon") or {}).get("name"), "id": o.get("id")}})
            if page * 200 >= d.get("total_results", 0) or page >= 15: break
            page += 1; time.sleep(0.6)
        json.dump({"type": "FeatureCollection", "features": feats}, open(out, "w")); print(out, len(feats))

def winds(y0=2015, y1=2025):
    """Catalina Airport (AVX) hourly observations from the Iowa Environmental Mesonet ASOS archive."""
    out = os.path.join(DATA, "weather", f"asos_AVX_{y0}_{y1}.csv")
    if os.path.exists(out): return
    os.makedirs(os.path.dirname(out), exist_ok=True)
    _get(f"https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=AVX&data=drct&data=sknt&data=gust&data=tmpf&data=relh&year1={y0}&month1=1&day1=1&year2={y1}&month2=12&day2=31&tz=America/Los_Angeles&format=onlycomma&latlon=no&missing=M&trace=T&direct=no&report_type=3", out); print(out)

def topo():
    """USGS historical 7.5-minute quads (1950 editions, plus 1943 East) as GeoTIFF; they carry mine and adit symbols."""
    folder = os.path.join(DATA, "histtopo"); os.makedirs(folder, exist_ok=True)
    for q in ("East_300230_1950", "North_300235_1950", "South_300238_1950", "West_300242_1950", "East_466348_1943"):
        out = os.path.join(folder, q + ".tif")
        if not os.path.exists(out): _get(f"https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/CA/CA_Santa%20Catalina%20{q}_24000_geo.tif", out); print(out)

def topobathy():
    """NOAA CoNED Southern California 1 m topobathymetric DEM (2016), windowed over the harbors straight from S3 (cloud-optimized)."""
    import rasterio
    from rasterio.windows import from_bounds
    from rasterio.warp import transform_bounds
    base = "/vsicurl/https://noaa-nos-coastal-lidar-pds.s3.amazonaws.com/dem/CA_Southern_CoNED_DEM_2016_8658/Southern_California_Topobathy_DEM_1m_%s.tif"
    tiles = {"F_09": (348124, 369199, 3689700, 3712222), "F_10": (369199, 390274, 3689700, 3712222), "G_09": (348124, 369199, 3667178, 3689700), "G_10": (369199, 390274, 3667178, 3689700)}
    areas = {"isthmus": (-118.5200, 33.4200, -118.4780, 33.4560), "avalon": (-118.3400, 33.3330, -118.3120, 33.3560), "little_harbor": (-118.4820, 33.3800, -118.4640, 33.3920), "emerald_howlands": (-118.5420, 33.4440, -118.5160, 33.4760)}
    folder = os.path.join(DATA, "dem", "topobathy"); os.makedirs(folder, exist_ok=True)
    for name, bb in areas.items():
        b = transform_bounds("EPSG:4326", "EPSG:26911", *bb)
        for tname, (x0, x1, y0, y1) in tiles.items():
            out = os.path.join(folder, f"coned_{name}_{tname}.tif")
            if os.path.exists(out) or not (b[0] < x1 and b[2] > x0 and b[1] < y1 and b[3] > y0): continue
            with rasterio.open(base % tname) as s:
                w = from_bounds(max(b[0], x0), max(b[1], y0), min(b[2], x1), min(b[3], y1), s.transform).round_offsets().round_lengths()
                a = s.read(1, window=w); prof = s.profile.copy(); prof.update(width=w.width, height=w.height, transform=s.window_transform(w), driver="GTiff", compress="deflate", tiled=True)
                with rasterio.open(out, "w", **prof) as dst: dst.write(a, 1)
            print(out)

def landcover(bbox=(-118.5040, 33.4380, -118.4900, 33.4480), name="isthmus", size=(2000, 1430)):
    """LA County LARIAC7 land cover 2023 (4 inch classes: tree canopy, grass, tall shrubs, bare soil, water, buildings, roads, paved) as a map export."""
    out = os.path.join(DATA, "lacounty", f"landcover_2023_{name}.png"); os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out): return
    _get("https://cache.gis.lacounty.gov/cache/rest/services/LARIAC7/LANDCOVER_2023/MapServer/export?" + urllib.parse.urlencode(dict(bbox="%s,%s,%s,%s" % bbox, bboxSR=4326, imageSR=4326, size="%d,%d" % size, layers="show:0", format="png", transparent="false", f="image")), out); print(out)

def moorings():
    """The two public PDFs with the mooring maps (images inside)."""
    folder = os.path.join(DATA, "moorings"); os.makedirs(folder, exist_ok=True)
    for name, url in (("two_harbors_manual_2024.pdf", "https://assets.simpleviewinc.com/simpleview/image/upload/v1/clients/catalinaisland/Two_Harbors_Policy_and_Procedures_Manual_REVISED_April_2024_FINAL_064bd6e3-4784-4e33-9e2e-18a58297059e.pdf"),
                      ("avalon_mooring_chart_2018.pdf", "https://www.cityofavalon.gov/DocumentCenter/View/175/Mooring-Information-and-Mooring-Map-PDF")):
        out = os.path.join(folder, name)
        if not os.path.exists(out): _get(url, out); print(out)

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    steps = dict(conservancy=conservancy, lacounty=lacounty, assessor=assessor, census=census, inat=inat, winds=winds, mines=lacounty, topo=topo, topobathy=topobathy, landcover=landcover, moorings=moorings)
    for k, f in steps.items():
        if which in ("all", k): f()
