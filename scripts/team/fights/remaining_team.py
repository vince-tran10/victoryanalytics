"""Team search on team/remaining_eval.json under the chapter rules: (b) no attack type the remaining foes use hits 3+
of the six super-effectively, (c) every such type resisted by >= 1, (d) every foe hit >= 100% or SE by someone, <= 2 misses;
one mon per species. Score = per foe best q + 0.35 x second best, weighted (singles x2)."""
import json, sys, itertools, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, os.path.join(HERE, '..', '..'))
os.environ.setdefault('MOVE_RULES', 'relearn'); os.environ.setdefault('FORCE_FORMAT', 'native')
from engine import Engine
E = Engine('.'); D = E.D
R = json.load(open('team/remaining_eval.json')); FO = R['foes']; WT = np.array(R['wt'])
keys = sorted({k for k, n, f in FO})
BAT = {b['key']: b for b in E.battles if b['key'] in keys}
def foe_moves(f):
    m = f['moves']; return [x for x, _ in m] if m and isinstance(m[0], (list, tuple)) else list(m)
ATK = {}
for k in keys:
    for f in BAT[k]['foes']:
        for m in foe_moves(f):
            mv = D.moves.get(m)
            if mv and mv['Category'] != 'Status': ATK.setdefault(mv['Type'], set()).add(k)
best = {}
for x in R['rows']:
    sp = x['name'].split(' (')[0] if 'Aevian' not in x['name'] and 'Hisuian' not in x['name'] else x['name']
    if x['name'] not in best: best[x['name']] = x
P = sorted(best.values(), key=lambda x: -x['score'])[:int(os.environ.get('POOL', '34'))]
Q = np.array([x['q'] for x in P]); COV = np.array([x['cov'] for x in P])
WK = {t: np.array([E.chart_eff(t, x['types']) > 1 for x in P]) for t in ATK}
RS = {t: np.array([E.chart_eff(t, x['types']) < 1 for x in P]) for t in ATK}
for i, x in enumerate(P):   # ability immunities
    if x['ab'] == 'LEVITATE' or x['ab'] == 'LUNARIDOL': WK.get('GROUND', np.zeros(len(P), bool))[i] = False; RS.get('GROUND', np.zeros(len(P), bool))[i] = True
    if x['ab'] in ('FLASHFIRE',) and 'FIRE' in WK: WK['FIRE'][i] = False; RS['FIRE'][i] = True
    if x['ab'] in ('WATERABSORB', 'STORMDRAIN', 'DRYSKIN') and 'WATER' in WK: WK['WATER'][i] = False; RS['WATER'][i] = True
    if x['ab'] in ('SAPSIPPER',) and 'GRASS' in WK: WK['GRASS'][i] = False; RS['GRASS'][i] = True
MAJOR = [t for t, ks in ATK.items() if len(ks) >= 2]
def ok(ix):
    ix = list(ix)
    for t in ATK:
        if WK[t][ix].sum() >= 3: return False
        if t in MAJOR and not RS[t][ix].any(): return False
    miss = ((COV[ix] >= 100).any(axis=0) == False).sum()
    return miss <= 2
def sc(ix):
    q = np.sort(Q[list(ix)], axis=0); return float(((q[-1] + .35 * q[-2]) * WT).sum() / WT.sum())
res = sorted(((sc(ix), ix) for ix in itertools.combinations(range(len(P)), 6) if ok(ix)), reverse=True)
print('attack types (fights):', {t: sorted(k) for t, k in ATK.items()}, '| major:', MAJOR)
print('sixes passing rules:', len(res))
for s, ix in res[:10]:
    print(round(s, 4), [P[i]['name'] + '/' + P[i]['ab'][:8] for i in ix])
json.dump([[s, [P[i]['name'] + '|' + P[i]['ab'] for i in ix]] for s, ix in res[:50]], open('team/remaining_team.json', 'w'))
cur = ['Musharna (Aevian Form)', 'Rhyperior', 'Vikavolt', 'Armarouge', 'Ludicolo', 'Annihilape']
ix = [next((i for i, x in enumerate(P) if x['name'] == n), None) for n in cur]
print('old six in pool:', ix, (round(sc(ix), 4), ok(ix)) if None not in ix else 'not all in pool')
