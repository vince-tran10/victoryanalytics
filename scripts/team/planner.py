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
BREAK = bool(os.environ.get('PLAN_BREAK')) and FE is not None   # 23 Nov: lead a Flash / Dazzling Gleam user, fight on no field
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
POOL += [n for n, r in TA.items() if r.get('where') == 'Overflow' and r['tier'] in ('S', 'A') and n not in POOL and n in C and FK in C[n]['matchups']]   # 23 Nov: the S / A moving into Active
def build(n):
    b = IB.get(n) or {}
    ms = (st.get('moves') or {}).get(n) or b.get('moves') or TA[n].get('attacks') or []
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
ind = (2 * ((RM < 1) * W).sum(1) - 3 * ((RM > 1) * W).sum(1) + 1.5 * (OFF >= 2).sum(1) + .7 * (OFF > 0).sum(1)
       + 1.5 * SAFE.sum(1) - 2 * DEAD.sum(1) + .6 * TIER + LQ.max(1).clip(-5, 99) * .5)
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
    s += 1.5 * np.minimum(SAFE[ix].sum(0), 3).sum() - 4 * DEAD[ix].sum() + .4 * TIER[ix].sum() + 2 * (ANS[ix].max(0).sum() if len(WINS) else 0)
    return s
res = sorted(((score(ix), ix) for ix in itertools.combinations(top, 6)), key=lambda x: -x[0])
def cmp_score(ix):   # field-neutral comparison of the two plans: safe switch-ins, one-shots, super-effective coverage
    ix = list(ix); return float(1.5 * np.minimum(SAFE[ix].sum(0), 3).sum() - 4 * DEAD[ix].sum() + 3 * np.minimum((OFF[ix] >= 2).sum(0), 2).sum() - 2 * ((RM[ix] > 1).sum(0) >= 3).sum())
best = list(res[0][1])
leads = max(itertools.combinations(best, 2), key=lambda p: LQ[p[0]][p[1]]) if FMT == 'Doubles' else (max(best, key=lambda i: -TAKE[i][0]),)
order = list(leads) + sorted([i for i in best if i not in leads], key=lambda i: -ind[i])
FLASHER = None
if BREAK:
    fl = [i for i in leads if FLASH[i]] or [i for i in best if FLASH[i]]
    FLASHER = fl[0]
    _ms = list(build(NAMES[FLASHER])[2]); _mv = 'Flash' if 'FLASH' in (TA[NAMES[FLASHER]].get('legal') or []) else 'Dazzling Gleam'
    _cand = [m for m in _ms if m != 'Protect' and m != _mv]
    def _val(m):   # how much this move adds vs their six (super effective hits); status moves 0
        mid = mvid(m); d = MV.get(mid) or {}
        return 0 if int(d.get('basedamage') or 0) <= 0 else sum(meff(mid, f['types']) >= 2 for f in FOES) + .5
    _rep = min(_cand, key=_val) if _cand else None
    if _rep and _mv not in _ms: _ms[_ms.index(_rep)] = _mv
    FLASH_PLAN = dict(user=NAMES[FLASHER], move=_mv, replaces=_rep, moves=_ms)
MULT = np.array([[E.chart_eff(t, TA[n]['types'], FE) for t in MAIN] for n in NAMES]) if MAIN else np.zeros((NP, 0))
alts = []
for s_, ix in res[1:40]:
    d = [NAMES[i] for i in ix if i not in best]
    if d and not any(set(d) == set(a['in']) for a in alts): alts.append(dict(score=round(float(s_), 1), **{'in': d, 'out': [NAMES[i] for i in best if i not in ix]}))
    if len(alts) >= 3: break
def mem(i):
    ms, ab, mnames = build(NAMES[i])
    return dict(name=NAMES[i], tier=TA[NAMES[i]]['tier'], types=TA[NAMES[i]]['types'], sid=TA[NAMES[i]].get('sid'), form=str(TA[NAMES[i]].get('form', '0')),
                lead=i in leads, where=TA[NAMES[i]].get('where'), moves=mnames, ability=ab,
                take=[int(x) for x in TAKE[i]], deal=[int(x) for x in DEAL[i]], worst=int(TAKE[i].max()), worst_foe=FN[int(TAKE[i].argmax())],
                safe=int(SAFE[i].sum()), mult={t: float(MULT[i][k]) for k, t in enumerate(MAIN)},
                rm=[float(x) for x in RM[i]], off=[float(x) for x in OFF[i]],
                answers=[WINS[j][0] for j in range(len(WINS)) if ANS[i, j]],
                warn=[f"Earthquake-type spread moves hit {NAMES[o]}" for o in leads if o != i and i in leads and ally_hit(i, o) > 0])
out = dict(fight=FK, field=FIELD, fe=FE, format=FMT, foes=[dict(name=f['name'], types=f['types'], moves=f['moves'], item=f.get('item'), ability=f.get('ability'),
           sid=f['species'], form=f.get('form')) for f in FOES], main=MAIN, atk={t: sorted(v) for t, v in ATK.items()},
           wins=[dict(win=w, foes=fs, answered_by=[NAMES[i] for i in best if ANS[i, j]]) for j, (w, fs) in enumerate(WINS)],
           emoves=[dict(foe=FN[fi], move=(MV.get(m) or {}).get('name', m), types=[t for t in mtypes(m) if t], w=round(float(w), 2)) for (fi, m, w) in EM],
           lead_moves=LM,
           six=[mem(i) for i in order], alts=alts, pool=len(NAMES), score=round(float(res[0][0]), 1), cmp=round(cmp_score(best), 2),
           break_field=FLASH_PLAN if BREAK else None,
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
