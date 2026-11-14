"""Fights tab: for each fight with a team/counters_<key>.json, list every opponent Pokémon and the ONE member of the
lineup that counters it (Vincent, 14 Nov: one dedicated counter per opponent). Runs after crest/aevian tabs, before tabs.py.
usage (from workspace/): counters_tab.py <report.html>"""
import glob, html, json, os, re, sys
E = html.escape
OUT = sys.argv[1]; page = open(OUT, encoding='utf-8').read()
TITLES = {'darkgardevoir': '1 · Dark Gardevoir (boss, Forest)', 'garbodor': '2 · Rift Garbodor (boss, Corrupted Cave)', 'karrina': '3 · Karrina (Blessed Field)',
          'spector': '4a · Spector day (Haunted)', 'spector2': '4b · Spector night (Haunted)', 'jenner9': '5 · Jenner (Concert Venue)',
          'amanda': '6 · Amanda (Factory)', 'erick': '7 · Erick, gym (Murkwater Surface)'}
done = set(json.load(open('team/state.json')).get('done', []))
blocks = ''
ORDER = list(TITLES)
for f in sorted(glob.glob('team/counters_*.json'), key=lambda f: ORDER.index(os.path.basename(f)[9:-5]) if os.path.basename(f)[9:-5] in ORDER else 99):
    key = os.path.basename(f)[9:-5]
    if key in done: continue
    d = json.load(open(f)); c = d.get('current') or d['best'][0]
    rows = ''.join(f"<tr><td><b>{E(p['foe'])}</b></td><td>{E(p['mon'].replace(' (Aevian Form)', '-A').replace(' (Hisuian Form)', '-Hisui').replace(' (Galarian Form)', '-Galar'))}</td>"
                   f"<td class='c' data-l='deals'>{p['dealt']}%</td><td class='c' data-l='takes'>{p['taken']}%</td>"
                   f"<td>{'<span class=ok>✓</span>' if p['ok'] else '<span class=warn>weak</span>'}</td></tr>" for p in c['pairs'])
    tag = ' <span class="legend">(box preview: team built before the fight)</span>' if d.get('preview') else ' <span class="legend">(your lineup)</span>'
    blocks += (f"<div class='panel pad'><h3>{E(TITLES.get(key, key))}{tag}: one counter per Pokémon "
               f"<span class='legend'>{c['counters']}/{len(c['pairs'])} countered</span></h3><div class='tablewrap'><table class='ctr'>"
               f"<thead><tr><th>Their Pokémon</th><th>Your counter</th><th>Deals</th><th>Takes</th><th></th></tr></thead><tbody>{rows}</tbody></table></div></div>")
if blocks:
    sec = f'<section aria-labelledby="sctr">\n  <h2 id="sctr">Counters</h2>\n  {blocks}\n</section>\n'
    page = re.sub(r'<section aria-labelledby="sctr">.*?</section>\s*', '', page, flags=re.S)
    i = page.find('<section aria-labelledby="s1f">')
    j = page.find('</section>', i) + len('</section>') if i >= 0 else page.rfind('<footer')
    page = page[:j] + '\n' + sec + page[j:]
    css = (' .ctr td, .ctr th { padding: 5px 8px; border-bottom: 1px solid var(--line); text-align: left; font-size: 13px }'
           ' .ctr .c { font-family: var(--mono) } .ctr .warn { color: #b45309; font-weight: 600 }'
           ' @media (max-width: 680px) { .ctr thead { display: none } .ctr tr { display: grid; grid-template-columns: 1fr 1fr; padding: 6px 0; border-bottom: 1px solid var(--line) }'
           ' .ctr td { border: 0 !important } .ctr td[data-l]::before { content: attr(data-l); margin-right: 6px; font: 500 10px var(--mono); color: var(--muted); text-transform: uppercase } }')
    page = re.sub(r' \.ctr td, \.ctr th \{.*?(?=</style>)', '', page, flags=re.S)
    page = page.replace('</style>', css + '</style>', 1)
open(OUT, 'w', encoding='utf-8').write(page)
print('counters tab:', bool(blocks))
