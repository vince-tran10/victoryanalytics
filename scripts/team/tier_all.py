"""One blended tier score for every owned Pokémon (Vincent, 16 Nov): crests, Aevians and regular Pokémon on ONE scale.
  fight   = measured solo score on the remaining hard fights (exact game data + fields), as a percentile of the owned pool
  general = competitive power: Smogon tier/usage (singles + doubles; Aevians from their kit's OP stars), base-stat total
  blend   = 0.6 fight + 0.4 general -> tiers S/A/B/C/D by fixed cut-offs.
Also stores per-fight scores and the Ch9 foes each Pokémon counters (>= 90% dealt, < 70% taken) for the Cores tab.
usage (from workspace/): BASE_RUN=r103 CREST_RUN=rc103 DONE=... python3 -I ../scripts/team/tier_all.py  -> team/tier_all.json"""
import json, os, pickle, sys
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


def meta_of(name, sp, op):
    if 'Aevian' in name:
        stars = AEV_OP.get(sp, 1)
        return {3: .85, 2: .68, 1: .45}[stars], f"Aevian kit {'★' * stars}"
    sd = SM.sd_name(name.replace(' (Hisuian Form)', '-Hisui').replace(' (Paldean Form)', '-Paldea'))
    if not sd: return .3, 'no meta data'
    m = SM.meta(sd); best, lab = 0, []
    for f, w in TIER_W.items():
        if sd in SM.SETS.get(f, {}):
            if w > best: best = w
            lab.append(LABEL[f])
    use = max((m['singles_usage'] or {}).get('usage', 0), (m['doubles_usage'] or {}).get('usage', 0))
    if not best:
        return (.25 + min(.15, use / 20)), (f'usage {use:.1f}%' if use else 'unranked')
    return min(1.0, best + min(.1, use / 100)), ' · '.join(dict.fromkeys(lab[:3]))


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
def pct(s):
    import bisect
    return bisect.bisect_left(fights_sorted, s) / max(1, len(fights_sorted) - 1)

rows = []
def row(name, s, c, kind, crest=''):
    sp = name.split(' (')[0]
    meta, lab = meta_of(name, sp, None)
    if crest: meta, lab = max(meta, .6), f'{crest} (Rejuvenation-only)'
    bst = bst_of(c)
    general = .65 * meta + .35 * max(0, min(1, (bst - 380) / 220))
    fp = min(1.0, pct(s))
    blend = .6 * fp + .4 * general
    src = c['src'] if isinstance(c['src'], dict) else {}
    rows.append(dict(name=name, kind=kind, crest=crest, sid=c['sid'], form=str(c.get('form', '0')), types=c['types'], base=c['base'], bst=bst,
                     fight=round(s, 3), fight_pct=round(fp, 3), meta=round(meta, 3), meta_label=lab, general=round(general, 3),
                     blend=round(blend, 3), ability=c['ability'], abilities=c['abilities'], nature=c['nature'], evs=c['evs'],
                     cat=c['cat'], attacks=[C.D.moves[m]['MoveName'] for m in c['attacks']], legal=sorted(c['legal']),
                     where=src.get('where'), dump=src.get('dump'), owned_as=c.get('owned_as'), evo=c.get('evo'),
                     per_fight=per_fight(c), counters=counters(c), stats=c['stats'], tags=sorted(c.get('tags') or [])))
for n, (s, c) in best.items():
    row(n, s, c, kind_of(c), 'Whiscash Crest' if kind_of(c) == 'crest' else '')
for n, (s, c, cname) in crest_best.items():
    row(n, s, c, 'crest', cname)

CUT = [('S', .85), ('A', .76), ('B', .62), ('C', .45), ('D', -9)]
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
