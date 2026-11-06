"""Every six from the pool that passes (a) no type SE on 3+, (b) every type resisted/immune by >=1,
(c) every type hit SE by >=1 member's attacks. Ranks by battle score; best team per 'ace'; field-use count per fight."""
import pickle, sys, os, itertools, json, collections
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from engine import Engine
from bosses import FIELD
BASE, N = sys.argv[1], int(sys.argv[2])
os.environ['FORCE_FORMAT'] = 'native'
E = Engine(BASE); D = E.D
RUN = pickle.load(open(f'{BASE}/team/r20_native.json.pkl', 'rb')); RUNN = pickle.load(open(f'{BASE}/team/r20n_native.json.pkl', 'rb'))
T = ['NORMAL', 'FIRE', 'WATER', 'ELECTRIC', 'GRASS', 'ICE', 'FIGHTING', 'POISON', 'GROUND', 'FLYING', 'PSYCHIC', 'BUG',
     'ROCK', 'GHOST', 'DRAGON', 'DARK', 'STEEL', 'FAIRY']
IMM = {'LEVITATE': 'GROUND', 'FLASHFIRE': 'FIRE', 'WATERABSORB': 'WATER', 'STORMDRAIN': 'WATER', 'DRYSKIN': 'WATER',
       'VOLTABSORB': 'ELECTRIC', 'LIGHTNINGROD': 'ELECTRIC', 'MOTORDRIVE': 'ELECTRIC', 'SAPSIPPER': 'GRASS', 'EARTHEATER': 'GROUND',
       'WELLBAKEDBODY': 'FIRE'}
def chart(atk, types):
    m = 1.0
    for t in types:
        ch = D.chart.get(t.capitalize(), {})
        if atk in ch.get('Immunities', []): m *= 0
        elif atk in ch.get('Weaknesses', []): m *= 2
        elif atk in ch.get('Resistances', []): m *= 0.5
    return m
def deff(atk, c):
    if IMM.get(c['ability']) == atk or ((c['src'].get('item') or '') == 'Whiscash Crest' and atk == 'GRASS'): return 0.0
    m = chart(atk, c['types'])
    if c['ability'] == 'THICKFAT' and atk in ('FIRE', 'ICE'): m /= 2
    return m
def atk_types(c):
    out = set()
    for mid in c['attacks']:
        mv = D.moves[mid]; t = mv['Type']
        if c['ability'] in ('PIXILATE', 'REFRIGERATE', 'AERILATE', 'GALVANIZE') and t == 'NORMAL':
            t = {'PIXILATE': 'FAIRY', 'REFRIGERATE': 'ICE', 'AERILATE': 'FLYING', 'GALVANIZE': 'ELECTRIC'}[c['ability']]
        if mid == 'FREEZEDRY': out.add('FREEZEDRY')
        out.add(t)
    return out
def hits_se(c, dt):
    for t in atk_types(c):
        if t == 'FREEZEDRY':
            if dt == 'WATER' or chart('ICE', [dt]) >= 2: return True
        elif chart(t, [dt]) >= 2: return True
    return False
def field_users(c, b):
    f = FIELD.get(b['field']) or {}
    for mid in c['attacks']:
        mv = D.moves[mid]
        if f.get('types', {}).get(mv['Type'], 1) * f.get('moves', {}).get(mid, 1) >= 1.2: return True
        if f.get('ground_vs_nonground') and mv['Type'] == 'GROUND': return True
    return False
def key(c): return (c['sid'], c['form'], c['ability'])
def prep(P):
    return {key(c): (c, {b['key']: [r['q'] for r in c['matchups'][b['key']]] for b in E.battles},
                     {b['key']: sum(1 for r in c['matchups'][b['key']] if r['deff'] >= 100) / len(b['foes']) for b in E.battles}) for c in P['cands']}
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
best = {}
for c in sorted(RUN['cands'], key=lambda c: -c['solo_total']):
    if c['gate'] or c['src']['where'] == 'Overflow': continue
    best.setdefault((c['sid'], c['form']), c)
pool = sorted(best.values(), key=lambda c: -c['solo_total'])[:N]
for c in best.values():
    if c['name'] in json.loads(os.environ.get('ALSO', '[]')) and c not in pool: pool.append(c)
W = {key(c): [deff(t, c) >= 2 for t in T] for c in pool}
R = {key(c): [deff(t, c) <= .5 for t in T] for c in pool}
S = {key(c): [hits_se(c, t) for t in T] for c in pool}
FU = {key(c): {b['key']: field_users(c, b) for b in E.battles} for c in pool}
byk = {key(c): c for c in pool}
nm = lambda c: c['name'].replace(' (Aevian Form)', '-A').replace(' (Galarian Form)', '-Galar').replace(' (Lunatone Dominant Fusion)', '-Idol').replace(' (Solrock Dominant Fusion)', '-Idol').replace(' (Aevian Form Male)', '-A')
print(len(pool), 'in pool;', 'combos', sum(1 for _ in itertools.combinations(range(len(pool)), 6)))
passing = []
for combo in itertools.combinations([key(c) for c in pool], 6):
    ok = True
    for j in range(len(T)):
        w = sum(W[k][j] for k in combo)
        if w > 2 or not any(R[k][j] for k in combo) or not any(S[k][j] for k in combo): ok = False; break
    if ok: passing.append(combo)
print('sixes passing (a)+(b)+(c):', len(passing))
res = sorted(((score(ks), ks) for ks in passing), reverse=True)
def fields(ks):
    cnt = [sum(FU[k][b['key']] for k in ks) for b in E.battles]
    return sum(cnt) / len(cnt), sum(1 for x in cnt if x >= 1), len(cnt), min(cnt)
def net(ks):
    return sum(1 for j in range(len(T)) if sum(W[k][j] for k in ks) - sum(R[k][j] for k in ks) > 0)
def line(v, ks):
    avg, n1, nb, mn = fields(ks)
    ace = max(ks, key=lambda k: byk[k]['solo_total'])
    return (f"{v:.3f} | ace {nm(byk[ace]):16s} | " + ', '.join(nm(byk[k]) for k in sorted(ks, key=lambda k: -byk[k]['solo_total']))
            + f" | red(+) rows {net(ks)} | field users avg {avg:.1f}/6, fights with >=1: {n1}/{nb}")
print('\nTOP 10 overall')
for v, ks in res[:10]: print(line(v, ks))
print('\nBEST TEAM PER ACE (ace = strongest member on its own)')
seen = set(); out = []
for v, ks in res:
    ace = max(ks, key=lambda k: byk[k]['solo_total'])
    if ace in seen: continue
    seen.add(ace); print(line(v, ks))
    out.append(dict(score=v, ace=nm(byk[ace]), team=[nm(byk[k]) for k in ks], red=net(ks), fields=fields(ks)))
json.dump(out, open(f'{BASE}/team/rules_aces.json', 'w'), indent=1)
print('\nfield-use per fight for the #1 team:', {b['key']: sum(FU[k][b['key']] for k in res[0][1]) for b in E.battles})
print('\nBEST TEAM BY FIELD COVERAGE (fights where >=1 member has a field-boosted attack)')
bycov = {}
for v, ks in res:
    avg, n1, nb, mn = fields(ks)
    if n1 not in bycov: bycov[n1] = (v, ks)
for n1 in sorted(bycov, reverse=True):
    v, ks = bycov[n1]; print(f"covers {n1}/20 ->", line(v, ks))
top = max(bycov); v, ks = bycov[top]
print('uncovered fights for the max-coverage team:', [ (b['key'], b['field']) for b in E.battles if not any(FU[k][b['key']] for k in ks)])
print('fields that boost something:', sorted({b['field'] for b in E.battles if FIELD.get(b['field'])}), 'none:', sorted({b['field'] for b in E.battles if not FIELD.get(b['field'])}))
