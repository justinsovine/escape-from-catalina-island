# 06. People, party, camps, conflict, infrastructure, boats, aircraft and the sea

Decisions: 26 to 31, 37 to 39, 44, 45, 52 to 57, 68. Review findings 13, 14, 17, 23, 24, 25 applied
(10-review.md).

## People

Two representations, one identity space.

**Groups** (always simulated, cheap): one record per place and kind.

```
{ id, at: node_id | feature_id, route: [node ids], kind: residents | visitors | campers | boaters | staff | crew,
  count: { adults, elders, children, pregnant }, supplies_days, water_days,
  disposition: cooperative | wary | desperate, attitude: { player_id: delta },
  state: sheltering | moving | fled | dead, leader?: npc id, faith_base_rate }
```

Counts come from data: residents from the 2020 census blocks (3,715 in the island's blocks: 3,460 in the
city of Avalon, the rest in the interior, Two Harbors and the coves), visitors from the month's cross-channel
counts and the cruise schedule for the date, campers from campground capacities and the season, boaters from
mooring counts times October occupancy. A group stands at a graph node or a feature, so it has one elevation,
one threshold and one cove; it moves on the graph at walking speed along `route`.

Behavior is a data table (`groups.json` carries the defaults), not engine code:

| trigger | response |
|---|---|
| quake felt | evacuate to the nearest node above the believed-safe elevation after a delay drawn per group |
| dose over the shelter threshold at `at` | shelter in the nearest building with the best protection factor |
| `water_days` at 0 | move to the nearest known water source; desperation rises |
| `supplies_days` at 0 | desperation rises; a desperate group raids the nearest stocked feature |
| a player's camp within reach and cooperative | join or trade |

Groups die by exposure (flood depth at `at`, dose over shelter factor, supplies at zero for days).

**Individuals** materialize from a group when the observer interacts with it or comes within range; the
group count drops by one. An individual dematerializes back into its group (count plus one, state carried
as a summary) when out of range, unless it is in the party or referenced by a relationship or a ledger
entry. Individual record:

```
{ id, group_origin, age_band, fitness, skills: [medic|mechanic|boat|fishing|radio|hunting|pilot],
  needs: { hydration, calories, sleep, core_temp, injury, dose, stress },
  disposition, attitude: { player_id: delta }, faith fields (07), relationships: { npc id: trust } }
```

Needs (decision 44) are the same record for the player and companions; `needs.json` holds the rates
(hydration and calories per hour by cost class and pack weight, core temperature from the tape and shelter,
sleep debt) and food classes carry nutrition fields. Pack weight scales speed and fatigue. Vulnerable people
(decision 55) are modifiers only: elders and pregnant people slower with higher needs, children slower with
lower needs, all three raising a group's morale cost when abandoned.

## Party, camps, rescue

- Party: up to 8 individuals under direct orders; others attach as groups that follow or wait.
- Camp: a designated shelter feature plus a group plus supplies plus the safety flags computed from the
  environment (03): `{ feature_id, group_id, supplies, flags: { above_water, shelter_pf, water_access,
  dose_rate } }`. Designation needs no building: it is a state record on an existing feature.
- Rescue score: the delta against the same seed's no-player baseline (the deterministic sim run at scenario
  creation without a player, a few seconds at 60 s steps), counting only people the player moved, sheltered,
  fed or signaled for, with diminishing weight beyond party scale and a vulnerability weight. Designating a
  building Avalon would have used anyway scores nothing; a found ferry hull full of people scores its delta,
  diminished.
- Lives (decision 45): `one_life` ends the run at the player's death; `lead` passes control to a companion.
  Multiplayer is one life each; a dead player spectates (a living player's view) or, in lead mode, takes a
  companion.

## Conflict

Abstract encounters, no tactical map (decision 54). Inputs: group sizes, weapons, disposition and the
group's attitude toward this player, light, terrain cover class at the cell, surprise (perception first).
Outcomes: talk, trade, flee, fight with injuries and losses. Weapons are inventory items placed from real
sources: the sheriff station, hunting rifles in the interior, flare guns on boats, tools. Desperation is the
driver of hostility; it is a group field, so aid changes it.

## Infrastructure graph (decisions 2, 39)

Few dozen nodes, always simulated:

```
node { id, kind: plant | line | substation | pump | tank | desal | well | pipeline | tower | backhaul |
       generator | fuel_store, depends_on: [node ids], serves: [group ids, feature ids],
       state: up | down | damaged, level?: liters or kWh, fuel_l?, burn_rate?, battery_h?, feature_id }
```

Rules per tick: `up = all(depends_on up) and not damaged and (fuel > 0 if it burns fuel)`. Tanks drain by the
demand of the groups in `serves` and refill while their pump is up. Taps are available while their tank holds
water (gravity feeds keep working after the plant floods). The backhaul to the mainland is down from
`t_blast`, so phones have no service from the start but keep GPS and offline maps; tower batteries matter only
if a radio-skilled character puts a tower into local mode (a walkie-range mesh), the one repair the game
allows on comms. The only other player action on the graph is refueling a generator (decision 7: not a
building game, not a utility game).

## Boats, vehicles, aircraft

Boats are individual entities seeded from the detections and the mooring maps (decision 30):

```
{ id, cove, length_m, class: dinghy | kayak | sail | power | fishing | ferry | yacht,
  fuel_l, fuel_type, burn_l_per_h, speed_kt, range_nm, seaworthiness: 1..4, capacity_persons,
  electronic: bool, state: moored | anchored | adrift | beached | sunk | underway,
  contents: [items], finds: [{item, p}], crew_skill_required }
```

Wave resolution: a moored boat in a cove with peak level above its class threshold goes adrift or sinks by a
class-dependent roll; boats at anchor in deep water ride it out. Drift (decision 56): hourly steps at a few
percent of wind speed plus a random walk; a drifting boat that reaches a land cell beaches, with a sink
chance per hour by damage. Towing links two boat entities and halves speed. An adrift or beached boat can be
boarded for fuel, food, a VHF, flares.

Vehicles: a handful of hand-placed trucks and carts at the two towns, Middle Ranch and the airport, same
record minus the sea fields; fuel from the registered tanks and station pumps that need power or a hand pump.
No registry-scale fleet.

Aircraft (decision 30): the same record plus `needs_runway: bool`, `water_landing: bool`, `range_nm`,
`pilot_required: true`. Seeded from the airport's 6 to 10 based aircraft (no fuel sold there, so fuel is what
is in the tanks) and the helicopter pad at Pebbly Beach. A flight segment needs a pilot skill in the party, a
runway state (debris, daylight) and fuel for the crossing with reserve; it resolves like a crossing segment
with its own risk table.

## Sea

- Fishing (decision 57, simplified after review): one per-cove table `{ habitat_class: kelp | reef | sand |
  open, base_catch_per_hour, contamination_lag_h }` from the state kelp surveys and the harbor bathymetry,
  gear factors (hand line, rod, spear, trap) and a daylight factor; no habitat raster, no moving schools. Sea
  contamination per cove rises with surface deposition and lags; fish carry it after the lag. Marine protected
  areas appear on official maps as a feature kind with no post-blast effect.
- Land animals: bison and deer as herd entities with a count and a range polygon (Conservancy counts);
  non-herd animals (fox, eagle, rattlesnake, sea lion, seal) as an encounter table per land-cover class in
  `animals.json`, not as entities or density rasters.
- Swimming: survival time from sea temperature on the tape and distance; a single risk roll per attempt.
- Crossing (decision 38): hourly segments over the channel with sea state from the tape, fuel burn by class,
  night and visibility, drift. Destinations are the scenario's `mainland.segments` (clean, contaminated,
  unknown). Rescue is responsive to signals (VHF range, flares, airfield SOS, mirrors) with a late baseline
  sweep. Satellite messengers work and are rare finds.
- Radio: `radio.json` is a scripted broadcast schedule keyed to events (emergency alerts, weather radio,
  Coast Guard traffic, dose reports) that any working receiver in range hears; it is how forecasts and
  mainland states reach knowledge.
- Starting money (decision 68): three budgets spent before departure on kit and on transport (ferry hour, or a
  charter to any cove at a steep price) from `shop.json`. Money has no use after the flash.
