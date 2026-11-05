import pickle, sys, os, json
sys.path.insert(0, 'scripts/team'); sys.path.insert(0, 'scripts')
os.environ['WALK'] = '1'
from engine import Engine
W2, WF, WS = 0.35, 0.35, 0.03
res = {}
for mode in ['native', 'Singles', 'Doubles']:
    os.environ['FORCE_FORMAT'] = mode
    E = Engine('.')
    d = pickle.load(open(f'team/res_{mode}.json.pkl', 'rb'))
    cands = d['cands']
    def bscore(team, b):
        foes = b['foes']; tot = 0
        for i in range(len(foes)):
            qs = sorted((m['matchups'][b['key']][i]['q'] for m in team), reverse=True)
            tot += qs[0] + W2 * (qs[1] if len(qs) > 1 else 0)
        frag = sum(sum(1 for r in m['matchups'][b['key']] if r['deff'] >= 100) / len(foes) for m in team) / len(team)
        sup = set()
        if b['format'] == 'Doubles':
            for m in team: sup |= m['tags']
        return tot / len(foes) - WF * frag + WS * len(sup)
    def tscore(team):
        return sum(bscore(team, b) * b['weight'] for b in E.battles) / sum(b['weight'] for b in E.battles)
    def get(name, owned=None):
        xs = [c for c in cands if c['name'] == name and not c.get('ability_changed') and (owned is None or c['src']['where'] == owned)]
        xs = xs or [c for c in cands if c['name'] == name]
        return max(xs, key=lambda c: c['solo_total'])
    core = [get(n) for n in ['Golisopod (Aevian Form)', 'Annihilape', 'Rhyperior', 'Gholdengo', 'Hariyama']]
    cur = [c for c in cands if c['src']['where'] == 'Party' and not c.get('ability_changed')]
    out = {'current': tscore(cur)}
    for c in cands:
        if c['gate'] or any(c['sid'] == k['sid'] for k in core):
            continue
        out[c['name'] + ' [' + c['ability'] + ']'] = tscore(core + [c])
    res[mode] = out
names = set(res['native']) & set(res['Singles']) & set(res['Doubles'])
rows = sorted(((sum(res[m][n] for m in res) / 3, n) for n in names), reverse=True)
print('current party: ', {m: round(res[m]['current'], 3) for m in res})
for avg, n in rows[:15]:
    print(f'{avg:.3f}', n, {m: round(res[m][n], 3) for m in res})
json.dump(res, open('team/slot_test.json', 'w'))
