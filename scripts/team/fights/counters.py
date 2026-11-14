"""One dedicated counter per opponent Pokémon (Vincent, 14 Nov). Given a fight's evaluator output (rows with per-foe
damage dealt / taken), find the six whose best one-to-one pairing (each foe -> a different member) is strongest.
A pairing counts as a counter when the member deals >= 90% (or is faster and deals >= 100%) and takes < 70% from it.
Score = number of real counters first, then the sum of matchup quality over the pairing.
usage: counters.py <eval json> <dealt key> <taken key> <out json> [current six names, | separated]"""
import json, sys, itertools
import numpy as np
src, dk, tk_key, out = sys.argv[1:5]
R = json.load(open(src)); FO = R['foes']; rows = R['rows']
SPE = {'Camerupt': 65, 'Arcanine': 141, 'Scovillain': 149, 'Blaziken': 138, 'Skeledirge': 93, 'Toxtricity': 180}
def mats(r):
    cov = np.array(r[dk], float); tk = np.array(r[tk_key], float)
    fast = np.array([r['spe'] > SPE.get(f, 0) for f in FO])
    q = np.minimum(cov, 120) / 100 * np.where(fast, 1.15, 1) * (1 - np.minimum(tk, 100) / 200)
    ok = ((cov >= 90) | (fast & (cov >= 100))) & (tk < 70)
    return q, ok
Q, OK = zip(*[mats(r) for r in rows]); Q = np.array(Q); OK = np.array(OK)
n = len(FO); P = np.array(list(itertools.permutations(range(n)))); ar = np.arange(n)
def best_pairing(ix):
    ix = np.array(ix); q = Q[ix][P, ar]; ok = OK[ix][P, ar]
    key = ok.sum(1) * 10 + q.sum(1); k = key.argmax()
    return key[k], [int(ix[P[k][j]]) for j in range(n)], int(ok[k].sum())
res = []
for ix in itertools.combinations(range(len(rows)), n):
    if OK[list(ix)].any(axis=0).sum() < n - 1: continue          # quick prune: some foe nobody counters
    res.append((best_pairing(ix), ix))
res.sort(key=lambda r: -r[0][0])
def show(score, pairing, nok):
    return dict(score=round(float(score), 3), counters=nok, pairs=[dict(foe=FO[j], mon=rows[pairing[j]]['name'], ability=rows[pairing[j]]['ab'],
                dealt=int(rows[pairing[j]][dk][j]), taken=int(rows[pairing[j]][tk_key][j]), ok=bool(OK[pairing[j]][j])) for j in range(n)])
outd = dict(best=[show(*r[0]) for r in res[:5]])
if len(sys.argv) > 5:
    names = sys.argv[5].split('|'); ix = [next(i for i, r in enumerate(rows) if r['name'] == nm) for nm in names if any(r['name'] == nm for r in rows)]
    if len(ix) == n: outd['current'] = show(*best_pairing(ix))
json.dump(outd, open(out, 'w'), indent=1)
for b in outd['best'][:3]:
    print(b['score'], b['counters'], [(p['foe'], p['mon'], p['dealt'], p['taken'], p['ok']) for p in b['pairs']])
if 'current' in outd: print('current', outd['current']['score'], outd['current']['counters'], [(p['foe'], p['mon'], p['dealt'], p['taken'], p['ok']) for p in outd['current']['pairs']])
