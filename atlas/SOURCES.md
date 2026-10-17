# Data sources, by gap

Status on 2026-10-17 from this environment. "Fetched" means the data is in the repo's `data/` folder (rebuild with
`python atlas/sources.py`) and on the map. "Needs you" means a key, a login or a records request. Raw research
sheets with more links are in `atlas/research/`.

## Moorings and harbors

| what | source | access | status |
|---|---|---|---|
| mooring rows, numbers and counts per cove | Two Harbors Harbor Department, Policies and Procedures Manual, April 2024, Appendix C (pages 42 to 51), https://assets.simpleviewinc.com/simpleview/image/upload/v1/clients/catalinaisland/Two_Harbors_Policy_and_Procedures_Manual_REVISED_April_2024_FINAL_064bd6e3-4784-4e33-9e2e-18a58297059e.pdf | open PDF, maps are images | fetched; pages and a transcription in `atlas/research/moorings/` |
| Avalon rows by boat length, Descanso and Hamilton numbering | City of Avalon, Mooring Information and Mooring Map brochure, https://www.cityofavalon.gov/DocumentCenter/View/175/Mooring-Information-and-Mooring-Map-PDF | open PDF | fetched, page image saved |
| rigged size of each Avalon mooring | City of Avalon moorings-for-sale list (sizes per number) https://cityofavalon.gov/DocumentCenter/View/2169/Website-Posting-Moorings-For-Sale-August-19-2026 and the row rule in Municipal Code 10-2.210 | open | partial: 21 moorings listed; the rest follow the row rule |
| per-buoy positions | none published; buoy dots on 0.6 m USDA imagery are unreliable in chop (tested) | LA County's 10 cm LARIAC aerials would resolve them: public records request to LA County ISD/eGIS, or the imagery service if the county exposes it | needs you |
| harbor depths and mooring-field bathymetry at 1 m | NOAA CoNED Southern California topobathy 2016, tiles F_09 F_10 G_09 G_10 on s3://noaa-nos-coastal-lidar-pds/dem/CA_Southern_CoNED_DEM_2016_8658/ | open, cloud-optimized GeoTIFF, windowed reads | fetched for the Isthmus, Cat Harbor, Avalon, Little Harbor, Emerald and Howlands; 5 to 50 m contours on the map |
| anchorage depths and rules | NOAA Coast Pilot 7 chapter 5, https://nauticalcharts.noaa.gov/publications/coast-pilot/files/cp7/CPB7_C05_WEB.pdf ; 33 CFR 110.216 | open | in FACTS.md |
| boats on an October day | Avalon Harbor monthly activity reports (Catalina Islander), the tourism authority's monthly visitor counts https://www.lovecatalina.com/members/resources/visitor-counts/ | open | in FACTS.md; per-day counts not published |
| October imagery of the mooring fields | Sentinel-2 L2A via https://earth-search.aws.element84.com/v1 (10 m, hulls over 15 m) | open STAC, no key | reachable, not yet used |

## Shelter, mines, military

| what | source | access | status |
|---|---|---|---|
| mine and adit locations | USGS MRDS records (Black Jack 10034274, Renton 10034280, Cherry Valley 10072444, quarries) https://mrdata.usgs.gov/mrds/ ; USGS historical 1950 7.5-minute quads with mine symbols, https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/CA/ (names like `CA_Santa Catalina East_300230_1950_24000_geo.tif`) | open | fetched; five Renton-area symbols and the Black Jack shaft read off the 1950 maps are on the map |
| active mines | California Mines Online, https://gis.conservation.ca.gov/server/rest/services/MOL/MOLMines/FeatureServer/0 | open ArcGIS REST | fetched: Pebbly Beach Quarry and Empire Quarry |
| sealed or open adits | nobody publishes this; the Conservancy and the state Abandoned Mine Lands Unit know | ask the Conservancy; AML inventory is not public | needs you |
| WWII sites | USACE Formerly Used Defense Sites portal https://fudsportal.usace.army.mil/ and the USACE open data hub https://geospatial-usace.opendata.arcgis.com/ ; California State Military Museum pages (Camp Cactus, Coast Guard base, OSS) | open | reachable; FUDS geometry not yet pulled (see the research sheet when it lands) |
| Ben Weston bunkers | Hiking Project "Ben Weston Bunkers Spur" https://www.hikingproject.com/trail/7013068/ben-weston-bunkers-spur | open page; GPX needs a free login | needs you for the GPX, or read the map |
| building construction and heights | LA County Countywide Building Outlines 2020 with HEIGHT and ELEV, https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines_(2020)/FeatureServer/0 ; LA County Assessor parcel roll (use, floor area, year built, units), https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Parcel_Data_2021_Table/FeatureServer/0 | open ArcGIS REST | fetched: 1,998 outlines, 1,259 Avalon parcels (2025 roll) |

## Water, food, fuel

| what | source | access | status |
|---|---|---|---|
| wells, tanks, treatment plants with capacities | State Water Board Drinking Water Watch (SDWIS) https://sdwis.waterboards.ca.gov/PDWW/ , search the system name "Catalina" (Southern California Edison) and open Water System Facilities | open web app, no API | reachable; facility pages to be read by hand or scraped |
| fuel tank registrations and capacities | CalEPA CERS public portal https://cers.calepa.ca.gov/ (search Avalon facilities: hazardous materials inventories list tank volumes); State Water Board GeoTracker https://geotracker.waterboards.ca.gov/ (underground tank sites) | CERS open; GeoTracker blocks this container (403) | CERS reachable; GeoTracker needs you |
| SCE plant fuel storage, water system | SCE Catalina water fact sheet https://www.sce.com/sites/default/files/inline-files/G23-050_Catalina_Water_System_Fact_Sheet_062223_web.pdf ; CPUC application A.21-10-005 documents https://docs.cpuc.ca.gov/ ; AQMD hearing-board exhibits for the Pebbly Beach plant | open | in FACTS.md |
| food stock | nothing public | ask Vons (Albertsons) or the Island Company; or estimate from floor area (Vons parcel floor area is in the assessor roll) | needs you |

## Fallout and weather

| what | source | access | status |
|---|---|---|---|
| wind climatology for the fallout dice | Iowa Environmental Mesonet ASOS archive for KAVX, https://mesonet.agron.iastate.edu/request/download.phtml?network=CA_ASOS (station AVX) | open | fetched 2015 to 2025 hourly: October winds W 32%, SW 14%, NW 13%, E 8%, N 7%, NE 6%; a NE wind of 10 kt or more on 10% of October days |
| trajectories for a given day | NOAA ARL HYSPLIT web https://www.ready.noaa.gov/HYSPLIT_traj.php (form, no API; a local install runs from GDAS files) | open, interactive | needs a person at the form, or run HYSPLIT locally |
| forecast winds | api.weather.gov hourly grid (already used by the trip page) | open | fetched |
| buoy climatology | NDBC 46025 historical files https://www.ndbc.noaa.gov/station_history.php?station=46025 | open | reachable |

## People

| what | source | access | status |
|---|---|---|---|
| Two Harbors and interior population | 2020 census blocks with P1 counts via TIGERweb https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2020/MapServer/10 | open, no key | fetched: island 3,715; blocks west of Avalon 192 people, 207 housing units |
| hotel rooms | LA County Assessor roll 2025, use code "Hotel and Motel" with Units | open | fetched: 30 hotel parcels, 632 rooms |
| visitors by month, cruise calls | https://www.lovecatalina.com/members/resources/visitor-counts/ (monthly PDFs) ; cruise schedule https://www.lovecatalina.com/community-information/cruise-ship-schedule/ | open | in FACTS.md |
| day-of-week ferry loads | Catalina Express does not publish; the Avalon Harbor Fund wharfage reports (city council agendas) carry monthly passenger counts | records request to the City of Avalon | needs you |
| trail permits | Conservancy | ask | needs you |

## Vehicles

| what | source | access | status |
|---|---|---|---|
| Avalon vehicle counts | City of Avalon vehicle FAQ and the March 2025 council study session (Catalina Islander) | open | in FACTS.md |
| fleets | Conservancy, Island Company, SCE, CR&R, LACoFD apparatus | ask; LACoFD station pages | needs you |

## Animals

| what | source | access | status |
|---|---|---|---|
| sightings with coordinates | iNaturalist API https://api.inaturalist.org/v1/observations (research grade, bbox query, no key) | open | fetched: bison 599, deer 520, fox 835, eagle 146, rattlesnake 104, sea lion 155, seal 36; on the map |
| birds | eBird API 2.0 (free key at https://ebird.org/api/keygen ; set `EBIRD_API_KEY`) | key | needs you |
| fox range and habitat | CDFW BIOS layers ds3288 and ds3298 via https://www.arcgis.com/home/item.html?id=4483fd6e36a04eb392ac899071b55661 | open | reachable |
| herd and population numbers | Conservancy permit filings and reports (see the research sheet) | open | in FACTS.md |
| GBIF occurrences | https://api.gbif.org/v1/occurrence/search | open | reachable |

## Map data

| what | source | access | status |
|---|---|---|---|
| vegetation map | Conservancy 2000 vegetation (3,149 polygons, 17 communities) https://services3.arcgis.com/vq5vGR4r1YX7ueLg/arcgis/rest/services/Catalina_vegetation_CIC/FeatureServer/0 | open | fetched |
| 2023 land cover at 4 inch (trees, shrubs, grass, bare, buildings, roads, paved, water) | LA County LARIAC7 https://cache.gis.lacounty.gov/cache/rest/services/LARIAC7/LANDCOVER_2023/MapServer (export endpoint) | open, dynamic map export | tested over the Isthmus |
| roads and trails with names, ownership, watersheds, property | Conservancy ArcGIS Online: roads_trails_all_2017 (773 lines), CICRoads_Ownership, Trails_KI, WMU watersheds, CIC_Property_Boundary on https://services5.arcgis.com/6todkfokiIaUCZfU/arcgis/rest/services/ | open | fetched |
| tsunami inundation line (2009 state maps) | LA County Hazards service layers 6 and 7, https://public.gis.lacounty.gov/public/rest/services/LACounty_Dynamic/Hazards/MapServer | open | fetched; on the map |
| state tsunami hazard area (2021 maps) | https://gis.conservation.ca.gov/server/rest/services/CGS/IW_Tsunami_Hazard_Area/FeatureServer/0 | open | fetched earlier |
| 1 m lidar | USGS 3DEP CA_LosAngeles_B23 via The National Map API | open | fetched |
| near-shore bathymetry | NOAA CoNED SoCal 1 m (above); NCEI 1/9 arc-second CUDEM has no southern California tiles | open | fetched for the harbors |
| 10 cm aerial imagery (LARIAC 2020 and 2023) | not in the county's public tile cache (which stops at 2014); ask LA County eGIS for LARIAC access https://egis-lacounty.hub.arcgis.com/ | needs you | |
| LANDFIRE vegetation and fuels | https://lfps.usgs.gov/ (job API) | open | reachable, not yet used |
