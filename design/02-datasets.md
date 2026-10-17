# 02. Each dataset: truth, state, knowledge, view

Columns: what the pipeline bakes from the sources already in the repo (truth), what the simulation may change
(state), how an observer learns it (knowledge), and how views draw it. Numbers are from the atlas build and
the bake step (01 has the budget).

| dataset | truth (baked) | state (mutable) | knowledge | view hints |
|---|---|---|---|---|
| terrain | 10 m heightmap (16-bit raw), 30 m block mean, slope and `cost_class` at 30 m, land mask, coastline polylines, cove regions, watershed regions | none (mountains do not change) | seen mask by viewshed; contour detail from map items | iso stack: elevation bands; 3D: mesh chunks; top 2D: hillshade baked as an image per style |
| water line | per-cove spill levels, one (cove, threshold) pair per coast side per cell at 10 m and 30 m (block min and max), seabed in the sea cells, per-cove arrival times from the shelf break, cove exposure factors | `water_level(cove, t)`, peak and trough per pulse, debris raster | wet cells perceived in view; `believed_level_m` per cove; peaks inferred later from debris lines and damage | the coast-pair comparison in a shader (threshold and cove textures, a level uniform per cove); CPU renderers rebuild the viewport mask on level-change events; plates below level submerged; water plane per cove in 3D |
| buildings | merged outlines (OSM 1,910 and county 1,998 with heights), ground elevation, `threshold_m` at centroid, use, floor area, rooms, construction class (assessor year and use, hand overrides), `shelter_pf`, contents categories by use | `damage`, `has_power`, `occupied`, contents taken | verified on sight within range; condition as last seen | polygons at town zoom, points beyond; damage and power as marks |
| roads and trails | graph: nodes at junctions and dead ends, edges with length, grade, surface, width, names (Conservancy 2017 names and widths, OSM, the Trans-Catalina Trail); edges reference the 30 m cells they cross | `passable`, cut reasons | edge beliefs; planner uses known edges only; walking verifies | lines by class; unknown edges absent; believed-but-cut edges drawn until seen |
| points of interest | 938 flagged features: food, stores, fuel, medical, emergency, water, camps, lodging, transport, infrastructure, shelter, civic, offices, sanitation, viewpoints, places, historic; each with `elev_m`, `threshold_m`, hazard flag, town, tier | `stock`, `damage`, `occupied` | belief records; map items reveal by kind and tier | icons by kind; halo by `err_m` |
| water sources | 85 sources typed: creek, spring, reservoir, trough, well, tank, desal, tap; the water system facilities list (10 wells, 15 tanks, 2 desal, 2 reservoirs) with capacities where published | level, `water_contaminated`, `water_available` | type is visible; contamination needs a test kit or inference | drop icon with a contamination mark once believed |
| fuel | registered tanks with gallons (Avalon fuel dock, Pebbly Beach station), boat and vehicle tanks as entity fields, the plant's propane and diesel stores | level, `fuel_available` | tested | icon with level once believed |
| infrastructure | graph of about 40 nodes: plant, substation, lines by town, pumps, tanks, desal, wells, pipelines, towers, backhaul, generators | `up`, `damaged`, `fuel_l`, `level` | seen indirectly (lights, noise) or tested | a system view with node states, from belief |
| campsites | 40 camps with amenities (water, toilets, shade, lockers, fire rings), capacity, `elev_m`, `threshold_m`, hazard flag | `occupied`, supplies left by groups | official maps show them | tent icon; flags as marks |
| mines, bunkers, shelters | 30 points: mines, adits, quarries, WWII sites, the promontory structure; each with `tier`, `shelter_pf`, access (open, sealed, flooded), capacity | access changed by actions, `occupied` | tier 1 and 2 only from unofficial maps, rumors, or sight | hidden until known |
| people | groups per place from census blocks, visitor counts by month, cruise days, campground capacity, mooring occupancy | counts, supplies, disposition, state, individuals | groups known where seen or told; individuals once met | group marks with believed size |
| animals | herds: bison (Conservancy count), deer, as entities with a range; non-herd animals as an encounter table per land-cover class (`animals.json`); the sightings inform the tables, no density rasters ship | herd positions, counts, contamination | seen; hunted | marks when in view |
| sea life | one per-cove table: habitat class, base catch per hour, contamination lag | contamination level | caught | none beyond catch results |
| boats, vehicles, aircraft | boats from the 2023 county-aerial detections and the mooring rows (about 180 hulls at three coves plus mooring counts for the rest), mooring fields as polygons per cove (not buoy points), ferries by schedule, a hand-placed handful of vehicles, the airport's based aircraft | `state`, position, fuel, contents, damage | seen; boarded | hull marks by class |
| devices and comms | item templates: paper maps (official, unofficial, chart), phone, GPS unit, satellite messenger, VHF, walkie, station radio, weather radio, dosimeter, test kit, writing tools; each with layers, accuracy, power, range, `electronic` | charge, damage, held by | the holder knows what it shows | gates detail (04) |
| weather | hourly tapes from real records with the eligibility rule (05) | current hour index | the sky; forecasts from a working radio | sky and wind marks |
| fallout | plume shapes per sector and speed class at 250 m; airborne mass fraction curve | deposition episodes; the hourly `dose_rate` raster | dosimeter, radio, symptoms | never drawn as truth; drawn as belief from readings |
| maps as items | map item records (04) with coverage, detail, includes, errors, `as_of` | annotations, condition | they are knowledge | the map screen is the belief store filtered by the held map |
| scenario | seed, date, start, severity, leading phase, mainland segments, modifiers (05) | event log | the player knows only what they chose | none |
| actions, needs, shop, radio | `actions.json` (every verb with its moral tag where it applies), `needs.json` (rates), `shop.json` (prices for the three budgets), `radio.json` (broadcast schedule keyed to events) | none | actions are the player's; broadcasts enter knowledge when heard | none |

## Resolution per dataset

| tier | resolution | used for |
|---|---|---|
| render | 10 m heightmap and threshold pairs; 1 m lidar only as baked town images | drawing, shoreline, flood depth at features |
| simulation | 30 m cost, seen mask, viewshed, drift, groups on the graph | everything that ticks |
| fields | 250 m fallout, 100 m "last seen" time if ever wanted | smooth fields |
| vector | feature points and polygons in meters, graph edges | everything with an identity |

## Identity

Every feature has a stable id assigned by the pipeline from its source id (OSM id, county building id,
assessor parcel, detection index with cove and rank) and kept in a map file so rebuilds do not renumber.
Hand-authored overrides (decision 33) live in `overrides.json` keyed by that id: add a feature, hide one, set
`tier`, `shelter_pf`, construction class, contents, a fictional flag. The pipeline applies overrides last.
