#!/usr/bin/env python3
"""Render a scene in a style.

    python render.py iso isthmus out/isthmus.png
    python render.py crt sheltowee out/sheltowee.png
    python render.py wire any out/red-river.png --bbox -83.74 37.74 -83.58 37.86 --trail "Sheltowee" --title "RED RIVER GORGE"

Elevation comes from Mapzen Terrarium tiles unless --dem (or MAPGAME_DEM) names a GeoTIFF such as a USGS 3DEP tile.
Everything downloaded is cached under data/ (or MAPGAME_DATA)."""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mapgame import scenes
from mapgame.styles import STYLES

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument("style", choices=sorted(STYLES))
p.add_argument("scene", help="a name from mapgame/scenes.py, or anything when --bbox is given")
p.add_argument("out")
p.add_argument("--bbox", nargs=4, type=float, metavar=("LON0", "LAT0", "LON1", "LAT1"))
p.add_argument("--trail", help="regex matched against OSM hiking-route relation names (or way names)")
p.add_argument("--title", default="")
p.add_argument("--zoom", type=int, default=13, help="Terrarium zoom: 13 is about 19 m, 14 about 10 m")
p.add_argument("--res", type=float, help="grid metres; defaults per style (iso 20, crt 36, wire 10)")
p.add_argument("--dem", help="local GeoTIFF to use instead of terrain tiles")
p.add_argument("--step-ft", type=float, help="iso: feet per slab")
p.add_argument("--focus", nargs=3, type=float, metavar=("LON", "LAT", "RADIUS_M"), help="wire: show one leg, a disc around this point")
a = p.parse_args()

res = a.res or {"iso": 20.0, "crt": 36.0, "wire": 10.0}[a.style]
if a.bbox:
    S = scenes.build(tuple(a.bbox), trail=a.trail, title=a.title, res=res, zoom=a.zoom, geotiff=a.dem)
else:
    cfg = dict(scenes.SCENES[a.scene]) if a.scene in scenes.SCENES else None
    if cfg is None: sys.exit(f"unknown scene {a.scene}; known: {', '.join(scenes.SCENES)} (or pass --bbox)")
    if a.trail: cfg["trail"] = a.trail
    if a.title: cfg["title"] = a.title
    if a.dem: cfg["geotiff"] = a.dem
    S = scenes.build(res=res, **cfg)
if a.step_ft: S["step_ft"] = a.step_ft; S["slab_m"] = a.step_ft * 0.7
if a.focus: S["focus"] = (*S["area"].xy(a.focus[0], a.focus[1]), a.focus[2])
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
STYLES[a.style](S, a.out)
print("wrote", a.out)
