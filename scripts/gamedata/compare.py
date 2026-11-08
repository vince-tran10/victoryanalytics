"""Compare the engine's current fight data (walkthrough) with the game's own data. Prints every difference.
usage (from workspace/): DONE=... python3 -I ../scripts/gamedata/compare.py [json_out]"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'team'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('FORCE_FORMAT', 'native')
import gamedata as G
from engine import Engine
E = Engine('.')
norm = lambda s: re.sub(r'[^a-z0-9]', '', (s or '').lower())
report = {}
for key in G.FIGHTS:
    b = next((b for b in E.battles if b['key'] == key), None)
    game = G.fight_mons(key)
    rows = []
    if not b:
        report[key] = {'note': 'not in engine (beaten or not tracked)'}; continue
    eng = list(b['foes'])
    used = set()
    for g in game:
        cand = [i for i, f in enumerate(eng) if i not in used and norm(f['name']) == norm(g['name'])]
        if not cand:
            rows.append(dict(mon=g['name'], diff=['MISSING in guide data'])); continue
        i = cand[0]; used.add(i); f = eng[i]; raw = f['raw']; d = []
        if int(f['level']) != int(g['level']): d.append(f"level {f['level']} → {g['level']}")
        if norm(f['item']) != norm(g['item']): d.append(f"item {f['item'] or '-'} → {g['item'] or '-'}")
        if norm(raw.get('ability')) != norm(g['ability']): d.append(f"ability {raw.get('ability') or '-'} → {g['ability']}")
        if norm(raw.get('nature')) != norm(g['nature']): d.append(f"nature {raw.get('nature') or '-'} → {g['nature']}")
        em = sorted(norm(m[1]['MoveName']) for m in f['moves']); gm = sorted(norm(re.sub(r' \(.*\)$', '', m)) for m in g['moves'])
        if em != gm: d.append(f"moves {[m[1]['MoveName'] for m in f['moves']]} → {g['moves']}")
        ft = sorted(t.upper() for t in f['types']); gt = sorted(g['types'])
        if ft != gt: d.append(f"types {'/'.join(f['types'])} → {'/'.join(g['types'])}")
        ev = [int(x) for x in (raw.get('evs') or '').split(';')] if raw.get('evs') else None
        if ev and ev != list(g['ev']): d.append(f"EVs {ev} → {g['ev']}")
        if g['shields']:
            hm = round(f.get('hp_mult', 1), 2)
            d.append(f"BOSS {g['shields']} shields (guide HP x{hm}); phases: " + '; '.join(
                f"at {k} shield(s): " + ', '.join(x for x in [v.get('message', '')[:60], ('moves → ' + '/'.join(G.move_name(m) for m in v['movesetUpdate'])) if v.get('movesetUpdate') else '',
                ('field → ' + v['fieldChange']) if v.get('fieldChange') else '', ('form ' + str(v['formchange'])) if v.get('formchange') else '',
                ('boss stats ' + str({G.STAT_IDX.get(int(s), s): c for s, c in v['bossStatChanges'].items()})) if v.get('bossStatChanges') else '',
                ('your side ' + str({G.STAT_IDX.get(int(s), s): c for s, c in v['playerSideStatChanges'].items()})) if v.get('playerSideStatChanges') else ''] if x)
                for k, v in sorted(g['phases'].items(), key=lambda kv: -int(kv[0]))))
        if g.get('sos'): d.append('calls SOS: ' + ', '.join(f"{G.mon(m['species'])['name']} Lv{m['level']}" for m in g['sos']['moninfos'].values()))
        rows.append(dict(mon=g['name'], diff=d))
    for i, f in enumerate(eng):
        if i not in used: rows.append(dict(mon=f['name'], diff=['EXTRA in guide data (not in the game entry)']))
    report[key] = dict(label=b['label'], game_src=sorted({g['src'] for g in game}), n_game=len(game), n_guide=len(eng), rows=rows)
for key, r in report.items():
    print(f"\n=== {key}: {r.get('label', '')}  game {r.get('n_game')} mons / guide {r.get('n_guide')} mons  {r.get('game_src', r.get('note'))}")
    for row in r.get('rows', []):
        print(f"  {row['mon']:14s} {'OK' if not row['diff'] else ' | '.join(row['diff'])}")
if len(sys.argv) > 1: json.dump(report, open(sys.argv[1], 'w'), indent=1, ensure_ascii=False)
