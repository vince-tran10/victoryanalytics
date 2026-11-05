"""Per party/Active mon: current moves, engine best attacks (MOVE_RULES=relearn), relearner-only and skipped level-up moves."""
import sys, os, json, pickle
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from engine import Engine
BASE, ROSTER, PKL, START = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
E = Engine(BASE); D = E.D
P = pickle.load(open(PKL, 'rb'))
STATUS_OK = {'Swords Dance', 'Nasty Plot', 'Bulk Up', 'Dragon Dance', 'Calm Mind', 'Quiver Dance', 'Shell Smash', 'Belly Drum', 'Coil',
             'Shift Gear', 'Rock Polish', 'Agility', 'Trick Room', 'Tailwind', 'Recover', 'Roost', 'Slack Off', 'Spore', 'Sleep Powder',
             'Will-O-Wisp', 'Fake Out', 'Follow Me', 'Rage Powder', 'Wide Guard', 'Sticky Web', 'Strength Sap', 'Moonlight', 'Synthesis',
             'Wish', 'Yawn', 'Thunder Wave', 'Haze', 'Curse', 'Work Up', 'Hone Claws', 'Iron Defense', 'Amnesia', 'Cosmic Power', 'Leech Seed',
             'Encore', 'Taunt', 'Helping Hand', 'Aurora Veil', 'Reflect', 'Light Screen', 'Teeter Dance', 'Psych Up', 'Stealth Rock',
             'Victory Dance', 'Tidy Up', 'Quiver Dance', 'Growth', 'Shore Up', 'Milk Drink', 'Soft-Boiled', 'Slack Off', 'Lunar Blessing'}
out = []
for m in json.load(open(ROSTER)):
    if not (m['dump'] <= 6 or m['dump'] >= START):
        continue
    me = E.build_me(m); lv = m.get('level', 50)
    ls = D.learnset(me['sid'], me['form'])
    known = {E.move_id(x) for x in m.get('moves', [])}
    nm = lambda x: D.moves[x]['MoveName']
    keepm = lambda x: x in D.moves and (D.moves[x]['Category'] != 'Status' or nm(x) in STATUS_OK)
    rel = sorted({nm(x) for x, meth, d in ls if meth == 'Move Relearner' and keepm(x) and x not in known})
    lvl = sorted({(int(d), nm(x)) for x, meth, d in ls if meth == 'Level-up' and d.isdigit() and int(d) <= lv and x not in known and keepm(x)})
    future = sorted({(int(d), nm(x)) for x, meth, d in ls if meth == 'Level-up' and d.isdigit() and lv < int(d) <= 55 and keepm(x)})
    egg = sorted({nm(x) for x, meth, d in ls if meth == 'Egg' and keepm(x)})
    c = next((c for c in P['cands'] if c['src'].get('dump') == m['dump']), None) or \
        next((c for c in P['cands'] if c['sid'] == me['sid'] and c['form'] == me['form']), None)
    out.append(dict(dump=m['dump'], name=m['name'], level=lv, types=me['types'], ability=m.get('ability'), nature=m.get('nature'),
                    item=m.get('item'), now=m.get('moves'), best=[nm(x) for x in c['attacks']] if c else None,
                    score=round(c['solo_total'], 3) if c else None, relearner=rel, skipped=[f'{a}:{b}' for a, b in lvl],
                    future=[f'{a}:{b}' for a, b in future], egg=egg, legal=sorted(nm(x) for x in me['legal'] if x in D.moves)))
json.dump(out, open(sys.argv[5], 'w'), indent=1, ensure_ascii=False)
for o in out:
    print(f"#{o['dump']} {o['name']} Lv{o['level']} [{'/'.join(o['types'])}] {o['ability']} {o['nature']} @{o['item']} now={o['now']} | best={o['best']} {o['score']}")
    print('   relearner-only:', o['relearner']); print('   skipped lv:', o['skipped']); print('   future lv:', o['future']); print('   egg:', o['egg'])
