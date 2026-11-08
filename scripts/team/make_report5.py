"""Chapter 8 report: team table, fight readiness, tier list, export-verified to-do, hidden metadata.

usage: make_report5.py NEW_EXPORT OLD_EXPORT F11_native F11_Singles F11_Doubles PROMOTE_JSON OUT
To-dos are checked against NEW_EXPORT: anything the export shows as done is dropped.
"""
import json, sys, html, os, hashlib, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from current_box import current_rows, tier as tier_of
import sheet_extras as SX

NEWX, OLDX, F9N, F9S, F9D, PROMO, OUT = sys.argv[1:8]
cur, ACT = current_rows(NEWX, OLDX, F9N)
party = {d['species']: d for d in cur if d['box'] == 'Party'}
rows = []
for d in cur:
    if d['box'] in ('Overflow', 'Staging') or d['score'] is None:
        continue
    rows.append(dict(name=d['name'], where=d['box'], level=d['level'], score=d['score'], types=d['types'],
                     best=sorted(d['solo'], key=d['solo'].get, reverse=True), solo=d['solo'], attacks=d['attacks'], ability=d['ability']))
rows.sort(key=lambda r: (r['where'] != 'Party', -r['score']))
rows.sort(key=lambda r: -r['score'])
promo = json.load(open(PROMO))
BLURB = json.load(open(os.path.join(os.path.dirname(os.path.abspath(F9N)), 'blurbs.json')))
fn, fs, fd = (json.load(open(p)) for p in (F9N, F9S, F9D))
E = html.escape
TYPE = {'Normal': ('#A8A77A', '#1d1d12'), 'Fire': ('#EE8130', '#2a1200'), 'Water': ('#6390F0', '#0a1530'),
        'Electric': ('#F7D02C', '#2b2300'), 'Grass': ('#7AC74C', '#132608'), 'Ice': ('#96D9D6', '#0d2a29'),
        'Fighting': ('#C22E28', '#ffffff'), 'Poison': ('#A33EA1', '#ffffff'), 'Ground': ('#E2BF65', '#2b2208'),
        'Flying': ('#A98FF3', '#1a1036'), 'Psychic': ('#F95587', '#2e0414'), 'Bug': ('#A6B91A', '#1c2003'),
        'Rock': ('#B6A136', '#221d05'), 'Ghost': ('#735797', '#ffffff'), 'Dragon': ('#6F35FC', '#ffffff'),
        'Dark': ('#705746', '#ffffff'), 'Steel': ('#B7B7CE', '#1b1b2a'), 'Fairy': ('#D685AD', '#2b0c1c')}
SHORT = {'aelita': 'Aelita', 'narcissa': 'Narcissa', 'danni': 'Danni & Layla', 'troye': 'Troye & Helen', 'zena': 'Zena',
         'kyogre': 'Kyogre', 'holly': 'Holly & Rorim', 'manaphy': 'Manaphy', 'factory': '??? (Factory)', 'marcie': 'Marcie & Chikie',
         'texen': 'Texen', 'guard1': 'Guard #1', 'guard2': 'Guard #2', 'tommen': 'Tommen', 'groudon': 'Groudon',
         'crawli': 'Crawli', 'neved': 'Neved', 'eli': 'Eli & Sharon', 'jenner': 'Jenner', 'geara': 'Geara & Zetta',
         'giratina': 'Giratina', 'amber': 'Amber'}


def chips(types):
    out = []
    for t in [x for x in types.split('/') if x]:
        bg, fg = TYPE.get(t, ('#888', '#fff'))
        out.append(f'<span class="type" style="background:{bg};color:{fg}">{E(t)}</span>')
    return ''.join(out)


def disp(n):
    return (n.replace(' (Aevian Form Male)', '-Aevian').replace(' (Aevian Form)', '-Aevian')
             .replace(' (Icy Aevian Form)', '-Aevian (Icy)').replace(' (Hisuian Form)', '-Hisui')
             .replace(' (Lunatone Dominant Fusion)', '-Idol').replace(' (Solrock Dominant Fusion)', '-Idol'))


# ---------------------------------------------------------------- 1) team
# (role, name, types, ability, nature, evs, item, moves[(move, is_new)], change notes)
TEAM = [   # best six for the 7 remaining hard fights on exact game data (8 Nov); roles = game plan (identity), not matchups
    ('Lead', 'Vikavolt', 'Bug/Electric', 'Levitate', 'Modest', '252 HP / 252 SpA / 4 SpD', 'Magnet',
     [('Thunderbolt', 0), ('Bug Buzz', 0), ('Sticky Web', 0), ('Protect', 0)], []),
    ('Lead', 'Ludicolo', 'Water/Grass', 'Own Tempo', 'Modest', '252 HP / 252 SpA / 4 SpD', 'Mystic Water',
     [('Fake Out', 0), ('Energy Ball', 0), ('Hydro Pump', 0), ('Protect', 0)], []),
    ('Mid', 'Rhyperior', 'Ground/Rock', 'Solid Rock', 'Adamant', '252 HP / 252 Atk / 4 SpD', 'Hard Stone',
     [('Stone Edge', 0), ('Headlong Rush', 0), ('Fire Fang', 0), ('Protect', 0)], []),
    ('Mid', 'Armarouge', 'Fire/Psychic', 'Flash Fire', 'Modest', '252 HP / 252 SpA / 4 SpD', 'Sitrus Berry',
     [('Flamethrower', 0), ('Psyshock', 0), ('Calm Mind', 0), ('Protect', 0)], []),
    ('Mid', 'Musharna-Aevian', 'Dark/Fairy', 'Tough Claws', 'Adamant', '252 HP / 252 Atk / 4 SpD', 'Sitrus Berry',
     [('Play Rough', 0), ('Throat Chop', 0), ('Glare', 0), ('Protect', 0)], []),
    ('Closer', 'Annihilape', 'Fighting/Ghost', 'Defiant', 'Adamant', '252 Atk / 252 Spe / 4 HP', 'Black Belt',
     [('Close Combat', 0), ('Rage Fist', 0), ('Sucker Punch', 0), ('Protect', 0)], []),
]
IDENTITY = ('<b>Identity</b> Slow, hard-hitting core (Rhyperior, Armarouge) backed by speed control: '
            'Vikavolt\'s Sticky Web, Musharna\'s Glare, Ludicolo\'s Fake Out. Annihilape is the fast cleaner.')
PLAY = [IDENTITY,
        '<b>Lead (turns 1–2)</b> Vikavolt sets Sticky Web; in doubles Ludicolo Fake Outs the biggest threat so Web goes up safely',
        '<b>Mid</b> Rhyperior and Armarouge do the damage on slowed foes; Armarouge Calm Minds when it can\'t be hurt much; '
        'Musharna Glares anything still faster',
        '<b>Close</b> Annihilape: fastest member, Sucker Punch priority, Rage Fist strongest late after taking hits',
        '<b>Singles</b> lead Vikavolt (Web, then Thunderbolt). <b>Speed Boost users</b> Protect turn 1, attack turn 2']
JOB = {'Annihilape': 'Fastest hitter.',
       'Ludicolo': 'Fake Out lead: a free turn for Annihilape. Grass + Water hits the Water/Ground mons.',
       'Armarouge': 'Fire/Psychic special attacker; Calm Mind turns it into a sweeper.',
       'Vikavolt': 'Electric/Bug special hitter (Magnet); Levitate dodges Ground. Sticky Web slows the foe team.',
       'Musharna-Aevian': 'Glare (never misses) halves a sweeper\'s Speed. Tough Claws Play Rough / Throat Chop.',
       'Gholdengo': 'Make It Rain hits both foes (1.5x on Big Top). Immune to status moves.',
       'Rhyperior': 'Resists Fire. Stone Edge (Hard Stone, 1.5x on Mountain and Volcanic Top) deals with Fire mons and fliers.',
       'Glaceon': 'Icy Wind slows the back line for Golisopod. Freeze-Dry and Blizzard are your Groudon answer.',
       'Golisopod-Aevian': 'Win condition. Skill Link makes Bone Rush and Pin Missile 125 power. After one Swords Dance it one-shots 60 of 68 boss mons.',
       'Leavanny-Aevian': 'Rage Powder pulls attacks so Golisopod gets a free Swords Dance; Focus Sash guarantees it survives that turn. Intimidate on entry.'}
EVOLVE_FIRST = {}
FIGHT = os.environ.get('FIGHT', '')
COUNTERS = {'groudon': dict(title='Groudon', note='Boss · Deep Earth · Drought sun · 1 shield', six=[
    ('Glalie-Aevian', 'Grassy Surge', 'Adamant', '252 HP / 252 Atk / 4 SpD', 'Focus Sash', ['Grassy Glide', 'Wood Hammer', 'Rock Slide', 'Protect'], 'Lead: Grassy Terrain halves Earthquake'),
    ('Musharna-Aevian', 'Tough Claws', 'Adamant', '252 HP / 252 Atk / 4 SpD', 'Focus Sash', ['Play Rough', 'Throat Chop', 'Glare', 'Protect'], 'Glare it (paralysis)'),
    ('Exeggutor', 'Chlorophyll', 'Modest', '252 HP / 252 SpA / 4 SpD', 'Focus Sash', ['Leaf Storm', 'Giga Drain', 'Extrasensory', 'Protect'], 'Faster in sun; Leaf Storm 94%'),
    ('Glaceon', 'Ice Body', 'Modest', '252 HP / 252 SpA / 4 SpD', 'Focus Sash', ['Freeze-Dry', 'Blizzard', 'Icy Wind', 'Protect'], 'Freeze-Dry ~80%'),
    ('Camerupt', 'Solid Rock', 'Modest', '252 HP / 252 SpA / 4 SpD', 'Focus Sash', ['Eruption', 'Earth Power', 'Lava Plume', 'Protect'], 'Eruption at full HP ~72%'),
    ('Golisopod-Aevian', 'Skill Link', 'Adamant', '252 HP / 252 Atk / 4 SpD', 'Focus Sash', ['Bone Rush', 'Pin Missile', 'Swords Dance', 'Protect'], 'Back-up; takes Earthquake well')],
    plan=['Lead Glalie-Aevian: Grassy Terrain halves Earthquake and heals you',
          'Musharna Glares Groudon, then your slow hitters move first',
          'Exeggutor Leaf Storm (then switch or Giga Drain: Leaf Storm drops SpA)',
          'Glaceon / Camerupt finish it; Sashes let each survive one hit',
          "Don't stall: its Sitrus Berry and the terrain heal it too"]),
    'kyogre': dict(title='Kyogre', note='Optional boss · Water Surface · Drizzle rain · 3.4x HP · all six outspeed it', six=[
    ('Ludicolo', 'Swift Swim', 'Adamant', '252 HP / 252 Atk / 4 SpD', 'Sitrus Berry', ['Bullet Seed', 'Razor Leaf', 'Trailblaze', 'Protect'], 'Lead. Speed doubles in rain; resists Water 4x, takes ~39% max. Bullet Seed ~15% x4'),
    ('Heliolisk', 'Dry Skin', 'Timid', '252 SpA / 252 Spe / 4 HP', 'Sitrus Berry', ['Thunder', 'Thunderbolt', 'Discharge', 'Protect'], 'Immune to Water + heals in rain. Thunder never misses in rain, ~20% x3'),
    ('Electivire', 'Motor Drive', 'Jolly', '252 Atk / 252 Spe / 4 HP', 'Focus Sash', ['Thunder Punch', 'Cross Chop', 'Quick Attack', 'Protect'], '2 Thunder Punches ~30% each'),
    ('Boltund', 'Strong Jaw', 'Adamant', '252 HP / 252 Atk / 4 SpD', 'Focus Sash', ['Thunder Fang', 'Wild Charge', 'Spark', 'Protect'], '2 Thunder Fangs ~30% each'),
    ('Togedemaru', 'Sturdy', 'Adamant', '252 Atk / 252 Spe / 4 HP', 'Magnet', ['Zing Zap', 'Wild Charge', 'Spark', 'Protect'], 'Sturdy = built-in Sash, so it holds Magnet. 2 Zing Zaps ~33% each'),
    ('Meowscarada', 'Protean', 'Jolly', '252 Atk / 252 Spe / 4 HP', 'Focus Sash', ['Flower Trick', 'Knock Off', 'U-turn', 'Protect'], '2 Flower Tricks ~27% each (always crit)')],
    plan=['All six are faster than Kyogre in its own rain: you always hit first',
          'Lead Ludicolo, then Heliolisk: the two bulky ones go first, before Calm Mind boosts stack up',
          'Then the Sash/Sturdy hitters: each gets 2 hits (hit, survive on Sash, hit again)',
          'Heliolisk uses Thunder, not Thunderbolt: rain makes it 100% accurate',
          'No recoil moves (Wild Charge) on Sash users until their 2nd hit; total damage ~350% of what you need is 100%'])}
CF_PREEVO = {'Heliolisk': ('Helioptile', 'Sun Stone'), 'Boltund': ('Yamper', 'Lv 25')}
CF = COUNTERS.get(FIGHT)
CF_NAMES = [x[0] for x in CF['six']] if CF else []
NEXT_LV = max(fo['lvl'] or 0 for p in sorted(fn['plans'], key=lambda p: SX.story_order(os.path.dirname(os.path.dirname(os.path.abspath(F9N)))).get(p['key'], 999))[:3] for fo in p['foes'])
ACTIONS = {}   # export entry number -> what to do; read by box_audit.py for the red highlights
REPL = {('Musharna-Aevian', 'Glare'): 'Moonlight: paralysis halves a sweeper\'s Speed, so your slow hitters move first',
        ('Annihilape', 'Sucker Punch'): 'Fire Punch: priority hit on faster foes',
        ('Annihilape', 'Rage Fist'): 'Shadow Punch: Move Relearner, +50 power per hit taken',
        ('Gholdengo', 'Power Gem'): 'Recover: Move Relearner, hits the Fire types',
        ('Rhyperior', 'Rock Blast'): 'Rock Slide: Move Relearner, until Stone Edge at Lv 54'}
LATER = {('Rhyperior', 'Stone Edge'): 'Stone Edge comes at Lv 54 on its own (Rhyperior is Lv {lv}); replace Rock Slide then'}


def verify(name, ab, nat, evs, item, moves):
    """What the export says still needs doing for this party slot."""
    d = party.get(name)
    if not d:
        cands0 = [x for x in cur if x['species'] == name]
        d0 = min(cands0, key=lambda x: (x['box'] != 'Active', len(verify_mon(x, ab, nat, evs, item, moves))), default=None)
        if d0:
            TEAM_SRC[name] = (d0['species'], d0['n'], d0['box'])
        if d0 and not CF:
            ACTIONS[d0['n']] = f"Move into the party (part of the ideal six)"
        if CF:
            return [f"After {CF['title']}: back into the party"]
        out = [f"Put {name} in the party (now in {d0['box']} #{d0['n']})" if d0 else (EVOLVE_FIRST.get(name) or f'Put {name} in the party')]
        if d0:
            out += [c for c in verify_mon(d0, ab, nat, evs, item, moves)]
        return out
    return verify_mon(d, ab, nat, evs, item, moves)


def verify_mon(d, ab, nat, evs, item, moves):
    name = d['species']
    out = []
    want = {k: int(v) for v, k in (x.split() for x in evs.split(' / ')) if int(v) >= 100}
    have = {k for k, v in (d.get('evs') or {}).items() if v >= 100}
    if d.get('evs') is not None and set(want) != have:
        out.append('EVs: ' + ' / '.join(f'{v} {k}' for k, v in want.items()) + ' (now ' + (' / '.join(sorted(have)) or 'none') + ')')
    if d['item'] != item:
        out.append(f"Item: {d['item'] or 'none'} → {item}")
    if d.get('ability') != ab:
        out.append(f"Ability: {d.get('ability')} → {ab} (Ability Capsule)")
    if d.get('nature') != nat:
        out.append(f"Nature: {d.get('nature')} → {nat} (mint)")
    if (d.get('level') or 55) < 55:
        out.append(f"Lv {d['level']} → 55")
    _target = [m for m, _ in moves]
    _gone = [m for m in d['moves'] if m not in _target]
    for m in _target:
        if m not in d['moves']:
            rep = _gone.pop(0) if _gone else None
            out.append(LATER.get((name, m), f'Teach {m}' + (f' (replaces {rep})' if rep else '')).format(lv=d['level']))
    return out


def ev_lines(evs):
    parts = sorted(((int(v), k) for v, k in (x.split() for x in evs.split(' / '))), key=lambda t: -t[0])
    keep = parts[:2] + [t for t in parts[2:3] if t[0] >= 60]
    return '<ul class="evl">' + ''.join(f'<li><b class="num">{v}</b> {k}</li>' for v, k in keep) + '</ul>'


team_rows, team_todo, LEVELS = [], [], []
TEAM_CHANGES, CF_ISSUES, TEAM_SRC = {}, {}, {}
ANY_CHANGE = any(verify(t[1], t[3], t[4], t[5], t[6], t[7]) for t in TEAM)
prev = None
for role, name, types, ab, nat, evs, item, moves, changes in TEAM:
    changes = verify(name, ab, nat, evs, item, moves)
    TEAM_CHANGES[name] = list(changes)
    if CF and name in CF_NAMES:
        changes = [c if c.startswith(('Lv ', 'After ')) else f"After {CF['title']}: {c}" for c in changes]
    team_todo += [(f'{name}: {c}', 'high') for c in changes if not c.startswith('Lv ') and not c.startswith('After ')]
    LEVELS += [(name, c.split()[1]) for c in changes if c.startswith('Lv ')]
    moves = [(m, 2 if (name, m) in LATER and m not in party.get(name, {}).get('moves', []) else 0) for m, _ in moves]
    mv = ''.join(f'<li class="{"new" if n == 1 else ("soon" if n == 2 else "")}">{E(m)}</li>' for m, n in moves)
    ch = ('<ul class="chg">' + ''.join(f'<li>{E(c)}</li>' for c in changes) + '</ul>') if changes else '<span class="ok">Done ✓ (matches export)</span>'
    rc = f'<td class="role role-{role.lower()}" rowspan="2">{role}</td>' if role != prev else ''
    prev = role
    team_rows.append(f'''<tr>{rc}<td><strong>{E(name)}</strong><div class="chips">{chips(types)}</div></td>
<td>{E(ab)}<div class="legend">{E(nat)}</div></td><td>{ev_lines(evs)}</td><td>{E(item)}</td><td><ul class="mv">{mv}</ul></td><td>{ch}</td></tr>''')


def readiness():
    trs, tot, ko, fast = [], 0, 0, 0
    risk = {}
    for p in fn['plans']:
        F = p['foes']
        k = sum(f['answer_dmg'] >= 100 for f in F); kf = sum(f['answer_dmg'] >= 100 and f['answer_faster'] for f in F)
        tot += len(F); ko += k; fast += kf
        th = [f for f in F if f['threat_dmg'] >= 100]
        for f in th:
            risk[f['threat_to']] = risk.get(f['threat_to'], 0) + 1
        worst = max(F, key=lambda f: f['threat_dmg'])
        watch = (f"{worst['foe']}'s {worst['threat_move']} vs {disp(worst['threat_to'])}" if worst['threat_dmg'] >= 100 else 'nothing one-shots you')
        cls = 'good' if k == len(F) and len(th) <= 2 else ('warn' if k >= len(F) - 1 else 'bad')
        trs.append(f'<tr><td><strong>{E(SHORT[p["key"]])}</strong><div class="job">{E(p["field"])} · {E(p["format"])}</div></td>'
                   f'<td class="num r-{cls}">{k}/{len(F)}</td><td class="num">{kf}/{len(F)}</td><td class="num">{len(th)}</td><td>{E(watch)}</td></tr>')
    return trs, tot, ko, fast, risk


ready_rows, R_TOT, R_KO, R_FAST, R_RISK = readiness()


if LEVELS:
    team_todo.append(('Level the six to 55 (the cap; the next bosses are Lv ' + str(NEXT_LV) + '+): ' + ', '.join(f'{n} {lv}' for n, lv in LEVELS), 'mid'))
IDEAL = [t[1] for t in TEAM]
TEAM_X = [(t[1], t[2], t[3], t[6], [m for m, _ in t[7]]) for t in TEAM]
_CS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(F9N))), 'team', 'chapter_status.json')
RULES_HTML = SX.rules_panel(TEAM_X, json.load(open(_CS)) if os.path.exists(_CS) else None, disp)
NEXT_HTML = SX.hard_fights(fn['plans'], TEAM_X, os.path.dirname(os.path.dirname(os.path.abspath(F9N))), SHORT, disp)

def _leads_html():
    order = SX.story_order(os.path.dirname(os.path.dirname(os.path.abspath(F9N))))
    by = {}
    for p in sorted(fn['plans'], key=lambda p: order.get(p['key'], 999)):
        if not p.get('leads'): continue
        lab = re.split(r' [–-] ', p['label'])[0]; lab = re.sub(r' \(.*?\)', '', lab).replace('&', '&amp;')
        if lab == '???': lab = '??? (Factory)'
        by.setdefault(disp(p['leads'][0]), []).append(lab)
    items = ''.join(f'<li><b>{k}</b>: {", ".join(v)}</li>' for k, v in by.items())
    return f'<div class="panel pad"><h3>Lead by fight</h3>\n    <ul>{items}</ul>\n  </div>'
LEADS_HTML = _leads_html()
for d in cur:
    if d['box'] == 'Party' and d['species'] not in IDEAL and not (CF and d['species'] in CF_NAMES):
        ACTIONS[d['n']] = 'Move out of the party, back to the Active box'
        team_todo.append((f"{d['species']}: move out of the party, back to the Active box", 'high'))
CF_HTML = ''
if CF:
    rows_, todo_cf = [], []
    for nm_, ab_, nat_, evs_, item_, mv_, note_ in CF['six']:
        d = party.get(nm_)
        if d:
            issues = verify_mon(d, ab_, nat_, evs_, item_, [(m, 0) for m in mv_])
        else:
            pre, how = CF_PREEVO.get(nm_, (nm_, ''))
            d0 = min((x for x in cur if x['species'] == pre), key=lambda x: (x['box'] == 'Overflow', -(x.get('level') or 0)), default=None)
            if d0 and how:
                d0 = dict(d0, species=nm_, moves=[], ability=d0.get('ability'))
            issues = ([f"{pre} {d0['box']} #{d0['n']} → party" + (f", evolve ({how})" if how else '')] + verify_mon(d0, ab_, nat_, evs_, item_, [(m, 0) for m in mv_])) if d0 else [f'Put {nm_} in the party']
        _dd = d if d else d0
        if _dd: CF_ISSUES[nm_] = (_dd, [x for x in issues if '→ party' not in x and not x.startswith('Put ')])
        if issues: todo_cf.append((f'{CF["title"]} · {nm_}: ' + '; '.join(issues), 'high'))
        rows_.append(f'<tr><td><strong>{E(nm_)}</strong></td><td class="legend">{E(item_)}</td><td>{E(" / ".join(mv_))}</td><td>{E(note_)}</td>'
                     f'<td>{"<span class=ok>✓</span>" if not issues else "<span class=chg2>" + E("; ".join(issues)) + "</span>"}</td></tr>')
    _back = [x for x in IDEAL if x not in CF_NAMES]
    team_todo[:0] = todo_cf
    team_todo.append((f"After {CF['title']}: swap back to the main six (" + ', '.join(_back) + ' back in, with their usual items)', 'low'))
    CF_HTML = (f'<div class="panel pad cf"><h3>Now: {E(CF["title"])} <span class="legend">{E(CF["note"])} · hard-counter lineup, this fight only</span></h3>'
               f'<div class="tablewrap"><table class="cft"><tbody>{"".join(rows_)}</tbody></table></div>'
               f'<ol class="plain">{"".join("<li>" + E(x) + "</li>" for x in CF["plan"])}</ol></div>')


_BASE_SPE = {}
for _sid, _sp in SX.D.sp.items():
    for _idx in [k for k in _sp if k.isdigit()]:
        try:
            _f = SX.D.form(_sid, _idx)
            _nm = SX.D.nm(_sid) + ('' if _idx == '0' else f" ({_f.get('FormName')})")
            _BASE_SPE.setdefault(_nm, _f['BaseStats'][5] if len(_f.get('BaseStats') or []) > 5 else 0)
        except Exception:
            pass
def nat_pick(d, phys):
    """One nature: speed-invested builds take the Speed nature (Jolly/Timid), bulky ones the power nature (Adamant/Modest)."""
    fast = ev_pick(d, 'Atk').endswith('Spe')
    return ('Jolly' if fast else 'Adamant') if phys else ('Timid' if fast else 'Modest')
def ev_pick(d, key):
    """The two EV stats: the attacking stat + Speed if it's naturally fast (base >= 85, same as the engine), else HP."""
    spe = _BASE_SPE.get(d.get('name') or '', _BASE_SPE.get(d.get('final') or d['species'], 0))
    return f"252 {key} / 252 {'Spe' if spe >= 85 else 'HP'}"

KEEP_STATUS = {'Swords Dance', 'Dragon Dance', 'Nasty Plot', 'Calm Mind', 'Bulk Up', 'Quiver Dance', 'Shell Smash', 'Glare', 'Spore',
               'Sleep Powder', 'Sing', 'Belly Drum', 'Yawn', 'Fake Out', 'Leech Seed', 'Trick Room', 'Tailwind', 'Recover', 'Roost',
               'Slack Off', 'Rage Powder', 'Follow Me', 'Agility', 'Coil', 'Work Up', 'Hone Claws'}
UTILITY_ATK = {'Fake Out', 'U-turn', 'Volt Switch', 'Flip Turn', 'Rapid Spin', 'Icy Wind', 'Electroweb', 'Snarl'}
RECOVERY = {'Slack Off', 'Recover', 'Roost', 'Synthesis', 'Moonlight', 'Morning Sun', 'Soft-Boiled', 'Milk Drink', 'Rest'}
def move_value(m, moves, phys, rec, ability):
    v = SX.MV.get(m) or {}
    if m in UTILITY_ATK: return 2
    if v.get('Category') in ('Physical', 'Special') and v['Category'] != ('Physical' if phys else 'Special'): return 0.5
    same = [SX.MV.get(o) for o in moves if o != m and SX.MV.get(o) and SX.MV[o].get('Type') == v.get('Type') and SX.MV[o]['Category'] != 'Status']
    if v.get('Category') != 'Status' and any(int(o.get('Strength') or 0) > int(v.get('Strength') or 0) for o in same): return 1.0
    if m in rec: return 3
    if v.get('Category') == 'Status':
        if m in RECOVERY and (ability or '').replace(' ', '').upper() == 'REGENERATOR': return 1.5
        return 2 if m in KEEP_STATUS else 0
    return 1 + int(v.get('Strength') or 0) / 1000
def plan_moves(have, target, phys, ability):
    """target attacks (+Protect) -> list of 'Teach X (replaces Y)' lines; free slots keep the best existing moves."""
    keep = list(dict.fromkeys(list(target) + ['Protect']))[:4]
    rest = sorted((m for m in have if m not in keep), key=lambda m: -move_value(m, have, phys, set(target), ability))
    while len(keep) < 4 and rest:
        keep.append(rest.pop(0))
    drop = sorted((m for m in have if m not in keep), key=lambda m: move_value(m, have, phys, set(target), ability))
    return [f'Teach {m}' + (f' (replaces {drop.pop(0)})' if drop else '') for m in keep if m not in have]

# ---------------------------------------------------------------- 1b) relearner upgrades
UP = json.load(open(os.path.join(os.path.dirname(os.path.abspath(F9N)), 'upgrades_relearn.json')))
ORDER = [t[1] for t in TEAM]
up_cards, up_same, up_left, up_done = [], [], 0, []
up_names = set()
PROFILE = {}   # (species, export #, box) -> list of profile changes
NO_PROTECT = {'Lapras-Aevian'}   # agreed exceptions only: No Guard Sing + Dragon Dance + STAB Lapras
PROTECT_LIKE = {'Protect', 'Detect', "King's Shield", 'Spiky Shield', 'Baneful Bunker', 'Silk Trap', 'Obstruct', 'Burning Bulwark'}
for d in sorted((d for d in cur if d['box'] != 'Overflow' and d['species'] in UP),
                key=lambda d: (d['box'] != 'Party', ORDER.index(d['species']) if d['species'] in ORDER else 9, not UP[d['species']].get('big'), d['species'])):
    u = dict(UP[d['species']])
    if not (PROTECT_LIKE & set(u['moves'])) and d['species'] not in NO_PROTECT:   # standing rule: Protect is always the 4th move
        mv4 = list(u['moves'])
        i = max(j for j, m in enumerate(mv4) if m not in ('Swords Dance', 'Glare', 'Nasty Plot', 'Calm Mind', 'Dragon Dance', 'Bulk Up'))
        mv4[i] = 'Protect'; u['moves'] = mv4
    if sorted(u['moves']) == sorted(d['moves']) and not u.get('nature') and not u.get('ability') and d['box'] == 'Active' and 'later' not in u:
        if not u['why'].startswith(('Nothing', 'Already', 'Support')):
            up_done.append(d['species'])
        continue
    if set(u['moves']) == set(d['moves']) and 'Swords Dance' in u['moves'] + ['Swords Dance'] and u['why'].startswith(('Nothing', 'Already', 'Support')):
        up_same.append(d['species']); continue
    gaps = [m for m in u['moves'] if m not in d['moves']]
    natg = u.get('nature') and d.get('nature') != u['nature']
    abg = u.get('ability') and d.get('ability') != u['ability']
    done = not gaps and not natg and not abg
    up_left += 0 if done else 1
    if done or d['box'] == 'Party' or d['species'] in IDEAL:
        up_done.append(d['species']); continue
    gone = [m for m in d['moves'] if m not in u['moves']]
    mv = ''.join(f'<li class="{"new" if m in gaps else ""}">{E(m)}</li>' for m in u['moves'])
    extra = ''
    if natg: extra += f'<div class="chg2">Nature: {E(d.get("nature"))} → <b>{E(u["nature"])}</b> (mint)</div>'
    if abg: extra += f'<div class="chg2">Ability: {E(d.get("ability"))} → <b>{E(u["ability"])}</b> (Ability Capsule)</div>'
    if u.get('later'): extra += f'<div class="mnote">Later: {E(u["later"])}</div>'
    status = '<span class="ok">Done ✓</span>' if done else ('<span class="b big">big upgrade</span>' if u.get('big') else '<span class="b small">upgrade</span>')
    role = {t[1]: t[0].lower() for t in TEAM}.get(d['species'], '')
    up_names.add(d['species'])
    _fx = [f"Teach {m}" + (f" (replaces {o})" if o else '') for m, o in zip(gaps, gone + [None] * len(gaps))]
    if natg: _fx.append(f"Nature: {d.get('nature')} → {u['nature']} (mint)")
    if abg: _fx.append(f"Ability: {d.get('ability')} → {u['ability']} (Ability Capsule)")
    if u.get('later'): _fx.append('Later: ' + u['later'])
    PROFILE.setdefault((d['species'], d['n'], d['box']), []).extend(_fx)
    up_cards.append(f'''<li class="mon up{" isparty" if d["box"] == "Party" else ""}"><div class="mtop"><strong>{E(d["species"])}</strong>{status}</div>
<div class="chips">{chips(d["types"] or "")}<span class="lv">Lv {d["level"]}</span>{'<span class="b party">Party</span>' if d["box"] == "Party" else ''}</div>
<ul class="mv">{mv}</ul>{('<div class="mnote">Out: ' + E(', '.join(gone)) + '</div>') if gone and not done else ''}{extra}
</li>''')
up_same += [d['species'] for d in cur if d['box'] != 'Overflow' and d['species'] not in UP and d['species'] not in up_same and d['score']]
up_same = sorted(set(up_same))
# ---------------------------------------------------------------- 1c) build fixes (Active): EVs, nature, ability, Protect
PHYS_NAT, SPEC_NAT = {'Adamant', 'Jolly', 'Brave'}, {'Modest', 'Timid', 'Quiet'}
fix_cards = []
for d in sorted((d for d in cur if d['box'] == 'Active' and d.get('score') is not None), key=lambda d: d['species']):
    _own = [SX.MV.get(m) for m in d['moves']]
    _p, _s = (sum(1 for v in _own if v and v['Category'] == c) for c in ('Physical', 'Special'))
    if _p == _s:   # tie / no attacks: fall back to the engine's recommended attacks
        atk = [SX.MV.get(m) for m in (d.get('attacks') or [])]
        _p, _s = (sum(1 for v in atk if v and v['Category'] == c) for c in ('Physical', 'Special'))
    phys = _p >= _s
    key, nats = ('Atk', PHYS_NAT) if phys else ('SpA', SPEC_NAT)
    want_nat = nat_pick(d, phys)
    fx = []
    if (d.get('evs') or {}).get(key, 0) < 100:
        fx.append(f"EVs: {ev_pick(d, key)} (now {' / '.join(f'{v} {k}' for k, v in (d.get('evs') or {}).items() if v >= 100) or 'none'})")
    if d.get('nature') not in nats:
        fx.append(f"Nature: {d.get('nature')} → {want_nat} (mint)")
    if d.get('capsule') and d['capsule'][0].replace(' ', '').lower() != (d.get('ability') or '').replace(' ', '').lower():
        fx.append(f"Ability: {d.get('ability')} → {d['capsule'][0]} (Ability Capsule)")
    if not (PROTECT_LIKE & set(d['moves'])) and d['species'] not in up_names and d['species'] not in NO_PROTECT:
        KEEP = {'Swords Dance', 'Dragon Dance', 'Nasty Plot', 'Calm Mind', 'Bulk Up', 'Quiver Dance', 'Shell Smash', 'Glare', 'Spore',
                'Sleep Powder', 'Sing', 'Belly Drum', 'Yawn', 'Fake Out', 'Leech Seed', 'Trick Room', 'Tailwind', 'Recover', 'Roost', 'Slack Off', 'Rage Powder', 'Follow Me'}
        rec = set(d.get('attacks') or [])
        RECOVERY = {'Slack Off', 'Recover', 'Roost', 'Synthesis', 'Moonlight', 'Morning Sun', 'Soft-Boiled', 'Milk Drink', 'Rest'}
        def _val(m):
            v = SX.MV.get(m) or {}
            if m in ('Fake Out', 'U-turn', 'Volt Switch', 'Flip Turn', 'Rapid Spin', 'Icy Wind', 'Electroweb', 'Snarl'):
                return 2   # utility attacks: their job isn't damage
            if v.get('Category') in ('Physical', 'Special') and v['Category'] != ('Physical' if phys else 'Special'):
                return 0.5   # attack that doesn't use this build's attacking stat (e.g. Knock Off on special Tangrowth)
            _same = [SX.MV.get(o) for o in d['moves'] if o != m and SX.MV.get(o) and SX.MV[o].get('Type') == v.get('Type') and SX.MV[o]['Category'] != 'Status']
            if v.get('Category') != 'Status' and any(int(o.get('Strength') or 0) > int(v.get('Strength') or 0) for o in _same):
                return 1.0   # weaker duplicate of another attack of the same type (Psyshock next to Psychic)
            if m in rec: return 3
            if v.get('Category') == 'Status':
                if m in RECOVERY and (d.get('ability') or '').replace(' ', '').upper() == 'REGENERATOR':
                    return 1.5   # Regenerator already heals a third on every switch
                return 2 if m in KEEP else 0
            return 1 + int(v.get('Strength') or 0) / 1000
        drop = min(d['moves'], key=_val) if d['moves'] else None
        fx.append(f'Teach Protect (replaces {drop})' if drop and len(d['moves']) >= 4 else 'Teach Protect')
    if fx:
        PROFILE.setdefault((d['species'], d['n'], d['box']), []).extend(fx)
        fix_cards.append(f'<li class="mon up"><div class="mtop"><strong>{E(d["species"])}</strong><span class="legend">Active #{d["n"]}</span></div>'
                         f'<ul class="chg">{"".join("<li>" + E(x) + "</li>" for x in fx)}</ul></li>')
promo_cards = []
for p in promo:
    nat = p['nature'].split(' ')[0]
    now = next((d for d in cur if d['species'] in (p['final'], p['owned']) and d['box'] != 'Overflow'), None)
    src = now or next((d for d in cur if d['n'] == p['n']), None)
    mvs = [m.split(' (Lv')[0] for m in p['moves']]
    if now and now['species'] == p['final'] and set(mvs) <= set(now['moves']) and now.get('nature') == nat and (now.get('ability') or '').replace('W. ', 'Water ') == p['ability']:
        continue
    have = set(src['moves']) if src else set()
    mv = ''.join(f'<li class="{"" if m in have else "new"}">{E(m)}</li>' for m in mvs)
    where = 'in Active, finish the build' if now else f'Overflow #{p["n"]}'
    abl = f'{E(p["ability"])}' + (' (Ability Capsule)' if p.get('capsule') else '')
    promo_cards.append(f'''<li class="mon up"><div class="mtop"><strong>{E(p["final"])}</strong><span class="b promote">promote · {E(p["tier"])} tier</span></div>
<div class="chips"><span class="lv">{E(where)} · Lv {src["level"] if src else "?"}{(" " + E(p["owned"])) if p["owned"] != p["final"] else ""}</span></div>
<div class="mnote"><b>{abl}</b> · {E(p["nature"])} · {E(p["evs_txt"])}</div>
<ul class="mv">{mv}</ul>
<div class="mnote">{E(p.get("level_note", ""))}</div><div class="mnote">{E(p.get("why", ""))}</div></li>''')

# ---------------------------------------------------------------- 2) tier list
FLAGS = {  # community / role notes (short)
    'Golisopod (Aevian Form)': ('', 'Forum: "THE MVP" of a V14 team'),
    'Lapras (Aevian Form)': ('', 'No Guard: Sing and Rock Slide never miss'),
    'Musharna (Aevian Form)': ('', 'Trick Room setter for Chapter 9 (forum pick)'),
    'Glalie (Aevian Form)': ('', 'Rock Head (no recoil) + Grassy Surge; forum: "don\'t sleep on it"'),
    'Electrode (Hisuian Form)': ('', 'Forum: "breaks the midgame", but only with its crest'),
    'Ampharos (Aevian Form)': ('', 'Forum: "Trick Room god" once crested (late game)'),
    'Sylveon': ('', 'Pixilate spread moves rated for doubles (Hyper Voice tutor needs 9 badges)'),
    'Whiscash': ('', 'Crest: no weaknesses, +20% Atk/SpA'),
    'Gholdengo': ('', 'Status-immune, spread Make It Rain'),
    'Rhyperior': ('', 'Best Fire answer in your boxes'),
    'Annihilape': ('', 'Fastest hard hitter you own'),
    'Leavanny (Aevian Form)': ('', 'Support: scores low alone, but Rage Powder is what lets Golisopod sweep'),
    'Tangrowth': ('', 'Rage Powder + Sleep Powder, Regenerator'),
    'Amoonguss': ('', 'Rage Powder + Spore-style support, Regenerator'),
    'Furret': ('', 'Crest: free Substitute on entry, Baton Pass'),
    'Meowstic': ('', 'Mega stone owned; Megas unlock in Chapter 12'),
    'Chandelure': ('', 'Mega stone owned; Megas unlock in Chapter 12'),
    'Crawdaunt': ('', 'Adaptability; rated for Trick Room teams'),
    'Donphan': ('', 'Strong alone, but doubles up on Rhyperior and Golisopod\'s Ground hits and weaknesses; makes the six weaker if swapped in'),
    'Azumarill': ('', 'Huge Power. Your best bench mon: basically ties Gholdengo in the six'),
    'Feraligatr': ('', 'Evolve Totodile first (next level-up). Crested Feraligatr is a forum favourite later'),
    'Froslass (Aevian Form)': ('', 'Adaptability; peaks once it gets Water Spout or Muddy Water (not available yet)'),
    'Throh': ('', 'Guts; Wide Guard support in doubles'),
    'Lunatone (Lunatone Dominant Fusion)': ('', 'Lunar Idol: Levitate + 1.5x Ice moves'),
    'Glaceon': ('', 'Speed control + Groudon answer'),
}
IN_SIX = {'Annihilape', 'Gholdengo', 'Rhyperior', 'Glaceon', 'Golisopod (Aevian Form)', 'Leavanny (Aevian Form)'}
TIERS = [('S', 0.60, 'Carries fights on its own'), ('A', 0.53, 'Strong all chapter'), ('B', 0.48, 'Good in several fights'),
         ('C', 0.40, 'Situational'), ('D', -9, 'Weak this chapter')]
seen, cards = set(), {t[0]: [] for t in TIERS}
for r in rows:
    if r['name'] in seen:
        continue
    seen.add(r['name'])
    tier = next(t for t, cut, _ in TIERS if r['score'] >= cut)
    flag, note = FLAGS.get(r['name'], ('', ''))
    best = ', '.join(SHORT[k] for k in r['best'][:2])
    badges = '<span class="b party">Party</span>' if disp(r['name']) in IDEAL else ''
    if r['where'] == 'New catch':
        note = ('New catch (Overflow box). ' + note).strip()
    where = ''
    cards[tier].append(f'''<li class="mon"><div class="mtop"><strong>{E(disp(r["name"]))}</strong><span class="num sc">{r["score"]:.2f}</span></div>
<div class="chips">{chips(r["types"])}<span class="lv">Lv {r["level"]}</span>{where}{badges}</div>
</li>''')
_tier = lambda t, desc: f'<div class="tier t{t}"><div class="tl"><b>{t}</b><span>{E(desc)}</span></div><ul class="tmons">{"".join(cards[t])}</ul></div>'
tier_html = ''.join(_tier(t, d) for t, _, d in TIERS if cards[t] and t in 'SAB')
_low = [(t, d) for t, _, d in TIERS if cards[t] and t in 'CD']
if _low:
    tier_html += (f'<details class="tierd"><summary>Show C and D tiers ({sum(len(cards[t]) for t, _ in _low)} Pokémon)</summary>'
                  + ''.join(_tier(t, d) for t, d in _low) + '</details>')

# ---------------------------------------------------------------- 3) to-do
TODO = []
if team_todo:
    TODO.append(('Team', team_todo))
import re as _re
promo_todo, promo_left = [], []
for p in promo:
    nat = p['nature'].split(' ')[0]
    mv = [_re.sub(r' \(Lv \d+\)$', '', m) for m in p['moves']]
    now = next((d for d in cur if d['species'] in (p['final'], p['owned']) and d['box'] != 'Overflow'), None)
    if not now:
        promo_left.append(p)
        od = next((d for d in cur if d['box'] == 'Overflow' and d['species'] in (p['owned'], p['final'])), None)
        if od:
            _iss = ([f"Evolve into {p['final']}"] if p['final'] != od['species'] else []) + verify_mon(dict(od, species=p['final']), p['ability'], nat, p['evs_txt'], od['item'], [(m, 0) for m in mv])
            _gone = [m for m in od['moves'] if m not in mv]
            _iss = [(x + f' (replaces {_gone.pop(0)})') if x.startswith('Teach ') and _gone else x for x in _iss]
            if _iss: PROFILE.setdefault((p['final'], od['n'], 'Overflow → Active'), []).extend(_iss)
            ACTIONS[od['n']] = f"Move to Active{(' (evolve into ' + p['final'] + ')') if p['final'] != od['species'] else ''}: {p['ability']}, {nat}, {p['evs_txt']}, {' / '.join(mv)}"
        promo_todo.append((f"#{p['n']} {p['owned']}{(' → evolve to ' + p['final']) if p['final'] != p['owned'] else ''} ({p['tier']} tier): move to the Active box. Build in section 02.", 'mid'))
        continue
    gaps = []
    if now['species'] != p['final']:
        gaps.append(f"evolve to {p['final']}")
    if now.get('nature') != nat:
        gaps.append(f"nature {now.get('nature')} → {nat} (mint)")
    if (now.get('ability') or '').replace('W. ', 'Water ') != p['ability']:
        gaps.append(f"ability {now.get('ability')} → {p['ability']}")
    for m, full in zip(mv, p['moves']):
        if m not in now['moves']:
            gaps.append(f"learn {full}")
    if gaps:
        PROFILE.setdefault((now['species'], now['n'], now['box']), []).extend(g[0].upper() + g[1:] for g in gaps)
        promo_todo.append((f"{p['final']} (Active box): " + '; '.join(gaps) + '.', 'low'))
if promo_todo:
    TODO.append(('New catches', promo_todo))

CUTS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(F9N)), 'cuts.json')))
cut_todo = []
for sp, why in CUTS['move'].items():
    sp_, lv_ = (sp.split('@') + [None])[:2]
    hits = [d for d in cur if d['box'] == 'Active' and d['species'] == sp_ and (lv_ is None or str(d['level']) == lv_)]
    if hits:
        cut_todo.append((f"{sp_}{' ×' + str(len(hits)) if len(hits) > 1 else ''} (#{', #'.join(str(d['n']) for d in hits)}): move to Overflow", 'mid'))
        for d in hits: ACTIONS[d['n']] = 'Move to Overflow'
for d in cur:
    if d['box'] == 'Active' and d['species'] in party and d['species'] in IDEAL and d['n'] not in ACTIONS:
        cut_todo.append((f"{d['species']} (#{d['n']}): move to Overflow. It's a second copy of the one in your party.", 'mid'))
        ACTIONS[d['n']] = 'Move to Overflow (duplicate)'
for sp, why in CUTS['maybe'].items():
    hits = [d for d in cur if d['box'] == 'Active' and d['species'] == sp]
    if hits:
        cut_todo.append((f"{sp} (#{hits[0]['n']}): your call. {why}", 'low'))
        ACTIONS[hits[0]['n']] = 'Your call: Overflow'
# boss specialists stay in Active whatever their overall score
# (only while that fight is still ahead; once beaten they get the normal Active-bar verdict)
_SPEC_ALL = {'Ludicolo': 'kyogre', 'Heliolisk': 'kyogre', 'Electivire': 'kyogre', 'Boltund': 'kyogre', 'Togedemaru': 'kyogre',
             'Exeggutor': 'groudon', 'Glaceon': 'groudon', 'Camerupt': 'groudon'}
_DONE = set(filter(None, os.environ.get('DONE', '').split(',')))
SPECIALISTS = {k: v.title() for k, v in _SPEC_ALL.items() if v not in _DONE}
SPECIALISTS = {k: 'boss specialist: ' + v for k, v in SPECIALISTS.items()}
SPECIALISTS['Meowscarada'] = 'your starter'
SPECIALISTS['Ceruledge'] = 'Swords Dance sweeper: +2 one-shots 50 of 69 boss mons'
# staging box: every mon gets a verdict (Active needs A tier on its own and a species not already in Party/Active)
_have = {d['final'] for d in cur if d['box'] in ('Party', 'Active')}
_to_act, _to_ovf = [], []
for d in cur:
    if d['box'] != 'Staging':
        continue
    spec = d['species'] in SPECIALISTS
    ok = spec or (d['score'] is not None and d['score'] >= 0.53 and d['final'] not in _have)
    ACTIONS[d['n']] = ('Move to Active (' + SPECIALISTS[d['species']] + ')') if spec else ('Move to Active' if ok else 'Move to Overflow')
    if ok and d.get('attacks'):
        _atk = list(d['attacks'])[:3] + ['Protect']
        _ph = sum(1 for m in _atk if (SX.MV.get(m) or {}).get('Category') == 'Physical') >= sum(1 for m in _atk if (SX.MV.get(m) or {}).get('Category') == 'Special')
        _key, _nats = ('Atk', {'Adamant', 'Jolly', 'Brave'}) if _ph else ('SpA', {'Modest', 'Timid', 'Quiet'})
        _nat = nat_pick(d, _ph)
        _iss = []
        if d['final'] != d['species']: _iss.append(f"Evolve into {d['final']}" + (f" ({d['evolve']})" if d.get('evolve') else ''))
        if (d.get('evs') or {}).get(_key, 0) < 100: _iss.append(f"EVs: {ev_pick(d, _key)} (now {' / '.join(f'{v} {k}' for k, v in (d.get('evs') or {}).items() if v >= 100) or 'none'})")
        if d.get('nature') not in _nats: _iss.append(f"Nature: {d.get('nature')} → {_nat} (mint)")
        if d.get('capsule') and d['capsule'][0].replace(' ', '').lower() != (d.get('ability') or '').replace(' ', '').lower():
            _iss.append(f"Ability: {d.get('ability')} → {d['capsule'][0]} (Ability Capsule)")
        if (d.get('level') or 55) < 55: _iss.append(f"Lv {d['level']} → 55")
        _iss += plan_moves(d['moves'], list(d['attacks'])[:3], _ph, d.get('ability'))
        if _iss: PROFILE.setdefault((d['final'], d['n'], 'Staging → Active'), []).extend(_iss)
    (_to_act if ok else _to_ovf).append(f"{d['species']} (#{d['n']})")
if _to_act:
    cut_todo.insert(0, ('Staging → Active: ' + ', '.join(_to_act), 'high'))
if _to_ovf:
    cut_todo.insert(0, ('Staging → Overflow: ' + ', '.join(_to_ovf), 'mid'))
if cut_todo:
    _mv = [t for t, pr in cut_todo if t.endswith('move to Overflow')]
    _other = [(t, pr) for t, pr in cut_todo if not t.endswith('move to Overflow')]
    if _mv:
        _other.insert(0, ('Move to Overflow: ' + ', '.join(t.replace(': move to Overflow', '') for t in _mv), 'mid'))
    TODO.append(('Box cleanup', _other))
todo_html = ''
k = 0
for group, items in TODO:
    lis = ''
    for text, pri in items:
        k += 1
        tid = 'todo-' + hashlib.md5(text.encode()).hexdigest()[:8]
        lis += (f'<li class="p-{pri}"><input type="checkbox" id="{tid}"><label for="{tid}">{E(text)}</label>'
                f'<span class="pri">{ {"high": "Priority", "mid": "Soon", "low": "Optional", "done": "Done"}[pri] }</span></li>')
    todo_html += f'<div class="tgroup"><h3>{E(group)}</h3><ul class="todo">{lis}</ul></div>'

# ---------------------------------------------------------------- 3b) PROFILE FIXES: one card per Pokémon (replaces the grouped list)
# Box moves (into/out of party, staging, cuts) live in the Boxes tab only (green = move in, red = move out).
_BOXMOVE = ('Put ', 'After ', 'Move ')
_cards = []   # (sort key, species, where, [changes])
for role, name, *_ in TEAM:
    pd = party.get(name)
    ch = [c for c in TEAM_CHANGES.get(name, []) if not c.startswith(_BOXMOVE)]
    if CF and name in CF_NAMES: ch = []
    key = (pd['species'], pd['n'], pd['box']) if pd else TEAM_SRC.get(name)
    if key and key in PROFILE:   # merge relearner / build-fix lines, skipping ones the team build already says
        _spec = next(t for t in TEAM if t[1] == name)   # the team build wins over generic box suggestions
        ch += [x for x in PROFILE.pop(key) if x not in ch and not (x.startswith('Teach ') and x.split(' (')[0] in {c.split(' (')[0] for c in ch})
               and not x.startswith(('Ability:', 'Nature:', 'EVs:'))]
    where = f"Party #{pd['n']}" if pd else (f"{key[2]} #{key[1]} → party" if key else 'main six')
    if ch: _cards.append((0, name, where, ch))
if CF:
    for nm_, (dd, iss) in CF_ISSUES.items():
        k2 = (dd['species'], dd['n'], dd['box'])
        extra = PROFILE.pop(k2, []) if k2 in PROFILE else []
        if iss or extra: _cards.append((-1, nm_, f"{CF['title']} lineup · {dd['box']} #{dd['n']}", iss + extra))
for (sp, n, box), ch in sorted(PROFILE.items(), key=lambda kv: (kv[0][2] != 'Party', kv[0][0])):
    if ch: _cards.append((1 if box == 'Party' else 2, sp, f'{box} #{n}', ch))
_cards.sort(key=lambda c: (c[0], c[1]))
todo_html = ''
for _, name, where, ch in _cards:
    lis = ''
    for text in ch:
        tid = 'todo-' + hashlib.md5((name + text).encode()).hexdigest()[:8]
        lis += f'<li class="p-mid"><input type="checkbox" id="{tid}"><label for="{tid}">{E(text)}</label></li>'
    todo_html += f'<div class="tgroup pcard"><h3>{E(name)} <span class="legend">{E(where)}</span></h3><ul class="todo">{lis}</ul></div>'
N_PROFILE = len(_cards)

# ---------------------------------------------------------------- 4) hidden metadata
meta = {
    'generated': '2026-11-05', 'trainer': 'Vincent', 'level_cap': 55, 'badges': 7, 'difficulty': 'Classic (walkthrough sets)',
    'move_rules': 'level-up <= 55, Egg, Chapter 1-7 TMs (71), tutors at 7 badges (Luck\'s Tent tiers 0/3/5/7, Wispy Shop, Kakori Beach), known moves; no Relearner, no Life Orb, no Megas, no Chapter 8 pickups',
    'readiness': {'one_shot': R_KO, 'one_shot_first': R_FAST, 'of': R_TOT, 'risk': R_RISK},
    'promote': promo,
    'scores': {'overall': [fn['score_current'], fn['score_best']], 'singles': [fs['score_current'], fs['score_best']],
               'doubles': [fd['score_current'], fd['score_best']]},
    'goli_swords_dance_ohko': {'no_boost': 51, 'after_sd': 60, 'of': 68},
    'battles': [{'key': p['key'], 'label': p['label'], 'field': p['field'], 'format': p['format'], 'notes': p['notes'],
                 'score_current': p['score_current'], 'score_new': p['score_best'], 'engine_leads': p['leads'],
                 'foes': [{'name': f['foe'], 'lvl': f['lvl'], 'types': f['types'], 'ability': f['ability'], 'item': f['item'],
                           'moves': f['moves'], 'best_answer': f['answer'], 'answer_move': f['answer_move'],
                           'answer_dmg_pct': f['answer_dmg'], 'threat_to': f['threat_to'], 'threat_move': f['threat_move'],
                           'threat_dmg_pct': f['threat_dmg']} for f in p['foes']]} for p in fn['plans']],
    'tier_inputs': [{'name': r['name'], 'where': r['where'], 'level': r['level'], 'score': r['score'], 'solo': r['solo'],
                     'attacks': r['attacks'], 'ability': r['ability']} for r in rows],
    'sources': ['https://bigjra.github.io/rejuvenation/', 'https://rejuvenation.wiki.gg/',
                'https://www.rebornevo.com/forums/topic/80802-list-your-endgame-v14-team-that-wasnt-made-just-to-cheese-v14-spoilers/',
                'https://www.rebornevo.com/forums/topic/66111-best-aevian-pokemon/',
                'https://www.rebornevo.com/forums/topic/66727-listing-of-pokemon-i-found-especially-strong-for-end-game/'],
}
meta_json = json.dumps(meta, ensure_ascii=False).replace('</', '<\\/')

page = f'''<title>Chapter 8 Guide</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: one-screen-at-a-time trainer sheet: team table, tier board, checklist. */
:root {{
  --bg: #f3f5f6; --panel: #ffffff; --ink: #142026; --muted: #5a6a72; --line: #d7dfe3;
  --accent: #0e7c86; --accent-soft: #dff1f2; --good: #1f7a3d; --good-soft: #e1f3e6; --warn: #9a6200; --warn-soft: #fbefd9;
  --bad: #b3261e; --bad-soft: #fbe3e1;
  --tS: #c0392b; --tA: #d9822b; --tB: #c9a227; --tC: #5b8c5a; --tD: #6b7b84;
  --display: "Chakra Petch", "Arial Narrow", system-ui, sans-serif;
  --body: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #0f171b; --panel: #162127; --ink: #e5eef1; --muted: #93a6ae; --line: #26363e;
  --accent: #4cc3cc; --accent-soft: #12343a; --good: #6fd08f; --good-soft: #143222; --warn: #f0b85a; --warn-soft: #3a2c12;
  --bad: #ff8a80; --bad-soft: #3d1a18; --tS: #ff7b6b; --tA: #f5a55a; --tB: #e6c65a; --tC: #8cc48a; --tD: #9aaab2; color-scheme: dark }} }}
:root[data-theme="dark"] {{
  --bg: #0f171b; --panel: #162127; --ink: #e5eef1; --muted: #93a6ae; --line: #26363e;
  --accent: #4cc3cc; --accent-soft: #12343a; --good: #6fd08f; --good-soft: #143222; --warn: #f0b85a; --warn-soft: #3a2c12;
  --bad: #ff8a80; --bad-soft: #3d1a18; --tS: #ff7b6b; --tA: #f5a55a; --tB: #e6c65a; --tC: #8cc48a; --tD: #9aaab2; color-scheme: dark }}
* {{ box-sizing: border-box }}
body {{ background: var(--bg); color: var(--ink); font: 14.5px/1.5 var(--body); margin: 0 }}
.wrap {{ max-width: 1180px; margin: 0 auto; padding-block: 28px 56px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); display: grid; gap: 36px }}
h1, h2, h3 {{ font-family: var(--display); margin: 0; text-wrap: balance }}
h1 {{ font-size: clamp(26px, 4.4vw, 38px); line-height: 1.05 }}
h2 {{ font-size: 22px; display: flex; gap: 10px; align-items: baseline; flex-wrap: wrap }}
h2 .n {{ font: 600 13px var(--mono); color: var(--accent) }}
h2 .tag {{ font: 500 12px var(--mono); color: var(--muted); letter-spacing: .06em; text-transform: uppercase }}
h3 {{ font-size: 16px }}
p {{ margin: 0; max-width: 75ch }}
a {{ color: var(--accent) }}
.num {{ font-family: var(--mono); font-variant-numeric: tabular-nums }}
.legend {{ font-size: 13px; color: var(--muted) }}
section {{ display: grid; gap: 14px; min-width: 0 }}
header.mast {{ display: grid; gap: 10px; border-bottom: 2px solid var(--ink); padding-bottom: 18px }}
.eyebrow {{ font: 500 12px var(--mono); letter-spacing: .12em; text-transform: uppercase; color: var(--accent) }}
.facts {{ display: flex; flex-wrap: wrap; gap: 6px 18px; font: 13px var(--mono); color: var(--muted) }}
.facts b {{ color: var(--ink); font-weight: 500 }}
.panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 10px; min-width: 0 }}
.tablewrap {{ overflow-x: auto }}
table {{ border-collapse: collapse; width: 100% }}
th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid var(--line); vertical-align: top }}
thead th {{ font: 500 11px var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); white-space: nowrap }}
tbody tr:last-child td {{ border-bottom: 0 }}
.team td {{ font-size: 13.5px }}
.role {{ font: 700 13px var(--display); letter-spacing: .06em; text-transform: uppercase; border-right: 1px solid var(--line); width: 74px }}
.role-lead {{ color: var(--accent) }} .role-mid {{ color: var(--warn) }} .role-closer {{ color: var(--good) }}
.job {{ color: var(--muted); font-size: 12.5px; margin-top: 4px; max-width: 30ch }}
.evs {{ font-family: var(--mono); font-size: 12px; white-space: nowrap }}
.evl {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 3px; white-space: nowrap; font-size: 13px }}
.evl b {{ font-weight: 600; display: inline-block; min-width: 2.2em }}
.chips {{ display: flex; gap: 4px; flex-wrap: wrap; align-items: center; margin-top: 4px }}
.type {{ font: 600 10px var(--mono); letter-spacing: .05em; text-transform: uppercase; padding: 2px 6px; border-radius: 3px }}
.mv {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 3px; min-width: 120px }}
.mv li.new {{ color: var(--warn); font-weight: 600 }} .mv li.new::after {{ content: " · new"; font: 500 10px var(--mono); text-transform: uppercase }}
.mv li.soon {{ color: var(--accent); font-weight: 600 }} .mv li.soon::after {{ content: " · Lv 54"; font: 500 10px var(--mono); text-transform: uppercase }}
.chg {{ margin: 0; padding-left: 16px; color: var(--warn); font-size: 13px; display: grid; gap: 3px; min-width: 170px }}
.ok {{ color: var(--good); font: 500 12px var(--mono) }}
.plan {{ display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); gap: 16px }}
.plan .panel {{ padding: 16px 18px; display: grid; gap: 8px; align-content: start }}
.plan ul {{ margin: 0; padding-left: 18px; display: grid; gap: 6px; font-size: 13.5px }}
.scores {{ display: grid; gap: 8px }}
.score {{ display: grid; grid-template-columns: 1fr auto 44px; gap: 10px; align-items: baseline; font-size: 13.5px }}
.score i {{ font-style: normal; color: var(--good); text-align: right }}
.ready summary {{ cursor: pointer; padding: 12px 16px; display: flex; gap: 10px; align-items: baseline; font-family: var(--display); font-size: 16px; flex-wrap: wrap }}
.ready td {{ font-size: 13.5px }} .r-good {{ color: var(--good) }} .r-warn {{ color: var(--warn) }} .r-bad {{ color: var(--bad) }} .pad2 {{ padding: 0 16px 14px }}
.board {{ display: grid; gap: 8px }}
.tier {{ display: grid; grid-template-columns: 110px minmax(0, 1fr); background: var(--panel); border: 1px solid var(--line); border-radius: 10px; overflow: hidden }}
.tl {{ padding: 12px; display: grid; align-content: start; gap: 2px; color: #fff }}
.tl b {{ font: 700 30px var(--display); line-height: 1 }} .tl span {{ font-size: 11.5px; opacity: .92 }}
.tS .tl {{ background: var(--tS) }} .tA .tl {{ background: var(--tA) }} .tB .tl {{ background: var(--tB) }} .tC .tl {{ background: var(--tC) }} .tD .tl {{ background: var(--tD) }}
:root .tl {{ color: #fff }}
.tmons {{ list-style: none; margin: 0; padding: 10px; display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 8px }}
.mon {{ border: 1px solid var(--line); border-radius: 8px; padding: 8px 10px; display: grid; gap: 3px; min-width: 0 }}
.mtop {{ display: flex; justify-content: space-between; gap: 8px; align-items: baseline }}
.sc {{ font-size: 12px; color: var(--muted) }}
.lv {{ font: 11px var(--mono); color: var(--muted) }}
.b {{ font: 600 10px var(--mono); text-transform: uppercase; letter-spacing: .04em; padding: 1px 6px; border-radius: 99px }}
.b.six {{ background: var(--accent-soft); color: var(--accent) }} .b.op {{ background: var(--bad-soft); color: var(--bad) }}
.b.sup {{ background: var(--good-soft); color: var(--good) }} .b.party {{ background: var(--warn-soft); color: var(--warn) }}
.mnote {{ font-size: 12px; color: var(--muted) }}
.upgrid {{ padding: 0; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)) }}
.up {{ background: var(--panel); gap: 6px }} .up .mv {{ font-size: 13.5px }}
.b.promote {{ background: var(--good-soft); color: var(--good) }}
.b.big {{ background: var(--bad-soft); color: var(--bad) }} .b.small {{ background: var(--accent-soft); color: var(--accent) }}
.chg2 {{ font-size: 12.5px; color: var(--warn) }}
.cf {{ border: 2px solid var(--accent) }} .cft td {{ padding: 6px 8px; font-size: 13px }} .cf ol.plain {{ padding-left: 20px }}
.todos {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px }}
.tgroup {{ background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px; display: grid; gap: 8px; align-content: start }}
.todo {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 8px }}
.todo li {{ display: grid; grid-template-columns: 20px minmax(0, 1fr) auto; gap: 8px; align-items: start; font-size: 13.5px }}
.todo input {{ margin-top: 3px; accent-color: var(--accent) }}
.todo input:checked + label {{ color: var(--muted); text-decoration: line-through }}
.pri {{ font: 600 10px var(--mono); text-transform: uppercase; padding: 1px 6px; border-radius: 99px; white-space: nowrap }}
.p-high .pri {{ background: var(--bad-soft); color: var(--bad) }} .p-mid .pri {{ background: var(--warn-soft); color: var(--warn) }}
.p-low .pri {{ background: var(--accent-soft); color: var(--accent) }} .p-done .pri {{ background: var(--good-soft); color: var(--good) }}
footer {{ font-size: 12.5px; color: var(--muted); border-top: 1px solid var(--line); padding-top: 12px }}
input:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px }}
@media (max-width: 820px) {{ .plan {{ grid-template-columns: 1fr }} .tier {{ grid-template-columns: 1fr }} .tl {{ grid-auto-flow: column; justify-content: start; align-items: baseline; gap: 10px }} }}
</style>

<div class="wrap">
<header class="mast">
  <span class="eyebrow">Pokémon Rejuvenation · Chapter 8 · Classic teams</span>
  <h1>Chapter 8 Guide</h1>
  <div class="facts"><span>Export <b>{E(os.environ.get('EXPORT_LABEL', '5 Nov'))}</b></span><span>Fights left <b>{len(fn['plans'])}</b></span><span>Level cap <b>55</b></span></div>
</header>

<section aria-labelledby="s1">
  <h2 id="s1">Team</h2>
  {CF_HTML}
  <div class="panel tablewrap"><table class="team">
    <thead><tr><th>Role</th><th>Pokémon</th><th>Ability / nature</th><th>EVs</th><th>Item</th><th>Moves</th><th>Status</th></tr></thead>
    <tbody>{"".join(team_rows)}</tbody>
  </table></div>
  {RULES_HTML}
  <div class="panel pad"><h3>How to play it</h3>
    <ul class="gp">{"".join("<li>" + x + "</li>" for x in PLAY)}</ul>
  </div>
</section>

<section aria-labelledby="s1f">
  <h2 id="s1f">Fights</h2>
  {CF_HTML}
  {NEXT_HTML}
</section>

<section aria-labelledby="s1b">
  <h2 id="s1b">Move Relearner</h2>
  <ul class="tmons upgrid">{"".join(up_cards)}</ul>
  {'' if up_cards else '<p class="ok">All relearner upgrades are done.</p>'}
  {('<h3>Promote from Overflow <span class="legend">every Pokémon re-scored at Lv 55 with relearner, TM, egg and level-up moves</span></h3><ul class="tmons upgrid">' + "".join(promo_cards) + '</ul>') if promo_cards else ''}
</section>

<section aria-labelledby="s1c">
  <h2 id="s1c">Build fixes</h2>
  <p class="legend">Active Pokémon whose EVs, nature, ability or Protect don't match a proper build. Moves are in Move Relearner.</p>
  <ul class="tmons upgrid">{"".join(fix_cards)}</ul>
</section>

<section aria-labelledby="s2">
  <h2 id="s2">Tier list</h2>
  <div class="board">{tier_html}</div>
</section>

<section aria-labelledby="s3">
  <h2 id="s3">To do</h2>
  <p class="legend">Profile fixes only: one card per Pokémon with everything it needs. Box moves are on the Boxes tab.</p>
  <div class="todos pcards">{todo_html or '<p class="ok">Nothing to fix: every Party and Active Pokémon matches its build ✓</p>'}</div>

</section>

<footer>Sources: <a href="https://bigjra.github.io/rejuvenation/">BIGJRA walkthrough</a>, <a href="https://rejuvenation.wiki.gg/">Rejuvenation wiki</a>, Smogon. Damage numbers are estimates.</footer>
</div>

<script type="application/json" id="report-data">{meta_json}</script>
<script>
(function () {{
  var KEY = 'ch8-todo';
  var saved = {{}};
  try {{ saved = JSON.parse(localStorage.getItem(KEY) || '{{}}') || {{}}; }} catch (e) {{ saved = {{}}; }}
  document.querySelectorAll('.todo input[type=checkbox]').forEach(function (cb) {{
    if (Object.prototype.hasOwnProperty.call(saved, cb.id)) cb.checked = !!saved[cb.id];
    cb.addEventListener('change', function () {{
      saved[cb.id] = cb.checked;
      try {{ localStorage.setItem(KEY, JSON.stringify(saved)); }} catch (e) {{}}
    }});
  }});
}})();
</script>
'''
if True:
    page = re.sub(r'<section aria-labelledby="s1c">.*?</section>\s*', '', page, count=1, flags=re.S)
if True:
    page = re.sub(r'<section aria-labelledby="s1b">.*?</section>\s*', '', page, count=1, flags=re.S)
page = page.replace('</style>', SX.CSS.replace('{{', '{').replace('}}', '}') + '</style>', 1)
open(OUT, 'w', encoding='utf-8').write(page)
json.dump({t[1]: t[0].lower() for t in TEAM}, open(os.path.join(os.path.dirname(os.path.abspath(F9N)), 'team_roles.json'), 'w'), indent=1)
json.dump({str(k): v for k, v in ACTIONS.items()}, open(os.path.join(os.path.dirname(os.path.abspath(F9N)), 'actions.json'), 'w'), indent=1)
print('wrote', OUT, len(page), 'tiers:', {t: len(v) for t, v in cards.items()})
