"""Turn the search result into concrete builds, per-battle plans and swap suggestions."""
import json, os, pickle, sys, math
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

BASE, PKL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.environ.setdefault('WEIGHTS', '0.35,0.35,0.03')
d = pickle.load(open(PKL, 'rb'))
moves = json.load(open(f'{BASE}/data/Database_Moves.json'))
names = json.load(open(f'{BASE}/data/Database_Names.json'))
from engine import Engine
E = Engine(BASE)
battles = E.battles
W2, WF, WS = 0.35, 0.35, 0.03


def battle_score(team, b):
    foes = b['foes']
    tot = 0.0
    for i in range(len(foes)):
        qs = sorted((m['matchups'][b['key']][i]['q'] for m in team), reverse=True)
        tot += qs[0] + W2 * (qs[1] if len(qs) > 1 else 0)
    cover = tot / len(foes)
    frag = sum(sum(1 for r in m['matchups'][b['key']] if r['deff'] >= 100) / len(foes) for m in team) / len(team)
    sup = set()
    if b['format'] == 'Doubles':
        for m in team:
            sup |= m['tags']
    return cover - WF * frag + WS * len(sup)


def team_score(team):
    return sum(battle_score(team, b) * b['weight'] for b in battles) / sum(b['weight'] for b in battles)


SETUP = ['FILLETAWAY', 'SHELLSMASH', 'DRAGONDANCE', 'QUIVERDANCE', 'SWORDSDANCE', 'BULKUP', 'NASTYPLOT', 'CALMMIND', 'SHIFTGEAR',
         'COIL', 'WORKUP']
SUPPORT_ORDER = ['FAKEOUT', 'FOLLOWME', 'RAGEPOWDER', 'SPORE', 'WILLOWISP', 'ICYWIND', 'ELECTROWEB', 'TAILWIND',
                 'HELPINGHAND', 'WIDEGUARD', 'THUNDERWAVE', 'YAWN', 'SLEEPPOWDER', 'REFLECT', 'LIGHTSCREEN', 'TAUNT',
                 'KNOCKOFF', 'STEALTHROCK']


OVERRIDE = json.loads(os.environ.get('MOVES', '{}'))
NAT_OVERRIDE = json.loads(os.environ.get('NATURES', '{}'))


def full_moveset(m):
    if m['name'] in OVERRIDE:
        return OVERRIDE[m['name']]
    atk = list(m['attacks'])
    legal = m['legal']
    out = [moves[x]['MoveName'] for x in atk]
    extras = []
    if m['ability'] == 'NOGUARD' and 'SING' in legal:
        extras.append('SING')
    setup = next((s for s in SETUP if s in legal and (
        (m['cat'] == 'Physical' and s in ('SHELLSMASH', 'DRAGONDANCE', 'SWORDSDANCE', 'BULKUP', 'SHIFTGEAR', 'COIL', 'WORKUP')) or
        (m['cat'] == 'Special' and s in ('SHELLSMASH', 'QUIVERDANCE', 'NASTYPLOT', 'CALMMIND', 'WORKUP')))), None)
    sup = next((s for s in SUPPORT_ORDER if s in legal and s not in atk), None)
    if m['src']['name'].startswith('Hariyama') or 'FAKEOUT' in legal:
        if 'FAKEOUT' in legal:
            sup = 'FAKEOUT'
    known = {E.move_id(x) for x in m['src'].get('moves', [])}
    known_setup = next((x for x in SETUP if x in known), None)
    if known_setup:
        setup = known_setup
    # doubles staples beat a third attack: Fake Out, or a setup move the mon already runs
    for staple in (['FAKEOUT'] if 'FAKEOUT' in legal else []) + ([known_setup] if known_setup else []):
        if len(out) >= 3 and moves[staple]['MoveName'] not in out:
            out = out[:2]
    slots = 4 - len(out) - 1  # keep Protect
    picks = []
    first = [x for x in (['FAKEOUT'] if 'FAKEOUT' in legal else []) + ([known_setup] if known_setup else [])]
    for x in first + extras + ([sup] if sup else []) + ([setup] if setup else []):
        if x and x not in picks and len(picks) < slots:
            picks.append(x)
    out += [moves[x]['MoveName'] for x in picks]
    # still free? useful known status moves, then the next-best legal attack
    useful = ['SLACKOFF', 'RECOVER', 'ROOST', 'SYNTHESIS', 'WISH', 'MOONLIGHT', 'SOFTBOILED', 'DRAGONDANCE', 'SWORDSDANCE',
              'AMNESIA', 'TAILWIND', 'SING', 'TRICKROOM']
    for mv in m['src'].get('moves', []):
        mid = E.move_id(mv)
        if len(out) < 3 and mid in useful and moves[mid]['MoveName'] not in out:
            out.append(moves[mid]['MoveName'])
    if len(out) < 3:
        def tot(x):
            mv = moves[x]
            return sum(min(E.damage_pct(m, f, x, mv, b, True), 100) for b in battles for f in b['foes'])
        more = sorted((x for x, _ in E.damaging_moves(m) if x not in m['attacks']), key=lambda x: -tot(x))
        lock = {'OUTRAGE', 'PETALDANCE', 'THRASH', 'RAGINGFURY'}
        for x in more:
            if x in lock and any(E.move_id(o) in lock for o in out):
                continue
            pw = int(moves[x].get('Strength') or 0)
            if pw < 50 and int(moves[x].get('Priority') or 0) <= 0:
                continue
            if len(out) < 3 and moves[x]['MoveName'] not in out:
                out.append(moves[x]['MoveName'])
    out.append('Protect')
    return out[:4]


def item_for(m):
    held = m['src'].get('item') or ''
    ab = m['ability']
    if ab == 'GUTS':
        return 'Flame Orb (Guts needs a status to switch on)'
    if held and held not in ('Life Orb',):
        return f'{held} (already holding)'
    return 'Sitrus Berry'


def why(m):
    out = []
    for b in battles:
        rows = m['matchups'][b['key']]
        ko = [r['foe'] for r in rows if r['off'] >= 100]
        if ko:
            out.append(f"{b['key'].title()}: OHKOs {', '.join(ko[:4])}{'…' if len(ko) > 4 else ''}")
    return ' | '.join(out[:4])


best = d['best']
if os.environ.get('TEAM'):
    want = os.environ['TEAM'].split('|')
    pick = []
    for n in want:
        xs = [c for c in d['cands'] if c['name'] == n and not c.get('ability_changed')] or [c for c in d['cands'] if c['name'] == n]
        pick.append(max(xs, key=lambda c: (c['src']['where'] != 'Overflow', c['solo_total'])))
    best = pick
current = d['current']
cands = d['cands']
ready = [c for c in cands if not c['gate']]

# re-score with the exact movesets shown: recommended six = final sets, current party = moves it runs today
import engine as _eng
_orig_spread = E.spread_for
def _spread(me):
    if me['name'] in NAT_OVERRIDE:
        o = NAT_OVERRIDE[me['name']]
        return o['cat'], o['evs'], o['nature']
    return _orig_spread(me)
E.spread_for = _spread
for m in best:
    m['final_moves'] = full_moveset(m)
    ids = {E.move_id(x) for x in m['final_moves']}
    E.evaluate(m, moveset=ids)
for m in current:
    if m in best:
        continue
    m['final_moves'] = list(m['src'].get('moves', []))
    E.evaluate(m, moveset={E.move_id(x) for x in m['final_moves']})
for grp in (best, current):
    for m in grp:
        for b in battles:
            for r in m['matchups'][b['key']]:
                r['q'] *= m.get('lvl_factor', 1)
        m['solo'] = {b['key']: battle_score([m], b) for b in battles}
        m['solo_total'] = team_score([m])
# current-party copies that are also in the six use today's moves for the 'current' comparison
import copy
current_eval = []
for m in current:
    if m in best:
        c2 = copy.deepcopy(m)
        E.evaluate(c2, moveset={E.move_id(x) for x in c2['src'].get('moves', [])})
        for b in battles:
            for r in c2['matchups'][b['key']]:
                r['q'] *= c2.get('lvl_factor', 1)
        c2['solo'] = {b['key']: battle_score([c2], b) for b in battles}
        c2['solo_total'] = team_score([c2])
        current_eval.append(c2)
    else:
        current_eval.append(m)


def describe(m):
    src = m['src']
    lv = src.get('level', 1)
    evo = m['evo']
    return dict(
        name=m['name'], owned_as=src['raw'], where=src['where'], dump=src['dump'], level=lv,
        levels_needed=max(0, 55 - lv), evolve=evo, types='/'.join(t.capitalize() for t in m['types']),
        base=m['base'], ability=names.get(m['ability'], m['ability']),
        ability_now=src.get('ability'), ability_change=m.get('ability_changed', False),
        nature=m['nature'], evs=m['evs'], stats55=m['stats'], moves=m.get('final_moves') or full_moveset(m),
        moves_now=src.get('moves'), item=item_for(m), tags=sorted(m['tags']),
        solo={k: round(v, 3) for k, v in m['solo'].items()}, solo_total=round(m['solo_total'], 3),
        why=why(m))


# per-battle: best answer for each foe, biggest threat, and the best single swap-in
plans = []
for b in battles:
    k = b['key']
    foes = []
    for i, f in enumerate(b['foes']):
        rows = [(m, m['matchups'][k][i]) for m in best]
        ans = max(rows, key=lambda x: x[1]['q'])
        threat = max(rows, key=lambda x: x[1]['deff'])
        safe = min(rows, key=lambda x: x[1]['deff'])
        foes.append(dict(foe=f['name'], lvl=f['level'], types='/'.join(t.capitalize() for t in f['types']),
                         ability=names.get(f['ability'], f['ability']), item=f['item'],
                         moves=[mv['MoveName'] for _, mv in f['moves']], spe=f['stats']['Spe'],
                         answer=ans[0]['name'], answer_move=ans[1]['offmv'], answer_dmg=round(ans[1]['off']),
                         answer_faster=ans[1]['faster'], threat_to=threat[0]['name'], threat_move=threat[1]['defmv'],
                         threat_dmg=round(threat[1]['deff']), safest=safe[0]['name'], safest_dmg=round(safe[1]['deff'])))
    base_val = battle_score(best, b)
    swaps = []
    for c in ready:
        if any(c['sid'] == t['sid'] for t in best):
            continue
        for i in range(6):
            t2 = best[:i] + [c] + best[i + 1:]
            v = battle_score(t2, b)
            if v > base_val + 0.02:
                swaps.append((v - base_val, c['name'], best[i]['name'], c['src']['where'], c['src'].get('level')))
    swaps.sort(reverse=True)
    seen, top = set(), []
    for s in swaps:
        if s[1] in seen:
            continue
        seen.add(s[1]); top.append(s)
        if len(top) >= 3:
            break
    # leads: the two team members with the best score vs the first two foes (doubles) / first foe (singles)
    n_lead = 2 if b['format'] == 'Doubles' else 1
    lead_rank = sorted(best, key=lambda m: -sum(m['matchups'][k][i]['q'] for i in range(min(n_lead, len(b['foes'])))))
    plans.append(dict(key=k, label=b['label'], field=b['field'], format=b['format'], notes=b['notes'],
                      score_current=round(battle_score(current_eval, b), 3), score_best=round(base_val, 3),
                      leads=[m['name'] for m in lead_rank[:n_lead]], foes=foes,
                      swaps=[dict(gain=round(g, 3), bring=n, replace=r, where=w, level=l) for g, n, r, w, l in top]))

roster_rows = []
for c in cands:
    roster_rows.append(dict(name=c['name'], owned_as=c['src']['raw'], where=c['src']['where'], dump=c['src']['dump'],
                            level=c['src'].get('level'), evolve=c['evo'], gate=c['gate'],
                            ability=names.get(c['ability'], c['ability']), ability_change=c.get('ability_changed', False),
                            types='/'.join(t.capitalize() for t in c['types']),
                            bst=sum(c['base'].values()), attacks=[moves[x]['MoveName'] for x in c['attacks']],
                            solo={k: round(v, 3) for k, v in c['solo'].items()}, total=round(c['solo_total'], 3),
                            in_best=c in best, in_party=c in current))

# alternative teams via weight sensitivity (computed earlier, re-run quickly here)
out = dict(best=[describe(m) for m in best], current=[describe(m) for m in current_eval],
           score_best=round(team_score(best), 3), score_current=round(team_score(current_eval), 3),
           plans=plans, roster=roster_rows)
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
for m in out['best']:
    print(m['name'], '|', m['where'], m['level'], '|', m['ability'], '(change)' if m['ability_change'] else '', '|', m['nature'],
          m['evs'], '|', m['moves'], '|', m['item'], '|', m['evolve'])
for p in plans:
    print(p['key'], p['score_current'], '->', p['score_best'], 'leads', p['leads'], 'swaps', [(s['bring'], s['replace'], s['gain']) for s in p['swaps']])
