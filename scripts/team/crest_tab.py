"""Crests tab (section s6): tier list of every owned crest-eligible Pokémon, scored with vs without its crest on the
hard fights (team/crest_tier.json from crest_tier.py). Runs after highlight.py, before tabs.py.
usage (from workspace/): crest_tab.py <report.html>"""
import html, json, os, re, sys
E = html.escape
OUT = sys.argv[1]
page = open(OUT, encoding='utf-8').read()
T = json.load(open('team/crest_tier.json'))
I = json.load(open('gamedata/itemtext.json')) if os.path.exists('gamedata/itemtext.json') else {}
desc = {v.get('name'): (v.get('desc') or '') for k, v in I.items() if k.endswith('CREST')}
owned = set(json.load(open('team/state.json')).get('crests_owned') or [])
# Where each crest is available up to Chapter 8 (BIGJRA walkthrough Ch1-8 in workspace/walkthrough). Not listed = not found
# in the Ch1-8 walkthrough (most likely a later chapter; the wiki has per-crest pages but isn't reachable from this session).
AVAIL = {'Ariados Crest': 'Ch 5 · Griselda\'s Treasure 2', 'Noctowl Crest': 'Ch 5 · Cairo\'s house, Route 4',
         'Plusle Crest': 'Ch 5 · Cairo\'s house, Route 4', 'Minun Crest': 'Ch 5 · Cairo\'s house, Route 4',
         'Simisage Crest': 'Ch 5 · Cairo\'s house, Route 4', 'Simisear Crest': 'Ch 5 · Cairo\'s house, Route 4',
         'Simipour Crest': 'Ch 5 · Cairo\'s house, Route 4', 'Thievul Crest': 'Ch 5 · Cairo\'s house, Route 4',
         'Furret Crest': 'Ch 7 · gift box', 'Whiscash Crest': 'Ch 7 · Griselda\'s Treasure 3',
         'Fearow Crest': 'Ch 8 · Griselda\'s Treasure 7 (Wispy Chasm)', 'Zoroark Crest': 'Ch 8 · with Zorua (Hisuian)',
         'Silvally Crest': 'Ch 8 · reward for beating Geara & Zetta', 'Phione Crest': 'Ch 8 · Tale of Two Hearts (after Manaphy)'}
ENEMY_ONLY = {'Crabom. Crest': 'only on Neved\'s Crabominable (you skipped Neved)', 'Relicanth Crest': 'only on Giratina\'s partner',
              'Swalot Crest': 'only on Giratina\'s partner'}
NOT_MODELLED = {'Castform Crest', 'Cherrim Crest', 'Luvdisc Crest', 'Zoroark Crest', 'Furret Crest', 'Swalot Crest', 'Zangoose Crest',
                'Thievul Crest', 'Vespiquen Crest', 'Plusle Crest', 'Minun Crest', 'Sunflora Crest', 'Ledian Crest', 'Delcatty Crest',
                'Probopass Crest'}
TIERS = [('S', 'Better than your six\'s median member with the crest'), ('A', 'Team-level with the crest'),
         ('B', 'Close to team level'), ('C', 'Crest helps, still not team level'), ('D', 'Crest does little here / not modelled')]
rows = {t: [] for t, _ in TIERS}
for r in T['rows']:
    have = r['crest'] in owned or r['held']
    if have: status = '<span class="ok">you have it</span>'
    elif r['crest'] in AVAIL: status = '<span class="warn">get it: ' + E(AVAIL[r['crest']]) + '</span>'
    elif r['crest'] in ENEMY_ONLY: status = '<span class="legend">not obtainable: ' + E(ENEMY_ONLY[r['crest']]) + '</span>'
    else: status = '<span class="legend">not yet (not in Ch 1–8)</span>'
    nm = ' <span class="legend">(effect not modelled)</span>' if r['crest'] in NOT_MODELLED else ''
    rows[r['tier']].append(
        f"<tr><td><b>{E(r['name'])}</b><div class='legend'>{E(r['where'])} #{r['dump']}</div></td>"
        f"<td>{E(r['crest'])}{nm}<div class='legend'>{E(desc.get(r['crest'], '')[:140])}</div></td>"
        f"<td class='c' data-l='with crest'>{r['with_crest']:.2f}</td><td class='c' data-l='without'>{r['without']:.2f}</td>"
        f"<td class='c {'up' if r['gain'] > 0.005 else ''}' data-l='gain'>{r['gain']:+.2f}</td><td>{status}</td></tr>")
body = ''
for t, why in TIERS:
    if not rows[t]: continue
    body += (f"<div class='panel pad'><h3><span class='tier t{t}'>{t}</span> {E(why)} <span class='legend'>{len(rows[t])}</span></h3>"
             f"<div class='tablewrap'><table class='crt'><thead><tr><th>Pokémon</th><th>Crest</th><th>With crest</th><th>Without</th>"
             f"<th>Gain</th><th>Availability</th></tr></thead><tbody>{''.join(rows[t])}</tbody></table></div></div>")
team_line = ', '.join(f"{k.replace(' (Aevian Form)', '-A')} {v:.2f}" for k, v in T['team'].items())
sec = f'''<section aria-labelledby="s6">
  <h2 id="s6">Crests</h2>
  <p class="legend">Every crest-eligible Pokémon you own, scored on the 7 hard fights (exact game data) with vs without its crest.
  Effects come from the game code. For reference, your six without crests: {E(team_line)}.</p>
  {body}
</section>
'''
CSS = ('.crt td, .crt th { padding: 5px 8px; border-bottom: 1px solid var(--line); text-align: left; font-size: 13px; vertical-align: top }'
       ' .crt .c { text-align: center; font-family: var(--mono) } .crt .warn { color: #b45309; font-weight: 600 } .crt .up { color: var(--good); font-weight: 600 }'
       ' .tier { display: inline-block; min-width: 22px; text-align: center; border-radius: 4px; font-weight: 700; margin-right: 6px }'
       ' .tS { background: #7c3aed22 } .tA { background: #16a34a22 } .tB { background: #2563eb22 } .tC { background: #ca8a0422 } .tD { background: #64748b22 }'
       ' @media (max-width: 680px) { .crt thead { display: none } .crt tr { display: grid; grid-template-columns: 1fr 1fr; padding: 6px 0;'
       ' border-bottom: 1px solid var(--line) } .crt td { border: 0 !important } .crt td:nth-child(2) { grid-column: 1 / -1 } .crt td[data-l]::before { content: attr(data-l); margin-right: 6px; font: 500 10px var(--mono); color: var(--muted); text-transform: uppercase } .crt .c { text-align: left } }')
page = re.sub(r'<section aria-labelledby="s6">.*?</section>\s*', '', page, flags=re.S)
anchor = page.rfind('<section aria-labelledby="s5">') if '<section aria-labelledby="s5">' in page else page.rfind('<footer')
page = page[:anchor] + sec + page[anchor:]
page = re.sub(r'\.crt td, \.crt th \{.*?(?=</style>)', '', page, flags=re.S)
page = page.replace('</style>', CSS + '</style>', 1)
open(OUT, 'w', encoding='utf-8').write(page)
print('crest tab:', {t: len(v) for t, v in rows.items()})
