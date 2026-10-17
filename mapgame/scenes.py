"""A scene is everything a style needs: the Area, the elevation grid (m), OSM layers in map coords,
the route, and a few words. Named scenes live in SCENES; any bbox works through `build`."""
import os
from . import DATA, FT
from .area import Area
from . import dem, osm

SCENES = {
    "catalina": dict(bbox=(-118.622, 33.372, -118.452, 33.492), trail=r"Trans.Catalina", title="CATALINA · WEST END", zoom=14,
                     step_ft=150, slab_m=110, tree_ft=700,
                     labels=[(-118.4979, 33.4423, "TWO HARBORS"), (-118.5492, 33.4731, "PARSONS LANDING"), (-118.6020, 33.4778, "STARLIGHT")],
                     ports=[(-118.4979, 33.4423, "TWO HARBORS")], camps=[(-118.5492, 33.4731, "PARSONS"), (-118.4708, 33.3861, "LITTLE HARBOR")],
                     crt_labels=[(-118.6020, 33.4778, "???", None), (-118.5687, 33.4599, "SILVER PEAK", "peak"), (-118.5200, 33.4760, "EMERALD BAY", None),
                                 (-118.5067, 33.4246, "CAT HARBOR", None), (-118.5212, 33.4343, "TORQUEMADA", "peak")],
                     pins=[(-118.497895, 33.442299, "S", "#eef1f2", "Two Harbors"), (-118.549237, 33.473085, "▲", "#e05a3a", "Parsons, camp"), (-118.554310, 33.455034, "⚑", "#f5c400", "viewpoint")],
                     card_title="Trans-Catalina Trail · west end", card_sub="Two Harbors, Silver Peak, Parsons Landing"),
    "isthmus": dict(bbox=(-118.55, 33.383, -118.46, 33.476), trail=r"Trans.Catalina", title="TWO HARBORS · CATALINA", zoom=14,
                    step_ft=250, slab_m=150, tree_ft=700,
                    labels=[(-118.4979, 33.4423, "TWO HARBORS"), (-118.4745, 33.3880, "LITTLE HARBOR"), (-118.5067, 33.4306, "CATALINA HARBOR")],
                    ports=[(-118.4979, 33.4423, "TWO HARBORS")], camps=[(-118.4708, 33.3861, "LITTLE HARBOR")]),
    "sheltowee": dict(bbox=(-83.74, 37.74, -83.58, 37.86), trail=r"Sheltowee Trace", title="SHELTOWEE TRACE · RED RIVER GORGE", zoom=13,
                      step_ft=150, slab_m=110, sea_ft=-1000, tree_ft=99999,
                      card_title="Sheltowee Trace · Red River Gorge", card_sub="Daniel Boone National Forest, Kentucky"),
}


def build(bbox, trail=None, title="", res=10.0, zoom=13, geotiff=None, **kw):
    """Build a scene for any lon/lat bbox. Elevation from a local GeoTIFF if given, else terrain tiles."""
    A = Area(*bbox, res=res)
    tif = geotiff or os.environ.get("MAPGAME_DEM")
    Z = dem.from_geotiff(A, tif) if tif else dem.from_terrarium(A, z=zoom)
    els = osm.fetch(bbox)
    layers = osm.layers(A, els)
    rt = osm.route(A, els, trail) if trail else None
    land = osm.land_mask(A, layers)
    S = dict(area=A, Z=Z, osm=layers, route=rt, land=land, title=title or "MAP",
             dem_src=os.path.basename(tif) if tif else f"Mapzen Terrarium z{zoom}",
             step_ft=100, slab_m=70, sea_ft=1, tree_ft=99999, labels=[], ports=[], camps=[], crt_labels=[], pins=[],
             card_title=title.title() if title else "Route", card_sub="")
    S.update(kw)
    for k in ("labels", "ports", "camps"):          # lon/lat in the registry -> map coords
        S[k] = [(*A.xy(lon, lat), name) for lon, lat, name in S[k]]
    S["crt_labels"] = [(*A.xy(lon, lat), name, sym) for lon, lat, name, sym in S["crt_labels"]]
    S["pins"] = [(*A.xy(lon, lat), *rest) for lon, lat, *rest in S["pins"]]
    return S


def load(name, res=10.0):
    if name not in SCENES: raise SystemExit(f"unknown scene {name}; known: {', '.join(SCENES)}")
    return build(res=res, **SCENES[name])
