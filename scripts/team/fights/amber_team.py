"""Amber (Concert Venue) per the fight protocol. Scores every owned mon x ability with its full legal moveset at Hype 1
and Hype 4 using the game code's variable-power rules (Battle_MoveEffects / Rejuv MoveEffects): Fever Pitch 40 / 130
(+ sound 1.5x), Reversal 200 at Hype 4, Magnitude 10 / 150, rolls 0.85 / 1.0, our Stomping Tantrum 1.5x at Hype 1-2.
Item/ability rules from the game data: Camerupt Focus Sash, Air Balloon (Blaziken, Toxtricity: Ground 0 until hit),
Passho Berry (Skeledirge: first Water hit halved), Flash Fire / Soundproof / Ghost immunities, Unaware ignores boosts.
Writes team/amber_team.json; prints the best sixes (weighted 60% Hype 4, 40% Hype 1)."""
import json, pickle, sys, itertools, os, copy
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, os.path.join(HERE, '..', '..'))
from engine import Engine
E = Engine('.'); D = E.D
b = [b for b in E.battles if b['key'] == 'amber'][0]; FO = b['foes']
st = json.load(open('team/state.json')); C = pickle.load(open(f"team/r{st['run']}_native.json.pkl", 'rb'))['cands']
SKIP = {'SOLARBEAM','SOLARBLADE','SKYATTACK','DIG','FLY','BOUNCE','DIVE','SKULLBASH','METEORBEAM','HYPERBEAM','GIGAIMPACT','FOCUSPUNCH',
        'FUTURESIGHT','DOOMDESIRE','FINALGAMBIT','LASTRESORT','DREAMEATER','BELCH','STEELBEAM','MINDBLOWN','OUTRAGE','PETALDANCE','THRASH',
        'RAGINGFURY','FIRSTIMPRESSION','SNORE','SPITUP','COUNTER','MIRRORCOAT','METALBURST','BIDE','ENDEAVOR','FLING','NATURALGIFT',
        'SYNCHRONOISE','ROLLOUT','ICEBALL','UPROAR','SHELLTRAP','BEAKBLAST','RAZORWIND','EXPLOSION','SELFDESTRUCT','FAKEOUT'}
SOUND = {'FEVERPITCH','HYPERVOICE','TORCHSONG','ALLURINGVOICE','BOOMBURST','BUGBUZZ','SNARL','ROUND','ECHOEDVOICE','DISARMINGVOICE',
         'SPARKLINGARIA','CLANGINGSCALES','RELICSONG','OVERDRIVE','CHATTER','DRUMBEATING','SHADOWPANIC','SPECTRALSCREAM'}
VAR = {1: {'FEVERPITCH': 40, 'MAGNITUDE': 10, 'REVERSAL': 80}, 4: {'FEVERPITCH': 130, 'MAGNITUDE': 150, 'REVERSAL': 200}}
ROLL = {1: 0.85 / 0.925, 4: 1.0 / 0.925}
def foe_moves(f):
    m = f['moves']; return [x for x, _ in m] if m and isinstance(m[0], (list, tuple)) else list(m)
def immune(def_ab, def_types, mtype, mid, mine_attacking, foe):
    if mtype == 'FIRE' and def_ab == 'FLASHFIRE': return True
    if mid in SOUND and def_ab == 'SOUNDPROOF': return True
    if mtype == 'GROUND' and (def_ab == 'LEVITATE' or (not mine_attacking and False)): return True
    if mine_attacking and mtype == 'GROUND' and foe['name'] in ('Blaziken', 'Toxtricity'): return 'balloon'
    return False
def dmg(att, dfn, mid, hype, mine, foe):
    mv = dict(D.moves[mid])
    if mid in VAR[hype]: mv['Strength'] = str(VAR[hype][mid])
    d = E.damage_pct(att, dfn, mid, mv, b, mine)
    if mid in SOUND and not (b.get('field') and False): pass   # engine already applies the field's sound 1.5x (bosses FIELD 'sound')
    d *= ROLL[hype]
    if mine and mid in ('STOMPINGTANTRUM',) and hype == 1: d *= 1.0   # engine applies the Concert damageMods map already
    ab = dfn.get('ability'); im = immune(ab, dfn['types'], D.moves[mid]['Type'], mid, mine, foe)
    if im is True: return 0.0
    if im == 'balloon': d *= 0.5                                     # pops the balloon: credit half
    if mine and foe['name'] == 'Camerupt' and not mid in ('BONERUSH','PINMISSILE','BULLETSEED','ROCKBLAST','ICICLESPEAR','SCALESHOT','TAILSLAP','WATERSHURIKEN','MUDBARRAGE','DOUBLEKICK','DUALCHOP','DOUBLEHIT','TRIPLEAXEL','SURGINGSTRIKES'):
        d = min(d, 99)                                               # Focus Sash
    if mine and foe['name'] == 'Skeledirge' and D.moves[mid]['Type'] == 'WATER': d *= 0.5
    return min(d, 130)
best = {}
for c in sorted(C, key=lambda c: -c.get('solo_total', 0)):
    if c['gate']: continue
    k = (c['name'], c['ability'])
    if k in best: continue
    best[k] = c
rows = []
for (n, ab), c in best.items():
    cat = 'Physical' if c['stats']['Atk'] >= c['stats']['SpA'] else 'Special'
    L = [m for m in E.legal_moves(c['sid'], c['form'], c['src'].get('moves', [])) if m not in SKIP and D.moves[m]['Category'] == cat and int(D.moves[m].get('Strength') or 0) > 1]
    if not L: continue
    res = {}
    for hype in (1, 4):
        tab = {m: np.array([dmg(c, f, m, hype, True, f) for f in FO]) for m in L}
        top = sorted(tab, key=lambda m: -tab[m].sum())[:9]
        ms = max(itertools.combinations(top, min(3, len(top))), key=lambda ms: np.max([tab[m] for m in ms], axis=0).sum())
        cov = np.max([tab[m] for m in ms], axis=0)
        me_def = dict(c, ability=c['ability'])
        taken = np.array([max([dmg(f, c, m, hype, False, f) * (0 if immune(c['ability'], c['types'], D.moves[m]['Type'], m, False, f) is True else 1)
                               for m in foe_moves(f) if D.moves[m]['Category'] != 'Status'] + [0]) for f in FO])
        fast = np.array([c['stats']['Spe'] > f['stats']['Spe'] for f in FO])
        q = np.minimum(cov, 120) / 100 * np.where(fast, 1.15, 1) * (1 - np.minimum(taken, 100) / 200)
        q = np.where((taken >= 100) & ~(fast & (cov >= 100)), q * .5, q)
        res[hype] = (ms, cov, taken, q)
    rows.append(dict(name=n, ab=ab, types=c['types'], spe=c['stats']['Spe'], where=c['src']['where'], dump=c['src'].get('dump'),
                     moves4=[D.moves[m]['MoveName'] for m in res[4][0]], moves1=[D.moves[m]['MoveName'] for m in res[1][0]],
                     cov4=res[4][1].round().tolist(), taken4=res[4][2].round().tolist(), cov1=res[1][1].round().tolist(), taken1=res[1][2].round().tolist(),
                     q=(0.6 * res[4][3] + 0.4 * res[1][3]).tolist()))
by = {}
for r in rows:
    if r['name'] not in by or sum(r['q']) > sum(by[r['name']]['q']): by[r['name']] = r
P = sorted(by.values(), key=lambda r: -sum(r['q']))[:30]
Q = np.array([r['q'] for r in P])
def sc(ix):
    q = np.sort(Q[list(ix)], axis=0); return float((q[-1] + .35 * q[-2]).mean())
res = sorted(((sc(ix), ix) for ix in itertools.combinations(range(len(P)), 6)), reverse=True)
json.dump(dict(foes=[f['name'] for f in FO], rows=P, top=[[s, [P[i]['name'] for i in ix]] for s, ix in res[:20]]), open('team/amber_team.json', 'w'))
print('solo top 15:')
for r in P[:15]: print(f"  {sum(r['q'])/6:.3f} {r['name'][:22]:22s} {r['ab'][:11]:11s} spe{r['spe']} H4 {r['moves4']} dealt{[int(x) for x in r['cov4']]} took{[int(x) for x in r['taken4']]} | H1 took{[int(x) for x in r['taken1']]} {r['where']}#{r['dump']}")
print('best sixes:')
for s, ix in res[:6]: print(round(s, 4), [P[i]['name'] for i in ix])
