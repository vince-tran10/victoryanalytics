"""Best core PER ARCHETYPE for the remaining Ch9 fights (cores.py archetype rules + core_fights.py fight coverage)."""
import itertools, json, os, runpy, sys, io, contextlib, shutil
import numpy as np
tmp = sys.argv[1]
with contextlib.redirect_stdout(io.StringIO()):
    G = runpy.run_path('../scripts/team/cores.py', run_name='cores_lib') if False else None
sys.argv = ['cores.py', tmp]
with contextlib.redirect_stdout(io.StringIO()):
    G = runpy.run_path('../scripts/team/cores.py')
ARCH, ALL, POOL, TOP, order_roles, has_setup = G['ARCH'], G['ALL'], G['POOL'], G['TOP'], G['order_roles'], G['has_setup']
sys.argv = ['x', '.', '20']
sys.path.insert(0, '../scripts/team')
import chapter_rules as C
st = json.load(open('team/state.json'))
FIGHTS = [k for k in ['karrina', 'spector', 'spector2', 'jenner9', 'erick'] if k not in st['done']]
W = {'spector': .5, 'spector2': .5}
OK, Q, NF = {}, {}, {}
names = list(ALL)
for k in FIGHTS:
    R = json.load(open(f'team/{k}_eval.json')); spe = R['foe_spe']; NF[k] = len(spe)
    best = {}
    for y in R['rows']:
        if y['name'] not in best or y.get('fixed') or (not best[y['name']].get('fixed') and y['score'] > best[y['name']]['score']): best[y['name']] = y
    for n in names:
        y = best.get(n)
        if not y: OK[(k, n)] = np.zeros(len(spe), bool); Q[(k, n)] = np.zeros(len(spe)); continue
        cov, tk = np.array(y['cov'], float), np.array(y['taken'], float) / (1.3 if R['foes'][0][2] == 'Doubles' else 1)
        fast = np.array([y['spe'] > s for s in spe]); sm = y.get('setup_mult') or 1
        OK[(k, n)] = ((cov >= 90) & (tk < 70)) | (fast & (cov >= 100)) | ((sm > 1) & (cov * sm >= 90) & (tk < 50))
        Q[(k, n)] = np.minimum(np.maximum(cov, np.where(tk < 50, cov * sm * .8, 0)), 120) / 100 * np.where(fast, 1.15, 1) * (1 - np.minimum(tk, 100) / 200)
TYPES = {k: [s for s in C.W if k in C.FIGHTS[s]] for k in FIGHTS}
def weak3(ms):
    return sum(1 for k in FIGHTS for s in TYPES[k] if sum(C.eff(s, m.r['types'], m.ab) > 1 for m in ms) >= 3)
def fscore(ms):
    tot = cov = 0; per = {}
    for k in FIGHTS:
        ok = np.any([OK[(k, m.name)] for m in ms], axis=0); q = np.max([Q[(k, m.name)] for m in ms], axis=0)
        w = W.get(k, 1); c = int(ok.sum()); per[k] = f'{c}/{NF[k]}'; cov += w * c; tot += w * (c + .5 * q.mean())
    return tot, cov, per
out = {}
mine = [ALL[n] for n in st['core'] if n in ALL]
for key, title, idt, en_f, mem_f, id_f in ARCH:
    ens = sorted([m for m in ALL.values() if en_f(m)], key=lambda m: -m.r['blend'])[:8]
    others = [m for m in TOP if mem_f(m)]
    if key in ('electric', 'sun', 'snow', 'grassy'): others += [m for m in POOL if m not in others and id_f((m,)) >= .3][:15]
    if key == 'tr': others = [m for m in POOL if mem_f(m)][:40]
    res = []
    for e in ens:
        rest = [m for m in others if m.name != e.name and m.sp != e.sp]
        for trio in itertools.combinations(rest, 3):
            if len({m.sp for m in trio}) < 3: continue
            ms = (e,) + trio
            idv = id_f(ms) if key in ('balance', 'tr', 'setup') else id_f(trio)
            if key == 'snow' and 'AURORAVEIL' in e.legal and not any('AURORAVEIL' in m.legal for m in trio): idv = min(1, idv + .2)
            if key != 'balance' and idv < .6: continue
            if key == 'balance' and idv < .5: continue
            if not any(has_setup(m) for m in ms) or weak3(ms): continue
            t, c, per = fscore(ms)
            res.append((t, c, ms, per))
    res.sort(key=lambda x: -x[0])
    if not res: out[key] = None; continue
    t, c, ms, per = res[0]
    lreq = None if key in ('balance', 'setup') else en_f
    fit, o = order_roles(ms, lreq)
    out[key] = dict(title=title, score=round(t, 2), cover=c, per=per, core=[m.name for m in o], tiers=[m.r['tier'] for m in o])
    print(f"{title:22s} {t:5.2f} {c:4.1f}/24 {[m.name.split(' (')[0] + '(' + m.r['tier'] + ')' for m in o]} {per}")
if len(mine) == 4:
    t, c, per = fscore(mine); print(f"{'YOURS (balance)':22s} {t:5.2f} {c:4.1f}/24 {per}")
json.dump(out, open('team/arch_fights.json', 'w'), indent=1)
