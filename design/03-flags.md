# 03. Flags: the booleans and derived values, where they come from, when they change

A flag is never typed in by hand. Each one has a scope, a derivation, a moment when it is computed, and a
belief counterpart (what an observer thinks it is). Three moments exist:

- **baked**: computed by the pipeline from truth; constant for the run.
- **resolved**: computed once when an event fires, then stored in state.
- **live**: computed from state when read; cheap by construction.

## Water and tsunami

| flag | scope | derivation | moment | belief counterpart |
|---|---|---|---|---|
| `threshold_m` | cell | spill level: lowest sea level that wets the cell through a connected path (01) | baked | known where terrain detail is 3; otherwise the observer only has elevation bands |
| `cove` | cell | nearest cove region id | baked | the same (regions are public) |
| `wet` | cell | `threshold_m <= water_level(cove, t)` | live | drawn only where perceived; remembered as last seen |
| `peak_level_m` | cove | max of `water_level` over the pulse | resolved per pulse | heard about, or inferred from debris lines |
| `flood_depth_m` | feature | `max(0, peak_level_m(cove) - ground_elev_m)` with `threshold_m <= peak` | resolved per pulse | unknown until seen; predicted before the event from believed elevation and the official hazard line (decision 22), and the prediction may be wrong |
| `tsunami_affected` | feature | `flood_depth_m > 0` at any pulse | resolved | as above |
| `damage` | building, boat, vehicle | class by depth and construction: wet (< 0.5 m), damaged (0.5 to 2 m or wood over 1 m), destroyed (over 2 m or swept), swept (depth over height or velocity class high) | resolved | last seen condition |
| `hazard_zone` | feature | inside the state tsunami hazard polygon | baked | printed on official maps |
| `debris` | cell | peak wet and near a damaged feature or the shore | resolved after the last pulse | seen |

## Fallout

| flag | scope | derivation | moment | belief counterpart |
|---|---|---|---|---|
| `deposition` | cell per episode | plume x source strength (05) | resolved per tape hour | never seen directly |
| `dose_rate` | cell | sum of episodes with t^-1.2 decay | live | a meter reading if the party has a dosimeter or a radio report; otherwise symptoms |
| `contaminated_air` | region | `dose_rate` above the shelter threshold | live | as above |
| `shelter_pf` | building, vehicle, boat, cave, adit | construction class: wood frame 2 to 3, masonry 5 to 10, basement or earth cover 20 to 50, adit or bunker 100 plus, vehicle 1.5, boat cabin 1.5 | baked from construction and height data, hand overrides allowed | guessed from appearance; verified by staying |
| `water_contaminated` | water source | by type and deposition history: open surface (reservoir, creek, trough) true after the first episode on its catchment; spring true after a lag; well false unless flooded; enclosed tank false unless its lid or vent failed; desal output false while the plant runs on clean intake | live, with a decay term for surface water | unknown until tested (a kit) or inferred from type |
| `food_contaminated` | item, animal, fish | surface exposure during an episode; sea life by cove contamination with a lag | live | inferred from type and time |

## Terrain and movement

| flag | scope | derivation | moment | belief counterpart |
|---|---|---|---|---|
| `cost_class` | cell at 30 m | slope and land cover: easy, moderate, steep, treacherous (slow, fatigue, injury roll), impassable | baked | believed from terrain detail; unknown terrain plans as moderate |
| `passable` | graph edge | not cut by a resolved event (flood, slide, debris) | resolved | last seen |
| `in_view` | cell | viewshed from the observer | live on movement | this is perception itself |

## Infrastructure and resources

| flag | scope | derivation | moment | belief counterpart |
|---|---|---|---|---|
| `up` | node | all dependencies up, not damaged, fuel above zero | live | seen (lights, pump noise) or tested |
| `has_power` | building | its node up | live | seen |
| `water_available` | tap | tank level above zero and pipeline up | live | tested |
| `fuel_available` | pump, tank | level above zero and (power or hand pump) | live | tested |
| `stock` | store | category quantities from floor area, decremented by takes | resolved on takes | a range, blurring with memory |
| `occupied` | shelter | a group or party present | live | seen |

## Knowledge

| flag | scope | derivation | moment |
|---|---|---|---|
| `state` | belief record | unknown, rumored, known, verified (04) | on perception or reading a map |
| `err_m` | belief record | memory decay formula | live |
| `pinned` | belief record | an annotation exists on a held map item | on annotating |
| `seen` | cell | viewshed union | on perception |

## Entities

| flag | scope | derivation | moment |
|---|---|---|---|
| `alive`, `injured`, `sick` | person | needs thresholds and dose | live |
| `desperate` | group | supplies and water below thresholds for days | daily |
| `afloat`, `adrift`, `beached`, `sunk` | boat | wave resolution and drift steps (06) | resolved |
| `electronic_dead` | device, engine | `electronic` and an EMP modifier fired | resolved |
| `secret_tier` | feature | authored, 0 to 3 | baked |
| `fictional` | feature | authored, tier 3 | baked; scenario flag `fiction` hides tier 3 entirely |

## Faith (hidden)

`elect`, `regenerate`, `standing`, `holiness`, trial outcomes: see 07. Never rendered, never in a belief
record, never in multiplayer sync beyond the owning player.

## Rule of thumb

If a value can be recomputed from state in one line, it is live. If it needs the history of an event (a
peak, a deposition episode), it is resolved at the event and stored. If it never changes, it is baked. Every
rendered value goes through a belief record first, except the live perception window.
