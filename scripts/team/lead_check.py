import sys, os, json
sys.argv = ['x', '.', '44']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gamedata'))
import chapter_rules as C, gamedata as G
keys = list(C.byk)
def pick(n): return min((k for k in keys if C.nm(C.byk[k]) == n), key=lambda k: (C.byk[k]['src']['where'] != 'Party', -C.byk[k]['solo_total']))
SIX = ['Vikavolt', 'Ludicolo', 'Rhyperior', 'Armarouge', 'Musharna-A', 'Annihilape']
T = {n: pick(n) for n in SIX}
# opposing leads = first Pokémon of each trainer (exact game order); singles: 1 lead, doubles: 2
def leads(b):
    fo = b['foes']; key = b['key']
    if key in G.FIGHTS and len(G.FIGHTS[key]) == 2:
        n1 = len(G.trainer(*G.FIGHTS[key][0])['mons'])
        return [0, n1] if b['format'] == 'Doubles' else [0]
    return [0, 1] if b['format'] == 'Doubles' and len(fo) > 1 and 'bar' not in fo[1]['name'] else ([0] if b['format'] == 'Singles' else [0, 2])
print(f"{'fight':9s} {'fmt':7s} opp leads")
for b in C.HARD:
    L = leads(b)
    print(f"{b['key']:9s} {b['format']:7s} {[b['foes'][i]['name'] for i in L]}")
    for n, k in T.items():
        rows = [C.byk[k]['matchups'][b['key']][i] for i in L]
        surv = all(r['deff'] < 100 for r in rows)
        txt = ' | '.join(f"vs {b['foes'][i]['name'][:10]}: hits {r['off']:.0f}% {'first' if r['faster'] else 'second'}, takes {r['deff']:.0f}%" for i, r in zip(L, rows))
        print(f"    {n:11s} {'SURVIVES' if surv else 'one-shot'}  {txt}")
# singles-only team score: current vs top alternatives
def sc_fmt(ks, fmt):
    tot = tw = 0
    for b in C.HARD:
        if b['format'] != fmt: continue
        n = len(b['foes']); s = 0
        for i in range(n):
            qs = sorted((C.I1[k][0][b['key']][i] for k in ks), reverse=True); s += qs[0] + .35 * qs[1]
        tot += (s / n - .35 * sum(C.I1[k][1][b['key']] for k in ks) / 6) * b['weight']; tw += b['weight']
    return tot / tw
ALT = {'CURRENT': SIX, 'deep#1': ['Golisopod-A', 'Glalie-A', 'Azumarill', 'Armarouge', 'Scrafty', 'Ampharos'],
       'deep#2': ['Golisopod-A', 'Glalie-A', 'Armarouge', 'Musharna-A', 'Ludicolo', 'Gholdengo'],
       'OLD': ['Golisopod-A', 'Annihilape', 'Glalie-A', 'Clawitzer', 'Gholdengo', 'Musharna-A']}
for nm_, v in ALT.items():
    ks = [pick(n) for n in v]
    print(f"{nm_:8s} singles {sc_fmt(ks, 'Singles'):.4f}  doubles {sc_fmt(ks, 'Doubles'):.4f}")
