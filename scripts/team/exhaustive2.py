"""Exhaustive six search with the weakness rule (no attacking type super-effective on 3+ members) and a field-neutral
objective: average of the score with fields and without fields. Prints the top teams and their weakness profile."""
import pickle, sys, os, itertools, json
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from engine import Engine
BASE, N = sys.argv[1], int(sys.argv[2])
WMAX = int(os.environ.get('WEAK_MAX', '2'))
RUNS = {}
ENG = {}
for f in ('native', 'Singles', 'Doubles'):
    os.environ['FORCE_FORMAT'] = f
    ENG[f] = Engine(BASE)
    for tag in ('r20', 'r20n'):
        RUNS[(tag, f)] = pickle.load(open(f'{BASE}/team/{tag}_{f}.json.pkl', 'rb'))
D = ENG['native'].D
TYPES = [t for t in D.chart if t.upper() not in ('SHADOW', 'QMARKS', '???')]
IMM = {'LEVITATE': 'GROUND', 'FLASHFIRE': 'FIRE', 'WATERABSORB': 'WATER', 'STORMDRAIN': 'WATER', 'DRYSKIN': 'WATER',
       'VOLTABSORB': 'ELECTRIC', 'LIGHTNINGROD': 'ELECTRIC', 'MOTORDRIVE': 'ELECTRIC', 'SAPSIPPER': 'GRASS', 'EARTHEATER': 'GROUND',
       'WELLBAKEDBODY': 'FIRE'}
def eff(atk, types, ability, item):
    if item == 'Whiscash Crest':
        return 0.5 if atk.upper() == 'GRASS' else 1.0
    if IMM.get(ability) == atk.upper():
        return 0
    m = 1.0
    for t in types:
        c = D.chart.get(t.capitalize(), {})
        if atk.upper() in c.get('Immunities', []): m *= 0
        elif atk.upper() in c.get('Weaknesses', []): m *= 2
        elif atk.upper() in c.get('Resistances', []): m *= 0.5
    if ability == 'THICKFAT' and atk.upper() in ('FIRE', 'ICE'): m /= 2
    return m
def weak_set(c):
    return {t for t in TYPES if eff(t, c['types'], c['ability'], c['src'].get('item') or c.get('item')) >= 2}
def key(c): return (c['sid'], c['form'], c['ability'])
def prep(P, E):
    bt = E.battles; idx = {}
    for c in P['cands']:
        q = {b['key']: [r['q'] for r in c['matchups'][b['key']]] for b in bt}
        fr = {b['key']: sum(1 for r in c['matchups'][b['key']] if r['deff'] >= 100) / len(b['foes']) for b in bt}
        idx[key(c)] = (c, q, fr)
    return bt, sum(b['weight'] for b in bt), idx
PP = {k: prep(P, ENG[k[1]]) for k, P in RUNS.items()}
def score(keys, k, W2=.35, WF=.35, WS=.03):
    bt, tw, idx = PP[k]; team = [idx[x] for x in keys]; tot = 0
    for b in bt:
        n = len(b['foes']); s = 0
        for i in range(n):
            qs = sorted((t[1][b['key']][i] for t in team), reverse=True); s += qs[0] + W2 * qs[1]
        frag = sum(t[2][b['key']] for t in team) / 6
        sup = set()
        if b['format'] == 'Doubles':
            for t in team: sup |= t[0]['tags']
        tot += (s / n - WF * frag + WS * len(sup)) * b['weight']
    return tot / tw
def obj(keys, f='native', **w): return (score(keys, ('r20', f), **w) + score(keys, ('r20n', f), **w)) / 2
P = RUNS[('r20', 'native')]
cands = [c for c in P['cands'] if not c['gate']]
best = {}
for c in sorted(cands, key=lambda c: -c['solo_total']):
    best.setdefault((c['sid'], c['form']), c)
pool = sorted(best.values(), key=lambda c: -c['solo_total'])[:N]
for c in best.values():
    if c['name'] in json.loads(os.environ.get('ALSO', '[]')) and c not in pool: pool.append(c)
WS_ = {key(c): weak_set(c) for c in pool}
print('pool', len(pool), [c['name'].replace(' (Aevian Form)', '-A') + ('*' if c['src']['where'] == 'Overflow' else '') for c in pool])
res = []
for combo in itertools.combinations(pool, 6):
    ks = [key(c) for c in combo]
    cnt = {}
    for k_ in ks:
        for t in WS_[k_]: cnt[t] = cnt.get(t, 0) + 1
    if cnt and max(cnt.values()) > WMAX: continue
    res.append((obj(ks), combo))
res.sort(key=lambda x: -x[0])
print('teams passing the weakness rule:', len(res))
W = [(.35, .35, .03), (.2, .35, .03), (.5, .35, .03), (.35, .2, .03), (.35, .5, .03), (.35, .35, 0), (.35, .35, .06), (.5, .5, .06)]
top = res[:15]; wins = [0] * len(top)
for w in W:
    vals = [obj([key(c) for c in t[1]], 'native', W2=w[0], WF=w[1], WS=w[2]) for t in top]
    wins[max(range(len(top)), key=lambda i: vals[i])] += 1
for i, (v, combo) in enumerate(top):
    ks = [key(c) for c in combo]
    cnt = {}
    for k_ in ks:
        for t in WS_[k_]: cnt[t] = cnt.get(t, 0) + 1
    two = sorted(t.capitalize() for t, n in cnt.items() if n == 2)
    print(f"{i+1:2d} {v:.3f} | field {score(ks,('r20','native')):.3f} nofield {score(ks,('r20n','native')):.3f} | S {obj(ks,'Singles'):.3f} D {obj(ks,'Doubles'):.3f} | best-in {wins[i]}/8 | "
          + ', '.join(c['name'].replace(' (Aevian Form)', '-A') + ('*' if c['src']['where'] == 'Overflow' else '') for c in combo) + f" | 2x-shared: {', '.join(two)}")
json.dump([[c['name'] for c in t[1]] for t in top], open(f'{BASE}/team/ex2_top.json', 'w'))
