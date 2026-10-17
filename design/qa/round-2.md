# Round 2, verbatim

## Questions (Claude)

Options with costs for 2, 8, 9 and 26 go in the design doc. On 15: the party can walk any trail it is standing on, but the "go to" planner only routes over trails you know, and walking an unknown trail adds it to your map. A wrong or damaged map plans routes that fail in the field. Confirm or reject in 47 below.

**Scenario and world edge**
34. Targets: one surface burst at the Port of LA, or a strike set (Long Beach, San Diego, Point Mugu, Vandenberg, Pendleton)? Yields? Decides fallout sources and which mainland landings are safe. Default: scenario file lists any number; first scenario Port of LA 300 kt surface plus Long Beach.
35. EMP: at 25 miles a surface burst does not fry island electronics. Keep that, or want EMP for drama? Default: no EMP; the grid dies from lost backhaul and the sea-level Pebbly Beach plant flooding.
36. GPS keeps working (satellites unaffected), so a charged phone is a precise position fix and paper-map skill only matters when batteries die. Default: yes.
37. Start positions: Two Harbors pier on arrival only, or also mid-channel on the ferry, Avalon, a campsite, a moored boat? Default: data supports any; first release Two Harbors.
38. Off-island world: simulate the crossing (fuel, sea state, drift, night), destinations as states from the scenario, rescue responsive to signals (radio, flares, airfield SOS) with a late baseline sweep. Default: yes.
39. Infrastructure as a dependency graph (plant, lines, pumps, tanks, taps, towers, fuel) with simple flow rules so off-map failures propagate. Default: yes, a few dozen nodes.
40. Escape attempts allowed at any time, even into the plume or debris, not phase-gated. Default: yes.

**Time and weather**
41. Opening phase at real time 1x, pausable, about 15 minutes; fallout phase through "wait" actions that compress days and break on events. Default: yes.
42. Weather as real hourly tapes (airport station plus buoy 46025) replayed from a seeded real date, choosing only dates with at least one offshore-wind episode in the first ten days. Fallout always arrives, but never the same way. Default: yes.
43. Season fixed to Santa Ana season (October, November); the ferry or charter choice sets only the hour of arrival. Default: yes.

**Movement and body**
44. Per-person needs: hydration, calories, sleep, core temperature, injury, dose, stress (stress feeds memory and the faith system). Pack weight affects speed and fatigue. Add or remove anything?
45. Death: control passes to a surviving party member, else the run ends. One autosave, replay by seed, no save scumming. Default: yes.

**Knowledge, memory, maps**
46. Memory: each remembered feature carries a position and an error radius that grows with time since last seen (faster under stress), reset by revisiting or writing it on a map. Seen terrain shape does not fade. Mild false memories allowed. Default: yes.
47. Route planning as described above. Default: yes.
48. Map annotations structured (pins, lines, crosses, short notes), not freehand drawing. Default: structured.
49. Main screen shows perception (truth within senses) crisp and belief (remembered) faded; truth beyond senses never appears. Default: yes.
50. Meta-progression: knowledge from past runs returns as rumors with a large error radius, never exact. Default: yes.
51. Devices as entities (paper map, phone with offline maps, GPS unit, satellite messenger, boat VHF, walkie, science-station radio, weather radio) with layers, precision, power, range and infrastructure dependencies. Satellite messengers keep working but are rare finds. Default: yes.

**People**
52. Multiplayer shape if any: co-op party with shared knowledge, separate survivors who can meet, or asynchronous shared world. Default: build knowledge per observer and a deterministic sim now, choose later; recommend separate survivors, 2 to 4.
53. Party members as individuals up to about 8 with needs and skills (medic, mechanic, boat, fishing); larger groups as aggregates. Default: yes.
54. Conflict with desperate people as abstract encounters fed by spatial inputs (terrain, dark, numbers, weapons), with real weapon sources inventoried (sheriff station, hunting rifles, flare guns). Default: yes.
55. Vulnerable people as simple modifiers (speed, needs, morale) and rescue scoring weighted by vulnerability, nothing more. Default: yes.

**Sea**
56. Loosed boats drift hourly with wind, then beach or sink; towing as a link between boat entities. Default: yes.
57. Fishing from habitat density fields (kelp, reef, sand, open water) by gear and time, species from state fisheries tables, contamination rising over time; no moving schools. Default: yes.

**Licensing**
58. The OSM-derived data pack ships as a separate open file under its share-alike license; code and art closed. Animal records limited to CC0 and CC BY. Scripture text from the KJV (public domain). Default: yes to all three.

**Faith**
59. Election is hidden and rolled at creation, independent of the Y/N answer, which records profession. A false professor (Y, not elect) gets the unbeliever path exactly: no help, no chastening, same screens. An elect N switches paths after effectual calling. Ratios? Default: 1 in 6 of Y false, 1 in 6 of N elect.
60. Calling comes only through means (a believing NPC, a found Bible, a church), then a profession opportunity recurs until the player answers Y. Default: yes.
61. Providence acts only through natural means: which weather tape, item placement, NPC dispositions, event timing. No divine text, no visible miracles. Default: yes.
62. Moral ledger domains: theft, violence beyond defense, deceit, broken promises, abandoning the vulnerable, harming or mocking believers, mercy and sharing, prayer and thanksgiving, Sabbath rest. Add or remove? Sabbath as a real mechanic (one rest day in seven)?
63. "Thoughts" in gameplay: planned orders later canceled, hovered dialogue options, or an explicit intent choice? Default: canceled plans only, light weight.
64. Repentance requires a confession prayer plus fruit (changed behavior over days) plus restitution where possible; chastening continues until then. Default: yes.
65. Balance: obedient believer gets more trials and the best expected outcome; disobedient believer gets chastening until repentance; unbeliever gets a flat run with natural consequences only. Confirm.
66. Prayer types (petition, confession, thanksgiving, intercession), free and with no UI feedback. NPC faith states never shown, even in the epilogue. Default: yes.

**Last three** (asked in round 3; see round-3.md)

## Answers (Justin)

34. The san pedro shelf is the only thing that can create the tsunami IIRC. Although it does seem like an opportunity for a difficulty modifier. Consider the real answer here. we can't balance too many moving parts.
35. In what circumstance would this actually happen? I thought air burst would do that? Maybe the difference is a surface burst vs a air burst, unless a spread strike would still cause the shelf issue. Thoughts?
36. default
37. default, but I think avalon and two harbors should both be options. you should also be able to use your money to charter a private boat for anywhere/anytime but it is very expensive and comes at the cost of your other gear. idk how starting money should work. set? maybe it should be like oregon trail as a difficulty modifier or something? just thinking outloud. if this is too variable the player could like, have hours at starting towns for prep which I could see as being fine to a degree, but we need to balance this
38. default.
39. default
40. default
41. default
42. default
43. default
44. default
45. Ummm, idk. I guess that balances out the difficulty of needing more resources and variable issues with more players. on th eother hand like, theoriginal idea was to be like a person and if that person dies you die, but idk what would be more fun tbh. maybe solo mode can be like the permadeath option even if you have companions? idk how this trickles down to multiplayer etc
46. default
47. default
48. default
49. default
50. default
51. default
52. use your best judgement w/ adversarial review.
53. use your best judgement w/ adversarial review. idk, you should be able to save a lot of people even if you don't have them all in your active group. set ppl up to wait in safety you've created maybe? You can fit a lot of ppl on a big boat but it requires more gas etc.
54. default
55. default. see above, use judgement
56. default
57. default
58. default. but don't limit me during development, this will be a finishing touch. think about it in advance though
59. default.
60. default. i love this
61. default
62. no sabbath rest. the lord's day is Sunday. idk how this really plays into things without over-evangelizing the game in an obvious way.
63. We should explore this more within reason
64. default. we need to remember to keep much of this opaque and unprompted. same as real life
65. confirm
66. default.

Any more questions?
