"""Aevian tab (section s7): tier list of every Aevian form Vincent owns. Tier = measured score on the remaining hard fights
(exact game data, same solo score as the Crests tab); OP = how broken the kit is (signature move/ability, level, meta analog).
Kit facts (types, stats, abilities, learn levels) come from the game files (gamedata/montext.json).
usage (from workspace/): BASE_RUN=r51 DONE=... python3 -I ../scripts/team/aevian_tab.py <report.html>"""
import html, json, os, pickle, re, sys
sys.argv, OUT = ['x', '.', '20'], sys.argv[1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chapter_rules as C
E = html.escape

# what makes each form strong: (OP stars 1-3, signature / key tools with level, meta analog, catch)
KIT = {
 'Golisopod': (3, 'Skill Link: Bone Rush (Lv 41) always hits 5× = 125 BP Ground STAB; Pin Missile (Lv 21) 125 BP Bug. Swords Dance Lv 16, Headlong Rush Lv 48',
               'Skill Link Cloyster / Cinccino: multi-hits break Sash, Sturdy, Substitute', '125 Atk / 130 Def, but base 50 Speed'),
 'Veluza': (3, 'Fillet Away (Lv 30): +2 Atk / SpA / Speed for half its HP. Reckless Wave Crash (Lv 45) + Flare Blitz (Lv 40) ×1.2, Extreme Speed Lv 50',
            'Shell Smash / Belly Drum sweepers (Cloyster, Azumarill) with Water + Fire STAB', '60 / 60 defences: needs a free turn, recoil adds up'),
 'Glalie': (2, 'Grassy Surge on entry: Grass moves ×1.3 + heal every turn. Grassy Glide (Move Relearner) = priority in terrain; Wood Hammer Lv 48',
            'Rillaboom (Grassy Surge + Grassy Glide, OU / VGC staple)', 'Weak to Bug, Fighting, Ice, Poison, Steel; base 50 Speed'),
 'Lapras': (2, 'No Guard: Sing (Lv 5) never misses = sleep on demand; Rock Slide (Lv 30) never misses + flinch; Dragon Dance (egg)',
            'Guaranteed sleep like Spore users (Amoonguss, Breloom)', 'Sleep is blocked by Electric / Misty terrain and sleep-immune bosses'),
 'Musharna': (2, 'Tough Claws: Play Rough / Throat Chop ×1.3; Glare (Lv 43 as Munna); Lovely Kiss Lv 41 + Bad Dreams as the sleep build',
              'Bulky Dark/Fairy hitter like Grimmsnarl; Bad Dreams = Darkrai\'s ability', 'Base 29 Speed: moves last'),
 'Drapion': (2, 'Fur Coat: physical damage halved (2× Defence). Merciless option: every hit on a poisoned foe crits (Toxic Spikes Lv 15)',
             'Fur Coat Alolan Persian; Merciless + Toxic combo like Toxapex', 'Ice/Poison: weak to Fire, Ground, Psychic, Steel'),
 'Froslass': (2, 'Adaptability: Grass + Water STAB ×2 (Hydro Pump Lv 41, Giga Drain Lv 48), base 110 Speed',
              'Adaptability Crawdaunt / Porygon-Z damage', 'Same Water/Grass role as your Ludicolo'),
 'Roserade': (1, 'Technician Vacuum Wave (priority, 40→60 BP) + Mud Shot; Aura Sphere (Lv 43 as Roselia), Earth Power (Relearner); 125 SpA',
              'Fast special Fighting/Ground with no direct meta analog', 'Dry Skin needs rain (none on the team): Technician only'),
 'Ampharos': (1, 'Filter (super-effective hits ×0.75) on Ice/Electric; Cotton Guard Lv 46 (+3 Def). Ice Ball (Lv 25) is weak',
              'Bulky special Electric like regular Ampharos', 'Its Aevian Ampharos Crest is not owned'),
 'Gastrodon': (1, 'Ground/Fairy with Storm Drain; Strange Steam (Lv 41), Earth Power (Lv 35), Recover (Lv 54)',
               'Bulky Ground pivot like Clodsire', 'Base 39 Speed, middling power'),
 'Unfezant': (1, 'Rock Head + Head Smash (Pidove Lv 52) with no recoil; Defiant; Tailwind only at Lv 60 (past the cap)',
              'Fast Rock/Fighting like Terrakion, but 115 Atk / 98 Spe', '55 / 55 special bulk'),
 'Palossand': (1, 'Rocky: Storm Drain, Power Gem. Fiery: Steam Engine (Fire/Water hit = +6 Speed), Lava Plume. Icy: Freeze-Dry (Lv 47)',
               'Bulky Ghost wall like regular Palossand', '35 Speed, 100 SpA'),
 'Leavanny': (1, 'Bug/Dragon with Intimidate, Swords Dance (Lv 46), Dragon Rush (Lv 50); Sticky Web as Swadloon (Lv 32)',
              'Physical Bug like Scizor without the bulk', '75 / 75 / 75 bulk'),
 'Mismagius': (1, 'Hexing Slash (learned on evolving): 90 BP Ghost, drains HP, may poison. Magic Bounce reflects status',
               'Mixed Ghost like regular Mismagius', '60 / 60 / 60 bulk: one-shot often'),
}
cands = pickle.load(open(f"team/{os.environ['BASE_RUN']}_native.json.pkl", 'rb'))['cands']
def solo(c):
    tot = tw = 0
    for b in C.HARD:
        rows = c['matchups'][b['key']]; n = len(rows)
        v = sum(r['q'] for r in rows) / n - .35 * sum(r['deff'] >= 100 for r in rows) / n
        w = C.bw(b); tot += v * w; tw += w
    return tot / tw
best = {}
for c in cands:
    if c['gate'] or 'Aevian' not in c['name']: continue
    if c['name'] not in best or solo(c) > solo(best[c['name']]): best[c['name']] = c
st = json.load(open('team/state.json'))
team_names = st['team']
anchor = sorted(solo(min((c for c in cands if c['name'] == n and not c['gate']), key=lambda c: -solo(c))) for n in team_names)
lo, med = anchor[0], anchor[len(anchor) // 2]
on_team = {n.split(' (')[0] for n in team_names if 'Aevian' in n}
TIERS = [('S', 'Beats your six\'s median member'), ('A', 'Team level'), ('B', 'Close to team level'), ('C', 'Bench'), ('D', 'Not for these fights')]
rows = {t: [] for t, _ in TIERS}
for n, c in sorted(best.items(), key=lambda kv: -solo(kv[1])):
    s = solo(c); sp = n.split(' (')[0]
    t = 'S' if s >= med else 'A' if s >= lo else 'B' if s >= lo * .85 else 'C' if s >= .3 else 'D'
    op, sig, meta, catch = KIT.get(sp, (1, '', '', ''))
    b = c['base']; types = '/'.join(x.title() for x in c['types'])
    form = n.replace(' Aevian Form', '').replace('(Aevian Form)', '').replace('( Male)', '').replace('  ', ' ').strip()
    tag = ' <span class="ok">on your team</span>' if sp in on_team else ''
    moves = ', '.join(C.D.moves[m]['MoveName'] for m in c['attacks'])
    rows[t].append(
        f"<tr><td><b>{E(form)}</b>{tag}<div class='legend'>{E(types)} · {b['HP']}/{b['Atk']}/{b['Def']}/{b['SpA']}/{b['SpD']}/{b['Spe']}"
        f" · {E(c['src']['where'])} #{c['src'].get('dump')}</div></td>"
        f"<td class='c op' data-l='OP'>{'★' * op}{'☆' * (3 - op)}</td>"
        f"<td>{E(sig)}<div class='legend'>Like: {E(meta)}</div></td>"
        f"<td class='legend'>{E(catch)}</td>"
        f"<td class='c' data-l='score'>{s:.2f}<div class='legend'>{E(moves)}</div></td></tr>")
body = ''
for t, why in TIERS:
    if not rows[t]: continue
    body += (f"<div class='panel pad'><h3><span class='tier t{t}'>{t}</span> {E(why)} <span class='legend'>{len(rows[t])}</span></h3>"
             f"<div class='tablewrap'><table class='aev'><thead><tr><th>Pokémon</th><th>OP</th><th>What makes it strong (learn level)</th>"
             f"<th>Catch</th><th>Score</th></tr></thead><tbody>{''.join(rows[t])}</tbody></table></div></div>")
sec = f'''<section aria-labelledby="s7">
  <h2 id="s7">Aevian forms</h2>
  <ul class="legend">
    <li>Tier = score on the remaining hard fights (exact game data). Your six: lowest {lo:.2f}, median {med:.2f}.</li>
    <li>OP ★ = how broken the kit is (signature move / ability), judged against meta Pokémon with the same tools.</li>
    <li>Factored in: every form here was in the whole-box team search, Fillet Away and Swords Dance counted.
      Best Aevian-heavy six (Golisopod, Glalie, Musharna + Armarouge, Ludicolo, Gholdengo) = +0.6%, a tie with more misses. Your six stays.</li>
  </ul>
  {body}
</section>
'''
CSS = ('.aev td, .aev th { padding: 5px 8px; border-bottom: 1px solid var(--line); text-align: left; font-size: 13px; vertical-align: top }'
       ' .aev .c { text-align: center; font-family: var(--mono) } .aev .op { color: #b45309; letter-spacing: 1px; white-space: nowrap }'
       ' @media (max-width: 680px) { .aev thead { display: none } .aev tr { display: grid; grid-template-columns: 1fr 1fr; padding: 6px 0;'
       ' border-bottom: 1px solid var(--line) } .aev td { border: 0 !important } .aev td:nth-child(1), .aev td:nth-child(3), .aev td:nth-child(4) { grid-column: 1 / -1 }'
       ' .aev td[data-l]::before { content: attr(data-l); margin-right: 6px; font: 500 10px var(--mono); color: var(--muted); text-transform: uppercase } .aev .c { text-align: left } }')
page = open(OUT, encoding='utf-8').read()
page = re.sub(r'<section aria-labelledby="s7">.*?</section>\s*', '', page, flags=re.S)
anchor_at = page.rfind('<section aria-labelledby="s5">') if '<section aria-labelledby="s5">' in page else page.rfind('<footer')
page = page[:anchor_at] + sec + page[anchor_at:]
page = re.sub(r'\.aev td, \.aev th \{.*?(?=</style>)', '', page, flags=re.S)
page = page.replace('</style>', CSS + '</style>', 1)
open(OUT, 'w', encoding='utf-8').write(page)
print('aevian tab:', {t: len(v) for t, v in rows.items()})
