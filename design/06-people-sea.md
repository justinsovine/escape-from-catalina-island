# 06. People, party, camps, conflict, infrastructure, boats and the sea

Decisions: 26 to 31, 37 to 39, 44, 45, 52 to 57, 68.

## People

Two representations, one identity space.

**Groups** (always simulated, cheap): one record per place and kind.

```
{ id, place: region id, kind: residents | visitors | campers | boaters | staff | crew,
  count: { adults, elders, children, pregnant }, supplies_days, water_days,
  disposition: cooperative | wary | desperate, state: sheltering | moving | fled | dead,
  leader?: npc id, faith_base_rate }
```

Counts come from data: residents from census blocks (3,715 on the island, 192 west of Avalon), visitors
from the month's cross-channel counts and the cruise schedule for the date, campers from the campground
capacities and the season, boaters from moorings times October occupancy. Groups move on the graph at walking
speed, consume supplies, and die by exposure (flood depth at their place, dose over shelter factor, supplies at
zero). Desperation rises with shortfall and falls with aid.

**Individuals** materialize from a group when the observer interacts with it or comes within range; the
group count drops by one and the individual persists:

```
{ id, group_origin, age_band, fitness, skills: [medic|mechanic|boat|fishing|radio|hunting|pilot],
  needs: { hydration, calories, sleep, core_temp, injury, dose, stress },
  disposition, faith fields (07), relationships: { npc id: trust } }
```

Needs (decision 44) are the same record for the player and companions. Pack weight scales speed and fatigue.
Vulnerable people (decision 55) are modifiers only: elders and pregnant people slower with higher needs,
children slower with lower needs, all three raising a group's morale cost when abandoned.

## Party, camps, rescue

- Party: up to 8 individuals under direct orders; others attach as groups that follow or wait.
- Camp: a designated shelter feature plus a group plus supplies plus the safety flags computed from the
  environment (03): `{ feature_id, group_id, supplies, flags: { above_water, shelter_pf, water_access,
  dose_rate } }`. Designation needs no building: it is a state record on an existing feature.
- Rescue score: people delivered to safety (mainland landing in a clean segment or a rescue pickup) plus
  people alive in camps at the end, weighted by vulnerability. A large boat carries many at a fuel cost per
  person-mile, which is the trade the player makes.
- Lives (decision 45): `one_life` ends the run at the player's death; `lead` passes control to a companion.
  Multiplayer is one life each; a dead player spectates or, in lead mode, takes a companion.

## Conflict

Abstract encounters, no tactical map (decision 54). Inputs: group sizes, weapons, disposition, light,
terrain cover class at the cell, surprise (perception first), the player's reputation with that group.
Outcomes: talk, trade, flee, fight with injuries and losses. Weapons are inventory items placed from real
sources: the sheriff station, hunting rifles in the interior, flare guns on boats, tools. Desperation is the
only driver of hostility; it is a group field, so aid changes it.

## Infrastructure graph (decisions 2, 39)

Few dozen nodes, always simulated:

```
node { id, kind: plant | line | substation | pump | tank | desal | well | pipeline | tower | backhaul |
       generator | fuel_store, depends_on: [node ids], state: up | down | damaged, level?: liters or kWh,
       fuel_l?, burn_rate?, feature_id }
```

Rules per tick: `up = all(depends_on up) and not damaged and (fuel > 0 if it burns fuel)`. Tanks drain by the
demand of groups mapped to them and refill while their pump is up. Taps are available while their tank holds
water (gravity feeds keep working after the plant floods). Towers run on batteries for 72 hours after the
grid falls, then go down; the backhaul to the mainland is down from `t_blast`, so phones have no service from
the start but keep GPS and offline maps. Fixing a node is an action with a skill and parts requirement that
sets `damaged = false` or adds fuel.

## Boats and vehicles

Boats are individual entities seeded from the detections and the mooring maps (decision 30):

```
{ id, cove, length_m, class: dinghy | kayak | sail | power | fishing | ferry | yacht,
  fuel_l, fuel_type, burn_l_per_h, speed_kt, range_nm, seaworthiness: 1..4, capacity_persons,
  electronic: bool, state: moored | anchored | adrift | beached | sunk | underway,
  contents: [items], crew_skill_required }
```

Wave resolution: a moored boat in a cove with peak level above its class threshold goes adrift or sinks by a
class-dependent roll; boats at anchor in deep water ride it out. Drift (decision 56): hourly steps at a few
percent of wind speed plus a random walk; a drifting boat that reaches a land cell beaches, with a sink
chance per hour by damage. Towing links two boat entities and halves speed. An adrift or beached boat can be
boarded for fuel, food, a VHF, flares. Vehicles use the same record minus the sea fields; their fuel comes
from the registered tanks and station pumps that need power or a hand pump.

## Sea

- Fishing (decision 57): a near-shore habitat raster (kelp canopy, rocky reef, sand, open water) built from
  the state kelp surveys and the 1 m bathymetry; species tables from state fisheries data by habitat and
  season; expected catch per hour = habitat density x gear factor x time of day x season x skill. Sea
  contamination per cove rises with surface deposition and lags; fish carry it after a delay. Marine
  protected areas appear on official maps as a feature kind with no post-blast effect.
- Swimming: survival time from sea temperature on the tape and distance; a single risk roll per attempt.
- Crossing (decision 38): hourly segments over the channel with sea state from the tape, fuel burn by class,
  night and visibility, drift. Destinations are scenario states: coast segments flagged clean or
  contaminated. Rescue is responsive to signals (VHF range, flares, airfield SOS, mirrors) with a late baseline
  sweep. Satellite messengers work and are rare finds.
- Starting money (decision 68): three budgets spent before departure on kit and on transport (ferry hour, or a
  charter to any cove at a steep price). Money has no use after the flash; what was not spent is paper.
