# 05. Time, events, the scripted chain, weather and the severity knob

Decisions: 8 to 11, 34, 35, 40 to 43, 67 to 69.

## Clock

- `t`: integer seconds since arrival. The scenario seed fixes the calendar date (October or November, Santa
  Ana season) and the arrival hour (ferry or charter choice, decision 43).
- Cadence by phase (decision 41): opening at 1 s steps, real time, pausable in single player; normal play at
  60 s steps; `wait` orders advance in 600 s steps until an interrupt (event, need threshold, arrival, dawn).
  Multiplayer: no pause; waiting advances at the slowest player's consent.
- Everything scheduled is an event with a fire time; nothing polls.

## Event interface

```
{ id, t_fire, kind, scope: global | region id | cove id | entity id,
  params, preconditions: [state predicates],
  effects: [ state operations ],
  perceivable: { cells | regions | entities, cue: flash|sound|shake|sight|radio },
  log: true }
```

Effects are state operations on the state layer (set a field, set a flag, change a level, move an entity,
spawn, remove). Knowledge is never written by an event directly; observers learn through perception of the
cue or of the changed state. Every event appends to the run log, which is also the save format (08).

## The scripted chain (decisions 34, 35, 67)

| step | time | what the data does | what the player can perceive |
|---|---|---|---|
| flash | `t_blast`, seeded, unknown to the player, in the first afternoon or evening | nothing on the island | sky flash from anywhere; a glow toward the mainland |
| sound | plus about 2 minutes | nothing | a report, distance-dependent |
| quake | plus a seeded 2 to 40 minutes | the stressed Palos Verdes fault slips; this is the slide trigger with the best real precedent (shaking triggering submarine slides: Grand Banks 1929, Papua New Guinea 1998, Palu 2018) | felt island-wide; this is the real warning |
| slide | quake plus 0 to 3 minutes | slide volume = severity (69) | nothing until the water moves |
| drawdown | slide plus travel time per cove minus a few minutes | `water_level(cove)` dips below 0 | the harbor empties, boats ground |
| waves | slide plus travel time per cove (baked table: 8 to 9 minutes from the shelf break to Two Harbors, 15 from the port) | 2 to 3 pulses, decreasing, 15 to 25 minutes apart; `water_level(cove, t)` follows each pulse: rise over about 3 minutes, fall over about 10 | the water line moves; flags resolve at each peak (03) |
| aftermath | after the last pulse | residual debris raster; drifting boats start; infrastructure graph re-evaluates (plant flooded) | |
| fallout | hours, from the weather tape | deposition episodes whenever the tape blows from the source sector | sky, dust, sick animals, radio |
| rescue | day 10 to 21 baseline, earlier on signals | sweep event visits coves; signals create pickup events | aircraft, boats, radio |

The blast is a single surface burst at the port (35): fallout and ground shock, no island EMP. The direct
explosion wave is not the tsunami; the slide is.

## Water model

`water_level(cove, t) = max(0, sum over pulses of pulse(t - t_arrival_cove,k) * H_cove,k) + drawdown term`.
`H_cove,1 = severity * factor(cove)` with factors from cove exposure and shape (Cat Harbor halved, per the
earlier run-up assumption; Avalon and the Isthmus full), later pulses scaled 0.7 and 0.5. Cells are wet when
`threshold(cell) <= water_level(cove_of(cell), t)` (01). The threshold raster is baked; the engine does one
comparison per cell it draws or simulates. Peak levels per cove are recorded in state so that flags and damage
are resolved once per pulse, not per frame.

## Weather tape (decisions 10, 42)

Real hourly records replayed from a seeded real start date: airport station (wind direction and speed,
temperature, sky, rain) and buoy 46025 (wave height, period, water temperature). Eligible start dates are
those where days 1 to 10 contain at least one offshore episode (wind from the source sector, 10 knots or
more, 6 hours or more), so fallout always arrives but never the same way. The tape is read-only data; the
engine indexes it by hour. The providence director may choose among eligible tapes in single player (07).

Tape row: `{ hour, wind_dir, wind_kt, gust_kt, temp_c, sky, rain_mm, swell_m, swell_s, sea_temp_c, tide_m }`.

## Fallout

Baked plume shapes per wind sector and speed class (02). Each tape hour with wind from the source sector
within the plume's angular width adds a deposition episode: `D_i(cell) = plume(sector, speed)(cell) *
source_strength(t_i)`, where source strength decays as the cloud depletes. Dose rate per cell:
`sum_i D_i(cell) * ((t - t_i) / 1 h) ^ -1.2` (the 7:10 rule). Dose to a person is dose rate over the shelter
protection factor. Contamination flags for water sources follow source type (03).

## Severity knob (decision 69)

One scenario number, slide volume class 1 to 3, mapped to `severity` in meters at the source. Yield is fixed
(strategic class, surface burst). The tape selection already guarantees fallout.

## Scenario file

```
{ seed, date, start: { place: two_harbors | avalon | charter{x,y}, hour, budget: 1|2|3, kit },
  blast: { site: port_of_la, burst: surface, t_offset_range_s },
  quake: { delay_range_s, magnitude },
  slide: { severity_class },
  modifiers: { hemp: none | precursor | second_strike{day}, fiction: bool },
  mode: { lives: one_life | lead, players: 1..4 } }
```

EMP permutations are parked (35): none (base); a high-altitude precursor at `t_blast` (electronics dead from
the start, paper-map game); a second strike on a later day (mid-run loss of phones, GPS receivers, modern
outboards; mechanical diesels keep running). The data pack needs only one field for it: every device and
engine carries `electronic: bool`.
