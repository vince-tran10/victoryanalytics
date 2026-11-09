"""Rejuvenation crest effects, taken from the game code (Rejuv/Battle/Battler.rb crestStats, Battle_Move.rb crest
damage multipliers / irregularTypeMods / finalmult / STAB). Used by engine.py when me['crest'] is set (env CRESTS).
Modelled: stat crests, damage crests, type/defence crests below. Not modelled (situational / gimmick): Castform,
Cherrim, Luvdisc, Zoroark, Furret, Swalot, Zangoose, Thievul, Vespiquen, Plusle/Minun, Sunflora, Ledian, Delcatty,
Probopass, Gothitelle type swap, Shiinotic drain, Druddigon sun heal, Reuniclus form swap, Silvally memory abilities."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
_MAP = os.path.join(HERE, '..', '..', 'workspace', 'gamedata', 'crest_map.json')
CREST_OF = json.load(open(_MAP)) if os.path.exists(_MAP) else {}   # SPECIES -> CRESTITEM (PBStuff.POKEMONTOCREST)

BITING = {'BITE', 'CRUNCH', 'FIREFANG', 'ICEFANG', 'THUNDERFANG', 'POISONFANG', 'PSYCHICFANGS', 'HYPERFANG', 'JAWLOCK',
          'FISHIOUSREND'}
STABBING = {'PECK', 'DRILLPECK', 'FURYATTACK', 'HORNATTACK', 'MEGAHORN', 'POISONJAB', 'SMARTSTRIKE', 'DRILLRUN', 'PINMISSILE',
            'TWINEEDLE', 'HORNDRILL', 'FALSESURRENDER'}
EXTRA_TYPE = {'LUXRAY': 'DARK', 'SAMUROTT': 'FIGHTING', 'SIMISEAR': 'WATER', 'SIMIPOUR': 'GRASS', 'SIMISAGE': 'FIRE',
              'EMPOLEON': 'ICE'}   # STAB on this type; the Simis + Luxray + Samurott also gain its resistances


def enabled(sid, form='0', formname=''):
    v = os.environ.get('CRESTS', '')
    if sid not in CREST_OF or sid == 'WHISCASH':        # Whiscash Crest is already modelled as its held item
        return False
    if sid == 'AMPHAROS' and 'Aevian' not in (formname or ''): return False   # A. Ampharos Crest: Aevian form only
    if sid == 'ELECTRODE' and str(form) != '0': return False                    # Kantonian Electrode only
    return v == '1' or sid in v.split(',')


def apply_stats(me):
    """Battler.rb crestStats (stat multipliers on top of the normal stats)."""
    c, s = me.get('crest'), me['stats']
    mul = {'SILVALLY': {'Atk': 1.2, 'SpA': 1.2}, 'SKUNTANK': {'Atk': 1.2, 'SpA': 1.2}, 'WHISCASH': {'Atk': 1.2, 'SpA': 1.2},
           'SIMISAGE': {'Atk': 1.2, 'SpA': 1.2}, 'SIMISEAR': {'Atk': 1.2, 'SpA': 1.2}, 'SIMIPOUR': {'Atk': 1.2, 'SpA': 1.2},
           'HYPNO': {'SpA': 1.5}, 'STANTLER': {'Atk': 1.5}, 'WYRDEER': {'Atk': 1.5}, 'ORICORIO': {'SpA': 1.25, 'Spe': 1.25},
           'SEVIPER': {'Spe': 1.5}, 'DUSKNOIR': {'Atk': 1.5}, 'COFAGRIGUS': {'Def': 1.4, 'SpA': 1.2}, 'ARIADOS': {'Spe': 1.5},
           'PHIONE': {'Def': 1.5, 'SpD': 1.5}, 'NOCTOWL': {'Def': 1.3}, 'CRABOMINABLE': {'Def': 1.25, 'SpD': 1.25},
           'REUNICLUS': {'SpA': 1.25}, 'GOTHITELLE': {'SpA': 1.25}, 'PANGORO': {'Def': 1.3, 'SpD': 1.3}, 'SHIINOTIC': {'SpD': 1.3},
           'RELICANTH': {'Atk': 1.25, 'SpD': 1.35}}.get(c, {})
    for k, m in mul.items():
        s[k] = int(s[k] * m)
    if c == 'MAGCARGO':
        s['Def'], s['Spe'] = s['Spe'], s['Def']; s['SpA'] = int(s['SpA'] * 1.2)
    elif c == 'CLAYDOL':
        s['SpA'] = s['Def']
    elif c == 'DEDENNE':
        s['Atk'] = s['SpA'] = s['Spe']
    elif c == 'TYPHLOSION':
        s['Atk'] = s['SpA']
    elif c == 'INFERNAPE':
        s['SpD'], s['Def'] = s['SpA'], s['Atk']
    elif c == 'CRYOGONAL':
        s['SpD'] = int(s['SpD'] * 1.2)
        for k in ('Atk', 'Def', 'SpA', 'Spe'): s[k] = int(s[k] + s['SpD'] * 0.1)
    elif c == 'ELECTRODE':
        for k in ('Def', 'SpA', 'SpD'): s[k] = int(s[k] + s['Spe'] * 0.1)
    elif c == 'SAWSBUCK':
        me['types'] = [{'0': 'WATER', '1': 'FIRE', '2': 'GROUND', '3': 'ICE'}.get(str(me.get('form', '0')), 'WATER')] + me['types'][1:]


def move_type(att, mid, mv, mtype):
    """Crest type changes (PBMove.rb): Luxray Normal->Electric, Simisear->Water, Sawsbuck Normal->season."""
    c = att.get('crest')
    if c == 'LUXRAY' and mtype == 'NORMAL': return 'ELECTRIC'
    if c == 'SAWSBUCK' and mtype == 'NORMAL': return att['types'][0]
    return mtype


def atk_mult(att, dfn, mid, mv, mtype, base_power):
    """Battle_Move.rb 'standard crest damage multipliers'."""
    c = att.get('crest'); m = 1.0
    faster = att['stats']['Spe'] > dfn['stats']['Spe']
    if c == 'FERALIGATR' and mid in BITING: m *= 1.5
    if c == 'CLAYDOL' and 'BEAM' in mid: m *= 1.5
    if c == 'DRUDDIGON' and mtype in ('DRAGON', 'FIRE'): m *= 1.3
    if c == 'BOLTUND' and mid in BITING and faster: m *= 1.5
    if c == 'FEAROW' and mid in STABBING: m *= 1.5
    if c == 'DUSKNOIR' and base_power <= 60: m *= 1.5
    if c == 'CRABOMINABLE' and not faster: m *= 1.5        # powered up after taking damage first
    if c == 'AMPHAROS': m *= 1.2 if mtype in att['types'] else 1.0   # first move slot only: assume the main STAB attack sits there
    if c == 'LUXRAY' and mv['Type'] == 'NORMAL': m *= 1.2
    if c == 'SAWSBUCK' and mv['Type'] == 'NORMAL': m *= 1.2
    if c == 'CINCCINO' and mv.get('Target') in ('SingleNonUser', 'RandomOpposing', 'SingleOpposing'):
        m *= 2.0 if att.get('ability') == 'SKILLLINK' else 1.24   # every single-target move hits 2-5 times at 0.4x
    return m


def extra_stab(att, mtype):
    return EXTRA_TYPE.get(att.get('crest')) == mtype


def def_typemod(dfn, mtype, eff, chart_one):
    """Battle_Move.rb irregularTypeMods + crest immunities. chart_one(atk, deftype) -> multiplier."""
    c = dfn.get('crest')
    if c == 'GLACEON' and mtype in ('FIGHTING', 'ROCK'): return 0.5
    if c == 'LEAFEON' and mtype in ('FIRE', 'FLYING'): return 0.5
    if c in ('LUXRAY', 'SAMUROTT', 'SIMISEAR', 'SIMIPOUR', 'SIMISAGE'):
        x = chart_one(mtype, EXTRA_TYPE[c])
        if x == 0: return 0.0
        if x < 1: return eff * 0.5
    if c == 'SKUNTANK' and mtype == 'GROUND': return 0.0
    if c == 'WHISCASH' and mtype == 'GRASS': return 0.0
    if c == 'DRUDDIGON' and mtype == 'FIRE': return 0.0
    return eff


def def_final(att, dfn, eff):
    """Battle_Move.rb finalmult defensive crests."""
    c = dfn.get('crest'); m = 1.0
    if c == 'MEGANIUM': m *= 0.8
    if c == 'AMPHAROS' and eff > 1: m *= 0.7
    if c == 'BEHEEYEM' and dfn['stats']['Spe'] > att['stats']['Spe']: m *= 0.67
    return m
