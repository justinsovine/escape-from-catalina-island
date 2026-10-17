# 01. Space: frame, tiers, fields, features, graph, regions

Decisions: 1 to 6, 19, 20. Review findings 2, 19, 20, 22 applied (10-review.md). Numbers from `atlas/bake.py`
on 2026-10-17 (150 s for the whole bake).

## Frame

One metric frame for everything: UTM 11N meters with the origin at the south-west corner of the island box
(the atlas grid, 3287 x 2374 cells at 10 m, 193.7 km2 of land). Positions are continuous (decision 5); cells
exist only for fields. Lon/lat is an import format, never a runtime one.

## Tiers

| tier | cell | cells | used for |
|---|---|---|---|
| render | 10 m | 7.80 M | heightmap, thresholds, land mask; textures and meshes; never iterated per frame on the CPU |
| simulation | 30 m | 0.87 M | cost class, seen mask, viewshed, drift, group movement, region ids, threshold min and max |
| field | 250 m | 13 k | fallout deposition and the hourly dose raster |
| town images | 1 m lidar | baked images only | the Avalon and Two Harbors insets |

## Fields (rasters)

| field | tier | type | source |
|---|---|---|---|
| height | 10 m, 30 m | uint16 raw, 0.1 m | USGS 3DEP |
| `thr_ne`, `cove_ne`, `thr_sw`, `cove_sw` | 10 m | uint16 raw (0.1 m, +50 m offset) and uint8 | bake: per-cove spill levels (below) |
| `thr_ne_min`, `thr_ne_max`, `thr_sw_min`, ids | 30 m | same | block min (any part wet) and max (all of it wet) of the 10 m values |
| land | 10 m | bit | OSM coastline |
| slope, cost class | 30 m | uint8 | bake (slope only; the land-cover modifier is a pack-builder step) |
| land cover | 30 m | uint8 | Conservancy vegetation 2000, county land cover 2023 |
| region id (cove, town) | 10 m, 30 m | uint8 | regions.json rasterized (the bake uses a nearest-bay partition of the sea until cove polygons are drawn) |
| seen mask | 30 m | bit, per observer | runtime |
| deposition per episode, dose rate | 250 m | float, runtime, resolved hourly | plume shapes x tape |
| debris | 30 m | bit | resolved after the last wave |

### The water line: one spill level per cell per coast

For a cove's water, a cell's spill level is the lowest level of that water at which the cell is wet through a
connected path from that cove. The pipeline floods from each of 18 coves separately (morphological
reconstruction by erosion with that cove's water as the seed and every other cove's water blocked, 7 s per
cove) and keeps, per cell, the lowest-threshold cove on each coast: `thr_ne, cove_ne` for the north-east
coast that faces the source (Avalon round to West End) and `thr_sw, cove_sw` for the south-west coast (East
End, Pebbly Beach, Silver Canyon round to Catalina Harbor). Then

`wet(cell, t) = thr_ne < water_level(cove_ne, t) or thr_sw < water_level(cove_sw, t)`

with a strict comparison at the datum. Coves on one coast share exposure and so share levels within a
fraction of a meter; the two coasts meet only at the isthmus, and the pair rule covers that from both
directions. The earlier single global raster compared against the cell's own cove failed at cove boundaries
and needed an isthmus special case (review finding 2); a "two lowest pairs" variant failed when a third
cove's water lay nearest (its pairs were both north-coast water at the Isthmus shore, so a Cat Harbor
overtopping was invisible). One pair per coast is the rule that passed every direction:

| test | result |
|---|---|
| every isthmus cove at 10.0 m | the harbors do not join |
| every isthmus cove at 10.5 m | a wet land body touches both harbors (matches the 10.5 m in `scenario/numbers.txt`) |
| north coves 12 m, Cat Harbor 6 m | joined, 56.3 ha wet in the isthmus box |
| north coves 6 m, Cat Harbor 12 m | joined, 54.8 ha |
| north coves 10.5 m, Cat Harbor 0 m, and the reverse | joined both ways |
| lowest path from north-east water to the Cat Harbor shore | 10.3 m |
| lowest path from Cat Harbor water to the Isthmus Cove shore | 10.3 m |
| Isthmus Cove at -2 m (drawdown) | 5.8 ha of seabed exposed |

Seabed: sea cells carry the NOAA 1 m topobathy where it was fetched (the harbors: 98,292 sea cells from five
tiles) and a -30 m default elsewhere, so a level below the datum exposes shallows in the harbors and nothing
offshore. Land cells at or below the datum (1,829 of them, waterfront fill) are dry at rest because the
comparison is strict. Land wet at 5, 10, 20 and 30 m: 0.9, 1.5, 2.7 and 4.0 percent of the island (1.7,
2.9, 5.2 and 7.7 km2).

Encoding: `uint16 = (threshold_m + 50) / 0.1`, little endian, raw files with a JSON sidecar; PNG is not used
for 16-bit products because both Godot's loader and browser decoders reduce 16-bit PNG to 8 bits (review
finding 1). Sizes at 10 m: the four pair rasters plus the cove map are 54.6 MB raw and 6.7 MB gzipped; at
30 m, 6.9 MB raw and 1.1 MB gzipped.

Rendering: the comparison runs in a fragment shader (two threshold textures, two cove-id textures, one
level uniform per cove) or, for a CPU renderer, once per level-change event over the viewport, never per
frame (review finding 18).

## Movement surface

Slope on land: 60.9 percent over 20 degrees, 29.1 over 30, 15.1 over 35, 1.8 over 45. Cost classes at 30 m
(decision 6): easy 12.7 percent of land cells, moderate 36.0, steep 32.4, treacherous 10.5 (slow, fatigue,
injury roll), impassable 8.4 (cliffs). Land cover modifies the class in the pack builder (dense chaparral
slows, bare grass does not). Off-trail travel costs time, calories and water by class and pack weight from
`needs.json`; trails cost by grade only.

## Features (vectors)

| kind | count | geometry |
|---|---|---|
| flagged points of interest | 938 | points |
| buildings | 1,910 OSM, 1,998 county (to merge) | polygons; points beyond town zoom |
| water bodies, woods, land uses, camps | 40 camps and the rest | polygons |
| coastline, streams, power lines, piers | lines | lines |
| boats (2023 county aerial) | 179 | points; the 1,562 buoy dots become mooring-field polygons per cove with row counts |
| mines, bunkers, WWII sites | 30 | points |
| cell sites, hotels | 2 and 23 | points |

Every feature carries `elev_m`, `thr_ne`, `thr_sw`, `cove`, `town`, `hazard_zone`, `tier` at bake time, so
flags in 03 resolve with one lookup.

## Graph

From OSM roads, trails and service roads after splitting at every crossing: 1,526 edges, 1,197 nodes
(833 junctions, 249 dead ends), 441 km, mean edge 289 m, 28,891 vertices. The Conservancy 2017 lines add
names and widths to edges by overlay. Each edge lists the 30 m cells it crosses so events that damage a cell
can cut the edge. Coast edges (walkable beaches) and piers join the same graph.

## Regions

- Coves: 18 named water bodies with a coast side, arrival time from the shelf break and an exposure factor;
  the unit of the water model and of boat and group placement. The bake partitions the sea by nearest bay;
  the pack builder replaces that with drawn polygons.
- Towns (Avalon, Two Harbors, Middle Ranch, airport, the camps as hubs) for group placement and infrastructure.
- Watersheds (the Conservancy's 106 management units) for water contamination catchments.

## Viewshed cost

3 km radius on the 30 m grid: 31 k cells; 5 km: 87 k; 5 km at 60 m: 22 k. Computed on movement, not per
frame.
