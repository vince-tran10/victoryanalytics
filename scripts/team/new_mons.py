"""Standing check for a new export: what's new, does it earn an Active-box spot, and its ideal Lv 55 build.

usage: python3 new_mons.py BASE old_roster.json new_roster.json out.json
Move rules: MOVE_RULES=ch7_notutor (Ch1-7 TMs + level-up <= 55 + Egg + known moves).
"""
import json, os, sys, collections
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('MOVE_RULES', 'ch7_notutor'); os.environ.setdefault('FORCE_FORMAT', 'native')
from engine import Engine
from recommend import EXCLUDE

BASE, OLD, NEW, OUT = sys.argv[1:5]
E = Engine(BASE); D = E.D
W2, WF, WS = 0.35, 0.35, 0.03
SUPPORT = {'speed': ['ICYWIND', 'ELECTROWEB', 'TAILWIND', 'THUNDERWAVE', 'STICKYWEB', 'SCARYFACE', 'BULLDOZE', 'ROCKTOMB'],
           'redirect': ['FOLLOWME', 'RAGEPOWDER'], 'fakeout': ['FAKEOUT'],
           'sleep': ['SPORE', 'SLEEPPOWDER', 'SING', 'HYPNOSIS', 'YAWN', 'LOVELYKISS', 'GRASSWHISTLE'],
           'burn': ['WILLOWISP'], 'helping': ['HELPINGHAND'], 'guard': ['WIDEGUARD', 'QUICKGUARD'],
           'screens': ['REFLECT', 'LIGHTSCREEN', 'AURORAVEIL']}
SETUP_P = ['SHELLSMASH', 'DRAGONDANCE', 'SWORDSDANCE', 'BULKUP', 'SHIFTGEAR', 'COIL', 'HONECLAWS', 'WORKUP', 'CURSE']
SETUP_S = ['SHELLSMASH', 'QUIVERDANCE', 'NASTYPLOT', 'CALMMIND', 'WORKUP']
UTIL = ['FAKEOUT', 'WIDEGUARD', 'RAGEPOWDER', 'FOLLOWME', 'WILLOWISP', 'ICYWIND', 'ELECTROWEB', 'TAILWIND', 'HELPINGHAND',
        'SPORE', 'SLEEPPOWDER', 'YAWN', 'THUNDERWAVE', 'KNOCKOFF', 'RECOVER', 'ROOST', 'SLACKOFF', 'SYNTHESIS', 'WISH']


def tags(m):
    t = {k for k, mv in SUPPORT.items() if any(x in m['legal'] for x in mv)}
    if m['ability'] == 'INTIMIDATE':
        t.add('intimidate')
    return t


def bscore(team, b):
    foes = b['foes']; tot = 0
    for i in range(len(foes)):
        qs = sorted((m['matchups'][b['key']][i]['q'] for m in team), reverse=True)
        tot += qs[0] + W2 * (qs[1] if len(qs) > 1 else 0)
    frag = sum(sum(1 for r in m['matchups'][b['key']] if r['deff'] >= 100) / len(foes) for m in team) / len(team)
    sup = set()
    if b['format'] == 'Doubles':
        for m in team:
            sup |= m['tags']
    return tot / len(foes) - WF * frag + WS * len(sup)


def tscore(team):
    return sum(bscore(team, b) * b['weight'] for b in E.battles) / sum(b['weight'] for b in E.battles)


def tier(s):
    return 'S' if s >= .70 else 'A' if s >= .58 else 'B' if s >= .50 else 'C' if s >= .40 else 'D'


def key(m):
    return (m['name'], m.get('gender'), m.get('nickname'))


old = json.load(open(OLD)); new = json.load(open(NEW))
oc = collections.Counter(key(m) for m in old)
added = []
for m in new:
    k = key(m)
    if oc[k] > 0:
        oc[k] -= 1
    else:
        added.append(m)

res = []
for m in added:
    best = None
    sid, form = m['sid'], m['form']
    f0 = D.form(sid, form)
    regs = list(dict.fromkeys(f0.get('Abilities') or []))
    cur_ab = (m.get('ability') or '').upper().replace(' ', '').replace('-', '').replace("'", '')
    options = list(dict.fromkeys([cur_ab] + regs))
    for ab in options:
        me = E.build_me(m, ability_override=ab if ab != cur_ab else None)
        E.evaluate(me)
        atk = E.pick_moves(me, 3)
        me['attacks'] = atk
        E.evaluate(me, moveset=set(atk))
        me['tags'] = tags(me)
        s = tscore([me])
        if best is None or s > best[0]:
            best = (s, me, ab != cur_ab and ab not in ('',))
    s, me, capsule = best
    # moveset: 3 attacks (top up to 3 from the ranked pool) + setup/utility or 4th attack, then Protect if learnable
    legal = me['legal']
    atk = list(me['attacks'])
    def tot(x):
        return sum(min(E.damage_pct(me, fo, x, D.moves[x], b, True), 100) for b in E.battles for fo in b['foes'])
    pool = sorted((x for x in legal if x in D.moves and D.moves[x]['Category'] != 'Status' and x not in EXCLUDE
                   and D.moves[x]['Type'] not in ('SHADOW', 'QMARKS') and x not in atk), key=lambda x: -tot(x))
    lock = {'OUTRAGE', 'PETALDANCE', 'THRASH', 'RAGINGFURY'}
    for x in pool:
        if len(atk) >= 3:
            break
        if x in lock and lock & set(atk):
            continue
        if int(D.moves[x].get('Strength') or 0) < 50 and int(D.moves[x].get('Priority') or 0) <= 0:
            continue
        atk.append(x)
    setup = next((x for x in (SETUP_P if me['cat'] == 'Physical' else SETUP_S) if x in legal), None)
    util = next((x for x in UTIL if x in legal), None)
    moves = [D.moves[x]['MoveName'] for x in atk[:3]]
    fourth = setup or util
    protect = 'PROTECT' in {mid for mid, meth, d in D.learnset(me['sid'], me['form'])}
    if fourth and protect:
        moves = moves[:2] + [D.moves[fourth]['MoveName']] if len(moves) >= 3 and tot(atk[2]) < 0.6 * tot(atk[0]) else moves
        moves = (moves + [D.moves[fourth]['MoveName']])[:3] if D.moves[fourth]['MoveName'] not in moves and len(moves) < 3 else moves
        moves.append('Protect')
    elif protect:
        moves.append('Protect')
    elif fourth:
        moves.append(D.moves[fourth]['MoveName'])
    moves = list(dict.fromkeys(moves))[:4]
    # where each move comes from
    src = {}
    known = {E.move_id(x) for x in m.get('moves', [])}
    ls = D.learnset(me['sid'], me['form'])
    for mvn in moves:
        mid = E.move_id(mvn)
        how = [f"Lv {d}" if meth == 'Level-up' and d != 'Evo' else ('evolution' if meth == 'Level-up' else (d if meth == 'TM' else meth))
               for x, meth, d in ls if x == mid and (meth in ('Level-up', 'Egg') or (meth == 'TM' and d in E.allowed_tms))]
        src[mvn] = 'known' if mid in known else (how[0] if how else 'known')
    # does it make the box? compare with the current Active-box median
    res.append(dict(dump=m['dump'], owned=m['name'], level=m.get('level'), now_ability=m.get('ability'), now_moves=m.get('moves'),
                    final=me['name'], evolve=me['evo'], gate=me.get('gate', ''), types='/'.join(t.capitalize() for t in me['types']),
                    score=round(s, 3), tier=tier(s), ability=D.nm(me['ability']), capsule=capsule, nature=me['nature'],
                    evs=me['evs'], moves=moves, move_src=src,
                    best=sorted(me['solo'] if 'solo' in me else {b['key']: bscore([me], b) for b in E.battles}, key=lambda k: 0)[:0],
                    per={b['key']: round(bscore([me], b), 2) for b in E.battles}))
json.dump(res, open(OUT, 'w'), indent=1, ensure_ascii=False)
for r in sorted(res, key=lambda r: -r['score']):
    top = sorted(r['per'], key=r['per'].get, reverse=True)[:2]
    print(f"{r['tier']} {r['score']:.3f} {r['owned']} -> {r['final']} [{r['types']}] Lv{r['level']} | {r['ability']}{' (capsule)' if r['capsule'] else ''} | {r['nature']} {r['evs']} | {r['moves']} | {r['move_src']} | best {top} | evo {r['evolve']} {r['gate']}")
