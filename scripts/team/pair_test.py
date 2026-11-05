import pickle, sys, os, json, itertools
sys.path.insert(0, 'scripts/team'); sys.path.insert(0, 'scripts')
from engine import Engine
W2, WF, WS = 0.35, 0.35, 0.03
PFX = os.environ.get('PFX', 'r7')
res = {}
LV = {}
for mode in ['native', 'Singles', 'Doubles']:
    os.environ['FORCE_FORMAT'] = mode
    E = Engine('.')
    d = pickle.load(open(f'team/{PFX}_{mode}.json.pkl', 'rb'))
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
    def get(name):
        xs = [c for c in cands if c['name'] == name and not c.get('ability_changed')] or [c for c in cands if c['name'] == name]
        return max(xs, key=lambda c: c['solo_total'])
    core = [get(n) for n in ['Golisopod (Aevian Form)', 'Annihilape', 'Rhyperior', 'Gholdengo']]
    ready = [c for c in cands if not c['gate'] and not c.get('ability_changed') and all(c['sid'] != k['sid'] for k in core)]
    ready.sort(key=lambda c: -tscore(core + [c]))
    force = {'Hariyama', 'Arcanine', 'Whiscash', 'Wyrdeer', 'Tangrowth', 'Meganium', 'Lapras (Aevian Form)', 'Glaceon', 'Sylveon', 'Jellicent', 'Leavanny (Aevian Form)', 'Ludicolo', 'Appletun', 'Glalie (Aevian Form)'}
    pool = ready[:30] + [c for c in ready[30:] if c['name'] in force]
    for c in pool: LV[c['name']] = c['src'].get('level')
    out = {}
    for a, b in itertools.combinations(pool, 2):
        if a['sid'] == b['sid']:
            continue
        out[a['name'] + ' + ' + b['name']] = tscore(core + [a, b])
    res[mode] = out
names = set(res['native']) & set(res['Singles']) & set(res['Doubles'])
rows = sorted(((sum(res[m][n] for m in res) / 3, n) for n in names), reverse=True)
for avg, n in rows[:15]:
    print(f'{avg:.3f}', n, {m: round(res[m][n], 3) for m in res}, 'lv:', LV.get(n.split(' + ')[0]), LV.get(n.split(' + ')[1]))
json.dump(res, open(f'team/pair_{PFX}.json', 'w'))
