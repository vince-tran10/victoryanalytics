"""Evaluate the whole roster against Chapter 8 and search for the best six."""
import json, os, sys, itertools, random, math
sys.path.insert(0, os.path.dirname(__file__))
from engine import Engine, CAP

BASE, ROSTER, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
E = Engine(BASE)
W2, WF, WS = (float(x) for x in os.environ.get('WEIGHTS', '0.35,0.35,0.03').split(','))
roster = json.load(open(ROSTER))

# one candidate per (species, form, ability) after evolving; prefer party/active copies, then higher level
loc_rank = {'Party': 0, 'Active': 1, 'Overflow': 2}


def where(m):
    i = m['dump']
    return 'Party' if i <= int(os.environ.get('PARTY_N', '6')) else ('Active' if i >= int(os.environ.get('ACTIVE_START', '356')) else 'Overflow')


cands = {}
for m0 in roster:
  m0['where'] = where(m0)
  for branch in range(len(E.evo_paths(m0['sid'], m0['form'], m0.get('gender') or '')) or 1):
    m = m0
    base_me = E.build_me(m, branch=branch)
    f = E.D.form(base_me['sid'], base_me['form'])
    capsule = list(dict.fromkeys(f.get('Abilities') or []))   # Ability Capsule swaps between the two regular abilities
    options = [(base_me['ability'], False)] + [(a, True) for a in capsule if a != base_me['ability']]
    if base_me['ability'] == f.get('HiddenAbility'):
        options = options[:1]          # already on its hidden ability: keep it
    for ab, changed in options:
        me = E.build_me(m, ability_override=ab, branch=branch) if changed else base_me
        me['ability_changed'] = changed
        key = (me['sid'], me['form'], me['ability'])
        prev = cands.get(key)
        rank = (loc_rank[m['where']], -m.get('level', 1))
        if prev is None or rank < prev[0]:
            cands[key] = (rank, me)
cands = [v[1] for v in cands.values()]
print('unique candidates:', len(cands))

for me in cands:
    E.evaluate(me)                      # full legal pool, to choose the moveset
    atk = E.pick_moves(me, 3)
    me['attacks'] = atk
    E.evaluate(me, moveset=set(atk))    # re-score with only the chosen attacks


SUPPORT = {
    'speed': ['ICYWIND', 'ELECTROWEB', 'TAILWIND', 'THUNDERWAVE', 'STICKYWEB', 'SCARYFACE', 'BULLDOZE', 'ROCKTOMB'],
    'redirect': ['FOLLOWME', 'RAGEPOWDER'],
    'fakeout': ['FAKEOUT'],
    'sleep': ['SPORE', 'SLEEPPOWDER', 'SING', 'HYPNOSIS', 'YAWN', 'LOVELYKISS', 'GRASSWHISTLE'],
    'burn': ['WILLOWISP'],
    'helping': ['HELPINGHAND'],
    'guard': ['WIDEGUARD', 'QUICKGUARD'],
    'screens': ['REFLECT', 'LIGHTSCREEN', 'AURORAVEIL'],
}


def support_tags(m):
    tags = {k for k, mv in SUPPORT.items() if any(x in m['legal'] for x in mv)}
    if m['ability'] == 'INTIMIDATE':
        tags.add('intimidate')
    if m['ability'] == 'NOGUARD' and 'SING' in m['legal']:
        tags.add('sleep')
    return tags


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
    return sum(battle_score(team, b) * b['weight'] for b in E.battles) / sum(b['weight'] for b in E.battles)


for me in cands:
    me['tags'] = support_tags(me)
    lv = me['src'].get('level', 1)
    me['lvl_factor'] = 1 - 0.003 * max(0, 45 - lv)
    for b in E.battles:
        for r in me['matchups'][b['key']]:
            r['q'] *= me['lvl_factor']
for me in cands:
    me['solo'] = {b['key']: battle_score([me], b) for b in E.battles}
    me['solo_total'] = team_score([me])
cands.sort(key=lambda m: -m['solo_total'])
ready = [c for c in cands if not c['gate']]
pool = [c for c in ready if not os.environ.get('POOL_NO_OVERFLOW') or c['src']['where'] != 'Overflow'][:80]


def ok(team, c):
    return c not in team and all(t['sid'] != c['sid'] for t in team)

# greedy + local search (swap) from several seeds
best_team, best_val = None, -1
random.seed(7)
seeds = [[]] + [[c] for c in pool[:8]]
for seed in seeds:
    team = list(seed)
    while len(team) < 6:
        nxt = max((c for c in pool if ok(team, c)), key=lambda c: team_score(team + [c]))
        team.append(nxt)
    improved = True
    while improved:
        improved = False
        cur = team_score(team)
        for i in range(6):
            for c in pool:
                t2 = team[:i] + [c] + team[i + 1:]
                if not ok(team[:i] + team[i + 1:], c):
                    continue
                v = team_score(t2)
                if v > cur + 1e-9:
                    team, cur, improved = t2, v, True
    v = team_score(team)
    if v > best_val:
        best_team, best_val = team, v

current = [c for c in cands if c['src']['where'] == 'Party' and not c['ability_changed']]
print('current party score', round(team_score(current), 3), [c['name'] for c in current])
print('best team score   ', round(best_val, 3), [c['name'] for c in best_team])
for b in E.battles:
    print(f"  {b['key']:9s} current {battle_score(current, b):.3f}  best {battle_score(best_team, b):.3f}")
print('\nTop 40 individual:')
for c in cands[:40]:
    print(f"{c['solo_total']:.3f} {c['name'][:30]:30s} <- {c['owned_as'][:16]:16s} {c['src']['where']:8s} Lv{c['src'].get('level')} {c['ability']:14s} "
          f"{[E.D.moves[m]['MoveName'] for m in c['attacks']]} {c['evo'][:40]} {('GATED:' + c['gate']) if c['gate'] else ''}")

json.dump(dict(
    current=[c['name'] for c in current], best=[c['name'] for c in best_team],
), open(OUT, 'w'))
import pickle
pickle.dump(dict(cands=cands, best=best_team, current=current), open(OUT + '.pkl', 'wb'))
