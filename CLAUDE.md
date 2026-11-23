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
  No Life Orb, no Megas, no trade evolutions.
- **Legality at his story point (Vincent, 22 Nov):** scripts/team/legality.py (run by update.py before scoring) walks each owned
  mon's evolution chain in montext; anything he can't have yet is scored as its PRIOR stage and gets a To do "De-evolve" card
  (make_report5, one card per species). Out now: Gholdengo (999 coins), Annihilape (Rage Fist = 15 badges), Ceruledge / Armarouge
  (Armors) and Porygon-Z (Dubious Disc) = Shayda shop later, Rhyperior (Protector Ch10), Parasect-Aevian (Xen Waste Ch12).
  Electirizer OK (Ch9 / held). Anything the Route 2 trailer sells counts as obtainable (legality.py ROUTE2_TRAILER: Ice / Dusk /
  Dawn / Shiny Stone, Galarica Cuff / Wreath; its stock may grow later in the story), e.g. Slowbro-Galar via the Cuff. Link Heart (= a trade for every trade method, Evolution.rb) is LIMITED: he has 4, used only on S / A tier evolved forms
  (state `link_hearts` = ['Slowking'], regular Slowking; 22 Nov tiers: Porygon2 / Escavalier B, Electivire / Golem / Machamp /
  Alakazam / Dusknoir C); every other trade evolution de-evolves. Engine (LINK_HEARTS env) stops evolving at the last reachable stage. engine.final_form gates
  CollectItem and Rage Fist evolutions. Trick Room TM not owned: only Oranguru / Porygon-Z learn Trick Room.
- Items: UNLIMITED (Vincent, 14 Nov) except Leftovers and Life Orb. Prefer reusable items: the type booster of the main
  attack (Charcoal, Mystic Water, Miracle Seed, Magnet, Never-Melt Ice, Black Belt, Poison Barb, Soft Sand, Sharp Beak,
  Twisted Spoon, Silver Powder, Hard Stone, Spell Tag, Dragon Fang, Black Glasses, Metal Coat, Fairy Feather, Silk Scarf).
  Single-use only Focus Sash (frail / fast leads) and Sitrus Berry (bulky support). No gems; no Choice items or Assault
  Vest (they block Protect, which is always the 4th move). Crests where owned.

## Team rules (chapter rules)
- **CORE BUILDER (Vincent, 23 Nov, later the same day): one main core of 4 + 2 flexes per fight, NO fixed roles.** scripts/team/core4.py
  picks the best GENERAL 4 (no opponent) and shows it on the Builder tab with how it is picked (strength / defense / offense / synergy /
  Aevian, each member's tier + meta + in-game, synergy lines, close alternatives, type check). Flexes (lead, mid or closer) are added per fight:
  the planner LOCKS the core 4 and picks only the 2 flexes for the next fight. Party order: slot 1 = singles lead and left doubles lead,
  slot 2 = doubles lead partner (a flex may take either). Team tab: Core / Flex + role labels and a 'Flexes for the next fight' card
  (opponent, field, format, their lead, each flex's role and why, threats, guide tips). PARTY ORDER (Vincent, 23 Nov): 1 lead, 2 doubles
  lead, then mid game, then closers (flex closer before core-only closer). Tabs: Team · Core (core4.py) · Flex (planner) · Fights · To do
  · Dex · Community. Fights card: name, format, field, their team, field effect, your + / - moves, Flex (the Flex tab's 2 picks).
- **TEAM PLANNER (Vincent, 23 Nov) REPLACES the core-of-4 + 2 flexes.** state mode='planner': scripts/team/planner.py picks the whole SIX
  for the next fight (state.fight) from his POOL = Party + Active box (S/A/B) + S/A he is moving in from Overflow. PRIORITIES (Vincent, 23 Nov,
  after losing again): 1) as many of the six as possible RESIST EACH MOVE THEY CARRY (move-level, field type chart + second types);
  2) every foe hit super effectively or with a field-boosted move; 3) the lead pair resists every attack their two leads carry.
  Planner tab grids: leads vs their leads, their moves vs your six, who hits them hard. Two plans per run: keep the field vs
  break it with a Flash / Dazzling Gleam lead (no-field engine run); field-neutral cmp (+ guide tips, + denied foe seed combos:
  field seeds that switch on Guts / Flare Boost etc. for a NON-lead foe; the engine does not model foe abilities) picks; the break plan
  also tests the keep plan's six. AEVIAN PREFERENCE (Vincent, 23 Nov):
  +1 per Aevian in the six (tiebreak, never over defense). Every move on the six must do something IN THAT FIGHT (Vincent: 'why Wake-Up
  Slap?'): audit each build vs their team before recommending; field seeds can backfire (Haunted Magical Seed burns its holder). planner.move_why() writes a reason per move
  (collapsed 'Why these moves' on the Planner tab) and FLAGS any attack that is the best hit on no foe: zero flags before recommending. Lead spread moves that hit the partner = penalty. Older wording: DEFENSE FIRST (Vincent: a counter that gets one-shot is useless;
  it must heavily resist what they bring): per foe count members taking < 50% from its best move, heavy penalty per one-shot, no attack type
  of theirs hits 3+, every type they use resisted once and their main types twice, a named answer per win condition (Tailwind / TR, setup,
  sleep, Perish trap, spread, Destiny Bond, screens); offense second; leads = the pair that beats their lead pair. Workflow shown on the
  Planner tab (Vincent, 23 Nov): Their team + attacks, GAME PLAN (leads, turn 1 targets, who takes each back foe), Your six with
  max 3 SHORT chips each (cues.py, 1-3 words: green = its job, e.g. Stat reset / Sleep / Spread / Unaware; grey = Immune X, Resists X / Y),
  type check; game plan + checks + alternatives + method folded under 'Details' at the bottom (Vincent: that text is for me, not him). No 'How they win' text. Lost? Ask what beat him and add it as a threat. The old Builder / core rules below are legacy.
  **Tabs (Vincent, 23 Nov):** Team = the six I recommend (planner six, leads first). Planner = an EVALUATION OF HIS BOXES for the next
  fight: the six with collapsed 'Why these moves' + 'Swap options', then 'Your boxes for this fight' (every pool mon graded Great / Good /
  Weak with resists / super effective / one-shot chips), grids, guide tips. Fights / To do / Dex / Community stay, all built from the same six.
  Field breaks only where fieldtext fieldChange lists Flash / Dazzling Gleam. Flagged moves cost -4 each in the pick.
- **WIN-CON ROLE TAGS (Vincent, 23 Nov):** scripts/team/wincon_tags.py tags every Pokemon A Win con / B Enabler / C Wallbreaker / D Pivot-glue / E Field-tech from what its BUILD runs (+ base stats, ability), singles and doubles separately (builder.json 'tags'). Dex: tiles show the letters, filter chips A-E, sheet 'Win-con roles' (one line per tag, '(singles only)' / '(doubles only)'). Next: Core / Flex built from these (singles core A + D + C, flexes B / backup A / E; doubles core 4 + 2 flexes).
- **CORE OF 3 + 3 FLEXES (Vincent, 23 Nov, latest; replaces core of 4 + 2):** state core_n = 3; core4.py (file names kept) picks the best general 3 with the Rejuvenation mindset (self-sufficient, field-agnostic, covers each other, pivot move) + a Singles plan (fast cleaner / bulky pivot / wallbreaker) and a Doubles plan (Fake Out-redirection / spread-speed control / bulky attacker) shown on the Core tab. Planner locks the 3 and picks 3 flexes with jobs: Field hijacker / Boss breaker / Speed control / Counter. Format mindsets (community_inputs.json 'mindset': singles, doubles, rejuv) are scored by planner.py (mindset / mindset_d) and shown on the Community tab + a 'Singles mindset' check on the Flex tab.
- **Speed control + sound (23 Nov, Jenner):** planner.py scores speed control per format (singles: paralysis / priority STAB or SE / TR / Icy Wind; doubles + Tailwind / Bulldoze) on every foe faster than 4+ of the six; core4 synergy +1.5 for core speed control (Slowking-G Thunder Wave). Sound moves: fieldtext key 'soundmove'; Punk Rock x1.5 on Concert / Big Top / Cave (x1.3 elsewhere), halves sound taken; Soundproof immune. Planner uses the engine candidate whose ability = the build's. Concert: sleep fails at Hype 3+.
- **Field type charts (23 Nov, lesson: Haunted Field made Ghost hit Normal neutrally and I missed it):** field rules live in TWO places:
  fieldtext (boosts, accuracy, typeMods, changes) AND the battle code (Battle_Move.rb pbTypeModifier type-chart overrides, Battle.rb
  end-of-turn effects). fields.field_typemod ports pbTypeModifier; engine.chart_eff applies it. Read BOTH before claiming a field mechanic.
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
- **Core now (22 Nov 20:41 export): Toxtricity-Aevian = CORE 1 (Vincent: 'my strongest Pokémon'; Torch Song CONFIRMED learnable in his
  game, engine.EXTRA_LEGAL; build Torch Song / Boomburst / Sludge Bomb / Protect, Punk Rock (sound x1.3, x1.5 on Big Top / Cave / Concert,
  halves sound damage taken; Battle_Move.rb 1846), Timid 252 SpA / Spe, Charcoal; recommend.py now models Punk Rock). Veluza-Aevian left
  the core (box flex). Slot 1 stability: his lead stays suggested when same tier and within 0.10 lead win (one-hit model can't value
  Torch Song's Sp. Atk boosts). Earlier: Veluza-Aevian (slot 1 until 22 Nov 20:41) · Amoonguss (confirmed slot 2: Spore / Rage Powder / Clear Smog / Protect, Modest 252 HP / SpA, Sitrus; Clear Smog over Sludge Bomb = the core's only stat reset; Pollen Puff not legal) ·
  Slowking-Galar (confirmed slot 3, 22 Nov: Sludge Bomb / Psychic / Shadow Ball / Protect. Chilly Reception out (sets SNOW, helps no one);
  Surf out too (spread move: hits Golisopod-A super effectively in doubles); Shadow Ball = single target, neutral on Steel, x1.5 on Haunted Field), Regenerator, Modest 252 HP / SpA,
  Poison Barb; replaced Alomomola) · Golisopod-Aevian (confirmed slot 4).** Rules (b)(c) per fight are HARD only for types in 2+
  hard fights or on a boss; one-off types (e.g. Spector Ninetales Fire/Ghost) are a tiebreak (chapter_rules.check_set 'minor'). Gholdengo is illegal at Ch9. Older history below. **Picked core (16 Nov): Balance / tempo** = Arcanine-Hisui (Intimidate) · Golisopod-Aevian (Skill Link, SD) · Gholdengo
  (Good as Gold, Thunder Wave) · Vaporeon (Water Absorb, Haze). #1 core score of 89,985 cores from the top 40 across all tier
  lists; no shared weakness. Swaps now: Copperajah + Muk-Alola (Dark Gardevoir). The core resists no Dark / Ghost:
  every fight's 2 swaps must bring a Dark/Ghost resist when that fight uses them (Muk-Alola resists both). checks.py: core (b) +
  fight six (b)(c) vs its own fight's types. state.json `core` holds the 4.
- **Zoroark exception (Vincent, 22 Nov, clarified): a deliberate trade, never a blanket rule.** Only when a crested Zoroark is in
  the six may the order change. update.py order_team(): (a) a slot 3-6 member moves to slot 6 if its copy beats the standard
  last member by > 0.05; (b) a LEAD (slot 1-2) moves to slot 6 only if its copy makes Zoroark OP (gain >= 0.30, ZORO_AB values)
  AND the gain beats the lead-quality loss (lead_q: tier + speed + Intimidate / Fake Out + status immunity) of promoting the best
  slot 3-6 replacement. The Team tab shows ONE small line: who Zoroark copies (ability), order changed / unchanged, leads
  considered. The full analysis stays in state.zoro_note and in chat (Vincent, 22 Nov: keep the page small).
- **Fights tab "Their team" (Vincent, 22 Nov, final):** a 2-column grid of their 6 in party order (1 top-left, 2 top-right, 3
  middle-left…), number + small sprite + name only, their lead(s) outlined. No notes on the page (threat notes go in chat).
- **Flex order (Vincent, 22 Nov):** slot 4 = mid-game flex, slot 5 = closer flex (has a setup move), labels Mid game / Closer only
  (no 'Battle start': he plays the flexes by ear). update.py order_team() enforces it every run.
- **Team tab = party order (Vincent, 21 Nov):** 1 Gholdengo (Core 1 · Lead: leads singles + left slot in doubles), 2 Arcanine-Hisui
  (Core 2 · Lead partner), 3 Vaporeon (Core 3 · Mid game), 4–5 the fight's 2 swaps (Flex 1 / Flex 2 · Battle start | Mid game |
  Closer: Battle start = that fight's planned lead, Closer = has a setup move), 6 Golisopod-Aevian (Core 4 · Closer, always last).
  state.json `core` order = [lead, lead partner, mid, closer]; team = core[:3] + swaps + core[3:]. Flexes are ALWAYS a
  battle-start swap-in, a mid-game piece or a secondary closer. Hard-fight leads and matchups live on the Fights tab
  (fight_plans `leads`, must survive the opening Pokémon); a core member leads there when it is better than a swap.
- **The core four is FIXED and must be the best VGC-style four in the box (Vincent, 22 Nov):** never benched per fight; only the
  2 flexes change per fight (boss / trainer / threat). Never suggest a six that drops a core member. The core is judged in BOTH
  formats: scripts/team/core_formats.py (each member's strength with every remaining hard fight forced to Singles and to Doubles,
  plus the four's doubles kit). 22 Nov result: Vincent's core is #1 in singles (.972) and doubles (.969). Doubles kit gap: no Fake
  Out / redirection (flexes can bring it).
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
**Guide tips (Vincent, 23 Nov): ALWAYS factored in.** Every walkthrough / community tip he sends goes into workspace/team/fight_tips.json
(per fight: tip text + needs); planner.py scores them (+3 per tip met) and the Planner tab shows 'Guide tips: N of M covered' (collapsed)
with who covers each tip. Ask for the tips before planning a new fight (step 4 below).
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
- Active bar (23 Nov, cuts.json RETIRED): Active = the Planner's pool. It keeps every S / A / B (live tier_all, crest tier when the crest is held) and the six; C / D in Active move to Overflow; S / A in Overflow with no copy of that final form in Party / Active move in (make_report5). Never a hand-written cut list. Boss specialists stay in Active only
  while their fight is still ahead. Meowscarada (starter) always stays (Ceruledge rule dropped 22 Nov: not obtainable yet).
- Every staging Pokémon gets a verdict: Active or Overflow.

## Guide page
- Clean, a guide not an essay: bullets, no paragraphs; explanations go in chat, not on the page.
  **ONE THOUGHT PER LINE (Vincent, 22 Nov, ANYTIME):** never join separate thoughts with " · " or commas on the page; each
  thought is its own bullet / line (e.g. Zoroark line, Next battle card). Same in chat replies.
- Tabs: Team · Builder · Fights · To do · Boxes · Dex (tier lists) · C&A checks. **Team Builder tab (Vincent, 22 Nov):**
  scripts/team/builder.py (runs after tier_tabs, before tabs.py) → team/builder.json + section 'sbuild': one card per CORE slot
  (1 Lead · 2 Doubles lead · 3 Mid game · 4 Closer): the role's needs (bullets), then EVERY owned Pokémon checked against that
  slot's real requirements (legal moves / ability): 1 = 80+ Spe or bulky + a turn-1 tool (speed control, Taunt/Encore, Intimidate,
  Fake Out); 2 = must bring Intimidate / Fake Out / Follow Me / Rage Powder / Tailwind (spread move a plus); 3 = bulk 270+ and Haze /
  phazing / recovery / Regenerator / pivot; 4 = setup move or boosting ability. Weak-3 cores excluded. Top 6 by tier, then tool
  count (closer: boost size), tool chips shown, NO numeric score (Vincent, 22 Nov: the tier is enough); no needs list, no rank line.
  Slot 1 (singles lead, Vincent 22 Nov: faster > bulky, takes one hit, KOs in 1-2): measured vs EVERY trainer in the game (r<run>all):
  gate outspeeds >= 70%, KOs in 1-2 hits >= 65%, takes a hit >= 60%; ranked tier, then lead win rate (KOs in <= 2 before it dies);
  List sorted tier, then lead preference (lead win rate), the pick placed IN that order (never appended). Grey chips: Outspeeds %,
  Takes N hits to KO (median vs all foes), Resists N types, Weak to N types, 'Single target only'; green: Spread: <move it runs>
  (party moves / ideal build), Intimidate, Fake Out, priority, Taunt, Good as Gold. common_chips() (resists / weak / spread) is
  meant for slots 2-4 too when Vincent redoes them.
  Tiers in the Builder = the LIVE Dex tiers (22 Nov; the chapter freeze is no longer used there). Stability: his pick stays the
  suggestion when same tier and within 0.3 fit. One suggestion per Pokémon across slots. When my suggestion is not the highest
  tier in that slot, its card lists 'Why not X (tier)' lines (role tools, weaknesses, resists, shared weaknesses, phys/spec balance).
  Dex sheet (22 Nov) ALWAYS shows the ideal build (team members: the role build), one line per move; party lines that differ show
  '(yours: X)' + 'Replace yours: ...'. Dark mode: Builder uses --panel / --panel-2 / --warn tokens.
  Builder cards (22 Nov): tap = the SAME Dex sheet (ideal build); green chips = what the BUILD runs, dashed 'Teach: X' = a role
  tool it can learn but its build lacks (builder.teach_split). Checkbox per card -> TYPE MATRIX at the bottom (18 attacking types x
  ticked Pokémon, weak / resist counts; his 4 picks ticked by default; selection kept in localStorage). Build and rating text must
  agree: Aevian community best-use builds are FIXED in ideal_builds.py (Glalie-A Grassy Glide, Froslass-A Muddy Water, Unfezant-A
  Rock Head Head Smash); Veluza-A text says Fillet Away is left out.
  ALWAYS VERIFY (Vincent, 22 Nov): before saying what the page shows, read it back from output/chapter8_report.html / builder.json
  AFTER the final run (checks.py prints 'Builder: my suggestion matches your core'). Fit = 2 x tier rank + role tools (max 2)
  + 0.1 x (resists - weak) + 0.2 x covered gaps (max 3): a lower tier can't win on tool count alone.
  No 'Teach: X' chips (Vincent, 22 Nov: never show something that will never happen); chips = what the build runs.
  FLEX cards (22 Nov): Builder ends with 'F1 Flex 1 · Mid game · <next fight>' and 'F2 Flex 2 · Closer · <next fight>': the plan's
  2 swaps (state.team) + the best alternatives from fight_plans.json 'alts' (full pair search, also for the hand-planned next fight),
  split by role (closer = has a setup move), 'Counters: <foe>' chips from the plan's pairs. Only the NEXT fight; Ch9-specific.
  RED outline = his pick. YELLOW 'Suggested' = MY pick for EVERY slot (Vincent 22 Nov): tier rank + role fit (slot 1 lead win;
  2/3 role tool count; 4 boost size capped at +2) + 0.1 x (resists - weaknesses); both outlines when they agree.
  Key-detail chips on every slot (22 Nov): grey = resists / weak / 'Single target only'; green = role tools + what its build RUNS
  (KIT in builder.py: Redirection, Status, Speed control, Setup, Pivot, Recovery, Stat reset, Disrupt, Screens, Support, Priority, Spread). Re-evaluated every run (new mons, story, team): expect it rarely, never default to his pick. Flex / chapter swaps come later. **Cores tab REMOVED (Vincent, 22 Nov)**: he plays the team
  I recommend; cores.py only runs with CORES=1 (chat analysis). Team check for the remaining fights: scripts/team/team_fights.py
  (core + best 2 flexes per fight, full-six one-to-one counters).
- **Community tab + Aevian sentiment (Vincent, 23 Nov):** every community input he sends is saved in workspace/team/community_inputs.json
  (tier lists: tiers + marks; discussions: gameplay comments with +1/-1/0) and shown on the Community tab (scripts/team/community_tab.py, 6th nav
  item). community.py: FORUM = older forum ratings; AEVIAN rating = 2/3 x average list mark + 1/3 x FORUM, +/-0.02 per net comment (max .06);
  SENT = every point players make for / against each Aevian (owned AND not owned; game notes as 'Note'), shown on the Dex sheet ('What players
  say', ▲/▼) and under 'Not owned yet' (community-only grade) so it is ready when he unlocks them. Add new inputs there, never by hand in tiers.
- Builder fit (23 Nov): role tools count only when the BUILD runs them (could-learn = 0.5); a setup move is never a slot 2 tool.
- **Builder lists (Vincent, 23 Nov):** S / A only; B only when a slot has fewer than 3 S / A; never C or below; no cap on options. A slot
  lists everyone who meets its gate (not just best-fit role). S / A that would make 3 of 4 weak to one type show a red '3 of 4 weak to X'
  chip and are never suggested. Closer gate also accepts a priority STAB cleaner in the build (+0.8). Flexes = plan + fight_plans alts (30) +
  every S / A with per-fight score >= .5. Dedenne Crest counts as available now (Vincent; crests_owned).
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
  **Dex roles (Vincent, 22 Nov):** every tile shows its role under the name + role filter buttons per Dex tab; the sheet shows
  'Role: X (why)'. builder.py role_of() from what the BUILD runs, first match: Doubles lead (Follow Me / Rage Powder / Fake Out /
  Intimidate / Tailwind) > Lead (slot-1 gate: outspeeds 70% / KOs 65% / survives 60%) > Closer (setup move) > Mid game (Regenerator /
  recovery / stat reset / pivot, bulk 270+) > Support (weather / terrain setter, Trick Room, screens, Safeguard, sleep, hazards...)
  > Attacker. Builder slot lists show ONLY Pokémon whose Dex role is that slot's role (best fit; 22 Nov), so Builder and Dex agree.
  Stored in builder.json 'roles' (theme.py DROLES; the old ROLES = team_roles.json is a different thing).
  **Best partners / Core synergy (Vincent, 22 Nov):** builder.pair(a, b) from the builds they RUN: +0.5 per weakness the other resists
  (both ways), -0.75 per shared weakness, redirection + setup partner +1.5, Trick Room + slow partner +1 (fast partner -0.5), sleep +
  setup +0.5, a spread move that hits the ally super effectively -1 (immune +0.5), real-meta teammates (Smogon chaos) +1. Dex sheet:
  Builder: 'Core synergy' card HIDDEN (Vincent, 22 Nov; SHOW_SYNERGY=1 shows it) but synergy is ALWAYS factored into every
  suggestion: the slot fit adds 0.15 x pair() with the other three, and every chat recommendation must check pair() first. Card = the 6 core pairs, ✓ works / ✗ friction, max 3 lines, HOW THEY PLAY first (redirection / sleep / boost
  reset / Regenerator switch-ins / speed split / physical + special), then type cover. Dex 'Best partners' REMOVED (Vincent, 22 Nov).
  Builder cards: max 3 chips each (Vincent, 22 Nov). Dex 'Why X tier' = the MAIN rationale only (1 meta / community line + 1 in-game
  line when notable; no 'weak in-game' for support kits the damage model can't score).
  **Dex = real tier list (Vincent, 22 Nov):** headers just "S Tier" / "A Tier"… (+ count), then a tight grid of tiles (sprite +
  name only, ~4 per row on a phone); tap a tile → detail sheet (one fact per line). Bottom nav = 5 tabs (Cores removed).
  Detail sheet (Vincent, 22 Nov): no box location; meta = ONLY the best Smogon tier (META_W; usage / unranked hidden); base stats
  colour-scaled red→green by percentile in HIS box (+ %); nature shown with +/− stats; party members show YOUR build (real item,
  e.g. Arcanine-H Focus Sash), others the ideal build; no counters list. **"Why <tier> tier" (Vincent, 22 Nov):** bullets that
  explain the tier score's drivers, one per line: fights rank (top X% in remaining Ch9), beats N of their Pokémon, best vs
  which fights, meta level, its top stats (≥ 70th pct of the box), ability + effect, strongest move (effective power incl. STAB /
  Skill Link). (why_tier in theme.py; the old 'unique trait' line was replaced: it didn't say why it's strong.)
- **Tiers are GENERAL, meta-first (Vincent, 22 Nov)** — they pick the core four; Ch9 matchups are the flexes' job. tier_all.py:
  score = 0.7 × (0.9 × META DOMINANCE + 0.1 × BST) + 0.3 × in-game percentile across EVERY fight in the game data (6th engine run,
  DONE='' → r<run>all, ~60s, parallel). Meta dominance = Smogon usage weighted by format (OU / VGC / Doubles OU 1.0, NatDex OU .95,
  UU .62 … NU .3; best of singles / doubles + 0.25 × the other); banned to Ubers (Ubers set, no OU usage) = .95; Aevians by kit OP
  stars (REPLACED 22 Nov: Aevians + crests use COMMUNITY ratings, scripts/team/community.py: Reborn Evolved forum threads 2021-24
  + rejuvenation.wiki.gg Crests, quotes shown in the Dex 'Why' lines; 'Kit rating' when no posts exist; crests from a later chapter
  (CREST_CH = EARLIEST instance of wiki vs BIGJRA walkthrough, Vincent 22 Nov: e.g. Whiscash Crest = Ch7 Griselda Treasure 3, not the wiki Ch14) do not count; held ones get a To do "remove" card); usage that needs a partner he doesn't own is ignored (COMBO_DEP: Tatsugiri = Commander + Dondozo). Cut-offs S .72 /
  A .58 / B .41 / C .27. Dex sheet "Why X tier" = meta dominance /100 + each usage line + in-game rank only (no stats / ability /
  moves: they don't make a tier).
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
  Curse). No Ch9 counter term, no Ch9-type gap penalty. **Strength is FROZEN per chapter (Vincent, 22 Nov):** tier scores move as
  fights are beaten (60% = remaining-fight percentile), so cores.py + the Cores tier chips use team/core_strength.json (first value
  seen per name this chapter, never overwritten; reset when state chapter changes). Seeded from the 21 Nov tiers. Fight-specific core checks: scripts/team/arch_fights.py (chat only).
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
  (Faster / Watch trial rows replaced on 22 Nov by "Their team", see Team rules.) Team tab trial: party cards show a red line for moves the next fight's field weakens or blocks.
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
- **22 Nov guide pass (Vincent: clean, short):** Fights: chapter progress chips on top (✓ done / ▶ next); next fight card has a
  'Plan' block (Turn 1 per lead: best move by power x STAB x type, faster/slower, KO; Watch: foe: win conditions → answer, grouped);
  (Plan block and threat dots REMOVED from the page, Vincent 22 Nov; code kept off in theme.py).
  To do: 'Before <fight>' checklist in party order (✓ ready / N changes) on top, Boxes moves inside the To do tab (Boxes tab
  removed, nav = 5 tabs, .appnav grid = repeat(5)), 'Coming soon' unlocks at the bottom. Builder: 'Gap: <type>' line (2+ core weak, none resists) + best
  S/A flex. Type matrix starts with the six ticked. C&A checks: one line ('All checks pass · N warnings'), warnings folded.
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
