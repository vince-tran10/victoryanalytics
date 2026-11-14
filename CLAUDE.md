# Vincent's Pokémon Rejuvenation guide — standing rules

Read this first, every session. It holds the rules Vincent has set; `NOTES.md` is the history log (long, append-only).
Live guide: https://claude.ai/artifact/DvaTJ8A4uqwsyDihPii6DS (publish `output/chapter8_report.html` to that URL).

## Workflow: one command per export
1. Copy the uploaded export, then run from the repo root:
   `python3 scripts/team/update.py <export.txt> [--beat <fight,...>] [--fight <boss>|none] [--staging A-B --active N] [--quick]`
2. Check the printed box layout ("around Active start"). If it's wrong, re-run with `--staging/--active` (saved in state).
3. Publish `output/chapter8_report.html` with the Artifact tool (same URL), append 2–5 lines to `NOTES.md`, commit, push.
4. Reply in chat: what changed, green/red box moves, To do cards, team verdict. Short, bullets, no paragraphs.
State (beaten fights, the six and its moves, box overrides, last export, file counters) lives in
`workspace/team/state.json`. Fight keys: see `scripts/team/bosses.py` (eli, geara, giratina, holly, manaphy, factory, amber…).

## Game data (exact, from Vincent's game files)
- Rejuvenation's own definitions (Classic): `workspace/gamedata/*.json`, converted from his `Scripts/Rejuv/Definitions/*.rb`
  by `ruby scripts/gamedata/to_json.rb <Definitions dir> workspace/gamedata <Scripts dir>`. Kept OUT of git (public repo):
  a fresh session must ask Vincent to re-upload the Scripts zip. update.py warns if missing (then walkthrough data is used).
- `scripts/gamedata/gamedata.py`: hard fight → exact trainer/boss entries (`FIGHTS`), boss phases (N shields = N+1 full
  HP bars, onBreakEffects → moves/form/stat stages/field per bar), SOS mons. `fields.py`: exact field multipliers,
  second types (typeAddOns/typeMods), field changes. `compare.py`: game vs guide diff (feeds the C&A tab).
- Verified game rules: unlisted trainer EVs = min(85, lvl×1.5), IVs = 10; Concert Venue hype 1 = min rolls (85%).

## Game facts
- Rejuvenation V14, Chapter 8, Classic mode, 7 badges, level cap 55.
- Every fight is scored with FULL legal movesets vs the actual targets (resistances!) and the field's game-code mechanics
  (scripts/team/fights/*_eval.py). Lesson 13 Nov: Venoshock picked into targets that all resist it.
- Never swap a status move (Sticky Web, Will-O-Wisp, Glare…) for an attack without measuring the attack's MARGINAL gain
  (vs the member's other attacks, foe by foe) against what the status move does in each fight. Lesson 13 Nov: Mud Barrage /
  Shock Wave were picked over Sticky Web / Will-O-Wisp and added almost nothing. Everyone is levelled to 55.
- **Debug mode:** any owned Pokémon can be levelled, re-natured, re-EV'd, ability-capsuled, taught any legal move,
  instantly. NEVER filter or rank by build effort. Pick purely on battle merit.
- Legal moves: level-up ≤ 55, Move Relearner, egg, Ch1–7 TMs, tutors ≤ 7 badges. Evolution items from Ch1–7 OK.
  No Life Orb, no Megas, no trade evolutions. Chapter 8 pickups wait for the end-of-chapter review.
- Items owned: type boosters (Black Belt, Metal Coat, Mystic Water ×3, Soft Sand, Hard Stone ×2, Never-Melt Ice ×2,
  Black Glasses ×3, Poison Barb, Magnet, Fairy Feather, Dragon Fang), Sitrus Berries, Focus Sash ×9, Lum Berry, crests.

## Team rules (chapter rules)
- One six for the whole chapter. Swap only for a true hard-counter boss (fight mode), then swap straight back.
- Only HARD fights count: bosses and real story fights (gym leaders, executives, named story trainers), never grunt
  fodder. The checked list is `HARD_WHY` / `NOT_HARD` in `scripts/team/sheet_extras.py`.
- (b) No attack type the hard-fight opponents actually use (move types, after field changes) hits 3+ of the six
  super-effectively. (c) Every such type is resisted by ≥ 1. Types in 2+ hard fights or on a boss are hard rules;
  one-offs are a tiebreak. (d) Every opposing Pokémon is hit super-effectively OR one-shot; at most 2 misses.
- (e) **Synergy / one identity:** the six has ONE stated game plan (e.g. "slow hard hitters + speed control"), with
  enablers and beneficiaries on the team, and NO dead pieces: every conditional ability or move needs its enabler on
  the team (Swift Swim/Rain Dish → rain setter; Dry Skin counts as live for its Water immunity; Chlorophyll/Solar Power → sun; Sand Rush/Force → sand;
  Slush Rush/Ice Body → snow; Surge Surfer → Electric Terrain…). No anti-synergy (e.g. Glare or fast mons under Trick
  Room). Weather teams aren't realistic yet: no Drizzle/Drought/Sand Stream owned. Checked by checks.py.
- Current identity (13 Nov, remaining fights Holly/Manaphy/Factory/Amber): block their main attack type and hit back SE —
  Flash Fire Chandelure (Amber all-Fire), Dry Skin Heliolisk (Manaphy/Beach Water), Levitate Vikavolt + Whiscash (Factory Electric);
  Glare + Fake Out for tempo.
- **One structure for singles AND doubles** (most battles are singles): party order = plan. Slot 1 leads singles, slots
  1–2 lead doubles. Leads must survive the opposing leads' hits in every hard fight (checked vs exact game lead order).
  Current order: Vikavolt, Chandelure, Ludicolo, Whiscash, Crabominable, Heliolisk.
- Then rank by battle score (singles count double).
- **Fields are a core factor (Vincent, 10 Nov): exploit them.** Score every fight with its full field mechanics from the game
  code (boosts, added types, end-of-turn field damage like Volcanic Top eruptions and who is immune, field changes), favour
  Pokémon the field boosts or protects, and for partner/tag battles count double-targeting and spread moves hitting the ally.
  Lesson: Geara & Zetta (Volcanic Top) was lost with a six picked without eruption damage or tag-battle targeting.
- Meta / Smogon builds preferred (SV + National Dex data in `workspace/smogon`; doubles data for doubles roles).

## Fight protocol (Vincent, 14 Nov — do this BEFORE recommending any team or lineup)
Why: Geara, Giratina, Holly and Manaphy each took several losses because the six was picked from a one-hit, +0-stage
damage score and the fight's real win condition was only read after Vincent lost. The data was in the game files.
1. **Fight brief from game data** (trainertext / bosstext / fieldtext + game code): every foe's moves, ability, item,
   level, EVs; boss shields, onBreakEffects (stat changes — index 1 Atk, 2 Def, 3 SpA, 4 SpD, 5 Spe — field/moveset/item
   changes, status cure), SOS mons, delayed actions; trainer effects and items (crests in the trainer's item list apply);
   field notes incl. end-of-turn effects; partner team; who controls which slot; fights that run back to back.
2. **Win-condition list:** for every foe name how it beats us — setup (boost moves, Speed Boost, Moxie, Dancer, Take
   Heart), screens, hazards, weather/terrain, priority, status, crests, field damage. Each one needs a named answer on the
   six (Haze / Clear Smog / Roar / Whirlwind, Screech / Scary Face / String Shot on stats it can't restore, Brick Break,
   Taunt / Encore, Unaware, Intimidate, Fake Out, immunity). No answer → the team is not done.
3. **Bosses:** list which stats its boosts/heals/breaks touch and plan drops on the others (Take Heart → Def/Spe drops);
   drops survive shield breaks, status does not; never Haze our own drops away.
4. **Ask Vincent for the community fight page / tips** before finalizing, and use them as input.
5. **Score with the evaluator, then sanity-check the result against 1–3.** Status/utility moves score 0 in the evaluator:
   value them by hand per fight. Verify any mechanic claim in the game code before stating it (Sticky Web never hits a
   mon already on the field; Hidden Power types; who resists the move).
6. **Say what the model does not simulate** for that fight in one line. Never call a six "the best" without it.
7. Give the turn-1 plan and the phase plan (early / mid / late, per boss bar) with the lineup.
8. **The lead only faces their lead.** After that the AI picks its switch-ins, so a late threat (e.g. Xurkitree) can come
   at any point but never turn 1. Never spend the answer to their biggest threat on their lead; keep it healthy in the back.

## Build rules
- **Protect is always the 4th move.** Only exception: Lapras-Aevian (No Guard: Rock Slide / Zen Headbutt /
  Dragon Dance / Sing). Detect etc. count as Protect.
- When suggesting a move, ALWAYS say what it replaces. Setup moves, Yawn, Fake Out, Leech Seed, Trick Room, sleep moves
  stay ONLY when they are clearly better than a coverage/other move for that Pokémon's job (Vincent, 13 Nov); otherwise
  replace them and say why (e.g. Shell Smash + Overheat cancel out). Cut wrong-stat attacks, weaker same-type duplicates,
  or recovery on Regenerator mons first.
- **One answer only:** never "X or Y" for EVs, natures, moves or items. EVs = 252 attacking stat + 252 Spe if base
  Speed ≥ 85, else 252 HP. Nature follows (Jolly/Timid with Speed EVs, Adamant/Modest with HP).
- Judge physical vs special from the moves the Pokémon actually knows.
- Gastrodon (doubles): Earth Power / Muddy Water / Yawn / Protect, Modest 252 HP / 252 SpA, Sitrus.
- Ceruledge: Active Swords Dance sweeper (Jolly 252 Atk / 252 Spe, Bitter Blade / Shadow Claw / SD / Protect, Sash).

## Boxes
- Export order: Party (6), Overflow A–Z, an optional unsorted staging box, Active A–Z.
- Active bar: A tier (score ≥ 0.53) and species not already in Party/Active. Boss specialists stay in Active only
  while their fight is still ahead. Meowscarada (starter) and Ceruledge always stay.
- Every staging Pokémon gets a verdict: Active or Overflow.

## Guide page
- Clean, a guide not an essay: bullets, no paragraphs; explanations go in chat, not on the page.
- Tabs: Team · Fights · To do · Tier list · Boxes · C&A checks.
- **Team tab:** the ideal six with a Status column (Done ✓ per member, always shown) plus the rules panel.
- **Fights tab:** every remaining hard fight: Singles/Doubles, Boss tag, field, why it's hard, lead.
- **To do tab = profile fixes only:** one card per Pokémon listing everything it needs (moves with replacements, EVs,
  nature, ability, item, level). Never two places for the same Pokémon. No box moves.
- **Boxes tab = all box moves:** GREEN = move into Active / the party, RED = move out. A Pokémon moving into Active also
  gets a To do build card.
- Role colours (lead blue / mid amber / closer magenta) only on the exact team forms, never in box lists.

- **C&A checks tab:** automatic pass/fail checks (scripts/team/checks.py, run by update.py; a blocking FAIL means don't
  publish), data sources, corrections from game files, game rules verified in code, known gaps.

## Boss counters (debug mode)
- Use `scripts/team/kyogre_counter.py`'s method: every owned Pokémon × ability × spread × item; total damage dealt
  before fainting (speed order, Sash/Sturdy, recoil vs boss HP, Swift Swim / Dry Skin in weather). It beat Kyogre.
- Give one decisive lineup when asked for "the best". State uncertainty briefly, don't hedge.
