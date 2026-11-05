"""Exhaustive six search over the top-N candidates (native run), then re-score the best teams in Singles/Doubles/weights."""
import pickle, sys, os, itertools, json
sys.path.insert(0, os.path.dirname(__file__))
from engine import Engine
BASE, PFX, N = sys.argv[1], sys.argv[2], int(sys.argv[3])
ENG, RUNS = {}, {}
for f in ('native', 'Singles', 'Doubles'):
    os.environ['FORCE_FORMAT'] = f; ENG[f] = Engine(BASE); RUNS[f] = pickle.load(open(f'{PFX}_{f}.json.pkl', 'rb'))
def key(c): return (c['sid'], c['form'], c['ability'])
def prep(f):
    E = ENG[f]; bt = E.battles; tw = sum(b['weight'] for b in bt)
    idx = {}
    for c in RUNS[f]['cands']:
        q = {b['key']: [r['q'] for r in c['matchups'][b['key']]] for b in bt}
        fr = {b['key']: sum(1 for r in c['matchups'][b['key']] if r['deff'] >= 100) / len(b['foes']) for b in bt}
        idx[key(c)] = (c, q, fr)
    return bt, tw, idx
P = {f: prep(f) for f in ENG}
def score(keys, f='native', W2=.35, WF=.35, WS=.03):
    bt, tw, idx = P[f]; team = [idx[k] for k in keys]; tot = 0
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
cands = [c for c in RUNS['native']['cands'] if not c['gate']]
best = {}
for c in sorted(cands, key=lambda c: -c['solo_total']):       # best ability per species/form
    best.setdefault((c['sid'], c['form']), c)
pool = sorted(best.values(), key=lambda c: -c['solo_total'])[:N]
must = json.loads(os.environ.get('ALSO', '[]'))
for c in best.values():
    if c['name'] in must and c not in pool: pool.append(c)
print('pool:', [c['name'] + ('*' if c['src']['where'] == 'Overflow' else '') for c in pool])
res = []
for combo in itertools.combinations(pool, 6):
    ks = [key(c) for c in combo]
    res.append((score(ks), combo))
res.sort(key=lambda x: -x[0])
W = [(.35, .35, .03), (.2, .35, .03), (.5, .35, .03), (.35, .2, .03), (.35, .5, .03), (.35, .35, 0), (.35, .35, .06), (.5, .5, .06)]
top = res[:12]
wins = {i: 0 for i in range(len(top))}
for w in W:
    vals = [score([key(c) for c in t[1]], 'native', *w) for t in top]
    wins[max(range(len(top)), key=lambda i: vals[i])] += 1
for i, (v, combo) in enumerate(top):
    ks = [key(c) for c in combo]
    print(f"{i+1:2d} native {v:.3f} singles {score(ks,'Singles'):.3f} doubles {score(ks,'Doubles'):.3f} best-in {wins[i]}/8 |",
          ', '.join(c['name'].replace(' (Aevian Form)', '-A') + ('*' if c['src']['where'] == 'Overflow' else '') for c in combo))
