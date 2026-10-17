# 04. Knowledge, memory, maps and views

Decisions: 12 to 18, 46 to 51. Review findings 7, 8, 9, 10, 20, 22 applied (10-review.md).

Truth is what the pipeline baked and the simulation mutates. Knowledge is what one observer believes. A
renderer reads knowledge plus the live perception window; it may read truth's baked immutable fields (kind,
name, geometry, tier) for any feature whose belief is at least `rumored`, and nothing else of truth. Multiplayer
keeps one knowledge store per player.

## Knowledge store (per observer)

| part | representation | resolution | notes |
|---|---|---|---|
| seen mask | bit raster | 30 m | cells ever inside the observer's perception; never fades (decision 46) |
| terrain detail | integer per region | per map region | contour detail the observer can draw: 0 none, 1 coarse (100 m), 2 (20 m), 3 (DEM); from map items |
| feature beliefs | records keyed by feature id | | see below |
| edge beliefs | state per graph edge | | unknown, rumored, known, verified, plus believed passability |
| water beliefs | `believed_level_m` per cove, as last seen | | drawn against the threshold over seen cells |
| own position | point plus error radius | | 0 with a GPS fix; grows with travel off trail without one; resets at verified landmarks |
| map items | inventory items carrying knowledge | | see below |
| rumors | feature beliefs with large error | | from NPC talk and from past runs (meta-progression, decision 50) |

### Feature belief record

```
{ feature_id, state: unknown|rumored|known|verified,
  pos: [x, y], err_m, err_band, offset_seed, last_seen_t,
  attrs: { kind, name, elev_m?, count?, condition?, ... as believed, each with its own last_seen_t },
  believed_removed: bool,
  sources: [ { kind: sight|map|told|rumor, id?, t } ] }
```

Resolution at render time, per feature: perception (in range now) > a held, readable map item that lists the
feature > memory. A map-sourced record does not decay while that map is held and readable; it starts decaying
from the moment the map is lost, wet or torn. Pins (annotations) are the same rule with the annotation as the
holder.

Memory decay (decision 46), per tick on records in the memory tier: `err_m += k * (1 + s * stress) * dt`,
capped at `err_max`. `err_m` is stored, so a stress change affects only the future. The displayed position is
`truth + offset(offset_seed) * err_band`, where `err_band` quantizes `err_m` into 0, 50, 100, 200, 500 and
1000 m and the offset vector is resampled from the seed only when the band changes: the mark stays put between
band changes while its halo grows, and it does not creep along one ray. Revisiting resets `err_m` to 0 and the
band to 0. Believed attributes blur the same way (a count becomes a range). Mild false memories: past a band
limit, a small chance per day that the believed kind or condition drifts. Constants live in `rules.json`.

### States

- unknown: nothing rendered.
- rumored: a vague mark with a halo of `err_m`; from talk, old maps or past runs.
- known: position and kind from a map or a distant sighting; attributes as the source gave them.
- verified: seen within the detection range of the attribute in question (below); attributes as seen at their
  own `last_seen_t`. A building seen intact before the wave stays intact in belief until seen again;
  `believed_removed` is set only by perception.

## Perception

On every move and every few minutes of waiting: a viewshed from the observer position over the 30 m DEM with a
radius set by daylight, weather and terrain (night cuts it to a few hundred meters; smoke and rain cut it).
Cells in the viewshed join the seen mask.

Detection is per attribute, not per feature: existence and kind at the size-class range (a tank at 2 km, a
cache at 20 m); `damage`, `occupied`, `has_power` within about 300 m (lights at night further); `stock` and
`contents` only on entering. An attribute outside its range keeps the previous belief. Edges: `known` when any
of an edge's cells is seen, `verified` when all of them are within trail range. Sound and smell add rumored
marks with a bearing (surf, generators, gunfire, smoke). Perception is truth: what is in range is drawn crisp at
true positions; everything else is drawn from belief, faded (decision 49).

Cost: a 3 km viewshed at 30 m is about 31 k cells; at 60 m about 8 k. Computed on movement events, not per
frame; visibility from graph nodes can be precomputed.

## Map items

A map is an item whose knowledge the observer can read while holding it. Reading merges its content into the
belief store as `known` records with the map's accuracy, under the map's errors; while held, those records
resolve from the map, not from memory.

```
{ id, title, kind: official|unofficial|phone|chart|hand_drawn,
  coverage: region ids or polygon,
  terrain_detail: 0..3,
  includes: { kinds: [...], tiers: [...] },
  errors: [ { feature_id, kind: omitted|misplaced|wrong_attr|stale, dx?, dy?, attr?, as_of? } ],
  as_of: date, accuracy_m: number,
  annotations: [ { t, type: pin|line|cross|note, geometry, feature_id?, text } ],
  condition: { wet, torn, burnt },
  requires: { device?: phone|gps, power: bool } }
```

Official map (Conservancy style): full coverage, terrain detail 2, roads, trails, camps, named places, water
tanks as symbols, tiers 1 and above omitted. Unofficial map (a hiker's hand-drawn sheet): partial coverage,
terrain detail 1, some tier 1 and 2 secrets, several features misplaced by 100 to 300 m, stale as of a past
year. Phone map: terrain detail 3, official content plus a GPS fix, requires a charged device. Marine chart:
depths, mooring fields, coves, no trails.

Annotations are structured (decision 48): pin a feature at a corrected place, draw a route line, cross out,
note. Annotating needs a writing tool item. Conflicts between sources: the newest verified sighting wins;
between two maps, the higher accuracy wins; a cross-out overrides both.

Mooring fields are polygons per cove with row counts and length limits, not buoy points: a field seen from
the pier is one record, not hundreds.

## Route planning (decisions 15, 47)

The planner builds its graph from edge beliefs: edges `known` or better, plus the edge the party stands on.
Believed passability comes from the last sighting, so a washed-out road still plans until seen. An "explore
along" order follows a physical trail one edge at a time, verifying each edge as it is walked. A plan that
meets truth it did not know stops the party at the obstacle and asks again.

## Secrecy tiers (decision 17)

Every truth feature carries `tier`: 0 public (on official maps), 1 local knowledge (adits, water tanks, fuel
tanks, Camp Cactus), 2 secret (WWII bunkers, radar site, sealed adits, caches), 3 fictional (labeled
`fictional: true`). Tier decides which map items may include a feature. The scenario flag `fiction: false`
removes tier 3 from truth at load, so in that run they never exist; otherwise tier never decides existence.

## Meta-progression (decision 50)

A profile file holds rumors from past runs: feature ids with `err_m` of 500 to 2000 m and a one-line text.
They load as `rumored`. Nothing loads as known.

## Exchange between observers (multiplayer)

Handing over a map item transfers its records with it. "Tell" copies the teller's beliefs for named features
to the listener as `told` with the teller's `err_m` plus a penalty from `rules.json`. Spectating shows a chosen
living player's view, never truth.

## Views

A view is a renderer configuration, not a data source:

```
{ id, source: belief | perception_and_belief,
  projection: top2d | iso_stack | compass | crt | terrain3d,
  layers: set of feature kinds and field names (toggles, like map layers),
  min_state: rumored | known | verified,
  terrain_detail: from the observer unless a device raises it,
  style: token set (the existing palettes) }
```

The three earlier experiments fit as projections: the iso stack draws terrain as elevation bands and marks
bands below the believed water level as submerged; the compass card draws bearings and distances from the
observer to believed features and to the nearest believed-wet cell; the CRT draws a one-bit raster of the same
belief. The 3D terrain draws the heightmap mesh with a water plane per cove at its believed level. All of them
call the same two functions: `visible(feature, observer, view)` and `water_level(cove, t)` (perception) or
`believed_level_m(cove)` (belief).

Display predicate: `belief.state >= view.min_state and not believed_removed and kind in view.layers and tier
allowed by the held map items`. Geometry and name come from truth's baked fields once the state is at least
`rumored`.

Devices gate detail, not views (decision 18): a charged phone with a downloaded map raises terrain detail to 3
and gives a position fix; a paper map gives its own detail; no map gives belief only. A dead battery drops the
phone's contribution without touching what was already learned.
