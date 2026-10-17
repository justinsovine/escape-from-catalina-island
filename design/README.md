# Escape from Catalina: representation spec

How every dataset in this repo becomes game data that any engine can load, with the water line, fallout,
discovery and the hidden mechanics expressed as data and rules rather than as engine code. Nothing here is
engine-specific. The earlier map views (iso stack, compass card, CRT, the Leaflet atlas) are renderers over the
same data.

Decisions referenced by number come from the two Q&A rounds; they are listed in `decisions.md`.

## The four layers

| layer | holds | written by | read by |
|---|---|---|---|
| truth | what the pipeline baked: terrain, threshold raster, features, graph, regions, tapes, plume shapes, templates | the Python pipeline, plus hand overrides | the simulation only |
| state | what the run has changed: levels, flags, positions, entity fields, the event log | events and ticks | the simulation; perception |
| knowledge | what one observer believes: seen mask, feature beliefs with error radii, edge beliefs, map items, rumors | perception and reading | every renderer |
| view | a renderer configuration: projection, layers, minimum belief state, style | the player | the renderer |

One rule makes "hide and show everything" a property of the data instead of a feature list: a renderer never
reads truth. It reads knowledge, plus the live perception window, through one predicate
(`visible(feature, observer, view)`) and one function (`water_level(cove, t)`).

## Files

| file | contents |
|---|---|
| `01-space.md` | coordinate frame, resolution tiers, fields, features, graph, regions, the budget numbers |
| `02-datasets.md` | each dataset as truth, state, knowledge and view |
| `03-flags.md` | every boolean and derived value: scope, derivation, moment, belief counterpart |
| `04-knowledge.md` | knowledge store, memory decay, map items, perception, route planning, views, devices |
| `05-time-events.md` | clock, event interface, the scripted chain, water model, weather tapes, fallout, severity, scenario file |
| `06-people-sea.md` | groups and individuals, party, camps, rescue score, conflict, infrastructure graph, boats, fishing, crossing |
| `07-faith.md` | the providence director |
| `08-datapack.md` | file formats, schemas, sizes, pipeline steps, engine responsibilities, saves, determinism |
| `09-options.md` | open choices with costs and recommendations |
| `10-review.md` | adversarial review findings and what changed because of them |
| `decisions.md` | the Q&A decisions by number |

## Reading order

01 then 03 for the shape of the data; 04 and 05 for how it moves and how it is seen; 06 and 07 for the
systems that sit on top; 08 to build the pack; 09 and 10 for what is still open.

## What the pipeline already proves

`atlas/bake.py` produces the two products the rest depends on: the flood threshold raster (one 16-bit image
that answers "is this cell wet at level L" for every L) and the 30 m cost classes, and it checks the threshold
raster against the earlier flood-fill result for the isthmus. `atlas/build.py`, `atlas/sources.py` and
`atlas/lariac/` produce the feature inventory the pack is built from.
