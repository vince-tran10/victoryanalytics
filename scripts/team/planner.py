"""Team Planner (Vincent, 23 Nov): the best SIX from his pool (Party + Active box) for the next fight, DEFENSE FIRST.
Replaces the fixed core-of-4 + 2 flexes. Workflow it encodes:
  1 scout (their six, their attack types after the field, how they win)  2 defense first (every member survives, their main
  types resisted, nothing hits 3+)  3 answers to each win condition  4 offense second  5 leads = the pair that beats their lead
  pair. Data: per-foe matchups from the engine run (field rules incl. the type-chart overrides), types via engine.chart_eff.
usage (from workspace/): python3 -I ../scripts/team/planner.py   -> team/planner.json (+ state team when mode == 'planner')"""
import itertools, json, math, os, pickle, sys
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
# 24 Nov (Vincent, Erick 'freeze the field' tip): ALT plan = turn the field into another one with a move (fieldtext fieldChange, e.g.
# Murkwater + Blizzard -> Icy Field); the lead must carry the move; the six is scored on the new field
ALTFIELD = os.environ.get('PLAN_ALT') or ''
ALT_FE = {'Icy Field': 'ICY', 'Water Surface': 'WATERSURFACE', 'Grassy Terrain': 'GRASSY'}.get(ALTFIELD)
ALTMOVES = set(); ALTABIL = set()
if ALTFIELD and FE and ALT_FE:
    ALTMOVES = set(((G.load('fieldtext').get(FE) or {}).get('fieldChange') or {}).get(ALT_FE) or [])
    ALTABIL = {'GRASSY': {'GRASSYSURGE'}}.get(ALT_FE, set())   # 24 Nov: Grassy Surge sets Grassy Terrain on entry for 5 turns (Battler.rb 2866)
    FIELD = ALTFIELD; FE = ALT_FE
ALT = bool(ALTMOVES or ALTABIL)
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
_AB = lambda n: ((st.get('abilities') or {}).get(n) or (IB.get(n) or {}).get('ability') or '').upper().replace(' ', '')
C = {}   # 23 Nov: one engine candidate per (name, ability); keep the one whose ability the BUILD runs (Tox = Punk Rock, not Galvanize)
for c in pickle.load(open(f'team/{run}{"n" if BREAK else ""}_native.json.pkl', 'rb'))['cands']:
    if c.get('gate'): continue
    if c['name'] not in C or (c['ability'] == _AB(c['name']) and C[c['name']]['ability'] != _AB(c['name'])): C[c['name']] = c
POOL = [n for n, r in TA.items() if r.get('where') in ('Party', 'Active') and r['tier'] in ('S', 'A', 'B') and n in C and FK in C[n]['matchups']]
POOL += [n for n, r in TA.items() if r.get('where') == 'Overflow' and r['tier'] in ('S', 'A') and n not in POOL and n in C and FK in C[n]['matchups']]
POOL += [n for n in (st.get('team') or []) if n in TA and n not in POOL and n in C and FK in C[n]['matchups']]
# 23 Nov (Vincent): ONE main core of 4 (core4.py, general, no opponent) + 2 flexes per fight
CORE = [m['name'] for m in json.load(open('team/core4.json'))['core']] if os.path.exists('team/core4.json') and st.get('core_lock', True) else []
CORE = [n for n in CORE if n in TA and n in C and FK in C[n]['matchups']]
COUNTER = (st.get('builder') or 'counter') == 'counter'   # 24 Nov (Vincent): ONE dedicated hard counter per foe, our slot N vs their slot N
if COUNTER: CORE = []
POOL += [n for n in CORE if n not in POOL]   # the current six stays in the pool (tiers wobble)   # 23 Nov: the S / A moving into Active
MOVE_OVR = {}   # planner-made move changes (Flash user) shown on the page
def build(n):
    b = IB.get(n) or {}
    _pb = ((st.get('plan_builds') or {}).get(FK) or {}).get(n)
    _pb = _pb.get('moves') if isinstance(_pb, dict) else _pb
    ms = MOVE_OVR.get(n) or _pb or (st.get('base_moves') or {}).get(n) or (st.get('moves') or {}).get(n) or b.get('moves') or TA[n].get('attacks') or []
    ab = (st.get('abilities') or {}).get(n) or b.get('ability') or TA[n].get('ability') or ''
    return {mvid(m) or m.upper().replace(' ', '') for m in ms}, ab.upper().replace(' ', ''), ms
if ALT:   # re-score the pool on the new field (same engine, field swapped)
    import copy as _cp
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gamedata'))
    from fields import game_field as _gf
    engine.FIELD[ALTFIELD] = engine.FIELD.get(ALTFIELD) or _gf(ALT_FE)
    _b0 = next(b for b in E.battles if b['key'] == FK); _ba = _cp.deepcopy(_b0); _ba['field'] = ALTFIELD
    _keep = E.battles; E.battles = [_ba]
    for n in POOL:
        c = _cp.deepcopy(C[n]); ids = {mvid(x) or x.upper().replace(' ', '') for x in build(n)[2]} & set(c.get('legal') or [])
        ids = {x for x in ids if int((MV.get(x) or {}).get('basedamage') or 0) > 0}
        if ids:
            E.evaluate(c, moveset=ids); C[n] = c
    E.battles = _keep
    for b in E.battles:
        if b['key'] == FK: b['field'] = ALTFIELD
ICEBREAK = set(((G.load('fieldtext').get(FE) or {}).get('fieldChange') or {}).get('INDOOR', []) +
               sum([v for k, v in ((G.load('fieldtext').get(FE) or {}).get('fieldChange') or {}).items()], [])) if ALT else set()
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
SOUNDB = TB.pop('soundmove', 1.0) if 'soundmove' in TB else 1.0   # 23 Nov: fieldtext keys sound moves as 'soundmove', not a type
def fbm(m, ab=''):   # field (+ Punk Rock) multiplier of move m: type boost x damageMods x sound boost
    d = MV.get(m) or {}; snd = bool(d.get('soundmove'))
    f = TB.get(d.get('type'), 1) * DMODS.get(m, 1) * (SOUNDB if snd else 1)
    if snd and ab in ('PUNKROCK',): f *= 1.5 if FIELD in ('Concert Venue', 'Big Top Arena', 'Cave') and not BREAK else 1.3   # Battle_Move.rb 1845
    return f
def mtypes(m): d = MV.get(m) or {}; return [d.get('type')] + ([TYPEMODS[m]] if m in TYPEMODS else [])
def meff(m, types, ab=''):
    ts = mtypes(m)
    if ab in ABSORB and ABSORB[ab] in ts: return 0.0
    snd = bool((MV.get(m) or {}).get('soundmove'))
    if snd and ab == 'SOUNDPROOF': return 0.0
    e = .5 if snd and ab == 'PUNKROCK' else 1.0   # Punk Rock halves sound damage taken (Battle_Move.rb 1759)
    for t in ts:
        if t: e *= E.chart_eff(t, types, FE, m)
    return e
EM = []   # their damaging moves: (foe index, move id, weight)
for fi, ms in enumerate(fmoves):
    for m in sorted(ms):
        d = MV.get(m) or {}; bp = int(d.get('basedamage') or 0)
        if bp <= 0 and m not in ('NIGHTSHADE', 'SEISMICTOSS'): continue
        EM.append((fi, m, max(.6, min(1.5, (bp or 60) * fbm(m, (FOES[fi].get('ability') or '').upper().replace(' ', '')) / 100))))
ABS_ = [build(n)[1] for n in NAMES]
RM = np.array([[meff(m, TA[n]['types'], ABS_[i]) for (_, m, _) in EM] for i, n in enumerate(NAMES)])   # member x their move
W = np.array([w for (_, _, w) in EM])
# offense: each member vs each foe: super effective with a build move, or a field-boosted (x1.5+) move that lands neutral or better
OFF = np.zeros((len(NAMES), nF))
for i, n in enumerate(NAMES):
    ms, ab_, _ = build(n)
    for fi, f in enumerate(FOES):
        best_ = 0
        for m in ms:
            d = MV.get(m) or {}
            if int(d.get('basedamage') or 0) <= 0: continue
            e = meff(m, f['types'], (f.get('ability') or '').upper().replace(' ', ''))
            fb = fbm(m, ab_)
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
    for i_ in p:   # 24 Nov audit (Erick): a lead that one of their leads one-shots is not a lead
        q -= 8 * sum(1 for j_ in L if TAKE[i_][j_] >= 100) + 2 * sum(1 for j_ in L if 70 <= TAKE[i_][j_] < 100)
    if len(p) == 2:   # 23 Nov: a lead's spread move must not hurt its partner
        for a, b in ((p[0], p[1]), (p[1], p[0])):
            h_ = ally_hit(a, b); q -= 4 if h_ >= 2 else 1.5 if h_ > 0 else 0
    return q
NP = len(NAMES)
FLASH = np.array([bool({'FLASH', 'DAZZLINGGLEAM'} & set(C[n].get('legal') or [])) for n in NAMES])
ALTCAN = np.array([bool(ALTMOVES & set(C[n].get('legal') or [])) or build(n)[1] in ALTABIL for n in NAMES])   # can change the field (move or ability)
LQ = np.full((NP, NP), -99.0)
for i in range(NP):
    for j in range(i + 1, NP):
        if BREAK and not (FLASH[i] or FLASH[j]): continue   # break plan: a lead must carry Flash / Dazzling Gleam
        if ALT and not (ALTCAN[i] or ALTCAN[j]): continue   # alt-field plan: a lead must carry the field move (e.g. Blizzard)
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
 'THUNDERWAVE': 'Speed control: paralysis halves Speed, 25% full para', 'GLARE': 'Speed control: paralysis (hits Ground too)',
 'NUZZLE': 'Speed control: paralysis + chip', 'TOXIC': 'Badly poisons: beats Recover / Roost stallers (not Poison / Steel types)',
 'HAZE': 'Resets every stat change', 'YAWN': 'Sleep next turn or forces a switch', 'SING': 'Puts one foe to sleep', 'STUNSPORE': 'Speed control: paralysis',
}
EXTRA = {'DELUGE': 'Goes last, power x2 (120) if that foe hit you first this turn', 'KNOCKOFF': 'Removes their item (Focus Sash, Life Orb, Ghost Gem)',
         'CLEARSMOG': 'Resets the target boosts (Luxray Howl)', 'SHADOWSNEAK': 'Priority +1: finishes a weakened foe first',
         'FAKEOUT': 'Flinches on its first turn: a free hit, x1.5 on Concert Venue',
         'GRASSYGLIDE': 'Priority +1 on Grassy Terrain: Grassy Surge sets it on entry (replaces Haunted Field for a few turns)',
         'AQUAJET': 'Priority +1', 'ROCKSLIDE': 'Spread move that never hits your partner; 30% flinch', 'EARTHQUAKE': 'Also hits your partner: only next to a Flying / Levitate partner'}
_ITEMS = [f"{f['name']} {f['item']}" for f in FOES if f.get('item') and 'Seed' not in f['item'] and 'ite' != f['item'][-3:]]
EXTRA['KNOCKOFF'] = 'Removes their item' + (' (' + ', '.join(_ITEMS) + ')' if _ITEMS else '')
_NOSLEEP = [f['name'] for f in FOES if (f.get('ability') or '').upper().replace(' ', '') in ('INSOMNIA', 'VITALSPIRIT', 'SWEETVEIL', 'COMATOSE')]
MULTI2 = {'DOUBLEHIT', 'DUALWINGBEAT', 'DOUBLEKICK', 'DRAGONDARTS', 'TWINEEDLE', 'GEARGRIND', 'BONEMERANG', 'DOUBLEIRONBASH', 'DUALCHOP', 'TACHYONCUTTER'}
MULTI25 = {'BONERUSH', 'PINMISSILE', 'ICICLESPEAR', 'ROCKBLAST', 'BULLETSEED', 'TAILSLAP', 'SCALESHOT', 'ARMTHRUST', 'WATERSHURIKEN', 'FURYATTACK',
           'FURYSWIPES', 'DOUBLESLAP', 'COMETPUNCH', 'SPIKECANNON', 'BARRAGE'}
def hits(m_, ab):   # 24 Nov audit: multi-hit moves (Skill Link = 5 hits; else 2-5 = about 3)
    if m_ in MULTI2: return 2
    if m_ in MULTI25: return 5 if ab == 'SKILLLINK' else 3
    if m_ == 'POPULATIONBOMB': return 10 if ab == 'SKILLLINK' else 6
    if m_ in ('TRIPLEAXEL',): return 4
    return 1
UTIL_ATK = {'CLEARSMOG', 'KNOCKOFF', 'FAKEOUT', 'ICYWIND', 'ELECTROWEB', 'SNARL', 'NUZZLE', 'UTURN', 'VOLTSWITCH', 'FLIPTURN', 'RAPIDSPIN', 'MORTALSPIN',
            'ROCKTOMB', 'MUDSHOT', 'LUNGE', 'BREAKINGSWIPE', 'STRUGGLEBUG', 'MYSTICALFIRE', 'SPIRITBREAK', 'FOULPLAY', 'SUPERFANG', 'SEISMICTOSS', 'NIGHTSHADE'}
HAZ_D = {'STEALTHROCK', 'SPIKES', 'TOXICSPIKES', 'STICKYWEB', 'TOXIC'}
def move_why(n, mname):
    mid = mvid(mname) or mname.upper().replace(' ', ''); d = MV.get(mid) or {}
    bp = int(d.get('basedamage') or 0)
    if bp <= 0:
        # 23 Nov audit: a status move must do something in THIS fight too
        if mid == 'FLASH' and not BREAKABLE: return ('Flash cannot change this field: does nothing here', True)
        if mid in SLEEP and any((f.get('ability') or '').upper().replace(' ', '') in ('INSOMNIA', 'VITALSPIRIT', 'COMATOSE') for f in FOES) and all((f.get('ability') or '').upper().replace(' ', '') in ('INSOMNIA', 'VITALSPIRIT', 'COMATOSE') for f in FOES): return ('Nobody here can sleep', True)
        w_ = WHY_STATUS.get(mid, 'Utility move')
        if mid in SLEEP and _NOSLEEP: w_ += '; not ' + ', '.join(_NOSLEEP) + ' (cannot sleep)'
        if mid in ('THUNDERWAVE', 'GLARE', 'NUZZLE', 'STUNSPORE'):
            _imm = [f['name'] for j, f in enumerate(FOES) if not any(sc_on(i_, j) for i_ in [NAMES.index(n)] if (sc_on(i_, j) or '').split(' (')[0] == mname)]
            _fast = [FN[j] for j in range(nF) if FASTF[NAMES.index(n), j] and FN[j] not in _imm]
            if _fast: w_ += '; slows ' + ', '.join(_fast)
            if _imm: w_ += '; not ' + ', '.join(_imm)
        if mid in SLEEP and (FE or '').startswith('CONCERT'):   # Concert Venue: sleep fails at Hype 3+ (fieldnotetext)
            w_ += '; fails once Hype reaches 3 (their sound moves / Work Up raise it): use it early'
        return (w_, False)
    se = [f['name'] for f in FOES if meff(mid, f['types'], (f.get('ability') or '').upper().replace(' ', '')) >= 2]
    imm = [f['name'] for f in FOES if meff(mid, f['types'], (f.get('ability') or '').upper().replace(' ', '')) == 0]
    fb = fbm(mid, build(n)[1]) if not BREAK else 1
    stab = d.get('type') in TA[n]['types']
    bits = []
    if se: bits.append('Super effective on ' + ', '.join(se))
    if fb > 1: bits.append(f'x{fb:g} on this field')
    if stab: bits.append('STAB')
    if d.get('target') in ('AllOpposing', 'AllNonUsers'): bits.append('hits both foes')
    if mid in EXTRA: bits.append(EXTRA[mid])
    if imm: bits.append('no effect on ' + ', '.join(imm))
    def epow(m_, f):   # effective power of move m_ on foe f: power x STAB x type x field
        d_ = MV.get(m_) or {}; b_ = int(d_.get('basedamage') or 0) * (2 if m_ == 'DELUGE' else 1) * hits(m_, build(n)[1]) * (1.5 if m_ == 'DELUGE' else 1) / (2 if m_ == 'DELUGE' else 1)
        if b_ <= 0: return 0
        return b_ * (1.5 if d_.get('type') in TA[n]['types'] else 1) * meff(m_, f['types'], (f.get('ability') or '').upper().replace(' ', '')) * (1 if BREAK else fbm(m_, build(n)[1]))
    mine = [mvid(x) or x.upper().replace(' ', '') for x in build(n)[2]]
    best_on = [f['name'] for f in FOES if epow(mid, f) > 0 and epow(mid, f) >= max(epow(x, f) for x in mine)]
    if best_on: bits.insert(0, 'Your best hit on ' + ', '.join(best_on))
    if ALT and mid in ALTMOVES:
        return (f'Turns the field into {ALTFIELD} (turn 1)', False)
    if ALT and mid in ICEBREAK:
        return (f'Undoes {ALTFIELD}: do not use it here', True)
    if int(d.get('priority') or 0) > 0 and mid != 'FAKEOUT':   # 23 Nov audit: priority attacks have a job (Extreme Speed, Aqua Jet...)
        fast_ = [FN[j] for j in range(nF) if FASTF[NAMES.index(n), j]] if n in NAMES else []
        bits.insert(0, f'Priority +{d.get("priority")}: hits first' + (f' (they outspeed it: {", ".join(fast_[:3])})' if fast_ else ''))
    if mid == 'GRASSYGLIDE' and (FE == 'GRASSY' or build(n)[1] == 'GRASSYSURGE'): bits.insert(0, 'Priority +1 on Grassy Terrain'); best_on = best_on or ['priority']
    if mid in UTIL_ATK: best_on = best_on or ['utility']
    flag = not best_on and mid not in EXTRA and not (int(d.get('priority') or 0) > 0 and mid != 'FAKEOUT') and not (FMT == 'Doubles' and d.get('target') == 'AllOpposing')
    return ('; '.join(bits) or 'Neutral coverage', flag)

# 23 Nov (Vincent, Jenner: 'fast Boomburst wrecks me'): SPEED CONTROL by format. Singles: paralysis / priority / Trick Room
# (Tailwind lasts 4 turns for one mon); doubles: Tailwind / Trick Room / Icy Wind / Electroweb / paralysis. Per foe that outspeeds
# 4+ of the six: does someone have a tool that works on IT (Electric can't be paralysed, Ground ignores Thunder Wave...)?
SC_SINGLES = {'THUNDERWAVE', 'NUZZLE', 'GLARE', 'STUNSPORE', 'TRICKROOM', 'ICYWIND', 'ELECTROWEB', 'STICKYWEB', 'ZAPCANNON'}
SC_DOUBLES = SC_SINGLES | {'TAILWIND', 'BULLDOZE'}
SCSET = SC_SINGLES if FMT == 'Singles' else SC_DOUBLES
def sc_on(i, j):   # member i's speed tool that works on foe j (name) or None
    n = NAMES[i]; ms, ab, mnames = build(n); f = FOES[j]; ft = set(f['types']); fab = (f.get('ability') or '').upper().replace(' ', '')
    for x in mnames:
        m = mvid(x) or ''; d = MV.get(m) or {}
        if m in SCSET:
            if m in ('THUNDERWAVE', 'NUZZLE', 'ZAPCANNON') and (ft & {'ELECTRIC', 'GROUND'} or fab == 'LIMBER'): continue
            if m == 'GLARE' and ('ELECTRIC' in ft or fab == 'LIMBER'): continue
            if m == 'STUNSPORE' and ('GRASS' in ft or fab in ('OVERCOAT', 'LIMBER')): continue
            if m in ('ELECTROWEB', 'BULLDOZE') and meff(m, f['types'], fab) == 0: continue
            if m == 'STICKYWEB' and 'FLYING' in ft: continue
            return x
        if int(d.get('priority') or 0) > 0 and int(d.get('basedamage') or 0) > 0 and m != 'FAKEOUT' \
                and (meff(m, f['types'], fab) >= 2 or (d.get('type') in TA[n]['types'] and meff(m, f['types'], fab) >= 1)):
            return x + ' (priority)'
    return None
SCM = np.array([[sc_on(i, j) is not None for j in range(nF)] for i in range(NP)])
FASTF = ~FAST   # foe faster than member
FLAGN = np.array([sum(move_why(n, mv_)[1] for mv_ in build(n)[2]) for n in NAMES], float)   # moves that do nothing here
ind = (2 * ((RM < 1) * W).sum(1) - 3 * ((RM > 1) * W).sum(1) + 1.5 * (OFF >= 2).sum(1) + .7 * (OFF > 0).sum(1)
       + 1.5 * SAFE.sum(1) - 2 * DEAD.sum(1) + .6 * TIER + LQ.max(1).clip(-5, 99) * .5 + .8 * AEV - 4 * FLAGN)
top = list(np.argsort(-ind)[:min(24, NP)])
if BREAK:   # make sure the best Flash users are in the search
    top += [i for i in np.argsort(-ind) if FLASH[i] and i not in top][:3]
# 23 Nov (Vincent): SINGLES MINDSET (community_inputs.json 'mindset'; Smogon / r/stunfisk consensus). Singles only:
# layered answers (2 checks per foe), a fast revenge killer per foe, priority, pivots, Ground / Electric immunity, hazards / Knock Off
# 23 Nov (Vincent: 'Return crushed Mush after a Work Up'): a check must survive the foe AFTER its setup move (one boost turn);
# field statusBuffs add +1 (Concert Venue: Work Up / Howl = +2)
FSETUP = {'WORKUP': 1, 'HOWL': 1, 'SWORDSDANCE': 2, 'NASTYPLOT': 2, 'DRAGONDANCE': 1, 'SHIFTGEAR': 1, 'CALMMIND': 1, 'BULKUP': 1, 'QUIVERDANCE': 1,
          'COIL': 1, 'CURSE': 1, 'GROWTH': 1, 'TAILGLOW': 3, 'SHELLSMASH': 2, 'VICTORYDANCE': 1, 'CLANGOROUSSOUL': 1, 'FILLETAWAY': 2, 'TIDYUP': 1,
          'BELLYDRUM': 6, 'GEOMANCY': 2}
_SB = set((FT.get('statusBuffs') or []) if not BREAK else [])
def _fstage(ms): return max([FSETUP[m] + (1 if m in _SB else 0) for m in ms if m in FSETUP] or [0])
FSTG = [_fstage(ms) for ms in fmoves]
FSETM = [next((MV[m]['name'] for m in ms if m in FSETUP), None) for ms in fmoves]
TAKE_B = np.minimum(150, TAKE * np.array([(2 + k) / 2 for k in FSTG]))
_bt = next((b for b in E.battles if b['key'] == FK), None)
SPE_F = np.array([(f_['stats']['Spe'] * (1.5 if f_.get('item') == 'Choice Scarf' else 1) * engine.field_speed(f_, _bt)) for f_ in (_bt['foes'] if _bt else [])] or [0] * nF, float)[:nF]
SPE_M = np.array([C[n]['stats']['Spe'] * engine.field_speed(dict(C[n], ability=build(n)[1]), _bt or {}) for n in NAMES], float)   # 24 Nov: field speed rules
CHECK = (TAKE_B < 50) & ((DEAL >= 60) | (OFF >= 2))        # member checks foe: walls it after its boost and hits it hard
REVK = FAST & (DEAL >= 100)                                 # outspeeds and one-shots it
def _has(i, ids): return bool({mvid(x) for x in build(NAMES[i])[2]} & ids)
PRIO = np.array([any(int((MV.get(mvid(x)) or {}).get('priority') or 0) > 0 and int((MV.get(mvid(x)) or {}).get('basedamage') or 0) > 0
                     and mvid(x) != 'FAKEOUT' and ((MV.get(mvid(x)) or {}).get('type') in TA[n]['types'] or int((MV.get(mvid(x)) or {}).get('basedamage') or 0) >= 80) for x in build(n)[2]) for n in NAMES])
PIVOT = np.array([build(n)[1] == 'REGENERATOR' or _has(i, {'UTURN', 'VOLTSWITCH', 'FLIPTURN', 'PARTINGSHOT', 'TELEPORT', 'RECOVER', 'ROOST', 'SLACKOFF',
                  'SOFTBOILED', 'MOONLIGHT', 'SYNTHESIS', 'WISH', 'SHOREUP', 'STRENGTHSAP'}) for i, n in enumerate(NAMES)])
HAZ = np.array([_has(i, {'STEALTHROCK', 'SPIKES', 'TOXICSPIKES', 'STICKYWEB', 'KNOCKOFF'}) for i in range(NP)])
_IMM = {t: np.array([meff_t == 0 for meff_t in [E.chart_eff(t, TA[n]['types'], FE) if build(n)[1] not in
        ({'LEVITATE', 'EARTHEATER'} if t == 'GROUND' else {'VOLTABSORB', 'LIGHTNINGROD', 'MOTORDRIVE'}) else 0 for n in NAMES]]) for t in ('GROUND', 'ELECTRIC')}
# 23 Nov (Vincent): DOUBLES MINDSET (VGC guide / Smogon doubles): disruption, spread move, Wide Guard vs spread spam, no hazards
DISR = np.array([_has(i, {'FAKEOUT', 'FOLLOWME', 'RAGEPOWDER', 'SNARL', 'WILLOWISP', 'ICYWIND', 'ELECTROWEB'}) or build(n)[1] == 'INTIMIDATE'
                 for i, n in enumerate(NAMES)])
WGUARD = np.array([_has(i, {'WIDEGUARD'}) for i in range(NP)])
FOE_SPREAD = sum(1 for (fi, m, _) in EM if (MV.get(m) or {}).get('target') in ('AllOpposing', 'AllNonUsers'))
HAZ_ONLY = np.array([sum(1 for x in build(n)[2] if mvid(x) in {'STEALTHROCK', 'SPIKES', 'TOXICSPIKES', 'STICKYWEB', 'TOXIC'}) for n in NAMES])
SPRD = np.array([any((MV.get(mvid(x)) or {}).get('target') in ('AllOpposing', 'AllNonUsers') and int((MV.get(mvid(x)) or {}).get('basedamage') or 0) > 0
                     for x in build(n)[2]) for n in NAMES])
def mindset_d(ix):
    ix = list(ix)
    s = (3 if DISR[ix].any() else -3) + (2 if SPRD[ix].any() else 0) - 2 * HAZ_ONLY[ix].sum()
    if FOE_SPREAD >= 2: s += 3 if WGUARD[ix].any() else 0
    return s
# 23 Nov (Vincent, Rejuvenation core 3 + flex 3): FIELD HIJACKER = a member whose best hit on 2+ foes is a field-boosted move
def _fieldv(i):
    n = NAMES[i]; ab = build(n)[1]; c = 0
    if BREAK: return 0
    for f in FOES:
        best_, fb_ = 0, 1
        for m in build(n)[0]:
            d = MV.get(m) or {}; b_ = int(d.get('basedamage') or 0)
            if b_ <= 0: continue
            v = b_ * (1.5 if d.get('type') in TA[n]['types'] else 1) * meff(m, f['types'], (f.get('ability') or '').upper().replace(' ', '')) * fbm(m, ab)
            if v > best_: best_, fb_ = v, fbm(m, ab)
        c += best_ > 0 and fb_ >= 1.5
    return c
FIELDV = np.array([_fieldv(i) for i in range(NP)])
BOSS = 'boss' in (B9[FK][1] if FK in B9 else '').lower()
BOSSB = np.array([_has(i, {'HAZE', 'CLEARSMOG', 'PERISHSONG', 'LEECHSEED', 'GASTROACID', 'ENDEAVOR', 'TOXIC', 'CURSE', 'KNOCKOFF'})
                  or build(n)[1] == 'UNAWARE' for i, n in enumerate(NAMES)])
def para_revk(ix):   # foes that someone in ix can paralyse AND someone in ix then outspeeds (Speed / 2) and one-shots
    ix = list(ix); out = np.zeros(nF, bool)
    if not len(SPE_F): return out
    for j in range(nF):
        if SCM[ix, j].any() and any(SPE_M[i] > SPE_F[j] / 2 and DEAL[i, j] >= 100 for i in ix): out[j] = True
    return out
def mindset(ix):
    ix = list(ix); ch = CHECK[ix].sum(0); rv = REVK[ix].any(0) | para_revk(ix)
    s = 3 * (ch >= 2).sum() - 4 * (ch == 0).sum() + 2 * rv.sum() + (3 if PRIO[ix].any() else 0) + (2 if PIVOT[ix].sum() >= 2 else 0) + (1 if HAZ[ix].any() else 0)
    for t in ('GROUND', 'ELECTRIC'):
        if t in ATK and _IMM[t][ix].any(): s += 2
    return s
# 23 Nov (Vincent): the FIGHT BRIEF (chapter_brief.py): everything that makes this fight hard; the six must answer each point.
import chapter_brief as CB
BR = CB.brief(FK, CB.foe_speeds(E, FK))
BF = [f for f in BR['factors'] if f['kind'] != 'fieldnote' or ('End of turn' in f['text'] and 'Poison or Steel' in f['text'])]
FOE_BREAK = [(f['name'], MV[m]['name']) for f, ms in zip(FOES, fmoves) for m in ms if ALT and m in ICEBREAK]
if ALT:
    BF = [x for x in BF if x['kind'] not in ('fieldexploit', 'fieldblock', 'fieldnote')]   # the old field's points no longer apply
    for fn_, mv_ in FOE_BREAK:
        BF.append(dict(id=f'{FK}:break:{fn_}', fight=FK, kind='setup', foe=fn_, text=f'{fn_}: {mv_} undoes {ALTFIELD}', how='KO it first or refreeze', stage=0))
def _bmem(i):
    n = NAMES[i]
    return dict(name=n, types=TA[n]['types'], ability=build(n)[1], moves=list(build(n)[0]), spe=float(SPE_M[i]), mu={x['foe']: x for x in C[n]['matchups'].get(FK, [])})
BMEM = [_bmem(i) for i in range(NP)]
BCOV = np.array([[bool(CB.cover(f, [BMEM[i]], E, BR['tb'], FMT)) for f in BF] for i in range(NP)])   # member alone answers the point
def bcheck(ix):   # -> list of (factor, [(name, how)], ok) for the group (speed: paralysis + a teammate that then one-shots)
    mm = [BMEM[i] for i in ix]
    return [(f, cv, CB.ok(f, cv)) for f in BF for cv in [CB.cover(f, mm, E, BR['tb'], FMT)]]
_BNEED = np.array([f.get('need', 1) for f in BF]); _BBLK = np.array([f['kind'] == 'fieldblock' for f in BF]); _BNOTE = np.array([f['kind'] == 'fieldnote' for f in BF])
def bscore(ix):   # fast: member-alone covers (paralysis pairs are counted in the final check only)
    c = BCOV[list(ix)].sum(0)
    ok = np.where(_BBLK, c == 0, c >= _BNEED)
    return 4 * (ok & ~_BNOTE).sum() - 2 * (~ok & ~_BNOTE).sum() + 1 * np.minimum(c, 2)[_BNOTE].sum()
def mind_items(ix):   # 23 Nov (Vincent): the format mindset as a checklist (community_inputs.json 'mindset'), for any group
    ix = list(ix); nm = lambda xs: [NAMES[i] for i in xs]; out_ = []
    def it(ok, text, who): out_.append(dict(ok=bool(ok), text=text, who=who))
    for t in ('GROUND', 'ELECTRIC'):
        if len(ATK.get(t, ())) >= 2: w = [i for i in ix if _IMM[t][i]]; it(w, f'{t.title()} immunity ({len(ATK[t])} of them use {t.title()})', nm(w))
    if FMT == 'Singles':
        ch = CHECK[ix].sum(0); two = [FN[j] for j in range(nF) if ch[j] >= 2]; none_ = [FN[j] for j in range(nF) if ch[j] == 0]
        _imp = [f for f in none_ if not CHECK[:, FN.index(f)].any()]   # nothing in his boxes walls it after its boost and hits it hard
        it(not [f for f in none_ if f not in _imp], f'Two checks per threat: {len(two)} of {nF}',
           (['No check for ' + ', '.join(f for f in none_ if f not in _imp)] if [f for f in none_ if f not in _imp] else [])
           + (['Nothing in your boxes checks ' + ', '.join(_imp) + ': beat them on speed / priority instead'] if _imp else []))
        pr = [i for i in ix if PRIO[i]]; it(pr, 'Priority attack', nm(pr))
        pv = [i for i in ix if PIVOT[i]]; it(len(pv) >= 1, 'Safe switch (Regenerator / recovery / pivot)', nm(pv))
        sp = [i for i in ix if SCM[i].any()] + [i for i in ix if PRIO[i]]
        it(sp, 'Speed control (paralysis / priority)', nm(list(dict.fromkeys(sp))))
    else:
        d_ = [i for i in ix if DISR[i]]; it(d_, 'Disruption: Fake Out / redirection / Intimidate / Snarl / Will-O-Wisp', nm(d_))
        sc = [i for i in ix if SCM[i].any()]; it(sc, 'Speed control: Tailwind / Trick Room / Icy Wind / Electroweb / paralysis', nm(sc))
        sp = [i for i in ix if SPRD[i]]; it(sp, 'Spread attack', nm(sp))
        if FOE_SPREAD >= 2: wg = [i for i in ix if WGUARD[i]]; it(wg, f'Wide Guard (they carry {FOE_SPREAD} spread attacks)', nm(wg))
        pt = [i for i in ix if _has(i, {'PROTECT', 'DETECT', 'SPIKYSHIELD', 'KINGSSHIELD', 'BANEFULBUNKER', 'SILKTRAP'})]
        it(len(pt) >= len(ix) - 1, f'Protect on almost everyone ({len(pt)} of {len(ix)})', [])
        hz = [i for i in ix if HAZ_ONLY[i]]; it(not hz, 'No hazards / passive moves', nm(hz))
    return out_
def score(ix):
    ix = list(ix); r = RM[ix]
    res = (r < 1).sum(0); weak = (r > 1).sum(0)
    s = 3 * (W * np.minimum(res, 4)).sum() - 2.5 * (W * np.maximum(weak - 1, 0)).sum() - 12 * (weak >= 3).sum() - 6 * (res == 0).sum()   # 1) defense: every move resisted by someone
    oc = (OFF[ix] >= 2).sum(0); ob = (OFF[ix] > 0).sum(0)
    s += 3 * np.minimum(oc, 2).sum() + 1 * np.minimum(ob, 3).sum() - 6 * (ob == 0).sum()   # 2) offense: super effective / field-boosted on every foe
    s += 4 * max(LQ[a][b] for a, b in itertools.combinations(ix, 2)) if FMT == 'Doubles' else 0   # 3) a lead pair that resists their leads
    if BREAK and not FLASH[ix].any(): s -= 999
    if ALT and not ALTCAN[ix].any(): s -= 999
    if ALT and any(ALTCAN[i] and build(NAMES[i])[1] == 'SNOWWARNING' for i in ix): s += 6   # snow: the freeze can't miss (Blizzard 100%)
    s += 3 * tips_met(ix)   # 23 Nov: the guide's tips count
    s += 1.5 * np.minimum(SAFE[ix].sum(0), 3).sum() - 4 * DEAD[ix].sum() + .4 * TIER[ix].sum() + 1.0 * AEV[ix].sum() - 4 * FLAGN[ix].sum() + 2 * (ANS[ix].max(0).sum() if len(WINS) else 0)
    fastf = FASTF[ix].sum(0) >= 4   # foes that outspeed 4+ of the six
    ans_ = SCM[ix].any(0)
    s += 4 * (fastf & ans_).sum() - 4 * (fastf & ~ans_).sum()   # speed control on each fast foe
    if FMT == 'Singles': s += mindset(ix)
    else: s += mindset_d(ix)
    s += bscore(ix)
    s += 8 * sum(x['ok'] for x in mind_items(ix))   # 23 Nov (Vincent): the format mindset must be ticked off (the main check)
    s += 3 if FIELDV[ix].max() >= 2 else 0   # a field hijacker in the six
    if BOSS: s += 3 if BOSSB[ix].any() else -3
    return s
SITOUT_GAIN = 10
if len(CORE) >= 3:   # core locked (23 Nov: core of 3 + 3 flexes): every set of flexes from the strongest 30 of the pool
    _ci = tuple(NAMES.index(n) for n in CORE)
    _fp = [i for i in np.argsort(-ind) if i not in _ci][:30]
    if ALT: _fp += [i for i in np.argsort(-ind) if ALTCAN[i] and i not in _fp and i not in _ci][:4]
    _cands = [_ci + pr for pr in itertools.combinations(_fp, 6 - len(_ci))]
    # 23 Nov (Vincent): a core member may sit out THIS fight only when that is clearly better (+10 or more); the core stays the stars
    SITOUT_GAIN = 10
    _cands += [tuple(c for c in _ci if c != o) + pr for o in _ci for pr in itertools.combinations(_fp[:15], 7 - len(_ci))]
else:
    _cands = itertools.combinations(top, 6)
_CI = set(NAMES.index(n) for n in CORE) if len(CORE) >= 3 else set()
res = sorted(((score(ix) - (SITOUT_GAIN if _CI and not _CI <= set(ix) else 0), ix) for ix in _cands), key=lambda x: -x[0])
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
def cmp_score(ix):   # field-neutral comparison (alt plan: -3 per foe move that undoes the new field, -2 for the turn spent)
    return _cmp0(ix) - ((3 * len(FOE_BREAK) + (1 if ALTABIL else 2)) if ALT else 0) - (999 if ALT and not ALTCAN[list(ix)[:len(L)]].any() else 0)
def _cmp0(ix):   # field-neutral comparison of the two plans: safe switch-ins, one-shots, super-effective coverage, guide tips, denied seeds
    ix = list(ix); return float(1.5 * tips_met(ix) + (4 * len(SEED_DENIED) if BREAK else 0) - (5 if BREAK and KO_RACE else 0) + 1.5 * np.minimum(SAFE[ix].sum(0), 3).sum() - 4 * DEAD[ix].sum() + 3 * np.minimum((OFF[ix] >= 2).sum(0), 2).sum() - 2 * ((RM[ix] > 1).sum(0) >= 3).sum())
best = list(res[0][1])
# 24 Nov audit: the search only looks at the strongest 30 of the pool; polish with one-for-one swaps from the WHOLE pool until nothing improves
def _pen(t):
    out_ = len(_CI - set(t)) if _CI else 0
    return 0 if not out_ else (SITOUT_GAIN if out_ == 1 else 999)
_bv = score(best) - _pen(best)
for _it in range(12):
    _imp = False
    for i_ in list(best):
        for c_ in range(NP):
            if c_ in best: continue
            t_ = [x for x in best if x != i_] + [c_]
            v_ = score(t_) - _pen(t_)
            if v_ > _bv + 1e-9: best, _bv, _imp = t_, v_, True; break
        if _imp: break
    if not _imp: break
res = [(_bv, tuple(best))] + res
COUNTERS = []
if COUNTER:   # 24 Nov (Vincent): the six = one dedicated hard counter per foe (one-to-one), in THEIR party order
    def _q(i, j):
        hk = math.ceil(100 / max(DEAL[i][j], 1)); hd = math.ceil(100 / max(TAKE_B[i][j], 1))
        win = hk < hd or (hk == hd and FAST[i][j])
        hard = (DEAL[i][j] >= 90 or (FAST[i][j] and DEAL[i][j] >= 100)) and TAKE_B[i][j] < 70
        q = 10 * hard + 4 * win + min(DEAL[i][j], 150) / 100 - min(TAKE_B[i][j], 150) / 100 - 4 * FLAGN[i] + .3 * AEV[i] + .2 * TIER[i]
        if j < len(L) and any(TAKE[i][k] >= 100 for k in L): q -= 8   # a lead must survive both of their leads
        if ALT and j < len(L) and ALTCAN[i]: q += 6   # the freeze plan needs its field move on a lead
        return q
    QM = np.array([[_q(i, j) for j in range(nF)] for i in range(NP)])
    _cand = [list(np.argsort(-QM[:, j])[:10]) for j in range(nF)]
    _bestv, _besta = -1e9, None
    def _rec(j, used, tot, pick):
        global _bestv, _besta
        if j == nF:
            if tot > _bestv: _bestv, _besta = tot, list(pick)
            return
        for i in _cand[j]:
            if i in used: continue
            _rec(j + 1, used | {i}, tot + QM[i][j], pick + [i])
    _rec(0, set(), 0.0, [])
    best = [int(i) for i in _besta]
    for j, i in enumerate(best):
        hk = math.ceil(100 / max(DEAL[i][j], 1)); hd = math.ceil(100 / max(TAKE_B[i][j], 1))
        alts_ = [int(a) for a in np.argsort(-QM[:, j]) if a != i][:3]
        COUNTERS.append(dict(foe=FN[j], member=NAMES[i], deal=int(DEAL[i][j]), take=int(TAKE[i][j]), take_b=int(TAKE_B[i][j]), faster=bool(FAST[i][j]),
                             hard=bool((DEAL[i][j] >= 90 or (FAST[i][j] and DEAL[i][j] >= 100)) and TAKE_B[i][j] < 70),
                             win=bool(hk < hd or (hk == hd and FAST[i][j])), setup=FSETM[j],
                             alts=[dict(name=NAMES[a], deal=int(DEAL[a][j]), take_b=int(TAKE_B[a][j]), faster=bool(FAST[a][j]),
                                        hard=bool((DEAL[a][j] >= 90 or (FAST[a][j] and DEAL[a][j] >= 100)) and TAKE_B[a][j] < 70),
                                        used_for=next((FN[k] for k, x in enumerate(best) if x == a), None)) for a in alts_]))
if BREAK and not os.environ.get('PLAN_SIX') and os.path.exists('team/planner_keep.json'):   # 23 Nov: also try the keep plan's six with Flash
    _k = [m['name'] for m in json.load(open('team/planner_keep.json'))['six']]
    if all(x in NAMES for x in _k):
        _ki = [NAMES.index(x) for x in _k]
        if FLASH[_ki].any() and cmp_score(_ki) > cmp_score(best): best = _ki
if FMT == 'Doubles':
    _safe = [p for p in itertools.combinations(best, 2) if max(TAKE[i][j] for i in p for j in L) < 100 and LQ[p[0]][p[1]] > -90]   # 24 Nov: hard rule, nobody one-shot turn 1
    leads = max(_safe or list(itertools.combinations(best, 2)), key=lambda p: LQ[p[0]][p[1]] if _safe else -max(TAKE[i][j] for i in p for j in L))
    leads = tuple(sorted(leads, key=lambda i: -lead_q((i,))))
else:   # singles fight: slot 1 leads (best vs their lead), slot 2 = the doubles partner for later doubles fights
    def _lead_win(i):   # 23 Nov audit: the singles lead must WIN the opening 1-v-1 vs their lead (their setup turn counted)
        k = FSTG[0]; hk = math.ceil(100 / max(DEAL[i][0], 1)); hd_plain = math.ceil(100 / max(TAKE[i][0], 1)); hd_b = math.ceil(100 / max(TAKE_B[i][0], 1))
        if k:   # they boost on turn 1: we get a free hit, then they hit boosted
            return hk <= 1 or hk <= hd_b
        return hk < hd_plain or (hk == hd_plain and FAST[i][0])
    _l1 = max(best, key=lambda i: 5 * _lead_win(i) + DEAL[i][0] / 100 - TAKE_B[i][0] / 100 + (100 if ALT and ALTCAN[i] else 0))
    leads = (_l1,)   # 23 Nov: singles has one lead; slot 2 follows the mid game / closer order
_setup_ids = {'SWORDSDANCE', 'NASTYPLOT', 'DRAGONDANCE', 'QUIVERDANCE', 'CALMMIND', 'BULKUP', 'CURSE', 'SHELLSMASH', 'COIL', 'BELLYDRUM', 'SHIFTGEAR'}
def _is_closer(i): return bool({mvid(x) for x in build(NAMES[i])[2]} & _setup_ids)
# 23 Nov (Vincent): slots 3-6 by role: mid game first, then closers; a flex closer before a core-only closer (core / flex does not matter otherwise)
order = list(leads) + sorted([i for i in best if i not in leads], key=lambda i: (_is_closer(i), NAMES[i] in CORE, -ind[i]))
if COUNTER:   # our slot N counters their slot N: leads counter their leads
    leads = tuple(best[:len(L)]); order = list(best)
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
    if FMT == 'Doubles' and len(leads) > 1 and i == leads[1]: return 'Doubles lead'
    return 'Closer' if {mvid(x) for x in build(NAMES[i])[2]} & SETUP_ else 'Mid game'
def flex_job(i):   # 23 Nov (Rejuvenation mindset): Field hijacker / Boss breaker / Speed control / Counter
    if NAMES[i] in CORE: return None
    fl = [j for j in best if NAMES[j] not in CORE]
    if FIELDV[i] >= 2 and FIELDV[i] == max(FIELDV[j] for j in fl): return 'Field hijacker'
    if BOSS and BOSSB[i]: return 'Boss breaker'
    if SCM[i].any() and not SCM[[j for j in best if NAMES[j] in CORE]].any(0)[SCM[i]].all(): return 'Speed control'
    cj = [FN[j] for j in range(nF) if CHECK[i, j]]
    return 'Counter' + (': ' + ', '.join(cj[:2]) if cj else '')
def mem(i):
    ms, ab, mnames = build(NAMES[i])
    return dict(core=NAMES[i] in CORE, role=role_of_(i), job=flex_job(i), name=NAMES[i], tier=TA[NAMES[i]]['tier'], types=TA[NAMES[i]]['types'], sid=TA[NAMES[i]].get('sid'), form=str(TA[NAMES[i]].get('form', '0')),
                lead=i in leads, where=TA[NAMES[i]].get('where'), moves=mnames, ability=ab,
                take=[int(x) for x in TAKE[i]], deal=[int(x) for x in DEAL[i]], worst=int(TAKE[i].max()), worst_foe=FN[int(TAKE[i].argmax())],
                safe=int(SAFE[i].sum()), mult={t: float(MULT[i][k]) for k, t in enumerate(MAIN)},
                rm=[float(x) for x in RM[i]], off=[float(x) for x in OFF[i]],
                answers=[WINS[j][0] for j in range(len(WINS)) if ANS[i, j]],
                why=[dict(move=mv_, why=move_why(NAMES[i], mv_)[0], flag=move_why(NAMES[i], mv_)[1]) for mv_ in build(NAMES[i])[2]],
                warn=[f"Earthquake-type spread moves hit {NAMES[o]}" for o in leads if o != i and i in leads and ally_hit(i, o) > 0])
# 23 Nov (Vincent): the Planner = an evaluation of his boxes for this fight. SWAPS: for each member of the six, the best
# replacements from the pool (six score with the swap); POOL FIT: every pool Pokemon rated for this fight
_b0 = score(best) - _pen(best)
def pair(a, b):   # synergy of two members: shared weaknesses (-), one covers the other's weakness (+), spread move hitting the partner (-)
    s_ = 0
    for t in ALLT_18:
        ea, eb = E.chart_eff(t, TA[NAMES[a]]['types']), E.chart_eff(t, TA[NAMES[b]]['types'])
        if ea > 1 and eb > 1: s_ -= .75
        if (ea > 1 and eb < 1) or (eb > 1 and ea < 1): s_ += .5
    if FMT == 'Doubles': s_ -= 1.5 * (ally_hit(a, b) >= 2) + 1.5 * (ally_hit(b, a) >= 2)
    return s_
def pairw(a, b):
    return [f'both weak to {t.title()}' for t in ALLT_18 if E.chart_eff(t, TA[NAMES[a]]['types']) > 1 and E.chart_eff(t, TA[NAMES[b]]['types']) > 1][:1]
ALLT_18 = ['NORMAL', 'FIRE', 'WATER', 'ELECTRIC', 'GRASS', 'ICE', 'FIGHTING', 'POISON', 'GROUND', 'FLYING', 'PSYCHIC', 'BUG', 'ROCK', 'GHOST', 'DRAGON', 'DARK', 'STEEL', 'FAIRY']
SWAPS = {}
for i in best:
    alt_ = []
    for c in range(NP):
        if c in best: continue
        t_ = [x for x in best if x != i] + [c]
        alt_.append((score(t_) - _pen(t_) - _b0, c))
    alt_.sort(key=lambda x: -x[0])
    def _why_sw(c, i=i):   # 23 Nov (Vincent): considerations per swap option (what it gains / loses vs the member it replaces)
        g, l = [], []
        for j in range(nF):
            if CHECK[c, j] and not CHECK[i, j]: g.append(f'checks {FN[j]}')
            if CHECK[i, j] and not CHECK[c, j]: l.append(f'loses the check on {FN[j]}')
            if REVK[c, j] and not REVK[i, j]: g.append(f'outspeeds and one-shots {FN[j]}')
            if DEAD[c, j] and not DEAD[i, j]: l.append(f'one-shot by {FN[j]}')
            if DEAD[i, j] and not DEAD[c, j]: g.append(f'survives {FN[j]}')
        for k_, f_ in enumerate(BF):
            if f_['kind'] in ('fieldnote', 'fieldblock'): continue
            if BCOV[c, k_] and not BCOV[i, k_]: g.append('answers ' + f_['text'])
            if BCOV[i, k_] and not BCOV[c, k_] and BCOV[[j for j in best if j != i], k_].sum() < f_.get('need', 1): l.append('loses ' + f_['text'])
        if FIELDV[c] > FIELDV[i]: g.append('uses the field more')
        if FIELDV[c] < FIELDV[i]: l.append('uses the field less')
        if PRIO[c] and not PRIO[i]: g.append('priority attack')
        if SCM[c].any() and not SCM[i].any(): g.append('speed control')
        _pc = [pair(c, j) for j in best if j != i]; _pi = [pair(i, j) for j in best if j != i]
        if sum(_pc) < sum(_pi) - .5: l.append('fits the team worse (' + ', '.join(sorted({w for j in best if j != i for w in pairw(c, j)}))[:60] + ')')
        return g[:4], l[:4]
    SWAPS[NAMES[i]] = [dict(name=NAMES[c], gain=_why_sw(c)[0], loss=_why_sw(c)[1], tier=TA[NAMES[c]]['tier'], sid=TA[NAMES[c]].get('sid'), form=str(TA[NAMES[c]].get('form', '0')),
                            delta=round(float(d_), 1), res=int((RM[c] < 1).sum()), se=int((OFF[c] >= 2).sum()),
                            oneshot=[FN[j] for j in range(nF) if DEAD[c, j]]) for d_, c in [a_ for a_ in alt_ if a_[0] > -500][:3]]
_fit = ind - FLAGN * 0   # individual value for this fight (defense first, offense, tips, flags)
_q = np.quantile(_fit, [.5, .8]) if NP > 4 else [0, 0]
POOLFIT = [dict(name=NAMES[i], tier=TA[NAMES[i]]['tier'], sid=TA[NAMES[i]].get('sid'), form=str(TA[NAMES[i]].get('form', '0')),
                fit=round(float(_fit[i]), 1), grade='Great' if _fit[i] >= _q[1] else 'Good' if _fit[i] >= _q[0] else 'Weak',
                res=int((RM[i] < 1).sum()), weak=int((RM[i] > 1).sum()), nmoves=len(EM), se=int((OFF[i] >= 2).sum()),
                oneshot=[FN[j] for j in range(nF) if DEAD[i, j]], in_six=i in best, where=TA[NAMES[i]].get('where'))
           for i in np.argsort(-_fit)]
SITOUT = [n for n in CORE if NAMES.index(n) not in best] if CORE else []
SITOUT_WHY = {}
for n in SITOUT:
    SITOUT_WHY[n] = f'sits out this fight: the six without it scores {SITOUT_GAIN}+ higher'
# 23 Nov (Vincent): per-fight builds. Singles: a FLEX drops Protect for a clearly better move (the core keeps it: doubles fights remain);
# EVs / nature = what this fight needs (speed benchmarks vs their Speed, else bulk vs the side that hits it hardest), no fixed rule
FBUILD = {}
import items_owned as _IO
BOOSTER_ = _IO.BOOSTERS
def _mid(x): return mvid(x) or (x or '').upper().replace(' ', '').replace('-', '')
UTIL_D = ['SNARL', 'WILLOWISP', 'ICYWIND', 'ELECTROWEB', 'TAILWIND', 'HELPINGHAND', 'FOLLOWME', 'RAGEPOWDER', 'WIDEGUARD', 'NASTYPLOT', 'SWORDSDANCE',
          'CALMMIND', 'BULKUP', 'TAUNT', 'ENCORE', 'YAWN', 'THUNDERWAVE', 'HAZE', 'CLEARSMOG', 'ROAR']
UTIL_S = ['WILLOWISP', 'THUNDERWAVE', 'GLARE', 'NASTYPLOT', 'SWORDSDANCE', 'CALMMIND', 'BULKUP', 'DRAGONDANCE', 'TAUNT', 'ENCORE', 'YAWN', 'HAZE',
          'CLEARSMOG', 'ROAR', 'TOXIC', 'RECOVER', 'ROOST', 'SLACKOFF']
def _util(n, have):   # a support move with a job here, when no attack is the best hit on any foe
    L_ = set(C[n].get('legal') or [])
    for u in (UTIL_D if FMT == 'Doubles' else UTIL_S):
        if u in L_ and u not in have and u in MV: return u
    return None
BADSWAP = {'FOCUSPUNCH', 'HYPERBEAM', 'GIGAIMPACT', 'SKYATTACK', 'SOLARBEAM', 'SOLARBLADE', 'METEORBEAM', 'EXPLOSION', 'SELFDESTRUCT', 'MISTYEXPLOSION',
           'FUTURESIGHT', 'DOOMDESIRE', 'BELCH', 'LASTRESORT', 'DREAMEATER', 'SYNCHRONOISE', 'OUTRAGE', 'THRASH', 'PETALDANCE', 'RAGINGFURY', 'FLING',
           'NATURALGIFT', 'SNORE', 'COUNTER', 'MIRRORCOAT', 'METALBURST', 'BIDE', 'ROLLOUT', 'ICEBALL', 'FAKEOUT', 'FIRSTIMPRESSION', 'SKULLBASH',
           'RAZORWIND', 'FLY', 'DIG', 'DIVE', 'BOUNCE', 'PHANTOMFORCE', 'SHADOWFORCE', 'FREEZESHOCK', 'ICEBURN', 'GEOMANCY', 'ELECTROSHOT',
           'STEELBEAM', 'MINDBLOWN', 'CHLOROBLAST', 'HEADLONGRUSH', 'SPITUP', 'POLTERGEIST', 'UPPERHAND', 'BURNUP', 'DOUBLESHOCK', 'SUCKERPUNCH',
           'THUNDERCLAP', 'SHELLTRAP', 'BEAKBLAST', 'ROLLINGKICK', 'DYNAMICPUNCH', 'ZAPCANNON', 'INFERNO'}   # charge / recharge / self-KO / conditional / 50% accuracy
def _stat(b_, ev, mult=1.0, hp=False):
    v = (2 * b_ + 31 + ev // 4) * 60 // 100
    return int((v + 60 + 10) if hp else int((v + 5) * mult))
for i in best:
    n = NAMES[i]; ms, ab, mn = build(n); base_ = TA[n]['base']; why_ = []
    mn = list((st.get('base_moves') or {}).get(n) or (st.get('moves') or {}).get(n) or (IB.get(n) or {}).get('moves') or mn)   # 24 Nov: from the BASE build, not another fight's
    ms = {_mid(x) for x in mn}
    atk_ = [_mid(x) for x in mn if int((MV.get(_mid(x)) or {}).get('basedamage') or 0) > 0]
    phys = sum((MV.get(m) or {}).get('category') == 'physical' for m in atk_) >= sum((MV.get(m) or {}).get('category') == 'special' for m in atk_)
    def _ep(m_, f):
        d_ = MV.get(m_) or {}; b_ = int(d_.get('basedamage') or 0) * hits(m_, ab) * (1.5 if m_ == 'DELUGE' else 1)   # Deluge doubles only when hit first: count x1.5
        return b_ * (1.5 if d_.get('type') in TA[n]['types'] else 1) * meff(m_, f['types'], (f.get('ability') or '').upper().replace(' ', '')) * fbm(m_, ab) if b_ > 0 else 0
    if FMT == 'Doubles':   # 24 Nov audit: in doubles a move that also hits the PARTNER (Boomburst, Earthquake, Surf...) is swapped for a legal one that doesn't
        for slot in list(mn):
            m0 = _mid(slot)
            if (MV.get(m0) or {}).get('target') != 'AllNonUsers' or int((MV.get(m0) or {}).get('basedamage') or 0) <= 0: continue
            ids_ = [_mid(x) for x in mn if int((MV.get(_mid(x)) or {}).get('basedamage') or 0) > 0]
            keep_ = [x for x in ids_ if x != m0]; ktypes = {(MV.get(x) or {}).get('type') for x in keep_}
            cat_ = (MV.get(m0) or {}).get('category')
            cands_ = [c_ for c_ in (C[n].get('legal') or []) if int((MV.get(c_) or {}).get('basedamage') or 0) >= 60 and c_ not in BADSWAP and c_ not in keep_
                      and (MV.get(c_) or {}).get('type') not in ktypes and (MV.get(c_) or {}).get('target') != 'AllNonUsers' and (MV.get(c_) or {}).get('category') == cat_ and int((MV.get(c_) or {}).get('accuracy') or 100) >= 80]
            val = lambda c_: sum(max(_ep(c_, f), 0) for f in FOES) + (40 * len(FOES) if (MV.get(c_) or {}).get('type') not in ktypes else 0)
            _bo = lambda c_: sum(1 for f in FOES if _ep(c_, f) > 0 and _ep(c_, f) >= max([_ep(x, f) for x in keep_] or [0]))
            cands_ = [c_ for c_ in cands_ if _bo(c_) >= 1]
            bestm = max(cands_, key=lambda c_: (_bo(c_), val(c_)), default=None) or _util(n, {_mid(x) for x in mn})
            if bestm:
                mn[mn.index(slot)] = MV[bestm]['name']
                why_.append(f"{MV[bestm]['name']} replaces {slot} (doubles: {slot} also hits your partner)")
    if ALT and n in CORE:   # the core keeps its build, but never a move that undoes the field
        for slot in list(mn):
            if _mid(slot) in ICEBREAK:
                keep_ = [_mid(x) for x in mn if _mid(x) != _mid(slot) and int((MV.get(_mid(x)) or {}).get('basedamage') or 0) > 0]
                cands_ = [c_ for c_ in (C[n].get('legal') or []) if int((MV.get(c_) or {}).get('basedamage') or 0) >= 60 and c_ not in ICEBREAK and c_ not in BADSWAP and c_ not in keep_
                          and (MV.get(c_) or {}).get('category') == (MV.get(_mid(slot)) or {}).get('category') and (FMT == 'Singles' or (MV.get(c_) or {}).get('target') != 'AllNonUsers')]
                bm_ = max(cands_, key=lambda c_: sum(_ep(c_, f) for f in FOES), default=None) or _util(n, {_mid(x) for x in mn})
                if bm_: mn[mn.index(slot)] = MV[bm_]['name']; why_.append(f"{MV[bm_]['name']} replaces {slot}: {slot} would undo {ALTFIELD}")
    if n not in CORE:   # flexes are built for THIS fight: dead attacks (best hit on no foe) and, in singles, Protect make way for better moves
        legal_ = [m for m in (C[n].get('legal') or []) if int((MV.get(m) or {}).get('basedamage') or 0) >= 40 and m not in BADSWAP
                  and (MV.get(m) or {}).get('category') == ('physical' if phys else 'special') and int((MV.get(m) or {}).get('accuracy') or 100) >= 80]
        def _dead(m_, kept):
            if ALT and m_ in ICEBREAK: return True
            if m_ in UTIL_ATK: return False   # utility attacks have a job beyond damage
            if m_ == 'GRASSYGLIDE' and (FE == 'GRASSY' or build(n)[1] == 'GRASSYSURGE'): return False   # priority on Grassy Terrain
            if ALT and m_ in ALTMOVES: return False
            if FMT == 'Doubles' and (MV.get(m_) or {}).get('target') == 'AllOpposing': return False   # hits both foes: has a job in doubles
            return all(_ep(m_, f) < max([_ep(x, f) for x in kept if x != m_] or [0]) or _ep(m_, f) == 0 for f in FOES) and int((MV.get(m_) or {}).get('priority') or 0) <= 0
        for slot in list(mn):
            m0 = _mid(slot)
            is_prot = slot == 'Protect' and FMT == 'Singles' and not ({'TOXIC', 'LEECHSEED', 'WISH', 'PERISHSONG'} & ms)
            ids_ = [_mid(x) for x in mn if int((MV.get(_mid(x)) or {}).get('basedamage') or 0) > 0]
            if not (is_prot or (m0 in ids_ and _dead(m0, ids_))): continue
            keep_ = [x for x in ids_ if x != m0]; ktypes = {(MV.get(x) or {}).get('type') for x in keep_}
            gain = lambda c_: sum(max(0, _ep(c_, f) - max([_ep(x, f) for x in keep_] or [0])) for f in FOES)
            cands_ = [c_ for c_ in legal_ if c_ not in keep_ and (MV.get(c_) or {}).get('type') not in ktypes]
            bestm = max(cands_, key=gain, default=None)
            if not (bestm and gain(bestm) >= (120 if is_prot else 1)) and not is_prot:   # no attack helps: a support move with a job
                u_ = _util(n, {_mid(x) for x in mn})
                if u_:
                    mn[mn.index(slot)] = MV[u_]['name']; why_.append(f"{MV[u_]['name']} replaces {slot} (no attack of its own beats its other moves here)")
                continue
            if bestm and gain(bestm) >= (120 if is_prot else 1):
                hit_ = [f['name'] for f in FOES if _ep(bestm, f) > max([_ep(x, f) for x in keep_] or [0])]
                mn[mn.index(slot)] = MV[bestm]['name']
                why_.append(f"{MV[bestm]['name']} replaces {slot}" + (' (singles: Protect matters less)' if is_prot else ' (it was the best hit on no foe)')
                            + f": better hit on {', '.join(hit_[:3])}")
    if FMT == 'Doubles':   # 24 Nov: hazards / slow status are dead slots in doubles: a support move with a job instead
        for slot in list(mn):
            if _mid(slot) in HAZ_D:
                u_ = _util(n, {_mid(x) for x in mn})
                if u_: mn[mn.index(slot)] = MV[u_]['name']; why_.append(f"{MV[u_]['name']} replaces {slot} (doubles: hazards / Toxic are too slow)")
    if ALT and ALTMOVES and ALTCAN[i] and i == leads[0] and not (ALTMOVES & {_mid(x) for x in mn}) and build(n)[1] not in ALTABIL:   # the lead changes the field turn 1
        am_ = next(m for m in ['BLIZZARD', 'GLACIATE', 'SUBZEROSLAMMER', 'WHIRLPOOL', 'PURIFY', 'TIDYUP'] if m in ALTMOVES and m in set(C[n].get('legal') or []))
        drop_ = min([x for x in mn if x != 'Protect'], key=lambda x: sum(_ep(_mid(x), f) for f in FOES))
        mn[mn.index(drop_)] = MV[am_]['name']; why_.append(f"{MV[am_]['name']} replaces {drop_}: turns the field into {ALTFIELD} on turn 1")
    sp_ = base_['Spe']; key_ = 'Atk' if phys else 'SpA'
    s_max = _stat(sp_, 252, 1.1); s_min = _stat(sp_, 0, 1.0)
    flips = [FN[j] for j in range(nF) if s_min <= SPE_F[j] < s_max and DEAL[i][j] >= 100]   # outspeed AND one-shot is what Speed buys
    wall = (ab in ('UNAWARE', 'REGENERATOR') or {'RECOVER', 'ROOST', 'SLACKOFF', 'WISH', 'MOONLIGHT', 'SOFTBOILED', 'STRENGTHSAP'} & ms) and max(DEAL[i]) < 100
    if flips and not wall:
        evs_ = f'252 {key_} / 252 Spe / 4 HP'; nat_ = 'Jolly' if phys else 'Timid'; why_.append(f"Speed: outspeeds {', '.join(flips[:3])} only with full Speed")
    elif wall:
        sp_cnt = sum(1 for (_, m_, w_) in EM if (MV.get(m_) or {}).get('category') == 'special'); ph_cnt = len(EM) - sp_cnt
        d_ = 'SpD' if sp_cnt >= ph_cnt else 'Def'
        evs_ = f'252 HP / 252 {d_} / 4 {key_}'; nat_ = ('Careful' if phys else 'Calm') if d_ == 'SpD' else ('Impish' if phys else 'Bold')
        why_.append(f"Wall: their attacks are mostly {'special' if d_ == 'SpD' else 'physical'}")
    else:
        evs_ = f'252 HP / 252 {key_} / 4 Def'; nat_ = 'Adamant' if phys else 'Modest'
        why_.append('Bulk + power: Speed EVs change no matchup here' if s_max < max(SPE_F) else 'Bulk + power: it already outspeeds what it needs to')
    # 24 Nov: the item boosts the attack that is the best hit on the most foes in THIS fight (not the first one listed)
    _ids = [_mid(x) for x in mn if int((MV.get(_mid(x)) or {}).get('basedamage') or 0) > 0]
    _cnt = {x: sum(1 for f in FOES if _ep(x, f) > 0 and _ep(x, f) >= max(_ep(y, f) for y in _ids)) for x in _ids}
    _top = max(_ids, key=lambda x: (_cnt[x], (MV.get(x) or {}).get('type') in TA[n]['types'], int((MV.get(x) or {}).get('basedamage') or 0)), default=None)
    _cur = (IB.get(n) or {}).get('item') or ''
    item_ = _cur if (_cur.endswith('Crest') or _cur in ('Focus Sash', 'Sitrus Berry') or (st.get('items') or {}).get(n)) else (BOOSTER_.get((MV.get(_top) or {}).get('type')) if _top else _cur) or _cur
    if item_ != _cur and _top: why_.append(f"{item_}: boosts {MV[_top]['name']}, the best hit on {_cnt[_top]} of their {nF}")
    FBUILD[n] = dict(moves=mn, evs=evs_, nature=nat_, item=item_, why=why_)
_core_ix = [i for i in best if NAMES[i] in CORE]
_bc_core = {f['id']: ok for f, _, ok in bcheck(_core_ix)}
_bcc = {f['id']: cv for f, cv, _ in bcheck(_core_ix)}
BRIEF_OUT = [dict(f, cov=[[a, b] for a, b in cv], ok=ok, core_ok=_bc_core.get(f['id']), core_cov=[[a, b] for a, b in _bcc.get(f['id'], [])]) for f, cv, ok in bcheck(best)]
FLEXWHY = {NAMES[i]: [f['text'] for f, cv, ok in bcheck(best) if ok and any(a == NAMES[i] for a, _ in cv) and not _bc_core.get(f['id']) and f['kind'] not in ('fieldnote', 'fieldblock')]
           for i in best if NAMES[i] not in CORE}
MODEL_GAPS = CB.model_gaps(FK, E)
out = dict(fight=FK, counters=COUNTERS, model_gaps=MODEL_GAPS, fbuild=FBUILD, sitout=SITOUT_WHY, brief=BRIEF_OUT, flexwhy=FLEXWHY, mind_core=mind_items(_core_ix), mind_six=mind_items(best), field=FIELD, fe=FE, format=FMT, foes=[dict(name=f['name'], types=f['types'], moves=f['moves'], item=f.get('item'), ability=f.get('ability'),
           sid=f['species'], form=f.get('form')) for f in FOES], main=MAIN, atk={t: sorted(v) for t, v in ATK.items()},
           wins=[dict(win=w, foes=fs, answered_by=[NAMES[i] for i in best if ANS[i, j]]) for j, (w, fs) in enumerate(WINS)],
           emoves=[dict(foe=FN[fi], move=(MV.get(m) or {}).get('name', m), types=[t for t in mtypes(m) if t], w=round(float(w), 2)) for (fi, m, w) in EM],
           lead_moves=LM,
           mindset=dict(layered={FN[j]: [NAMES[i] for i in best if CHECK[i, j]] for j in range(nF)},
                        revenge={FN[j]: [NAMES[i] for i in best if REVK[i, j]] for j in range(nF)},
                        para={FN[j]: [NAMES[i] for i in best if SPE_M[i] > SPE_F[j] / 2 and DEAL[i, j] >= 100] for j in range(nF) if para_revk(best)[j]},
                        setup={FN[j]: [FSETM[j], FSTG[j]] for j in range(nF) if FSTG[j]},
                        speeds={FN[j]: int(SPE_F[j]) for j in range(nF)}, myspeed={NAMES[i]: int(SPE_M[i]) for i in best},
                        sc={FN[j]: [f"{NAMES[i]}: {sc_on(i, j)}" for i in best if SCM[i, j]] for j in range(nF)},
                        priority=[NAMES[i] for i in best if PRIO[i]], pivot=[NAMES[i] for i in best if PIVOT[i]],
                        hazards=[NAMES[i] for i in best if HAZ[i]],
                        immune={t: [NAMES[i] for i in best if _IMM[t][i]] for t in ('GROUND', 'ELECTRIC') if t in ATK}) if FMT == 'Singles' else None,
           speed=[dict(foe=FN[j], faster_than=int(FASTF[best][:, j].sum()), tools=[f"{NAMES[i]}: {sc_on(i, j)}" for i in best if SCM[i, j]])
                  for j in range(nF)],
           tips=[dict(tip=t['tip'], needs=[dict(need=nd, met_by=tip_who(nd)) for nd in t['needs']]) for t in TIPS],
           six=[mem(i) for i in order], alts=alts, swaps=SWAPS, poolfit=POOLFIT, pool=len(NAMES), score=round(float(res[0][0]), 1), cmp=round(cmp_score(best), 2),
           break_field=dict(FLASH_PLAN, denies=SEED_DENIED) if BREAK else None,
           checks=dict(weak3=[t for k, t in enumerate(ALLT) if (MALL[best][:, k] > 1).sum() >= 3],
                       nores=[t for k, t in enumerate(ALLT) if (MALL[best][:, k] < 1).sum() == 0],
                       res_lt2=[t for k, t in enumerate(MAIN) if (MULT[best][:, k] < 1).sum() < 2],
                       no_se=[FN[f] for f in range(nF) if not (OFF[best][:, f] >= 2).any()],
                       one_shot=[(NAMES[i], FN[j]) for i in best for j in range(nF) if DEAD[i, j]],
                       unanswered=[w for j, (w, _) in enumerate(WINS) if not ANS[best].max(0)[j]]))
out['plan'] = 'alt' if ALT else 'break' if BREAK else 'keep'
out['alt_field'] = ALTFIELD if ALT else None
out['foe_break'] = FOE_BREAK if ALT else []
OUTF = f'team/planner_alt_{ALT_FE}.json' if ALT else 'team/planner_break.json' if BREAK else 'team/planner_keep.json'
json.dump(out, open(OUTF, 'w'), indent=1, ensure_ascii=False)
_other = 'team/planner_keep.json' if BREAK else 'team/planner_break.json'
APPLY = os.environ.get('PLAN_APPLY')   # the second run decides: the plan with the higher field-neutral score wins
if APPLY:
    if not BREAKABLE and os.path.exists('team/planner_break.json') and not BREAK: os.remove('team/planner_break.json')
    import glob as _gl
    _plans = [out] + [json.load(open(f_)) for f_ in ['team/planner_keep.json', 'team/planner_break.json'] + sorted(_gl.glob('team/planner_alt_*.json'))
                      if os.path.exists(f_) and f_ != OUTF and json.load(open(f_)).get('fight') == FK]
    win_ = max(_plans, key=lambda p_: p_['cmp'])   # 24 Nov: keep / break / alt field: the best field-neutral score wins
    _o = next((p_ for p_ in _plans if p_ is not win_), None)
    win_['alt_plan'] = dict(cmp=(_o or out)['cmp'] if win_ is out else out['cmp'], six=[m['name'] for m in ((_o or out)['six'] if win_ is out else out['six'])],
                            break_field=bool(((_o or {}) if win_ is out else out).get('break_field')))
    json.dump(win_, open('team/planner.json', 'w'), indent=1, ensure_ascii=False)
    out = win_
if APPLY and st.get('mode') == 'planner':   # the planner's six IS the team (leads first)
    six = [m['name'] for m in out['six']]
    st['team'] = six
    if out.get('break_field'):
        st.setdefault('moves', {})[out['break_field']['user']] = out['break_field']['moves']
    _fb = out.get('fbuild') or {}
    for n, fb in _fb.items():
        bm = (st.get('base_moves') or {}).get(n) or (st.get('moves') or {}).get(n) or (IB.get(n) or {}).get('moves')
        st.setdefault('plan_builds', {}).setdefault(FK, {}).pop(n, None)
        if fb['moves'] != bm:
            st.setdefault('base_moves', {})[n] = bm; st['plan_builds'][FK][n] = dict(moves=fb['moves'], ability=(st.get('abilities') or {}).get(n) or (IB.get(n) or {}).get('ability')); st['moves'][n] = fb['moves']
        elif n in (st.get('base_moves') or {}):
            st['moves'][n] = st['base_moves'][n]
        if n in IB: IB[n].update(evs=fb['evs'], nature=fb['nature'], fight_why=fb['why'], moves=st['moves'].get(n, IB[n].get('moves')), item=fb.get('item') or IB[n].get('item'))
    json.dump(IB, open('team/ideal_builds.json', 'w'), indent=1, ensure_ascii=False)
    for n in six:
        b = IB.get(n) or {}
        st.setdefault('moves', {})[n] = (st.get('moves') or {}).get(n) or b.get('moves') or TA[n].get('attacks') or []
        st.setdefault('abilities', {})[n] = (st.get('abilities') or {}).get(n) or b.get('ability') or TA[n].get('ability') or ''
    json.dump(st, open(STATE, 'w'), indent=1, ensure_ascii=False)
print(f"planner {FK} ({FIELD}{' BROKEN by Flash' if BREAK else ''}, {FMT}): pool {len(NAMES)} cmp {out['cmp'] if not APPLY else cmp_score(best):.1f} | six:", [NAMES[i] + (' (lead)' if i in leads else '') for i in order])
if APPLY: print('  CHOSEN:', 'break the field' if out.get('break_field') else 'keep the field', [m['name'] for m in out['six']], out.get('break_field'))
print('  main types', MAIN, '| checks', out['checks'])
