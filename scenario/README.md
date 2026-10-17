# Escape from Catalina: the scenario, in numbers

A nuclear strike on the Los Angeles harbor. You are standing on the Two Harbors pier with a pack on, 23 miles away.
Everything below is computed from real data by `scenario/numbers.py` (full output in `numbers.txt`) and drawn by
`scenario/flood_map.py`. Run-up zones are elevation bands, not a wave model.

## Act I: the flash

| what | number | source |
|---|---|---|
| Distance, Port of LA entrance to the Two Harbors pier | 23.1 mi | geodesic |
| Light | instant | |
| Sound | 1.8 min after the flash | 343 m/s |
| Wave from the harbor itself | 15 min | shallow-water speed over ETOPO bathymetry |
| Wave from a slide on the shelf break (5 mi out, 18 mi from the island) | 8.4 min | same |
| Run-up at which Isthmus Cove meets Catalina Harbor (the isthmus becomes sea) | 10.5 m (34 ft) | USGS 3DEP 10 m DEM, flood fill |
| Isthmus land below 10 m / below 20 m | 41 ha / 81 ha | DEM |
| Nearest ground at 30 m from the town | 242 m WNW, run 1.3 min, walk 2.9 min | DEM |
| Nearest ground at 100 m from the town | 396 m NW, run 2.2 min, walk 4.7 min | DEM |
| Two Harbors buildings below 10 / 20 / 30 m | 73 / 121 / 139 of 166 | OSM + DEM |
| Avalon buildings below 10 / 20 / 30 m | 498 / 669 / 825 of 1191 | OSM + DEM |
| Buildings inside the state's tsunami hazard area | Two Harbors 72 of 166, Avalon 555 of 1191 | CGS |

The California Geological Survey's own tsunami hazard area (its evacuation planning line for the worst modelled
cases) reaches a median of 4 m and a 99th percentile of 19 m above sea level on the island, and it does **not**
join the two harbors across the isthmus. The game's 10.5 m "two islands" moment is beyond the state's planning
line, which is fine for fiction and worth knowing.

Gameplay reading: you cannot see a tsunami coming across deep water (it is a metre high out there, moving at
130 to 150 km/h). The cues are the flash, the sound two minutes later, and the harbor draining a few minutes
before the wave. The whole of act I is an 8 to 15 minute timer with a 250 m sprint uphill at the end of it.

## Act II: fallout

Not computed here. Public civil-defence guidance is enough for game design: fallout decays by about a factor of
ten for every seven-fold increase in time (7 hours: 10%, 2 days: 1%, 2 weeks: 0.1% of the one-hour rate), so the
first 24 to 72 hours indoors matter most. Southern California's prevailing wind is onshore (west to east), which
carries a plume inland and away from the island; a Santa Ana (offshore, north-east) event, common in October,
reverses that. The wind on the day is the dice roll.

High ground with real infrastructure, from OSM (height above sea level):

| place | height | what is there |
|---|---|---|
| Airport in the Sky | 482 m | hangar, storage tanks, parking, the only flat ground for a helicopter |
| Black Jack Campground / Volunteer Camp | 457 to 475 m | water, shade |
| Wrigley, Haypress, Patrick, Buffalo Springs reservoirs | 404 to 436 m | open water |
| Laura Stein Volunteer Camp | 399 m | Conservancy camp |
| Empire and Marble quarries | 315 to 319 m | pits, equipment |
| Renton Mine (above Avalon) | 260 m | historic mine, the only "into the mountain" candidate OSM knows |
| Middle Ranch: Conservancy HQ, native plant nursery, Thompson Reservoir | 203 to 220 m | buildings, water |
| Summit Reservoir, covered reservoir and substation above Two Harbors | 105 to 160 m | the nearest water and power to the start |
| USC Wrigley Marine Science Center (Big Fisherman Cove) | 5 m | science station: in the flood zone |
| Camp Emerald Bay infirmary | 4 m | in the flood zone |

OSM has no bunkers, adits or caves on the island. Black Jack Mine (historic silver and zinc workings on Black
Jack Mountain) is real but not mapped.

## Act III: escape

From the Catalina Harbor mouth, great circle:

| destination | distance | 6 kn | 20 kn |
|---|---|---|---|
| San Clemente Island, Wilson Cove (Navy) | 25.2 nm | 4.2 h | 1.3 h |
| Santa Barbara Island | 26.4 nm | 4.4 h | 1.3 h |
| Newport harbor | 33.3 nm | 5.5 h | 1.7 h |
| Dana Point | 40.9 nm | 6.8 h | 2.0 h |
| Oceanside | 57.6 nm | 9.6 h | 2.9 h |
| Channel Islands Harbor, Oxnard | 56.7 nm | 9.4 h | 2.8 h |
| San Diego, Point Loma | 78.5 nm | 13.1 h | 3.9 h |

Catalina Harbor faces south-west, away from the mainland, so it is the one place near the start where a boat
might survive; that is the act III asset. Whether it does is a design decision, not something this data decides.

## Data

| source | used for | access |
|---|---|---|
| USGS 3DEP 1/3 arc-second DEM (10 m) | whole island | prd-tnm.s3.amazonaws.com, no key |
| USGS 3DEP 1 m lidar, CA_LosAngeles_B23 (2025) | the isthmus map | The National Map API lists tiles; S3 download, no key |
| OpenStreetMap (plain map API, four strips) | buildings, roads, trails, coast, names, shelter tags | api.openstreetmap.org |
| Mapzen Terrarium z10 (ETOPO bathymetry) | wave travel time | s3.amazonaws.com/elevation-tiles-prod |
| California Geological Survey tsunami hazard area | the state's planning line | gis.conservation.ca.gov ArcGIS REST |
