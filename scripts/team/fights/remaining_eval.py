"""General six for the remaining hard fights: every owned mon x ability, FULL legal moveset (3 attacks + Protect)
scored vs every foe of every remaining hard fight with the engine (exact game data + field multipliers), foe best hits,
speed, doubles double-targeting. Singles fights count double (chapter rule). Writes team/remaining_eval.json.
usage (from workspace/): MOVE_RULES=relearn FORCE_FORMAT=native python3 -I ../scripts/team/fights/remaining_eval.py <fight,...>"""
import json, pickle, sys, itertools, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, os.path.join(HERE, '..', '..'))
from engine import Engine
E = Engine('.'); D = E.D
KEYS = sys.argv[1].split(',')
BAT = [b for k in KEYS for b in E.battles if b['key'] == k]
st = json.load(open('team/state.json')); C = pickle.load(open(f"team/r{st['run']}_native.json.pkl", 'rb'))['cands']
SKIP = {'SOLARBEAM','SOLARBLADE','SKYATTACK','DIG','FLY','BOUNCE','DIVE','SKULLBASH','METEORBEAM','HYPERBEAM','GIGAIMPACT','FOCUSPUNCH',
        'FUTURESIGHT','DOOMDESIRE','EXPLOSION','SELFDESTRUCT','MISTYEXPLOSION','FINALGAMBIT','LASTRESORT','DREAMEATER','BELCH','STEELBEAM',
        'MINDBLOWN','OUTRAGE','PETALDANCE','THRASH','RAGINGFURY','FAKEOUT','FIRSTIMPRESSION','SNORE','SPITUP','COUNTER','MIRRORCOAT',
        'METALBURST','BIDE','ENDEAVOR','FLING','NATURALGIFT','SYNCHRONOISE','ROLLOUT','ICEBALL','UPROAR','SHELLTRAP','BEAKBLAST'}
FOES = [(bi, j, f) for bi, b in enumerate(BAT) for j, f in enumerate(b['foes'])]
def fw(b): return (2.0 if b['format'] == 'Singles' else 1.0) * (b.get('weight') or 1.0)
WT = np.array([fw(BAT[bi]) / len(BAT[bi]['foes']) for bi, j, f in FOES])
def foe_moves(f):
    m = f['moves']; return [x for x, _ in m] if m and isinstance(m[0], (list, tuple)) else list(m)
def evaluate(c):
    cat = 'Physical' if c['stats']['Atk'] >= c['stats']['SpA'] else 'Special'
    L = [m for m in E.legal_moves(c['sid'], c['form'], c['src'].get('moves', [])) if m not in SKIP
         and D.moves[m]['Category'] == cat and int(D.moves[m].get('Strength') or 0) > 1]
    if not L: return None
    tab = {}
    for m in L:
        row = []
        for bi, j, f in FOES:
            try: d = E.damage_pct(c, f, m, D.moves[m], BAT[bi], True)
            except Exception: d = 0
            row.append(min(d, 130))
        tab[m] = np.array(row)
    top = sorted(tab, key=lambda m: -(tab[m] * WT).sum())[:10]
    best = max(itertools.combinations(top, min(3, len(top))), key=lambda ms: (np.max([tab[m] for m in ms], axis=0) * WT).sum())
    cov = np.max([tab[m] for m in best], axis=0)
    taken = []
    for bi, j, f in FOES:
        t = 0
        for m in foe_moves(f):
            mv = D.moves.get(m)
            if not mv or mv['Category'] == 'Status': continue
            try: t = max(t, E.damage_pct(f, c, m, mv, BAT[bi], False))
            except Exception: pass
        taken.append(t * (1.3 if BAT[bi]['format'] == 'Doubles' else 1.0))
    taken = np.array(taken)
    fast = np.array([c['stats']['Spe'] > f['stats']['Spe'] for bi, j, f in FOES])
    q = np.minimum(cov, 120) / 100 * np.where(fast, 1.15, 1) * (1 - np.minimum(taken, 100) / 200)
    q = np.where((taken >= 100) & ~(fast & (cov >= 100)), q * .5, q)
    return best, cov, taken, q
out, seen = [], set()
for c in sorted(C, key=lambda c: -c.get('solo_total', 0)):
    if c['gate']: continue
    k = (c['name'], c['ability'])
    if k in seen: continue
    seen.add(k)
    r = evaluate(c)
    if not r: continue
    best, cov, taken, q = r
    out.append(dict(name=c['name'], ab=c['ability'], types=c['types'], moves=[D.moves[m]['MoveName'] for m in best], mids=list(best),
                    cov=cov.round().tolist(), taken=taken.round().tolist(), q=q.tolist(), score=float((q * WT).sum() / WT.sum()),
                    where=c['src']['where'], dump=c['src'].get('dump'), spe=c['stats']['Spe'], nature=c['nature'], evs=c['evs'], item=c['item'],
                    base_spe=c['base']['Spe']))
out.sort(key=lambda x: -x['score'])
json.dump(dict(foes=[(BAT[bi]['key'], f['name'], BAT[bi]['format']) for bi, j, f in FOES], wt=WT.tolist(), rows=out),
          open(os.environ.get('EVAL_OUT', 'team/remaining_eval.json'), 'w'), default=str)
for x in out[:40]:
    print(f"{x['score']:.3f} {x['name'][:24]:24s} {x['ab'][:12]:12s} {'/'.join(x['types']):16s} spe{x['spe']} {x['moves']} {x['where']}#{x['dump']}")
