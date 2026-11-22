# Vincent's Pokémon Rejuvenation guide — standing rules

Read this first, every session. It holds the rules Vincent has set; `NOTES.md` is the history log (long, append-only).
Live guide: https://claude.ai/artifact/DvaTJ8A4uqwsyDihPii6DS (publish `output/chapter8_report.html` to that URL).

## Workflow: one command per export (~80s: the 5 engine runs run in parallel; TIMING=1 prints the slowest steps)
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
- Rejuvenation V14, **Chapter 9** (since 14 Nov), Classic mode, 8 badges, **level cap 60** (state.json cap/chapter; LEVELCAPS in
  SystemConstants.rb: 9th badge → 65). Ch 9 hard fights, in order: Dark Gardevoir (boss, Melia), Rift Garbodor (boss, Melia),
  Karrina, Spector (day / night), Spirit Jenner, Amanda, Erick (gym). Keys in gamedata.FIGHTS / bosses.CH9.
- Every fight is scored with FULL legal movesets vs the actual targets (resistances!) and the field's game-code mechanics
  (scripts/team/fights/*_eval.py). Lesson 13 Nov: Venoshock picked into targets that all resist it.
- Never swap a status move (Sticky Web, Will-O-Wisp, Glare…) for an attack without measuring the attack's MARGINAL gain
  (vs the member's other attacks, foe by foe) against what the status move does in each fight. Lesson 13 Nov: Mud Barrage /
  Shock Wave were picked over Sticky Web / Will-O-Wisp and added almost nothing. Everyone is levelled to the cap.
- **Debug mode:** any owned Pokémon can be levelled, re-natured, re-EV'd, ability-capsuled, taught any legal move,
  instantly. NEVER filter or rank by build effort. Pick purely on battle merit.
  EVs stay LEGAL (Vincent, 20 Nov): 510 total, 252 max per stat; no over-legal spreads even though debug allows it.
- Legal moves (16 Nov): level-up ≤ cap, Move Relearner, egg, Ch1–8 TMs (allowed_tms.json), tutors ≤ 8 badges (the game has
  no 8-badge tier, so ≤ 7 in practice). Evolution items from Ch1–8 (adds Razor Claw, Prism Scale, King's Rock, Dragon Scale).
  No Life Orb, no Megas, no trade evolutions. Trick Room TM not owned: only Oranguru / Porygon-Z learn Trick Room.
- Items: UNLIMITED (Vincent, 14 Nov) except Leftovers and Life Orb. Prefer reusable items: the type booster of the main
  attack (Charcoal, Mystic Water, Miracle Seed, Magnet, Never-Melt Ice, Black Belt, Poison Barb, Soft Sand, Sharp Beak,
  Twisted Spoon, Silver Powder, Hard Stone, Spell Tag, Dragon Fang, Black Glasses, Metal Coat, Fairy Feather, Silk Scarf).
  Single-use only Focus Sash (frail / fast leads) and Sitrus Berry (bulky support). No gems; no Choice items or Assault
  Vest (they block Protect, which is always the 4th move). Crests where owned.

## Team rules (chapter rules)
- **Core of 4 + 2 swaps (Vincent, 16 Nov):** Vincent picks ONE core of 4 with a playstyle identity from the Cores tab
  (scripts/team/cores.py; Balance/tempo preferred, but strongest wins). It stays all chapter; each fight adds 2 swaps
  (boss hard counters, one dedicated counter per foe). Until he picks, the Dark Gardevoir fight six stays.
- Only HARD fights count: bosses and real story fights (gym leaders, executives, named story trainers), never grunt
  fodder. The checked list is `HARD_WHY` / `NOT_HARD` in `scripts/team/sheet_extras.py`.
- (b) No attack type the hard-fight opponents actually use (move types, after field changes) hits 3+ of the six
  super-effectively. (c) Every such type is resisted by ≥ 1. Types in 2+ hard fights or on a boss are hard rules;
  one-offs are a tiebreak. (d) Every opposing Pokémon is hit super-effectively OR one-shot; at most 2 misses.
- (e) **Synergy / one identity:** the six has ONE stated game plan (e.g. "slow hard hitters + speed control"), with
  enablers and beneficiaries on the team, and NO dead pieces: every conditional ability or move needs its enabler on
  the team (Swift Swim/Rain Dish → rain setter; Dry Skin counts as live for its Water immunity; Chlorophyll/Solar Power → sun; Sand Rush/Force → sand;
  Slush Rush/Ice Body → snow; Surge Surfer → Electric Terrain…). No anti-synergy (e.g. Glare or fast mons under Trick
  Room). Owned weather/terrain setters (16 Nov): Drought Ninetales, Snow Warning (Ninetales-Alola, Vanilluxe, Aurorus,
  Abomasnow), Grassy Surge Glalie-A, Electric Surge Pincurchin. No Drizzle / Sand Stream. Checked by checks.py.
- **Picked core (16 Nov): Balance / tempo** = Arcanine-Hisui (Intimidate) · Golisopod-Aevian (Skill Link, SD) · Gholdengo
  (Good as Gold, Thunder Wave) · Vaporeon (Water Absorb, Haze). #1 core score of 89,985 cores from the top 40 across all tier
  lists; no shared weakness. Swaps now: Copperajah + Muk-Alola (Dark Gardevoir). The core resists no Dark / Ghost:
  every fight's 2 swaps must bring a Dark/Ghost resist when that fight uses them (Muk-Alola resists both). checks.py: core (b) +
  fight six (b)(c) vs its own fight's types. state.json `core` holds the 4.
- **Team tab = party order (Vincent, 21 Nov):** 1 Gholdengo (Core 1 · Lead: leads singles + left slot in doubles), 2 Arcanine-Hisui
  (Core 2 · Lead partner), 3 Vaporeon (Core 3 · Mid game), 4–5 the fight's 2 swaps (Flex 1 / Flex 2 · Battle start | Mid game |
  Closer: Battle start = that fight's planned lead, Closer = has a setup move), 6 Golisopod-Aevian (Core 4 · Closer, always last).
  state.json `core` order = [lead, lead partner, mid, closer]; team = core[:3] + swaps + core[3:]. Flexes are ALWAYS a
  battle-start swap-in, a mid-game piece or a secondary closer. Hard-fight leads and matchups live on the Fights tab
  (fight_plans `leads`, must survive the opening Pokémon); a core member leads there when it is better than a swap.
- **Core roles (Vincent, 21 Nov):** core = 2 leads (slot 1 leads singles AND the left slot in doubles: Gholdengo; slot 2 =
  Arcanine-Hisui), 1 mid-game piece (Vaporeon), 1 dedicated closer (Golisopod-Aevian, SD: beats more remaining foes than any
  speed-boosting closer incl. DD Crawdaunt). The 2 swaps per fight are mid-game counters / immediate switch-ins or a
  secondary closer played before the core closer. One-six mode (`one_six`) exists in fight_plans.py but is OFF: Vincent
  prefers core + 2 swaps per fight (21 Nov).
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
9. **One dedicated counter per opponent Pokémon** (Vincent, 14 Nov): the six must pair every foe with a DIFFERENT member
   that deals >= 90% (or outspeeds and OHKOs) and takes < 70% (scripts/team/fights/counters.py, best one-to-one pairing).
   Pick the six by that pairing (counters first, then total quality), not by one member covering several. The Fights tab
   lists each foe and its counter (counters_tab.py).

## Ideal builds (Vincent, 17 Nov)
- scripts/team/ideal_builds.py → team/ideal_builds.json, run by update.py: every owned Pokémon's ideal build from
  Rejuvenation's OWN trainer sets (trainertext, same species+form, level-weighted; crested sets weigh more when he holds the
  crest) + Smogon (singles + doubles), legal moves only. Rules builds win (Lapras-A, Gastrodon, Ceruledge, crested Furret =
  Follow Me / Super Fang / Baton Pass support), then the party's own builds (state moves). The engine (run.py), fight evals
  (FIXED / FIXED_AB) and Dex sheets all score these builds.
- Win conditions per foe (fight_plans.py WINCON: setup, healing, screens, Trick Room, sleep, Perish Song) need a named answer
  on that fight's six; answers weigh into the swap pick (+5 each); a swap may be TAUGHT the answer (shown "teach X"), which
  update.py writes into that swap's build when the fight becomes next. Fight cards show green/red answer chips.
- Auto next fight: after --beat, update.py sets state.fight to the next unbeaten Ch9 fight, team = core + its plan swaps
  (plan_builds per fight override, e.g. Garbodor Gastro Acid Muk), To do cards follow. Cap rises to 65 once Erick is beaten.

- **Boss simulator (18 Nov):** scripts/team/fights/boss_sim.py plays every boss fight turn by turn (one active Pokémon in
  Melia fights, Melia's team as a simple partner from gamedata.PARTNER, boss healing: Poison Heal / Black Sludge (x2 on
  Corrupted Cave) / Sitrus / drains, field poison, Gastro Acid / Heal Block / Knock Off / Clear Smog / Unaware / one setup turn,
  boss setup move, Reflect after a break, overflow lost at breaks). fight_plans.py runs it solo AND with the partner for
  boss fights: it decides near-equal pairs when there is no hand plan; results go in fight_plans.json `sim` and in CHAT only.
- **Crests (18 Nov, game code):** Zoroark Crest = ability + STAB types of the last party member → scored with the BEST
  possible slot-6 partner (run.py, `zoro_partner`, shown on the Crest tab); Furret Crest = Substitute on entry for 1/4 HP
  (engine: survives one extra hit). Zoroark Crest copy target (game code, Battle.rb illusionChoice): the LAST LIVING mon in the
  current party order, re-checked on every switch-in (a faint moves it up); ability copied unless in PBStuff ABILITYBLACKLIST; Typhlosion Crest (form 0) = Atk equals SpA + contact moves hit twice, 2nd at 0.3x
  (Battler.rb pbNumHits / Battle_Move.rb bondmult) → crests.py x1.3 on single-target contact moves. Crested mons pick their own
  attacks in the crest run (ideal builds don't override them).

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
- **Every To do / build card names the best item** (Vincent, 14 Nov): the booster of its main attack's type unless the job
  says Sash / Sitrus (make_report5 BOOSTER).
- Gastrodon (doubles): Earth Power / Muddy Water / Yawn / Protect, Modest 252 HP / 252 SpA, Sitrus.
- Ceruledge: Active Swords Dance sweeper (Jolly 252 Atk / 252 Spe, Bitter Blade / Shadow Claw / SD / Protect, Sash).

## Boxes
- Export order: Party (6), Overflow A–Z, an optional unsorted staging box, Active A–Z.
- Active bar: A tier (score ≥ 0.53) and species not already in Party/Active. Boss specialists stay in Active only
  while their fight is still ahead. Meowscarada (starter) and Ceruledge always stay.
- Every staging Pokémon gets a verdict: Active or Overflow.

## Guide page
- Clean, a guide not an essay: bullets, no paragraphs; explanations go in chat, not on the page.
- Tabs: Team · Fights · Cores · To do · Boxes · Tier list · Crest tiers · Aevian tiers · C&A checks.
- **App look (Vincent, 17 Nov): it must look like an app, Pokémon themed.** scripts/team/theme.py runs LAST (after tabs.py) and
  only reskins: Rotom-Dex red app bar, party slots with level bars + "Next battle" card on Team, bottom tab bar (phone) / side
  rail (desktop) with 6 tabs (Team, Fights, Cores, To do, Boxes, Dex = the 3 tier tabs behind a switcher; C&A checks behind the
  shield icon), scoring legends folded into "How this works". New sections/tables need a phone layout (stacked rows).
  **No caption text (Vincent, 17 Nov):** only names, builds, key numbers and the turn plan show; descriptive captions are
  removed or folded (theme.py trims them; lineup notes become short role chips like "Lead · Bar 1 counter").
  Hidden from the page (17 Nov, data kept in team/*.json and given in chat when asked): the fight lineup card + turn plan, the
  Team rules panel, "How to play it", the Fight plans table, the fight cards' description line + threat notes, and on Cores cards the score / identity text / role line / bullets.
  Explain plans in chat, not on the page.
- **Sprites (17 Nov):** Vincent's Graphics/Battlers (2x2 sheets: front normal/shiny, back normal/shiny) live in
  workspace/gamedata/Battlers (out of git; ask for Battlers.zip again in a fresh session). scripts/team/sprites.py: tag()
  emits a CSS class; theme.py embeds each used sprite ONCE. Shown on party cards (shiny if his mon is), Cores, Fights
  (foes + counters; boss forms from bosstext), Dex rows. Empty-cell sheets fall back to the other cell.
- **Boxes tab (17 Nov):** "Move in" (green) / "Move out" (red) lists in box-number order from team/actions.json; full
  rosters folded below. **Dex (17 Nov):** tap a row → detail sheet (stats, best build, Ch9 foes it counters).
- Tier tabs (16 Nov) share ONE blended scale (scripts/team/tier_all.py → tier_tabs.py): 0.6 × Ch9 fight percentile +
  0.4 × meta (Smogon tier/usage + BST; Aevians by kit OP stars). Cut-offs S .85 / A .76 / B .62 / C .45.
- **Team tab (17 Nov):** only "Your party": one card per member (slot, Core/Swap · role, types, level bar, ability · nature, EVs,
  item, 4 moves, open to-dos) + the Next battle card. The old team table is folded into the cards by theme.py.
- **Cores tab (17 Nov):** compact grid, one card per style. **Role order (Vincent, 21 Nov):** every core is built and shown as
  1 Lead (singles + left slot in doubles) · 2 Doubles lead · 3 Flex · 4 Closer (cores.py order_roles: role-fit scores
  s_lead / s_partner / s_flex / s_closer, +0.15 × fit in the core score; the closer must have a setup move or boosting ability,
  else −0.05; weather / terrain / Trick Room setters must take slot 1 or 2). Swaps replace a member IN THE SAME ROLE at the
  same tier or higher (slot_ok). **Cores = OVERALL strength + synergy as a self-sufficient 4 (Vincent, 21 Nov, VGC bring-4 logic),
  NOT Ch9 matchups** (those are the 2 flexes' job, so key pieces don't churn): core score = 0.30 strength (the tier score: legal
  builds + meta) + 0.20 defence (no shared weakness, every one of 18 types resisted) + 0.10 offensive coverage + 0.10 answers
  + 0.15 identity + 0.15 role fit (role scores use strength; the closer is rated by setup size: +2 moves > DD-type > Bulk Up /
  Curse). No Ch9 counter term, no Ch9-type gap penalty. Fight-specific core checks: scripts/team/arch_fights.py (chat only).
  Consistency (Vincent, 21 Nov): every style shows ITS BEST 4 by the same score; Vincent's
  core is NOT forced onto the Balance card ("your core" badge only when a card matches it). Swaps shown only when notable:
  ONE role changes, same tier or higher, core score within 0.01 of that style's best, one per role. Each row shows its role label; members with tier chips, key piece (the setter) marked; the alt core's
  replacements sit greyed on the right of the member they replace (⇄ + tier chip). Swap rule (Vincent, 18 Nov): every
  replacement is the SAME tier or higher than the member it replaces (paired by tier); no such alt → no swap shown. Kept members have nothing on the right. No builds there (they live on Team / To do).
- **Fights tab (17 Nov):** one collapsible card per remaining fight, built by theme.py from team/fight_plans.json (single
  source; the old hard-fights table, opener cards and counter tables are replaced). Header: number, name, format/boss/field
  chips, "Needs a plan" badge (no x/n count). Body (Vincent, 21 Nov): Bring (the 2 swaps) and Field only: type pills (Team-tab
  colours) per multiplier, green ▲ ×1.5 / red ▼ ×0.5, notes like "special moves only", field chip, then "Your moves here": one
  line per move of the six the field changes (▲/▼ ×N, sprite, name, move, why: type pill or "field bonus" = the field's
  damageMods, e.g. Haunted Field bone moves). Game rule (Battle_Move.rb / Battle_Field.rb, verified 21 Nov): damage x move bonus
  (damageMods, any category) x max(flag bonus [sound / slicing...], type bonus [only if its typeCondition holds]); x0 = the move
  FAILS (isMoveValidOnField?), shown "✕ fails" (Murkwater Surface: Ground moves). Classic mode = full field strength (Story halves). NO Lead row and NO foe → counter list (data stays in fight_plans.json, plans go in chat).
  TRIAL rows (Vincent, 21 Nov, may be removed), upcoming fight only: "Faster" = foes faster than every member of the six
  (sprite + Speed, plus your fastest); "Watch" = each foe's trick → your answer (fight_plans win conditions, hazards with who
  is immune, Focus Energy). Team tab trial: party cards show a red line for moves the next fight's field weakens or blocks.
  Swap roles are NOT forced (Vincent, 21 Nov: he plays the 2 swaps by ear).
  Spector day hand builds (22 Nov, state plan_builds + items): Oranguru = Trick Room / Psychic / Safeguard / Protect, Inner
  Focus (Fake Out can't stop TR), Sitrus; Zoroark-H = Bitter Malice / Nasty Plot / Taunt / Protect (Bitter Malice over Shadow
  Ball: -5 power, 100% Atk drop on physical Houndstone / Mega Banette). state `items` {name: item} overrides the build item.
  Trick Room on a FLEX = situational tool: checks.py anti-synergy is a warning (no Thunder Wave while TR is up); blocking only in the core.
  Fight icon = the fight's ace (last Pokémon) or the boss sprite (21 Nov; trainer portraits need Vincent's Graphics/Trainers).
  Boss fights also keep the bar plan. Only the next fight shows (Vincent, 21 Nov); the rest fold under "Later fights".
  **Boss bar plan (Vincent, 20 Nov):** for the NEXT boss fight the foe→counter list is replaced by a bar-by-bar plan of the
  real six (scripts/team/fights/bar_plan.py → team/bar_plan_<fight>.json, run by update.py): each bar shows the boss's
  types / item / stat stages / new moves, then who is in and what they click (moves named, our boost stage), with Hit (+0) /
  Takes bars. It searches the switch-in order turn by turn: speed, Unaware, Swords Dance / Curse / Recover, Gastro Acid /
  Knock Off vs healing, Sitrus, drains, field chip, recoil vs Sash, Rocky Helmet, overflow lost, free switch after a faint,
  Melia's chip; worst case = the boss always hits OUR mon. Rows: Field (the field's real multipliers + chip), Boosted
  (our moves the field boosts), Speed, Key (the carrier + backup). Header shows "Plan ✓" instead of x/n.
  **Fight plans (17 Nov):** scripts/team/fights/fight_plans.py (run by update.py after remaining_eval.py per fight, core scored
  with its REAL builds via FIXED) picks each fight's best 2 swaps (one-to-one counters incl. one setup turn, rules (b)(c) vs that
  fight's types) and its lead(s) (must survive the opening Pokémon). Boss damage is per health bar. The fight in `state.fight`
  keeps its hand-checked six. checks.py: lead check is blocking; rules and counters per plan are warnings.
  Hand plans: state.json `plan_swaps` {fight: [2 names]} and `plan_leads` {fight: [lead]} override the search (used when the
  fight protocol was done in chat, e.g. Garbodor). Melia partner fights (darkgardevoir, garbodor): ONE lead (she has the other
  slot). Boss fights (bars of one boss): the same member may take several bars. Rule 9 as written: an outspeeding one-shot
  counts whatever it would take.
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
