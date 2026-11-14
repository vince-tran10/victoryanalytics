"""Box-wide preview: for a fight's evaluator output, give every opponent Pokémon its OWN counter from the whole box
(distinct mons; counter = deals >= 90% or outspeeds + >= 100%, takes < 70%). Brute force over each foe's top 8.
Writes team/counters_<key>.json in counters_tab.py's format (marked preview=True).
usage (from workspace/): box_counters.py <key> [...]"""
import json, sys, itertools
import numpy as np
for key in sys.argv[1:]:
    R = json.load(open(f'team/{key}_eval.json')); FO = [n for k, n, f in R['foes']]; SPE = R.get('foe_spe') or [0] * len(FO)
    best = {}
    for r in R['rows']:
        if r['name'] not in best or r['score'] > best[r['name']]['score']: best[r['name']] = r
    rows = list(best.values())
    def ok(r, j): return ((r['cov'][j] >= 90) or (r['spe'] > SPE[j] and r['cov'][j] >= 100)) and r['taken'][j] < 70
    tops = [sorted(range(len(rows)), key=lambda i: -(ok(rows[i], j) * 10 + rows[i]['q'][j]))[:8] for j in range(len(FO))]
    bestv, bestc = None, None
    for combo in itertools.product(*tops):
        if len(set(combo)) < len(combo): continue
        v = sum(ok(rows[i], j) * 10 + rows[i]['q'][j] for j, i in enumerate(combo))
        if bestv is None or v > bestv: bestv, bestc = v, combo
    pairs = [dict(foe=FO[j], mon=rows[i]['name'], ability=rows[i]['ab'], dealt=int(rows[i]['cov'][j]), taken=int(rows[i]['taken'][j]),
                  ok=bool(ok(rows[i], j))) for j, i in enumerate(bestc)]
    json.dump(dict(preview=True, current=dict(counters=sum(p['ok'] for p in pairs), pairs=pairs)), open(f'team/counters_{key}.json', 'w'), indent=1)
    print(key, sum(p['ok'] for p in pairs), '/', len(pairs), [(p['foe'], p['mon'], p['dealt'], p['taken']) for p in pairs])
