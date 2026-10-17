# 01. Space: frame, tiers, fields, features, graph, regions

Decisions: 1 to 6, 19, 20. Numbers from `atlas/bake.py` on 2026-10-17.

## Frame

One metric frame for everything: UTM 11N meters with the origin at the south-west corner of the island box
(the atlas grid, 3287 x 2374 cells at 10 m, 193.7 km2 of land). Positions are continuous (decision 5); cells
exist only for fields. Lon/lat is an import format, never a runtime one.

## Tiers

| tier | cell | cells | used for |
|---|---|---|---|
| render | 10 m | 7.80 M | heightmap, threshold, land mask; textures and meshes; never iterated per frame |
| simulation | 30 m | 0.87 M | cost class, seen mask, viewshed, drift, group movement, region ids |
| field | 250 m | 13 k | fallout deposition and dose |
| town images | 1 m lidar | baked images only | the Avalon and Two Harbors insets |

## Fields (rasters)

| field | tier | type | source |
|---|---|---|---|
| height | 10 m, 30 m | 16-bit, 0.1 m | USGS 3DEP |
| threshold (spill level) | 10 m, 30 m | 16-bit, 0.1 m | bake: morphological reconstruction from the sea |
| land | 10 m | bit | OSM coastline |
| slope, cost class | 30 m | 8-bit | bake |
| land cover | 30 m | 8-bit | Conservancy vegetation 2000, county land cover 2023 |
| region id (cove, town) | 30 m | 8-bit | regions.json rasterized |
| seen mask | 30 m | bit, per observer | runtime |
| deposition per episode, dose rate | 250 m | float, runtime | plume shapes x tape |
| debris | 30 m | bit | resolved after the last wave |

### The threshold raster is the water line

For each cell, the lowest sea level at which the cell is wet through a connected path from the sea. Because a
wet region only grows with the level, one raster answers every level: `wet(cell, L) = threshold(cell) <= L`,
`depth = L - height`. The pipeline computes it in 15 s by priority flood (morphological reconstruction by
erosion with the sea as the seed).

Checks against the earlier flood-fill numbers: the lowest-max-elevation path from Isthmus Cove water to the
Cat Harbor shore crosses at 10.3 m, and a single wet land body touches both harbors at 10.5 m but not at
10.0 m, matching the 10.5 m "the harbors join" figure in `scenario/numbers.txt`. Land wet at 5, 10, 20 and
30 m: 0.9, 1.5, 2.7 and 4.0 percent of the island (1.7, 2.9, 5.2 and 7.7 km2).

Per-cove levels: `L = water_level(cove_of(cell), t)` with the cove from the region raster. Known
approximation: a cell's spill path may run through a neighboring cove's water while its level is taken from
its own cove; adjacent coves get similar levels so the error is small. The one place where it matters is the
isthmus, handled by one rule: when Isthmus Cove's level exceeds the 10.3 m pass, Cat Harbor's side also sees
that level minus a loss term.

## Movement surface

Slope on land: 60.9 percent over 20 degrees, 29.1 over 30, 15.1 over 35, 1.8 over 45. Cost classes at 30 m
(decision 6): easy 12.7 percent of land cells, moderate 36.0, steep 32.4, treacherous 10.5 (slow, fatigue,
injury roll), impassable 8.4 (cliffs). Land cover modifies the class (dense chaparral slows, bare grass does
not). Off-trail travel costs time, calories and water by class and pack weight; trails cost by grade only.

## Features (vectors)

| kind | count | geometry |
|---|---|---|
| flagged points of interest | 938 | points |
| buildings | 1,910 OSM, 1,998 county (to merge) | polygons; points beyond town zoom |
| water bodies, woods, land uses, camps | 40 camps and the rest | polygons |
| coastline, streams, power lines, piers | lines | lines |
| boats and buoys (2023) | 179 and 1,562 | points |
| mines, bunkers, WWII sites | 30 | points |
| cell sites, hotels | 2 and 23 | points |

Every feature carries `elev_m`, `threshold_m`, `cove`, `town`, `hazard_zone`, `tier` at bake time, so flags
in 03 resolve with one lookup.

## Graph

From OSM roads, trails and service roads after splitting at every crossing: 1,526 edges, 1,197 nodes
(833 junctions, 249 dead ends), 441 km, mean edge 289 m, 28,891 vertices. The Conservancy 2017 lines add
names and widths to edges by overlay. Each edge lists the 30 m cells it crosses so events that damage a cell
can cut the edge. Coast edges (walkable beaches) and piers join the same graph.

## Regions

- Coves (about 15 named bays) with arrival time from the shelf break and an exposure factor; the unit of
  the water model and of boat and group placement.
- Towns (Avalon, Two Harbors, Middle Ranch, airport, the camps as hubs) for group placement and infrastructure.
- Watersheds (the Conservancy's 106 management units) for water contamination catchments.

## Viewshed cost

3 km radius on the 30 m grid: 31 k cells; 5 km: 87 k; 5 km at 60 m: 22 k. Computed on movement, not per
frame.
