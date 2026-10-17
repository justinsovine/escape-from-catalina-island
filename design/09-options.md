# 09. Open options with costs

Things decided "make options and weigh" or "use judgement with adversarial review". Each has a recommendation;
10-review.md records the attack on it.

## Simulation scope (decision 2)

| option | what runs every tick | cost | what it buys |
|---|---|---|---|
| A. whole island, coarse | all groups (about 40), infrastructure graph (about 40 nodes), all boats (about 200 drifting after the wave), water levels per cove (15), fallout fields at 250 m, weather tape | under 1 ms of logic per 60 s step on any engine; memory in the low MB | off-map systems behave: tanks drain, towers die, Avalon's groups flee and die, boats drift to where you later find them |
| B. local bubble | only entities within a radius of the party; the rest frozen and reconciled on arrival by closed-form catch-up (tank level = f(time), group state = f(time)) | less logic, more code: every system needs a catch-up function | nothing the player can perceive, since A is already cheap |
| A plus B for individuals | A for aggregates; individuals exist only near the party (06) | A's cost plus a few dozen individuals | the only thing that is expensive is individuals, and they are already local |

Recommendation: A plus B for individuals. Showing the player the whole island is a knowledge question, not a
simulation one (04); the sim can run everywhere while the map shows only belief.

## Multiplayer shape (decision 52, judgement with review)

| shape | knowledge | time | what it adds | what it costs |
|---|---|---|---|---|
| co-op party, one leader | shared store | shared | nothing the solo game lacks | loses the unreliable narrator: one player's sighting corrects everyone |
| separate survivors, same island, 2 to 4 | per player | shared, no pause, waits by consent | meeting by chance or radio, trading maps and rumors, towing each other, splitting the rescue score; faith per player | a server or lockstep; the opening is real time for everyone; a dead player waits |
| asynchronous shared world | per player | each plays in turn | fits a web build | breaks the real-time opening and weather tape sharing |

Recommendation: design for separate survivors and build solo first. The data model keeps knowledge and
faith per observer and the sim is deterministic from the seed and the logs. Transport is host-authoritative:
the host runs the simulation and keeps the shared and hidden logs; a client receives per tick only state
deltas for entities inside its perception window, its own knowledge deltas, and the cues from `perceivable`
that reach its observer. The shared log never goes to a client, so the unreliable narrator survives a file
browser. Lockstep across engines is not worth the float determinism fight. What makes the shape true is in 04
(exchange, spectate) and 05 (consent expiry). Do not promise it until the solo loop is fun.

## Death (decision 45)

`one_life` for solo by default, `lead` as an option, one life each in multiplayer with spectate or take-over
in lead mode. Cost: none in the data; one rule flag.

## Fallout plume: baked or runtime (decision 23)

Baked: 16 sectors x 3 speed classes = 48 small rasters at 250 m (about 13 k cells each, under 1 MB total)
and one hourly resolution into the dose raster. Runtime: a Gaussian plume per episode, a few hundred
operations per cell per episode, still cheap at 250 m. Recommendation: bake, keep the runtime formula as the
generator so a mod can change it; both produce the same deposition field schema.

## EMP timing (decision 35)

None in the base scenario. Options parked as a scenario modifier: precursor (paper-map game from the start) or
second strike on day N (mid-run loss of electronics and modern engines). Data cost: one `electronic` flag on
devices and engines, already in the schema.

## Terrain in 3D (decision 4)

The heightmap and the threshold pairs serve both 2D and 3D. 3D adds a mesh: the 30 m grid everywhere
(0.87 M vertices) plus 10 m chunks inside a stated radius of the camera (2 km is about 125 k vertices), and a
water plane per cove. The full 10 m grid as a mesh would be 7.8 M vertices and is never built. Nothing changes
in the data pack.

## Deferred, with a place in the data

- Fire: a fuel class raster from the vegetation map and a spread rule; the cost raster already has the
  land-cover channel. Not in the first scenario.
- Tides: on the weather tape as a column; no effect until the water model adds it to the base level.
- Live weather: replaced by tapes (decision 42); a tape generator from a live feed would plug into the same
  format if ever wanted.
- Fiction tier: in the schema as `tier 3`, off by default, labeled.
