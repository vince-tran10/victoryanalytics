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
C = {c['name']: c for c in pickle.load(open(f'team/{run}_native.json.pkl', 'rb'))['cands'] if not c.get('gate')}
POOL = [n for n, r in TA.items() if r.get('where') in ('Party', 'Active') and r['tier'] in ('S', 'A', 'B') and n in C and FK in C[n]['matchups']]
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
BEAT = (DEAL >= 100) | ((DEAL >= 50) & FAST) | (DEAL >= 60) & ~DEAD
# individual value -> prefilter (defense counts double offense)
ind = 3 * SAFE.sum(1) - 4 * DEAD.sum(1) + 1.2 * BEAT.sum(1) + .8 * TIER + .5 * (MULT < 1).sum(1) - .5 * (MULT > 1).sum(1) + 1.5 * ANS.sum(1)
top = list(np.argsort(-ind)[:min(24, len(NAMES))])
def score(ix):
    ix = list(ix)
    safe = np.minimum(SAFE[ix].sum(0), 3).sum(); dead = DEAD[ix].sum()
    beat = np.minimum(BEAT[ix].sum(0), 2).sum()
    weak = (MULT[ix] > 1).sum(0); res = (MULT[ix] < 1).sum(0)
    ans = (ANS[ix].max(0) if len(WINS) else np.zeros(0)).sum()
    s = 3 * safe - 4 * dead + 1.5 * beat + .6 * TIER[ix].sum() + 3 * ans
    s -= 8 * ((MALL[ix] > 1).sum(0) >= 3).sum() + 3 * (res < 2).sum() + 4 * ((MALL[ix] < 1).sum(0) == 0).sum()   # all their types: none hits 3, each resisted once; main types resisted twice
    s -= 4 * (np.minimum(SAFE[ix].sum(0), 3) == 0).sum()   # a foe nobody can take a hit from
    return s
res = sorted(((score(ix), ix) for ix in itertools.combinations(top, 6)), key=lambda x: -x[0])
best = list(res[0][1])
# leads: the pair that handles THEIR lead pair (doubles) / their lead (singles): least damage taken, then damage dealt, speed
L = [0, 1] if FMT == 'Doubles' else [0]
def lead_q(p):
    p = list(p)
    return -TAKE[p][:, L].max() / 100 + .5 * DEAL[p][:, L].max(0).sum() / 100 + .2 * FAST[p][:, L].mean() + .3 * ANS[p].max(0).sum()
leads = max(itertools.combinations(best, 2 if FMT == 'Doubles' else 1), key=lead_q)
order = list(leads) + sorted([i for i in best if i not in leads], key=lambda i: -ind[i])
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
                answers=[WINS[j][0] for j in range(len(WINS)) if ANS[i, j]])
out = dict(fight=FK, field=FIELD, fe=FE, format=FMT, foes=[dict(name=f['name'], types=f['types'], moves=f['moves'], item=f.get('item'), ability=f.get('ability'),
           sid=f['species'], form=f.get('form')) for f in FOES], main=MAIN, atk={t: sorted(v) for t, v in ATK.items()},
           wins=[dict(win=w, foes=fs, answered_by=[NAMES[i] for i in best if ANS[i, j]]) for j, (w, fs) in enumerate(WINS)],
           six=[mem(i) for i in order], alts=alts, pool=len(NAMES), score=round(float(res[0][0]), 1),
           checks=dict(weak3=[t for k, t in enumerate(ALLT) if (MALL[best][:, k] > 1).sum() >= 3],
                       nores=[t for k, t in enumerate(ALLT) if (MALL[best][:, k] < 1).sum() == 0],
                       res_lt2=[t for k, t in enumerate(MAIN) if (MULT[best][:, k] < 1).sum() < 2],
                       one_shot=[(NAMES[i], FN[j]) for i in best for j in range(nF) if DEAD[i, j]],
                       unanswered=[w for j, (w, _) in enumerate(WINS) if not ANS[best].max(0)[j]]))
json.dump(out, open('team/planner.json', 'w'), indent=1, ensure_ascii=False)
if st.get('mode') == 'planner':   # the planner's six IS the team (leads first)
    six = [NAMES[i] for i in order]
    st['team'] = six
    for n in six:
        b = IB.get(n) or {}
        st.setdefault('moves', {})[n] = (st.get('moves') or {}).get(n) or b.get('moves') or TA[n].get('attacks') or []
        st.setdefault('abilities', {})[n] = (st.get('abilities') or {}).get(n) or b.get('ability') or TA[n].get('ability') or ''
    json.dump(st, open(STATE, 'w'), indent=1, ensure_ascii=False)
print(f"planner {FK} ({FIELD}, {FMT}): pool {len(NAMES)} | six:", [NAMES[i] + (' (lead)' if i in leads else '') for i in order])
print('  main types', MAIN, '| checks', out['checks'])
