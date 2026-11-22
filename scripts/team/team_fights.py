"""Best TEAM for the remaining Ch9 fights (Vincent, 22 Nov): candidate core of 4 + its best 2 flexes PER FIGHT, scored as the
full six (one-to-one counters, rule 9: each foe a different member). Spector day / night count half each.
usage (from workspace/): python3 -I ../scripts/team/team_fights.py  -> team/team_fights.json"""
import itertools, json, os, sys
import numpy as np
st = json.load(open('team/state.json'))
FIGHTS = [k for k in ['spector', 'spector2', 'jenner9', 'erick', 'karrina', 'amanda'] if k not in st['done']]
W = {'spector': .5, 'spector2': .5}
T = {}
for r in json.load(open('team/tier_all.json'))['rows']: T.setdefault(r['name'], r)
DATA = {}
for k in FIGHTS:
    R = json.load(open(f'team/{k}_eval.json')); spe = R['foe_spe']; n = len(spe)
    best = {}
    for y in R['rows']:
        if y['name'] not in best or y.get('fixed') or (not best[y['name']].get('fixed') and y['score'] > best[y['name']]['score']): best[y['name']] = y
    OK, Q = {}, {}
    dbl = R['foes'][0][2] == 'Doubles'
    for nm, y in best.items():
        cov, tk = np.array(y['cov'], float), np.array(y['taken'], float)
        fast = np.array([y['spe'] > s for s in spe]); sm = y.get('setup_mult') or 1
        plain = ((cov >= 90) & (tk < 70)) | (fast & (cov >= 100))
        OK[nm] = plain | ((sm > 1) & (cov * sm >= 90) & (tk < 50))
        Q[nm] = np.minimum(np.maximum(cov, np.where(tk < 50, cov * sm * .8, 0)), 120) / 100 * np.where(fast, 1.15, 1) * (1 - np.minimum(tk, 100) / 200)
    pool = sorted(best, key=lambda x: -best[x]['score'])[:40]
    for j in range(n):
        pool += sorted(best, key=lambda x: -(OK[x][j] * 10 + Q[x][j]))[:6]
    DATA[k] = (n, OK, Q, list(dict.fromkeys(pool)), R['foes'][0][1:], [f[1] for f in R['foes']])
P = {n: np.array(list(itertools.permutations(range(6), n))) for n in {d[0] for d in DATA.values()}}
def best_six(core, k):
    n, OK, Q, pool, _, foes = DATA[k]
    if any(c not in OK for c in core): return None
    P_ = P[n]; ar = np.arange(n); res = None
    sp_core = {c.split(' (')[0] for c in core}
    cand = [x for x in pool if x not in core and x.split(' (')[0] not in sp_core]
    for a, b in itertools.combinations(cand, 2):
        if a.split(' (')[0] == b.split(' (')[0]: continue
        six = list(core) + [a, b]
        Ok = np.array([OK[x] for x in six]); Qm = np.array([Q[x] for x in six])
        key = Ok[P_, ar].sum(1) * 10 + Qm[P_, ar].sum(1); i = int(key.argmax())
        if res is None or key[i] > res[0]: res = (float(key[i]), (a, b), int(Ok[P_[i], ar].sum()), [six[x] for x in P_[i]])
    return res
def team_score(core):
    tot = cnt = 0; per = {}
    for k in FIGHTS:
        r = best_six(core, k)
        if not r: return None
        w = W.get(k, 1); tot += w * r[0]; cnt += w * r[2]; per[k] = dict(flex=list(r[1]), counters=f'{r[2]}/{DATA[k][0]}', pairs=dict(zip(DATA[k][5], r[3])))
    return tot, cnt, per
if __name__ == '__main__':
    cands = {'yours': st['core']}
    for f in ('team/arch_fights.json',):
        if os.path.exists(f):
            for k, v in json.load(open(f)).items():
                if v: cands['arch ' + k] = v['core']
    if os.path.exists('team/core_fights.json'):
        for i, v in enumerate(json.load(open('team/core_fights.json'))[:4]): cands[f'free #{i + 1}'] = v['core']
    out = {}
    for lab, core in cands.items():
        r = team_score(core)
        if not r: continue
        out[lab] = dict(core=core, score=round(r[0], 2), counters=r[1], per=r[2])
        print(f"{lab:14s} {r[0]:7.2f} counters {r[1]:4.1f}/{sum(W.get(k, 1) * DATA[k][0] for k in FIGHTS):.0f}  {[c.split(' (')[0] for c in core]}  " +
              ' | '.join(f"{k} {v['counters']} +{'/'.join(x.split(' (')[0] for x in v['flex'])}" for k, v in r[2].items()))
    json.dump(out, open('team/team_fights.json', 'w'), indent=1)
