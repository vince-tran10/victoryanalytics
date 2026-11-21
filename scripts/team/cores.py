"""Cores tab (section s9): cores of 4 with one playstyle identity each, built from the blended tier list (team/tier_all.json).
Vincent (16 Nov): play a core of 4 (like a VGC bring-4) + swap in 2 for each fight. Every core must stand on its own
(general soundness) AND cover as many Ch9 foes as possible, so the 2 swaps stay small.
Core score = 0.30 tier quality + 0.20 Ch9 foes countered + 0.15 defence (no shared weakness) + 0.10 offensive coverage
           + 0.10 answers to win conditions + 0.15 identity strength (+ small Smogon teammate bonus).
usage (from workspace/): DONE=... CR_RUN=r103 python3 -I ../scripts/team/cores.py <report.html>"""
import html, itertools, json, os, re, sys, collections
sys.argv, OUT = ['x', '.', '20'], sys.argv[1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chapter_rules as C, smogon_meta as SM
from kits import disp, abn, SHORT
E = html.escape
D = C.D
T = json.load(open('team/tier_all.json'))
ST = json.load(open('team/state.json'))
TYPES = ['NORMAL', 'FIRE', 'WATER', 'ELECTRIC', 'GRASS', 'ICE', 'FIGHTING', 'POISON', 'GROUND', 'FLYING', 'PSYCHIC', 'BUG', 'ROCK',
         'GHOST', 'DRAGON', 'DARK', 'STEEL', 'FAIRY']
FOES = sorted({f"{b['key']}:{f['name']}" for b in T['fights'] for f in b['foes']})
mv_by_name = {v['MoveName']: k for k, v in D.moves.items()}

G = dict(fakeout={'FAKEOUT'}, tr={'TRICKROOM'}, tailwind={'TAILWIND'}, redirect={'FOLLOWME', 'RAGEPOWDER'},
         setup={'SWORDSDANCE', 'DRAGONDANCE', 'NASTYPLOT', 'QUIVERDANCE', 'SHIFTGEAR', 'CALMMIND', 'BULKUP', 'SHELLSMASH',
                'FILLETAWAY', 'COIL', 'VICTORYDANCE', 'TIDYUP', 'BELLYDRUM'},
         haze={'HAZE', 'CLEARSMOG', 'ROAR', 'WHIRLWIND', 'DRAGONTAIL', 'CIRCLETHROW'}, taunt={'TAUNT', 'ENCORE'},
         speedctl={'ICYWIND', 'ELECTROWEB', 'THUNDERWAVE', 'GLARE', 'STICKYWEB', 'SCARYFACE', 'STRINGSHOT', 'BULLDOZE', 'ROCKTOMB',
                   'TAILWIND', 'TRICKROOM', 'LOWSWEEP'},
         screens={'REFLECT', 'LIGHTSCREEN', 'AURORAVEIL'}, pivot={'UTURN', 'VOLTSWITCH', 'FLIPTURN', 'PARTINGSHOT', 'TELEPORT'},
         priority={'EXTREMESPEED', 'AQUAJET', 'ICESHARD', 'SHADOWSNEAK', 'BULLETPUNCH', 'MACHPUNCH', 'SUCKERPUNCH', 'GRASSYGLIDE',
                   'VACUUMWAVE', 'ACCELEROCK', 'JETPUNCH', 'FIRSTIMPRESSION', 'QUICKATTACK'},
         breaker={'BRICKBREAK', 'PSYCHICFANGS', 'RAGINGBULL', 'DEFOG'}, recover={'RECOVER', 'ROOST', 'SLACKOFF', 'MOONLIGHT', 'SYNTHESIS',
                                                                                'SOFTBOILED', 'MILKDRINK', 'SHOREUP', 'WISH', 'MORNINGSUN', 'STRENGTHSAP'})
SETUP_NAME = {'SWORDSDANCE': 'Swords Dance', 'DRAGONDANCE': 'Dragon Dance', 'NASTYPLOT': 'Nasty Plot', 'QUIVERDANCE': 'Quiver Dance',
              'SHIFTGEAR': 'Shift Gear', 'CALMMIND': 'Calm Mind', 'BULKUP': 'Bulk Up', 'SHELLSMASH': 'Shell Smash',
              'FILLETAWAY': 'Fillet Away', 'COIL': 'Coil', 'VICTORYDANCE': 'Victory Dance', 'TIDYUP': 'Tidy Up', 'BELLYDRUM': 'Belly Drum'}
BOOSTER = {'STEEL': 'Metal Coat', 'FIGHTING': 'Black Belt', 'ROCK': 'Hard Stone', 'GROUND': 'Soft Sand', 'DRAGON': 'Dragon Fang',
           'DARK': 'Black Glasses', 'ELECTRIC': 'Magnet', 'WATER': 'Mystic Water', 'ICE': 'Never-Melt Ice', 'POISON': 'Poison Barb',
           'FAIRY': 'Fairy Feather', 'FIRE': 'Charcoal', 'GRASS': 'Miracle Seed', 'FLYING': 'Sharp Beak', 'BUG': 'Silver Powder',
           'PSYCHIC': 'Twisted Spoon', 'GHOST': 'Spell Tag', 'NORMAL': 'Silk Scarf'}


def chart(atk, t):
    ch = D.chart.get(t.capitalize(), {})
    return 0 if atk in ch.get('Immunities', []) else 2 if atk in ch.get('Weaknesses', []) else .5 if atk in ch.get('Resistances', []) else 1


class Mon:
    def __init__(s, r):
        s.r, s.name, s.sp = r, r['name'], r['name'].split(' (')[0]
        s.legal, s.ab = set(r['legal']), r['ability']
        s.flags = {g for g, ms in G.items() if ms & s.legal}
        if 'INTIMIDATE' in r['abilities']: s.flags.add('intimidate')
        s.spe, s.bulk = r['base']['Spe'], r['base']['HP'] + r['base']['Def'] + r['base']['SpD']
        s.atk = max(r['base']['Atk'], r['base']['SpA'])
        s.mult = {}
        for a in TYPES:
            m = 1
            for t in r['types']: m *= chart(a, t)
            if C.IMM.get(s.ab) == a: m = 0
            s.mult[a] = m
        s.atypes = {D.moves[mv_by_name[a]]['Type'] for a in r['attacks'] if a in mv_by_name}
        s.se = {t for t in TYPES if any(chart(a, t) == 2 for a in s.atypes)}
        s.counters = set(r['counters'])
        s.sd = SM.sd_name(s.name)


rows = T['rows']
seen, POOL = set(), []
for r in rows:
    if r['tier'] in 'SAB' and r['name'] not in seen:
        seen.add(r['name']); POOL.append(Mon(r))
EXTRA = {r['name']: Mon(r) for r in rows if r['tier'] == 'C' and set(r['abilities']) & {'ELECTRICSURGE', 'SNOWWARNING', 'DROUGHT'}}
ALL = {m.name: m for m in POOL} | EXTRA
TEAMMATES = collections.defaultdict(set)
for fmt in ('gen9doublesou-1695', 'gen9vgc2024regg-1630', 'gen9nationaldexdoubles-1500', 'gen9ou-1695'):
    for sp, d in SM.CHAOS.get(fmt, {}).items():
        TEAMMATES[sp] |= set(sorted(d['Teammates'], key=lambda k: -d['Teammates'][k])[:12])


def defence(ms):
    pen, shared = 0, []
    for a in TYPES:
        w = sum(m.mult[a] > 1 for m in ms); res = sum(m.mult[a] < 1 for m in ms)
        if w >= 3: pen += 1; shared.append(a)
        elif w == 2 and res == 0: pen += .5; shared.append(a)
    return max(0, 1 - pen / 3), shared


ANS = [('Haze / phaze', {'haze'}), ('Taunt / Encore', {'taunt'}), ('Fake Out / Intimidate', {'fakeout', 'intimidate'}),
       ('speed control', {'speedctl'}), ('priority', {'priority'}), ('screen breaker', {'breaker'})]


def answers(ms):
    have = set().union(*(m.flags for m in ms))
    got = [n for n, fl in ANS if fl & have]
    return len(got) / len(ANS), got, [n for n, fl in ANS if not fl & have]


def meta_bonus(ms):
    b = 0
    for x, y in itertools.combinations(ms, 2):
        if x.sd and y.sd and (y.sd in TEAMMATES.get(x.sd, ()) or x.sd in TEAMMATES.get(y.sd, ())): b += .01
    return min(b, .03)


def core_score(ms, ident, ans=None):
    q = sum(m.r['blend'] for m in ms) / 4
    cov = len(set().union(*(m.counters for m in ms))) / len(FOES)
    dfn, _ = defence(ms)
    gaps = [s for s in C.MAJOR if not any(C.eff(s, m.r['types'], m.ab) < 1 for m in ms)]   # 17 Nov: major Ch9 types nobody resists
    dfn = max(0, dfn - .1 * len(gaps))
    off = len(set().union(*(m.se for m in ms))) / len(TYPES)
    if ans is None: ans, _, _ = answers(ms)
    return .30 * q + .20 * min(1, cov * 1.6) + .15 * dfn + .10 * off + .10 * ans + .15 * ident + meta_bonus(ms)


def gaps_of(ms):
    return ['/'.join(s).title() for s in C.MAJOR if not any(C.eff(s, m.r['types'], m.ab) < 1 for m in ms)]


# ---------------- archetypes: (id, title, identity text, enabler filter, member filter, identity strength fn, roles fn)
def grass_user(m): return 'GRASS' in m.atypes or 'GRASSYGLIDE' in m.legal
def eq_user(m): return bool({'EARTHQUAKE', 'BULLDOZE'} & m.legal) and 'GROUND' in m.atypes


def id_balance(ms):
    s = sum(.25 for m in ms if m.flags & {'fakeout', 'intimidate'})
    s += .25 * min(2, sum(1 for m in ms if m.flags & {'pivot', 'recover'} or m.ab == 'REGENERATOR'))
    s += .25 * min(1, sum(1 for m in ms if 'speedctl' in m.flags))
    s += min(.25, max(0, (sum(m.bulk for m in ms) / 4 - 230) / 200))
    return min(1, s)


def id_tr(ms):
    slow = sum(1 for m in ms if m.spe <= 60 and m.atk >= 95)
    sup = any(m.flags & {'fakeout', 'redirect'} for m in ms)
    return min(1, .3 * slow + (.2 if sup else 0) + (.1 if sum(m.spe for m in ms) / 4 <= 50 else 0))


def id_terrain(ms):
    ben = sum(1 for m in ms if grass_user(m)) + .5 * sum(1 for m in ms if eq_user(m))
    return min(1, .3 * ben + .1)


def id_eterrain(ms):
    ben = sum(1 for m in ms if 'ELECTRIC' in m.atypes)
    return min(1, .35 * ben)


def id_setup(ms):
    sw = sum(1 for m in ms if 'setup' in m.flags and (m.spe >= 80 or 'priority' in m.flags or m.legal & {'DRAGONDANCE', 'SHIFTGEAR', 'QUIVERDANCE', 'FILLETAWAY', 'SHELLSMASH'}))
    en = any(m.flags & {'fakeout', 'redirect', 'tailwind', 'screens'} for m in ms)
    return min(1, .3 * sw + (.3 if en else 0))


def id_sun(ms):
    ben = sum(1 for m in ms if 'FIRE' in m.atypes) + 1.5 * sum(1 for m in ms if set(m.r['abilities']) & {'CHLOROPHYLL', 'SOLARPOWER'})
    return min(1, .3 * ben)


def id_snow(ms):
    ben = sum(1 for m in ms if 'ICE' in m.atypes or 'ICE' in m.r['types']) + 1.5 * sum(1 for m in ms if set(m.r['abilities']) & {'SLUSHRUSH', 'ICEBODY'})
    veil = any('AURORAVEIL' in m.legal for m in ms)
    return min(1, .25 * ben + (.2 if veil else 0))


ARCH = [
    ('balance', 'Balance / tempo', 'Bulky attackers that win the long game: Intimidate / Fake Out to control turn 1, speed control, pivots and recovery, and an answer to every setup or screens win condition.',
     lambda m: m.flags & {'fakeout', 'intimidate'}, lambda m: True, id_balance),
    ('tr', 'Trick Room', 'Hard Trick Room: a setter turns the slowest, hardest hitters into the fastest for 4 turns. Fake Out / Follow Me protects the setter on turn 1.',
     lambda m: 'tr' in m.flags, lambda m: m.spe <= 65, id_tr),
    ('setup', 'Setup / hyper offense', 'Two setup sweepers behind a support that buys the free turn (Fake Out, Follow Me / Rage Powder, Tailwind or screens). Overwhelm before the AI can respond.',
     lambda m: m.flags & {'fakeout', 'redirect', 'tailwind', 'screens'}, lambda m: True, id_setup),
    ('grassy', 'Grassy Terrain', 'Glalie-Aevian sets Grassy Terrain on entry: Grass moves ×1.3, Grassy Glide gets priority, everyone grounded heals 1/16 each turn, and Earthquake / Bulldoze do half damage (spam them next to your own team).',
     lambda m: m.ab == 'GRASSYSURGE' or 'GRASSYSURGE' in m.r['abilities'], lambda m: True, id_terrain),
    ('electric', 'Electric Terrain', 'Pincurchin\'s Electric Surge: Electric moves ×1.3, nobody grounded can be put to sleep. Strongest with several Electric attackers.',
     lambda m: 'ELECTRICSURGE' in m.r['abilities'], lambda m: True, id_eterrain),
    ('sun', 'Sun (Drought)', 'Drought Ninetales: Fire ×1.5, Water halved, Chlorophyll users double their Speed, Solar Beam in one turn.',
     lambda m: 'DROUGHT' in m.r['abilities'], lambda m: True, id_sun),
    ('snow', 'Snow (Snow Warning)', 'Snow Warning: Ice types get +50% Defence, Aurora Veil halves all damage for 5 turns, Slush Rush doubles Speed.',
     lambda m: 'SNOWWARNING' in m.r['abilities'], lambda m: True, id_snow),
]


# ---- 21 Nov (Vincent): every core = [1 lead (singles + left slot in doubles), 2 doubles lead partner, 3 flex, 4 closer]
SLOT = ['Lead', 'Doubles lead', 'Flex', 'Closer']
PHYS_SET = {'SWORDSDANCE', 'DRAGONDANCE', 'SHIFTGEAR', 'BULKUP', 'COIL', 'VICTORYDANCE', 'TIDYUP', 'BELLYDRUM', 'CURSE', 'SHELLSMASH', 'FILLETAWAY'}
SPEC_SET = {'NASTYPLOT', 'CALMMIND', 'QUIVERDANCE', 'SHELLSMASH', 'FILLETAWAY', 'TAILGLOW', 'GEOMANCY'}
SPREAD = {'EARTHQUAKE', 'ROCKSLIDE', 'HEATWAVE', 'MAKEITRAIN', 'MUDDYWATER', 'DAZZLINGGLEAM', 'HYPERVOICE', 'ICYWIND', 'BLIZZARD',
          'DISCHARGE', 'SURF', 'BULLDOZE', 'ERUPTION', 'WATERSPOUT', 'SLUDGEWAVE', 'BOOMBURST', 'SNARL', 'ELECTROWEB', 'BREAKINGSWIPE', 'LAVAPLUME'}
def has_setup(m):
    return bool(m.legal & (PHYS_SET if m.r['cat'] == 'Physical' else SPEC_SET)) or bool(set(m.r['abilities']) & {'SPEEDBOOST', 'MOXIE', 'BEASTBOOST'})
def s_lead(m):     # singles lead + left slot in doubles: fast or bulky, turn-1 utility, status-proof helps
    u = .2 * bool(m.flags & {'fakeout', 'intimidate'}) + .15 * bool(m.flags & {'speedctl', 'taunt', 'tr', 'tailwind', 'screens'})
    return .4 * m.r['blend'] + .2 * min(1, m.spe / 130) + u + .1 * min(1, m.bulk / 330) + (.05 if 'GOODASGOLD' in m.r['abilities'] or 'MAGICGUARD' in m.r['abilities'] else 0)
def s_partner(m):  # doubles lead partner: Intimidate / Fake Out / redirection / Tailwind, spread damage
    u = .25 * bool(m.flags & {'fakeout', 'intimidate', 'redirect'}) + .1 * bool(m.flags & {'tailwind', 'speedctl', 'screens', 'tr'}) + .1 * bool(m.legal & SPREAD)
    return .4 * m.r['blend'] + .15 * min(1, m.spe / 130) + u
def s_flex(m):     # flex / mid game: bulky pivot with an answer (Haze, recovery, pivot moves)
    return .5 * m.r['blend'] + .25 * min(1, m.bulk / 330) + .15 * bool(m.flags & {'haze', 'recover', 'pivot'}) + .1 * bool(m.flags & {'taunt', 'speedctl'})
def s_closer(m):   # closer: one setup move (or a boosting ability), then clean up; counters what's left
    return (.5 * m.r['blend'] + .3 * min(1, len(m.counters) / 15) + .2) if has_setup(m) else .3 * m.r['blend']
SFN = [s_lead, s_partner, s_flex, s_closer]
def order_roles(ms, lead_req=None):
    best = None
    for p in itertools.permutations(ms):
        if lead_req and not (lead_req(p[0]) or lead_req(p[1])): continue   # a setter must lead (slot 1 or 2)
        fit = sum(f(m) for f, m in zip(SFN, p)) / 4
        if best is None or fit > best[0]: best = (fit, p)
    return best if best else (0.0, tuple(ms))
TOP = sorted(POOL, key=lambda m: -m.r['blend'])[:42]
results, CAND = {}, {}
for key, title, idt, en_f, mem_f, id_f in ARCH:
    ens = [m for m in ALL.values() if en_f(m)]
    ens = sorted(ens, key=lambda m: -m.r['blend'])[:8]
    others = [m for m in TOP if mem_f(m)]
    if key in ('electric', 'sun', 'snow', 'grassy'):   # beneficiaries may sit lower in the list
        others += [m for m in POOL if m not in others and (id_f((m,)) >= .3)][:15]
    if key == 'tr': others = [m for m in POOL if mem_f(m)][:40]
    cand = []
    for e in ens:
        rest = [m for m in others if m.name != e.name and m.sp != e.sp]
        for trio in itertools.combinations(rest, 3):
            if len({m.sp for m in trio}) < 3: continue
            ms = (e,) + trio
            idv = id_f(ms) if key in ('balance', 'tr', 'setup') else id_f(trio)   # the setter doesn't power itself
            if key == 'snow' and 'AURORAVEIL' in e.legal and not any('AURORAVEIL' in m.legal for m in trio): idv = min(1, idv + .2)
            if key != 'balance' and idv < .6: continue          # must actually play its style
            cand.append((core_score(ms, idv), ms))
    cand.sort(key=lambda x: -x[0])
    lreq = None if key in ('balance', 'setup') else en_f
    cand = [(sc + .15 * fit - (.05 if not has_setup(o[3]) else 0), o) for sc, ms in cand[:250] for fit, o in [order_roles(ms, lreq)]]
    cand.sort(key=lambda x: -x[0])
    CAND[key] = (cand, id_f, lreq)


# ---------------- builds per member, role-aware
def role_of(m, key, ms, enabler):
    if m is enabler:
        return {'balance': 'tempo lead', 'tr': 'Trick Room setter', 'setup': 'support lead', 'grassy': 'terrain setter',
                'electric': 'terrain setter', 'sun': 'sun setter', 'snow': 'snow setter'}[key]
    phys_setup = {'DRAGONDANCE', 'SHIFTGEAR', 'FILLETAWAY', 'SHELLSMASH', 'SWORDSDANCE', 'VICTORYDANCE', 'TIDYUP', 'BULKUP', 'COIL', 'BELLYDRUM'}
    spec_setup = {'QUIVERDANCE', 'FILLETAWAY', 'SHELLSMASH', 'NASTYPLOT', 'CALMMIND'}
    if key == 'setup' and m.legal & (phys_setup if m.r['cat'] == 'Physical' else spec_setup): return 'setup sweeper'
    if key == 'tr': return 'Trick Room attacker'
    if m.flags & {'fakeout', 'intimidate'}: return 'tempo / pivot'
    if m.bulk >= 300 and m.flags & {'haze', 'recover'}: return 'bulky answer'
    return 'attacker'


NEEDS_W = {'rain': {'HYDRATION', 'SWIFTSWIM', 'RAINDISH'}, 'sun': {'CHLOROPHYLL', 'SOLARPOWER', 'LEAFGUARD', 'HARVEST', 'FLOWERGIFT'},
           'sand': {'SANDVEIL', 'SANDRUSH', 'SANDFORCE'}, 'snow': {'SLUSHRUSH', 'ICEBODY', 'SNOWCLOAK'}, 'eterrain': {'SURGESURFER'}}


def pick_ability(m, role, have):
    abil = list(dict.fromkeys(m.r['abilities']))
    dead = set().union(*(v for k, v in NEEDS_W.items() if k not in have))
    live = [a for a in abil if a not in dead] or abil
    for want in ('GRASSYSURGE', 'ELECTRICSURGE', 'DROUGHT', 'SNOWWARNING'):
        if role.endswith('setter') and want in live: return want
    for want in ('CHLOROPHYLL', 'SLUSHRUSH', 'INNERFOCUS' if role == 'Trick Room setter' else '', 'INTIMIDATE', 'MAGICGUARD', 'REGENERATOR'):
        if want in live: return want
    u = (SM.meta(m.sd).get('doubles_usage') or SM.meta(m.sd).get('singles_usage') or {}) if m.sd else {}
    for a, _ in u.get('abilities', []):
        hit = next((x for x in live if x.lower() == a), None)
        if hit: return hit
    return m.r['ability'] if m.r['ability'] in live else live[0]


FILL_BY_CAT = {'Taunt / Encore': ('TAUNT', 'ENCORE'), 'screen breaker': ('BRICKBREAK', 'PSYCHICFANGS', 'DEFOG'),
               'Haze / phaze': ('CLEARSMOG', 'HAZE', 'ROAR', 'WHIRLWIND', 'DRAGONTAIL'), 'Fake Out / Intimidate': ('FAKEOUT',),
               'speed control': ('ICYWIND', 'ELECTROWEB', 'THUNDERWAVE', 'GLARE', 'SCARYFACE', 'ROCKTOMB', 'BULLDOZE', 'TAILWIND'),
               'priority': ('EXTREMESPEED', 'AQUAJET', 'ICESHARD', 'SHADOWSNEAK', 'BULLETPUNCH', 'MACHPUNCH', 'SUCKERPUNCH', 'VACUUMWAVE')}
GENERIC_FILL = ('KNOCKOFF', 'WILLOWISP', 'ICYWIND', 'THUNDERWAVE', 'HELPINGHAND', 'SWORDSDANCE', 'NASTYPLOT', 'CALMMIND', 'RECOVER',
                'SLACKOFF', 'ROOST', 'MOONLIGHT', 'SYNTHESIS', 'BULKUP')


def build(m, key, role, need, have=frozenset()):
    r = m.r
    tr_core = key == 'tr'
    utility = []
    if role == 'Trick Room setter': utility.append('Trick Room')
    if role in ('tempo lead', 'support lead', 'tempo / pivot') and 'FAKEOUT' in m.legal: utility.append('Fake Out')
    if role == 'support lead' and 'FAKEOUT' not in m.legal:
        for mv, n in (('FOLLOWME', 'Follow Me'), ('RAGEPOWDER', 'Rage Powder'), ('TAILWIND', 'Tailwind'), ('AURORAVEIL', 'Aurora Veil'), ('REFLECT', 'Reflect'), ('LIGHTSCREEN', 'Light Screen')):
            if mv in m.legal: utility.append(n); break
    if role == 'snow setter' and 'AURORAVEIL' in m.legal: utility.append('Aurora Veil')
    if role == 'setup sweeper':
        pref = (['DRAGONDANCE', 'SHIFTGEAR', 'FILLETAWAY', 'SHELLSMASH', 'SWORDSDANCE', 'VICTORYDANCE', 'TIDYUP', 'BULKUP', 'COIL', 'BELLYDRUM']
                if r['cat'] == 'Physical' else ['QUIVERDANCE', 'FILLETAWAY', 'SHELLSMASH', 'NASTYPLOT', 'CALMMIND'])
        s = next((x for x in pref if x in m.legal), None)
        if s: utility.append(SETUP_NAME[s])
    if role == 'bulky answer':
        for mv, n in (('HAZE', 'Haze'), ('CLEARSMOG', 'Clear Smog'), ('ROAR', 'Roar'), ('WHIRLWIND', 'Whirlwind')):
            if mv in m.legal: utility.append(n); break
    if key == 'grassy' and 'GRASSYGLIDE' in m.legal and 'Grassy Glide' not in r['attacks']: utility.append('Grassy Glide')
    att = [a for a in r['attacks'] if a not in utility][:3 - len(utility)]
    free = 3 - len(utility) - len(att)
    for cat in need:                                   # fill free slots with the core's missing answers first
        if free <= 0: break
        if tr_core and cat == 'speed control': continue
        mv = next((x for x in FILL_BY_CAT.get(cat, ()) if x in m.legal), None)
        if mv and D.moves[mv]['MoveName'] not in utility:
            utility.append(D.moves[mv]['MoveName']); need.remove(cat); free -= 1
    for mv in GENERIC_FILL:
        if free <= 0: break
        if tr_core and mv in ('ICYWIND', 'THUNDERWAVE'): continue
        if mv in m.legal and D.moves[mv]['MoveName'] not in utility + att:
            utility.append(D.moves[mv]['MoveName']); free -= 1
    if free > 0:                                       # still a slot: best extra attack of a new type, same category
        used = {D.moves[mv_by_name[a]]['Type'] for a in att if a in mv_by_name}
        ex = sorted((x for x in m.legal if D.moves[x]['Category'] == r['cat'] and int(D.moves[x].get('Strength') or 0) >= 60
                     and D.moves[x]['Type'] not in used and x not in ('HYPERBEAM', 'GIGAIMPACT', 'SOLARBEAM', 'SKYATTACK', 'FOCUSPUNCH', 'SELFDESTRUCT', 'EXPLOSION', 'OUTRAGE', 'THRASH', 'PETALDANCE', 'HIDDENPOWER')),
                    key=lambda x: -int(D.moves[x].get('Strength') or 0))
        for x in ex[:free]: att.append(D.moves[x]['MoveName'])
    moves = utility + att + ['Protect']
    main = next((a for a in att if a in mv_by_name), None)
    mt = D.moves[mv_by_name[main]]['Type'] if main else None
    item = ('Focus Sash' if role in ('tempo lead', 'support lead') and m.bulk < 270 and m.spe >= 85 else
            'Sitrus Berry' if role in ('Trick Room setter', 'support lead') else
            BOOSTER.get(mt, 'Sitrus Berry'))
    if m.ab == 'GRASSYSURGE': item = 'Miracle Seed'
    phys = r['base']['Atk'] >= r['base']['SpA'] if not main else D.moves[mv_by_name[main]]['Category'] == 'Physical'
    if key == 'tr' and role != 'Trick Room setter':
        nat, evs = ('Brave' if phys else 'Quiet'), f"252 HP / 252 {'Atk' if phys else 'SpA'} · 0 Spe IVs"
    elif m.spe >= 85:
        nat, evs = ('Jolly' if phys else 'Timid'), f"252 {'Atk' if phys else 'SpA'} / 252 Spe"
    else:
        nat, evs = ('Adamant' if phys else 'Modest'), f"252 HP / 252 {'Atk' if phys else 'SpA'}"
    ab = pick_ability(m, role, have)
    return dict(moves=moves, item=item, nature=nat, evs=evs, ability=abn(ab))


def best_swaps(ms):
    got = set().union(*(m.counters for m in ms)); names = {m.sp for m in ms}; out = []
    for _ in range(2):
        b = max((m for m in POOL if m.sp not in names and m not in out), key=lambda m: (len(m.counters - got), m.r['blend']))
        out.append(b); got |= b.counters; names.add(b.sp)
    return out, got


RANK = {'S': 4, 'A': 3, 'B': 2, 'C': 1, 'D': 0}
def swap_pairs(main, alt):
    out = sorted([m for m in main if m.name not in {x.name for x in alt}], key=lambda m: -RANK[m.r['tier']])
    inn = sorted([m for m in alt if m.name not in {x.name for x in main}], key=lambda m: -RANK[m.r['tier']])
    return list(zip(out, inn))
def tier_ok(main, alt):
    pr = swap_pairs(main, alt)
    return bool(pr) and all(RANK[i.r['tier']] >= RANK[o.r['tier']] for o, i in pr)


def enabler_of(ms, key):
    en_f = next(a[3] for a in ARCH if a[0] == key)
    return next((m for m in ms if en_f(m)), ms[0])
def slot_ok(main, alt):   # alt differs only in whole slots: the new member sits in the replaced member's role, same tier or higher
    names_m = {m.name for m in main}; names_a = {m.name for m in alt}; diff = 0
    for o, i in zip(main, alt):
        if o.name == i.name: continue
        if i.name in names_m or o.name in names_a: return False
        if RANK[i.r['tier']] < RANK[o.r['tier']]: return False
        diff += 1
    return diff > 0
def covered_of(ms, bds, who=False):
    hits = {}
    for m, bd in zip(ms, bds):
        for x in bd['moves']:
            for n, fl in ANS:
                if fl & {g for g, mvs in G.items() if mv_by_name.get(x) in mvs}: hits.setdefault(n, []).append(f"{disp(m.name)} ({x})")
        if bd['ability'] == 'Intimidate': hits.setdefault('Fake Out / Intimidate', []).append(f"{disp(m.name)} (Intimidate)")
    return hits if who else [n for n, _ in ANS if n in hits]


def slot_role(m, i, key, ms):   # build role from the slot (21 Nov): setters keep their setter role
    en = enabler_of(ms, key)
    if m is en and key not in ('balance',): return role_of(m, key, ms, en)
    if i == 3: return 'setup sweeper' if has_setup(m) else 'attacker'
    if i in (0, 1): return 'tempo lead' if m.flags & {'fakeout', 'intimidate'} or key == 'balance' else role_of(m, key, ms, None)
    return role_of(m, key, ms, None)
def real_builds(ms, key):
    roles = [slot_role(m, i, key, ms) for i, m in enumerate(ms)]
    have = {w for w, ab in (('sun', 'DROUGHT'), ('snow', 'SNOWWARNING'), ('eterrain', 'ELECTRICSURGE')) if key in (w, 'electric' if w == 'eterrain' else w) and any(ab in m.r['abilities'] for m in ms)}
    bds = [build(m, key, rl, [], have) for m, rl in zip(ms, roles)]
    need = [n for n, _ in ANS if n not in covered_of(ms, bds)]
    return roles, [build(m, key, rl, need, have) for m, rl in zip(ms, roles)]


# 17 Nov: rank by the answers the shown builds actually run (not everything each member could learn)
for key, (cand, id_f, lreq) in CAND.items():
    rescored = []
    for sc, ms in cand:
        _, bds = real_builds(ms, key)
        en = enabler_of(ms, key)
        idv = id_f(ms) if key in ('balance', 'tr', 'setup') else id_f(tuple(m for m in ms if m is not en))
        fit = sum(f(m) for f, m in zip(SFN, ms)) / 4
        rescored.append((core_score(ms, idv, len(covered_of(ms, bds)) / len(ANS)) + .15 * fit - (.05 if not has_setup(ms[3]) else 0), ms))
    rescored.sort(key=lambda x: -x[0])
    main = rescored[0] if rescored else None
    mine = [ALL[n] for n in (ST.get('core') or []) if n in ALL]
    if key == 'balance' and len(mine) == 4:   # Vincent's picked core is always the first card of its style (state core order = roles)
        mine = tuple(mine)
        bds = [dict(moves=ST['moves'].get(m.name, []), ability=ST['abilities'].get(m.name, '')) for m in mine]
        fit = sum(f(m) for f, m in zip(SFN, mine)) / 4
        main = (core_score(mine, id_f(mine), len(covered_of(mine, bds)) / len(ANS)) + .15 * fit, mine)
    picked = [main] if main else []
    if main:   # 18 + 21 Nov (Vincent): a swap replaces a member IN THE SAME ROLE, at the same tier or higher
        for sc, ms in rescored:
            if [m.name for m in ms] == [m.name for m in main[1]]: continue
            if slot_ok(main[1], ms): picked.append((sc, ms)); break
    results[key] = picked
    print(key, [(round(s_, 3), [disp(m.name) for m in ms]) for s_, ms in picked])

cards = []
NOT_VIABLE = [t for k, t, *_ in ARCH if not results.get(k)]
for key, title, idt, en_f, mem_f, id_f in ARCH:
    for i, (sc, ms) in enumerate(results.get(key, [])):
        enabler = enabler_of(ms, key)
        dfn, shared = defence(ms)
        cov = set().union(*(m.counters for m in ms))
        per = {b['key']: (len({f for f in cov if f.startswith(b['key'] + ':')}), len(b['foes'])) for b in T['fights']}
        sw, cov6 = best_swaps(ms)
        uncovered = sorted(set(FOES) - cov6)
        roles = [slot_role(m, i, key, ms) for i, m in enumerate(ms)]
        def covered(bds, who=False):
            hits = {}
            for m, bd in zip(ms, bds):
                for x in bd['moves']:
                    for n, fl in ANS:
                        if fl & {g for g, mvs in G.items() if mv_by_name.get(x) in mvs}: hits.setdefault(n, []).append(f"{disp(m.name)} ({x})")
                if bd['ability'] == 'Intimidate': hits.setdefault('Fake Out / Intimidate', []).append(f"{disp(m.name)} (Intimidate)")
            return hits if who else [n for n, _ in ANS if n in hits]
        have = {w for w, ab in (('sun', 'DROUGHT'), ('snow', 'SNOWWARNING'), ('eterrain', 'ELECTRICSURGE')) if key in (w, 'electric' if w == 'eterrain' else w) and any(ab in m.r['abilities'] for m in ms)}
        bds = [build(m, key, rl, [], have) for m, rl in zip(ms, roles)]
        need = [n for n, _ in ANS if n not in covered(bds)]
        bds = [build(m, key, rl, need, have) for m, rl in zip(ms, roles)]
        if sorted(m.name for m in ms) == sorted(ST.get('core') or []):   # the core Vincent plays: show his real builds
            for j, m in enumerate(ms):
                if m.name in ST['moves']:
                    bds[j] = dict(bds[j], moves=ST['moves'][m.name], ability=ST['abilities'].get(m.name, bds[j]['ability']))
        got = covered(bds); miss = [n for n, _ in ANS if n not in got]; whom = covered(bds, True)
        mem = ''
        for m, role, bd in zip(ms, roles, bds):
            mem += (f"<tr><td><b>{E(disp(m.name))}</b> <span class='tier t{m.r['tier']}'>{m.r['tier']}</span>"
                    f"<div class='legend'>{E(role)} · base Spe {m.spe}</div></td>"
                    f"<td>{E(bd['ability'])} · {E(bd['nature'])} · {E(bd['evs'])}<div class='legend'>{E(bd['item'])}</div></td>"
                    f"<td>{E(' / '.join(bd['moves']))}</td></tr>")
        fl = ' · '.join(f"{SHORT[k]} {a}/{n}" for k, (a, n) in per.items())
        cards.append(
            f"<div class='panel pad core'><h3>{E(title)}{' (alt)' if i else (' · your core' if sorted(m.name for m in ms) == sorted(ST.get('core') or []) else '')} <span class='legend'>core score {sc:.2f}</span></h3>"
            f"<p class='legend'>{E(idt)}</p>"
            f"<div class='tablewrap'><table class='tlx'><thead><tr><th>Member</th><th>Ability · nature · EVs / item</th><th>Moves</th></tr></thead><tbody>{mem}</tbody></table></div>"
            f"<ul><li><b>Ch9 foes it counters:</b> {len(cov)}/{len(FOES)} <span class='legend'>({E(fl)})</span></li>"
            f"<li><b>Shared weaknesses:</b> {E(', '.join(t.title() for t in shared) or 'none')} · <b>major Ch9 types nobody resists:</b> {E(', '.join(gaps_of(ms)) or 'none')} (the 2 swaps must cover these)</li>"
            f"<li><b>Answers:</b> {E(' · '.join(n + ': ' + ', '.join(whom[n]) for n in got) or 'none')}{' · <b>missing:</b> ' + E(', '.join(miss)) if miss else ''}</li>"
            f"<li><b>Best 2 swaps for Ch9:</b> {E(disp(sw[0].name))} + {E(disp(sw[1].name))} → {len(cov6)}/{len(FOES)} foes"
            f"{' · still open: ' + E(', '.join(u.split(':')[1] + ' (' + SHORT[u.split(':')[0]] + ')' for u in uncovered[:8])) if uncovered else ''}</li></ul></div>")
        results[key][i] = dict(score=round(sc, 3), slots=SLOT, enabler=enabler.name, members=[m.name for m in ms], cover=len(cov), swaps=[x.name for x in sw], builds=bds, roles=roles, shared=shared, answers=got, missing=miss, per_fight=per, open=uncovered, cover6=len(cov6))

sec = f'''<section aria-labelledby="s9">
  <h2 id="s9">Cores</h2>
  <ul class="legend">
    <li>Pick ONE core of 4 for your playstyle; it stays all chapter. Add 2 swaps per fight (boss hard counters) from the Fights tab.</li>
    <li>Core score = 0.30 tier quality + 0.20 Ch9 foes countered + 0.15 no shared weakness + 0.10 type coverage + 0.10 answers
      (Haze, Taunt, Fake Out / Intimidate, speed control, priority, screen breaker) + 0.15 how well it plays its identity.</li>
    <li>Members come from S/A/B of the three tier tabs; enablers (setters) may come from lower tiers. Builds use Ch1–8 TMs. Protect is always the 4th move.</li>
    <li>Not modelled: turns of setup, Trick Room turn count, terrain / weather duration. Trick Room TM is not owned yet: only Oranguru and Porygon-Z learn it now.</li>
  </ul>
  {''.join(cards)}
  {('<p class="legend">No sound core yet for: ' + E(', '.join(NOT_VIABLE)) + ' (the setter has too few partners it powers).</p>') if NOT_VIABLE else ''}
</section>
'''
page = open(OUT, encoding='utf-8').read()
page = re.sub(r'<section aria-labelledby="s9">.*?</section>\s*', '', page, flags=re.S)
anchor = page.rfind('<section aria-labelledby="s5">') if '<section aria-labelledby="s5">' in page else page.rfind('<footer')
page = page[:anchor] + sec + page[anchor:]
page = page.replace('</style>', '.core ul { margin-top: 8px }</style>', 1) if '.core ul' not in page else page
open(OUT, 'w', encoding='utf-8').write(page)
json.dump(results, open('team/cores.json', 'w'), indent=1, ensure_ascii=False)
print('cores:', sum(len(v) for v in results.values()))
