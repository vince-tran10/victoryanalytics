"""Best core + 2 flexes for ONE fight (spector). Two stages: cores by any-member coverage, then full-six flex search."""
import itertools, json, sys
import numpy as np
sys.argv = ['x']
sys.path.insert(0, '../scripts/team')
import team_fights as TF
K = 'spector'
TF.FIGHTS[:] = [K]
n, OK, Q, pool, _, foes = TF.DATA[K]
st = json.load(open('team/state.json'))
T = TF.T
PH = {'SWORDSDANCE', 'DRAGONDANCE', 'SHIFTGEAR', 'BULKUP', 'COIL', 'VICTORYDANCE', 'TIDYUP', 'BELLYDRUM', 'CURSE', 'SHELLSMASH', 'FILLETAWAY'}
SP = {'NASTYPLOT', 'CALMMIND', 'QUIVERDANCE', 'SHELLSMASH', 'FILLETAWAY'}
def closer_ok(x):
    r = T.get(x) or {}; L = set(r.get('legal') or [])
    return bool(L & (PH if r.get('cat') == 'Physical' else SP))
names = [x for x in pool if x in T][:46]
stage = []
for c in itertools.combinations(names, 4):
    if len({x.split(' (')[0] for x in c}) < 4 or not any(closer_ok(x) for x in c): continue
    ok = np.any([OK[x] for x in c], axis=0); q = np.max([Q[x] for x in c], axis=0)
    stage.append((ok.sum() + .5 * q.mean() + .1 * np.mean([T[x]['blend'] for x in c]), c))
stage.sort(key=lambda x: -x[0])
res = []
for _, c in stage[:60]:
    r = TF.best_six(list(c), K)
    if r: res.append((r[0], r[2], c, r[1], r[3]))
mine = TF.best_six(st['core'], K)
res.sort(key=lambda x: -x[0])
for sc, cnt, c, fl, pr in res[:8]:
    print(round(sc, 2), f'{cnt}/{n}', [x.split(' (')[0] + '(' + T[x]['tier'] + ')' for x in c], '+', [x.split(' (')[0] for x in fl], dict(zip(foes, [p.split(' (')[0] for p in pr])))
print('YOURS', round(mine[0], 2), f'{mine[2]}/{n}', '+', mine[1], dict(zip(foes, [p.split(' (')[0] for p in mine[3]])))
E = json.load(open(f'team/{K}_eval.json'))
print('lead foes Murkrow+Gothitelle; spe', E['foe_spe'])
json.dump([dict(score=round(s, 2), counters=c_, core=list(c), flex=list(f), pairs=dict(zip(foes, p))) for s, c_, c, f, p in res[:8]], open('team/spector_day_best.json', 'w'), indent=1)
