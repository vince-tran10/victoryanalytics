"""Core of 4 judged SEPARATELY in singles and in doubles (Vincent, 22 Nov: 'factor singles and doubles').
Per member: strength in every remaining hard fight forced to Singles and forced to Doubles (engine runs r<run>_Singles / _Doubles),
as a percentile of the box; plus the doubles toolkit of the four (Fake Out, Intimidate, redirection, speed control, spread
damage, Wide Guard / Helping Hand). Candidates: the top cores of every style from cores.py (CORES_FREE) + Vincent's core.
usage (from workspace/): DONE=... CR_RUN=r<run> python3 -I ../scripts/team/core_formats.py"""
import bisect, itertools, json, os, pickle, sys
sys.argv = ['x', '.', '20']
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import chapter_rules as C
st = json.load(open('team/state.json')); run = st['run']
def solo(c):
    tot = tw = 0
    for b in C.HARD:
        rows = c['matchups'].get(b['key']) or []
        if not rows: continue
        n = len(rows); v = sum(r['q'] for r in rows) / n - .35 * sum(r['deff'] >= 100 for r in rows) / n
        w = C.bw(b); tot += v * w; tw += w
    return tot / tw if tw else 0
PCT = {}
for f in ('Singles', 'Doubles'):
    best = {}
    for c in pickle.load(open(f'team/r{run}_{f}.json.pkl', 'rb'))['cands']:
        if c['gate']: continue
        s = solo(c)
        if c['name'] not in best or s > best[c['name']]: best[c['name']] = s
    srt = sorted(best.values())
    PCT[f] = {n: bisect.bisect_left(srt, s) / max(1, len(srt) - 1) for n, s in best.items()}
T = {}
for r in json.load(open('team/tier_all.json'))['rows']: T.setdefault(r['name'], r)
TOOLS = {'Fake Out': {'FAKEOUT'}, 'redirection': {'FOLLOWME', 'RAGEPOWDER'}, 'speed control': {'TAILWIND', 'TRICKROOM', 'ICYWIND', 'ELECTROWEB', 'THUNDERWAVE', 'SCARYFACE'},
         'Wide Guard / Helping Hand': {'WIDEGUARD', 'HELPINGHAND', 'QUICKGUARD'},
         'spread attack': {'EARTHQUAKE', 'ROCKSLIDE', 'HEATWAVE', 'MAKEITRAIN', 'MUDDYWATER', 'DAZZLINGGLEAM', 'HYPERVOICE', 'ICYWIND', 'BLIZZARD',
                           'DISCHARGE', 'SURF', 'BULLDOZE', 'ERUPTION', 'SLUDGEWAVE', 'SNARL', 'BREAKINGSWIPE', 'LAVAPLUME', 'WATERSPOUT'}}
def kit(core):   # what the four actually RUN (state moves for the party, else ideal builds)
    IB = json.load(open('team/ideal_builds.json')) if os.path.exists('team/ideal_builds.json') else {}
    have = set(); ab = set()
    for n in core:
        mv = (st.get('moves') or {}).get(n) or (IB.get(n) or {}).get('moves') or []
        have |= {''.join(ch for ch in m.upper() if ch.isalpha()) for m in mv}
        ab.add(''.join(ch for ch in ((st.get('abilities') or {}).get(n) or (IB.get(n) or {}).get('ability') or T.get(n, {}).get('ability', '')).upper() if ch.isalpha()))
    got = [k for k, v in TOOLS.items() if have & v] + (['Intimidate'] if 'INTIMIDATE' in ab else [])
    return got
def rate(core):
    s = sum(PCT['Singles'].get(n, 0) for n in core) / 4; d = sum(PCT['Doubles'].get(n, 0) for n in core) / 4
    k = kit(core); dk = d * .8 + .2 * min(1, len(k) / 4)
    return s, d, dk, k
if __name__ == '__main__':
    cands = {'YOURS': st['core']}
    if os.path.exists('team/cores_free.json'):
        for k, v in json.load(open('team/cores_free.json')).items():
            for i, c in enumerate(v[:3]): cands[f'{k} #{i + 1}'] = c
    rows = []
    for lab, core in cands.items():
        s, d, dk, k = rate(core); rows.append((min(s, dk), s, d, dk, lab, core, k))
    rows.sort(key=lambda x: -x[0])
    for mn, s, d, dk, lab, core, k in rows:
        print(f"{lab:12s} singles {s:.3f}  doubles {d:.3f}  doubles+kit {dk:.3f}  [{', '.join(x.split(' (')[0] for x in core)}]  kit: {', '.join(k)}")
