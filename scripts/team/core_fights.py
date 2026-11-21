"""Best core of 4 for the REMAINING Ch9 fights only (run from workspace/ with DONE + CR_RUN set)."""
import itertools, json, os, sys
import numpy as np
sys.argv = ['x', '.', '20']
sys.path.insert(0, '../scripts/team')
import chapter_rules as C
st = json.load(open('team/state.json'))
FIGHTS = [k for k in ['karrina', 'spector', 'spector2', 'jenner9', 'erick'] if k not in st['done']]
W = {'spector': .5, 'spector2': .5}
T = {}
for r in json.load(open('team/tier_all.json'))['rows']: T.setdefault(r['name'], r)
POOL = [r['name'] for r in sorted(T.values(), key=lambda r: -r['blend']) if r['tier'] in 'SAB'][:45]
mine = st['core']
for n in mine:
    if n not in POOL: POOL.append(n)
PH = {'SWORDSDANCE', 'DRAGONDANCE', 'SHIFTGEAR', 'BULKUP', 'COIL', 'VICTORYDANCE', 'TIDYUP', 'BELLYDRUM', 'CURSE', 'SHELLSMASH', 'FILLETAWAY'}
SPc = {'NASTYPLOT', 'CALMMIND', 'QUIVERDANCE', 'SHELLSMASH', 'FILLETAWAY'}
def closer_ok(n):
    r = T[n]; L = set(r['legal'])
    return bool(L & (PH if r['cat'] == 'Physical' else SPc)) or bool(set(r['abilities']) & {'SPEEDBOOST', 'MOXIE', 'BEASTBOOST'})
OK, Q = {}, {}   # per fight: name -> arrays over foes
NF = {}
for k in FIGHTS:
    R = json.load(open(f'team/{k}_eval.json')); spe = R['foe_spe']; NF[k] = len(spe)
    best = {}
    for y in R['rows']:
        if y['name'] not in best or y.get('fixed') or (not best[y['name']].get('fixed') and y['score'] > best[y['name']]['score']): best[y['name']] = y
    for n in POOL:
        y = best.get(n)
        if not y: OK[(k, n)] = np.zeros(len(spe), bool); Q[(k, n)] = np.zeros(len(spe)); continue
        cov, tk = np.array(y['cov'], float), np.array(y['taken'], float) / (1.3 if R['foes'][0][2] == 'Doubles' else 1)
        fast = np.array([y['spe'] > s for s in spe]); sm = y.get('setup_mult') or 1
        plain = ((cov >= 90) & (tk < 70)) | (fast & (cov >= 100))
        setup = (sm > 1) & (cov * sm >= 90) & (tk < 50)
        OK[(k, n)] = plain | setup
        Q[(k, n)] = np.minimum(np.maximum(cov, np.where(tk < 50, cov * sm * .8, 0)), 120) / 100 * np.where(fast, 1.15, 1) * (1 - np.minimum(tk, 100) / 200)
TYPES = {k: [s for s in C.W if k in C.FIGHTS[s]] for k in FIGHTS}
def weak3(core):
    bad = 0
    for k in FIGHTS:
        for s in TYPES[k]:
            if sum(C.eff(s, T[n]['types'], T[n]['ability']) > 1 for n in core) >= 3: bad += 1
    return bad
def score(core):
    tot = cov = 0; per = {}
    for k in FIGHTS:
        ok = np.any([OK[(k, n)] for n in core], axis=0); q = np.max([Q[(k, n)] for n in core], axis=0)
        w = W.get(k, 1); c = int(ok.sum()); per[k] = f'{c}/{NF[k]}'
        cov += w * c; tot += w * (c + .5 * q.mean())
    return tot, cov, per
res = []
for core in itertools.combinations(POOL, 4):
    if len({n.split(' (')[0] for n in core}) < 4: continue
    if not any(closer_ok(n) for n in core): continue
    if weak3(core): continue
    tot, cov, per = score(core)
    res.append((tot, cov, core, per))
res.sort(key=lambda x: -x[0])
tier = lambda n: T[n]['tier']
for tot, cov, core, per in res[:12]:
    print(round(tot, 2), cov, [f"{n.split(' (')[0][:12]}({tier(n)})" for n in core], per)
mt, mc, mp = score(tuple(mine))
rank = next((i + 1 for i, x in enumerate(res) if sorted(x[2]) == sorted(mine)), None)
print('YOURS', round(mt, 2), mc, mp, 'rank', rank, 'of', len(res))
json.dump([dict(score=round(t, 3), counters=c, core=list(co), per=p) for t, c, co, p in res[:30]], open('team/core_fights.json', 'w'), indent=1)
