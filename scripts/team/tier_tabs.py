"""Tier tabs on ONE blended scale (team/tier_all.json from tier_all.py): Crests (s6), Aevians (s7), all other Pokémon (s8).
Replaces crest_tab.py / aevian_tab.py. Runs after highlight.py, before tabs.py.
usage (from workspace/): python3 -I ../scripts/team/tier_tabs.py <report.html>"""
import html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kits import KIT, SHORT, disp, abn
from sprites import tag as sprite
E = html.escape
OUT = sys.argv[1]
T = json.load(open('team/tier_all.json'))
_st = json.load(open('team/state.json')); ST_CORE = set(_st.get('core') or []); ST_TEAM = set(_st.get('team') or [])
PLAN_SWAPS = {r['name'] for p in (json.load(open('team/fight_plans.json')).values() if os.path.exists('team/fight_plans.json') else []) for r in p['swaps']}
I = json.load(open('gamedata/itemtext.json'))
CDESC = {v.get('name'): (v.get('desc') or '') for k, v in I.items() if k.endswith('CREST')}
CT = {r['name']: r for r in json.load(open('team/crest_tier.json'))['rows']} if os.path.exists('team/crest_tier.json') else {}
CUT = dict(T['cut'])
WHY = {'S': 'Top of your boxes: strong in these fights and in the meta', 'A': 'Team level', 'B': 'Good, situational',
       'C': 'Bench', 'D': 'Not for these fights'}


def fights_line(r):
    top = sorted(r['per_fight'].items(), key=lambda kv: -kv[1])[:2]
    return 'best vs ' + ', '.join(SHORT.get(k, k) for k, _ in top)


def row(r, extra):
    b = r['base']; types = '/'.join(t.title() for t in r['types'])
    oa = r.get('owned_as') or ''
    same = not oa or oa in r['name'] or oa == disp(r['name']) or oa.split('-')[0] == r['name'].split(' (')[0] and r['sid'].lower().startswith(oa.split('-')[0].lower())
    where = f"{r['where']} #{r['dump']}" + ('' if same else f" · now {oa} (evolve)")
    party = (' <span class="ok">core</span>' if r['name'] in ST_CORE else ' <span class="ok">swap now</span>' if r['name'] in ST_TEAM
             else ' <span class="legend">plan swap</span>' if r['name'] in PLAN_SWAPS else '')
    return (f"<tr><td><div class='dexname'>{sprite(r['sid'], r.get('form', '0'), size='m')}<div><b>{E(disp(r['name']))}</b>{party}<div class='legend'>{E(types)} · {b['HP']}/{b['Atk']}/{b['Def']}/{b['SpA']}/{b['SpD']}/{b['Spe']} · {E(where)}</div></div></div></td>"
            f"<td class='c' data-l='score'><b>{r['blend']:.2f}</b><div class='legend'>fights {r['fight']:.2f}<br>meta {r['general']:.2f}</div></td>"
            f"<td>{extra}</td>"
            f"<td>{E(abn(r['ability']))} · {E(', '.join(r['attacks']))}<div class='legend'>counters {len(r['counters'])} Ch9 foes · {E(fights_line(r))}</div></td></tr>")


def table(rs, head3, extra_fn, compact_from='C'):
    body = ''
    for t in 'SABCD':
        tr = [r for r in rs if r['tier'] == t]
        if not tr: continue
        h = f"<h3><span class='tier t{t}'>{t}</span> {E(WHY[t])} <span class='legend'>{len(tr)}</span></h3>"
        if t >= compact_from and len(tr) > 12:
            items = ', '.join(f"{E(disp(r['name']))} <span class='legend'>{r['blend']:.2f}</span>" for r in tr)
            body += f"<div class='panel pad'><details><summary>{h}</summary><p class='tlc'>{items}</p></details></div>"
            continue
        body += (f"<div class='panel pad'>{h}<div class='tablewrap'><table class='tlx'><thead><tr><th>Pokémon</th><th>Score</th>"
                 f"<th>{head3}</th><th>Best build (ability · attacks)</th></tr></thead><tbody>"
                 + ''.join(row(r, extra_fn(r)) for r in tr) + '</tbody></table></div></div>')
    return body


rows = T['rows']
cuts = ' · '.join(f"{t} ≥ {v:.2f}" for t, v in T['cut'][:-1])
LEG = (f"<li>One scale for all three tier tabs: score = 0.6 × fights + 0.4 × meta. Cut-offs {cuts}.</li>"
       "<li>Fights = measured on the remaining Ch9 hard fights (exact game data, fields), as a percentile of your boxes. "
       "Meta = Smogon tier + usage (singles and doubles) and base-stat total; Aevians use their kit's OP stars.</li>"
       "<li>Every Pokémon is scored at Lv 60 with its best legal build (Ch1–8 TMs, tutors ≤ 8 badges, Relearner, egg).</li>")

# --- Crests
def crest_extra(r):
    ct = CT.get(r['name'], {})
    g = ct.get('gain')
    gain = f" <span class='legend'>gain {g:+.2f}</span>" if g is not None else ''
    zp = f"<div class='ok'>Best last slot: {E(disp(r['zoro_partner']))}</div>" if r.get('zoro_partner') else ''
    return f"{E(r['crest'])}{gain}{zp}<div class='legend'>{E(CDESC.get(r['crest'], '')[:150])}</div>"
crest_rows = [r for r in rows if r['kind'] == 'crest']
s6 = (f'<section aria-labelledby="s6">\n  <h2 id="s6">Crests</h2>\n  <ul class="legend">{LEG}<li>Only crests you hold. '
      f'Gain = fight score with vs without the crest. Zoroark / Furret crest effects are situational (not in the damage model).</li></ul>\n'
      f'  {table(crest_rows, "Crest", crest_extra, "Z")}\n</section>\n')

# --- Aevians
def aev_extra(r):
    sp = r['name'].split(' (')[0]
    op, sig, meta, catch = KIT.get(sp, (1, '', '', ''))
    return (f"<span class='op'>{'★' * op}{'☆' * (3 - op)}</span> {E(sig)}<div class='legend'>Like: {E(meta)}. Catch: {E(catch)}</div>")
aev_rows = [r for r in rows if r['kind'] == 'aevian']
s7 = (f'<section aria-labelledby="s7">\n  <h2 id="s7">Aevian forms</h2>\n  <ul class="legend">{LEG}'
      f'<li>OP ★ = how broken the kit is (signature move / ability) vs meta Pokémon with the same tools.</li></ul>\n'
      f'  {table(aev_rows, "Kit (learn level)", aev_extra, "Z")}\n</section>\n')

# --- Everything else
reg_rows = [r for r in rows if r['kind'] == 'regular']
s8 = (f'<section aria-labelledby="s8">\n  <h2 id="s8">Tier list (all other Pokémon)</h2>\n  <ul class="legend">{LEG}'
      f'<li>Regional forms and fusions included; crests and Aevians have their own tabs. C and D tiers are folded.</li></ul>\n'
      f'  {table(reg_rows, "Meta (Smogon)", lambda r: E(r["meta_label"]))}\n</section>\n')

CSS = ('.tlx td, .tlx th { padding: 5px 8px; border-bottom: 1px solid var(--line); text-align: left; font-size: 13px; vertical-align: top }'
       ' .tlx .c { text-align: center; font-family: var(--mono) } .tlx .op { color: #b45309; letter-spacing: 1px; white-space: nowrap }'
       ' .tlc { font-size: 13px; line-height: 1.7; margin: 6px 0 0 } details > summary { cursor: pointer; list-style: none } details > summary h3 { display: inline }'
       ' .tier { display: inline-block; min-width: 22px; text-align: center; border-radius: 4px; font-weight: 700; margin-right: 6px }'
       ' .tS { background: #7c3aed22 } .tA { background: #16a34a22 } .tB { background: #2563eb22 } .tC { background: #ca8a0422 } .tD { background: #64748b22 }'
       ' @media (max-width: 680px) { .tlx thead { display: none } .tlx tr { display: grid; grid-template-columns: 1fr; padding: 6px 0;'
       ' border-bottom: 1px solid var(--line) } .tlx td { border: 0 !important } .tlx td[data-l]::before { content: attr(data-l); margin-right: 6px;'
       ' font: 500 10px var(--mono); color: var(--muted); text-transform: uppercase } .tlx .c { text-align: left } }')
page = open(OUT, encoding='utf-8').read()
for s in ('s6', 's7', 's8'):
    page = re.sub(rf'<section aria-labelledby="{s}">.*?</section>\s*', '', page, flags=re.S)
anchor = page.rfind('<section aria-labelledby="s5">') if '<section aria-labelledby="s5">' in page else page.rfind('<footer')
page = page[:anchor] + s6 + s7 + s8 + page[anchor:]
page = re.sub(r'\.tlx td, \.tlx th \{.*?(?=</style>)', '', page, flags=re.S)
page = page.replace('</style>', CSS + '</style>', 1)
open(OUT, 'w', encoding='utf-8').write(page)
import collections
print('tier tabs:', {k: dict(collections.Counter(r['tier'] for r in rows if r['kind'] == k)) for k in ('crest', 'aevian', 'regular')})
