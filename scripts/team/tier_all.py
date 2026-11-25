"""One blended tier score for every owned Pokémon (Vincent, 16 Nov): crests, Aevians and regular Pokémon on ONE scale.
  fight   = measured solo score on the remaining hard fights (exact game data + fields), as a percentile of the owned pool
  general = competitive power: Smogon tier/usage (singles + doubles; Aevians from their kit's OP stars), base-stat total
  blend   = 0.6 fight + 0.4 general -> tiers S/A/B/C/D by fixed cut-offs.
Also stores per-fight scores and the Ch9 foes each Pokémon counters (>= 90% dealt, < 70% taken) for the Cores tab.
usage (from workspace/): BASE_RUN=r103 CREST_RUN=rc103 DONE=... python3 -I ../scripts/team/tier_all.py  -> team/tier_all.json"""
import json, os, pickle, re, sys
sys.argv = ['x', '.', '20']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('CR_RUN', os.environ.get('BASE_RUN', 'r103'))
import chapter_rules as C, crests, smogon_meta as SM

# Aevian kits have no Smogon data: OP stars (kits.KIT) stand in for the meta tier
AEV_OP = {'Golisopod': 3, 'Veluza': 3, 'Glalie': 2, 'Lapras': 2, 'Musharna': 2, 'Drapion': 2, 'Froslass': 2, 'Parasect': 2}   # Parasect-A: Resuscitation = second life as Zombie Ghost (130 Atk / 105 Spe)
TIER_W = {'gen9ubers': 1.0, 'gen9nationaldexubers': 1.0, 'gen9ou': .9, 'gen9nationaldex': .85, 'gen9doublesou': .9,
          'gen9nationaldexdoubles': .8, 'gen9uu': .72, 'gen9nationaldexuu': .68, 'gen9ru': .58, 'gen9nu': .45}
LABEL = {'gen9ubers': 'Ubers', 'gen9nationaldexubers': 'NatDex Ubers', 'gen9ou': 'OU', 'gen9nationaldex': 'NatDex OU',
         'gen9doublesou': 'Doubles OU', 'gen9nationaldexdoubles': 'NatDex Doubles', 'gen9uu': 'UU', 'gen9nationaldexuu': 'NatDex UU',
         'gen9ru': 'RU', 'gen9nu': 'NU'}


def solo(c, fights=None):
    tot = tw = 0
    for b in (fights or C.HARD):
        rows = c['matchups'][b['key']]; n = len(rows)
        v = sum(r['q'] for r in rows) / n - .35 * sum(r['deff'] >= 100 for r in rows) / n
        w = C.bw(b); tot += v * w; tw += w
    return tot / tw


def per_fight(c):
    return {b['key']: round(solo(c, [b]), 3) for b in C.HARD}


SETUP_X = {'SWORDSDANCE': 2, 'NASTYPLOT': 2, 'BELLYDRUM': 4, 'SHELLSMASH': 2, 'FILLETAWAY': 2, 'DRAGONDANCE': 1.5, 'SHIFTGEAR': 1.5,
           'QUIVERDANCE': 1.5, 'CALMMIND': 1.5, 'BULKUP': 1.5, 'COIL': 1.5, 'VICTORYDANCE': 1.5, 'TIDYUP': 1.5}
PHYS = {'SWORDSDANCE', 'BELLYDRUM', 'SHELLSMASH', 'FILLETAWAY', 'DRAGONDANCE', 'SHIFTGEAR', 'BULKUP', 'COIL', 'VICTORYDANCE', 'TIDYUP'}
SPEC = {'NASTYPLOT', 'SHELLSMASH', 'FILLETAWAY', 'QUIVERDANCE', 'CALMMIND'}


def counters(c):
    # 17 Nov: a setup move counts too: deals >= 90% after ONE setup turn while taking < 50% (survives the setup turn + the hit)
    sx = max((SETUP_X[m] for m in c['legal'] if m in SETUP_X and m in (PHYS if c['cat'] == 'Physical' else SPEC)), default=1)
    out = []
    for b in C.HARD:
        for r in c['matchups'][b['key']]:
            if (r['off'] >= 90 and r['deff'] < 70) or (r.get('faster') and r['off'] >= 100) or (sx > 1 and r['off'] * sx >= 90 and r['deff'] < 50):
                out.append(f"{b['key']}:{r['foe']}")
    return sorted(set(out))


FW = {'gen9ou-1695': 1.0, 'gen9nationaldex-1630': .95, 'gen9uu-1630': .62, 'gen9nationaldexuu-1630': .58, 'gen9ru-1630': .42, 'gen9nu-1630': .3,
      'gen9doublesou-1695': 1.0, 'gen9vgc2024regg-1630': 1.0, 'gen9nationaldexdoubles-1500': .9}
FLAB = {'gen9ou-1695': 'OU', 'gen9nationaldex-1630': 'NatDex OU', 'gen9uu-1630': 'UU', 'gen9nationaldexuu-1630': 'NatDex UU', 'gen9ru-1630': 'RU',
        'gen9nu-1630': 'NU', 'gen9doublesou-1695': 'Doubles OU', 'gen9vgc2024regg-1630': 'VGC', 'gen9nationaldexdoubles-1500': 'NatDex Doubles'}
SING = ['gen9ou-1695', 'gen9nationaldex-1630', 'gen9uu-1630', 'gen9nationaldexuu-1630', 'gen9ru-1630', 'gen9nu-1630']
DOUB = ['gen9doublesou-1695', 'gen9vgc2024regg-1630', 'gen9nationaldexdoubles-1500']


COMBO_DEP = {'Tatsugiri': 'DONDOZO'}
try:
    import current_box as _cb
    OWNED_SP = {re.sub(r'[^A-Z]', '', d_['species'].split('-')[0].upper()) for d_ in _cb.parse(json.load(open('team/state.json'))['export'])}
except Exception:
    OWNED_SP = set()


def meta_of(name, sp, op):
    """22 Nov (Vincent): META DOMINANCE = Smogon usage weighted by how high the format is (OU / VGC 1.0 ... NU .3), singles and
    doubles (best + 0.25 x the other); banned to Ubers (Ubers set, no OU usage) counts .95; Aevians by their kit's OP stars."""
    if 'Aevian' in name:   # 22 Nov (Vincent): Aevians have no Smogon / VGC data -> community opinion of the kit (community.py)
        import community as CM
        v, kind, lines = CM.AEVIAN.get(sp, (.45, 'kit', ['Not discussed by the community']))
        return v, ' | '.join([('Community rating' if kind == 'community' else 'Kit rating (no community posts)')] + lines)
    sd = SM.sd_name(name.replace(' (Hisuian Form)', '-Hisui').replace(' (Paldean Form)', '-Paldea').replace(' (Alolan Form)', '-Alola').replace(' (Galarian Form)', '-Galar'))
    if not sd: return .15, 'no competitive data'
    def best(fs):
        b, lab = 0, ''
        for f in fs:
            u = SM.usage(sd, f)
            if u and u.get('usage'):
                v = FW[f] * min(1, (u['usage'] / 20) ** .5)
                if v > b: b, lab = v, f"{FLAB[f]} {u['usage']:.1f}%"
        return b, lab
    s, ls = best(SING); d, ld = best(DOUB)
    need = COMBO_DEP.get(sd)   # usage that only exists with a partner you don't own doesn't count (Tatsugiri = Commander + Dondozo)
    if need and need not in OWNED_SP:
        d, ld = 0, ''
        if s < .3: s, ls = s, (ls + f' (doubles usage needs {need.title()}, not owned)').strip()
    ou_use = (SM.usage(sd, 'gen9ou-1695') or {}).get('usage')
    if sd in SM.SETS.get('gen9ubers', {}) and not ou_use: s, ls = max(s, .95), 'Ubers (banned from OU)'
    elif sd in SM.SETS.get('gen9nationaldexubers', {}) and not ou_use and s < .6: s, ls = max(s, .6), 'NatDex Ubers'
    v = min(1.0, max(s, d) + .25 * min(s, d))
    labs = [x for x in (ls, ld) if x]
    labs.sort(key=lambda x: 0 if (x == (ls if s >= d else ld)) else 1)
    return max(v, .15), ' | '.join(labs) or 'unranked'


def bst_of(c):
    return sum(c['base'].values())


def kind_of(c):
    if c.get('crest') or (c['sid'] == 'WHISCASH' and c['src'].get('item') == 'Whiscash Crest'): return 'crest'
    return 'aevian' if 'Aevian' in c['name'] else 'regular'


base = pickle.load(open(f"team/{os.environ['BASE_RUN']}_native.json.pkl", 'rb'))['cands']
crest_c = pickle.load(open(f"team/{os.environ['CREST_RUN']}_native.json.pkl", 'rb'))['cands'] if os.environ.get('CREST_RUN') else []
st = json.load(open('team/state.json'))
import current_box as cb
held = {d['item'] for d in cb.parse(st['export']) if d.get('item') and 'Crest' in d['item']}
owned_crests = set(st.get('crests_owned') or []) | held
import community as _CM   # 22 Nov: a crest from a later chapter does not count yet (wiki chapter list)
owned_crests = {c_ for c_ in owned_crests if _CM.CREST_CH.get(c_, 0) <= st.get('chapter', 9)}
I = json.load(open('gamedata/itemtext.json'))

best = {}
for c in base:
    if c['gate']: continue
    s = solo(c)
    if c['name'] not in best or s > best[c['name']][0]: best[c['name']] = (s, c)
crest_best = {}
for c in crest_c:
    if c['gate'] or not c.get('crest'): continue
    cname = I.get(crests.CREST_OF.get(c['sid'], ''), {}).get('name', '')
    if cname not in owned_crests: continue
    s = solo(c)
    if c['name'] not in crest_best or s > crest_best[c['name']][0]: crest_best[c['name']] = (s, c, cname)

fights_sorted = sorted(s for s, _ in best.values())
# 22 Nov (Vincent): in-game part = EVERY hard fight in the game (engine run with nothing marked done: ALL_RUN), not just Ch9
ALLS = {}
CTR = {}   # 25 Nov (Vincent: tiers factor in the community rules): share of hard-fight foes it hard-counters (deals 90%+ and takes < 70%, or outspeeds and one-shots)
_TF = set(st.get('tier_fights') or [])   # Ch10 hook: when set, the in-game part and counters use ONLY these fight keys (his hard-fight list)
if os.environ.get('ALL_RUN') and os.path.exists(f"team/{os.environ['ALL_RUN']}_native.json.pkl"):
    for c in pickle.load(open(f"team/{os.environ['ALL_RUN']}_native.json.pkl", 'rb'))['cands']:
        if c['gate']: continue
        tot = tw = 0; nc_ = nf_ = 0
        for k_, rows_ in c['matchups'].items():
            if not rows_ or (_TF and k_ not in _TF): continue
            nf_ += len(rows_); nc_ += sum(1 for r_ in rows_ if (r_['off'] >= 90 and r_['deff'] < 70) or (r_.get('faster') and r_['off'] >= 100))
            n_ = len(rows_); tot += sum(r_['q'] for r_ in rows_) / n_ - .35 * sum(r_['deff'] >= 100 for r_ in rows_) / n_; tw += 1
        v_ = tot / tw if tw else 0
        if c['name'] not in ALLS or v_ > ALLS[c['name']]: ALLS[c['name']] = v_
        if nf_: CTR[c['name']] = max(CTR.get(c['name'], 0), nc_ / nf_)
ALL_SORTED = sorted(ALLS.values())
N_ALL = len(next(iter(pickle.load(open(f"team/{os.environ['ALL_RUN']}_native.json.pkl", 'rb'))['cands']))['matchups']) if ALLS else 0
def allpct(name):
    import bisect
    if name not in ALLS: return None
    return bisect.bisect_left(ALL_SORTED, ALLS[name]) / max(1, len(ALL_SORTED) - 1)
def pct(s):
    import bisect
    return bisect.bisect_left(fights_sorted, s) / max(1, len(fights_sorted) - 1)

CTR_SORTED = sorted(CTR.values())
# mindset kit (community_inputs.json 'mindset': singles / doubles / Rejuvenation): what the BUILD he would run brings to a team
_IBK = json.load(open('team/ideal_builds.json')) if os.path.exists('team/ideal_builds.json') else {}
_MVT = json.load(open('gamedata/movetext.json'))
_BYN = {v['name'].lower(): k for k, v in _MVT.items()}
KIT_CHECKS = [
    ('Speed control', lambda ms, ab, ty: ms & {'THUNDERWAVE', 'ICYWIND', 'ELECTROWEB', 'TAILWIND', 'TRICKROOM', 'GLARE', 'NUZZLE', 'STICKYWEB', 'SCARYFACE', 'BULLDOZE', 'STRINGSHOT'}),
    ('STAB priority', lambda ms, ab, ty: {m for m in ms if int(_MVT.get(m, {}).get('priority') or 0) > 0 and int(_MVT.get(m, {}).get('basedamage') or 0) > 0 and _MVT[m].get('type') in ty and m != 'FAKEOUT'}
                                          or ({'GRASSYGLIDE'} & ms and ab == 'GRASSYSURGE' and 'GRASS' in ty)),
    ('Pivot / sustain', lambda ms, ab, ty: (ms & {'UTURN', 'VOLTSWITCH', 'FLIPTURN', 'PARTINGSHOT', 'TELEPORT', 'CHILLYRECEPTION', 'RECOVER', 'ROOST', 'SLACKOFF', 'SOFTBOILED', 'MOONLIGHT', 'SYNTHESIS', 'MORNINGSUN', 'WISH', 'STRENGTHSAP', 'SHOREUP'}) or ({'REGENERATOR'} & {ab})),
    ('Immunity', lambda ms, ab, ty: ({'FLYING', 'GROUND', 'GHOST', 'DARK', 'FAIRY', 'NORMAL', 'STEEL'} & set(ty)) or ({'LEVITATE', 'VOLTABSORB', 'LIGHTNINGROD', 'MOTORDRIVE', 'WATERABSORB', 'STORMDRAIN', 'FLASHFIRE', 'SAPSIPPER', 'EARTHEATER', 'SOUNDPROOF', 'WELLBAKEDBODY', 'DRYSKIN'} & {ab})),
    ('Disruption', lambda ms, ab, ty: (ms & {'FAKEOUT', 'FOLLOWME', 'RAGEPOWDER', 'WIDEGUARD', 'TAUNT', 'ENCORE', 'HAZE', 'CLEARSMOG', 'ROAR', 'WHIRLWIND', 'KNOCKOFF', 'SPORE', 'SLEEPPOWDER', 'YAWN', 'WILLOWISP'}) or ({'INTIMIDATE', 'UNAWARE'} & {ab})),
    ('Win condition', lambda ms, ab, ty: (ms & (set(SETUP_X) | {'TORCHSONG', 'POWERUPPUNCH', 'FLAMECHARGE', 'TRAILBLAZE', 'METEORBEAM', 'CHARGEBEAM', 'RAPIDSPIN', 'AQUASTEP', 'ESPERWING', 'SPINOUT'})) or ({'SPEEDBOOST', 'MOXIE', 'BEASTBOOST', 'SKILLLINK', 'PROTEAN', 'LIBERO', 'HUGEPOWER', 'PUREPOWER', 'ADAPTABILITY'} & {ab})),
]
def kit_of(name, c):
    b = _IBK.get(name) or {}
    ms = {_BYN.get(m.lower()) or m.upper().replace(' ', '') for m in (b.get('moves') or [])} or set(c.get('attacks') or [])
    ab = (b.get('ability') or c.get('ability') or '').upper().replace(' ', ''); ty = c['types']
    return [k for k, f in KIT_CHECKS if f(ms, ab, ty)]
rows = []
def row(name, s, c, kind, crest=''):
    sp = name.split(' (')[0]
    meta, lab = meta_of(name, sp, None)
    if crest:   # 22 Nov: crests rated by the community / wiki (community.py), not a flat .6 floor
        import community as CM
        cv, lines = CM.CREST.get(crest, (.5, ['Not discussed by the community']))
        meta, lab = max(meta, cv), ' | '.join([f'Community rating ({crest})'] + lines)
    bst = bst_of(c)
    general = .9 * meta + .1 * max(0, min(1, (bst - 380) / 220))   # meta dominance (+ a small base-stat tiebreak)
    fp = min(1.0, pct(s))
    ap = allpct(name)
    gp = ap if ap is not None else fp
    import bisect
    cp = bisect.bisect_left(CTR_SORTED, CTR.get(name, 0)) / max(1, len(CTR_SORTED) - 1) if CTR_SORTED else 0
    kit = kit_of(name, c)
    team = .6 * cp + .4 * len(kit) / len(KIT_CHECKS)
    # 25 Nov (Vincent: factor in the community rules: tier lists, mindsets, counters): 55% meta / community rating, 20% in-game across the
    # hard fights, 25% team value (hard counters + mindset kit)
    blend = .55 * general + .2 * gp + .25 * team
    src = c['src'] if isinstance(c['src'], dict) else {}
    rows.append(dict(name=name, kind=kind, crest=crest, zoro_partner=c.get('zoro_partner'), sid=c['sid'], form=str(c.get('form', '0')), types=c['types'], base=c['base'], bst=bst,
                     fight=round(s, 3), fight_pct=round(fp, 3), meta=round(meta, 3), meta_label=lab, general=round(general, 3),
                     blend=round(blend, 3), game_pct=round(gp, 3), n_all=N_ALL, ability=c['ability'], abilities=c['abilities'], nature=c['nature'], evs=c['evs'],
                     cat=c['cat'], attacks=[C.D.moves[m]['MoveName'] for m in c['attacks']], legal=sorted(c['legal']),
                     where=src.get('where'), dump=src.get('dump'), owned_as=c.get('owned_as'), evo=c.get('evo'),
                     per_fight=per_fight(c), counters=counters(c), stats=c['stats'], tags=sorted(c.get('tags') or []),
                     ctr_share=round(CTR.get(name, 0), 3), ctr_pct=round(cp, 3), kit=kit, team=round(team, 3)))
for n, (s, c) in best.items():
    _k = kind_of(c)
    if _k == 'crest' and 'Whiscash Crest' not in owned_crests: _k = 'regular'   # held but not obtainable yet
    row(n, s, c, _k, 'Whiscash Crest' if _k == 'crest' else '')
for n, (s, c, cname) in crest_best.items():
    row(n, s, c, 'crest', cname)

CUT = [('S', .675), ('A', .58), ('B', .44), ('C', .29), ('D', -9)]   # 25 Nov: recalibrated (same tier sizes) for 55% meta + 20% in-game + 25% team value
for r in rows:
    r['tier'] = next(t for t, v in CUT if r['blend'] >= v)
rows.sort(key=lambda r: -r['blend'])
fights = [dict(key=b['key'], format=b['format'], field=b['field'], weight=C.bw(b),
               foes=[dict(name=r['foe']) for r in best[next(iter(best))][1]['matchups'][b['key']]]) for b in C.HARD]
json.dump(dict(cut=CUT, fights=fights, rows=rows), open('team/tier_all.json', 'w'), indent=1, ensure_ascii=False)
import collections
print('tiers:', {k: dict(collections.Counter(r['tier'] for r in rows if r['kind'] == k)) for k in ('regular', 'aevian', 'crest')})
for r in rows[:45]:
    print(f"{r['tier']} {r['blend']:.2f} f{r['fight']:.2f}/{r['fight_pct']:.2f} g{r['general']:.2f} {r['kind'][:3]} {r['name'][:28]:28s} {r['meta_label'][:30]:30s} {len(r['counters'])}")
