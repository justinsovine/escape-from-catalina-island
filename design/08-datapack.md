# 08. The data pack: formats, schemas, sizes, pipeline, engine duties, saves

Decisions: 1, 3, 32, 33, 58. Review findings 1, 4, 5, 18, 21, 25 applied (10-review.md).

## Frame

All geometry is in meters in one island-local frame: UTM zone 11N (EPSG:32611) with the origin moved to the
south-west corner of the island bounding box, x east, y north. Rasters carry a sidecar with origin, cell size
and size; vector files use plain `[x, y]` pairs. Longitude and latitude never appear in the pack.

## Files

| file | format | content |
|---|---|---|
| `terrain/height_10m.u16`, `height_30m.u16` | raw little-endian uint16, 0.1 m | heightmap |
| `terrain/thr_ne_10m.u16`, `thr_sw_10m.u16`, `cove_ne_10m.u8`, `cove_sw_10m.u8` | raw uint16 (0.1 m, +50 m offset) and uint8 | spill levels per coast and the cove each refers to (01) |
| `terrain/thr_ne_min_30m.u16`, `thr_ne_max_30m.u16`, `thr_sw_min_30m.u16`, ids | same | the 30 m block min and max |
| `terrain/cost_30m.u8`, `landcover_30m.u8`, `regions_30m.u8`, `cove_10m.u8` | raw uint8 (PNG copies allowed) | cost class, land cover, region and cove ids |
| `terrain/land_10m.bin` | bit mask | land |
| `terrain/*.json` | sidecars | origin, cell size, size, units, offset, class tables, cove list with sides |
| `features.json` | JSON | every feature: id, kind, subtype, tier, geometry, attributes, baked flags, `finds` |
| `graph.json` | JSON | nodes and edges with length, grade, surface, names, cells crossed |
| `regions.json` | JSON | coves (with side, arrival time, exposure factor), towns, watersheds, mooring fields |
| `infra.json` | JSON | infrastructure graph with `serves` |
| `groups.json` | JSON | population groups for the scenario date with the behavior table defaults |
| `boats.json`, `vehicles.json`, `aircraft.json` | JSON | entities with fields from 06 |
| `items.json` | JSON | item templates: devices, tools, weapons, food classes with nutrition, maps, writing tools |
| `actions.json` | JSON | every verb the player or an NPC can take, with cost, requirements and `moral` where it applies |
| `needs.json` | JSON | need rates by cost class, pack weight, shelter and tape temperature |
| `shop.json` | JSON | pre-departure prices for the three budgets, including charters |
| `maps.json` | JSON | map item instances (official, unofficial, chart, phone) with coverage and errors |
| `weather/tape_<date>.json` | JSON arrays | hourly rows (05), one file per eligible start date |
| `fallout/plume_<sector>_<speed>.u8` | raw uint8 at 250 m | deposition shape |
| `events.json` | JSON | the scripted chain templates and the ordinary templates that trials and chastening mimic |
| `radio.json` | JSON | broadcast schedule keyed to events |
| `animals.json` | JSON | herd records and the encounter table per land-cover class; per-cove fishing table |
| `rules.json` | JSON | every named constant (memory decay, detection ranges, drift, thresholds, ratios, windows) |
| `overrides.json` | JSON | hand overrides keyed by stable id, applied last by the pipeline |
| `scenario/*.json` | JSON | scenario files (05), including mainland segments and rules overrides |
| `styles/*.json` | JSON | palette tokens and marks per view (the existing palettes) |
| `images/*.jpg` | baked hillshade and town images per style, optional | render-only |

GeoJSON is not required: the geometry convention is `Point [x,y]`, `Line [[x,y],...]`, `Polygon [[[x,y],...]]`
inside plain JSON. A converter to GeoJSON in WGS84 exists in the pipeline for GIS checks. 16-bit rasters are
never PNG: Godot's loader and browser decoders reduce 16-bit PNG to 8 bits. An RG8 PNG (high byte, low byte)
is an acceptable alternative for a web build; the raw file is the canonical form.

## Core schemas

```
feature  { id, kind, subtype, tier, name?, geom, elev_m, thr_ne, thr_sw, cove, town, hazard_zone,
           attrs: { ... per kind }, shelter_pf?, construction?, capacity?,
           contents?: { category: qty }, finds?: [ { item, p } ],   # finds roll once on first search
           source: [ ... ], fictional?: true }
node     { id, xy, kind: junction | dead_end | place, feature_id? }
edge     { id, a, b, length_m, grade_pct, surface, class: road | track | trail | path | coast | pier,
           names: [], cells: [cell index ...] }
region   { id, kind: cove | town | watershed | mooring_field, polygon, side?: ne | sw,
           arrival_s_from_shelf?, exposure_factor?, rows?, length_limit_m? }
group, entity, item, aircraft: 06      map_item, belief, view: 04      event: 05
```

Every record has `id`; references are by id, never by index. Ids are stable across rebuilds through the
pipeline's id map (02).

## Sizes (bake output)

| tier | grid | cells | 16-bit | 8-bit | bit mask |
|---|---|---|---|---|---|
| 10 m | 3287 x 2374 | 7.80 M | 15.6 MB | 7.8 MB | 0.98 MB |
| 30 m | 1096 x 792 | 0.87 M | 1.7 MB | 0.9 MB | 0.11 MB |
| 100 m | 329 x 238 | 0.08 M | 0.2 MB | 0.1 MB | 0.01 MB |

Measured: the 10 m water set (two thresholds, two cove ids, the cove map) is 54.6 MB raw and 6.7 MB
gzipped; the 30 m set 6.9 MB raw and 1.1 MB gzipped. Vector sizes: 938 flagged features, about 3,900
building outlines before merging, 1,526 graph edges with 28,891 vertices (441 km), 179 boats, about 40
groups, about 40 infrastructure nodes. The pack on disk, compressed, without town images, is under 40 MB.

Runtime memory: the 30 m rasters in memory (a few MB), the 10 m height and water rasters uploaded as
textures (about 55 MB of texture data, or the water set alone if the heightmap is not drawn), vectors under
10 MB. Under 100 MB in 2D on any target including a browser. 3D adds the 30 m mesh everywhere (0.87 M
vertices) plus 10 m chunks inside a radius of the camera (2 km is about 125 k vertices); the full 10 m grid
is never built as a mesh (review finding 18).

Per-tick cost at 60 s steps: water levels for 18 coves, 40 infrastructure nodes, 40 groups, up to 200
drifting boats; per game hour one fallout resolution into the 250 m dose raster (13 k cells, a sum over
episodes so far). Viewsheds on movement only (31 k cells at 3 km on the 30 m grid). The wet test runs in a
shader or on level-change events. Nothing per frame touches the 10 m grid on the CPU.

## Pipeline steps (Python, in this repo)

1. `scenario/common.py` and `atlas/build.py`: DEM, OSM, inventory with flags (exists).
2. `atlas/sources.py`: outside datasets (exists).
3. `atlas/lariac/`: aerial mosaics and detections (exists).
4. `atlas/bake.py`: per-cove thresholds with the seabed, slope, cost, graph statistics, size budget
   (exists; writes `data/bake/`).
5. To write: `pack/` builder that merges buildings, assigns stable ids, builds the graph with junction
   splitting, draws or loads cove polygons and computes arrival times and exposure factors, derives shelter
   classes, contents and `finds` from use and floor area, writes groups for a date with the behavior table,
   cuts weather tapes with the eligibility rule, bakes plume shapes, writes the mooring-field polygons, applies
   the land-cover modifier to cost, applies overrides, and emits the files above with a manifest and checksums.

## Engine duties

Load the pack; keep the state layer; run the event scheduler and the tick rules in 03, 05 and 06; keep one
knowledge store per observer and run perception; render views from knowledge; keep the logs. No engine code
decides what exists or where: that is the pack.

## Logs, saves, determinism, multiplayer

- Two logs. The shared event log holds every world event under its ordinary template. The hidden per-player
  log holds prayers, intent entries and the providence director's decisions with the ids of the events they
  produced. Both are replay input; only the shared log is ever exported, and in multiplayer neither leaves the
  host.
- A save is the scenario file plus both logs plus a periodic snapshot of state and knowledge for fast resume.
  Replay from the seed reproduces the run, which is the test harness for rules, believers included.
- Randomness comes from one seeded generator per system (events, encounters, drift, director), so adding a
  system never shifts another's rolls.
- Multiplayer (09): host-authoritative. The host runs the simulation and keeps the logs; a client receives
  per tick only state deltas for entities inside its perception window, its own knowledge deltas, and the
  cues from `perceivable` that reach its observer. Saves are host-only.

## Licensing notes to act on at the end (decision 58)

- OSM-derived files (features, graph) carry the ODbL attribution and ship as an open data file.
- County and state layers are public records; the aerial-derived points are our own derived data.
- Animal tables built from observation records: filter to CC0 and CC BY observations before the final
  build; keep all records during development.
- Scripture text: KJV only.
- No raw imagery in the pack; the town images are our hillshade renders.
