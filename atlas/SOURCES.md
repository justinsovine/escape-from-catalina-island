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
| per-buoy positions, boats, vehicles at 10 cm | LA County LARIAC7 2023 4-inch aerial tiles (public WMTS behind the county hub): `https://svc.pictometry.com/Image/BCC27E3E-766E-CE0B-7D11-AA4760AC43ED/wmts/PICT-LARIAC7--KCrSFBeqgG/default/GoogleMapsCompatible/{z}/{x}/{y}.png` (2020: `PICT-LARIAC6--pCqXruF2NL`); hub https://egis-lacounty.hub.arcgis.com/maps/b301429f8bc1469bb2bbd5a6c3330abe ; product guide https://apps.gis.lacounty.gov/static/hub/lariac_documents/LARIAC7/Documents_Data/LARIAC7_ProductGuide_Final.pdf | open tiles, no key (GeoTIFFs and obliques need LARIAC membership) | fetched over the Isthmus, Avalon, Cat Harbor, the village and Ben Weston; see the Boats tab |
| harbor depths and mooring-field bathymetry at 1 m | NOAA CoNED Southern California topobathy 2016, tiles F_09 F_10 G_09 G_10 on s3://noaa-nos-coastal-lidar-pds/dem/CA_Southern_CoNED_DEM_2016_8658/ | open, cloud-optimized GeoTIFF, windowed reads | fetched for the Isthmus, Cat Harbor, Avalon, Little Harbor, Emerald and Howlands; 5 to 50 m contours on the map |
| anchorage depths and rules | NOAA Coast Pilot 7 chapter 5, https://nauticalcharts.noaa.gov/publications/coast-pilot/files/cp7/CPB7_C05_WEB.pdf ; 33 CFR 110.216 | open | in FACTS.md |
| boats on an October day | Avalon Harbor monthly activity reports (Catalina Islander), the tourism authority's monthly visitor counts https://www.lovecatalina.com/members/resources/visitor-counts/ | open | in FACTS.md; per-day counts not published |
| October imagery of the mooring fields | Sentinel-2 L2A via https://earth-search.aws.element84.com/v1 (10 m, hulls over 15 m) | open STAC, no key | reachable, not yet used |

## Shelter, mines, military

| what | source | access | status |
|---|---|---|---|
| mine symbols digitized from the 1943 quads | USGS USMIN points, WFS `https://mrdata.usgs.gov/wfs/usmin?request=GetFeature&service=WFS&version=1.1.0&typeName=points&bbox=33.27,-118.66,33.52,-118.27,EPSG:4326` (8 points: Renton Mine, open pits, quarries) | open | fetched; on the map |
| mine and adit locations | USGS MRDS records (Black Jack 10034274, Renton 10034280, Cherry Valley 10072444, quarries) https://mrdata.usgs.gov/mrds/ ; USGS historical 1950 7.5-minute quads with mine symbols, https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/CA/ (names like `CA_Santa Catalina East_300230_1950_24000_geo.tif`) | open | fetched; five Renton-area symbols and the Black Jack shaft read off the 1950 maps are on the map |
| active mines | California Mines Online, https://gis.conservation.ca.gov/server/rest/services/MOL/MOLMines/FeatureServer/0 | open ArcGIS REST | fetched: Pebbly Beach Quarry and Empire Quarry |
| sealed or open adits | nobody publishes this; the Conservancy and the state Abandoned Mine Lands Unit know | ask the Conservancy; AML inventory is not public | needs you |
| WWII sites | USACE FUDS feature service https://services7.arcgis.com/n1YM8pTrFmm7L4hs/arcgis/rest/services/fuds/FeatureServer (layer 1 property points, 4 polygons, 3 munitions sites): Camp Cactus 33.3508 -118.4578, Radar Site J-41 33.3667 -118.4806, Mount Orizaba 1K2 33.3417 -118.4181, Catalina Training Base (Coast Guard) polygon at the Isthmus, OSS Toyon Cove, Buffalo Spring Airport, the island bombing area and dive-bombing target, the amphibian airport; inventory PDF https://www.usace.army.mil/Portals/2/docs/Environmental/FUDS/FUDS_Inventory/FUDS_Inventory_California.pdf | open REST | fetched; on the map |
| Ben Weston bunkers | Hiking Project "Ben Weston Bunkers Spur" https://www.hikingproject.com/trail/7013068/ben-weston-bunkers-spur (trail start 33.37135 -118.47993 in the page data; GPX needs a free login) | open page | start point fetched; a structure at the promontory road end is visible on the 2023 aerial at 33.3710 -118.4806 |
| building construction and heights | LA County Countywide Building Outlines 2020 with HEIGHT and ELEV, https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines_(2020)/FeatureServer/0 ; LA County Assessor parcel roll (use, floor area, year built, units), https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Parcel_Data_2021_Table/FeatureServer/0 | open ArcGIS REST | fetched: 1,998 outlines, 1,259 Avalon parcels (2025 roll) |

## Water, food, fuel

| what | source | access | status |
|---|---|---|---|
| wells, tanks, treatment plants | Drinking Water Watch system CA1910006 "SO. CAL. EDISON CO.-SANTA CATALINA": facilities page https://sdwis.waterboards.ca.gov/PDWW/JSP/WaterSystemFacilities.jsp?tinwsys_is_number=2485&tinwsys_st_code=CA (47 facilities: 10 wells, 15 tanks TK001 to TK015, desal and treatment plants); capacities in the CPUC water quality report https://www.cpuc.ca.gov/-/media/cpuc-website/divisions/news-and-outreach/documents/pao/customer-notices/cn-2021/sce-a2010018-water-quality-report.pdf (Thompson 343 MG, Wrigley 9.45 MG, 12 tanks 2.22 MG) | open | read; in FACTS.md |
| fuel tank registrations and capacities | EPA UST Finder feature service https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/UST_Finder_Feature_Layer_2/FeatureServer (table 4 = tanks; Avalon fuel dock CA10271113: 4,000 + 4,000 + 4,000 diesel + 3,000 gal; Pebbly Beach station CA10271122: 3 x 6,000 gal); GeoTracker cases via the Water Boards hosted layer https://gispublic.waterboards.ca.gov/portalserver/rest/services/Hosted/UST_Cases_08032021/FeatureServer/0 (15 cases on the island); CalEPA site portal https://siteportal.calepa.ca.gov/nsite/map/ ; the hazardous-materials inventories themselves are a records request to LA County Fire HHMD | open REST | fetched; in FACTS.md |
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
| day-of-week ferry loads | not published by the operators; monthly series: tourism authority visitor counts (needs a browser User-Agent), Avalon transient occupancy tax Jul 2016 to 2025 https://assets.simpleviewinc.com/simpleview/image/upload/v1/clients/catalinaislandccvb/Avalon_Tourism_Revenue_Report_Statistics_July_2016_to_2025_c2461d18-f82a-4dfb-b6ec-4613ac8ffa69.pdf | open | monthly only; daily needs a records request to the City of Avalon |
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
| birds | eBird API 2.0 (free key at https://ebird.org/api/keygen, header x-ebirdapitoken; hotspot L3932699 "Santa Catalina Island--Two Harbors area": https://api.ebird.org/v2/data/obs/L3932699/recent) | key: set `EBIRD_API_KEY` in the environment | needs you |
| historic tsunami run-ups | NOAA NCEI hazards API https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/tsunamis/runups?country=USA (filter locationName for Catalina) | open | fetched: 1946 1.5 to 1.8 m, 1960 0.6 m, 1964 1.5 m, 1975 1.4 m |
| cell sites | HIFLD Cellular Towers https://services2.arcgis.com/PYn6bWCjT6bhw1z3/arcgis/rest/services/HIFLD_Cellular_Tower/FeatureServer/0 (two at Black Jack); FCC ASR bulk https://data.fcc.gov/download/pub/uls/complete/r_tower.zip ; CPUC fire-threat tiers https://services2.arcgis.com/VofPZYDe2pLxSP5G/arcgis/rest/services/CPUC_High_Fire_Threat_District/FeatureServer/0 (interior is Tier 3); backup-power decision https://docs.cpuc.ca.gov/PublishedDocs/Published/G000/M344/K021/344021480.PDF | open | fetched; on the map |
| census API | https://api.census.gov/data/2020/dec/pl (now needs a key: https://api.census.gov/data/key_signup.html, set `CENSUS_API_KEY`); TIGERweb carries the same block counts without a key (used) | key optional | fetched via TIGERweb |
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
| LANDFIRE vegetation and fuels | https://lfps.usgs.gov/api/job/submit?Email=you@example.org&Layer_List=LF2024_EVT;LF2024_CC&Area_of_Interest=-118.65 33.28 -118.28 33.52&Output_Projection=4326 then poll /api/job/status?JobId= | open, email parameter required | format verified, not yet pulled |
| NLCD land cover clip | https://www.mrlc.gov/geoserver/mrlc_download/wcs?service=WCS&version=2.0.1&request=GetCoverage&coverageId=mrlc_download__NLCD_2021_Land_Cover_L48&subset=Long(-118.66,-118.27)&subset=Lat(33.27,33.52)&subsettingcrs=http://www.opengis.net/def/crs/EPSG/0/4326&format=image/geotiff | open | verified |
| more Conservancy and UCLA layers | same org services5.arcgis.com/6todkfokiIaUCZfU: trans_catalina_trail, trans_catalina_trail_mile_markers, CIC_Trails_Ownership, Culverts_All, CIC_Signs, Exclosure_outline, NoFirearmZone; UCLA bundle https://services7.arcgis.com/2hYXmwteFLemN5bW/arcgis/rest/services/CIC_Data/FeatureServer (campgrounds, campsites, roads and trails, Avalon boundary, exclosures, property) | open | reachable |
| tsunami hazard downloads | CGS statewide hazard area zip https://www.conservation.ca.gov/cgs/Documents/Publications/Tsunami-Maps/CGS_Tsunami_Hazard_Area_for_Emergency_Planning.zip ; LA County KMZ https://www.conservation.ca.gov/cgs/Documents/Publications/Tsunami-Maps/Tsunami_Hazard_Area_Los_Angeles_County.kmz ; the 2009 quad series never covered Catalina; Avalon's harbor tsunami playbook exists (CGS SR 241) but is not posted: request from the CGS tsunami program or the Avalon Harbor Department | open / request | partly fetched |
