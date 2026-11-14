"""Factory (??? Lv 60-64) six, per the fight protocol. Re-scores the strongest candidates with every legal move and the
fight's item/ability rules from the game data: Raichu Focus Sash (single hits capped at 99%; multi-hit breaks it),
Orthworm Earth Eater (Ground = 0), Shuca (Xurkitree) / Rindo (Swampert) halve the first super-effective Ground / Grass hit
(multi-hit loses only one hit's share). No Earthquake / Bulldoze / Discharge (they flip the field to Short-Circuit).
Requirements: a Sash / substitute breaker (multi-hit) and a non-Ground answer to Orthworm."""
import json, pickle, sys, itertools, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, os.path.join(HERE, '..', '..'))
from engine import Engine
E = Engine('.'); D = E.D
b = [b for b in E.battles if b['key'] == 'factory'][0]; FO = b['foes']
st = json.load(open('team/state.json')); C = pickle.load(open(f"team/r{st['run']}_native.json.pkl", 'rb'))['cands']
R = json.load(open('team/factory_eval.json'))
FLIP = {'EARTHQUAKE', 'BULLDOZE', 'MAGNITUDE', 'DISCHARGE', 'EXPLOSION', 'SELFDESTRUCT', 'FISSURE'}
SKIP = {'SOLARBEAM','SOLARBLADE','SKYATTACK','DIG','FLY','BOUNCE','DIVE','SKULLBASH','METEORBEAM','HYPERBEAM','GIGAIMPACT','FOCUSPUNCH',
        'FUTURESIGHT','DOOMDESIRE','FINALGAMBIT','LASTRESORT','DREAMEATER','BELCH','STEELBEAM','MINDBLOWN','OUTRAGE','PETALDANCE',
        'THRASH','RAGINGFURY','FAKEOUT','FIRSTIMPRESSION','SNORE','SPITUP','COUNTER','MIRRORCOAT','METALBURST','BIDE','ENDEAVOR',
        'FLING','NATURALGIFT','SYNCHRONOISE','ROLLOUT','ICEBALL','UPROAR','SHELLTRAP','BEAKBLAST','RAZORWIND'} | FLIP
def multi(mv): return 'BONERUSH' == mv or D.moves[mv].get('Function') in ('0C0', '0BD', '0BE') or mv in ('PINMISSILE', 'BULLETSEED', 'ROCKBLAST', 'ICICLESPEAR', 'TAILSLAP', 'SCALESHOT', 'DOUBLEHIT', 'DUALWINGBEAT', 'MUDBARRAGE', 'WATERSHURIKEN', 'TRIPLEAXEL', 'SURGINGSTRIKES', 'DOUBLEKICK', 'TWINEEDLE', 'DRAGONDARTS', 'BONEMERANG', 'DUALCHOP', 'GEARGRIND', 'DOUBLEIRONBASH')
def foe_moves(f):
    m = f['moves']; return [x for x, _ in m] if m and isinstance(m[0], (list, tuple)) else list(m)
def adj(c, f, m, d):
    mv = D.moves[m]; t = mv['Type']
    if f['name'] == 'Orthworm' and t == 'GROUND': return 0.0
    if f['name'] == 'Raichu' and not multi(m): d = min(d, 99)
    if f['name'] == 'Xurkitree' and t == 'GROUND' and E.chart_eff(t, f['types']) > 1: d *= 0.9 if multi(m) else 0.5
    if f['name'] == 'Swampert' and t == 'GRASS' and E.chart_eff(t, f['types']) > 1: d *= 0.9 if multi(m) else 0.5
    return d
best = {}
for x in R['rows']: best.setdefault(x['name'], x)
pool_names = [x['name'] for x in sorted(best.values(), key=lambda x: -x['score'])[:40]] + ['Whiscash', 'Raichu', 'Crobat']
cmap = {}
for c in C:
    if not c['gate'] and c['name'] in pool_names:
        if c['name'] not in cmap or best.get(c['name'], {}).get('ab') == c['ability']: cmap[c['name']] = c
rows = []
for n, c in cmap.items():
    cat = 'Physical' if c['stats']['Atk'] >= c['stats']['SpA'] else 'Special'
    L = [m for m in E.legal_moves(c['sid'], c['form'], c['src'].get('moves', [])) if m not in SKIP and D.moves[m]['Category'] == cat and int(D.moves[m].get('Strength') or 0) > 1]
    tab = {m: np.array([min(adj(c, f, m, E.damage_pct(c, f, m, D.moves[m], b, True)), 130) for f in FO]) for m in L}
    if not tab: continue
    top = sorted(tab, key=lambda m: -tab[m].sum())[:10]
    ms = max(itertools.combinations(top, min(3, len(top))), key=lambda ms: np.max([tab[m] for m in ms], axis=0).sum())
    cov = np.max([tab[m] for m in ms], axis=0)
    taken = np.array([max([E.damage_pct(f, c, m, D.moves[m], b, False) for m in foe_moves(f) if D.moves[m]['Category'] != 'Status'] + [0]) for f in FO])
    fast = np.array([c['stats']['Spe'] > f['stats']['Spe'] for f in FO])
    q = np.minimum(cov, 120) / 100 * np.where(fast, 1.15, 1) * (1 - np.minimum(taken, 100) / 200)
    q = np.where((taken >= 100) & ~(fast & (cov >= 100)), q * .5, q)
    rows.append(dict(name=n, ab=c['ability'], moves=[D.moves[m]['MoveName'] for m in ms], multi=any(multi(m) for m in ms),
                     cov=cov.round().tolist(), taken=taken.round().tolist(), q=q.tolist(), spe=c['stats']['Spe'], types=c['types'],
                     where=c['src']['where'], dump=c['src'].get('dump')))
Q = np.array([r['q'] for r in rows]); COV = np.array([r['cov'] for r in rows])
def ok(ix):
    ix = list(ix)
    breaker = any(rows[i]['multi'] and rows[i]['cov'][0] >= 100 for i in ix)
    orth = (COV[ix, 2] >= 100).any()
    return breaker and orth
def sc(ix):
    q = np.sort(Q[list(ix)], axis=0); return float((q[-1] + .35 * q[-2]).mean())
res = sorted(((sc(ix), ix) for ix in itertools.combinations(range(len(rows)), 6) if ok(ix)), reverse=True)
json.dump(dict(rows=rows, top=[[s, [rows[i]['name'] for i in ix]] for s, ix in res[:20]]), open('team/factory_team.json', 'w'))
for s, ix in res[:8]: print(round(s, 4), [rows[i]['name'] for i in ix])
s, ix = res[0]
print('foes', [f['name'] for f in FO])
for i in ix:
    r = rows[i]; print(r['name'], r['ab'], r['moves'], 'dealt', [int(v) for v in r['cov']], 'took', [int(v) for v in r['taken']], 'spe', r['spe'], r['where'], r['dump'])
