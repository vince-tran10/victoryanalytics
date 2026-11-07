"""Kyogre hard counter, debug mode: every owned mon, every evo branch / ability / spread / item; sum damage dealt before fainting."""
import sys, os, json, math, itertools
sys.path.insert(0, '/home/user/victoryanalytics/scripts/team'); sys.path.insert(0, '/home/user/victoryanalytics/scripts')
os.environ['FORCE_FORMAT'] = 'native'; os.environ['MOVE_RULES'] = 'relearn'
import engine
from engine import Engine, calc_stats
E = Engine('.'); D = E.D
b = [b for b in E.battles if b['key'] == 'kyogre'][0]; K = b['foes'][0]
KM = [(m, v) for m, v in (K['moves'] if isinstance(K['moves'], list) else eval(K['moves'])) if v['Category'] != 'Status']
KHP = K['stats']['HP'] * K.get('hp_mult', 1)
R = json.load(open('team/roster11_lv55.json'))
RECOIL = {'VOLTTACKLE': 1/3, 'WOODHAMMER': 1/3, 'WILDCHARGE': .25, 'FLAREBLITZ': 1/3, 'BRAVEBIRD': 1/3, 'DOUBLEEDGE': 1/3,
          'HEADSMASH': .5, 'WAVECRASH': 1/3, 'TAKEDOWN': .25, 'SUBMISSION': .25, 'HEADLONGRUSH': 0, 'CHLOROBLAST': None}
DROP = {'LEAFSTORM', 'OVERHEAT', 'DRACOMETEOR', 'FLEURCANNON', 'PSYCHOBOOST'}
SKIP = {'SOLARBEAM', 'SOLARBLADE', 'SKYATTACK', 'DIG', 'FLY', 'BOUNCE', 'DIVE', 'SKULLBASH', 'METEORBEAM', 'HYPERBEAM', 'GIGAIMPACT',
        'FOCUSPUNCH', 'FUTURESIGHT', 'DOOMDESIRE', 'EXPLOSION', 'SELFDESTRUCT', 'MISTYEXPLOSION', 'FINALGAMBIT', 'LASTRESORT', 'DREAMEATER', 'BELCH', 'STEELBEAM', 'MINDBLOWN'}
BOOST = {'FIGHTING': 'Black Belt', 'STEEL': 'Metal Coat', 'WATER': 'Mystic Water', 'GROUND': 'Soft Sand', 'ROCK': 'Hard Stone',
         'ICE': 'Never-Melt Ice', 'DARK': 'Black Glasses', 'POISON': 'Poison Barb', 'ELECTRIC': 'Magnet', 'FAIRY': 'Fairy Feather', 'DRAGON': 'Dragon Fang'}
def sim(me, spe, mvs, maxd, item):
    faster = spe > K['stats']['Spe']
    best = (0, None, 0)
    for dmg, mid, name, typ in mvs[:6]:
        mult = 1.2 if item == BOOST.get(typ) else 1.0
        hp, tot, n, ate = 100.0, 0.0, 0, False
        for t in range(12):
            def hit():
                nonlocal hp, ate
                if hp >= 100 and item == 'Focus Sash' and maxd >= 100: hp = 1
                else: hp -= maxd
                if item == 'Sitrus Berry' and 0 < hp <= 50 and not ate: hp += 25; ate = True
            if not faster:
                hit()
                if hp <= 0: break
            d = dmg * mult * (0.6 ** n if mid in DROP else 1); tot += d; n += 1
            if mid in RECOIL and RECOIL[mid]: hp -= d / 100 * KHP * RECOIL[mid] / me['stats']['HP'] * 100
            if mid == 'CHLOROBLAST': hp -= 50
            if hp <= 0: break
            if faster:
                hit()
                if hp <= 0: break
        if tot > best[0]: best = (tot, name, n)
    return best
SPREADS = {'Physical': [('Adamant', {'Atk': 252, 'HP': 252, 'SpD': 4}), ('Jolly', {'Atk': 252, 'Spe': 252, 'HP': 4}), ('Adamant', {'Atk': 252, 'Spe': 252, 'HP': 4})],
           'Special': [('Modest', {'SpA': 252, 'HP': 252, 'SpD': 4}), ('Timid', {'SpA': 252, 'Spe': 252, 'HP': 4}), ('Modest', {'SpA': 252, 'Spe': 252, 'HP': 4})]}
res = {}
for m in R:
    for br in range(3):
        try: base = E.build_me(m, branch=br)
        except Exception: continue
        if base is None or base.get('gate'): continue
        for ab in set(base['abilities']) or {base['ability']}:
            me = E.build_me(m, branch=br, ability_override=ab)
            if me['sid'] != base['sid']: continue
            for cat, spreads in SPREADS.items():
                for nat, evs in spreads:
                    me['stats'] = calc_stats(me['base'], evs, nat); me['nature'], me['evs'] = nat, evs
                    mvs = []
                    for mid in me['legal']:
                        mv = D.moves.get(mid)
                        if not mv or mv['Category'] != cat or int(mv.get('Strength') or 0) <= 1 or mid in SKIP or mid in engine.EXCLUDE: continue
                        dmg = E.damage_pct(me, K, mid, mv, b, True) * (0.85 if cat == 'Special' else 1)   # Calm Mind tax
                        mvs.append((dmg, mid, mv['MoveName'], mv['Type']))
                    if not mvs: continue
                    mvs.sort(reverse=True)
                    maxd = max(E.damage_pct(K, me, mid, mv, b, False) for mid, mv in KM)
                    spe = me['stats']['Spe'] * (2 if ab == 'SWIFTSWIM' else 1)
                    for item in ['Focus Sash', 'Sitrus Berry'] + sorted(set(BOOST.values())):
                        tot, mvname, n = sim(me, spe, mvs, maxd, item)
                        key = (m['dump'])
                        if key not in res or tot > res[key][0]:
                            res[key] = (tot, dict(dump=m['dump'], name=me['name'], owned=m['name'], lv=m['level'], ability=ab, nature=nat, evs=evs,
                                                  item=item, move=mvname, hits=n, spe=spe, faster=spe > K['stats']['Spe'], takes=round(maxd),
                                                  moves=[x[2] for x in mvs[:3]], types=me['types'], where=m['dump']))
rows = sorted(res.values(), key=lambda x: -x[0])
seen = set(); top = []
for tot, d in rows:
    if d['name'] in seen: continue
    seen.add(d['name']); top.append((tot, d))
for tot, d in top[:25]:
    print(f"{tot:5.0f}%  #{d['dump']} {d['name']:28s} [{d['ability']}] {d['nature']} {d['evs']} @ {d['item']} | {d['move']} x{d['hits']} | Spe {d['spe']} {'>' if d['faster'] else '<'} 144 | takes {d['takes']}% | {'/'.join(d['types'])} | owned as {d['owned']} L{d['lv']}")
json.dump([[t, d] for t, d in top[:40]], open('team/kyogre_counter.json', 'w'), indent=1)
