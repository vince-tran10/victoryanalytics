"""Team check under the chapter rules: every six from Party+Active (top-N pool) passing (b) no 3+ weakness, (c) every
threat type resisted, (d) every hard-fight foe hit SE or one-shot with <= 2 misses; ranked by hard-fight score.
usage (from workspace/): CR_RUN=r30 DONE=... TEAM_NAMES='[...]' python3 -I ../scripts/team/team_check.py [N=36]
Prints JSON on the last line: {"rank":..,"of":..,"gap":..,"top":[...]}"""
import sys, os, itertools, json
_N = sys.argv[1] if len(sys.argv) > 1 else '36'
sys.argv = ['x', '.', _N]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chapter_rules as C
keys = list(C.byk)
idx = {}
for i, (bk, fo) in enumerate(C.FOES):
    b = [b for b in C.HARD if b['key'] == bk][0]; idx[i] = (bk, [id(f) for f in b['foes']].index(id(fo)))
OFF = {k: [C.byk[k]['matchups'][idx[i][0]][idx[i][1]]['off'] for i in range(len(C.FOES))] for k in keys}
def base_ok(combo):
    return all(sum(C.WK[k][s] for k in combo) < 3 and any(C.RS[k][s] for k in combo) for s in C.MAJOR)
def misses(combo):
    return [i for i in range(len(C.FOES)) if not any(C.HT[k][i] or OFF[k][i] >= 100 for k in combo)]
_names = json.loads(os.environ['TEAM_NAMES'])
ck = tuple(min((k for k in keys if C.byk[k]['name'] == n), key=lambda k: (C.byk[k]['src']['where'] != 'Party', -C.byk[k]['solo_total']))
           for n in _names if any(C.byk[k]['name'] == n for k in keys))
cs = C.score(ck)
L = [combo for combo in itertools.combinations(keys, 6) if base_ok(combo) and len(misses(combo)) <= 2]
r = sorted(((C.score(ks), ks) for ks in L), reverse=True)
rk = next((n + 1 for n, (sc, ks) in enumerate(r) if set(ks) == set(ck)), None)
top = [dict(score=round(sc, 4), pct=round(sc / cs * 100, 1), team=[C.nm(C.byk[t]) for t in ks],
            misses=[f"{C.FOES[i][1]['name']} ({C.FOES[i][0]})" for i in misses(ks)]) for sc, ks in r[:3]]
print(f"{len(L)} sixes pass; current rank {rk}, score {cs:.4f}, misses {[C.FOES[i][1]['name'] for i in misses(ck)]}")
for t in top: print(f"  {t['pct']}%  {t['team']}  misses {t['misses']}")
print(json.dumps(dict(rank=rk, of=len(L), gap=round((r[0][0] / cs - 1) * 100, 2) if r else None, top=top,
                      current_misses=[C.FOES[i][1]['name'] for i in misses(ck)])))
