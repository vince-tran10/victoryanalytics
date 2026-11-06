"""Extra panels for the report: team-rules check with defensive/offensive matrices, next-fights card, level info."""
import json, os, re, html, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from dataset import Data
from bosses import FIELD, WALK
E = html.escape
TYPES = ['NORMAL', 'FIRE', 'WATER', 'ELECTRIC', 'GRASS', 'ICE', 'FIGHTING', 'POISON', 'GROUND', 'FLYING', 'PSYCHIC', 'BUG',
         'ROCK', 'GHOST', 'DRAGON', 'DARK', 'STEEL', 'FAIRY']
IMM = {'Flash Fire': 'FIRE', 'Levitate': 'GROUND', 'Water Absorb': 'WATER', 'Storm Drain': 'WATER', 'Dry Skin': 'WATER',
       'Volt Absorb': 'ELECTRIC', 'Lightning Rod': 'ELECTRIC', 'Motor Drive': 'ELECTRIC', 'Sap Sipper': 'GRASS',
       'Earth Eater': 'GROUND', 'Well-Baked Body': 'FIRE'}
CREST_IMM = {'Whiscash Crest': 'GRASS'}
SETUP = {'Swords Dance', 'Dragon Dance', 'Nasty Plot', 'Calm Mind', 'Quiver Dance', 'Shell Smash', 'Bulk Up', 'Agility',
         'Rock Polish', 'Shift Gear', 'Coil', 'Belly Drum', 'Tail Glow', 'Work Up', 'Growth', 'Victory Dance', 'Tidy Up',
         'Hone Claws', 'Iron Defense', 'Cosmic Power', 'Amnesia', 'Curse', 'Tailwind', 'Trick Room', 'Baton Pass'}
SPEED_AB = {'Speed Boost', 'Unburden', 'Moxie', 'Swift Swim', 'Chlorophyll', 'Sand Rush', 'Slush Rush', 'Surge Surfer', 'Beast Boost'}
D = Data(os.path.join(HERE, '..', '..', 'workspace'))
MV = {v['MoveName']: v for v in D.moves.values()}


def chart(atk, types):
    m = 1.0
    for t in types:
        ch = D.chart.get(t.capitalize(), {})
        if atk in ch.get('Immunities', []): m *= 0
        elif atk in ch.get('Weaknesses', []): m *= 2
        elif atk in ch.get('Resistances', []): m *= 0.5
    return m


def defend(atk, types, ability, item):
    if IMM.get(ability) == atk or CREST_IMM.get(item) == atk:
        return 0.0
    m = chart(atk, types)
    if ability == 'Thick Fat' and atk in ('FIRE', 'ICE'):
        m /= 2
    return m


def attack_types(moves):
    return [MV[m]['Type'] for m in moves if m in MV and MV[m]['Category'] != 'Status']


def fmt(v):
    return '' if v == 1 else ('0' if v == 0 else {0.25: '¼', 0.5: '½', 2: '2×', 4: '4×'}.get(v, f'{v:g}×'))


def rules_panel(team):
    """team: list of (name, types 'A/B', ability, item, moves)."""
    mons = [(n, [t.upper() for t in ty.split('/')], ab, it, mv) for n, ty, ab, it, mv in team]
    drow, orow, weak3, nores, nose, pos = [], [], [], [], [], []
    for t in TYPES:
        dv = [defend(t, ty, ab, it) for _, ty, ab, it, _ in mons]
        w, r = sum(v >= 2 for v in dv), sum(v <= .5 for v in dv)
        if w >= 3: weak3.append(t)
        if r == 0: nores.append(t)
        if w - r > 0: pos.append(t)
        cells = ''.join(f'<td class="m {"mw" if v >= 2 else ("mr" if v <= .5 else "")}">{fmt(v)}</td>' for v in dv)
        drow.append(f'<tr><th class="ty">{t.capitalize()}</th>{cells}<td class="c mw-c">{w or ""}</td><td class="c mr-c">{r or ""}</td>'
                    f'<td class="c n{"p" if w - r > 0 else ("n" if w - r < 0 else "z")}">{w - r:+d}</td></tr>')
        ov = []
        for _, _, _, _, mv in mons:
            best = max((chart(a, [t]) for a in attack_types(mv)), default=1)
            ov.append(best)
        se, nve = sum(v >= 2 for v in ov), sum(v <= .5 for v in ov)
        if se == 0: nose.append(t)
        cells = ''.join(f'<td class="m {"mr" if v >= 2 else ("mw" if v <= .5 else "")}">{"2×" if v >= 2 else ("½" if v <= .5 and v > 0 else ("0" if v == 0 else ""))}</td>' for v in ov)
        orow.append(f'<tr><th class="ty">{t.capitalize()}</th>{cells}<td class="c mr-c">{se or ""}</td><td class="c mw-c">{nve or ""}</td>'
                    f'<td class="c n{"n" if se - nve > 0 else ("p" if se - nve < 0 else "z")}">{se - nve:+d}</td></tr>')
    head = ''.join(f'<th class="mh">{E(n.split("-")[0][:7])}</th>' for n, *_ in mons)
    ok = lambda b: '<span class="ok">✓</span>' if b else '<span class="bad">✗ fail</span>'
    checks = (f'<ul class="rules"><li>{ok(not weak3)} No type hits 3+ super-effectively'
              f'{(": " + E(", ".join(t.capitalize() for t in weak3))) if weak3 else ""}</li>'
              f'<li>{ok(not nores)} Every type resisted'
              f'{(": none for " + E(", ".join(t.capitalize() for t in nores))) if nores else ""}</li>'
              f'<li>{ok(not nose)} Every type hit super-effectively'
              f'{(": nothing hits " + E(", ".join(t.capitalize() for t in nose))) if nose else ""}</li>'
              f'<li class="legend">Watch: {E(", ".join(t.capitalize() for t in pos)) or "none"}</li></ul>')
    tbl = lambda title, a, b, rows: (f'<div class="mx"><h4>{title}</h4><div class="tablewrap"><table class="mxt"><thead><tr><th></th>{head}'
                                     f'<th class="c">{a}</th><th class="c">{b}</th><th class="c">Net</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div></div>')
    return (f'<div class="panel pad rulesp"><h3>Team rules</h3>{checks}<details class="mxd"><summary>Show matrices</summary><div class="mxs">'
            + tbl('Defensive matrix', 'Weak', 'Resist', drow) + tbl('Offensive matrix', 'SE', 'NVE', orow) + '</div></details></div>')


def story_order(base):
    ev = [e for e in json.load(open(os.path.join(base, 'team', 'walk_ch8.json'))) if e['type'] == 'trainer']
    order = {}
    for match, key, *_ in WALK:
        nth = int(match.rsplit('#', 1)[1]) if re.search(r'#\d+$', match) else 0
        mt = re.sub(r'#\d+$', '', match)
        hits = [i for i, t in enumerate(ev) if mt in t['trainer'] and 'Partner' not in t['trainer']]
        if hits:
            order[key] = hits[nth - 1] if nth and len(hits) >= nth else max(hits, key=lambda i: len(ev[i]['mons']))
    return order


def next_fights(plans, team, base, n=3, short=None, disp=lambda x: x):
    order = story_order(base)
    plans = sorted(plans, key=lambda p: order.get(p['key'], 999))[:n]
    tm = {disp(x[0]): x for x in team}
    cards = []
    for p in plans:
        f = FIELD.get(p['field']) or {}
        users = []
        for nm_, ty, ab, it, mv in team:
            for m in mv:
                v = MV.get(m)
                if not v or v['Category'] == 'Status': continue
                mid = re.sub(r'[^A-Z]', '', m.upper())
                if f.get('types', {}).get(v['Type'], 1) * f.get('moves', {}).get(mid, 1) >= 1.2 or (f.get('ground_vs_nonground') and v['Type'] == 'GROUND'):
                    users.append(f'{nm_} ({m})'); break
        thr = []
        for fo in p['foes']:
            setup = [m for m in fo['moves'] if m in SETUP]
            spd = fo['ability'] in SPEED_AB
            ohko = fo['threat_dmg'] >= 100
            if not (setup or spd or ohko):
                continue
            why = []
            if setup: why.append(' + '.join(setup))
            if spd: why.append(fo['ability'])
            if ohko: why.append(f"{fo['threat_move']} one-shots {disp(fo['threat_to'])}")
            ans = disp(fo['answer']) + f" ({fo['answer_move']}, {round(fo['answer_dmg'])}%)"
            if setup or spd:
                ans = 'Musharna Glares it, then ' + ans
            thr.append((ohko, f'<li><b>{E(fo["foe"])}</b> <span class="legend">{E("; ".join(why))}</span> → {E(ans)}</li>'))
        thr = [t for _, t in sorted(thr, key=lambda x: not x[0])][:4]
        leads = ' + '.join(disp(x) for x in p['leads'])
        ko = sum(1 for fo in p['foes'] if fo['answer_dmg'] >= 100)
        cards.append(f'''<div class="panel pad nf"><h4>{E((short or {}).get(p["key"], p["label"]))} <span class="legend">{E(p["format"])} · {E(p["field"])}</span></h4>
<div><b>Lead:</b> {E(leads)}</div>
{('<ul class="plain">' + "".join(thr) + '</ul>') if thr else ''}</div>''')
    return '<div class="nfs">' + ''.join(cards) + '</div>'


CSS = '''
.rulesp .rules {{ margin: 0; padding-left: 0; list-style: none; display: grid; gap: 4px; font-size: 13.5px }}
.rulesp .bad {{ color: var(--bad); font: 500 12px var(--mono) }}
.mxs {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(330px, 1fr)); gap: 14px }}
.mx h4, .nf h4 {{ margin: 0 0 6px; font-family: var(--display); font-size: 14px }}
.mxt {{ font-size: 11.5px; width: auto; min-width: 100% }}
.mxt th, .mxt td {{ padding: 3px 5px; border-bottom: 1px solid var(--line); text-align: center; white-space: nowrap }}
.mxt th.ty {{ text-align: left; font: 500 11px var(--mono); color: var(--muted) }}
.mxt .mh {{ font: 500 10px var(--mono); color: var(--muted); text-transform: none; letter-spacing: 0 }}
.mxt .m.mw {{ background: var(--bad-soft); color: var(--bad); font-weight: 600 }}
.mxt .m.mr {{ background: var(--good-soft); color: var(--good); font-weight: 600 }}
.mxt .c {{ font-family: var(--mono); font-weight: 600 }} .mxt .mw-c {{ color: var(--bad) }} .mxt .mr-c {{ color: var(--good) }}
.mxt .np {{ background: var(--bad-soft); color: var(--bad) }} .mxt .nn {{ background: var(--good-soft); color: var(--good) }} .mxt .nz {{ color: var(--muted) }}
.nfs {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px }}
.nf {{ font-size: 13.5px }}
.mxd summary, .tierd > summary {{ cursor: pointer; font: 600 13px var(--display); color: var(--accent); padding: 6px 0 }}
.mxd[open] summary {{ margin-bottom: 8px }} .nfh {{ margin-top: 4px }}
'''
