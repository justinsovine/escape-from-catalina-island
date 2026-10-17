# Boats on the water, from NAIP aerial imagery

Compact bright hulls on the sea inside each cove, 0.6 m pixels; length is the long axis. Mooring buoys, kelp, surf and glint are rejected by size, shape and colour; piers and the shore are masked. Check images: atlas/out/boats_check_*.png.

| cove | image date | boats | under 6 m | 6 to 12 m | 12 to 20 m | 20 to 35 m | over 35 m | longest |
|---|---|---|---|---|---|---|---|---|
| Avalon harbor | 2022-05-11 | 56 | 4 | 40 | 12 | 0 | 0 | 18 m |
| Descanso Bay / Hamilton Cove | 2022-05-11 | 6 | 0 | 5 | 1 | 0 | 0 | 15 m |
| Isthmus Cove / Two Harbors | 2022-05-11 | 4 | 1 | 2 | 1 | 0 | 0 | 17 m |
| Fourth of July / Cherry Cove | 2022-05-11 | 3 | 0 | 1 | 2 | 0 | 0 | 17 m |
| Catalina Harbor | 2022-05-11 | 26 | 1 | 14 | 10 | 1 | 0 | 21 m |
| Emerald Bay | 2022-05-11 | 0 | 0 | 0 | 0 | 0 | 0 | 0 m |
| Howlands Landing | 2022-05-11 | no water in image | | | | | | |
| Toyon Bay / White's Landing | 2022-05-11 | 6 | 1 | 3 | 2 | 0 | 0 | 20 m |
| Little Harbor | 2022-05-11 | 0 | 0 | 0 | 0 | 0 | 0 | 0 m |
| Big Fisherman Cove (USC) | 2022-05-11 | 0 | 0 | 0 | 0 | 0 | 0 | 0 m |
| Long Point / Italian Gardens / Goat Harbor | 2022-05-11 | 0 | 0 | 0 | 0 | 0 | 0 | 0 m |
| Empire Landing / Ripper's / Cabrillo | 2022-05-11 | 5 | 1 | 2 | 2 | 0 | 0 | 16 m |

Reading the counts: the detector only trusts calm water, so these are lower bounds for the sheltered inner
harbors on a Wednesday in May. The official statistics are the better planning numbers: Avalon averaged about
170 boats a night on moorings in October 2025 (1,264 vessels over the month), Two Harbors reported 1,428 moored
and 157 anchored for the month of June 2023, and the coves sell out for Buccaneer Days in early October.

## 2023 county aerial (LARIAC7, 0.25 m, winter 2023, calm water)

Same detector on the 4-inch LA County orthoimagery (WMTS tiles stitched at zoom 19), with the OSM coastline as the
water mask. The calm, glint-free winter imagery also resolves the white mooring buoys, so each cove's buoy-sized
dots are counted too (about 2 to 3 dots per mooring: bow and stern buoys plus pickup floats, so dots divided by 2.5
approximates the moorings in the water that day). Points are in atlas/out/boats_2023.geojson and on the page as
"boats and mooring buoys, 2023 county aerial". Check images: data/lariac/check_*.png (not committed).

| cove | boats | under 6 m | 6 to 12 m | 12 to 20 m | 20 to 35 m | over 35 m | buoy-sized dots | dots / 2.5 |
|---|---|---|---|---|---|---|---|---|
| Isthmus Cove / Two Harbors | 18 | 4 | 12 | 1 | 1 | 0 | 775 | 310 |
| Avalon harbor + Descanso | 111 | 13 | 72 | 23 | 3 | 0 | 410 | 164 |
| Catalina Harbor | 50 | 8 | 31 | 9 | 2 | 0 | 377 | 151 |

Against the published mooring counts (Two Harbors manual: Isthmus 257 rows plus 64 string-line spots, Cat Harbor
117 plus Wells Beach; Avalon chart about 350 to 400 moorings), the dot counts are consistent with nearly every
mooring having its gear in the water in winter while most of the boats are gone: the Isthmus held 18 boats on
about 300 moorings, Avalon 111 boats on about 164 to 400.
