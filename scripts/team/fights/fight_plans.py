"""Fight plans (Vincent, 17 Nov): core of 4 + the best 2 swaps for EVERY remaining Ch9 fight, with its lead(s).
Per fight (team/<key>_eval.json from remaining_eval.py, core scored with its REAL builds via FIXED):
  1. swaps = the pair that gives the best one-to-one counter pairing (each foe -> a different member; counter = deals >= 90%
     or outspeeds + >= 100%, takes < 70%; or, with a setup move in its build, deals >= 90% after ONE setup turn and takes < 50%),
     subject to rules (b)(c) vs that fight's own attack types (no type hits 3+, every type resisted). Ties: total quality.
  2. lead = slot 1 (singles) / slots 1-2 (doubles): survives every opening Pokémon (takes < 100%), best matchup quality.
The fight being prepared (state 'fight') keeps its hand-checked six. Writes team/fight_plans.json + team/counters_<key>.json.
usage (from workspace/): DONE=... CR_RUN=rNN python3 -I ../scripts/team/fights/fight_plans.py"""
import itertools, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = ['x', '.', '20']; sys.path.insert(0, os.path.join(HERE, '..'))
import chapter_rules as C
st = json.load(open('team/state.json'))
CORE = st['core']; FIGHT = st.get('fight')
KEYS = [k for k in ['darkgardevoir', 'garbodor', 'karrina', 'spector', 'spector2', 'jenner9', 'amanda', 'erick'] if k not in set(st['done'])]
NEED_TIPS = {'garbodor': 'boss: ask Vincent for the community fight page before locking this in (fight protocol 4)'}


def load(key):
    R = json.load(open(f'team/{key}_eval.json'))
    best = {}
    for r in R['rows']:
        if r['name'] not in best or r.get('fixed') or (not best[r['name']].get('fixed') and r['score'] > best[r['name']]['score']):
            best[r['name']] = r
    return R, best


BARS = [1]
def mats(r, spe):
    cov, tk = np.array(r['cov'], float) * np.array(BARS), np.array(r['taken'], float)   # boss: % of ONE health bar
    fast = np.array([r['spe'] > s for s in spe])
    sm = r.get('setup_mult') or 1
    plain = ((cov >= 90) | (fast & (cov >= 100))) & (tk < 70)
    setup = (sm > 1) & (cov * sm >= 90) & (tk < 50) & ~plain
    q = np.minimum(np.maximum(cov, np.where(tk < 50, cov * sm * .8, 0)), 120) / 100 * np.where(fast, 1.15, 1) * (1 - np.minimum(tk, 100) / 200)
    return q, plain | setup, setup


def rule_fail(six, key):
    types = [s for s in C.W if key in C.FIGHTS[s]]
    weak3 = ['/'.join(s) for s in types if sum(C.eff(s, r['types'], r['ab']) > 1 for r in six) >= 3]
    nores = ['/'.join(s) for s in types if not any(C.eff(s, r['types'], r['ab']) < 1 for r in six)]
    return weak3, nores


plans = {}
for key in KEYS:
    R, best = load(key)
    FO = [f[1] for f in R['foes']]; FMT = R['foes'][0][2]; SPE = R['foe_spe']; n = len(FO)
    BARS[:] = R.get('foe_bars') or [1] * n
    core = [best[c] for c in CORE if c in best]
    if len(core) < 4: sys.exit(f'{key}: core member missing from the eval ({[c for c in CORE if c not in best]})')
    others = [r for r in best.values() if r['name'] not in CORE and r['name'].split(' (')[0] not in {c.split(' (')[0] for c in CORE}]
    pool = sorted(others, key=lambda r: -r['score'])[:45]
    for j in range(n):   # plus the best few specialists for every single foe
        pool += sorted(others, key=lambda r: -(mats(r, SPE)[1][j] * 10 + mats(r, SPE)[0][j]))[:6]
    pool = list({r['name']: r for r in pool}.values())
    M = {r['name']: mats(r, SPE) for r in core + pool}
    P = np.array(list(itertools.permutations(range(6), n))); ar = np.arange(n)
    def pairing(six):
        Q = np.array([M[r['name']][0] for r in six]); OK = np.array([M[r['name']][1] for r in six])
        key_ = OK[P, ar].sum(1) * 10 + Q[P, ar].sum(1); k = int(key_.argmax())
        return float(key_[k]), [int(x) for x in P[k]], int(OK[P[k], ar].sum())
    if key == FIGHT:   # the fight being prepared keeps its hand-checked six (Fights tab / make_report5 COUNTERS)
        fixed = [x for x in st['team'] if x not in CORE]
        cands = [tuple(best[x] for x in fixed)]
    else:
        cands = list(itertools.combinations(pool, 2))
    res = []
    for pair in cands:
        if pair[0]['name'].split(' (')[0] == pair[1]['name'].split(' (')[0]: continue
        six = core + list(pair)
        sc, pr, nok = pairing(six); w3, nr = rule_fail(six, key)
        res.append((sc - 30 * (len(w3) + len(nr)) + .01 * sum(r['score'] for r in pair), pair, pr, nok, w3, nr))
    res.sort(key=lambda x: -x[0])
    _, pair, pr, nok, w3, nr = res[0]
    six = core + list(pair)
    # leads: survive every opening Pokémon (taken < 100), then best quality vs them
    nl = 1 if FMT == 'Singles' else 2; lf = list(range(min(nl, n)))
    def lead_val(ix):
        tk = max(six[i]['taken'][j] for i in ix for j in lf)
        q = max(sum(M[six[i]['name']][0][j] for i, j in zip(ix, perm)) for perm in itertools.permutations(lf, len(lf))) if len(ix) == len(lf) else \
            sum(M[six[i]['name']][0][j] for i in ix for j in lf)
        return (tk < 100, q), tk
    lead = max(itertools.combinations(range(6), nl), key=lambda ix: lead_val(ix)[0])
    lv, ltk = lead_val(lead)
    srow = lambda r: dict(name=r['name'], ab=r['ab'], moves=r['moves'], setup=r.get('setup'), where=r.get('where'), dump=r.get('dump'),
                          nature=r.get('nature'), evs=r.get('evs'), types=r['types'])
    pairs = [dict(foe=FO[j], mon=six[pr[j]]['name'], ability=six[pr[j]]['ab'], dealt=int(six[pr[j]]['cov'][j] * BARS[j]), taken=int(six[pr[j]]['taken'][j]),
                  ok=bool(M[six[pr[j]]['name']][1][j]), setup=bool(M[six[pr[j]]['name']][2][j]) and six[pr[j]].get('setup')) for j in range(n)]
    plans[key] = dict(key=key, format=FMT, foes=FO, swaps=[srow(r) for r in pair], hand=key == FIGHT, counters=nok, n=n, pairs=pairs,
                      weak3=w3, nores=nr, leads=[six[i]['name'] for i in lead], lead_foes=[FO[j] for j in lf], lead_taken=round(float(ltk)),
                      lead_ok=bool(lv[0]), note=NEED_TIPS.get(key, ''))
    json.dump(dict(preview=False, plan=True, current=dict(counters=nok, pairs=pairs)), open(f'team/counters_{key}.json', 'w'), indent=1)
    print(f"{key:13s} {FMT:7s} swaps {[r['name'] for r in pair]} counters {nok}/{n} rules {w3 or ''}{nr or ''} "
          f"lead {[six[i]['name'] for i in lead]} vs {[FO[j] for j in lf]} takes {ltk:.0f}%")
json.dump(plans, open('team/fight_plans.json', 'w'), indent=1, ensure_ascii=False)
