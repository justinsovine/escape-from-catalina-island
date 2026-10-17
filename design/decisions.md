# Decisions from the Q&A, by number

"Default" means the recommended option was accepted as stated in the question.

## Round 1

1. Engines: Godot, web canvas or custom are all possible; pack format JSON, GeoJSON-style geometry in meters, 16-bit PNG rasters, bit masks.
2. Simulation scope: options for whole-island and local-bubble with costs (09); off-map systems must function.
3. Heavy fields baked by the pipeline; the engine runs cheap rules.
4. 2D and 3D both.
5. Continuous positions; cells only for fields.
6. Graph movement plus off-trail cost surface; gradation makes areas slow, treacherous or impassable and feeds fatigue and needs; mines and hunting reachable off trail.
7. Not a building game; state changes on existing features only.
8. Time: real time for the opening, compressed waiting for fallout; one clock, cadence per phase.
9. Season fixed to Santa Ana season; arrival hour by ferry or charter (43).
10. Scripted event chain behind a generic event interface; real weather via tapes (42).
11. Seeded randomization within ranges.
12. Knowledge per feature, per cell and per layer.
13. Graded knowledge: unknown, rumored, known, verified.
14. Knowledge can be wrong; verification needs presence.
15. Route planning uses known edges only; any trail can be walked; walking verifies (47).
16. Fog of war without a map; wrong maps fixable with a pen; memory decays with time and stress; unreliable narrator; coherent, usable.
17. Secrets by tier; fictional features allowed, labeled, off-switchable, reserved for balance; past runs give rough knowledge (50).
18. Views are render styles with layer toggles; devices gate detail; 2D paper, 3D on a charged phone; comms devices exist.
19. Per-cove heights from one wave parameter, arrival times, two to three waves; propagation animation liked as a later option.
20. Water line at DEM-cell precision; views quantize.
21. Damage graded by depth and construction; persistent aftermath.
22. Flags can be predicted from known elevation and the prediction can be wrong.
23. Fallout fields baked; runtime formula kept as the generator (09).
24. Shelter protection factor per building class from data where possible.
25. Water contamination by source type with time.
26. Solo hiker to small group, all possible; multiplayer open (52).
27. People as groups and individuals with all states; danger from desperate people.
28. Herds for herding animals, individuals for non-herding; sea life with schools and fishing within reason (57: habitat fields rather than moving schools).
29. Resources as category quantities derived from data with overrides.
30. Boats as individual entities; endings by boat, aircraft or signaling.
31. Buildings merged from both sources with height, use, capacity, material class, contents.
32. Commercial release; use what is legal; no raw imagery shipped; data modeling and rendering only.
33. Hand overrides in a separate file with stable ids.

## Round 2

34. Single source for the tsunami: a submarine slide at the shelf edge, triggered through a quake on the stressed Palos Verdes fault; the blast's own wave is not the tsunami (05).
35. No EMP in the base scenario; EMP permutations parked as a modifier (precursor or second strike).
36. GPS works throughout.
37. Starts at Two Harbors or Avalon; charter to anywhere at a steep price out of the kit budget.
38. Crossing simulated; destinations as scenario states; rescue responsive to signals with a late baseline sweep.
39. Infrastructure dependency graph.
40. Escape attempts at any time.
41. Opening at real time, pausable; fallout through wait actions with interrupts.
42. Weather tapes from real records with an offshore-wind eligibility rule.
43. Season fixed; ferry or charter sets the hour.
44. Needs: hydration, calories, sleep, core temperature, injury, dose, stress; pack weight matters.
45. Death: one life for solo by default, lead mode optional, one life each in multiplayer (09).
46. Memory model with error radius, pins, no fading of seen terrain, mild false memories.
47. Route planning as in 15.
48. Structured map annotations.
49. Perception crisp, belief faded, truth never beyond senses.
50. Meta-progression as rumors.
51. Devices as entities with layers, precision, power, range, dependencies; satellite messengers rare.
52. Multiplayer shape by judgement with adversarial review (09, 10).
53. Party and groups by judgement with review; people can be set up to wait in designated safety; big boats carry many at a fuel cost.
54. Conflict as abstract encounters with real weapon sources.
55. Vulnerable people as simple modifiers; rescue scoring weighted.
56. Boats drift, beach, sink; towing.
57. Fishing from habitat fields and species tables; contamination over time.
58. Licensing handled at the end; think ahead; do not limit development.
59. Election hidden, rolled at creation; false professors and converts possible; ratios 1 in 6.
60. Calling through means; recurring profession opportunity.
61. Providence only through natural means; nothing visible.
62. No Sabbath mechanic; Sunday exists on the calendar only.
63. "Thoughts" explored within reason: canceled plans and backed-out choices at light weight.
64. Repentance needs confession, fruit and restitution; all of it opaque and unprompted.
65. Balance confirmed: obedient believer best expected outcome with more trials; chastening until repentance; unbeliever flat.
66. Prayer types free with no feedback; NPC faith never shown.
67. Blast time fixed per seed, unknown to the player, in the first afternoon or evening; ferry or charter sets time ashore.
68. Three budgets as difficulty, spent before departure; money useless after the flash.
69. One severity knob: slide volume; yield fixed.
