# 10. Adversarial review: findings and what changed

A fresh reviewer (a separate agent with no part in writing the spec) was asked to attack the draft as a
senior systems engineer and a skeptical designer: contradictions, performance claims, the knowledge model,
the water model, time, people, multiplayer, the providence director, scope, missing pieces. It returned 25
findings. Each is listed with its resolution. "Adopted" means the fix is now in the file named; "adapted"
means a different fix for the same problem; "declined" gives the reason.

## Blocking

| # | finding | resolution |
|---|---|---|
| 1 | 16-bit PNG rasters lose precision in Godot and browser loaders (both decode to 8 bits), so 0.1 m thresholds become 25 m steps | adopted: 16-bit products ship as raw little-endian `uint16` files with a sidecar; PNG only for 8-bit products; `bake.py` writes them that way (08) |
| 2 | one global threshold raster compared against the cell's own cove level is wrong at cove boundaries, and the isthmus rule floods all of Cat Harbor | adapted: `bake.py` now runs the flood from each cove's water separately. The reviewer's "two lowest pairs" failed a reverse test (at the Isthmus shore both pairs were north-coast water, so a Cat Harbor overtopping was invisible); keeping one pair per coast side passed every direction. `wet = thr_ne < level(cove_ne) or thr_sw < level(cove_sw)`; the cove-of-cell approximation and the isthmus rule are gone (01, 05) |
| 3 | the fallout decay ran from deposition time instead of burst time and was singular at deposition | adopted: `dose_rate = sum D_i * max((t - t_blast)/1 h, 1)^-1.2`, `D_i` H+1-referenced, mass fraction for depletion only (05, 03) |
| 4 | a shared event log in multiplayer is the truth of the run, so per-player knowledge is decorative; two transports were described | adopted: host-authoritative deltas only (perception-window state, own knowledge, reaching cues); the log stays on the host; saves are host-only (08, 09) |
| 5 | director events were domain-tagged in the shared log and prayers were unlogged, so saves leak and replay cannot reproduce a believer's run | adopted: a per-player hidden log on the host (prayers, intents, director decisions) as replay input, never exported; director events enter the shared log under the ordinary template with no tag (07, 08) |
| 6 | profession prompts recurred only for the called, which prints election on screen | adopted: opportunities are offered by the world at one visible rate to everyone (each believer NPC once, each Bible once, no post-prayer prompt); hidden state decides only what an answer does (07) |
| 7 | the display predicate read truth and a swept building vanished from belief | adopted: renderers may read truth's baked immutable fields for features with a belief; `exists_in_truth and not removed` dropped; `believed_removed` set only by perception (04) |
| 8 | map-sourced beliefs decayed while the map was still in hand | adopted: resolution order perception > held map record > memory; map records decay only after the map is lost or damaged; pins are the same rule (04) |

## Important

| # | finding | resolution |
|---|---|---|
| 9 | misremembered positions crept along a fixed ray and un-decayed when stress dropped | adopted: `err_m` stored and advanced per tick; bands 0/50/100/200/500/1000 m; offset resampled only on a band change (04) |
| 10 | one hilltop verified every attribute of all of Avalon | adopted: detection ranges per attribute (existence by size class, condition and power at 300 m, contents on entering) (04, 03) |
| 11 | 600 s waits overshot events; wait consent had no timeout; separate survivors had no exchange or spectate rules | adopted: every step is cut at the next `t_fire` and need threshold; consent expires and is implicit for dead or absent players; exchange and spectate defined (05, 04) |
| 12 | blast time was defined two ways and the opening had no boundary | adopted: seeded clock time in a window; arrivals limited to the real schedule before it; pre-blast at 60 s; the opening is flash to last pulse plus 30 minutes at 1 s (05) |
| 13 | groups had no position, no behavior, no tank mapping; individuals persisted forever | adopted: groups stand at a node or feature with a route; a behavior table as data; `serves` on nodes; individuals dematerialize unless party, relationship or ledger (06) |
| 14 | the rescue score paid for people who would have lived anyway and one ferry find dominated it | adopted: score is the delta against the same seed's no-player baseline, only for people the player acted for, with diminishing weight (06) |
| 15 | prayer was a spammable free buff; good works reduced standing | adopted: petition is one window flag, silent while unrepented standing in that domain is above threshold; thanksgiving once per day; positive domains raise holiness only (07) |
| 16 | judgment on the regenerate contradicted the chastening-of-sons framing; `apostate` had no setter | adopted: judgment only for the non-regenerate; for the regenerate the same act is maximal chastening with a standing consequence; `apostate` defined (07) |
| 17 | mid-run weather-tape splicing is detectable; multiplayer means landed on other players | adopted: the tape is chosen once at run start and never spliced; multiplayer means limited to encounter rolls, skill margins and the target's own containers; `attitude[player_id]` on groups and individuals (07, 06) |
| 18 | per-frame work hid in the water comparison, the live dose sum and a full 10 m mesh; the 100 MB claim failed in 3D | adopted: water comparison in a shader or on level-change events; dose resolved hourly into a raster; 3D is the 30 m mesh plus 10 m chunks inside a radius (08, 09, 03) |
| 19 | drawdown could not be represented (no seabed, negatives clipped, cells at 0 wet at rest) and the leading phase was likely the wrong sign | adopted: the seabed from the NOAA 1 m topobathy where fetched (deep default elsewhere) is in the thresholds, encoded with a +50 m offset, strict comparison at the datum; `leading: crest|trough` is a scenario parameter, default crest (01, 05) |

## Minor

| # | finding | resolution |
|---|---|---|
| 20 | undefined derivations: edge belief from sight, velocity class, remembered water, the 30 m threshold as a block mean | adopted: edge belief by cells seen; velocity class from exposure and shore distance; `believed_level_m` per cove; 30 m thresholds stored as block min with the max alongside (03, 04, 01) |
| 21 | tuning constants had no home; six small inconsistencies | adopted: `rules.json` holds every named constant with scenario overrides; the tower 72 h rule now matters only for the local-mode repair; the fiction flag removes tier 3 at load; the census figure is explained (3,715 in the blocks, 3,460 in the city); the 2023 detections and the 2022 count are both named; the slope-only cost raster is labeled as such with land cover as a builder step (03, 04, 06, 01) |
| 22 | 1,562 buoys as belief records | adopted: mooring fields are polygons per cove with row counts; boats are the only entities there (04, 02) |

## Scope

| # | finding | resolution |
|---|---|---|
| 23 | fishing from rasters, species tables and gear factors, plus density fields for five species | adapted: one per-cove table (habitat class, base catch, contamination lag) with gear and daylight factors; herds as entities; other animals as an encounter table per land-cover class. The gear factor stays because the owner asked for fishing "within reason" (06, 02) |
| 24 | infrastructure repair with skills and parts; a vehicle registry | adapted: refuel is the only player action on the graph, plus one comms repair (a tower into local walkie-range mode) because the owner raised it in round 1; vehicles reduced to a hand-placed handful (06) |

## Missing

| # | finding | resolution |
|---|---|---|
| 25 | aircraft, actions, needs rates, finds, shop prices, mainland segments, radio broadcasts, animals had no file | adopted: `aircraft` records on the boat schema with runway and pilot fields and a flight segment; `actions.json`, `needs.json`, `shop.json`, `mainland` segments in the scenario file, `radio.json`, `animals.json`, and `finds: [{item, p}]` on contents rolled on first search (06, 08, 05) |

## What the second bake confirmed

The per-cove representation was re-baked twice after the review (`atlas/bake.py`); the numbers and the test
table are in 01. The isthmus check still reproduces the earlier flood-fill result (join at 10.5 m, not at
10.0 m), overtopping works from either coast, and a level below the datum exposes seabed in the harbors.

## Still open after the review

- Judgment on the non-regenerate (finding 16's reading) is the one theological reading the owner has not
  confirmed.
- The cove partition in `bake.py` is a nearest-bay Voronoi over the sea; the pack builder should replace it
  with drawn cove polygons before exposure factors are tuned.
- The seabed is known at 1 m only where the topobathy tiles were fetched (the harbors); elsewhere a deep
  default stands in, which is fine for drawdown but not for a boat grounding model away from the harbors.
