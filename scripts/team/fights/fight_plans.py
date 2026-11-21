"""Fight plans (Vincent, 17 Nov): core of 4 + the best 2 swaps for EVERY remaining Ch9 fight, with its lead(s).
Per fight (team/<key>_eval.json from remaining_eval.py, core scored with its REAL builds via FIXED):
  1. swaps = the pair that gives the best one-to-one counter pairing (each foe -> a different member; counter = deals >= 90%
     or outspeeds + >= 100%, takes < 70%; or, with a setup move in its build, deals >= 90% after ONE setup turn and takes < 50%),
     subject to rules (b)(c) vs that fight's own attack types (no type hits 3+, every type resisted). Ties: total quality.
  2. lead = slot 1 (singles) / slots 1-2 (doubles): survives every opening Pokémon (takes < 100%), best matchup quality.
The fight being prepared (state 'fight') keeps its hand-checked six. Writes team/fight_plans.json + team/counters_<key>.json.
usage (from workspace/): DONE=... CR_RUN=rNN python3 -I ../scripts/team/fights/fight_plans.py"""
import itertools, json, os, re, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = ['x', '.', '20']; sys.path.insert(0, os.path.join(HERE, '..'))
import chapter_rules as C
sys.path.insert(0, HERE)
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
    plain = ((cov >= 90) & (tk < 70)) | (fast & (cov >= 100))   # rule 9: an outspeeding one-shot never gets hit
    setup = (sm > 1) & (cov * sm >= 90) & (tk < 50) & ~plain
    q = np.minimum(np.maximum(cov, np.where(tk < 50, cov * sm * .8, 0)), 120) / 100 * np.where(fast, 1.15, 1) * (1 - np.minimum(tk, 100) / 200)
    return q, plain | setup, setup


def rule_fail(six, key):
    types = [s for s in C.W if key in C.FIGHTS[s]]
    weak3 = ['/'.join(s) for s in types if sum(C.eff(s, r['types'], r['ab']) > 1 for r in six) >= 3]
    nores = ['/'.join(s) for s in types if not any(C.eff(s, r['types'], r['ab']) < 1 for r in six)]
    return weak3, nores


# ---- win conditions (fight protocol step 2, 17 Nov): what each foe does to win, and whether the six has a named answer
SETUP = {'SWORDSDANCE', 'DRAGONDANCE', 'NASTYPLOT', 'CALMMIND', 'QUIVERDANCE', 'BULKUP', 'SHELLSMASH', 'SHIFTGEAR', 'COIL', 'AGILITY',
         'ROCKPOLISH', 'TAILGLOW', 'GEOMANCY', 'VICTORYDANCE', 'FILLETAWAY', 'WORKUP', 'GROWTH', 'HONECLAWS', 'IRONDEFENSE', 'COTTONGUARD', 'AMNESIA', 'CURSE'}
HEAL = {'RECOVER', 'ROOST', 'SLACKOFF', 'SOFTBOILED', 'MOONLIGHT', 'SYNTHESIS', 'MORNINGSUN', 'WISH', 'SHOREUP', 'STRENGTHSAP', 'MILKDRINK', 'REST'}
WINCON = [  # (label, foe trigger moves, foe trigger abilities, foe trigger items, answer moves, answer abilities)
    ('Setup', SETUP, {'SPEEDBOOST', 'MOXIE', 'BEASTBOOST'}, set(), {'HAZE', 'CLEARSMOG', 'ROAR', 'WHIRLWIND', 'DRAGONTAIL', 'CIRCLETHROW', 'ENCORE'}, {'UNAWARE'}),
    ('Healing', HEAL, {'POISONHEAL', 'REGENERATOR'}, {'BLACKSLUDGE', 'LEFTOVERS'}, {'HEALBLOCK', 'GASTROACID', 'KNOCKOFF', 'TAUNT'}, set()),
    ('Screens', {'REFLECT', 'LIGHTSCREEN', 'AURORAVEIL'}, set(), set(), {'BRICKBREAK', 'PSYCHICFANGS', 'DEFOG', 'RAGINGBULL'}, {'INFILTRATOR'}),
    ('Trick Room', {'TRICKROOM'}, set(), set(), {'TAUNT', 'IMPRISON', 'FAKEOUT'}, set()),
    ('Sleep', {'HYPNOSIS', 'SPORE', 'SLEEPPOWDER', 'SING', 'LOVELYKISS', 'YAWN', 'DARKVOID', 'GRASSWHISTLE'}, set(), set(), {'SAFEGUARD', 'MISTYTERRAIN', 'ELECTRICTERRAIN'}, {'INSOMNIA', 'VITALSPIRIT', 'SWEETVEIL', 'COMATOSE'}),
    ('Perish Song', {'PERISHSONG'}, set(), set(), {'TAUNT'}, set()),
]
def _id(x): return re.sub(r'[^A-Z]', '', str(x or '').upper())
def wincons(R, j):
    mv = {_id(m) for m in (R.get('foe_moves') or [[]] * 99)[j]}; ab = _id((R.get('foe_ability') or [''] * 99)[j]); it = _id((R.get('foe_item') or [''] * 99)[j])
    return [w for w in WINCON if (mv & w[1]) or ab in w[2] or it in w[3]]
LEGAL = {r['name']: set(r['legal']) for r in json.load(open('team/tier_all.json'))['rows']} if os.path.exists('team/tier_all.json') else {}
def answers_for(w, six, swaps=()):
    out = []
    for r in six:
        b = BUILD.get(r['name']) or {}
        mv = {_id(m) for m in (b.get('moves') or r.get('moves') or [])}; ab = _id(b.get('ability') or r.get('ab'))
        hit = sorted(mv & w[4]) + ([ab] if ab in w[5] else [])
        if hit: out.append(f"{NAMES.get(hit[0], hit[0].title())} ({r['name'].split(' (')[0]})")
    if not out:   # debug mode: a swap can be taught the answer in place of its weakest move
        for r in six:
            if r['name'] not in swaps: continue
            t = sorted(LEGAL.get(r['name'], set()) & w[4])
            if t: out.append(f"teach {NAMES.get(t[0], t[0].title())} ({r['name'].split(' (')[0]})"); break
    return out

IB = json.load(open('team/ideal_builds.json')) if os.path.exists('team/ideal_builds.json') else {}
BUILD = {n: dict(moves=b['moves'], ability=b['ability']) for n, b in IB.items()}
for n, m in (st.get('moves') or {}).items(): BUILD[n] = dict(moves=m, ability=(st.get('abilities') or {}).get(n, (BUILD.get(n) or {}).get('ability')))
import sys as _s; _s.path.insert(0, os.path.join(HERE, '..', '..'))
from dataset import Data as _Data
NAMES = {k: v['MoveName'] for k, v in _Data('.').moves.items()}
NAMES.update({'UNAWARE': 'Unaware', 'INFILTRATOR': 'Infiltrator', 'INSOMNIA': 'Insomnia', 'VITALSPIRIT': 'Vital Spirit', 'SWEETVEIL': 'Sweet Veil', 'COMATOSE': 'Comatose'})

# ---- ONE six for every remaining fight (Vincent, 21 Nov: fights can come out of order) -------------------------------
if st.get('one_six') and KEYS:
    FW = {'spector': .5, 'spector2': .5}   # day OR night: one of the two
    DATA = {}
    for key in KEYS:
        R, best = load(key); SPE = R['foe_spe']; n = len(R['foes'])
        BARS[:] = R.get('foe_bars') or [1] * n
        core = [best[c] for c in CORE]
        others = {r['name']: r for r in best.values() if r['name'] not in CORE and r['name'].split(' (')[0] not in {c.split(' (')[0] for c in CORE}}
        top = sorted(others.values(), key=lambda r: -r['score'])[:40]
        for j in range(n):
            top += sorted(others.values(), key=lambda r: -(mats(r, SPE)[1][j] * 10 + mats(r, SPE)[0][j]))[:5]
        DATA[key] = (R, best, core, others, {r['name'] for r in top}, list(BARS))
    union = set.union(*[d[4] for d in DATA.values()]) & set.intersection(*[set(d[3]) for d in DATA.values()])
    union = sorted(union)
    def fight_score(key, names):
        R, best, core, others, _, bars = DATA[key]; BARS[:] = bars
        n = len(R['foes']); SPE = R['foe_spe']; six = core + [others[x] for x in names]
        Q = np.array([mats(r, SPE)[0] for r in six]); OK = np.array([mats(r, SPE)[1] for r in six])
        P = np.array(list(itertools.permutations(range(6), n))); ar = np.arange(n)
        kk = OK[P, ar].sum(1) * 10 + Q[P, ar].sum(1); k = int(kk.argmax())
        w3, nr = rule_fail(six, key)
        ans = sum(1 for j in range(n) for w in wincons(R, j) if answers_for(w, six, names))
        return float(kk[k]) + 5 * ans - 30 * (len(w3) + len(nr)), int(OK[P[k], ar].sum()), n, len(w3) + len(nr)
    MC = {}
    for key in KEYS:   # cache mats per fight
        pass
    tot = []
    for a, b in itertools.combinations(union, 2):
        if a.split(' (')[0] == b.split(' (')[0]: continue
        sc = cnt = fails = 0; det = {}; worst = 9
        for key in KEYS:
            R = DATA[key][0]; w = FW.get(key, 1) * (2 if R['foes'][0][2] == 'Singles' else 1)
            v, c, n, fl = fight_score(key, (a, b)); sc += w * v; det[key] = f'{c}/{n}'; cnt += FW.get(key, 1) * c; fails += fl
            if key not in FW: worst = min(worst, c)
        tot.append((sc, (a, b), det, cnt, worst, fails))
    tot.sort(key=lambda x: (x[5], -x[3], -x[4], -x[0]))   # rules (b)(c) are hard: pass them first   # rule 9: counters first (Spector day/night count half each), then the weakest fight, then quality
    for sc, pr_, det, cnt, wst, fl_ in tot[:8]: print('ONE-SIX', cnt, round(sc, 1), pr_, det)
    pick = list(tot[0][1])
    st['plan_swaps'] = {k: pick for k in KEYS}
    st['team'] = list(CORE) + pick
    for k in KEYS: (st.get('plan_pairs') or {}).pop(k, None)
    json.dump(st, open('team/state.json', 'w'), indent=1, ensure_ascii=False)
    json.dump(dict(pick=pick, top=[dict(score=round(sc, 1), counters=c_, swaps=list(p), per_fight=d) for sc, p, d, c_, w_, f_ in tot[:8]]), open('team/one_six.json', 'w'), indent=1)
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
    BOSS = n > 1 and all('(bar ' in f for f in FO)   # one boss over several bars: the same member may take several bars
    def pairing(six):
        Q = np.array([M[r['name']][0] for r in six]); OK = np.array([M[r['name']][1] for r in six])
        if BOSS:
            pick = [int((OK[:, j] * 10 + Q[:, j]).argmax()) for j in range(n)]
            return float(sum(OK[i, j] * 10 + Q[i, j] for j, i in enumerate(pick))), pick, int(sum(OK[i, j] for j, i in enumerate(pick)))
        key_ = OK[P, ar].sum(1) * 10 + Q[P, ar].sum(1); k = int(key_.argmax())
        return float(key_[k]), [int(x) for x in P[k]], int(OK[P[k], ar].sum())
    for n_, b_ in ((st.get('plan_builds') or {}).get(key) or {}).items():   # this fight's hand-plan builds (e.g. Gastro Acid Muk)
        BUILD[n_] = dict(moves=b_.get('moves'), ability=b_.get('ability'))
    HAND = (st.get('plan_swaps') or {}).get(key)   # hand-made plans (fight protocol done in chat), e.g. Garbodor 17 Nov
    if key == FIGHT:   # the fight being prepared keeps its hand-checked six (Fights tab / make_report5 COUNTERS)
        fixed = [x for x in st['team'] if x not in CORE]
        cands = [tuple(best[x] for x in fixed)]
    elif HAND:
        cands = [tuple(best[x] for x in HAND)]
    else:
        cands = list(itertools.combinations(pool, 2))
    for pr_ in cands:
        for r in pr_: M.setdefault(r['name'], mats(r, SPE))
    res = []
    for pair in cands:
        if pair[0]['name'].split(' (')[0] == pair[1]['name'].split(' (')[0]: continue
        six = core + list(pair)
        sc, pr, nok = pairing(six); w3, nr = rule_fail(six, key)
        ans = sum(1 for j in range(n) for w in wincons(R, j) if answers_for(w, six, [x['name'] for x in pair]))   # utility valued per fight (Vincent, 17 Nov)
        res.append((sc + 5 * ans - 30 * (len(w3) + len(nr)) + .01 * sum(r['score'] for r in pair), pair, pr, nok, w3, nr))
    res.sort(key=lambda x: -x[0])
    SIM = None
    if BOSS or n == 1 and R.get('foe_bars', [1])[0] > 1:   # boss fight: play it turn by turn (18 Nov), solo and with the partner
        import boss_sim as BS
        bl = dict(BUILD)
        def sim_pair(pr_, lead_):
            six_ = core + list(pr_)
            a = BS.simulate(R, six_, bl, key, with_partner=True, lead=lead_); b = BS.simulate(R, six_, bl, key, with_partner=False, lead=lead_)
            left = lambda r_: sum(max(0, t['hp']) for t in r_['team'])
            return (2 * b['ok'] + a['ok'], left(b) + left(a)), a, b
        LEAD0 = ((st.get('plan_leads') or {}).get(key) or [None])[0]
        pool_ = [x[1] for x in res[:30]] if not HAND and key != FIGHT else \
            [res[0][1]] + list(itertools.combinations(sorted(pool, key=lambda r: -r['score'])[:18], 2))[:60]   # hand plan + 60 alternatives
        scored = []
        for pr_ in pool_:
            if pr_[0]['name'].split(' (')[0] == pr_[1]['name'].split(' (')[0]: continue
            for r in pr_: M.setdefault(r['name'], mats(r, SPE))
            k_, a, b = sim_pair(pr_, LEAD0 if LEAD0 in [x['name'] for x in core + list(pr_)] else None)
            scored.append((k_, pr_, a, b))
        scored.sort(key=lambda x: x[0], reverse=True)
        chosen = res[0][1]
        k0, a0, b0 = sim_pair(chosen, LEAD0)
        SIM = dict(plan=dict(melia=BS.summary(a0), solo=BS.summary(b0), log=a0['log'][:40]),
                   best=[dict(swaps=[r['name'] for r in pr_], melia=BS.summary(a), solo=BS.summary(b)) for k_, pr_, a, b in scored[:3]])
        if not HAND and key != FIGHT and scored and scored[0][0] > k0:   # no hand plan: the simulator decides between near-equal pairs
            res.insert(0, next(x for x in res if x[1] == scored[0][1]) if any(x[1] == scored[0][1] for x in res) else res[0])
    if os.environ.get('DEBUG_TOP') == key:   # inspection: the best pairs and why
        for sc_, pr_, prr_, nok_, w3_, nr_ in res[:8]:
            six_ = core + list(pr_)
            print('TOP', round(sc_, 2), [r['name'] for r in pr_], 'counters', nok_, 'rules', w3_ + nr_,
                  [(FO[j], six_[prr_[j]]['name'], int(six_[prr_[j]]['cov'][j] * BARS[j]), int(six_[prr_[j]]['taken'][j])) for j in range(n)],
                  [(w[0], answers_for(w, six_, [x['name'] for x in pr_])) for j in range(n) for w in wincons(R, j)])
    _, pair, pr, nok, w3, nr = res[0]
    six = core + list(pair)
    # leads: survive every opening Pokémon (taken < 100), then best quality vs them
    PARTNER = {'darkgardevoir', 'garbodor'}   # Melia controls the other slot: you send ONE Pokémon at a time
    nl = 1 if FMT == 'Singles' or key in PARTNER else 2; lf = list(range(min(nl, n)))
    def lead_val(ix):
        tk = max(six[i]['taken'][j] for i in ix for j in lf)
        q = max(sum(M[six[i]['name']][0][j] for i, j in zip(ix, perm)) for perm in itertools.permutations(lf, len(lf))) if len(ix) == len(lf) else \
            sum(M[six[i]['name']][0][j] for i in ix for j in lf)
        return (tk < 100, q), tk
    lead = max(itertools.combinations(range(6), nl), key=lambda ix: lead_val(ix)[0])
    LEADS = (st.get('plan_leads') or {}).get(key)   # hand-picked lead (a utility lead the evaluator can't score)
    if LEADS: lead = tuple(i for i, r in enumerate(six) if r['name'] in LEADS)
    lv, ltk = lead_val(lead)
    PP = (st.get('plan_pairs') or {}).get(key)   # hand pairing (fight protocol in chat): {foe: our mon}
    if PP:
        pr = [next((i for i, r in enumerate(six) if r['name'] == PP.get(FO[j])), pr[j]) for j in range(n)]
        nok = sum(bool(M[six[pr[j]]['name']][1][j]) for j in range(n))
    srow = lambda r: dict(name=r['name'], ab=r['ab'], moves=r['moves'], setup=r.get('setup'), where=r.get('where'), dump=r.get('dump'),
                          nature=r.get('nature'), evs=r.get('evs'), types=r['types'])
    pairs = [dict(foe=FO[j], mon=six[pr[j]]['name'], ability=six[pr[j]]['ab'], dealt=int(six[pr[j]]['cov'][j] * BARS[j]), taken=int(six[pr[j]]['taken'][j]),
                  ok=bool(M[six[pr[j]]['name']][1][j]), setup=bool(M[six[pr[j]]['name']][2][j]) and six[pr[j]].get('setup'),
                  wincons=[dict(what=w[0], answers=answers_for(w, six, [x['name'] for x in pair])) for w in wincons(R, j)]) for j in range(n)]
    plans[key] = dict(key=key, format=FMT, foes=FO, swaps=[srow(r) for r in pair], counters=nok, n=n, pairs=pairs,
                      weak3=w3, nores=nr, leads=[six[i]['name'] for i in lead], lead_foes=[FO[j] for j in lf], lead_taken=round(float(ltk)),
                      sim=SIM, lead_ok=bool(lv[0]), note='' if (key == FIGHT or HAND) else NEED_TIPS.get(key, ''), hand=bool(key == FIGHT or HAND))
    json.dump(dict(preview=False, plan=True, current=dict(counters=nok, pairs=pairs)), open(f'team/counters_{key}.json', 'w'), indent=1)
    BUILD.update({n: dict(moves=m, ability=(st.get('abilities') or {}).get(n)) for n, m in (st.get('moves') or {}).items()})   # undo per-fight builds
    print(f"{key:13s} {FMT:7s} swaps {[r['name'] for r in pair]} counters {nok}/{n} rules {w3 or ''}{nr or ''} "
          f"lead {[six[i]['name'] for i in lead]} vs {[FO[j] for j in lf]} takes {ltk:.0f}%")
json.dump(plans, open('team/fight_plans.json', 'w'), indent=1, ensure_ascii=False)
