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


def rules_panel(team, chapter=None, disp=lambda x: x):
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
    if chapter:
        c = chapter; mi = c['misses']
        miss = '; '.join(f"{E(m['foe'])} ({E(m['fight'])}): {E(disp(m['best']))} {m['dmg']}%" for m in mi)
        checks = (f'<ul class="rules"><li class="legend">Chapter rules: only the {c["fights"]} hard fights left count '
                  f'({c["foes"]} Pokémon). Types = the moves they actually use, after field changes.</li>'
                  f'<li>{ok(not c["weak3"])} No attack type they use hits 3+ super-effectively'
                  f'{(": " + E(", ".join(c["weak3"]))) if c["weak3"] else ""}</li>'
                  f'<li>{ok(not c["nores"])} Every attack type they use is resisted'
                  f'{(": none for " + E(", ".join(c["nores"]))) if c["nores"] else ""}</li>'
                  f'<li>{ok(len(mi) <= 2)} Every opposing Pokémon is hit super-effectively or one-shot'
                  f'{(" — " + str(len(mi)) + " allowed miss" + ("es" if len(mi) != 1 else "") + ": " + miss) if mi else ""}</li>'
                  f'<li class="legend">One-off types (tiebreak only): {E(", ".join(c["minor"])) or "none"}</li></ul>')
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


def next_fights(plans, team, base, n=3, short=None, disp=lambda x: x, keep_order=False):
    order = story_order(base)
    plans = (plans if keep_order else sorted(plans, key=lambda p: order.get(p['key'], 999)))[:n]
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
        cards.append(f'''<div class="panel pad nf"><h4>{E((short or {}).get(p["key"], p["label"]))} <span class="legend">{E(p["format"])}{" · Boss" if "boss" in p["label"].lower() else ""} · {E(p["field"])}</span></h4>
<div class="legend nfn">{E(p.get("notes", ""))}</div>
<div><b>Lead:</b> {E(leads)}</div>
{('<div><b>Field boosts:</b> ' + E(", ".join(users)) + '</div>') if users else '<div class="legend">No field boost on your six</div>'}
{('<ul class="plain">' + "".join(thr) + '</ul>') if thr else ''}</div>''')
    return '<div class="nfs">' + ''.join(cards) + '</div>'


# Hand-checked against the walkthrough's trainer classes (7 Nov): bosses + real story/key fights, no grunt fodder.
HARD_WHY = {
    'kyogre': 'Legendary boss (optional, Saving Amber)',
    'eli': 'Misfortunate Duo story fight, 10 mons, Venam partner',
    'geara': 'Two Xen Executives, 12 mons, Melia partner',
    'giratina': 'Rift boss, crested partners',
    'holly': 'Commander Holly quest fight, Lv 55–58 (over cap)',
    'manaphy': 'Boss, Lv 60',
    'factory': 'Mystery trainer, Lv 60–64 (over cap)',
    'amber': 'Gym leader (Lyric Badge)',
    # earlier ones, kept for the record
    'aelita': 'Rival', 'narcissa': 'Gym leader', 'narcissa1': 'Gauntlet', 'narcissa2': 'Gauntlet', 'texen': 'Gym leader',
    'groudon': 'Legendary boss', 'crawli': 'Head Ranger', 'tommen': 'Xen boss',
}
NOT_HARD = {'danni': 'Team Xen grunts', 'troye': 'Team Xen grunts', 'zena': 'Xen Analyst, 4 mons',
            'jenner': 'Story fight but 4 mons at Lv 50–51', 'marcie': '4 mons at Lv 53–54', 'neved': 'Optional',
            'guard1': 'Optional', 'guard2': 'Optional'}


def is_hard(p):
    """Hard = a boss or a real story/key fight (gym leader, executives, named story trainers), never grunt fodder."""
    if p['key'] in HARD_WHY: return True
    if p['key'] in NOT_HARD: return False
    return 'boss' in (p['label'] + ' ' + p.get('notes', '')).lower()   # unknown new fight: only bosses by default


def hard_fights(plans, team, base, short=None, disp=lambda x: x):
    """All remaining hard fights (bosses and real story fights, no grunts): overview table + one card each."""
    order = story_order(base)
    hard = [p for p in sorted(plans, key=lambda p: order.get(p['key'], 999)) if is_hard(p)]
    rows = []
    for i, p in enumerate(hard, 1):
        boss = 'boss' in (p['label'] + ' ' + p.get('notes', '')).lower()
        _base = lambda nm: re.sub(r'\s*\(bars? [\d-]+\)$', '', nm)
        n = len({_base(fo['foe']) for fo in p['foes']})   # a boss split into HP-bar phases is still one Pokémon
        _bars = [int(x) for fo in p['foes'] for x in re.findall(r'\d+', (re.search(r'\(bars? ([\d-]+)\)$', fo['foe']) or [None, ''])[1])]
        name = (short or {}).get(p['key'], re.sub(r' \(.*?\)', '', re.split(r' [–-] ', p['label'])[0]))
        if name == '???': name = '??? (Factory)'
        opt = ' <span class="legend">optional</span>' if 'optional' in p['label'].lower() else ''
        risk = sum(1 for fo in p['foes'] if fo['threat_dmg'] >= 100)
        if boss:
            best = p['foes'][0]
            _m = re.search(r'\(bars? (\d+)(?:-(\d+))?\)$', best['foe'])
            _rowbars = (int(_m.group(2) or _m.group(1)) - int(_m.group(1)) + 1) if _m else 1
            _per_bar = best['answer_dmg'] * _rowbars
            st = f"best hit {round(_per_bar)}% of a bar ({disp(best['answer'])}) · {max(_bars) if _bars else 1} HP bars"
            cls = 'bad' if _per_bar < 50 else 'warn'
        else:
            ko = sum(1 for fo in p['foes'] if fo['answer_dmg'] >= 100)
            st = f"one-shot {ko}/{n}"
            cls = 'ok' if ko == n and risk <= 1 else 'warn'
        st += f" · {risk} can one-shot us" if risk and not boss else ''
        fmt = f'<span class="fmt {p["format"].lower()}">{E(p["format"])}</span>'
        rows.append(f'<tr><td class="c">{i}</td><td><b>{E(name)}</b>{opt}</td><td>{fmt}</td>'
                    f'<td>{"<span class=bossb>Boss</span>" if boss else ""}</td><td>{E(p["field"])}</td><td class="c">{n}</td><td class="legend">{E(HARD_WHY.get(p["key"], ""))}</td>'
                    f'<td>{E(" + ".join(disp(x) for x in p["leads"]))}</td><td class="st {cls}">{E(st)}</td></tr>')
    table = ('<div class="panel pad"><h3>Hard fights left <span class="legend">bosses and real story fights, no grunts · story order</span></h3>'
             '<div class="tw"><table class="hft"><thead><tr><th>#</th><th>Fight</th><th>Format</th><th>Boss</th><th>Field</th>'
             '<th>Mons</th><th>Why hard</th><th>Lead</th><th>Your six</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div></div>')
    return table + next_fights(hard, team, base, len(hard), short, disp, keep_order=True)


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
.nf {{ font-size: 13.5px }} .nfn {{ margin: 0 0 6px; font-size: 12px }}
.hft td, .hft th {{ padding: 6px 8px; border-bottom: 1px solid var(--line); text-align: left; font-size: 13px }}
.hft .c {{ text-align: center; font-family: var(--mono) }} .tw {{ overflow-x: auto }}
.fmt {{ font: 600 11px var(--mono); padding: 2px 6px; border-radius: 4px; background: var(--line) }}
.fmt.singles {{ color: var(--lead); }} .fmt.doubles {{ color: var(--mid); }}
.bossb {{ font: 700 11px var(--mono); padding: 2px 6px; border-radius: 4px; background: var(--bad-soft); color: var(--bad) }}
.hft .st {{ font-size: 12.5px; white-space: nowrap }} .hft .st.ok {{ color: var(--good) }} .hft .st.warn {{ color: #b45309 }} .hft .st.bad {{ color: var(--bad); font-weight: 600 }}
.mxd summary, .tierd > summary {{ cursor: pointer; font: 600 13px var(--display); color: var(--accent); padding: 6px 0 }}
.mxd[open] summary {{ margin-bottom: 8px }} .nfh {{ margin-top: 4px }}
'''
