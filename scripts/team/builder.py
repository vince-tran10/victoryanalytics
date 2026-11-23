"""Team Builder tab (Vincent, 22 Nov): how each of the 4 CORE slots was picked.
For every slot: the role's job, then the best candidates for THAT slot with the other three core members kept in place
(same core score as cores.py: strength + defence + coverage + answers + identity + role fit), your pick marked.
Writes team/builder.json and inserts section 'sbuild' into the report (before tabs.py).
usage (from workspace/): DONE=... CR_RUN=r<run> python3 -I ../scripts/team/builder.py <report.html>"""
import contextlib, html, io, json, os, re, runpy, shutil, sys, tempfile
OUT = sys.argv[1]
tmp = tempfile.NamedTemporaryFile(suffix='.html', delete=False).name
shutil.copy(OUT, tmp)
_cs = 'team/cores.json'; _bak = open(_cs).read() if os.path.exists(_cs) else None
sys.argv = ['cores.py', tmp]
with contextlib.redirect_stdout(io.StringIO()):
    G = runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cores.py'))
if _bak is not None: open(_cs, 'w').write(_bak)   # cores.py writes cores.json: keep the real one
os.unlink(tmp)
Mon, rows_all, TYPES = G['Mon'], G['rows'], G['TYPES']
from kits import disp
E = html.escape
st = json.load(open('team/state.json'))
MT = json.load(open('gamedata/movetext.json')) if os.path.exists('gamedata/movetext.json') else {}
def mname(k): return (MT.get(k) or {}).get('name', k.title())
# 22 Nov: the Builder shows the SAME tier as the Dex (live tier_all), not the chapter-frozen core snapshot
_LIVE = {}
for _r in json.load(open('team/tier_all.json'))['rows']: _LIVE.setdefault(_r['name'], _r)
rows_all = [dict(r, tier=_LIVE[r['name']]['tier'], blend=_LIVE[r['name']]['blend']) if r['name'] in _LIVE else r for r in rows_all]
ALLM = {}
for r in rows_all:
    if r['name'] not in ALLM: ALLM[r['name']] = Mon(r)
core = [n if n in ALLM else None for n in st['core']]   # 22 Nov: a member he no longer owns leaves its slot empty
SPREAD = ['MAKEITRAIN', 'HEATWAVE', 'EARTHQUAKE', 'ROCKSLIDE', 'MUDDYWATER', 'DAZZLINGGLEAM', 'HYPERVOICE', 'ICYWIND', 'BLIZZARD', 'DISCHARGE',
          'SURF', 'SLUDGEWAVE', 'ERUPTION', 'WATERSPOUT', 'SNARL', 'BREAKINGSWIPE', 'LAVAPLUME', 'BULLDOZE', 'ELECTROWEB', 'BOOMBURST', 'EXPANDINGFORCE']
# Slot 1 = singles lead (Vincent, 22 Nov): faster > bulky, takes one hit, KOs in 1-2 hits. Measured vs EVERY trainer in the game data
# (all-fights engine run r<run>all): per foe faster / hits to KO (hko) / hits to die (hdie). Lead win = KOs in <= 2 hits before it dies.
import pickle
LEAD = {}
_pk = f"team/r{st['run']}all_native.json.pkl"
if os.path.exists(_pk):
    for c in pickle.load(open(_pk, 'rb'))['cands']:
        if c['gate']: continue
        rr = [x for v in c['matchups'].values() for x in v]
        if not rr: continue
        n = len(rr)
        hd = sorted(x['hdie'] for x in rr)
        v = dict(hits=hd[n // 2], fast=sum(x['faster'] for x in rr) / n, ko=sum(x['hko'] <= 2 for x in rr) / n, surv=sum(x['hdie'] >= 2 for x in rr) / n,
                 win=sum(x['hko'] <= 2 and (x['hdie'] >= x['hko'] if x['faster'] else x['hdie'] > x['hko']) for x in rr) / n)
        if c['name'] not in LEAD or (v['win'], v['fast']) > (LEAD[c['name']]['win'], LEAD[c['name']]['fast']): LEAD[c['name']] = v
PRIO = ['EXTREMESPEED', 'SUCKERPUNCH', 'AQUAJET', 'JETPUNCH', 'BULLETPUNCH', 'MACHPUNCH', 'ICESHARD', 'SHADOWSNEAK', 'ACCELEROCK',
        'VACUUMWAVE', 'FIRSTIMPRESSION', 'GRASSYGLIDE', 'QUICKATTACK']
SPREAD_ALL = set(SPREAD) | {'SURGINGSTRIKES', 'PRECIPICEBLADES', 'ORIGINPULSE', 'GLACIATE', 'PETALBLIZZARD', 'SWIFT', 'PARABOLICCHARGE', 
                            'POWDERSNOW', 'RAZORLEAF', 'AIRCUTTER', 'TWISTER', 'STRUGGLEBUG', 'MORTALSPIN', 'MATCHAGOTCHA', 'BLEAKWINDSTORM',
                            'SANDSEARSTORM', 'SPRINGTIDESTORM', 'WILDBOLTSTORM', 'OVERDRIVE', 'SPARKLINGARIA',
                            'DIAMONDSTORM', 'HYPERSPACEFURY', 'SELFDESTRUCT', 'EXPLOSION', 'MINDBLOWN', 'SURF', 'MAGNITUDE'}
IB = json.load(open('team/ideal_builds.json')) if os.path.exists('team/ideal_builds.json') else {}
def _id(x): return ''.join(ch for ch in x.upper() if ch.isalpha())
def build_moves(n):   # what it actually runs: his party moves, else its ideal build
    return [_id(x) for x in ((st.get('moves') or {}).get(n) or (IB.get(n) or {}).get('moves') or [])]
def common_chips(m):   # shared by every slot (Vincent, 22 Nov): bulk as resistances / weaknesses, spread vs single target
    res_ = sum(m.mult[a] < 1 for a in TYPES); wk = sum(m.mult[a] > 1 for a in TYPES)
    sp = next((mname(x) for x in build_moves(m.name) if x in SPREAD_ALL), None)
    can = None if sp else first(m.legal, [x for x in SPREAD if x in m.legal])
    pl = lambda k: f"{k} type" + ('' if k == 1 else 's')
    return [f'Resists {pl(res_)}', f'Weak to {pl(wk)}'], ([f'Spread: {sp}'] if sp else [])
def lead_chips(m):
    v = LEAD[m.name]
    cs, ct = common_chips(m)
    st_ = [f"Outspeeds {v['fast']:.0%}", f"Takes {v['hits']} hits to KO"] + cs
    if not ct: st_.append('Single target only')
    L, ab = m.legal, set(m.r.get('abilities') or [])
    t = list(ct)
    if 'INTIMIDATE' in ab: t.append('Intimidate')
    if 'FAKEOUT' in L: t.append('Fake Out')
    x = first(L, PRIO); t += [f'Priority: {x}'] if x else []
    if 'TAUNT' in L: t.append('Taunt')
    if 'GOODASGOLD' in ab: t.append('Blocks status moves')
    return st_, merge(t, kit(m))
def first(L, ids): return next((mname(x) for x in ids if x in L), None)
# 22 Nov (Vincent): key details per Pokémon = what its build actually RUNS, by what roles care about
KIT = [('Redirection', ['FOLLOWME', 'RAGEPOWDER']),
       ('Status', ['SPORE', 'SLEEPPOWDER', 'YAWN', 'WILLOWISP', 'THUNDERWAVE', 'GLARE', 'NUZZLE', 'TOXIC', 'HYPNOSIS', 'STUNSPORE', 'SING']),
       ('Speed control', ['TAILWIND', 'TRICKROOM', 'ICYWIND', 'ELECTROWEB', 'SCARYFACE', 'BULLDOZE', 'STRINGSHOT']),
       ('Setup', ['SWORDSDANCE', 'NASTYPLOT', 'SHELLSMASH', 'BELLYDRUM', 'DRAGONDANCE', 'QUIVERDANCE', 'CALMMIND', 'BULKUP', 'CURSE',
                  'SHIFTGEAR', 'COIL', 'TIDYUP', 'VICTORYDANCE', 'FILLETAWAY', 'TAILGLOW', 'GEOMANCY', 'IRONDEFENSE', 'COSMICPOWER']),
       ('Pivot', ['UTURN', 'VOLTSWITCH', 'FLIPTURN', 'PARTINGSHOT', 'TELEPORT', 'CHILLYRECEPTION']),
       ('Recovery', ['RECOVER', 'ROOST', 'SLACKOFF', 'MOONLIGHT', 'SYNTHESIS', 'SOFTBOILED', 'WISH', 'SHOREUP', 'STRENGTHSAP', 'MILKDRINK', 'MORNINGSUN']),
       ('Stat reset', ['HAZE', 'CLEARSMOG', 'ROAR', 'WHIRLWIND', 'DRAGONTAIL', 'CIRCLETHROW']),
       ('Disrupt', ['FAKEOUT', 'TAUNT', 'ENCORE', 'KNOCKOFF', 'TRICK']),
       ('Screens', ['REFLECT', 'LIGHTSCREEN', 'AURORAVEIL']),
       ('Support', ['HELPINGHAND', 'WIDEGUARD', 'QUICKGUARD', 'POLLENPUFF', 'LIFEDEW', 'SAFEGUARD', 'MISTYTERRAIN'])]
def kit(m):
    bm = build_moves(m.name); out_ = []
    for lab, ids in KIT:
        hit = [mname(x) for x in bm if x in ids]
        if hit: out_.append(f'{lab}: {hit[0]}')
    x = next((mname(y) for y in bm if y in PRIO), None)
    if x: out_.append(f'Priority: {x}')
    return out_
ABIL_CHIPS = ('Intimidate', 'Regenerator', 'Blocks status moves', 'Speed Boost', 'Moxie', 'Beast Boost', 'status-proof')
def teach_split(m, chips):   # 22 Nov (Vincent): chips must match the build: move chips not in its build become "Teach: X"
    bm = set(build_moves(m.name)); have, teach = [], []
    for x in chips:
        mv = x.split(': ')[-1].split(' (')[0]
        if x in ABIL_CHIPS or x.startswith(('Spread:',)) or _id(mv) in bm or not any(_id(mv) == k for k in MT): have.append(x)
        else: teach.append(mv)
    return have, teach
def merge(a, b):   # role tools first, then kit chips naming a move not already shown
    seen = {x.split(': ')[-1].split(' (')[0] for x in a}
    return a + [x for x in b if x.split(': ')[-1] not in seen]
def tools(m, slot):   # the role's tools this Pokémon can legally run (moves) or has (ability)
    L, ab = m.legal, set(m.r.get('abilities') or [])
    t = []
    if slot in (1, 2):
        if 'INTIMIDATE' in ab: t.append('Intimidate')
        if 'FAKEOUT' in L: t.append('Fake Out')
    if slot == 2:
        x = first(L, ['FOLLOWME', 'RAGEPOWDER']);  t += [x] if x else []
        if 'TAILWIND' in L: t.append('Tailwind')
        x = first(L, SPREAD); t += [f'spread: {x}'] if x else []
    if slot == 1:
        x = first(L, ['THUNDERWAVE', 'ICYWIND', 'ELECTROWEB', 'TAILWIND', 'TRICKROOM', 'GLARE', 'SCARYFACE']); t += [x] if x else []
        x = first(L, ['TAUNT', 'ENCORE']); t += [x] if x else []
        if ab & {'GOODASGOLD', 'MAGICGUARD', 'INSOMNIA', 'VITALSPIRIT', 'COMATOSE', 'PURIFYINGSALT'}: t.append('status-proof')
    if slot == 3:
        x = first(L, ['HAZE', 'CLEARSMOG', 'ROAR', 'WHIRLWIND']); t += [x] if x else []
        x = first(L, ['RECOVER', 'ROOST', 'SLACKOFF', 'MOONLIGHT', 'SYNTHESIS', 'SOFTBOILED', 'WISH', 'SHOREUP', 'STRENGTHSAP', 'MILKDRINK'])
        t += [x] if x else []
        if 'REGENERATOR' in ab: t.append('Regenerator')
        x = first(L, ['UTURN', 'VOLTSWITCH', 'FLIPTURN', 'PARTINGSHOT', 'TELEPORT']); t += [x] if x else []
    if slot == 4:
        setv = {'SWORDSDANCE': '+2', 'NASTYPLOT': '+2', 'SHELLSMASH': '+2', 'BELLYDRUM': '+6', 'FILLETAWAY': '+2', 'TAILGLOW': '+3', 'GEOMANCY': '+2',
                'DRAGONDANCE': '+1/+1', 'QUIVERDANCE': '+1/+1', 'SHIFTGEAR': '+1/+2', 'TIDYUP': '+1/+1', 'VICTORYDANCE': '+1',
                'CALMMIND': '+1', 'BULKUP': '+1', 'COIL': '+1', 'CURSE': '+1'}
        phys = m.r.get('cat') == 'Physical'
        ok = [k for k in setv if k in L and ((phys and k not in ('NASTYPLOT', 'CALMMIND', 'QUIVERDANCE', 'TAILGLOW', 'GEOMANCY')) or (not phys and k in ('NASTYPLOT', 'CALMMIND', 'QUIVERDANCE', 'SHELLSMASH', 'FILLETAWAY', 'TAILGLOW', 'GEOMANCY')))]
        if ok:
            best_ = max(ok, key=lambda k: {'+6': 6, '+3': 3, '+2': 2, '+1/+2': 1.9, '+1/+1': 1.6, '+1': 1}[setv[k]])
            t.append(f"{mname(best_)} ({setv[best_]})")
        for a_ in ('SPEEDBOOST', 'MOXIE', 'BEASTBOOST'):
            if a_ in ab: t.append(a_.title().replace('boost', ' Boost'))
    return t
NEED = {1: lambda m, t: bool(t) and (m.spe >= 80 or m.bulk >= 270),
        2: lambda m, t: any(x in ('Intimidate', 'Fake Out', 'Tailwind', 'Follow Me', 'Rage Powder') for x in t),
        3: lambda m, t: m.bulk >= 270 and any(not x.startswith('spread') for x in t),
        4: lambda m, t: bool(t)}
RK = {'S': 4, 'A': 3, 'B': 2, 'C': 1, 'D': 0}
ROLES = [
    ('Core 1 · Lead', ['Leads singles', 'Left slot in doubles', 'Fast (80+ base Speed) or bulky', 'Turn-1 tools: Intimidate, Fake Out, speed control, Taunt', 'Status-proof is a plus']),
    ('Core 2 · Doubles lead', ['Right slot in doubles', 'Must bring Intimidate, Fake Out, Follow Me / Rage Powder or Tailwind', 'A spread move is a plus']),
    ('Core 3 · Mid game', ['Bulky pivot (HP + Def + SpD 270+)', 'Must bring an answer: Haze / phazing, recovery, Regenerator or a pivot move']),
    ('Core 4 · Closer', ['Must have a setup move (or a boosting ability)', 'Bigger boosts rank higher (+2 beats +1)']),
]
def weak3(ms):
    return any(sum(m.mult[a] > 1 for m in ms) >= 3 for a in TYPES)
out = []
USED = set()   # one suggestion per Pokémon across the 4 slots
if len(core) == 4:
    base = [ALLM[n] if n else None for n in core]
    for i, (title, needs) in enumerate(ROLES):
        slot = i + 1; others = [m for j, m in enumerate(base) if j != i and m]
        res = []
        if slot == 1 and LEAD:
            res = []
            for m in ALLM.values():
                v = LEAD.get(m.name)
                if not v or m.sp in {o.sp for o in others}: continue
                if v['fast'] < .70 or v['ko'] < .65 or v['surv'] < .60 or weak3(others + [m]): continue
                res.append((RK.get(m.r['tier'], 0), v['win'], v['fast'], m, lead_chips(m)))
            res.sort(key=lambda x: (-x[0], -x[1], -x[2]))
            mine = base[i].name if base[i] else None; pv = LEAD.get(mine, dict(win=0, fast=0))
            # yellow = a real alternative: same tier or higher, not in the core, fits the other three, clearly better lead (win +.05)
            rec = res[0][3].name if res else None; USED.add(rec)   # 22 Nov: my suggestion = the top of this ranking (tier, then role preference)
            top = [x for x in res if x[3].name not in (rec, mine)][:6 - len({rec, mine} - {None})]
            for want in (rec, mine):
                if want and want not in [x[3].name for x in top]:
                    v_ = LEAD.get(want, dict(win=0, fast=0))
                    top.append(next((x for x in res if x[3].name == want), None) or (RK.get(ALLM[want].r['tier'], 0), v_['win'], v_['fast'], ALLM[want], lead_chips(ALLM[want]) if want in LEAD else ([], [])))
            top.sort(key=lambda x: (-x[0], -x[1], -x[2]))   # tier, then lead preference (pick included in order)
            out.append(dict(slot=slot, title=title, pick=mine, rec=rec,
                            cands=[dict(name=m.name, tier=m.r['tier'], stats=ch[0], tools=ch[1], sid=m.r.get('sid'), form=str(m.r.get('form', '0')),
                                        pick=m.name == mine, rec=m.name == rec) for _, _, _, m, ch in top]))
            for c in out[-1]['cands']: c['tools'], c['teach'] = teach_split(ALLM[c['name']], c['tools'])
            continue
        for m in ALLM.values():
            if m.sp in {o.sp for o in others}: continue
            t = tools(m, slot)
            if not NEED[slot](m, t): continue
            if weak3(others + [m]): continue
            sz = max([{'(+6)': 6, '(+3)': 3, '(+2)': 2, '(+1/+2)': 1.9, '(+1/+1)': 1.6, '(+1)': 1}.get(x.split(' ')[-1], 0) for x in t] + [0]) if slot == 4 else len(t)
            res.append((RK.get(m.r['tier'], 0), sz, m.r['blend'], m, t))
        res.sort(key=lambda x: (-x[0], -x[1], -x[2]))
        names = [x[3].name for x in res]
        top = res[:6]
        mine = base[i].name if base[i] else None
        if mine not in [x[3].name for x in top]:
            hit = next((x for x in res if x[3].name == mine), None)
            if hit: top = top[:5] + [hit]
        # suggestion (Vincent 22 Nov: highlight MY pick per slot): tier + role fit + type matchups, not just the list order
        def _fit(x):
            m, t = x[3], x[4]
            f_ = min(x[1], 2) if slot == 4 else len([y for y in t if not y.startswith('spread')])
            cover = sum(1 for a in TYPES if m.mult[a] < 1 and any(o.mult[a] > 1 for o in others) and not any(o.mult[a] < 1 for o in others))
            # 22 Nov: + covering the other three's weaknesses that nobody else resists (the type-matrix gaps)
            # 22 Nov fix: tier counts double and tools cap at 2, so tool count / coverage can't lift a lower tier over a higher one
            # by itself (Scrafty B was suggested over Amoonguss A on Intimidate + Fake Out)
            return 2 * RK.get(m.r['tier'], 0) + min(f_, 2) + .1 * (sum(m.mult[a] < 1 for a in TYPES) - sum(m.mult[a] > 1 for a in TYPES)) + .2 * min(cover, 3)
        _pool = [x for x in res if x[3].name not in USED] or res
        _best = max(_pool, key=_fit) if _pool else None
        _mine = next((x for x in _pool if x[3].name == (base[i].name if base[i] else None)), None)
        # stability (22 Nov): his pick stays my suggestion when it is the same tier and within 0.3 role fit of the best (no flip-flops)
        if _best and _mine and _mine[0] == _best[0] and _fit(_mine) >= _fit(_best) - .3: _best = _mine
        rec = _best[3].name if _best else None
        USED.add(rec)
        if rec and rec not in [x[3].name for x in top]: top = top[:5] + [next(x for x in res if x[3].name == rec)]
        top.sort(key=lambda x: (-x[0], -x[1], -x[2]))
        def _st(m):
            cs, ct = common_chips(m)
            return cs + ([] if ct else ['Single target only']), ct
        # 22 Nov (Vincent): when my suggestion is not the highest tier, defend it vs each higher-tier option (one reason per line)
        def why_not(rm, rt, cm, ct):
            out_ = []
            rt_ = [y for y in rt if not y.startswith('spread')]; ct_ = [y for y in ct if not y.startswith('spread')]
            if slot == 4:
                if x_rec[1] > next(x for x in res if x[3].name == cm.name)[1]: out_.append(f"Bigger boost: {rt_[0]} vs {ct_[0] if ct_ else 'none'}")
            elif len(rt_) > len(ct_):
                out_.append(f"Role tools: {', '.join(rt_)} vs {', '.join(ct_) or 'none'}")
            rw = sum(rm.mult[a] > 1 for a in TYPES); cw = sum(cm.mult[a] > 1 for a in TYPES)
            rr = sum(rm.mult[a] < 1 for a in TYPES); cr = sum(cm.mult[a] < 1 for a in TYPES)
            if rw < cw: out_.append(f"Weak to {rw} types vs {cw}")
            if rr > cr: out_.append(f"Resists {rr} types vs {cr}")
            stack = lambda mm: [a.title() for a in TYPES if mm.mult[a] > 1 and any(o.mult[a] > 1 for o in others)]
            rs, cs = stack(rm), stack(cm)
            if len(rs) < len(cs): out_.append(f"Shares fewer weaknesses with the core: {len(rs)} vs {len(cs)} ({', '.join(cs)})")
            cat = lambda mm: mm.r.get('cat') or ''
            phys = sum(cat(o) == 'Physical' for o in others); spec = sum(cat(o) == 'Special' for o in others)
            if cat(rm) != cat(cm) and ((cat(rm) == 'Special' and phys > spec) or (cat(rm) == 'Physical' and spec > phys)):
                out_.append(f"Balances the core: {cat(rm).lower()} next to {max(phys, spec)} {('physical' if phys > spec else 'special')} attackers")
            if (rm.r.get('abilities') and 'REGENERATOR' in rm.r['abilities']) and not (cm.r.get('abilities') and 'REGENERATOR' in cm.r['abilities']) and slot == 3:
                out_.append('Regenerator: heals on every switch-out')
            return out_
        x_rec = next((x for x in res if x[3].name == rec), None)
        WHY = []
        if x_rec:
            for x in sorted(res, key=lambda x: (-x[0], -x[2])):
                if x[0] > x_rec[0] and len(WHY) < 2:
                    WHY.append(dict(name=disp(x[3].name), tier=x[3].r['tier'], lines=why_not(x_rec[3], x_rec[4], x[3], x[4])))
        out.append(dict(slot=slot, title=title, pick=mine, rec=rec, why=WHY,
                        cands=[dict(name=m.name, tier=m.r['tier'], stats=_st(m)[0], tools=merge([x for x in t if not x.startswith('spread')] + _st(m)[1], kit(m)),
                                    sid=m.r.get('sid'), form=str(m.r.get('form', '0')), pick=m.name == mine, rec=m.name == rec)
                               for _, _, _, m, t in top]))
        for c in out[-1]['cands']: c['tools'], c['teach'] = teach_split(ALLM[c['name']], c['tools'])
# 22 Nov (Vincent): Flex 1 / Flex 2 = the 2 chapter swaps for the NEXT fight only (fight_plans.json: the plan + its best alternatives)
FIGHT_TITLE = {'spector': 'Spector (day)', 'spector2': 'Spector (night)', 'jenner9': 'Spirit Jenner', 'amanda': 'Amanda', 'erick': 'Erick',
               'karrina': 'Karrina', 'garbodor': 'Rift Garbodor', 'darkgardevoir': 'Dark Gardevoir'}
_fp = json.load(open('team/fight_plans.json')) if os.path.exists('team/fight_plans.json') else {}
_fk = st.get('fight') or next((k for k in _fp), None)
_pl = _fp.get(_fk) or {}
if _pl and len(core) == 4:
    flexes = [n for n in st['team'] if n not in st['core']][:2]
    counters_of = {}
    for p_ in _pl.get('pairs') or []:
        if p_.get('ok'): counters_of.setdefault(p_['mon'], []).append(p_['foe'])
    alt_names = []
    for a_ in _pl.get('alts') or []:
        for n_ in a_['swaps']:
            if n_ not in alt_names and n_ not in st['core']: alt_names.append(n_)
    for fi, (lab, fn) in enumerate(zip(['Flex 1 · Mid game', 'Flex 2 · Closer'], flexes)):
        _setup = lambda n_: any(k.startswith('Setup') for k in kit(ALLM[n_])) if n_ in ALLM else False
        names = [fn] + [x for x in alt_names if x not in flexes and (_setup(x) == (fi == 1))][:4]   # closer flex = has a setup move
        cands = []
        for n_ in names:
            m = ALLM.get(n_)
            if not m: continue
            cs, ct = common_chips(m)
            tl = merge(ct + [f'Counters: {f_}' for f_ in counters_of.get(n_, [])], kit(m))
            have, teach = teach_split(m, tl)
            cands.append(dict(name=n_, tier=m.r['tier'], stats=cs + ([] if ct else ['Single target only']), tools=have, teach=teach,
                              sid=m.r.get('sid'), form=str(m.r.get('form', '0')), pick=n_ == fn, rec=n_ == fn))
        out.append(dict(slot=5 + fi, title=f"{lab} · {FIGHT_TITLE.get(_fk, _fk)}", pick=fn, rec=fn, flex=True, cands=cands))
# 22 Nov (Vincent): a role for EVERY Pokémon (Dex tiles / filters / sheet), from what its BUILD runs (same data as the chips)
ROLE_ORDER = ['Lead', 'Doubles lead', 'Mid game', 'Closer', 'Support', 'Attacker']
def role_of(m):
    bm = set(build_moves(m.name)); ab = set(m.r.get('abilities') or [])
    ab_run = re.sub(r'[^A-Z]', '', str((st.get('abilities') or {}).get(m.name) or (IB.get(m.name) or {}).get('ability') or m.r.get('ability') or '').upper())
    has = lambda ids: next((mname(x) for x in ids if x in bm), None)
    x = has(['FOLLOWME', 'RAGEPOWDER']) or has(['FAKEOUT']) or ('Intimidate' if ab_run == 'INTIMIDATE' else None) or has(['TAILWIND'])
    if x: return 'Doubles lead', x
    v = LEAD.get(m.name)
    if v and v['fast'] >= .70 and v['ko'] >= .65 and v['surv'] >= .60: return 'Lead', f"outspeeds {v['fast']:.0%}"
    x = has(['SWORDSDANCE', 'NASTYPLOT', 'SHELLSMASH', 'BELLYDRUM', 'DRAGONDANCE', 'QUIVERDANCE', 'CALMMIND', 'BULKUP', 'CURSE', 'SHIFTGEAR',
             'COIL', 'TIDYUP', 'VICTORYDANCE', 'FILLETAWAY', 'TAILGLOW', 'GEOMANCY'])
    if x: return 'Closer', x
    x = (('Regenerator' if ab_run == 'REGENERATOR' else None) or has(['RECOVER', 'ROOST', 'SLACKOFF', 'MOONLIGHT', 'SYNTHESIS', 'SOFTBOILED', 'WISH',
         'SHOREUP', 'STRENGTHSAP', 'MILKDRINK', 'MORNINGSUN']) or has(['HAZE', 'CLEARSMOG', 'ROAR', 'WHIRLWIND']) or has(['UTURN', 'VOLTSWITCH', 'FLIPTURN', 'PARTINGSHOT', 'TELEPORT']))
    if x and m.bulk >= 270: return 'Mid game', x
    SET = {'DROUGHT': 'Drought', 'DRIZZLE': 'Drizzle', 'SANDSTREAM': 'Sand Stream', 'SNOWWARNING': 'Snow Warning', 'GRASSYSURGE': 'Grassy Surge',
           'ELECTRICSURGE': 'Electric Surge', 'PSYCHICSURGE': 'Psychic Surge', 'MISTYSURGE': 'Misty Surge'}
    if ab_run in SET: return 'Support', f'{SET[ab_run]} setter'
    x = has(['TRICKROOM', 'REFLECT', 'LIGHTSCREEN', 'AURORAVEIL', 'SAFEGUARD', 'HELPINGHAND', 'WIDEGUARD', 'SPORE', 'SLEEPPOWDER', 'YAWN',
             'WILLOWISP', 'THUNDERWAVE', 'GLARE', 'STEALTHROCK', 'SPIKES', 'TOXICSPIKES', 'STICKYWEB', 'LIGHTSCREEN'])
    if x: return 'Support', x
    return 'Attacker', ''
ROLES_ALL = {}
for m in ALLM.values():
    ROLES_ALL[disp(m.name)] = role_of(m)
json.dump(dict(core=core, slots=out, roles=ROLES_ALL), open('team/builder.json', 'w'), indent=1, ensure_ascii=False)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sprites as SP
cards = ''
for s_ in out:
    rows = ''
    for c in s_['cands']:
        rows += ('<li class="bc' + (' pick' if c['pick'] else '') + (' rec' if c.get('rec') else '') + '" data-dn="' + E(disp(c['name'])) + '" tabindex="0" role="button"><div class="bct">'
                 + '<label class="bchk" title="Add to the type matrix"><input type="checkbox" data-tm="' + E(disp(c['name'])) + '"' + (' checked' if c['pick'] else '') + '></label>'
                 + '<span class="tier t' + c['tier'] + '">' + c['tier'] + '</span>' + SP.tag(c['sid'], c['form'], size='s')
                 + '<b>' + E(disp(c['name'])) + '</b>' + ('<span class="bpick">Your pick</span>' if c['pick'] else '') + ('<span class="brec">Suggested</span>' if c.get('rec') else '') + '</div>'
                 + '<div class="btools">' + ''.join('<span class="bstat">' + E(x) + '</span>' for x in c.get('stats', [])) + ''.join('<span class="btool">' + E(x) + '</span>' for x in c['tools']) + '</div>'
                 + (''.join('<div class="bwhy"><b>Why not ' + E(w['name']) + ' (' + w['tier'] + ')</b><ul>' + ''.join('<li>' + E(l) + '</li>' for l in w['lines']) + '</ul></div>'
                            for w in s_.get('why') or [] if w['lines']) if c.get('rec') else '') + '</li>')
    cards += ('<article class="bslot' + (' bflex' if s_.get('flex') else '') + '"><header><span class="bn">' + (('F' + str(s_['slot'] - 4)) if s_.get('flex') else str(s_['slot'])) + '</span><b>' + E(s_['title']) + '</b>'
              + ('<span class="bempty">Empty</span>' if not s_['pick'] else '') + '</header>'
              + '<ol class="bcands">' + rows + '</ol></article>')
# 22 Nov (Vincent): type matrix at the bottom; tick a Pokémon's box to add it (your 4 picks start ticked)
_tm = {}
for s_ in out:
    for c in s_['cands']:
        m = ALLM.get(c['name'])
        if m: _tm[disp(c['name'])] = dict(t=[x.title() for x in m.r['types']], m={a.title(): m.mult[a] for a in TYPES}, sp=SP.cls(c['sid'], c['form'])[3:])
TM = ('<div class="tmx"><h3>Type matrix</h3>'
      '<div class="tmx-wrap"><table class="tmx-t" id="tmx"></table></div></div>'
      '<script type="application/json" id="tmdata">' + json.dumps(dict(types=[a.title() for a in TYPES], mons=_tm)).replace('</', '<\\/') + '</script>')
sec = ('<section aria-labelledby="sbuild">\n  <h2 id="sbuild">Team Builder</h2>\n'
       '  <div class="bgrid">' + cards + '</div>\n' + TM + '\n</section>\n')
page = open(OUT, encoding='utf-8').read()
page = re.sub(r'<section aria-labelledby="sbuild">.*?</section>\s*', '', page, flags=re.S)
anchor = page.find('<section aria-labelledby="s1f">')
page = page[:anchor] + sec + page[anchor:] if anchor >= 0 else page.replace('</main>', sec + '</main>')
open(OUT, 'w', encoding='utf-8').write(page)
print('builder:', [(s_['title'], s_['pick'], s_.get('rec')) for s_ in out])
