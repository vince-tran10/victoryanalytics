"""Chapter-based team rules (7 Nov). Only the HARD fights left in the chapter (boss, or 6+ opposing mons) count.
(a) hard fights = format + field from bosses/walkthrough.
(b) no attack type the opponents actually use (move types, after field type changes and -ate abilities) hits 3+ of the six SE.
(c) every such attack type is resisted/immune by >=1 member.
    'Major' types (used in 2+ hard fights, or by a boss) are hard rules; minor ones only count in the weighted exposure.
(d) every opposing Pokemon in the hard fights is hit SE by >=1 member's attack (real dual typing + immunity abilities).
Rank: passes -> battle score on the hard fights (singles x2), weighted exposure shown as tiebreak."""
import pickle, sys, os, itertools, json, collections, re
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('FORCE_FORMAT', 'native')
from engine import Engine
from bosses import FIELD
BASE = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 30
E = Engine(BASE); D = E.D
RUN = pickle.load(open(f'{BASE}/team/{os.environ.get('CR_RUN','r29')}_native.json.pkl', 'rb')); RUNN = pickle.load(open(f'{BASE}/team/{os.environ.get('CR_RUN','r29')}n_native.json.pkl', 'rb'))
IMM = {'LEVITATE': 'GROUND', 'FLASHFIRE': 'FIRE', 'WATERABSORB': 'WATER', 'STORMDRAIN': 'WATER', 'DRYSKIN': 'WATER',
       'VOLTABSORB': 'ELECTRIC', 'LIGHTNINGROD': 'ELECTRIC', 'MOTORDRIVE': 'ELECTRIC', 'SAPSIPPER': 'GRASS', 'EARTHEATER': 'GROUND',
       'WELLBAKEDBODY': 'FIRE'}
ATE = {'PIXILATE': 'FAIRY', 'REFRIGERATE': 'ICE', 'AERILATE': 'FLYING', 'GALVANIZE': 'ELECTRIC'}
ADD = {'Volcanic Top Field': {'ROCK': 'FIRE'}, 'Volcanic Top': {'ROCK': 'FIRE'}}   # field type changes
WEATHER = {'kyogre': {'WATER': 1.5, 'FIRE': 0.5}, 'manaphy': {}}
def chart(atk, types):
    m = 1.0
    for t in types:
        ch = D.chart.get(t.capitalize(), {})
        if atk in ch.get('Immunities', []): m *= 0
        elif atk in ch.get('Weaknesses', []): m *= 2
        elif atk in ch.get('Resistances', []): m *= 0.5
    return m
def eff(sig, types, ability='', crest=''):
    m = 1.0
    for t in sig:
        if IMM.get(ability) == t or (crest == 'Whiscash Crest' and t == 'GRASS'): return 0.0
        m *= chart(t, types)
    if ability in ('THICKFAT',) and set(sig) & {'FIRE', 'ICE'}: m /= 2
    return m
def sig_of(mid, mv, ability, field):
    t = mv['Type']
    if t == 'NORMAL' and ability in ATE: t = ATE[ability]
    add = (ADD.get(field) or {}).get(t)
    return (t, add) if add else (t,)
from sheet_extras import is_hard
HARD = [b for b in E.battles if is_hard(b)]
def bw(b): return b['weight'] * (2 if b['format'] == 'Singles' else 1)
def isboss(b): return 'boss' in (b['label'] + ' ' + b.get('notes', '')).lower()
# ---- threat types (what the opponents actually throw) ----
W = collections.Counter(); FIGHTS = collections.defaultdict(set); BOSS = set(); WHO = collections.defaultdict(list)
for b in HARD:
    f = FIELD.get(b['field']) or {}
    for fo in b['foes']:
        mvs = fo['moves'] if isinstance(fo['moves'], list) else eval(fo['moves'])
        seen = set()
        for mid, mv in mvs:
            if mv['Category'] == 'Status' or int(mv.get('Strength') or 0) <= 1: continue
            s = sig_of(mid, mv, fo['ability'], b['field'])
            if s in seen: continue
            seen.add(s)
            mult = f.get('types', {}).get(mv['Type'], 1) * f.get('moves', {}).get(mid, 1) * WEATHER.get(b['key'], {}).get(mv['Type'], 1)
            W[s] += bw(b) * mult / len(b['foes']); FIGHTS[s].add(b['key']); WHO[s].append(fo['name'])
            if isboss(b) and fo is b['foes'][0]: BOSS.add(s)
MAJOR = sorted(s for s in W if len(FIGHTS[s]) >= 2 or s in BOSS)
FOES = [(b['key'], fo) for b in HARD for fo in b['foes']]
# ---- pool ----
def key(c): return (c['sid'], c['form'], c['ability'])
best = {}
for c in sorted(RUN['cands'], key=lambda c: -c['solo_total']):
    if c['gate'] or (c['src']['where'] == 'Overflow' and c['name'] not in os.environ.get('ALSO_OVF', '')): continue
    best.setdefault((c['sid'], c['form']), c)
pool = sorted(best.values(), key=lambda c: -c['solo_total'])[:N]
for c in best.values():
    if c['src']['where'] == 'Party' and c not in pool: pool.append(c)
def crest(c): return c['src'].get('item') or ''
def atk_sigs(c, field=''):
    out = set()
    for mid in c['attacks']:
        mv = D.moves[mid]
        if mv['Category'] == 'Status': continue
        out.add(sig_of(mid, mv, c['ability'], field))
    return out
WK = {key(c): {s: eff(s, c['types'], c['ability'], crest(c)) >= 2 for s in W} for c in pool}
RS = {key(c): {s: eff(s, c['types'], c['ability'], crest(c)) <= .5 for s in W} for c in pool}
FB = {b['key']: b['field'] for b in HARD}
def hits(c, bk, fo):
    fty = fo['types']; ab = (fo['ability'] or '').upper().replace(' ', '')
    return any(eff(s, fty, ab) >= 2 for s in atk_sigs(c, FB[bk]))
HT = {key(c): [hits(c, bk, fo) for bk, fo in FOES] for c in pool}
byk = {key(c): c for c in pool}
nm = lambda c: c['name'].replace(' (Aevian Form)', '-A').replace(' (Aevian Form Male)', '-A').replace(' (Galarian Form)', '-Galar').replace(' (Hisuian Form)', '-Hisui')
def prep(P):
    out = {}
    for c in P['cands']:
        out[key(c)] = ({b['key']: [r['q'] for r in c['matchups'][b['key']]] for b in HARD},
                       {b['key']: sum(1 for r in c['matchups'][b['key']] if r['deff'] >= 100) / len(b['foes']) for b in HARD})
    return out
I1, I2 = prep(RUN), prep(RUNN)
TW = sum(bw(b) for b in HARD)
def sc(ks, idx):
    tot = 0
    for b in HARD:
        n = len(b['foes']); s = 0
        for i in range(n):
            qs = sorted((idx[k][0][b['key']][i] for k in ks), reverse=True); s += qs[0] + .35 * qs[1]
        tot += (s / n - .35 * sum(idx[k][1][b['key']] for k in ks) / 6) * bw(b)
    return tot / TW
def score(ks): return (sc(ks, I1) + sc(ks, I2)) / 2
def exposure(ks):   # weighted (weak - resist) over every threat type, per unit of fight weight
    return sum(W[s] * (sum(WK[k][s] for k in ks) - sum(RS[k][s] for k in ks)) for s in W) / TW
def check(ks):
    bad = []
    for s in MAJOR:
        w = sum(WK[k][s] for k in ks)
        if w >= 3: bad.append(f"{'/'.join(s)} hits {w} SE")
        if not any(RS[k][s] for k in ks): bad.append(f"{'/'.join(s)} not resisted")
    miss = [FOES[i][1]['name'] for i in range(len(FOES)) if not any(HT[k][i] for k in ks)]
    if miss: bad.append('no SE hit on ' + ', '.join(sorted(set(miss))))
    return bad
FI = {}
for i, (bk, fo) in enumerate(FOES):
    b = [b for b in HARD if b['key'] == bk][0]; FI[i] = (bk, [id(f) for f in b['foes']].index(id(fo)))
def off(k, i): return byk[k]['matchups'][FI[i][0]][FI[i][1]]['off']
def misses(ks):   # (d): not hit SE and not one-shot by anyone
    return [i for i in range(len(FOES)) if not any(HT[k][i] or off(k, i) >= 100 for k in ks)]
SHORTF = {'neved': 'Neved', 'eli': 'Eli & Sharon', 'geara': 'Geara & Zetta', 'giratina': 'Giratina', 'danni': 'Danni & Layla',
          'kyogre': 'Kyogre', 'holly': 'Holly & Rorim', 'manaphy': 'Manaphy', 'factory': '??? (Factory)', 'amber': 'Amber'}
def status(names):
    ks = list({nm(byk[k]): k for k in byk if byk[k]['name'] in names and byk[k]['src']['where'] == 'Party'}.values())
    weak3 = ['/'.join(s) for s in MAJOR if sum(WK[k][s] for k in ks) >= 3]
    nores = ['/'.join(s) for s in MAJOR if not any(RS[k][s] for k in ks)]
    ms = []
    for i in misses(ks):
        bk, fo = FOES[i]; b = max(ks, key=lambda k: off(k, i))
        ms.append({'foe': fo['name'], 'fight': SHORTF.get(bk, bk), 'best': byk[b]['name'], 'dmg': round(off(b, i))})
    return {'fights': len(HARD), 'foes': len(FOES), 'major': ['/'.join(s).title() for s in MAJOR],
            'minor': ['/'.join(s).title() for s in W if s not in MAJOR], 'weak3': weak3, 'nores': nores, 'misses': ms,
            'n_types': len(W)}
if __name__ == '__main__' and '--status' in sys.argv:
    names = json.loads(os.environ['TEAM_NAMES'])
    json.dump(status(names), open(f'{BASE}/team/chapter_status.json', 'w'), indent=1); print(json.dumps(status(names), indent=1)); sys.exit()
if __name__ == '__main__':
    print('hard fights:', [(b['key'], b['format'], b['field'], len(b['foes'])) for b in HARD])
    print('threat types (weight, fights):')
    for s, w in W.most_common(): print(f"  {'/'.join(s):14s} {w:5.2f} {'MAJOR' if s in MAJOR else 'minor'} {sorted(FIGHTS[s])}")
    print('pool', len(pool))
    keys = list(byk)
    passing = []
    for combo in itertools.combinations(keys, 6):
        ok = True
        for s in MAJOR:
            if sum(WK[k][s] for k in combo) >= 3 or not any(RS[k][s] for k in combo): ok = False; break
        if not ok: continue
        if all(any(HT[k][i] for k in combo) for i in range(len(FOES))): passing.append(combo)
    print('passing', len(passing))
    res = sorted(((score(ks), exposure(ks), ks) for ks in passing), reverse=True)
    for v, x, ks in res[:15]: print(f"{v:.4f} exp {x:+.2f}", [nm(byk[k]) for k in ks])
    cur = ['Golisopod-A', 'Annihilape', 'Glalie-A', 'Clawitzer', 'Gholdengo', 'Musharna-A']
    ck = [k for k in byk if nm(byk[k]) in cur and byk[k]['src']['where'] == 'Party']
    ck = list({nm(byk[k]): k for k in ck}.values())
    print('CURRENT', round(score(ck), 4), 'exp', round(exposure(ck), 2), check(ck))
    json.dump({'major': ['/'.join(s) for s in MAJOR], 'W': {'/'.join(s): round(w, 3) for s, w in W.items()},
               'top': [[v, x, [nm(byk[k]) for k in ks], [byk[k]['name'] for k in ks]] for v, x, ks in res[:60]],
               'current': [score(ck), exposure(ck), check(ck)]}, open(f'{BASE}/team/chapter_rules.json', 'w'), indent=1)
