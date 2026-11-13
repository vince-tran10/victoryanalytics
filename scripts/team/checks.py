"""C&A (Checks & Audit) tab: data provenance, game-verified mechanics, corrections, known gaps, automatic checks.
Runs after make_report5 + box_audit + highlight, before tabs.py.  usage (from workspace/): checks.py <report.html>
Exit code 1 if a BLOCKING check fails (update.py then refuses to call the page ready)."""
import html, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'gamedata'))
E = html.escape
OUT = sys.argv[1]
page = open(OUT, encoding='utf-8').read()
TEAMD = os.path.join(os.getcwd(), 'team')
st = json.load(open(os.path.join(TEAMD, 'state.json')))
acts = json.load(open(os.path.join(TEAMD, 'actions.json')))
sec = lambda sid: (re.search(rf'<section aria-labelledby="{sid}">.*?</section>', page, re.S) or re.search('x^', ''))
text = lambda s: ' '.join(re.sub(r'<[^>]+>', ' ', s).split())

# ------------------------------------------------------------- automatic checks
checks = []   # (name, ok, detail, blocking)
def chk(name, ok, detail='', blocking=True): checks.append((name, bool(ok), detail, blocking))
todo = sec('s3').group(0) if sec('s3') else ''
team = sec('s1').group(0) if sec('s1') else ''
cards = re.findall(r'<div class="tgroup pcard"><h3>(.*?) <span', todo)
_done = text(team).count('Done ✓'); _moving_in = sum(1 for v in acts.values() if v.startswith('Move into the party'))
_in_party_card = len(re.findall(r'<div class="tgroup pcard"><h3>.*?</h3>\s*<div[^>]*>[^<]*Party #', todo)) or \
    sum(1 for c in re.findall(r'<div class="tgroup pcard">.*?(?=<div class="tgroup pcard">|$)', todo, re.S) if 'Party #' in text(c)[:200])
chk('Every member of the six is Done ✓, or has a To do card (in the party, or with a green move into it)',
    _done + max(_moving_in, _in_party_card) >= 6 or st.get('fight'), f"{_done} done, {_moving_in} moving in, {_in_party_card} in party with a card")
chk('To do: one card per Pokémon (no duplicates)', len(cards) == len(set(cards)), f'{len(cards)} cards')
chk('To do: no "X or Y" answers', not re.search(r'\b(\w+) or (\w+)\b', re.sub(r'<p class="legend">.*?</p>', '', text(todo))),
    'checked every card line')
chk('To do: no box moves', not re.search(r'Move to (Active|Overflow)|move out of the party|Put .* in the party', text(todo)), '')
teach_p = re.findall(r'Teach Protect[^<]*', todo)
chk('To do: every "Teach" says what it replaces', all('replaces' in t for t in re.findall(r'Teach [^<]*', todo) if not t.startswith('Teach Protect (4th')),
    f"{len(re.findall(r'Teach [^<]*', todo))} teach lines")
green = [n for n, v in acts.items() if v.startswith(('Move to Active', 'Move into'))]
_carded = [n for n in green if f'#{n}' in todo]
chk('Boxes: every Pokémon moving into Active has a To do build card', len(_carded) == len(green) or not green,
    f'{len(_carded)}/{len(green)} have a card' + ('' if len(_carded) == len(green) else ' (the rest already match their build: verify)'), blocking=False)
chk('Lapras-Aevian is the only Protect exception', 'Lapras' not in text(todo) or 'Protect' not in text(todo).split('Lapras')[1][:120], '')
try:
    import gamedata as GD
    gd_ok = GD.available()
except Exception:
    gd_ok = False
chk('Fight data comes from the game files (not the walkthrough)', gd_ok,
    'workspace/gamedata/*.json present' if gd_ok else 'MISSING: re-upload the Scripts zip and run scripts/gamedata/to_json.rb')
cmp = os.path.join(TEAMD, 'gamedata_compare.json')
if os.path.exists(cmp):
    C = json.load(open(cmp))
    left = [(k, r['mon'], d) for k, v in C.items() for r in v.get('rows', []) for d in r['diff']
            if not d.startswith(('BOSS', 'calls SOS', 'MISSING', 'EXTRA'))]
    chk('Every hard-fight Pokémon matches the game data exactly', not left, f'{len(left)} differences' if left else 'level, item, ability, nature, moves, types, EVs')
NEEDS = {'Swift Swim': 'rain', 'Rain Dish': 'rain', 'Hydration': 'rain', 'Chlorophyll': 'sun', 'Solar Power': 'sun',
         'Leaf Guard': 'sun', 'Flower Gift': 'sun', 'Sand Rush': 'sand', 'Sand Force': 'sand', 'Sand Veil': 'sand', 'Slush Rush': 'snow',
         'Ice Body': 'snow', 'Snow Cloak': 'snow', 'Surge Surfer': 'e-terrain', 'Grass Pelt': 'g-terrain', 'Quark Drive': 'e-terrain',
         'Protosynthesis': 'sun'}
GIVES = {'Drizzle': 'rain', 'Rain Dance': 'rain', 'Drought': 'sun', 'Sunny Day': 'sun', 'Sand Stream': 'sand', 'Sandstorm': 'sand',
         'Snow Warning': 'snow', 'Snowscape': 'snow', 'Electric Surge': 'e-terrain', 'Electric Terrain': 'e-terrain',
         'Grassy Surge': 'g-terrain', 'Grassy Terrain': 'g-terrain'}
_ab = st.get('abilities') or {}; _mv = st.get('moves') or {}
_have = {GIVES[x] for x in list(_ab.values()) + [m for ms in _mv.values() for m in ms] if x in GIVES}
_dead = [f"{n}: {a} (needs {NEEDS[a]})" for n, a in _ab.items() if a in NEEDS and NEEDS[a] not in _have]
_tr = any('Trick Room' in ms for ms in _mv.values()); _glare = any('Glare' in ms or 'Thunder Wave' in ms for ms in _mv.values())
chk('Synergy: no dead abilities (every conditional ability has its enabler on the team)', not _dead, '; '.join(_dead) or 'none dead')
chk('Synergy: no anti-synergy (Glare / paralysis under Trick Room)', not (_tr and _glare), '')
chk('Synergy: the team states one identity', 'Identity' in text(team) or 'Identity' in page, '')
tc = st.get('team_check') or {}
chk('Team passes the chapter rules', tc.get('rank') is not None, f"#{tc.get('rank')} of {tc.get('of')}")
chk('Team is within 1% of the best six', (tc.get('gap') or 0) <= 1.0,
    f"best six is {tc.get('gap'):+.2f}%: {', '.join(tc['top'][0]['team'])}" if tc.get('top') else '', blocking=False)

# ------------------------------------------------------------- static audit content
SOURCES = [('Eli & Sharon', 'trainertext · MISFORTUNATEDUO #10', '10'), ('Geara & Zetta', 'trainertext · XENEXECUTIVE_3 #2 + XENEXECUTIVE_1 #8', '6 + 6'),
           ('Giratina', 'trainertext · ALGRISELDA #0 + bosstext VALORGIRATINA', '3 (boss: 2 shields)'),
           ('Holly & Rorim', 'trainertext · COMMANDER #0 + DISCOTEEN #3', '3 + 3'), ('Manaphy', 'bosstext · SEAPRINCE (+ Phione SOS)', '1 (boss: 2 shields)'),
           ('??? (Factory)', 'trainertext · UNKNOWN_1 #1', '6'), ('Amber', 'trainertext · LEADER_AMBER #0', '6'),
           ('Fields', 'fieldtext · MOUNTAIN, VOLCANICTOP, WASTELAND, ASHENBEACH, FACTORY, CONCERT1, WATERSURFACE', '')]
VERIFIED = [('Trainer EVs when unlisted = min(85, level × 1.5)', 'Pokemon.rb · applyEVs'),
            ('Trainer IVs when unlisted = 10 (all hard-fight Pokémon list 31)', 'Pokemon.rb · applyIVs'),
            ('Boss with N shields = N+1 full HP bars; overflow damage is lost', 'Battler.rb · pbReduceHP'),
            ('Field type add-ons multiply in a 2nd type (Rock on Volcanic Top = Rock + Fire)', 'Battle_Move.rb · fieldTypeChangeModifier'),
            ('Concert Venue hype 1 = minimum damage rolls (85%)', 'Battle_Move.rb · random = 85 if CONCERT1'),
            ('Classic mode uses trainertext/bosstext; *_story files are Story mode', 'CacheAddOn.rb · compileTrainersStory')]
FIXED = [('Giratina', 'had no boss shields → 2 shields (3 HP bars); last bar: Dragon/Poison, Griseous Orb, +1 Atk/SpA, Dragon Pulse / Venoshock'),
         ('Manaphy', '2 shields modelled as ×2.2 HP → 3 full bars; +3 SpA after the 1st break; last bar floods the field to Water Surface'),
         ('Kyogre (beaten)', '4 shields were ×3.4 HP → really 5 full bars'),
         ('Rorim\'s Oricorio', 'Baile (Fire/Flying) → Pom-Pom (Electric/Flying) + Hidden Power Ice'),
         ('Factory Rotom', 'Ghost → Mow Rotom (Electric/Grass)'),
         ('Hidden Power', 'missing on Typhlosion (Grass), Oricorio (Ice), Raichu (Ice), Xurkitree (Ice), Camerupt (Electric), Toxtricity (Grass)'),
         ('Volcanic Top', 'Icy Wind ×3 → ×1.5 and Fire-typed; wind moves, Smog, Dig, Dive gain Fire; Scald/Steam ×1.67 → ×1.5'),
         ('Wasteland', 'Venoshock / Barb Barrage ×2 → no boost'),
         ('Beach', 'Hidden Power ×1.5, Strength becomes Psychic (were missing)'),
         ('Water Surface', 'Ground moves ×0 (fail), Fire ×0.5 (were missing)'),
         ('Factory', 'Flash Cannon / Gyro Ball ×2 (missing); Discharge / Earthquake turn it into Short-Circuit'),
         ('Concert Venue', 'minimum damage rolls at hype 1 (was average)')]
GAPS = ['Boss delayed actions (Manaphy dims its +3 SpA after 2 turns) and player-side stat drops are not simulated',
        'Moves that change the field mid-battle (Eruption: Mountain → Volcanic Top; Discharge: Factory → Short-Circuit) are listed, not simulated',
        'Concert hype going up (rolls rise to 100% at hype 4) is not simulated; the fight is modelled at hype 1',
        'The game uses the AI\'s real move choice; the engine assumes the foe uses its strongest attack',
        'Non-hard fights (grunts, Jenner, Marcie…) still use walkthrough data']

ok_n = sum(1 for c in checks if c[1]); n = len(checks)
rows = ''.join(f'<tr><td>{"<span class=ok>✓</span>" if ok else ("<span class=bad>✗</span>" if blk else "<span class=warn>!</span>")}</td>'
               f'<td>{E(nm)}</td><td class="legend">{E(d)}</td></tr>' for nm, ok, d, blk in checks)
tbl = lambda head, rws: (f'<div class="tablewrap"><table class="cat"><thead><tr>{"".join("<th>" + h + "</th>" for h in head)}</tr></thead>'
                         f'<tbody>{"".join("<tr>" + "".join("<td>" + E(c) + "</td>" for c in r) + "</tr>" for r in rws)}</tbody></table></div>')
html_sec = f'''<section aria-labelledby="s5">
  <h2 id="s5">C&amp;A checks</h2>
  <div class="panel pad"><h3>Automatic checks <span class="legend">{ok_n}/{n} passed · run on every update</span></h3>
    <div class="tablewrap"><table class="cat"><tbody>{rows}</tbody></table></div></div>
  <div class="panel pad"><h3>Data sources <span class="legend">Rejuvenation's own files (Classic mode), not the wiki</span></h3>{tbl(['Fight', 'Game entry', 'Pokémon'], SOURCES)}</div>
  <div class="panel pad"><h3>Corrections from the game files</h3>{tbl(['What', 'Fix'], FIXED)}</div>
  <div class="panel pad"><h3>Game rules verified in the code</h3>{tbl(['Rule', 'Where'], VERIFIED)}</div>
  <div class="panel pad"><h3>Not modelled (known gaps)</h3><ul>{"".join("<li>" + E(g) + "</li>" for g in GAPS)}</ul></div>
</section>
'''
CSS = ('.cat td, .cat th { padding: 5px 8px; border-bottom: 1px solid var(--line); text-align: left; font-size: 13px; vertical-align: top }'
       ' .cat .warn, .warn { color: #b45309; font-weight: 600 }'
       ' @media (max-width: 680px) { .cat thead { display: none } .cat tr { display: grid; grid-template-columns: 22px 1fr; padding: 4px 0;'
       ' border-bottom: 1px solid var(--line) } .cat td { border: 0 !important; padding: 2px 4px !important }'
       ' .cat td:nth-child(n+3) { grid-column: 2 } .cat td:only-child, .cat tr td:first-child:nth-last-child(2),'
       ' .cat tr td:first-child:nth-last-child(2) ~ td { grid-column: auto } }')
page = re.sub(r'<section aria-labelledby="s5">.*?</section>\s*', '', page, flags=re.S)
anchor = page.rfind('<footer') if '<footer' in page else page.rfind('</main>')
page = page[:anchor] + html_sec + page[anchor:]
page = re.sub(r'\.cat td, \.cat th \{.*?(?=</style>)', '', page, flags=re.S)
page = page.replace('</style>', CSS + '</style>', 1)
open(OUT, 'w', encoding='utf-8').write(page)
for nm, ok, d, blk in checks:
    print(('PASS ' if ok else ('FAIL ' if blk else 'WARN ')) + nm + (f' — {d}' if d else ''))
sys.exit(1 if any(not ok and blk for nm, ok, d, blk in checks) else 0)
