# 05. Time, events, the scripted chain, weather and the severity knob

Decisions: 8 to 11, 34, 35, 40 to 43, 67 to 69. Review findings 3, 11, 12, 17, 19 applied (10-review.md).

## Clock

- `t`: integer seconds since arrival. The scenario seed fixes the calendar date (October or November, Santa
  Ana season) and the arrival hour from the real ferry schedule or a charter (decision 43).
- The blast fires at a seeded clock time inside a stated window (decision 67: fixed per seed, unknown to the
  player); arrival choices are limited to the real schedule before that window, so no choice moves the blast
  and no arrival lands at sea at the flash.
- Cadence: pre-blast at 60 s steps with waits allowed; the opening, from the flash to the last pulse plus 30
  minutes, at 1 s steps in real time, pausable in single player; then 60 s steps; `wait` orders advance in
  600 s steps. Every step, of any size, is cut at the next scheduled `t_fire` and at the next need threshold,
  so a wait never overshoots an event.
- Multiplayer: no pause; waits advance at the slowest player's consent, consent expires after N real seconds
  (`rules.json`) and is implicit for dead, disconnected or spectating players.
- Everything scheduled is an event with a fire time; nothing polls.

## Event interface

```
{ id, t_fire, kind, template, scope: global | region id | cove id | entity id,
  params, preconditions: [state predicates],
  effects: [ state operations ],
  perceivable: { cells | regions | entities, cue: flash|sound|shake|sight|radio },
  log: shared | hidden }
```

Effects are state operations on the state layer. Knowledge is never written by an event directly; observers
learn through perception of the cue or of the changed state. Shared-log events append to the run log (08);
director decisions go to the hidden per-player log and the events they produce appear in the shared log under
the ordinary template (07).

## The scripted chain (decisions 34, 35, 67)

| step | time | what the data does | what the player can perceive |
|---|---|---|---|
| flash | `t_blast`, seeded in a window in the first afternoon or evening | nothing on the island | sky flash from anywhere; a glow toward the mainland |
| sound | plus about 2 minutes | nothing | a report, distance-dependent |
| quake | plus a seeded 2 to 40 minutes | the stressed Palos Verdes fault slips; the slide trigger | felt island-wide; this is the reliable warning |
| slide | quake plus 0 to 3 minutes | slide volume = severity (69) | nothing until the water moves |
| waves | slide plus travel time per cove (baked: 8 to 9 minutes from the shelf break to Two Harbors, 15 from the port) | 2 to 3 pulses, decreasing, 15 to 25 minutes apart; `leading: crest|trough` is a scenario parameter, default crest for this source (the island sits downslope of the slide); troughs between pulses are the drawdowns | the water line moves; flags resolve at each peak (03) |
| aftermath | after the last pulse | residual debris raster; drifting boats start; infrastructure graph re-evaluates (plant flooded) | |
| fallout | hours, from the weather tape | deposition episodes whenever the tape blows from the source sector | sky, dust, sick animals, radio |
| rescue | day 10 to 21 baseline, earlier on signals | sweep event visits coves; signals create pickup events | aircraft, boats, radio |

Precedent for the trigger, for the record: a 1.1 Mt underground test (Benham, 1968) moved mapped faults and
set off a sequence of small earthquakes within about 13 km, attributed to release of natural tectonic strain
(Hamilton, McKeown and Healy, Science 166, 1969); natural shaking has triggered submarine slides and their
tsunamis within minutes (Grand Banks 1929, Papua New Guinea 1998, Palu 2018). A surface burst couples far
less energy into the ground than an underground one, so the stressed-fault step is the premise's one
hand-wave, and it is the only one.

The blast is a single surface burst at the port (35): fallout and ground shock, no island EMP. The direct
explosion wave is not the tsunami; the slide is.

## Water model

`water_level(cove, t) = sum over pulses of pulse_k(t - t_arrival(cove, k)) * H(cove, k)`, signed: a pulse is
a crest followed by a trough (or the reverse when `leading = trough`), rise over about 3 minutes, fall over
about 10, with the trough depth a fraction of the crest. `H(cove, 1) = severity * factor(cove)` with factors
from cove exposure and shape (Cat Harbor halved, per the earlier run-up assumption; Avalon and the Isthmus
full), later pulses scaled 0.7 and 0.5. Cells are wet by the coast-pair rule in 01:
`thr_ne < level(cove_ne) or thr_sw < level(cove_sw)`, strict at the datum, so a level below zero exposes the seabed
the thresholds carry. Peak and trough levels per cove per pulse are recorded in state; flags and damage
resolve once per pulse, not per frame.

## Weather tape (decisions 10, 42)

Real hourly records replayed from a seeded real start date: airport station (wind direction and speed,
temperature, sky, rain) and buoy 46025 (wave height, period, water temperature). Eligible start dates are
those where days 1 to 10 contain at least one offshore episode (wind from the source sector, 10 knots or
more, 6 hours or more). The tape is chosen once at run start and never spliced; the providence director may
choose among eligible tapes in single player only (07).

Tape row: `{ hour, wind_dir, wind_kt, gust_kt, temp_c, sky, rain_mm, swell_m, swell_s, sea_temp_c, tide_m }`.

## Fallout

Baked plume shapes per wind sector and speed class (02). Each tape hour with wind from the source sector
within the plume's angular width adds a deposition episode `i` at time `t_i` with
`D_i(cell) = plume(sector, speed)(cell) * mass_fraction(t_i)`, where `mass_fraction` is the share of the
cloud still airborne (depletion only, not activity) and `D_i` is expressed as the H+1-referenced dose rate
that deposit would give. Dose rate at a cell:

`dose_rate(cell, t) = sum over episodes with t_i <= t of D_i(cell) * max((t - t_blast) / 1 h, 1) ^ -1.2`

Decay runs from the burst, not from deposition (the 7:10 rule), so late-arriving fallout is already cooler
and nothing is singular. The sum is resolved once per game hour into a 250 m raster; entities read their cell
from that raster (03). Dose to a person is dose rate over the shelter protection factor. Contamination flags
for water sources follow source type (03).

## Severity knob (decision 69)

One scenario number, slide volume class 1 to 3, mapped to `severity` in meters at the source. Yield is fixed
(strategic class, surface burst). The tape selection already guarantees fallout.

## Scenario file

```
{ seed, date, start: { place: two_harbors | avalon | charter{x,y}, hour, budget: 1|2|3, kit },
  blast: { site: port_of_la, burst: surface, window: [clock_s, clock_s] },
  quake: { delay_range_s, magnitude },
  slide: { severity_class, leading: crest | trough },
  mainland: { segments: [ { id, state: clean | contaminated | unknown } ] },
  modifiers: { hemp: none | precursor | second_strike{day}, fiction: bool },
  mode: { lives: one_life | lead, players: 1..4 },
  rules_overrides: { ... any constant from rules.json } }
```

EMP permutations are parked (35): none (base); a high-altitude precursor at `t_blast` (electronics dead from
the start, paper-map game); a second strike on a later day (mid-run loss of phones, GPS receivers, modern
outboards; mechanical diesels keep running). The data pack needs only one field for it: every device and
engine carries `electronic: bool`.
