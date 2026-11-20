"""Bar-by-bar plan for a boss fight (Vincent, 20 Nov): searches the switch-in order of the fight's six, turn by turn.
Uses the fight eval (deal / take per bar, % of one bar / of our HP) plus mechanics the one-hit model misses:
speed order, boss stat stages per bar (Unaware ignores them), Swords Dance / Curse / Recover, Gastro Acid + Knock Off vs
boss healing, Sitrus, drains, field chip (Corrupted Cave 1/8 to grounded non-Poison/Steel), recoil (breaks our Sash),
Focus Sash, Rocky Helmet vs contact, overflow lost at breaks, free switch after a faint, Melia's partner chip.
usage (from workspace/): python3 -I ../scripts/team/fights/bar_plan.py garbodor -> team/bar_plan_garbodor.json"""
import itertools, json, os, sys
KEY = sys.argv[1]
R = json.load(open(f'team/{KEY}_eval.json')); ST = json.load(open('team/state.json'))
SIX = ST['team']
STAGE = lambda s: (2 + s) / 2 if s >= 0 else 2 / (2 - s)
# boss stat stages per bar (gamedata.boss_rows; cumulative bossStatChanges, statDropCure only cures OUR drops)
import importlib.util
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'gamedata'))
import gamedata as G
b = G.boss(next(x for t, x in G.FIGHTS[KEY] if t == 'boss'))
eff = b.get('onBreakEffects', {}); S = b.get('shieldCount', 0)
stg = {'atk': 0, 'def': 0, 'spa': 0, 'spd': 0}; BARS = []
mi = b['moninfo']; types = None; item = mi.get('item'); moves = mi['moves']
IDX = {1: 'atk', 2: 'def', 3: 'spa', 4: 'spd'}
MT = json.load(open('gamedata/montext.json')).get(mi['species'], {})
_forms = list(MT.values()); _f0 = _forms[0] if _forms else {}; _ff = _forms[mi.get('form', 0)] if len(_forms) > mi.get('form', 0) else {}
types = [t for t in [_ff.get('Type1') or _f0.get('Type1'), _ff.get('Type2') or _f0.get('Type2')] if t]
BARS.append(dict(stg=dict(stg), item=item, moves=moves, types=types))
for k in range(S, 0, -1):
    e = eff.get(str(k)) or {}
    for s, c in (e.get('bossStatChanges') or {}).items():
        if int(s) in IDX: stg[IDX[int(s)]] += c
    item = e.get('itemchange') or item; moves = e.get('movesetUpdate') or moves; types = e.get('typeChange') or types
    BARS.append(dict(stg=dict(stg), item=item, moves=moves, types=types))
NB = len(BARS)
FIELD_CHIP = KEY == 'garbodor'           # Corrupted Cave
CONTACT = {'FLAREBLITZ', 'HEADSMASH', 'EXTREMESPEED', 'KNOCKOFF', 'DRAINPUNCH', 'PLAYROUGH', 'IRONHEAD'}
RECOIL = {'FLAREBLITZ': 1 / 3, 'HEADSMASH': .5, 'DOUBLEEDGE': 1 / 3, 'BRAVEBIRD': 1 / 3, 'WOODHAMMER': 1 / 3}
DRAIN = {'DRAINPUNCH', 'GIGADRAIN'}
BOSS_HP = R['foe_hp'][0]; BOSS_SPE = R['foe_spe'][0]
rows = {}
for y in R['rows']:
    if y['name'] in SIX and (y['name'] not in rows or y.get('fixed')): rows[y['name']] = y
mv = {n: set((ST.get('moves') or {}).get(n) or []) for n in SIX}
import re
mid = lambda m: re.sub(r'[^A-Z]', '', m.upper())
MV = {n: {mid(m) for m in mv[n]} for n in SIX}
ABL = {n: re.sub(r'[^A-Z]', '', ((ST.get('abilities') or {}).get(n) or rows[n]['ab']).upper()) for n in SIX}
ITEM = {n: rows[n].get('item') or '' for n in SIX}
items_state = {'Arcanine (Hisuian Form)': 'Focus Sash'}


def mon(n):
    y = rows[n]; t = [x / 1.3 for x in y['taken']]   # eval adds x1.3 for doubles spread; one boss = one target
    d = list(y['cov'])
    if ABL[n] == 'UNAWARE':
        for j, B in enumerate(BARS):
            t[j] /= STAGE(max(B['stg']['atk'], B['stg']['spa'])); d[j] *= STAGE(B['stg']['def'])
    atk_mv = next((m for m in y['mids'] if m in RECOIL), None)
    return dict(n=n, hp=100.0, d=d, t=t, spe=y['spe'], boost=0, curse=0, used_sd=False,
                types=y['types'], grounded=not ({'FLYING'} & set(y['types'])) and ABL[n] != 'LEVITATE',
                recoil=RECOIL.get(atk_mv, 0), contact=bool(set(y['mids']) & CONTACT) and not set(y['mids']) - CONTACT,
                sash=ITEM[n] == 'Focus Sash', maxhp=y['hp'])


PART = R.get('partner') or []
FOCUS_PARTNER = False   # worst case: the boss always hits OUR active Pokémon; Melia's mon only adds chip


def play(order, partner=True, log=None):
    team = [mon(n) for n in order]; ai = 0; me = team[0]
    gastro = knocked = False; sitrus_used = False; pi = 0; part = [dict(p, cur=100.0) for p in PART] if partner else []
    turns = 0
    for j, B in enumerate(BARS):
        bar = 100.0; sitrus = B['item'] == 'SITRUSBERRY'; t_bar = 0
        while bar > 0:
            turns += 1; t_bar += 1
            if turns > 60: return None
            act = 'attack'
            kill_now = me['d'][j] * STAGE(me['boost'] + me['curse']) >= bar and (me['spe'] > BOSS_SPE or me['hp'] > me['t'][j])
            if kill_now: pass
            elif t_bar == 1 and j > 0 and me['hp'] <= me['t'][j] and ai + 1 < len(team): act = 'switch'   # would faint: save it
            elif 'GASTROACID' in MV[me['n']] and not gastro: act = 'Gastro Acid'
            elif 'KNOCKOFF' in MV[me['n']] and B['item'] == 'BLACKSLUDGE' and not knocked and me['d'][j] < 50: act = 'Knock Off'
            elif 'SWORDSDANCE' in MV[me['n']] and not me['used_sd'] and me['hp'] > 1.6 * me['t'][j] and me['d'][j] < 100: act = 'Swords Dance'
            elif 'RECOVER' in MV[me['n']] and me['hp'] <= me['t'][j] + 5 and me['hp'] < 60 and me['t'][j] < 45: act = 'Recover'
            elif 'CURSE' in MV[me['n']] and me['curse'] < 3 and me['hp'] > me['t'][j] + 10 and me['d'][j] * STAGE(me['curse']) < 100: act = 'Curse'
            elif (gastro and bar < 100 and me['d'][j] * STAGE(me['boost']) < 8) and ai + 1 < len(team):
                act = 'switch'
            def ours():
                nonlocal bar, gastro, knocked
                if act == 'Gastro Acid': gastro = True
                elif act == 'Knock Off': knocked = True; bar -= me['d'][j] * 1.5
                elif act == 'Swords Dance': me['boost'] = 2; me['used_sd'] = True
                elif act == 'Curse': me['curse'] += 1
                elif act == 'Recover': me['hp'] = min(100, me['hp'] + 50)
                elif act == 'attack':
                    dmg = me['d'][j] * STAGE(me['boost'] + me['curse'])
                    bar -= dmg
                    if me['recoil']: me['hp'] -= me['recoil'] * min(dmg, max(0, bar + dmg)) / 100 * BOSS_HP / me['maxhp'] * 100
                    if B['item'] == 'ROCKYHELMET' and me['contact']: me['hp'] -= 100 / 6
            def boss():
                nonlocal bar
                if bar <= 0 or me['hp'] <= 0: return
                hit = me['t'][j]
                p = part[pi] if part and pi < len(part) else None
                if FOCUS_PARTNER and p and p['take'][j] / 1.3 > hit:   # the AI hits whoever it hurts most (relative)
                    p['cur'] -= p['take'][j] / 1.3; return
                if me['sash'] and me['hp'] >= 100 and hit >= 100: me['hp'] = 0.5; me['sash'] = False
                else: me['hp'] -= hit
                if set(B['moves']) & DRAIN: bar = min(100, bar + .25 * min(hit, 100) * me['maxhp'] / BOSS_HP)
            b0 = bar; h0 = me['hp']
            if act == 'switch':
                ai += 1; me = team[ai]; h0 = me['hp']; boss()
            elif me['spe'] > BOSS_SPE: ours(); boss()
            else: boss(); ours() if me['hp'] > 0 else None
            if log is not None: log.append(dict(stage=me['boost'] + me['curse'], bar=j, t=t_bar, mon=me['n'], act=act, dealt=round(max(0, min(b0, b0 - bar))), took=round(max(0, h0 - me['hp'])),
                                                 left=round(max(0, bar)), hp=round(max(0, me['hp'])), partner=(part[pi]['name'] if part and pi < len(part) else '')))
            if part and pi < len(part) and part[pi]['cur'] <= 0: pi += 1
            if bar > 0 and part and pi < len(part): bar -= part[pi]['deal'][j]
            if bar > 0:   # end of turn
                if not gastro: bar += 12.5
                if B['item'] == 'BLACKSLUDGE' and not knocked: bar += 12.5
                if sitrus and bar < 50: bar += 25; sitrus = False
                bar = min(100, bar)
            if me['hp'] > 0 and FIELD_CHIP and me['grounded'] and not ({'POISON', 'STEEL'} & set(me['types'])): me['hp'] -= 12.5
            if me['hp'] > 0 and ITEM[me['n']] == 'Black Sludge' and 'POISON' in me['types']: me['hp'] = min(100, me['hp'] + 12.5)
            if me['hp'] <= 0:
                ai += 1
                if ai >= len(team): return None
                me = team[ai]
    return dict(turns=turns, left=sum(max(0, m['hp']) for m in team), alive=sum(m['hp'] > 0 for m in team), order=order)


def best(partner):
    res = []
    lead = (ST.get('plan_leads') or {}).get(KEY)
    for perm in itertools.permutations(SIX):
        if lead and perm[0] != lead[0]: continue
        r = play(list(perm), partner)
        if r: res.append(r)
    res.sort(key=lambda r: -(r['alive'] * 250 + r['left'] - 2 * r['turns']))
    return res


out = {}
for mode in ('melia', 'solo'):
    rs = best(mode == 'melia')
    if not rs: out[mode] = None; continue
    lg = []; play(rs[0]['order'], mode == 'melia', lg)
    out[mode] = dict(order=rs[0]['order'], alive=rs[0]['alive'], left=round(rs[0]['left']), turns=rs[0]['turns'], log=lg, n_wins=len(rs))
if out.get('melia'):
    from collections import Counter
    carrier = Counter(l['mon'] for l in out['melia']['log']).most_common(1)[0][0]; out['carrier'] = carrier
    rest = [n for n in SIX if n != carrier]; lead = (ST.get('plan_leads') or {}).get(KEY)
    rs = [r for p in itertools.permutations(rest) if not lead or p[0] == lead[0] or lead[0] == carrier for r in [play(list(p), True)] if r]
    rs.sort(key=lambda r: -(r['alive'] * 250 + r['left'] - 2 * r['turns']))
    if rs:
        lg = []; play(rs[0]['order'], True, lg); out['backup'] = dict(order=rs[0]['order'], log=lg)
TY = json.load(open('data/Database_Types.json')); MD = json.load(open('gamedata/movetext.json'))
def eff(at, dts):
    m = 1.0
    for d in dts:
        e = TY.get(d.title(), {})
        if at in e.get('Weaknesses', []): m *= 2
        if at in e.get('Resistances', []): m *= .5
        if at in e.get('Immunities', []): m *= 0
    return m
def main_move(n, j):
    ms = rows[n]['mids']
    return max(ms, key=lambda x: (eff(MD.get(x, {}).get('type', ''), BARS[j]['types'] or []) * (MD.get(x, {}).get('basedamage') or 0)))
out['move'] = {n: [MD.get(main_move(n, j), {}).get('name', '') for j in range(NB)] for n in SIX}
out['mons'] = {n: dict(d=[round(x) for x in mon(n)['d']], t=[round(x) for x in mon(n)['t']], spe=rows[n]['spe']) for n in SIX}
out['bars'] = [dict(types=B['types'], item=B['item'], moves=B['moves'], stg=B['stg']) for B in BARS]
out['boss_spe'] = BOSS_SPE
json.dump(out, open(f'team/bar_plan_{KEY}.json', 'w'), indent=1)
for mode in ('melia', 'solo'):
    o = out[mode]
    print(mode, 'NO WIN' if not o else f"WIN {o['alive']} left, {o['left']}% HP, {o['turns']} turns, {o['n_wins']} winning orders: {o['order']}")
    for l in (o or {}).get('log', []): print('  ', l)
print('backup', (out.get('backup') or {}).get('order'))
