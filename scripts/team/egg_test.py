import os, sys, json, pickle, copy
sys.path.insert(0, 'scripts/team'); sys.path.insert(0, 'scripts')
os.environ.setdefault('MOVE_RULES', 'ch7'); os.environ['FORCE_FORMAT'] = 'native'
from engine import Engine
import recommend
E = Engine('.')
D = E.D
W2, WF, WS = 0.35, 0.35, 0.03
SUPPORT = {'speed': ['ICYWIND','ELECTROWEB','TAILWIND','THUNDERWAVE','STICKYWEB','SCARYFACE','BULLDOZE','ROCKTOMB'],
           'redirect': ['FOLLOWME','RAGEPOWDER'], 'fakeout': ['FAKEOUT'], 'sleep': ['SPORE','SLEEPPOWDER','SING','HYPNOSIS','YAWN','LOVELYKISS','GRASSWHISTLE'],
           'burn': ['WILLOWISP'], 'helping': ['HELPINGHAND'], 'guard': ['WIDEGUARD','QUICKGUARD'], 'screens': ['REFLECT','LIGHTSCREEN','AURORAVEIL']}
def tags(m):
    t = {k for k, mv in SUPPORT.items() if any(x in m['legal'] for x in mv)}
    if m['ability'] == 'INTIMIDATE': t.add('intimidate')
    return t
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

d = pickle.load(open('team/r10_native.json.pkl', 'rb'))
def get(n):
    xs = [c for c in d['cands'] if c['name'] == n and not c.get('ability_changed')]
    return max(xs, key=lambda c: c['solo_total'])
six = [get(n) for n in ['Annihilape','Gholdengo','Rhyperior','Glaceon','Golisopod (Aevian Form)','Leavanny (Aevian Form)']]
for m in six: m['tags'] = m.get('tags') or tags(m)
base = tscore(six)

pool = ['AZURILL','IMPIDIMP','NACLI','TOGEPI','SNEASEL','DHELMISE',('LITWICK','Aevian'),'AXEW','MIENFOO','PAWNIARD','TRAPINCH',
        'HIPPOPOTAS','COTTONEE','DARUMAKA','HATENNA','STARLY','TYRUNT','LARVESTA','MAREANIE','STUFFUL','ROOKIDEE']
out = []
for p in pool:
    sid, tag = (p, '') if isinstance(p, str) else p
    form = '0'
    if tag:
        form = next(k for k in D.sp[sid] if k.isdigit() and tag in (D.sp[sid][k].get('FormName') or ''))
    best = None
    f0 = D.form(sid, form)
    abil0 = list(f0.get('Abilities') or [])
    for ai in range(max(1, len(abil0))):
        mon = dict(name=D.nm(sid), sid=sid, form=form, level=55, moves=[], ability=D.nm(abil0[ai]) if abil0 else '', where='Egg', dump=0, raw=D.nm(sid))
        me = E.build_me(mon)
        me['ability'] = me['abilities'][min(ai, len(me['abilities']) - 1)] if me['abilities'] else ''
        E.evaluate(me)
        atk = E.pick_moves(me, 3)
        me['attacks'] = atk
        E.evaluate(me, moveset=set(atk))
        me['tags'] = tags(me)
        me['src'] = mon
        solo = tscore([me])
        # best swap into the six
        swaps = sorted(((tscore(six[:i] + [me] + six[i+1:]) - base, six[i]['name']) for i in range(6)), reverse=True)
        r = dict(egg=D.nm(sid) + (' (Aevian)' if tag else ''), final=me['name'], ability=D.nm(me['ability']), types='/'.join(t.capitalize() for t in me['types']),
                 evo=me['evo'], gate=me.get('gate', ''), solo=round(solo, 3), swap_gain=round(swaps[0][0], 3), swap_for=swaps[0][1],
                 attacks=[D.moves[x]['MoveName'] for x in atk], best=sorted(me['solo'] if 'solo' in me else {}, key=lambda k: 0)[:0],
                 per={b['key']: round(bscore([me], b), 2) for b in E.battles}, bst=sum(me['base'].values()))
        if best is None or r['solo'] > best['solo']:
            best = r
    out.append(best)
out.sort(key=lambda r: -r['solo'])
def tier(s):
    return 'S' if s >= .70 else 'A' if s >= .58 else 'B' if s >= .50 else 'C' if s >= .40 else 'D'
for r in out:
    top = sorted(r['per'], key=r['per'].get, reverse=True)[:2]
    print(f"{tier(r['solo'])} {r['solo']:.3f} swap{r['swap_gain']:+.3f} ({r['swap_for'][:12]}) | {r['egg']:16s} -> {r['final']:22s} {r['ability']:14s} {r['types']:15s} BST{r['bst']} | {r['attacks']} | best {top} | evo: {r['evo'][:60]} {('GATED '+r['gate']) if r['gate'] else ''}")
json.dump(out, open('team/egg_test.json', 'w'), indent=1)
