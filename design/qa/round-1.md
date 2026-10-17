# Round 1, verbatim

## Questions (Claude)

Answer by number; "defaults" accepts every marked default.

**Engine and scale**
1. Likely engines (Godot, Unity, Unreal, web canvas, custom)? Only changes the example formats. Default: JSON + GeoJSON + 16-bit PNG heightmaps + bit masks.
2. Whole island simulated at once, or only around the party with the rest abstracted? Default: whole island at 30 m fields with aggregated groups; fine detail only in loaded towns.
3. Heavy fields baked by the Python pipeline (flood masks per level, fallout plumes per wind sector, travel graph) with the engine running only cheap rules? Default: yes.
4. 2D top-down only, or must the same data drive a 3D terrain mesh? Default: 2D, heightmap kept so 3D stays possible.

**Space and movement**
5. Continuous positions, or a visible grid/hex the player clicks? Default: continuous positions; cells exist only for fields.
6. Movement on the trail/road/coast graph only, or free off-trail travel over a cost surface (slope, vegetation, water)? Default: graph plus off-trail cost raster at 30 m.
7. Can the player modify the world (barricade, build, burn, open an adit)? Default: state changes on existing features only, no free building.

**Time and events**
8. Real-time with pause and speed, or turns? Different cadence per phase (seconds during the wave, hours in the fallout wait)? Default: one clock in seconds; display cadence per phase.
9. Fixed start (an October day at Two Harbors) or player-chosen date and hour? Season drives people, winds and boats. Default: fixed day, chosen hour.
10. Scripted chain only (blast, wave, fallout, escape) or a systemic event engine (second waves, landslides, fire, storms)? Default: scripted chain behind a generic event interface.
11. Seeded randomization per playthrough (wave height, wind, yield) or identical every time? Default: seeded ranges.

**Knowledge and maps**
12. Knowledge grain: per feature, per cell (fog), per layer (trail network), or all three? Default: all three.
13. Boolean or graded (unknown, rumored, known, verified)? Default: graded.
14. Can knowledge be wrong (outdated map, misplaced feature, fake secret), and must the player visit to verify? Default: yes to both.
15. Does map quality limit route planning (no pathing on unknown trails) and positional accuracy (an unofficial map is 200 m off)? Default: yes.
16. Terrain without a map: does standing there reveal shape by viewshed, with contour detail coming from map items? Default: yes.
17. Which real sites are secret (WWII bunkers, Camp Cactus, Mount Orizaba radar, adits, science stations, water and fuel tanks)? May I add fictional secrets (caches, a sealed bunker) flagged as fictional? Default: that list, fictional allowed and flagged.
18. Are the earlier views (iso stack, compass card, CRT) in-world devices that filter information, or pure render styles showing whatever is known? Default: render styles; a device wraps a style with its own filter.

**Water line and tsunami**
19. One run-up level per cove, per-cove heights from a single wave parameter, or animated propagation with arrival times and several waves? Default: per-cove heights from one parameter, arrival times per cove, two to three waves, masks baked per 0.5 m.
20. Water line precision: the DEM cell (10 m) or the 20 m plate band the iso view uses? Default: DEM cell; each view quantizes.
21. Damage boolean, or graded by depth and construction (wet, damaged, destroyed, swept) with persistent aftermath (debris, beached boats, drained tanks)? Default: graded, persistent.
22. Can the player predict a feature's flag before the event from known elevation, and can that prediction be wrong versus the official hazard line? Default: yes.

**Fallout**
23. Plume as baked dose fields per wind sector and hour, or computed at runtime? Dose tracked per character or only zones safe/unsafe? Default: baked, per character.
24. Shelter protection factor per building class (concrete, wood, underground, vehicle, boat) derived from data where possible? Default: yes.
25. Water contamination by source type (open surface, spring, well, enclosed tank, desal) with a time decay? Default: yes.

**Entities**
26. Player is one character, a small party, or a managed group of survivors? Default: small party.
27. People as aggregated groups per place with states (sheltering, fled, dead, hostile, cooperative) that consume and move, or individuals? Default: groups.
28. Animals as herds per range with density, or individuals? Do they matter for food and danger? Default: herds, both.
29. Resources as category quantities (food-days, liters, gallons) at nodes, derived from floor area and tank capacity with hand overrides? Default: yes.
30. Boats as individual entities from the detections (class, fuel, range, state)? Endgame options limited to boats, or also aircraft and signaling? Default: individual boats, all three endings.
31. Buildings: merge OSM and county outlines into one set with height, use, capacity, material class and contents? Default: yes.

**Data pack**
32. Commercial release? Affects shipping OSM (attribution), county and iNaturalist data (per-record licenses) and imagery-derived points. Default: assume commercial, ship derived data with attribution, no raw imagery.
33. Hand-authored overrides (mark a shelter, hide a feature, add a cache) in a separate file over generated data, with stable IDs that survive rebuilds? Default: yes.

## Answers (Justin)

Note: the first send of this message was interrupted after item 27 and a shorter version of the last
paragraph, then sent again in full. The full version follows.

1. Godot, Web Canvas, Custom - All options possible. I like the idea of it being a web app but like, godot would probably let us release cross-platform app on steam or even switch.
2. I don't see the benefit or cons of either option right now. I imagine things need to happen everywhere in order for things like electricity/freshwater tanks/etc to function that might be off-map. I guess make options for both and we can weigh the costs. I don't know if it makes sense to show the player every part of the map as if it's visible digitally unless maybe there's a reason that makes sense, even if only for gameplay purposes.
3. I'm good with that as long as it doesn't hinder us in a meaningful way.
4. Both.
5. default.
6. default. some things like mines and access to hunting animals should be possible, but the gradation needs to either make certain areas impassable or trecherous and affect fatigue and needs for food/water/rest/etc. Keep this roped in to the scope of this #.
7. I don't know. This isn't going to be a building game. It's mostly about surviving and trying to get to the mainland via multiple possible vectors.
8. Open to suggestion. I felt it might be a good idea to explore with using both real-time and different cadence per phase (e.g. i'm not making anyone wait days IRL for fallout. but the initial arrival to blast to tsunami seems like an appropriate real time event but i want to be open to the best options for the game at this stage
9. This is an open question. Fallout on the island is a core mechanic and if wind will literally never blow on it, it makes it very easy to just prevent that by selecting the correct season. I am familiar with Santa Ana or whaqtever. idk what the pros/cons of selecting which ferry to come over on or using money to charter a private trip at a different time would be in this scenario.
10. Default. Although a more dynamic system eventually could be interesting, just less repeatable. I wish some real time weather data could be used, but that obviously creates issues for us. open to suggestion
11. Use your best judgement
12. default
13. default
14. default
15. I don't know how route planning differs from reality. obviously you should be able to take any trail or road regardless of whether your map exists, is correct, or has been damaged. You seem to have an idea though. curious
16. yes, terrain should be revealed fog of war style w/o a map and incorrect maps can be fixed if you have a pen. memory can be an issue so exact locations of certain things simply can't be recalled with detail as time goes on unless you have a map/pen/etc or something. unreliable narrator. stress increases memory issues unless that's an unnecessary element. needs to be a coherent system and not just tons of useless data the player can't actually use for anything.
17. use your best judgement. maybe player builds and past games can open up options for knowing roughly about things that are secret. I'm okay with some fictional stuff, but it needs to be definitely labelled and not over-done. Ideally we reserve this for finishing touches for gameplay balance and maybe some intrigue or where we don't have real data. must be able to be turned off. the cool thing about all this is we're using real constraints IRL.
18. default. maybe some views are more useful than others. shouldn't be merely an aesthetic choice, although google maps layers on each view should be possible (in spirit, not literally). those views were largely experiments, but they are really excellent. 2D for like, paper maps, and 3D if your phone still has charge and you had the foresight to purchase and download a map for an app like FarOut does. May be able to find phones. Cell towers may be able to be fixed and provide local mesh, idk. Radio at science stations and Walkie Talkies possible maybe? idk what NPC / multiplayer communications look like if at all.
19. default. but I like the other idea too
20. default
21. default
22. default
23. default. but honestly i feel like we might want to consider the other option also
24. default
25. default
26. all of the above are possible. i'm opening up to the possibility for multiplayer also but i can't tell whether this game will work well for that or not. You should definitely be able to start out as a solo hiker and finish that way, or lead a small group, but idk how this complicates things and what it really adds or if it detracts in any way.
27. all of the above. possible danger from desperate ppl
28. herds for herding animals, individual for non-herding animals. Don't forget sea life w/ schools of fish and such. accurate fishing mechanics and such within reason.
29. default
30. default
31. default
32. yes. we will explore how to use what we have without necessarily eiliminating anything besides like, where it's STRICTLY illegal or requires way too much money to use. i don't want to use actual resources, this is all data modelling with rendering on our part, except where we do decide to use sprites and vector graphics.
33. default

Maybe boating around the coast should be possible? Maybe fishing from coast and boat possible? Gas needs. Possible to get stranded away from the coast and need to attempt to swim, even if it wasn't an escape attempt. Maybe boats that were loosed can be accessed this way for supplies. Tow boats! haha. Save more than just yourself!!! become a hero for "overkill" success. older ppl, pregnant women, and children are a burden though, this might be going too far, just thoughts. can't be a whole civ sim.

also, I want an option during character creation that asks simply "Are you a believer? Y/N". it doesn't add any detail after that or explain. Whether you believe or not, you are always given an option of praying. if you are a believer, God is now your father. In a biblical sense, he will put trials in front of you, but overcoming them will lead to strengths and benefits somehow, or better outcomes. this process should be wholly invisible to the player who isn't paying attention. If you are obedient in moral areas during your choices during the game, you won't be punished with chastening events, but trials/chastening are always meant to bring you to "repentance", however that might play out in the gameplay itself. If you don't pray, i don't know what should happen, but a true believer will always be brought to repentance, although i guess false believers can also be exposed through this although I am seeking to deliver exactly what the god of the bible would do w/ a modern believer. Let's choose reformed theology. If you are not a believer, God is not your father. you can run wild like a dog in the yard and god won't chasten, teach, trial, or speak (indireclty) with you in any way, even if you pray. HOWEVER. I feel that maybe it makes sense to make it possible to become a false believer or on the other hand, a convert. Some ppl on the island are more or less religious than others, but "born again" status is pre-election like in bible. npcs display the same variability as real ppl who are in process of sanctification through this disaster, but "judge nothing until the time" e.g you don't know who's real and who's not until the end, not that that will necessarily be displayed to the player. This is largely a hidden mechanic but should have a balanced outcome on the game in that God definitely helps you but the trials/chastening based on moral behavior and maybe even things that could be considered "thoughts" are difficult sometimes, although normal occurrences for the most part. the holier you are, the more likely it is that you'll be given chastening for certain actions, and god also wants his holy ones to become even more holy, pushing you towards even higher standards through trials also. this will be difficult to add without being obvious, but you should be able to help people spiritually. if you hurt a believer spiritually, "Vengeance is mine, I will repay" says the Lord. and "It would be better if a millstone were hung around his neck and to be cast into the sea" etc.

Any more questions?
