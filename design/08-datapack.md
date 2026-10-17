# 08. The data pack: formats, schemas, sizes, pipeline, engine duties, saves

Decisions: 1, 3, 32, 33, 58.

## Frame

All geometry is in meters in one island-local frame: UTM zone 11N (EPSG:32611) with the origin moved to the
south-west corner of the island bounding box, x east, y north. Rasters carry a sidecar with origin, cell size
and size; vector files use plain `[x, y]` pairs. Longitude and latitude never appear in the pack. The atlas
grid already uses this frame at 10 m.

## Files

| file | format | content |
|---|---|---|
| `terrain/height_10m.png`, `height_30m.png` | 16-bit PNG, 0.1 m units | heightmap |
| `terrain/threshold_10m.png`, `threshold_30m.png` | 16-bit PNG, 0.1 m units | spill level (01) |
| `terrain/cost_30m.png` | 8-bit PNG | cost class |
| `terrain/landcover_30m.png` | 8-bit PNG | class from the vegetation map and the county land cover |
| `terrain/regions_30m.png` | 8-bit PNG | cove and town region id per cell |
| `terrain/land_10m.bin` | bit mask | land |
| `terrain/*.json` | sidecars | origin, cell size, size, units, class tables |
| `features.json` | JSON | every feature: id, kind, subtype, tier, geometry, attributes, flags baked |
| `graph.json` | JSON | nodes and edges with length, grade, surface, names, cells crossed |
| `regions.json` | JSON | coves, towns, watersheds as polygons with ids and arrival times and exposure factors |
| `infra.json` | JSON | infrastructure graph |
| `groups.json` | JSON | population groups for the scenario date |
| `boats.json`, `vehicles.json` | JSON | entities with fields from 06 |
| `items.json` | JSON | item templates: devices, tools, weapons, food classes, maps |
| `maps.json` | JSON | map item instances (official, unofficial, chart, phone) with coverage and errors |
| `weather/tape_<date>.json` | JSON arrays | hourly rows (05), one file per eligible start date |
| `fallout/plume_<sector>_<speed>.png` | 8-bit PNG at 250 m | deposition shape |
| `events.json` | JSON | the scripted chain templates and the trial and chastening templates with domain tags |
| `overrides.json` | JSON | hand overrides keyed by stable id, applied last by the pipeline |
| `scenario/*.json` | JSON | scenario files (05) |
| `styles/*.json` | JSON | palette tokens and marks per view (the existing palettes) |
| `images/*.jpg` | baked hillshade and town images per style, optional | render-only |

GeoJSON is not required: the geometry convention is `Point [x,y]`, `Line [[x,y],...]`, `Polygon [[[x,y],...]]`
inside plain JSON. A one-line converter to GeoJSON in WGS84 exists in the pipeline for GIS checks.

## Core schemas

```
feature  { id, kind, subtype, tier, name?, geom, elev_m, threshold_m, cove, town, hazard_zone,
           attrs: { ... per kind }, shelter_pf?, construction?, capacity?, contents?: { category: qty },
           source: [ ... ], fictional?: true }
node     { id, xy, kind: junction | dead_end | place, feature_id? }
edge     { id, a, b, length_m, grade_pct, surface, class: road | track | trail | path | coast | pier,
           names: [], cells: [cell index ...] }
region   { id, kind: cove | town | watershed, polygon, arrival_s_from_shelf, exposure_factor }
group    { ... 06 }   entity { ... 06 }   item { ... 06 }   map_item { ... 04 }
event    { ... 05 }   belief { ... 04 }   view { ... 04 }
```

Every record has `id`; references are by id, never by index. Ids are stable across rebuilds through the
pipeline's id map (02).

## Sizes (bake output)

| tier | grid | cells | 16-bit | 8-bit | bit mask |
|---|---|---|---|---|---|
| 10 m | 3287 x 2374 | 7.80 M | 15.6 MB | 7.8 MB | 0.98 MB |
| 30 m | 1096 x 792 | 0.87 M | 1.7 MB | 0.9 MB | 0.11 MB |
| 100 m | 329 x 238 | 0.08 M | 0.2 MB | 0.1 MB | 0.01 MB |

The 10 m threshold raster compresses to 2.2 MB as PNG; the 30 m one to 0.3 MB. Vector sizes: 938 flagged
features, about 3,900 building outlines before merging, 1,526 graph edges with 28,891 vertices (441 km),
about 1,750 boat and buoy detections, 40 groups, 40 infrastructure nodes. The whole pack without town images
fits under 40 MB; with the 10 m rasters loaded as textures and the 30 m rasters in memory, runtime memory is
under 100 MB on any target including a browser.

Per-tick cost at 60 s steps: water levels for 15 coves, 40 infrastructure nodes, 40 groups, up to 200
drifting boats, a fallout update on 13 k cells per episode hour. Viewsheds on movement only (31 k cells at 3 km
on the 30 m grid). Nothing per frame touches the 10 m grid except drawing.

## Pipeline steps (Python, in this repo)

1. `scenario/common.py` and `atlas/build.py`: DEM, OSM, inventory with flags (exists).
2. `atlas/sources.py`: outside datasets (exists).
3. `atlas/lariac/`: aerial mosaics and detections (exists).
4. `atlas/bake.py`: threshold, slope, cost, graph statistics (exists; writes `data/bake/`).
5. To write: `pack/` builder that merges buildings, assigns stable ids, builds the graph with junction
   splitting, computes cove arrival times and exposure factors, derives shelter classes and contents from use
   and floor area, writes groups for a date, cuts weather tapes with the eligibility rule, bakes plume shapes,
   applies overrides, and emits the files above with a manifest and checksums.

## Engine duties

Load the pack; keep the state layer; run the event scheduler and the tick rules in 03, 05 and 06; keep one
knowledge store per observer and run perception; render views from knowledge; write the event log. No
engine code decides what exists or where: that is the pack.

## Saves, determinism, multiplayer

- A save is the scenario file plus the event log plus a periodic snapshot of state and knowledge for fast
  resume. Replay of the log from the seed reproduces the run, which is the test harness for rules.
- Randomness comes from one seeded generator per system (events, encounters, drift, director), so adding a
  system never shifts another's rolls.
- Multiplayer (09): a host runs the simulation and ships state deltas and each player's own knowledge
  deltas; the log is shared, knowledge is not. The faith director's state stays on the host, per player.

## Licensing notes to act on at the end (decision 58)

- OSM-derived files (features, graph) carry the ODbL attribution and ship as an open data file.
- County and state layers are public records; the aerial-derived points are our own derived data.
- Animal density fields built from observation records: filter to CC0 and CC BY observations before the
  final build; keep all records during development.
- Scripture text: KJV only.
- No raw imagery in the pack; the town images are our hillshade renders.
