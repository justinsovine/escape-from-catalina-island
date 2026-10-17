# 04. Knowledge, memory, maps and views

Decisions: 12 to 18, 46 to 51.

Truth is what the pipeline baked and the simulation mutates. Knowledge is what one observer believes. Every
render reads knowledge, never truth, except a dev overlay. Multiplayer keeps one knowledge store per player.

## Knowledge store (per observer)

| part | representation | resolution | notes |
|---|---|---|---|
| seen mask | bit raster | 30 m | cells ever inside the observer's perception; never fades (decision 46) |
| terrain detail | integer per region | per map region | contour interval the observer can draw: 0 none, 1 coarse (100 m), 2 (20 m), 3 (DEM); comes from map items |
| feature beliefs | records keyed by feature id | | see below |
| edge beliefs | state per graph edge | | unknown, rumored, known, verified, plus believed passability |
| own position | point plus error radius | | 0 with a GPS fix; grows with travel off trail without one; resets at verified landmarks |
| map items | inventory items carrying knowledge | | see below |
| rumors | feature beliefs with large error | | from NPC talk and from past runs (meta-progression, decision 50) |

### Feature belief record

```
{ feature_id, state: unknown|rumored|known|verified,
  pos: [x, y], err_m, last_seen_t, pinned: [map_item_id],
  attrs: { elev_m?, count?, condition?, ... as believed },
  sources: [ sight|map|told|rumor ... ] }
```

Memory decay (decision 46): `err_m(t) = min(err_max, err_0 + k * (t - last_seen_t) * (1 + s * stress))`.
Pinned on a map item with a writing tool: `err_m` frozen at that map's accuracy. Revisiting resets. The
displayed position is `truth + offset(seed(feature, observer)) * err_m`, so a misremembered place is stable,
not jittering. Believed attributes blur the same way (a count becomes a range). Mild false memories: with
`err_m` past a limit, a small chance per day that the believed kind or condition drifts (a store remembered as
"had food" when it was looted).

### States

- unknown: nothing rendered.
- rumored: rendered as a vague mark with a halo of `err_m`; from talk, old maps or past runs.
- known: position and kind from a map or a distant sighting; attributes as the source gave them.
- verified: seen within perception range; attributes as seen at `last_seen_t`. Condition is the condition
  last seen: a building seen intact before the wave stays intact in belief until seen again.

## Perception

On every move and every few minutes of waiting: a viewshed from the observer position over the 30 m DEM with a
radius set by daylight, weather and terrain (night cuts it to a few hundred meters; smoke and rain cut it).
Cells in the viewshed join the seen mask. Features inside seen cells become verified if within their detection
range for their size class (a tank at 2 km, a cache at 20 m). Sound and smell add rumored marks with a
bearing (surf, generators, gunfire, smoke). Perception is truth: what is in range is drawn crisp at true
positions; everything else is drawn from belief, faded (decision 49).

Cost: a 3 km viewshed at 30 m is about 31 k cells; at 60 m about 8 k. Compute on movement events, not per
frame; precompute visibility from graph nodes if needed.

## Map items

A map is an item whose knowledge the observer can read while holding it. Reading merges its content into the
belief store as `known` records with the map's accuracy, under the map's errors.

```
{ id, title, kind: official|unofficial|phone|chart|hand_drawn,
  coverage: region ids or polygon,
  terrain_detail: 0..3,
  includes: { kinds: [...], tiers: [...] },      # which feature kinds and secrecy tiers it shows
  errors: [ { feature_id, kind: omitted|misplaced|wrong_attr|stale, dx?, dy?, attr?, as_of? } ],
  as_of: date,
  accuracy_m: number,
  annotations: [ { t, type: pin|line|cross|note, geometry, feature_id?, text } ],
  condition: { wet, torn, burnt },
  requires: { device?: phone|gps, power: bool } }
```

Official map (Conservancy style): full coverage, terrain detail 2, roads, trails, camps, named places, water
tanks shown as symbols, secrecy tier 1 and above omitted. Unofficial map (a hiker's hand-drawn sheet): partial
coverage, terrain detail 1, some tier 1 and 2 secrets included, several features misplaced by 100 to 300 m,
stale as of a past year. Phone map (FarOut style): terrain detail 3, official content plus GPS fix, requires a
charged device. Marine chart: depths, moorings, coves, no trails.

Annotations are structured (decision 48): pin a feature at a corrected place, draw a route line, cross out,
note. A pin freezes the belief error for that feature. Annotating needs a writing tool item.

Conflicts between sources: the newest verified sighting wins; between two maps, the higher accuracy wins; a
cross-out overrides both.

## Route planning (decisions 15, 47)

The planner builds its graph from edge beliefs: edges `known` or better, plus the edge the party stands on.
Believed passability comes from the last sighting, so a washed-out road still plans until seen. An "explore
along" order follows a physical trail one edge at a time, verifying each edge as it is walked. A plan that
meets truth it did not know (a cut edge, a flooded crossing) stops the party at the obstacle and asks again.

## Secrecy tiers (decision 17)

Every truth feature carries `tier`: 0 public (on official maps), 1 local knowledge (adits, water tanks, fuel
tanks, Camp Cactus), 2 secret (WWII bunkers, radar site, sealed adits, caches), 3 fictional (only when the
scenario flag `fiction` is on; always labeled `fictional: true` in the data). Tier decides which map items may
include a feature, never whether it exists.

## Meta-progression (decision 50)

A profile file holds rumors from past runs: feature ids with `err_m` of 500 to 2000 m and a one-line text.
They load as `rumored`. Nothing loads as known.

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
bands below the water level as submerged; the compass card draws bearings and distances from the observer to
believed features and to the nearest wet cell; the CRT draws a one-bit raster of the same belief. The 3D
terrain draws the heightmap mesh with a water plane per cove at its current level. All of them call the same
two functions: `visible(feature, observer, view)` and `water_level(cove, t)`.

Display predicate: `exists_in_truth and not removed and belief.state >= view.min_state and kind in
view.layers and tier allowed by the current map items`.

Devices gate detail, not views (decision 18): a charged phone with a downloaded map raises terrain detail to 3
and gives a position fix; a paper map gives its own detail; no map gives belief only. A dead battery drops the
phone's contribution without touching what was already learned.
