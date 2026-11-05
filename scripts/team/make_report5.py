"""Chapter 8 report: team table, fight readiness, tier list, export-verified to-do, hidden metadata.

usage: make_report5.py NEW_EXPORT OLD_EXPORT F11_native F11_Singles F11_Doubles PROMOTE_JSON OUT
To-dos are checked against NEW_EXPORT: anything the export shows as done is dropped.
"""
import json, sys, html, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from current_box import current_rows, tier as tier_of

NEWX, OLDX, F9N, F9S, F9D, PROMO, OUT = sys.argv[1:8]
cur, ACT = current_rows(NEWX, OLDX, F9N)
party = {d['species']: d for d in cur if d['box'] == 'Party'}
rows = []
for d in cur:
    if d['box'] == 'Overflow' or d['score'] is None:
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
TEAM = [
    ('Lead', 'Annihilape', 'Fighting/Ghost', 'Defiant', 'Adamant', '252 Atk / 252 Spe / 4 HP', 'Black Belt',
     [('Close Combat', 0), ('Rage Fist', 0), ('Sucker Punch', 0), ('Protect', 0)], []),
    ('Lead', 'Arcanine', 'Fire', 'Intimidate', 'Adamant', '252 Atk / 252 Spe / 4 Def', 'Sitrus Berry',
     [('Flare Blitz', 0), ('Extreme Speed', 0), ('Close Combat', 0), ('Protect', 0)], []),
    ('Mid', 'Chandelure', 'Ghost/Fire', 'Flash Fire', 'Timid', '252 SpA / 252 Spe / 4 HP', 'Focus Sash',
     [('Shadow Ball', 0), ('Overheat', 0), ('Will-O-Wisp', 0), ('Protect', 0)], []),
    ('Mid', 'Lapras-Aevian', 'Rock/Psychic', 'No Guard', 'Adamant', '252 HP / 252 Atk / 4 SpD', 'Hard Stone',
     [('Rock Slide', 0), ('Zen Headbutt', 0), ('Dragon Dance', 0), ('Sing', 0)], []),
    ('Closer', 'Golisopod-Aevian', 'Bug/Ground', 'Skill Link', 'Adamant', '252 HP / 252 Atk / 4 SpD', 'Soft Sand',
     [('Bone Rush', 0), ('Pin Missile', 0), ('Swords Dance', 0), ('Protect', 0)], []),
    ('Closer', 'Glalie-Aevian', 'Grass/Rock', 'Grassy Surge', 'Adamant', '252 HP / 252 Atk / 4 SpD', 'Sitrus Berry',
     [('Grassy Glide', 0), ('Wood Hammer', 0), ('Rock Slide', 0), ('Protect', 0)], []),
]
JOB = {'Annihilape': 'Fastest hitter.',
       'Gholdengo': 'Make It Rain hits both foes (1.5x on Big Top). Immune to status moves.',
       'Rhyperior': 'Resists Fire. Stone Edge (Hard Stone, 1.5x on Mountain and Volcanic Top) deals with Fire mons and fliers.',
       'Glaceon': 'Icy Wind slows the back line for Golisopod. Freeze-Dry and Blizzard are your Groudon answer.',
       'Golisopod-Aevian': 'Win condition. Skill Link makes Bone Rush and Pin Missile 125 power. After one Swords Dance it one-shots 60 of 68 boss mons.',
       'Leavanny-Aevian': 'Rage Powder pulls attacks so Golisopod gets a free Swords Dance; Focus Sash guarantees it survives that turn. Intimidate on entry.'}
REPL = {('Annihilape', 'Sucker Punch'): 'Fire Punch: priority hit on faster foes',
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
        out = [f"Put {name} in the party (now in {d0['box']} #{d0['n']})" if d0 else f'Put {name} in the party']
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
    for m, _ in moves:
        if m not in d['moves']:
            out.append(LATER.get((name, m), f'Teach {m}' + (f' (replaces {REPL[(name, m)]})' if (name, m) in REPL else '')).format(lv=d['level']))
    return out


def ev_lines(evs):
    parts = sorted(((int(v), k) for v, k in (x.split() for x in evs.split(' / '))), key=lambda t: -t[0])
    keep = parts[:2] + [t for t in parts[2:3] if t[0] >= 60]
    return '<ul class="evl">' + ''.join(f'<li><b class="num">{v}</b> {k}</li>' for v, k in keep) + '</ul>'


team_rows, team_todo = [], []
prev = None
for role, name, types, ab, nat, evs, item, moves, changes in TEAM:
    changes = verify(name, ab, nat, evs, item, moves)
    team_todo += [(f'{name}: {c}', 'mid' if c.startswith('Lv ') else 'high') for c in changes]
    moves = [(m, 2 if (name, m) in LATER and m not in party.get(name, {}).get('moves', []) else 0) for m, _ in moves]
    mv = ''.join(f'<li class="{"new" if n == 1 else ("soon" if n == 2 else "")}">{E(m)}</li>' for m, n in moves)
    ch = ('<ul class="chg">' + ''.join(f'<li>{E(c)}</li>' for c in changes) + '</ul>') if changes else '<span class="ok">Done ✓ (matches export)</span>'
    rc = f'<td class="role role-{role.lower()}" rowspan="2">{role}</td>' if role != prev else ''
    prev = role
    team_rows.append(f'''<tr>{rc}<td><strong>{E(name)}</strong><div class="chips">{chips(types)}</div></td>
<td>{E(ab)}</td><td>{E(nat)}</td><td>{ev_lines(evs)}</td><td>{E(item)}</td><td><ul class="mv">{mv}</ul></td><td>{ch}</td></tr>''')


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


# ---------------------------------------------------------------- 1b) relearner upgrades
UP = json.load(open(os.path.join(os.path.dirname(os.path.abspath(F9N)), 'upgrades_relearn.json')))
ORDER = ['Annihilape', 'Arcanine', 'Chandelure', 'Lapras-Aevian', 'Golisopod-Aevian', 'Glalie-Aevian']
up_cards, up_same, up_left, up_done = [], [], 0, []
for d in sorted((d for d in cur if d['box'] != 'Overflow' and d['species'] in UP),
                key=lambda d: (d['box'] != 'Party', ORDER.index(d['species']) if d['species'] in ORDER else 9, not UP[d['species']].get('big'), d['species'])):
    u = UP[d['species']]
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
    if done and d['box'] != 'Party':
        up_done.append(d['species']); continue
    mv = ''.join(f'<li class="{"new" if m in gaps else ""}">{E(m)}</li>' for m in u['moves'])
    gone = [m for m in d['moves'] if m not in u['moves']]
    extra = ''
    if natg: extra += f'<div class="chg2">Nature: {E(d.get("nature"))} → <b>{E(u["nature"])}</b> (mint)</div>'
    if abg: extra += f'<div class="chg2">Ability: {E(d.get("ability"))} → <b>{E(u["ability"])}</b> (Ability Capsule)</div>'
    if u.get('later'): extra += f'<div class="mnote">Later: {E(u["later"])}</div>'
    status = '<span class="ok">Done ✓</span>' if done else ('<span class="b big">big upgrade</span>' if u.get('big') else '<span class="b small">upgrade</span>')
    role = {'Annihilape': 'lead', 'Arcanine': 'lead', 'Chandelure': 'mid', 'Lapras-Aevian': 'mid'}.get(d['species'], 'closer' if d['box'] == 'Party' else '')
    up_cards.append(f'''<li class="mon up{" isparty" if d["box"] == "Party" else ""}"><div class="mtop"><strong>{E(d["species"])}</strong>{status}</div>
<div class="chips">{chips(d["types"] or "")}<span class="lv">Lv {d["level"]}</span>{'<span class="b party">Party</span>' if d["box"] == "Party" else ''}</div>
<ul class="mv">{mv}</ul>{('<div class="mnote">Out: ' + E(', '.join(gone)) + '</div>') if gone and not done else ''}{extra}
<div class="mnote">{E(u["why"])}</div>{('<div class="mnote"><b>Playstyle:</b> ' + E(u["style"]) + '</div>') if u.get("style") else ''}</li>''')
up_same += [d['species'] for d in cur if d['box'] != 'Overflow' and d['species'] not in UP and d['species'] not in up_same and d['score']]
up_same = sorted(set(up_same))
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
TIERS = [('S', 0.70, 'Carries fights on its own'), ('A', 0.58, 'Strong all chapter'), ('B', 0.50, 'Good in several fights'),
         ('C', 0.40, 'Situational'), ('D', -9, 'Weak this chapter')]
seen, cards = set(), {t[0]: [] for t in TIERS}
for r in rows:
    if r['name'] in seen:
        continue
    seen.add(r['name'])
    tier = next(t for t, cut, _ in TIERS if r['score'] >= cut)
    flag, note = FLAGS.get(r['name'], ('', ''))
    best = ', '.join(SHORT[k] for k in r['best'][:2])
    badges = '<span class="b party">Party</span>' if r['where'] == 'Party' else ''
    if r['where'] == 'New catch':
        note = ('New catch (Overflow box). ' + note).strip()
    where = ''
    cards[tier].append(f'''<li class="mon"><div class="mtop"><strong>{E(disp(r["name"]))}</strong><span class="num sc">{r["score"]:.2f}</span></div>
<div class="chips">{chips(r["types"])}<span class="lv">Lv {r["level"]}</span>{where}{badges}</div>
<div class="mnote">{E(BLURB.get(r["name"], note))}</div></li>''')
tier_html = ''.join(
    f'<div class="tier t{t}"><div class="tl"><b>{t}</b><span>{E(desc)}</span></div><ul class="tmons">{"".join(cards[t])}</ul></div>'
    for t, _, desc in TIERS if cards[t])

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
        promo_todo.append((f"{p['final']} (Active box): " + '; '.join(gaps) + '.', 'low'))
if promo_todo:
    TODO.append(('New catches', promo_todo))
if up_left:
    TODO.append(('Move Relearner', [(f'{up_left} Pokémon still to update. Work through the cards in section 02; each flips to Done ✓ once your export matches.', 'mid')]))
CUTS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(F9N)), 'cuts.json')))
cut_todo = []
for sp, why in CUTS['move'].items():
    hits = [d for d in cur if d['box'] == 'Active' and d['species'] == sp]
    if hits:
        cut_todo.append((f"{sp}{' ×' + str(len(hits)) if len(hits) > 1 else ''} (#{', #'.join(str(d['n']) for d in hits)}): move to Overflow. {why}", 'mid'))
for d in cur:
    if d['box'] == 'Active' and d['species'] in party:
        cut_todo.append((f"{d['species']} (#{d['n']}): move to Overflow. It's a second copy of the one in your party.", 'mid'))
for sp, why in CUTS['maybe'].items():
    hits = [d for d in cur if d['box'] == 'Active' and d['species'] == sp]
    if hits:
        cut_todo.append((f"{sp} (#{hits[0]['n']}): your call. {why}", 'low'))
if cut_todo:
    TODO.append(('Box cleanup: Active → Overflow', cut_todo))
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

page = f'''<title>Chapter 8 Team Report</title>
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
  <h1>Chapter 8 Team Report</h1>
  <div class="facts"><span>Trainer <b>Vincent</b></span><span>Cap <b>55</b></span><span>Badges <b>7</b></span><span>Moves <b>Ch 1–7 TMs &amp; tutors only</b></span><span>Checked vs <b>68 boss mons, 12 battles</b></span><span>Export <b>{E(os.environ.get('EXPORT_LABEL', '5 Nov'))}, {len(cur)} mons</b></span></div>
</header>

<section aria-labelledby="s1">
  <h2 id="s1"><span class="n">01</span> Your team <span class="tag">lead · mid · closer — same plan for singles and doubles</span></h2>
  <div class="panel tablewrap"><table class="team">
    <thead><tr><th>Role</th><th>Pokémon</th><th>Ability</th><th>Nature</th><th>EVs</th><th>Item</th><th>Moves</th><th>Change in game</th></tr></thead>
    <tbody>{"".join(team_rows)}</tbody>
  </table></div>
  <div class="plan">
    <div class="panel">
      <h3>Game plan</h3>
      <ul>
        <li><strong>Two win conditions.</strong> Annihilape is the main one. Once it has been hit, Rage Fist one-shots 67 of the 113 boss mons, and 83 after two hits, with no setup turn. Golisopod is the closer: after one Swords Dance it one-shots 95 of 113.</li>
        <li><strong class="role-lead">Lead</strong> Annihilape + Arcanine. Arcanine's Intimidate weakens physical attackers on entry and Extreme Speed picks off weakened foes. Let Ape take a hit, then Rage Fist.</li>
        <li><strong class="role-mid">Mid</strong> Chandelure's Will-O-Wisp burns physical threats; Lapras-Aevian's Sing never misses (No Guard), and Rock Slide hits both foes. Sleep and burns are what buy Golisopod its Swords Dance turn.</li>
        <li><strong class="role-closer">Closer</strong> Golisopod sets up Swords Dance on a sleeping or burned foe, then sweeps. Glalie-Aevian's Grassy Surge heals the team every turn, and Grassy Glide hits first in the terrain.</li>
        <li><strong>Only the lead changes, never the six.</strong> Golisopod leads vs Aelita (Bone Rush breaks Sturdy), Tommen, Troye &amp; Helen, Zena, Giratina and the ??? Factory fight. Arcanine + Chandelure lead vs Crawli, Narcissa, Danni &amp; Layla, Holly &amp; Rorim and Marcie. Glalie-Aevian + Arcanine vs Eli &amp; Sharon. Glalie-Aevian leads vs Groudon, Kyogre and Manaphy (Grass hits all three). Texen (bring 3): Chandelure, Annihilape, Golisopod.</li>
      </ul>
    </div>
    <div class="panel scores">
      <h3>Team strength, in plain terms</h3>
      <div class="score"><span>Boss mons someone in your six can one-shot</span><b class="num">{R_KO}/{R_TOT}</b><i></i></div>
      <div class="score"><span>…and does it before that foe moves</span><b class="num">{R_FAST}/{R_TOT}</b><i></i></div>
      <div class="score"><span>After one Golisopod Swords Dance</span><b class="num">95/113</b><i></i></div>
      <div class="score"><span>Annihilape alone, after its Rage Fist takes 1 / 2 hits</span><b class="num">67 / 83</b><i></i></div>
      <p class="legend">Checked against all 22 Chapter 8 fights (113 boss mons). The ones without a one-shot answer are the three bosses with boosted HP (Groudon, Kyogre, Manaphy), Multiscale Dragonite, and four that take 92–99% (Kleavor, Kommo-o, Grimmsnarl, Gyarados). Most often one-shot on your side: {", ".join(f"{E(disp(k))} ({v} boss hits)" for k, v in sorted(R_RISK.items(), key=lambda x: -x[1])[:3])}. Chandelure's Focus Sash is what keeps it alive.</p>
      <p class="legend">Hardest fight: <b>Kyogre</b> (Lv 60 boss in rain). Nobody one-shots it, so lead Glalie-Aevian and chip it with Grass moves.</p>
    </div>
  </div>
</section>

<section aria-labelledby="s1b">
  <h2 id="s1b"><span class="n">02</span> Move Relearner upgrades <span class="tag">party + Active box · {up_left} to do</span></h2>
  <p class="legend">With the relearner unlocked, any level-up move up to its level plus relearner-only moves are open (egg moves still need breeding). New moves are highlighted. Each card checks itself against your export and flips to Done ✓ once it matches.</p>
  <ul class="tmons upgrid">{"".join(up_cards)}</ul>
  {('<p class="legend"><b class="ok">Done ✓ per your export:</b> ' + E(", ".join(sorted(up_done))) + '.</p>') if up_done else ''}
  <p class="legend">No relearner upgrade worth making: {E(", ".join(up_same))}.</p>
  {('<h3>Promote from Overflow <span class="legend">every Pokémon re-scored at Lv 55 with relearner, TM, egg and level-up moves</span></h3><ul class="tmons upgrid">' + "".join(promo_cards) + '</ul>') if promo_cards else ''}
</section>

<section aria-labelledby="s2">
  <h2 id="s2"><span class="n">03</span> Chapter 8 tier list <span class="tag">party + Active box · {len(seen)} Pokémon</span></h2>
  <div class="board">{tier_html}</div>
</section>

<section aria-labelledby="s3">
  <h2 id="s3"><span class="n">04</span> To do</h2>
  <div class="todos">{todo_html or '<p>Nothing left: the export matches the plan.</p>'}</div>
  <p class="legend">Built from your latest export: anything the export shows as done is removed, and anything you ticked that the export doesn't show done comes back. Ticks are saved in this browser only. Levels come naturally; nothing here needs grinding.</p>
</section>

<footer>Sources: <a href="https://bigjra.github.io/rejuvenation/">BIGJRA walkthrough</a> (Classic Mode), <a href="https://rejuvenation.wiki.gg/">Rejuvenation wiki</a>, <a href="https://www.rebornevo.com/forums/">Reborn Evolved forums</a>, your latest export. Damage is an average-roll estimate; turns, crits and partner AI aren't simulated.</footer>
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
open(OUT, 'w', encoding='utf-8').write(page)
print('wrote', OUT, len(page), 'tiers:', {t: len(v) for t, v in cards.items()})
