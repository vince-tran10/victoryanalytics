"""Crest tier list: every owned crest-eligible Pokémon scored on the hard fights with and without its crest.
usage (from workspace/): DONE=... CR_RUN=<crest run, e.g. rc1> BASE_RUN=<normal run, e.g. r40> python3 -I ../scripts/team/crest_tier.py"""
import sys, os, json, pickle
sys.argv = ['x', '.', '20']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chapter_rules as C, crests
HARD = C.HARD
def load(run): return pickle.load(open(f'team/{run}_native.json.pkl', 'rb'))['cands']
def solo(c):
    tot = tw = 0
    for b in HARD:
        rows = c['matchups'][b['key']]; n = len(rows)
        v = sum(r['q'] for r in rows) / n - .35 * sum(r['deff'] >= 100 for r in rows) / n
        w = C.bw(b); tot += v * w; tw += w
    return tot / tw
def best_by_name(cands, crested=None):
    out = {}
    for c in cands:
        if c['gate']: continue
        if crested is not None and bool(c.get('crest')) != crested: continue
        if c['name'] not in out or solo(c) > solo(out[c['name']]): out[c['name']] = c
    return out
with_c = best_by_name(load(os.environ['CREST_RUN']), True)
without = best_by_name(load(os.environ['BASE_RUN']))
team = json.load(open('team/state.json'))['team']
anchor = sorted(solo(without[n]) for n in team if n in without)
held = set()
import current_box as cb
N = cb.parse(os.path.join('.', json.load(open('team/state.json'))['export']))
held = {d['item'] for d in N if d.get('item') and 'Crest' in d['item']}
I = json.load(open('gamedata/itemtext.json'))
rows = []
for n, c in with_c.items():
    b = without.get(n)
    s1, s0 = solo(c), solo(b) if b else 0
    cname = I.get(crests.CREST_OF.get(c['sid'], ''), {}).get('name', '')
    rows.append(dict(name=n, crest=cname, held=cname in held, where=c['src']['where'], dump=c['src'].get('dump'),
                     with_crest=round(s1, 3), without=round(s0, 3), gain=round(s1 - s0, 3), attacks=[C.D.moves[m]['MoveName'] for m in c['attacks']],
                     ability=c['ability']))
rows.sort(key=lambda r: -r['with_crest'])
lo, med = anchor[0], anchor[len(anchor) // 2]
for r in rows:
    r['tier'] = 'S' if r['with_crest'] >= med else 'A' if r['with_crest'] >= lo else 'B' if r['with_crest'] >= lo * 0.85 else 'C' if r['gain'] >= 0.02 else 'D'
json.dump(dict(anchor_low=round(lo, 3), anchor_median=round(med, 3), team={n: round(solo(without[n]), 3) for n in team if n in without}, rows=rows),
          open('team/crest_tier.json', 'w'), indent=1)
print('your six (no crest):', {n: round(solo(without[n]), 3) for n in team if n in without})
for r in rows:
    print(f"{r['tier']} {r['with_crest']:.3f} (no crest {r['without']:.3f}, {r['gain']:+.3f}) {r['name']:30s} {r['crest']:20s} {'HELD' if r['held'] else ''} {r['where']} {r['attacks']}")
