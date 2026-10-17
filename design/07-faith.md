# 07. The providence director

Decisions: 59 to 66 (round 2), 62 no Sabbath mechanic, 64 opaque and unprompted, 65 balance confirmed.
Review findings 5, 6, 15, 16, 17 applied (10-review.md).
Theology: Reformed. Election precedes faith; calling is effectual; the elect persevere; the Father disciplines
sons (Hebrews 12:5 to 11) and those without discipline are not sons (12:8); repentance bears fruit; the Lord
does not hear the one who regards iniquity in his heart (Psalm 66:18); vengeance belongs to the Lord (Romans
12:19); causing a believer to stumble is the millstone (Matthew 18:6). Scripture in the world is KJV.

## Visible surface

Exactly these things are visible to the player, ever, and all of them are offered to every player at the same
rate regardless of hidden state:

- Character creation: "Are you a believer? Y/N". No follow-up, no explanation.
- The verb **pray** is always available, with four sub-types: petition, confession, thanksgiving, intercession
  (for a named person). It returns nothing. No counter, no log entry the player can see.
- Profession opportunities, offered by the world at a fixed visible rate to everyone: each believing NPC asks
  once on first meeting; reading a Bible prompts once per Bible. There is no prompt after prayer. Hidden state
  decides only what an answer does, never whether the question appears.
- In-world objects: Bibles (hotel rooms, homes, the churches in Avalon), church buildings, believing NPCs,
  Sunday gatherings where a church still stands. Nothing is highlighted.

Nothing else: no stats, no notifications, no achievements, no epilogue reveal, no event text that differs from
ordinary event text, no entry in any journal or save export. A player who is not paying attention sees a
survival game.

## Hidden state per person

| field | type | set by | notes |
|---|---|---|---|
| `elect` | bool | rolled at creation | player: 5 in 6 of Y answers, 1 in 6 of N answers; NPC: base rate by visible religiosity, never determined by it |
| `profession` | none, professing, apostate | the Y/N; later opportunities | the only field the player ever chose; `apostate` is defined below |
| `called_at` | time or null | director | effectual calling; set at creation for elect + Y |
| `regenerate` | bool | derived: elect and called | the believer path runs only for regenerate people |
| `standing` | float >= 0 | ledger | unrepented weight; cleared only by repentance |
| `holiness` | float >= 0 | director | grows with obedience and endured trials; raises trial rate and standards |
| `ledger[]` | records | moral events | `{t, domain, weight, target, intent_only, repented, restitution}` |
| `trials[]` | records | director | `{kind, t_start, t_deadline, domain, condition, outcome}` |
| `prayers[]` | records | the verb | `{t, type, target}`; hidden log only |
| `means[]` | records | perception | exposures to means of grace: believer NPC, Bible read, church entered, Sunday gathering |

A false professor is `profession = professing, elect = false`: the unbeliever path with the believer's
screens; the game never says so. An elect N is `elect = true, called_at = null`: the unbeliever path until
calling. `apostate` is a professing, non-regenerate person who answers N at a later opportunity or enters
the harming-believers domain; a regenerate person is never marked apostate.

## Moral ledger

Domains (decision 62, no Sabbath): theft; violence beyond defense; deceit; broken promises (any accepted
request from an NPC is a promise); abandoning the vulnerable; harming or mocking believers; and the positive
domains mercy and sharing, prayer and thanksgiving. Each action template in `actions.json` carries
`moral: {domain, weight}` where it applies, so the ledger is filled by the ordinary action system, not by a
separate judge. Positive domains raise `holiness` only; nothing but repentance lowers `standing`.

"Thoughts" (decision 63, within reason): a planned order in a negative domain that is canceled before execution
writes an `intent_only` entry at one fifth weight; a dialogue option selected and backed out of counts the same.
Hovering counts for nothing. Repeated intent entries in one domain within a day merge into one.

## The director

Runs once per game day at a random hour and on every ledger write. It never acts directly on the world: it
only chooses among means the world already has, so every outcome has a natural explanation.

Means, single player: the whole weather tape, chosen once at run start among eligible dates and never
spliced mid-run; placement and timing of finds inside containers the player opens (`finds` rolls, 08); NPC
dispositions and arrivals; timing of already-possible events (a boat breaks loose now rather than later, an
engine fails on the dock rather than mid-channel); encounter rolls; skill checks at the margin.

Means, multiplayer: encounter rolls, skill margins, and finds inside containers the target player is opening;
NPC attitude toward that player only (`attitude[player_id]` on groups and individuals, 06). The weather tape,
event timing and shared placements are off limits, so one player's chastening never lands on another.

Director-scheduled events enter the shared event log under the ordinary template they mimic (`boat_adrift`,
`find`, `encounter`) with no domain tag. The director's own decisions, prayers and intent entries go to a
per-player hidden log on the host, which is replay input and never part of a journal, save export or client
delta (08).

### Regenerate person

- `standing` above a threshold: schedule **chastening** in the same domain, proportional, through means, never
  lethal on its own, always paired with a way to repent (the stolen thing can be returned, the abandoned person
  found again, the deceived party told). Repeats on the daily tick until repentance.
- `standing` low: with probability rising in `holiness`, schedule a **growth trial**: a hardship with a path
  through it. Enduring it (reaching the end without a ledger entry in its domain) raises `holiness` and pays a
  **benefit** through means: a find where one could plausibly be, an NPC who decides to help, a skill check at
  the margin that passes.
- Grave harm to a believer by a regenerate person is maximal chastening with a repentance path and a
  consequence that stands after repentance (David after Uriah). Never judgment.
- Prayer: petition sets one favorable-odds window flag (idempotent: praying twice in a window does nothing
  more) and is silent while unrepented `standing` in the petition's domain is above threshold; confession
  clears `standing` only when followed by fruit (no ledger entry in that domain for N days) and restitution
  where possible; thanksgiving counts once per day and nudges `holiness`; intercession applies a small
  favorable bias to the named person.
- Balance target (65): more trials, best expected outcome when obedient; chastening until repentance when not.

### Not regenerate (unbeliever, false professor, apostate)

Nothing. No trials, no chastening, no answers. Natural consequences only. Flat run.

Exception: **judgment** for grave harm to a believer (killing, spiritual sabotage that causes a believer NPC
to fall, betrayal to the desperate). Judgment is not discipline: no repentance pairing, one severe
natural-means consequence. Reading: the unregenerate are not disciplined, but they are not immune to
judgment (Romans 12:19 next to Hebrews 12:8). Open to the owner's override.

### Elect but not yet called

Each exposure in `means[]` rolls for calling with a probability that rises with each exposure, so calling is
certain within a bounded number of exposures (irresistible, through means). On calling: `regenerate = true`
and the prayer verb becomes live. The next world-offered profession opportunity (same rate as everyone's)
records Y as profession. The game never announces the change.

## Content it needs from the data pack

- `actions.json`: every action template, tagged with `moral` where it applies.
- NPC records with visible religiosity and the hidden fields above.
- Means-of-grace features: churches (Avalon has them, Two Harbors has none), Bibles as items with a placement
  rate per building use (hotel rooms high), believer NPCs by base rate.
- Trial and chastening templates in `events.json`, each the ordinary template it mimics plus a hidden domain
  and repentance pairing that never leave the host.
- `rules.json` constants: ratios, thresholds, N days of fruit, window length, trial probability curve.

## Development aid

A dev-only overlay shows the hidden fields and the director's queue. It does not ship.
