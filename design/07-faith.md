# 07. The providence director

Decisions: 59 to 66 (round 2), 62 no Sabbath mechanic, 64 opaque and unprompted, 65 balance confirmed.
Theology: Reformed. Election precedes faith; calling is effectual; the elect persevere; the Father disciplines
sons (Hebrews 12:5 to 11) and those without discipline are not sons (12:8); repentance bears fruit; vengeance
belongs to the Lord (Romans 12:19); causing a believer to stumble is the millstone (Matthew 18:6). Scripture in
the world is KJV (public domain).

## Visible surface

Exactly these things are visible to the player, ever:

- Character creation: "Are you a believer? Y/N". No follow-up, no explanation.
- The verb **pray** is always available, with four sub-types: petition, confession, thanksgiving, intercession
  (for a named person). It returns nothing. No cooldown, no counter, no log entry.
- Profession opportunities: an ordinary dialogue option or a quiet prompt ("He asks if you believe"). They
  recur only for one hidden case (below).
- In-world objects: Bibles (hotel rooms, homes, the churches in Avalon), church buildings, believing NPCs,
  Sunday gatherings where a church still stands. Nothing is highlighted.

Nothing else: no stats, no notifications, no achievements, no epilogue reveal, no event text that differs from
ordinary event text. A player who is not paying attention sees a survival game.

## Hidden state per person

| field | type | set by | notes |
|---|---|---|---|
| `elect` | bool | rolled at creation | player: 5 in 6 of Y answers, 1 in 6 of N answers; NPC: base rate by visible religiosity, never determined by it |
| `profession` | none, professing, apostate | the Y/N; later opportunities | the only field the player ever chose |
| `called_at` | time or null | director | effectual calling; set at creation for elect + Y |
| `regenerate` | bool | derived: elect and called | the believer path runs only for regenerate people |
| `standing` | float >= 0 | ledger | unrepented weight; decays only through repentance |
| `holiness` | float >= 0 | director | grows with obedience and endured trials; raises trial rate and standards |
| `ledger[]` | records | moral events | `{t, domain, weight, target, intent_only, repented, restitution}` |
| `trials[]` | records | director | `{kind, t_start, t_deadline, domain, condition, outcome}` |
| `prayers[]` | records | the verb | `{t, type, target}`; never shown |
| `means[]` | records | perception | exposures to means of grace: believer NPC, Bible read, church entered, Sunday gathering |

A false professor is `profession = professing, elect = false`: the game runs the unbeliever path for them with
the believer's screens, and never says so. An elect N is `elect = true, called_at = null`: the unbeliever path
until calling.

## Moral ledger

Domains (decision 62, no Sabbath): theft; violence beyond defense; deceit; broken promises (any accepted
request from an NPC is a promise); abandoning the vulnerable; harming or mocking believers; and the positive
domains mercy and sharing, prayer and thanksgiving. Each action in the game that touches a domain carries a
weight in its data (`moral: {domain, weight}`), so the ledger is filled by the ordinary action system, not by a
separate judge. Positive domains reduce `standing` slightly and raise `holiness`.

"Thoughts" (decision 63, within reason): a planned order in a negative domain that is canceled before execution
writes an `intent_only` entry at one fifth weight; a dialogue option selected and backed out of counts the same.
Hovering counts for nothing. Repeated intent entries in one domain within a day merge into one.

## The director

Runs once per game day at a random hour and on every ledger write. It never acts directly on the world: it
only chooses among means the world already has, so every outcome has a natural explanation.

Means available to it, in order of preference: which weather-tape segment plays next (single player only),
placement and timing of item finds, NPC dispositions and arrivals, timing of already-possible events (a boat
breaks loose now rather than later, an engine fails on the dock rather than mid-channel), encounter rolls,
skill checks at the margin.

### Regenerate person

- `standing` above a threshold: schedule **chastening** in the same domain, proportional, through means, never
  lethal on its own, always paired with a way to repent (the stolen thing can be returned, the abandoned person
  can be found again, the deceived party can be told). Repeats on the daily tick until repentance.
- `standing` low: with probability rising in `holiness`, schedule a **growth trial**: a hardship with a path
  through it. Enduring it (reaching the end without a ledger entry in its domain) raises `holiness` and pays a
  **benefit** through means: the tape turns favorable, provision appears where it could plausibly be, an NPC
  decides to help, a skill check at the margin passes.
- Prayer: petition raises the odds of favorable means within a window; confession clears `standing` only when
  followed by fruit (no ledger entry in that domain for N days) and restitution where possible; thanksgiving
  nudges `holiness`; intercession applies a small favorable bias to the named person.
- Balance target (65): more trials, best expected outcome when obedient; chastening until repentance when not.

### Not regenerate (unbeliever, false professor)

Nothing. No trials, no chastening, no answers. Natural consequences only. Flat run.

Exception, applies to everyone: **judgment** for grave harm to a believer (killing, spiritual sabotage that
causes a believer NPC to fall, betrayal to the desperate). Judgment is not discipline: it has no repentance
pairing and one severe natural-means consequence. This is my reading of "vengeance is mine" next to "the dog
in the yard": the unregenerate are not disciplined, but they are not immune to judgment. Confirm or strike.

### Elect but not yet called

Each exposure in `means[]` rolls for calling with a probability that rises with each exposure, so calling is
certain within a bounded number of exposures (irresistible, through means). On calling: `regenerate = true`,
the prayer verb becomes live, and a profession opportunity recurs (an NPC asks, a found Bible prompts, a quiet
prompt after prayer) until the answer is Y. The game never announces the change.

## Multiplayer

State and director are per player. In multiplayer the weather tape is shared and off limits to the director;
it uses personal means only (the player's own finds, encounters, gear, NPC dispositions toward them). One
player's chastening must never land on another player.

## Content it needs from the data pack

- Every action template tagged with `moral` where it applies (theft, violence, deceit, promise, abandonment,
  mercy, sharing).
- NPC records with visible religiosity and the hidden fields above.
- Means-of-grace features: churches (Avalon has them, Two Harbors has none), Bibles as items with a placement
  rate per building use (hotel rooms high), believer NPCs by base rate.
- Trial and chastening templates expressed as ordinary events with a domain tag and a repentance pairing.

## Development aid

A dev-only overlay shows the hidden fields and the director's queue. It does not ship.
