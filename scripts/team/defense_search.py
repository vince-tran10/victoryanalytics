"""Defensive-matrix team search: (a) no type super-effective on 3+ members, (b) every type resisted/immune by >= 1.
Then rank passing sixes by the battle score (average of with-field and no-field). Pool = party + Active (+ ALSO names)."""
import pickle, sys, os, itertools, json
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from engine import Engine
BASE, N = sys.argv[1], int(sys.argv[2])
WMAX, RMIN = int(os.environ.get('WEAK_MAX', '2')), int(os.environ.get('RESIST_MIN', '1'))
NETMAX, NPOS = int(os.environ.get('NET_MAX', '9')), int(os.environ.get('NET_POS_MAX', '99'))
os.environ['FORCE_FORMAT'] = 'native'
E = Engine(BASE); D = E.D
RUN = pickle.load(open(f'{BASE}/team/r20_native.json.pkl', 'rb')); RUNN = pickle.load(open(f'{BASE}/team/r20n_native.json.pkl', 'rb'))
TYPES = ['NORMAL', 'FIRE', 'WATER', 'ELECTRIC', 'GRASS', 'ICE', 'FIGHTING', 'POISON', 'GROUND', 'FLYING', 'PSYCHIC', 'BUG',
         'ROCK', 'GHOST', 'DRAGON', 'DARK', 'STEEL', 'FAIRY']
IMM = {'LEVITATE': 'GROUND', 'FLASHFIRE': 'FIRE', 'WATERABSORB': 'WATER', 'STORMDRAIN': 'WATER', 'DRYSKIN': 'WATER',
       'VOLTABSORB': 'ELECTRIC', 'LIGHTNINGROD': 'ELECTRIC', 'MOTORDRIVE': 'ELECTRIC', 'SAPSIPPER': 'GRASS', 'EARTHEATER': 'GROUND',
       'WELLBAKEDBODY': 'FIRE'}
CREST_IMM = {'Whiscash Crest': 'GRASS'}
def eff(atk, c):
    item = c['src'].get('item') or ''
    if IMM.get(c['ability']) == atk or CREST_IMM.get(item) == atk:
        return 0.0
    m = 1.0
    for t in c['types']:
        ch = D.chart.get(t.capitalize(), {})
        if atk in ch.get('Immunities', []): m *= 0
        elif atk in ch.get('Weaknesses', []): m *= 2
        elif atk in ch.get('Resistances', []): m *= 0.5
    if c['ability'] == 'THICKFAT' and atk in ('FIRE', 'ICE'): m /= 2
    return m
def key(c): return (c['sid'], c['form'], c['ability'])
def prep(P):
    idx = {}
    for c in P['cands']:
        idx[key(c)] = (c, {b['key']: [r['q'] for r in c['matchups'][b['key']]] for b in E.battles},
                       {b['key']: sum(1 for r in c['matchups'][b['key']] if r['deff'] >= 100) / len(b['foes']) for b in E.battles})
    return idx
I1, I2 = prep(RUN), prep(RUNN); TW = sum(b['weight'] for b in E.battles)
def score1(keys, idx):
    team = [idx[k] for k in keys]; tot = 0
    for b in E.battles:
        n = len(b['foes']); s = 0
        for i in range(n):
            qs = sorted((t[1][b['key']][i] for t in team), reverse=True); s += qs[0] + .35 * qs[1]
        sup = set()
        if b['format'] == 'Doubles':
            for t in team: sup |= t[0]['tags']
        tot += (s / n - .35 * sum(t[2][b['key']] for t in team) / 6 + .03 * len(sup)) * b['weight']
    return tot / TW
def score(keys): return (score1(keys, I1) + score1(keys, I2)) / 2
# pool: best ability per species/form among party + Active, plus named extras
best = {}
for c in sorted(RUN['cands'], key=lambda c: -c['solo_total']):
    if c['gate'] or c['src']['where'] == 'Overflow': continue
    best.setdefault((c['sid'], c['form']), c)
pool = sorted(best.values(), key=lambda c: -c['solo_total'])[:N]
extra = json.loads(os.environ.get('ALSO', '[]'))
for c in best.values():
    if c['name'] in extra and c not in pool: pool.append(c)
vec = {key(c): [eff(t, c) for t in TYPES] for c in pool}
print(len(pool), 'in pool:', ', '.join(c['name'].replace(' (Aevian Form)', '-A') for c in pool))
passing = []
for combo in itertools.combinations(pool, 6):
    ks = [key(c) for c in combo]; ok = True
    for j in range(len(TYPES)):
        w = r = 0
        for k_ in ks:
            v = vec[k_][j]
            if v >= 2: w += 1
            elif v <= 0.5: r += 1
        if w > WMAX or r < RMIN or w - r > NETMAX: ok = False; break
        if w - r > 0: npos = locals().get('npos', 0) + 1
    if ok:
        npos_ = sum(1 for j in range(len(TYPES)) if sum(1 for k in ks if vec[k][j] >= 2) > sum(1 for k in ks if vec[k][j] <= .5))
        if npos_ <= NPOS: passing.append(ks)
print('sixes passing (a) and (b):', len(passing))
res = sorted(((score(ks), ks) for ks in passing), reverse=True)
byk = {key(c): c for c in pool}
out = []
for v, ks in res[:15]:
    names = [byk[k]['name'] for k in ks]
    W = [sum(1 for k in ks if vec[k][j] >= 2) for j in range(len(TYPES))]
    R = [sum(1 for k in ks if vec[k][j] <= 0.5) for j in range(len(TYPES))]
    net = [w - r for w, r in zip(W, R)]
    pos = [f"{t.capitalize()}+{n}" for t, n in zip(TYPES, net) if n > 0]
    print(f"{v:.3f} | field {score1(ks, I1):.3f} no-field {score1(ks, I2):.3f} | " + ', '.join(n.replace(' (Aevian Form)', '-A') for n in names)
          + f" | weak-2 types: {', '.join(t.capitalize() for t, w in zip(TYPES, W) if w == 2) or 'none'} | net>0: {', '.join(pos) or 'none'} | sum net {sum(net)}")
    out.append(dict(score=v, names=names, weak=dict(zip(TYPES, W)), resist=dict(zip(TYPES, R))))
json.dump(out, open(f'{BASE}/team/defense_top.json', 'w'), indent=1)
cur = ['Annihilape', 'Chandelure', 'Azumarill', 'Whiscash', 'Golisopod (Aevian Form)', 'Glalie (Aevian Form)']
ck = [key(next(c for c in pool if c['name'] == n)) for n in cur if any(c['name'] == n for c in pool)]
if len(ck) == 6:
    print('current six score', round(score(ck), 3), 'unresisted:', [t for j, t in enumerate(TYPES) if sum(1 for k in ck if vec[k][j] <= .5) == 0])
