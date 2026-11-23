"""Team Planner (Vincent, 23 Nov): the best SIX from his pool (Party + Active box) for the next fight, DEFENSE FIRST.
Replaces the fixed core-of-4 + 2 flexes. Workflow it encodes:
  1 scout (their six, their attack types after the field, how they win)  2 defense first (every member survives, their main
  types resisted, nothing hits 3+)  3 answers to each win condition  4 offense second  5 leads = the pair that beats their lead
  pair. Data: per-foe matchups from the engine run (field rules incl. the type-chart overrides), types via engine.chart_eff.
usage (from workspace/): python3 -I ../scripts/team/planner.py   -> team/planner.json (+ state team when mode == 'planner')"""
import itertools, json, os, pickle, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gamedata'))
import numpy as np
import gamedata as G
from fields import GUIDE_TO_FE
os.environ.setdefault('MOVE_RULES', 'relearn')
import engine
STATE = 'team/state.json'
st = json.load(open(STATE))
FK = os.environ.get('PLAN_FIGHT') or st.get('fight')
import bosses
B9 = {b[0]: b for b in bosses.CH9}
FIELD = B9[FK][2] if FK in B9 else ''
FE = GUIDE_TO_FE.get(FIELD)
_FC = (G.load('fieldtext').get(FE or '', {}) or {}).get('fieldChange') or {}
BREAKABLE = any({'FLASH', 'DAZZLINGGLEAM'} & set(v) for v in _FC.values())   # 23 Nov: only fields the game lets Flash change (not Concert Venue)
BREAK = bool(os.environ.get('PLAN_BREAK')) and FE is not None and BREAKABLE   # lead a Flash / Dazzling Gleam user, fight on no field
FE0 = FE
if BREAK: FE = None
FMT = B9[FK][3] if FK in B9 else 'Doubles'
E = engine.Engine(os.path.abspath('.'))
MV = G.load('movetext'); BYNAME = {v['name'].lower(): k for k, v in MV.items()}
FT = G.load('fieldtext').get(FE or '', {}) if FE else {}
TYPEMODS = {mv: t for t, ms in (FT.get('typeMods') or {}).items() for mv in ms}
SPREAD_T = {'AllOpposing', 'AllNonUsers', 'AllBattlers'}
SETUP = {'SWORDSDANCE', 'NASTYPLOT', 'DRAGONDANCE', 'QUIVERDANCE', 'CALMMIND', 'BULKUP', 'SHELLSMASH', 'COIL', 'HOWL', 'WORKUP', 'GROWTH',
         'CURSE', 'IRONDEFENSE', 'AGILITY', 'ROCKPOLISH', 'SHIFTGEAR', 'TAILGLOW', 'GEOMANCY', 'VICTORYDANCE', 'TIDYUP', 'FILLETAWAY', 'BELLYDRUM'}
SLEEP = {'HYPNOSIS', 'SPORE', 'SLEEPPOWDER', 'SING', 'LOVELYKISS', 'GRASSWHISTLE', 'DARKVOID', 'YAWN'}
# their win conditions -> what answers them (moves in OUR builds / abilities / types)
WIN = {
 'Speed control (Tailwind / Trick Room)': (lambda ms: ms & {'TAILWIND', 'TRICKROOM'},
     {'moves': {'TRICKROOM', 'TAILWIND', 'ICYWIND', 'ELECTROWEB', 'THUNDERWAVE', 'TAUNT', 'IMPRISON', 'GLARE', 'NUZZLE', 'SCARYFACE'}}),
 'Setup (stat boosts)': (lambda ms: ms & SETUP,
     {'moves': {'HAZE', 'CLEARSMOG', 'ROAR', 'WHIRLWIND', 'DRAGONTAIL', 'CIRCLETHROW', 'ENCORE', 'TAUNT', 'SPECTRALTHIEF', 'PARTINGSHOT', 'SNARL'},
      'abil': {'UNAWARE', 'INTIMIDATE'}}),
 'Sleep': (lambda ms: ms & SLEEP, {'moves': {'SAFEGUARD', 'MISTYTERRAIN', 'ELECTRICTERRAIN', 'SLEEPTALK'},
     'abil': {'INSOMNIA', 'VITALSPIRIT', 'SWEETVEIL', 'COMATOSE', 'PURIFYINGSALT', 'ELECTRICSURGE', 'MISTYSURGE'}}),
 'Perish trap': (lambda ms: ms & {'PERISHSONG'}, {'types': {'GHOST'}, 'abil': {'SOUNDPROOF'}}),
 'Spread attacks': (lambda ms: {m for m in ms if (MV.get(m) or {}).get('target') in SPREAD_T and int((MV.get(m) or {}).get('basedamage') or 0) > 0},
     {'moves': {'WIDEGUARD'}}),
 'Destiny Bond': (lambda ms: ms & {'DESTINYBOND'}, {'moves': {'TAUNT'}}),
 'Screens': (lambda ms: ms & {'REFLECT', 'LIGHTSCREEN', 'AURORAVEIL'}, {'moves': {'BRICKBREAK', 'PSYCHICFANGS', 'DEFOG', 'RAGINGBULL'}, 'abil': {'INFILTRATOR'}}),
}
RK = {'S': 4, 'A': 3, 'B': 2, 'C': 1, 'D': 0}
# ---- their team
FOES = G.fight_mons(FK)
TIPS = (json.load(open('team/fight_tips.json')) if os.path.exists('team/fight_tips.json') else {}).get(FK, [])
def fidx(nm): return next((k for k, f in enumerate(FOES) if f['name'] == nm), None)
def mvid(n): return BYNAME.get((n or '').lower())
fmoves = []
for f in FOES:
    ids = [mvid(n) for n in f['moves']]; fmoves.append({i for i in ids if i})
ATK = {}   # attack type -> foes using it (damaging moves; field typeMods add a 2nd type)
for f, ms in zip(FOES, fmoves):
    for m in ms:
        d = MV.get(m) or {}
        if int(d.get('basedamage') or 0) <= 0 and m not in ('NIGHTSHADE', 'SEISMICTOSS'): continue
        for t in [d.get('type')] + ([TYPEMODS[m]] if m in TYPEMODS else []):
            if t: ATK.setdefault(t, set()).add(f['name'])
MAIN = sorted([t for t, fs in ATK.items() if len(fs) >= 2 or FOES[-1]['name'] in fs], key=lambda t: -len(ATK[t]))
WINS = [(w, sorted({f['name'] for f, ms in zip(FOES, fmoves) if fn(ms)})) for w, (fn, _) in WIN.items()]
WINS = [(w, fs) for w, fs in WINS if fs]
# ---- our pool (Party + Active), engine matchups for this fight
TA = {r['name']: r for r in json.load(open('team/tier_all.json'))['rows'] if r.get('kind') != 'crest'}
IB = json.load(open('team/ideal_builds.json')) if os.path.exists('team/ideal_builds.json') else {}
run = os.environ.get('BASE_RUN') or f"r{st['run']}"
C = {c['name']: c for c in pickle.load(open(f'team/{run}{"n" if BREAK else ""}_native.json.pkl', 'rb'))['cands'] if not c.get('gate')}
POOL = [n for n, r in TA.items() if r.get('where') in ('Party', 'Active') and r['tier'] in ('S', 'A', 'B') and n in C and FK in C[n]['matchups']]
POOL += [n for n, r in TA.items() if r.get('where') == 'Overflow' and r['tier'] in ('S', 'A') and n not in POOL and n in C and FK in C[n]['matchups']]
POOL += [n for n in (st.get('team') or []) if n in TA and n not in POOL and n in C and FK in C[n]['matchups']]
# 23 Nov (Vincent): ONE main core of 4 (core4.py, general, no opponent) + 2 flexes per fight
CORE = [m['name'] for m in json.load(open('team/core4.json'))['core']] if os.path.exists('team/core4.json') and st.get('core_lock', True) else []
CORE = [n for n in CORE if n in TA and n in C and FK in C[n]['matchups']]
POOL += [n for n in CORE if n not in POOL]   # the current six stays in the pool (tiers wobble)   # 23 Nov: the S / A moving into Active
MOVE_OVR = {}   # planner-made move changes (Flash user) shown on the page
def build(n):
    b = IB.get(n) or {}
    ms = MOVE_OVR.get(n) or (st.get('moves') or {}).get(n) or b.get('moves') or TA[n].get('attacks') or []
    ab = (st.get('abilities') or {}).get(n) or b.get('ability') or TA[n].get('ability') or ''
    return {mvid(m) or m.upper().replace(' ', '') for m in ms}, ab.upper().replace(' ', ''), ms
nF = len(FOES); FN = [f['name'] for f in FOES]
TAKE, DEAL, FAST, NAMES = [], [], [], []
for n in POOL:
    mu = {x['foe']: x for x in C[n]['matchups'][FK]}
    TAKE.append([min(150, mu[f]['deff']) if f in mu else 100 for f in FN]); DEAL.append([min(150, mu[f]['off']) if f in mu else 0 for f in FN])
    FAST.append([bool(mu[f]['faster']) if f in mu else False for f in FN]); NAMES.append(n)
TAKE, DEAL, FAST = np.array(TAKE, float), np.array(DEAL, float), np.array(FAST)
MULT = np.array([[E.chart_eff(t, TA[n]['types'], FE) for t in MAIN] for n in NAMES]) if MAIN else np.zeros((len(NAMES), 0))
ALLT = sorted(ATK)
MALL = np.array([[E.chart_eff(t, TA[n]['types'], FE) for t in ALLT] for n in NAMES])
TIER = np.array([RK[TA[n]['tier']] for n in NAMES], float)
AEV = np.array(['Aevian' in n for n in NAMES], float)   # 23 Nov (Vincent): prefer Aevian forms (unique, often stronger): a tiebreak bonus
ANS = np.zeros((len(NAMES), len(WINS)))
for i, n in enumerate(NAMES):
    ms, ab, _ = build(n)
    for j, (w, _) in enumerate(WINS):
        a = WIN[w][1]
        if ms & a.get('moves', set()) or ab in a.get('abil', set()) or set(TA[n]['types']) & a.get('types', set()): ANS[i, j] = 1
SAFE = TAKE < 50          # takes under half from that foe's best move
DEAD = TAKE >= 100        # one-shot by it
# ---- 23 Nov (Vincent, after losing again): 1) RESIST THE MOVES THEY HAVE, 2) HIT EVERY FOE SUPER EFFECTIVELY (or with a field-boosted move),
# 3) LEADS that resist every attack their two leads carry. Move-level type checks with the field's type chart + second types.
ABSORB = {'FLASHFIRE': 'FIRE', 'WELLBAKEDBODY': 'FIRE', 'WATERABSORB': 'WATER', 'STORMDRAIN': 'WATER', 'DRYSKIN': 'WATER', 'VOLTABSORB': 'ELECTRIC',
          'LIGHTNINGROD': 'ELECTRIC', 'MOTORDRIVE': 'ELECTRIC', 'SAPSIPPER': 'GRASS', 'LEVITATE': 'GROUND', 'EARTHEATER': 'GROUND'}
TB = {t: float(m) for m, ts in (FT.get('typeBoosts') or {}).items() for t in ts}
DMODS = {mv: float(m) for m, ms in (FT.get('damageMods') or {}).items() for mv in ms}
def mtypes(m): d = MV.get(m) or {}; return [d.get('type')] + ([TYPEMODS[m]] if m in TYPEMODS else [])
def meff(m, types, ab=''):
    ts = mtypes(m)
    if ab in ABSORB and ABSORB[ab] in ts: return 0.0
    e = 1.0
    for t in ts:
        if t: e *= E.chart_eff(t, types, FE, m)
    return e
EM = []   # their damaging moves: (foe index, move id, weight)
for fi, ms in enumerate(fmoves):
    for m in sorted(ms):
        d = MV.get(m) or {}; bp = int(d.get('basedamage') or 0)
        if bp <= 0 and m not in ('NIGHTSHADE', 'SEISMICTOSS'): continue
        EM.append((fi, m, max(.6, min(1.5, (bp or 60) * TB.get(d.get('type'), 1) * DMODS.get(m, 1) / 100))))
ABS_ = [build(n)[1] for n in NAMES]
RM = np.array([[meff(m, TA[n]['types'], ABS_[i]) for (_, m, _) in EM] for i, n in enumerate(NAMES)])   # member x their move
W = np.array([w for (_, _, w) in EM])
# offense: each member vs each foe: super effective with a build move, or a field-boosted (x1.5+) move that lands neutral or better
OFF = np.zeros((len(NAMES), nF))
for i, n in enumerate(NAMES):
    ms, _, _ = build(n)
    for fi, f in enumerate(FOES):
        best_ = 0
        for m in ms:
            d = MV.get(m) or {}
            if int(d.get('basedamage') or 0) <= 0: continue
            e = meff(m, f['types'], (f.get('ability') or '').upper().replace(' ', ''))
            fb = TB.get(d.get('type'), 1) * DMODS.get(m, 1)
            best_ = max(best_, 2 if e >= 2 else 1.5 if (fb >= 1.5 and e >= 1) else 0)
        OFF[i, fi] = best_
L = [0, 1] if FMT == 'Doubles' else [0]
LM = [k for k, (fi, _, _) in enumerate(EM) if fi in L]   # their leads' attacks
SPR = [[mvid(m) for m in build(n)[2] if mvid(m) and (MV.get(mvid(m)) or {}).get('target') == 'AllNonUsers' and int((MV.get(mvid(m)) or {}).get('basedamage') or 0) > 0] for n in NAMES]
def ally_hit(a, b):   # a's spread moves that also hit partner b (Earthquake, Surf, Discharge...)
    e = [meff(m, TA[NAMES[b]]['types'], ABS_[b]) for m in SPR[a]]
    return max(e) if e else 0
def lead_q(p):   # every attack their leads carry: resisted by BOTH of ours (+), anything super effective on either (heavy -)
    p = list(p); r = RM[p][:, LM]
    q = (r < 1).sum() + .5 * (r == 0).sum() - 4 * (r > 1).sum() + .5 * (OFF[p][:, L] >= 2).any(0).sum() + .3 * (OFF[p][:, L] > 0).sum() / len(p)
    for nd in [t_ for tt in TIPS for t_ in tt['needs'] if t_.startswith('ko:')]:   # 23 Nov: guide says KO this lead fast
        j_ = fidx(nd[3:])
        if j_ is not None and j_ in L and DEAL[p][:, j_].sum() >= 100: q += 3
    if len(p) == 2:   # 23 Nov: a lead's spread move must not hurt its partner
        for a, b in ((p[0], p[1]), (p[1], p[0])):
            h_ = ally_hit(a, b); q -= 4 if h_ >= 2 else 1.5 if h_ > 0 else 0
    return q
NP = len(NAMES)
FLASH = np.array([bool({'FLASH', 'DAZZLINGGLEAM'} & set(TA[n].get('legal') or [])) for n in NAMES])
LQ = np.full((NP, NP), -99.0)
for i in range(NP):
    for j in range(i + 1, NP):
        if BREAK and not (FLASH[i] or FLASH[j]): continue   # break plan: a lead must carry Flash / Dazzling Gleam
        LQ[i, j] = LQ[j, i] = lead_q((i, j)) if FMT == 'Doubles' else 0
# 23 Nov (Vincent): guide TIPS for this fight (team/fight_tips.json) are part of the pick: each tip's needs -> which members meet them
TIPS = (json.load(open('team/fight_tips.json')) if os.path.exists('team/fight_tips.json') else {}).get(FK, [])
SPEEDC = {'TAILWIND', 'TRICKROOM', 'ICYWIND', 'ELECTROWEB', 'THUNDERWAVE', 'NUZZLE', 'GLARE', 'SCARYFACE', 'STRINGSHOT', 'BULLDOZE'}
ANTISLEEP_M = {'SAFEGUARD', 'TAUNT', 'MISTYTERRAIN', 'ELECTRICTERRAIN', 'SLEEPTALK'}
ANTISLEEP_A = {'INSOMNIA', 'VITALSPIRIT', 'SWEETVEIL', 'COMATOSE', 'PURIFYINGSALT', 'ELECTRICSURGE', 'MISTYSURGE'}
def fidx(nm): return next((k for k, f in enumerate(FOES) if f['name'] == nm), None)
def meets(i, need):
    """-> how this member meets the need (text) or None"""
    n = NAMES[i]; ms, ab, mnames = build(n); kind, _, arg = need.partition(':')
    mn = lambda ids: next((x for x in mnames if (mvid(x) or '') in ids), None)
    if kind == 'speed_control': return mn(SPEEDC)
    if kind == 'spread_defense': return mn({'WIDEGUARD'})
    if kind == 'spread_attack':
        return next((x for x in mnames if (MV.get(mvid(x)) or {}).get('target') in ('AllOpposing', 'AllNonUsers') and int((MV.get(mvid(x)) or {}).get('basedamage') or 0) > 0), None)
    if kind == 'anti_sleep': return mn(ANTISLEEP_M) or (ab.title() if ab in ANTISLEEP_A else None)
    if kind == 'anti_perish': return mn({'TAUNT'}) or ('Ghost type: switches out of traps' if 'GHOST' in TA[n]['types'] else None) or ('Soundproof' if ab == 'SOUNDPROOF' else None)
    if kind == 'resist': return f'resists {arg.title()}' if E.chart_eff(arg, TA[n]['types'], FE) < 1 else None
    j = fidx(arg)
    if j is None: return None
    if kind == 'answer': return f'takes {int(TAKE[i][j])}%, deals {int(DEAL[i][j])}%' if TAKE[i][j] < 50 and (DEAL[i][j] >= 60 or OFF[i][j] >= 2) else None
    if kind in ('ko', 'lead_hits'): return f'deals {int(DEAL[i][j])}%' if DEAL[i][j] >= 50 else None
    if kind == 'priority_vs':
        for x in mnames:
            d = MV.get(mvid(x)) or {}
            if int(d.get('priority') or 0) > 0 and int(d.get('basedamage') or 0) > 0 and meff(mvid(x), FOES[j]['types']) >= 1: return x
    return None
NEEDS = sorted({nd for t in TIPS for nd in t['needs']})
TM = np.array([[1 if meets(i, nd) else 0 for nd in NEEDS] for i in range(len(NAMES))]) if NEEDS else np.zeros((len(NAMES), 0))
def tips_met(ix):
    ix = list(ix); got = 0
    for k, nd in enumerate(NEEDS):
        c = TM[ix, k].sum()
        if nd.startswith('ko:'):   # two members together can take it down in the first turns
            j = fidx(nd[3:]); ok = j is not None and sorted(DEAL[ix, j])[-2:] and sum(sorted(DEAL[ix, j])[-2:]) >= 100
        elif nd.startswith('resist:'): ok = c >= 2   # 'many' priority moves: two resists
        else: ok = c >= 1
        got += ok
    return got

# 23 Nov (Vincent: 'explain your rationale for each move'): every move of the six gets a reason from the data, and an attack that does
# nothing special in this fight (no super-effective target, no field boost, no STAB) is FLAGGED so a bad move can't slip through.
WHY_STATUS = {
 'PROTECT': 'Always the 4th move: scout, stall their Tailwind turns, block double targets',
 'DETECT': 'Protect: scout and stall', 'WISH': 'Heals 50% next turn, to itself or whoever switches in',
 'WIDEGUARD': 'Blocks spread attacks for both of yours (goes first, priority +3)',
 'HELPINGHAND': "Partner's attack x1.5 (goes first, priority +5)",
 'TAILWIND': 'Doubles your Speed for 4 turns: answers their Tailwind', 'ROOST': 'Heals 50%', 'RECOVER': 'Heals 50%',
 'FLASH': 'Breaks the field for the rest of the battle (their Ghost moves lose x1.5)',
 'LOVELYKISS': 'Puts one foe to sleep (75% accurate)', 'SPORE': 'Puts one foe to sleep', 'RAGEPOWDER': 'Pulls single-target attacks to itself',
 'TRICKROOM': 'Slow Pokemon move first for 5 turns', 'SAFEGUARD': 'Blocks status for 5 turns', 'TAUNT': 'Stops status / setup moves',
 'HAZE': 'Resets all stat boosts', 'SWORDSDANCE': 'Attack +2', 'CURSE': 'Attack and Defense +1, Speed -1', 'NASTYPLOT': 'Sp. Atk +2',
 'CALMMIND': 'Sp. Atk and Sp. Def +1', 'DRAGONDANCE': 'Attack and Speed +1', 'GASTROACID': 'Removes a foe ability',
}
EXTRA = {'DELUGE': 'Goes last, power x2 (120) if that foe hit you first this turn', 'KNOCKOFF': 'Removes their item (Focus Sash, Life Orb, Ghost Gem)',
         'CLEARSMOG': 'Resets the target boosts (Luxray Howl)', 'SHADOWSNEAK': 'Priority +1: finishes a weakened foe first',
         'FAKEOUT': 'Flinches on its first turn: a free hit, x1.5 on Concert Venue',
         'GRASSYGLIDE': 'Priority +1 on Grassy Terrain: Grassy Surge sets it on entry (replaces Haunted Field for a few turns)',
         'AQUAJET': 'Priority +1', 'ROCKSLIDE': 'Spread move that never hits your partner; 30% flinch', 'EARTHQUAKE': 'Also hits your partner: only next to a Flying / Levitate partner'}
_ITEMS = [f"{f['name']} {f['item']}" for f in FOES if f.get('item') and 'Seed' not in f['item'] and 'ite' != f['item'][-3:]]
EXTRA['KNOCKOFF'] = 'Removes their item' + (' (' + ', '.join(_ITEMS) + ')' if _ITEMS else '')
_NOSLEEP = [f['name'] for f in FOES if (f.get('ability') or '').upper().replace(' ', '') in ('INSOMNIA', 'VITALSPIRIT', 'SWEETVEIL', 'COMATOSE')]
def move_why(n, mname):
    mid = mvid(mname) or mname.upper().replace(' ', ''); d = MV.get(mid) or {}
    bp = int(d.get('basedamage') or 0)
    if bp <= 0:
        w_ = WHY_STATUS.get(mid, 'Utility move')
        if mid in SLEEP and _NOSLEEP: w_ += '; not ' + ', '.join(_NOSLEEP) + ' (cannot sleep)'
        return (w_, False)
    se = [f['name'] for f in FOES if meff(mid, f['types'], (f.get('ability') or '').upper().replace(' ', '')) >= 2]
    imm = [f['name'] for f in FOES if meff(mid, f['types'], (f.get('ability') or '').upper().replace(' ', '')) == 0]
    fb = TB.get(d.get('type'), 1) * DMODS.get(mid, 1) if not BREAK else 1
    stab = d.get('type') in TA[n]['types']
    bits = []
    if se: bits.append('Super effective on ' + ', '.join(se))
    if fb > 1: bits.append(f'x{fb:g} on this field')
    if stab: bits.append('STAB')
    if d.get('target') in ('AllOpposing', 'AllNonUsers'): bits.append('hits both foes')
    if mid in EXTRA: bits.append(EXTRA[mid])
    if imm: bits.append('no effect on ' + ', '.join(imm))
    def epow(m_, f):   # effective power of move m_ on foe f: power x STAB x type x field
        d_ = MV.get(m_) or {}; b_ = int(d_.get('basedamage') or 0) * (2 if m_ == 'DELUGE' else 1)
        if b_ <= 0: return 0
        return b_ * (1.5 if d_.get('type') in TA[n]['types'] else 1) * meff(m_, f['types'], (f.get('ability') or '').upper().replace(' ', '')) * (1 if BREAK else TB.get(d_.get('type'), 1) * DMODS.get(m_, 1))
    mine = [mvid(x) or x.upper().replace(' ', '') for x in build(n)[2]]
    best_on = [f['name'] for f in FOES if epow(mid, f) > 0 and epow(mid, f) >= max(epow(x, f) for x in mine)]
    if best_on: bits.insert(0, 'Your best hit on ' + ', '.join(best_on))
    flag = not best_on and mid not in EXTRA
    return ('; '.join(bits) or 'Neutral coverage', flag)

FLAGN = np.array([sum(move_why(n, mv_)[1] for mv_ in build(n)[2]) for n in NAMES], float)   # moves that do nothing here
ind = (2 * ((RM < 1) * W).sum(1) - 3 * ((RM > 1) * W).sum(1) + 1.5 * (OFF >= 2).sum(1) + .7 * (OFF > 0).sum(1)
       + 1.5 * SAFE.sum(1) - 2 * DEAD.sum(1) + .6 * TIER + LQ.max(1).clip(-5, 99) * .5 + .8 * AEV - 4 * FLAGN)
top = list(np.argsort(-ind)[:min(24, NP)])
if BREAK:   # make sure the best Flash users are in the search
    top += [i for i in np.argsort(-ind) if FLASH[i] and i not in top][:3]
def score(ix):
    ix = list(ix); r = RM[ix]
    res = (r < 1).sum(0); weak = (r > 1).sum(0)
    s = 3 * (W * np.minimum(res, 4)).sum() - 2.5 * (W * np.maximum(weak - 1, 0)).sum() - 12 * (weak >= 3).sum() - 6 * (res == 0).sum()   # 1) defense: every move resisted by someone
    oc = (OFF[ix] >= 2).sum(0); ob = (OFF[ix] > 0).sum(0)
    s += 3 * np.minimum(oc, 2).sum() + 1 * np.minimum(ob, 3).sum() - 6 * (ob == 0).sum()   # 2) offense: super effective / field-boosted on every foe
    s += 4 * max(LQ[a][b] for a, b in itertools.combinations(ix, 2)) if FMT == 'Doubles' else 0   # 3) a lead pair that resists their leads
    if BREAK and not FLASH[ix].any(): s -= 999
    s += 3 * tips_met(ix)   # 23 Nov: the guide's tips count
    s += 1.5 * np.minimum(SAFE[ix].sum(0), 3).sum() - 4 * DEAD[ix].sum() + .4 * TIER[ix].sum() + 1.0 * AEV[ix].sum() - 4 * FLAGN[ix].sum() + 2 * (ANS[ix].max(0).sum() if len(WINS) else 0)
    return s
if len(CORE) == 4:   # core locked: every pair of flexes from the whole pool
    _ci = tuple(NAMES.index(n) for n in CORE)
    _cands = (_ci + pr for pr in itertools.combinations([i for i in range(NP) if i not in _ci], 2))
else:
    _cands = itertools.combinations(top, 6)
res = sorted(((score(ix), ix) for ix in _cands), key=lambda x: -x[0])
if os.environ.get('PLAN_SIX'):   # evaluate a given six (names | separated) instead of searching
    _fix = tuple(NAMES.index(x) for x in os.environ['PLAN_SIX'].split('|'))
    res = [(score(_fix), _fix)] + res
# 23 Nov: their field SEEDS (Battler.rb seedCheck): Haunted Magical Seed burns the holder on entry -> Guts / Flare Boost / Toxic Boost /
# Quick Feet / Marvel Scale switch on (and Facade doubles). The engine does not model foe abilities, so count it here: breaking the field
# before a NON-lead seed holder enters denies its combo (leads are burned at the start either way).
SEED_ABUSE = {'GUTS', 'FLAREBOOST', 'TOXICBOOST', 'QUICKFEET', 'MARVELSCALE'}
_seed = (FT.get('seed') or {}).get('seedtype') if FT else (G.load('fieldtext').get(FE0 or '', {}).get('seed') or {}).get('seedtype')
SEED_DENIED = [f['name'] for k, f in enumerate(FOES) if k not in L and _seed and (f.get('item') or '').upper().replace(' ', '') == _seed
               and (f.get('ability') or '').upper().replace(' ', '') in SEED_ABUSE]
KO_RACE = any(t_.startswith('ko:') and fidx(t_[3:]) in L for tt in TIPS for t_ in tt['needs'])   # Flash costs a turn in the race
def cmp_score(ix):   # field-neutral comparison of the two plans: safe switch-ins, one-shots, super-effective coverage, guide tips, denied seeds
    ix = list(ix); return float(1.5 * tips_met(ix) + (4 * len(SEED_DENIED) if BREAK else 0) - (5 if BREAK and KO_RACE else 0) + 1.5 * np.minimum(SAFE[ix].sum(0), 3).sum() - 4 * DEAD[ix].sum() + 3 * np.minimum((OFF[ix] >= 2).sum(0), 2).sum() - 2 * ((RM[ix] > 1).sum(0) >= 3).sum())
best = list(res[0][1])
if BREAK and not os.environ.get('PLAN_SIX') and os.path.exists('team/planner_keep.json'):   # 23 Nov: also try the keep plan's six with Flash
    _k = [m['name'] for m in json.load(open('team/planner_keep.json'))['six']]
    if all(x in NAMES for x in _k):
        _ki = [NAMES.index(x) for x in _k]
        if FLASH[_ki].any() and cmp_score(_ki) > cmp_score(best): best = _ki
if FMT == 'Doubles':
    leads = max(itertools.combinations(best, 2), key=lambda p: LQ[p[0]][p[1]])
    leads = tuple(sorted(leads, key=lambda i: -lead_q((i,))))
else:   # singles fight: slot 1 leads (best vs their lead), slot 2 = the doubles partner for later doubles fights
    _l1 = max(best, key=lambda i: lead_q((i,)) - TAKE[i][0] / 100)
    leads = (_l1, max([i for i in best if i != _l1], key=lambda i: lead_q((_l1, i))))
_setup_ids = {'SWORDSDANCE', 'NASTYPLOT', 'DRAGONDANCE', 'QUIVERDANCE', 'CALMMIND', 'BULKUP', 'CURSE', 'SHELLSMASH', 'COIL', 'BELLYDRUM', 'SHIFTGEAR'}
def _is_closer(i): return bool({mvid(x) for x in build(NAMES[i])[2]} & _setup_ids)
# 23 Nov (Vincent): slots 3-6 by role: mid game first, then closers; a flex closer before a core-only closer (core / flex does not matter otherwise)
order = list(leads) + sorted([i for i in best if i not in leads], key=lambda i: (_is_closer(i), NAMES[i] in CORE, -ind[i]))
FLASHER = None
if BREAK:
    fl = [i for i in leads if FLASH[i]] or [i for i in best if FLASH[i]]
    FLASHER = fl[0]
    _ms = list(build(NAMES[FLASHER])[2]); _mv = 'Flash' if 'FLASH' in (TA[NAMES[FLASHER]].get('legal') or []) else 'Dazzling Gleam'
    _cand = [m for m in _ms if m != 'Protect' and m != _mv]
    def _val(m):   # how much this move adds vs their six (super effective hits); status moves 0
        mid = mvid(m); d = MV.get(mid) or {}
        return 0 if int(d.get('basedamage') or 0) <= 0 else sum(meff(mid, f['types']) >= 2 for f in FOES) + .5
    _rep = (min(_cand, key=_val) if _cand else None) if _mv not in _ms else None   # already knows it: nothing replaced
    if _rep and _mv not in _ms: _ms[_ms.index(_rep)] = _mv
    FLASH_PLAN = dict(user=NAMES[FLASHER], move=_mv, replaces=_rep, moves=_ms)
    MOVE_OVR[NAMES[FLASHER]] = _ms
MULT = np.array([[E.chart_eff(t, TA[n]['types'], FE) for t in MAIN] for n in NAMES]) if MAIN else np.zeros((NP, 0))
alts = []
for s_, ix in res[1:40]:
    d = [NAMES[i] for i in ix if i not in best]
    if d and not any(set(d) == set(a['in']) for a in alts): alts.append(dict(score=round(float(s_), 1), **{'in': d, 'out': [NAMES[i] for i in best if i not in ix]}))
    if len(alts) >= 3: break

def tip_who(nd):
    if nd.startswith('ko:'):   # two attackers together
        j = fidx(nd[3:]); top2 = sorted(best, key=lambda i: -DEAL[i][j])[:2] if j is not None else []
        return [f"{NAMES[i]}: deals {int(DEAL[i][j])}%" for i in top2] if top2 and sum(DEAL[i][j] for i in top2) >= 100 else []
    return [f"{NAMES[i]}: {meets(i, nd)}" for i in best if meets(i, nd)]
SETUP_ = {'SWORDSDANCE', 'NASTYPLOT', 'DRAGONDANCE', 'QUIVERDANCE', 'CALMMIND', 'BULKUP', 'CURSE', 'SHELLSMASH', 'COIL', 'BELLYDRUM', 'SHIFTGEAR'}
def role_of_(i):
    if i == leads[0]: return 'Lead'
    if len(leads) > 1 and i == leads[1]: return 'Doubles lead'
    return 'Closer' if {mvid(x) for x in build(NAMES[i])[2]} & SETUP_ else 'Mid game'
def mem(i):
    ms, ab, mnames = build(NAMES[i])
    return dict(core=NAMES[i] in CORE, role=role_of_(i), name=NAMES[i], tier=TA[NAMES[i]]['tier'], types=TA[NAMES[i]]['types'], sid=TA[NAMES[i]].get('sid'), form=str(TA[NAMES[i]].get('form', '0')),
                lead=i in leads, where=TA[NAMES[i]].get('where'), moves=mnames, ability=ab,
                take=[int(x) for x in TAKE[i]], deal=[int(x) for x in DEAL[i]], worst=int(TAKE[i].max()), worst_foe=FN[int(TAKE[i].argmax())],
                safe=int(SAFE[i].sum()), mult={t: float(MULT[i][k]) for k, t in enumerate(MAIN)},
                rm=[float(x) for x in RM[i]], off=[float(x) for x in OFF[i]],
                answers=[WINS[j][0] for j in range(len(WINS)) if ANS[i, j]],
                why=[dict(move=mv_, why=move_why(NAMES[i], mv_)[0], flag=move_why(NAMES[i], mv_)[1]) for mv_ in build(NAMES[i])[2]],
                warn=[f"Earthquake-type spread moves hit {NAMES[o]}" for o in leads if o != i and i in leads and ally_hit(i, o) > 0])
# 23 Nov (Vincent): the Planner = an evaluation of his boxes for this fight. SWAPS: for each member of the six, the best
# replacements from the pool (six score with the swap); POOL FIT: every pool Pokemon rated for this fight
_b0 = score(best)
SWAPS = {}
for i in best:
    alt_ = []
    for c in range(NP):
        if c in best: continue
        t_ = [x for x in best if x != i] + [c]
        alt_.append((score(t_) - _b0, c))
    alt_.sort(key=lambda x: -x[0])
    SWAPS[NAMES[i]] = [dict(name=NAMES[c], tier=TA[NAMES[c]]['tier'], sid=TA[NAMES[c]].get('sid'), form=str(TA[NAMES[c]].get('form', '0')),
                            delta=round(float(d_), 1), res=int((RM[c] < 1).sum()), se=int((OFF[c] >= 2).sum()),
                            oneshot=[FN[j] for j in range(nF) if DEAD[c, j]]) for d_, c in alt_[:2]]
_fit = ind - FLAGN * 0   # individual value for this fight (defense first, offense, tips, flags)
_q = np.quantile(_fit, [.5, .8]) if NP > 4 else [0, 0]
POOLFIT = [dict(name=NAMES[i], tier=TA[NAMES[i]]['tier'], sid=TA[NAMES[i]].get('sid'), form=str(TA[NAMES[i]].get('form', '0')),
                fit=round(float(_fit[i]), 1), grade='Great' if _fit[i] >= _q[1] else 'Good' if _fit[i] >= _q[0] else 'Weak',
                res=int((RM[i] < 1).sum()), weak=int((RM[i] > 1).sum()), nmoves=len(EM), se=int((OFF[i] >= 2).sum()),
                oneshot=[FN[j] for j in range(nF) if DEAD[i, j]], in_six=i in best, where=TA[NAMES[i]].get('where'))
           for i in np.argsort(-_fit)]
out = dict(fight=FK, field=FIELD, fe=FE, format=FMT, foes=[dict(name=f['name'], types=f['types'], moves=f['moves'], item=f.get('item'), ability=f.get('ability'),
           sid=f['species'], form=f.get('form')) for f in FOES], main=MAIN, atk={t: sorted(v) for t, v in ATK.items()},
           wins=[dict(win=w, foes=fs, answered_by=[NAMES[i] for i in best if ANS[i, j]]) for j, (w, fs) in enumerate(WINS)],
           emoves=[dict(foe=FN[fi], move=(MV.get(m) or {}).get('name', m), types=[t for t in mtypes(m) if t], w=round(float(w), 2)) for (fi, m, w) in EM],
           lead_moves=LM,
           tips=[dict(tip=t['tip'], needs=[dict(need=nd, met_by=tip_who(nd)) for nd in t['needs']]) for t in TIPS],
           six=[mem(i) for i in order], alts=alts, swaps=SWAPS, poolfit=POOLFIT, pool=len(NAMES), score=round(float(res[0][0]), 1), cmp=round(cmp_score(best), 2),
           break_field=dict(FLASH_PLAN, denies=SEED_DENIED) if BREAK else None,
           checks=dict(weak3=[t for k, t in enumerate(ALLT) if (MALL[best][:, k] > 1).sum() >= 3],
                       nores=[t for k, t in enumerate(ALLT) if (MALL[best][:, k] < 1).sum() == 0],
                       res_lt2=[t for k, t in enumerate(MAIN) if (MULT[best][:, k] < 1).sum() < 2],
                       no_se=[FN[f] for f in range(nF) if not (OFF[best][:, f] >= 2).any()],
                       one_shot=[(NAMES[i], FN[j]) for i in best for j in range(nF) if DEAD[i, j]],
                       unanswered=[w for j, (w, _) in enumerate(WINS) if not ANS[best].max(0)[j]]))
OUTF = 'team/planner_break.json' if BREAK else 'team/planner_keep.json'
json.dump(out, open(OUTF, 'w'), indent=1, ensure_ascii=False)
_other = 'team/planner_keep.json' if BREAK else 'team/planner_break.json'
APPLY = os.environ.get('PLAN_APPLY')   # the second run decides: the plan with the higher field-neutral score wins
if APPLY:
    _o = json.load(open(_other)) if os.path.exists(_other) else None
    if not BREAKABLE:   # field can't be broken: this run IS the keep plan; drop any stale break file
        _o = None
        if os.path.exists('team/planner_break.json'): os.remove('team/planner_break.json')
    win_ = out if (not _o or out['cmp'] >= _o['cmp']) else _o
    win_['alt_plan'] = dict(cmp=(_o or out)['cmp'] if win_ is out else out['cmp'], six=[m['name'] for m in ((_o or out)['six'] if win_ is out else out['six'])],
                            break_field=bool(((_o or {}) if win_ is out else out).get('break_field')))
    json.dump(win_, open('team/planner.json', 'w'), indent=1, ensure_ascii=False)
    out = win_
if APPLY and st.get('mode') == 'planner':   # the planner's six IS the team (leads first)
    six = [m['name'] for m in out['six']]
    st['team'] = six
    if out.get('break_field'):
        st.setdefault('moves', {})[out['break_field']['user']] = out['break_field']['moves']
    for n in six:
        b = IB.get(n) or {}
        st.setdefault('moves', {})[n] = (st.get('moves') or {}).get(n) or b.get('moves') or TA[n].get('attacks') or []
        st.setdefault('abilities', {})[n] = (st.get('abilities') or {}).get(n) or b.get('ability') or TA[n].get('ability') or ''
    json.dump(st, open(STATE, 'w'), indent=1, ensure_ascii=False)
print(f"planner {FK} ({FIELD}{' BROKEN by Flash' if BREAK else ''}, {FMT}): pool {len(NAMES)} cmp {out['cmp'] if not APPLY else cmp_score(best):.1f} | six:", [NAMES[i] + (' (lead)' if i in leads else '') for i in order])
if APPLY: print('  CHOSEN:', 'break the field' if out.get('break_field') else 'keep the field', [m['name'] for m in out['six']], out.get('break_field'))
print('  main types', MAIN, '| checks', out['checks'])
