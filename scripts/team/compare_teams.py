"""Score named sixes in native/Singles/Doubles runs and under weight variants; also top teams by local search."""
import pickle, sys, os, itertools, json
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('MOVE_RULES', 'relearn')
from engine import Engine
BASE = sys.argv[1]; PFX = sys.argv[2]
ENG = {}
for f in ('native', 'Singles', 'Doubles'):
    os.environ['FORCE_FORMAT'] = f; ENG[f] = Engine(BASE)
E = ENG['native']
runs = {f: pickle.load(open(f'{PFX}_{f}.json.pkl', 'rb')) for f in ('native', 'Singles', 'Doubles')}


def pick(cands, name):
    xs = [c for c in cands if c['name'] == name]
    return max(xs, key=lambda c: (not c['ability_changed'], c['solo_total'])) if xs else None


def score(team, W2=.35, WF=.35, WS=.03, keys=None, f='native'):
    tot = wt = 0
    for b in ENG[f].battles:
        if keys and b['key'] not in keys: continue
        foes = b['foes']; s = 0
        for i in range(len(foes)):
            qs = sorted((m['matchups'][b['key']][i]['q'] for m in team), reverse=True)
            s += qs[0] + W2 * (qs[1] if len(qs) > 1 else 0)
        frag = sum(sum(1 for r in m['matchups'][b['key']] if r['deff'] >= 100) / len(foes) for m in team) / len(team)
        sup = set()
        if b['format'] == 'Doubles':
            for m in team: sup |= m['tags']
        tot += (s / len(foes) - WF * frag + WS * len(sup)) * b['weight']; wt += b['weight']
    return tot / wt


TEAMS = json.loads(sys.argv[3])
W = [(.35, .35, .03), (.2, .35, .03), (.5, .35, .03), (.35, .2, .03), (.35, .5, .03), (.35, .35, 0), (.35, .35, .06), (.5, .5, .06)]
for label, names in TEAMS.items():
    row = []
    for f, P in runs.items():
        team = [pick(P['cands'], n) for n in names]
        if None in team: row.append(f'{f}: missing {[n for n, t in zip(names, team) if t is None]}'); continue
        row.append(f'{f} {score(team, f=f):.3f}')
    P = runs['native']; team = [pick(P['cands'], n) for n in names]
    sens = [round(score(team, *w), 3) for w in W] if None not in team else []
    print(f'{label:28s}', ' | '.join(row), '| sens', sens)
