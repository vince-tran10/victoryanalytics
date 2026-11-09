"""Heuristic competitive-set recommender for Pokemon Rejuvenation data.

Given a Pokemon's base stats, types, abilities and full learnset, pick a role,
ability, nature, EV spread, item and four moves. The rules are intentionally
transparent so they can be audited/overridden in the spreadsheet.
"""
import math

STATS = ['HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe']
ATTACK_TYPES = ['NORMAL', 'FIGHTING', 'FLYING', 'POISON', 'GROUND', 'ROCK', 'BUG', 'GHOST', 'STEEL',
                'FIRE', 'WATER', 'GRASS', 'ELECTRIC', 'PSYCHIC', 'ICE', 'DRAGON', 'DARK', 'FAIRY']

# ---------------------------------------------------------------- move tables
EXCLUDE = set('''DREAMEATER FOCUSPUNCH SYNCHRONOISE BELCH LASTRESORT SNORE SPITUP FLING NATURALGIFT PRESENT BEATUP
HIDDENPOWER SELFDESTRUCT EXPLOSION MISTYEXPLOSION MEMENTO FINALGAMBIT COUNTER MIRRORCOAT METALBURST BIDE ENDEAVOR
SUPERFANG NATURESMADNESS RUINATION GUARDIANOFALOLA COMEUPPANCE FISSURE SHEERCOLD GUILLOTINE HORNDRILL FRUSTRATION
FLAIL REVERSAL PUNISHMENT STOREDPOWER POWERTRIP TRUMPCARD SONICBOOM DRAGONRAGE PSYWAVE FAKEOUT FEINT SKYDROP SHELLTRAP
BURNUP ROLLOUT ICEBALL UPROAR FURYCUTTER ECHOEDVOICE ROUND SPLASH CELEBRATE HOLDHANDS FEVERPITCH VENGEFULHEX MAGNITUDE
FIRSTIMPRESSION STEELROLLER POLTERGEIST ROUND SNIPESHOT HYPERSPACEFURY LIGHTOFRUIN FUTURESIGHT DOOMDESIRE
SEISMICTOSS NIGHTSHADE STRUGGLE BEAKBLAST SPECTRALTHIEF ATTACKORDER'''.split())
# ATTACKORDER is fine actually; keep it
EXCLUDE.discard('ATTACKORDER')

VARIABLE_POWER = {'RETURN': 102, 'LOWKICK': 70, 'GRASSKNOT': 70, 'CRUSHGRIP': 70, 'WRINGOUT': 70, 'HARDPRESS': 60}
TWO_TURN = set('FLY DIG DIVE BOUNCE PHANTOMFORCE SHADOWFORCE SOLARBEAM SOLARBLADE SKYATTACK SKULLBASH RAZORWIND '
               'FREEZESHOCK ICEBURN GEOMANCY ELECTROSHOT SKYDROP METEORBEAM'.split())
TWO_HIT = {'0BD', '17E'}           # Double Kick, Dragon Darts...
MULTI_HIT = {'0C0', '307'}         # 2-5 hits (incl. Scale Shot)
STAT_DROP = set('''CLOSECOMBAT SUPERPOWER OVERHEAT DRACOMETEOR LEAFSTORM PSYCHOBOOST FLEURCANNON VCREATE HAMMERARM
MAKEITRAIN ARMORCANNON HEADLONGRUSH DRAGONASCENT CLANGINGSCALES SPINOUT ICEHAMMER HYPERSPACEHOLE'''.split())
LOCKING = set('OUTRAGE PETALDANCE THRASH RAGINGFURY'.split())
HEAVY_RECOIL = set('HEADSMASH LIGHTOFRUIN STEELBEAM MINDBLOWN CHLOROBLAST'.split())
PIVOT = set('UTURN VOLTSWITCH FLIPTURN'.split())
BITE = set('BITE CRUNCH FIREFANG ICEFANG THUNDERFANG POISONFANG PSYCHICFANGS JAWLOCK FISHIOUSREND HYPERFANG'.split())
PULSE = set('AURASPHERE DARKPULSE DRAGONPULSE WATERPULSE ORIGINPULSE TERRAINPULSE HEALPULSE'.split())

SETUP_PHYS = ['FILLETAWAY', 'SHELLSMASH', 'DRAGONDANCE', 'VICTORYDANCE', 'SHIFTGEAR', 'NORETREAT', 'CLANGOROUSSOUL', 'SWORDSDANCE',
              'BULKUP', 'COIL', 'TIDYUP', 'HONECLAWS', 'CURSE', 'HOWL']
SETUP_SPEC = ['FILLETAWAY', 'SHELLSMASH', 'QUIVERDANCE', 'TAILGLOW', 'CLANGOROUSSOUL', 'NORETREAT', 'NASTYPLOT', 'CALMMIND',
              'TAKEHEART', 'GEOMANCY', 'WORKUP', 'GROWTH']
RECOVERY = ['RECOVER', 'ROOST', 'SLACKOFF', 'SOFTBOILED', 'MILKDRINK', 'SHOREUP', 'STRENGTHSAP', 'MOONLIGHT',
            'MORNINGSUN', 'SYNTHESIS', 'JUNGLEHEALING', 'LUNARBLESSING', 'HEALORDER', 'WISH', 'REST']
STATUS_PHYS_WALL = ['WILLOWISP', 'SPORE', 'TOXIC', 'THUNDERWAVE', 'GLARE', 'YAWN']
STATUS_SPEC_WALL = ['SPORE', 'TOXIC', 'THUNDERWAVE', 'GLARE', 'WILLOWISP', 'YAWN']
HAZARDS = ['STEALTHROCK', 'SPIKES', 'STICKYWEB', 'TOXICSPIKES']
UTILITY = ['KNOCKOFF', 'UTURN', 'VOLTSWITCH', 'FLIPTURN', 'PARTINGSHOT', 'DEFOG', 'RAPIDSPIN', 'MORTALSPIN',
           'LEECHSEED', 'HAZE', 'WHIRLWIND', 'ROAR', 'TAUNT', 'PROTECT']

# ---------------------------------------------------------------- abilities
# flat strategic value (roughly -10..10) and which roles it applies to.
# 'any' | 'att' (attackers) | 'phys' | 'spec' | 'def' (walls) | 'fast'
AB_FLAT = {
    'SPEEDBOOST': (9, 'att'), 'PROTEAN': (3, 'any'), 'LIBERO': (3, 'any'), 'REGENERATOR': (8, 'any'),
    'INTIMIDATE': (7, 'any'), 'DROUGHT': (6, 'any'), 'DRIZZLE': (6, 'any'), 'SANDSTREAM': (4, 'any'),
    'SNOWWARNING': (4, 'any'), 'MULTISCALE': (8, 'any'), 'SHADOWSHIELD': (8, 'any'), 'PRANKSTER': (7, 'def'),
    'MAGICBOUNCE': (7, 'any'), 'DELTASTREAM': (8, 'any'), 'DESOLATELAND': (8, 'any'), 'PRIMORDIALSEA': (8, 'any'),
    'BEASTBOOST': (7, 'att'), 'MOXIE': (7, 'att'), 'SIMPLE': (4, 'any'), 'UNAWARE': (8, 'def'), 'POISONHEAL': (8, 'any'),
    'DISGUISE': (8, 'any'), 'GOODASGOLD': (7, 'any'), 'PROTOSYNTHESIS': (4, 'att'), 'QUARKDRIVE': (4, 'att'),
    'ELECTRICSURGE': (5, 'any'), 'PSYCHICSURGE': (5, 'any'), 'GRASSYSURGE': (5, 'any'), 'MISTYSURGE': (5, 'any'),
    'ICESCALES': (7, 'any'), 'FLUFFY': (6, 'any'), 'FURCOAT': (9, 'any'), 'THICKFAT': (5, 'any'), 'LEVITATE': (5, 'any'),
    'SWIFTSWIM': (4, 'att'), 'CHLOROPHYLL': (4, 'att'), 'SANDRUSH': (4, 'att'), 'SLUSHRUSH': (4, 'att'),
    'SURGESURFER': (3, 'att'), 'UNBURDEN': (4, 'att'), 'MAGICGUARD': (7, 'any'), 'WONDERGUARD': (10, 'any'),
    'NATURALCURE': (4, 'any'), 'SERENEGRACE': (5, 'any'), 'STURDY': (3, 'any'), 'FILTER': (4, 'any'),
    'SOLIDROCK': (4, 'any'), 'PRISMARMOR': (4, 'any'), 'MARVELSCALE': (4, 'def'), 'IRONBARBS': (3, 'def'),
    'ROUGHSKIN': (3, 'any'), 'FLAMEBODY': (3, 'def'), 'STATIC': (2, 'def'), 'EFFECTSPORE': (2, 'def'),
    'POISONPOINT': (1, 'def'), 'CURSEDBODY': (2, 'def'), 'WATERABSORB': (4, 'any'), 'VOLTABSORB': (4, 'any'),
    'FLASHFIRE': (4, 'any'), 'SAPSIPPER': (4, 'any'), 'STORMDRAIN': (4, 'any'), 'LIGHTNINGROD': (4, 'any'),
    'MOTORDRIVE': (4, 'any'), 'DRYSKIN': (3, 'any'), 'EARTHEATER': (4, 'any'), 'WELLBAKEDBODY': (4, 'any'),
    'PURIFYINGSALT': (7, 'any'), 'ARMORTAIL': (3, 'any'), 'QUEENLYMAJESTY': (3, 'any'), 'DAZZLING': (3, 'any'),
    'BULLETPROOF': (3, 'any'), 'SOUNDPROOF': (2, 'any'), 'HEATPROOF': (3, 'any'), 'WATERBUBBLE': (5, 'any'),
    'DAUNTLESSSHIELD': (6, 'any'), 'INTREPIDSWORD': (6, 'att'), 'DOWNLOAD': (5, 'att'), 'MOLDBREAKER': (3, 'att'),
    'TERAVOLT': (3, 'att'), 'TURBOBLAZE': (3, 'att'), 'INFILTRATOR': (2, 'att'), 'SCRAPPY': (2, 'att'),
    'MINDSEYE': (2, 'att'), 'DEFIANT': (3, 'att'), 'COMPETITIVE': (3, 'att'), 'JUSTIFIED': (2, 'att'),
    'STAMINA': (4, 'def'), 'WATERCOMPACTION': (2, 'def'), 'WEAKARMOR': (-1, 'any'), 'SHEDSKIN': (3, 'any'),
    'HYDRATION': (1, 'any'), 'GUTS': (2, 'phys'), 'TOXICBOOST': (2, 'phys'), 'FLAREBOOST': (2, 'spec'),
    'QUICKFEET': (3, 'att'), 'TRACE': (3, 'any'), 'IMPOSTER': (8, 'any'), 'ILLUSION': (3, 'any'),
    'SHADOWTAG': (7, 'any'), 'ARENATRAP': (5, 'any'), 'MAGNETPULL': (3, 'any'), 'PRESSURE': (2, 'def'),
    'TRIAGE': (3, 'def'), 'COMATOSE': (5, 'any'), 'ZEROTOHERO': (8, 'any'), 'ORICHALCUMPULSE': (7, 'phys'),
    'HADRONENGINE': (7, 'spec'), 'SWORDOFRUIN': (5, 'phys'), 'BEADSOFRUIN': (5, 'spec'), 'TABLETSOFRUIN': (5, 'def'),
    'VESSELOFRUIN': (5, 'def'), 'SUPREMEOVERLORD': (3, 'att'), 'OPPORTUNIST': (2, 'att'), 'CONTRARY': (6, 'att'),
    'MOODY': (6, 'any'), 'SPEEDBOOST_': (0, 'any'), 'ANGERSHELL': (4, 'att'), 'BERSERK': (3, 'att'),
    'WINDRIDER': (3, 'att'), 'SEEDSOWER': (3, 'any'), 'TOXICDEBRIS': (3, 'def'), 'CUDCHEW': (2, 'any'),
    'GOOEY': (2, 'def'), 'TANGLINGHAIR': (2, 'def'), 'COTTONDOWN': (2, 'def'), 'PERISHBODY': (0, 'any'),
    'MIRRORARMOR': (3, 'any'), 'GUARDDOG': (4, 'any'), 'STALWART': (1, 'any'), 'PROPELLERTAIL': (1, 'any'),
    'GRASSPELT': (2, 'def'), 'ICEBODY': (1, 'def'), 'RAINDISH': (1, 'def'), 'HARVEST': (3, 'def'), 'OVERCOAT': (1, 'any'),
    'CLEARBODY': (2, 'any'), 'WHITESMOKE': (2, 'any'), 'FULLMETALBODY': (2, 'any'), 'INNERFOCUS': (1, 'any'),
    'OWNTEMPO': (1, 'any'), 'OBLIVIOUS': (1, 'any'), 'KEENEYE': (0, 'any'), 'BIGPECKS': (0, 'any'),
    'SCHOOLING': (6, 'any'), 'STANCECHANGE': (6, 'any'), 'POWERCONSTRUCT': (7, 'any'), 'SHIELDSDOWN': (5, 'any'),
    'BATTLEBOND': (5, 'att'), 'ZENMODE': (0, 'any'), 'ICEFACE': (4, 'any'), 'GULPMISSILE': (3, 'any'),
    'MIMICRY': (1, 'any'), 'NEUTRALIZINGGAS': (3, 'any'), 'UNNERVE': (1, 'any'), 'ASONEGRIM': (8, 'att'),
    'ASONECHILLING': (8, 'att'), 'GRIMNEIGH': (7, 'spec'), 'CHILLINGNEIGH': (7, 'phys'), 'TERASHELL': (5, 'any'),
    'TERAFORMZERO': (3, 'any'), 'TERASHIFT': (3, 'any'), 'POISONPUPPETEER': (2, 'any'), 'TOXICCHAIN': (4, 'any'),
    'EMBODYASPECT': (4, 'any'), 'ELECTROMORPHOSIS': (2, 'att'), 'WINDPOWER': (2, 'att'), 'THERMALEXCHANGE': (3, 'any'),
    'HOSPITALITY': (1, 'any'), 'COSTAR': (1, 'any'), 'COMMANDER': (1, 'any'), 'LINGERINGAROMA': (1, 'any'),
    'SUPERSWEETSYRUP': (2, 'any'), 'MYCELIUMMIGHT': (3, 'def'), 'STEAMENGINE': (3, 'any'), 'RATTLED': (1, 'any'),
    'CURIOUSMEDICINE': (1, 'any'), 'SCREENCLEANER': (0, 'any'), 'QUICKDRAW': (2, 'att'), 'BALLFETCH': (0, 'any'),
    'POWERSPOT': (0, 'any'), 'STEELYSPIRIT': (0, 'any'), 'PASTELVEIL': (2, 'any'), 'LIMBER': (1, 'any'),
    'IMMUNITY': (1, 'any'), 'INSOMNIA': (2, 'any'), 'VITALSPIRIT': (2, 'any'), 'SWEETVEIL': (1, 'any'),
    'LEAFGUARD': (1, 'any'), 'FLOWERVEIL': (0, 'any'), 'AROMAVEIL': (1, 'any'), 'FRIENDGUARD': (0, 'any'),
    'HEALER': (1, 'any'), 'SYMBIOSIS': (0, 'any'), 'TELEPATHY': (0, 'any'), 'FOREWARN': (0, 'any'),
    'ANTICIPATION': (0, 'any'), 'FRISK': (1, 'any'), 'SYNCHRONIZE': (1, 'any'), 'CUTECHARM': (0, 'any'),
    'STENCH': (0, 'any'), 'SHIELDDUST': (2, 'any'), 'SHELLARMOR': (1, 'any'), 'BATTLEARMOR': (1, 'any'),
    'STICKYHOLD': (1, 'any'), 'SUCTIONCUPS': (1, 'any'), 'WONDERSKIN': (3, 'def'), 'AFTERMATH': (1, 'any'),
    'INNARDSOUT': (2, 'any'), 'LIQUIDOOZE': (1, 'def'), 'MUMMY': (1, 'any'), 'WANDERINGSPIRIT': (1, 'any'),
    'IRONBARBS_': (0, 'any'), 'GLUTTONY': (1, 'any'), 'CHEEKPOUCH': (1, 'any'), 'RIPEN': (1, 'any'),
    'EMERGENCYEXIT': (1, 'any'), 'WIMPOUT': (1, 'any'), 'DANCER': (1, 'any'), 'RECEIVER': (0, 'any'),
    'POWEROFALCHEMY': (0, 'any'), 'BATTERY': (0, 'any'), 'PLUS': (0, 'any'), 'MINUS': (0, 'any'),
    'HONEYGATHER': (0, 'any'), 'PICKUP': (0, 'any'), 'RUNAWAY': (0, 'any'), 'ILLUMINATE': (0, 'any'),
    'MAGICIAN': (1, 'att'), 'PICKPOCKET': (1, 'any'), 'TANGLEDFEET': (0, 'any'), 'SANDVEIL': (0, 'any'),
    'SNOWCLOAK': (1, 'any'), 'EARLYBIRD': (1, 'any'), 'COLORCHANGE': (1, 'any'), 'FORECAST': (1, 'any'),
    'FLOWERGIFT': (2, 'any'), 'MULTITYPE': (5, 'any'), 'RKSSYSTEM': (3, 'any'), 'AIRLOCK': (3, 'any'),
    'CLOUDNINE': (2, 'any'), 'DAMP': (0, 'any'), 'HUNGERSWITCH': (1, 'any'), 'SANDSPIT': (2, 'any'),
    'MERCILESS': (2, 'att'), 'CORROSION': (3, 'def'), 'POISONTOUCH': (2, 'phys'), 'ANGERPOINT': (1, 'att'),
    'STEADFAST': (1, 'att'), 'RIVALRY': (0, 'att'), 'FAIRYAURA': (0, 'att'), 'DARKAURA': (0, 'att'), 'AURABREAK': (1, 'any'),
    'SNIPER': (1, 'att'), 'SUPERLUCK': (2, 'att'), 'LONGREACH': (1, 'phys'), 'UNSEENFIST': (2, 'phys'),
    'EELEVATE': (3, 'any'), 'MEGASOL': (4, 'any'), 'PIERCINGDRILL': (2, 'att'), 'VICTORYSTAR': (1, 'att'),
    'SOULHEART': (4, 'spec'), 'NEUROFORCE': (2, 'att'), 'HEAVYMETAL': (0, 'any'), 'LIGHTMETAL': (0, 'any'),
    'FIREMANE': (0, 'any'), 'MAGMAARMOR': (1, 'any'), 'WATERVEIL': (1, 'any'), 'BLAZE': (1, 'att'),
    'TORRENT': (1, 'att'), 'OVERGROW': (1, 'att'), 'SWARM': (1, 'att'),
    # negatives
    'TRUANT': (-10, 'any'), 'SLOWSTART': (-8, 'any'), 'DEFEATIST': (-5, 'any'), 'KLUTZ': (-4, 'any'),
    'STALL': (-3, 'any'), 'NORMALIZE': (-3, 'any'),
    # Rejuvenation custom abilities
    'CHIFOCUS': (3, 'att'), 'COALFURNACE': (4, 'any'), 'DEADEYE': (2, 'att'), 'DEFRAGMENT': (5, 'any'),
    'DESSERTTRAY': (4, 'def'), 'EXTRAFLUFFYMANE': (8, 'any'), 'FOAMSPRAY': (3, 'any'), 'GRAVITYCONTROL': (5, 'any'),
    'HOTSHOT': (3, 'att'), 'INEXORABLE': (2, 'att'), 'INVIGORATE': (3, 'def'), 'JUNGLEBEAT': (2, 'any'),
    'LUNARIDOL': (4, 'any'), 'SOLARIDOL': (4, 'any'), 'MEMORYLEAK': (2, 'any'), 'POLLENFLIGHT': (5, 'any'),
    'PROTECTIVERIME': (5, 'any'), 'QUAKEPROOF': (3, 'any'), 'REFLECTOR': (5, 'any'), 'RESUSCITATION': (6, 'any'),
    'SACCHARINENECTAR': (4, 'any'), 'SOULEATER': (4, 'any'), 'SWORNDUTY': (1, 'any'), 'WATERBARRAGE': (5, 'any'),
    'WILDFIRE': (5, 'any'),
}


def ability_move_mult(ab, mv, mtype, stab_types):
    """Return (new_type, multiplier, stab_override) for a damaging move under ability ab."""
    mid, m = mv
    flags = set(m.get('DataFlags') or [])
    power = m['_power']
    mult = 1.0
    t = mtype
    if ab in ('AERILATE', 'PIXILATE', 'REFRIGERATE', 'GALVANIZE', 'DRAGONIZE') and t == 'NORMAL':
        t = {'AERILATE': 'FLYING', 'PIXILATE': 'FAIRY', 'REFRIGERATE': 'ICE', 'GALVANIZE': 'ELECTRIC',
             'DRAGONIZE': 'DRAGON'}[ab]
        mult *= 1.2
    if ab == 'LIQUIDVOICE' and 'Soundmove' in flags:
        t = 'WATER'
    if ab == 'NORMALIZE':
        t = 'NORMAL'; mult *= 1.2
    if ab == 'TECHNICIAN' and power <= 60:
        mult *= 1.5
    if ab == 'IRONFIST' and 'Punchmove' in flags:
        mult *= 1.2
    if ab == 'STRONGJAW' and mid in BITE:
        mult *= 1.5
    if ab == 'MEGALAUNCHER' and mid in PULSE:
        mult *= 1.5
    if ab == 'SHARPNESS' and 'Sharpmove' in flags:
        mult *= 1.5
    if ab == 'TOUGHCLAWS' and 'Contact' in flags:
        mult *= 1.3
    if ab == 'RECKLESS' and 'Recoil' in flags:
        mult *= 1.2
    if ab == 'SHEERFORCE' and m.get('Chance') not in (None, '', '0', '100'):
        mult *= 1.3
    if ab in ('PUNKROCK',) and 'Soundmove' in flags:
        mult *= 1.3
    if ab == 'JUNGLEBEAT' and ('Soundmove' in flags or t == 'GRASS'):
        mult *= 1.3
    if ab == 'STEELWORKER' and t == 'STEEL':
        mult *= 1.5
    if ab == 'WATERBUBBLE' and t == 'WATER':
        mult *= 2.0
    if ab == 'TRANSISTOR' and t == 'ELECTRIC':
        mult *= 1.3
    if ab == 'DRAGONSMAW' and t == 'DRAGON':
        mult *= 1.5
    if ab == 'ROCKYPAYLOAD' and t == 'ROCK':
        mult *= 1.5
    if ab == 'SOLARIDOL' and t == 'FIRE':
        mult *= 1.5
    if ab == 'LUNARIDOL' and t == 'ICE':
        mult *= 1.5
    if ab == 'COALFURNACE' and t == 'FIRE':
        mult *= 1.1
    if ab == 'FAIRYAURA' and t == 'FAIRY':
        mult *= 1.33
    if ab == 'DARKAURA' and t == 'DARK':
        mult *= 1.33
    if ab == 'HOTSHOT' and (flags & {'Shotmove'} or 'BALL' in mid or 'BOMB' in mid or 'KICK' in mid):
        mult *= 1.3
    if ab in ('BLAZE', 'TORRENT', 'OVERGROW', 'SWARM') and t == {'BLAZE': 'FIRE', 'TORRENT': 'WATER',
                                                               'OVERGROW': 'GRASS', 'SWARM': 'BUG'}[ab]:
        mult *= 1.05
    if ab == 'SKILLLINK' and m['Effect'] in MULTI_HIT:
        mult *= 5 / 3.1
    if ab == 'ROCKHEAD' and ('Recoil' in flags or mid in HEAVY_RECOIL):
        mult *= 1 / m['_drawback'] if m['_drawback'] < 1 else 1
    if ab == 'HUSTLE' and m['Category'] == 'Physical':
        mult *= 0.85  # accuracy loss (power gain handled in stat mult)
    stab = None
    if ab in ('PROTEAN', 'LIBERO'):
        stab = 1.5
    if ab == 'ADAPTABILITY' and t in stab_types:
        stab = 2.0
    return t, mult, stab


def ability_stat_mult(ab):
    """(atk_mult, spa_mult, general_mult)"""
    return {
        'HUGEPOWER': (2.0, 1, 1), 'PUREPOWER': (2.0, 1, 1), 'GORILLATACTICS': (1.5, 1, 1), 'HUSTLE': (1.5, 1, 1),
        'GUTS': (1.5, 1, 1), 'TOXICBOOST': (1.5, 1, 1), 'FLAREBOOST': (1, 1.5, 1), 'SOLARPOWER': (1, 1.25, 1),
        'TINTEDLENS': (1, 1, 1.12), 'PARENTALBOND': (1, 1, 1.25), 'DEADEYE': (1, 1, 1.12), 'SNIPER': (1, 1, 1.03),
        'INEXORABLE': (1, 1, 1.12), 'ANALYTIC': (1, 1, 1.08), 'CHIFOCUS': (1, 1, 1.1), 'SUPERLUCK': (1, 1, 1.03),
        'SOLARIDOL': (1.15, 1, 1), 'LUNARIDOL': (1, 1.15, 1), 'MEGASOL': (1, 1, 1.05),
        'ORICHALCUMPULSE': (1.2, 1, 1), 'HADRONENGINE': (1, 1.2, 1), 'SWORDOFRUIN': (1.15, 1, 1),
        'BEADSOFRUIN': (1, 1.15, 1), 'STAKEOUT': (1, 1, 1.05), 'SANDFORCE': (1, 1, 1.03),
    }.get(ab, (1, 1, 1))


# ---------------------------------------------------------------- core helpers
def type_eff(atk_type, def_type, chart):
    d = chart.get(def_type, {})
    if atk_type in d.get('Immunities', []):
        return 0.0
    if atk_type in d.get('Weaknesses', []):
        return 2.0
    if atk_type in d.get('Resistances', []):
        return 0.5
    return 1.0


def move_base_value(mid, m, ctx):
    """Expected power per use before stat/ability; also stores drawback factor."""
    try:
        p = int(m.get('Strength') or 0)
    except ValueError:
        p = 0
    if mid in VARIABLE_POWER:
        p = VARIABLE_POWER[mid]
    elif mid in ('HEAVYSLAM', 'HEATCRASH'):
        w = ctx['weight']
        p = 100 if w >= 200 else 80 if w >= 100 else 60 if w >= 50 else 40
    elif mid == 'GYROBALL':
        s = ctx['spe']; p = 120 if s <= 40 else 90 if s <= 60 else 60 if s <= 80 else 40
    elif mid == 'ELECTROBALL':
        s = ctx['spe']; p = 100 if s >= 110 else 80 if s >= 90 else 60
    if p <= 1:
        return 0, 1
    acc = int(m.get('Accuracy') or 0)
    accf = 1.0 if acc == 0 else acc / 100
    eff = m['Effect']
    flags = set(m.get('DataFlags') or [])
    if eff in TWO_HIT or mid in ('DUALCHOP', 'BONEMERANG', 'DOUBLEHIT', 'GEARGRIND', 'TWINBEAM', 'DOUBLEIRONBASH',
                                 'TACHYONCUTTER', 'DUALWINGBEAT', 'DOUBLEKICK', 'DRAGONDARTS'):
        p *= 2
    elif eff in MULTI_HIT:
        p *= 3.1
    elif mid == 'TRIPLEAXEL':
        p = 94
    elif mid == 'TRIPLEKICK':
        p = 47
    elif mid == 'SURGINGSTRIKES':
        p = 25 * 3 * 1.5
    elif mid == 'WICKEDBLOW':
        p = p * 1.5
    elif mid == 'POPULATIONBOMB':
        p = 110
    draw = 1.0
    if 'Cooldown' in flags or eff == '0C2':
        draw = 0.45
    elif 'Chargetime' in flags or mid in TWO_TURN:
        draw = 0.45
    elif mid in HEAVY_RECOIL:
        draw = 0.6
    elif 'Recoil' in flags:
        draw = 0.9
    elif mid in STAT_DROP:
        draw = 0.88
    elif mid in LOCKING:
        draw = 0.85
    if mid in PIVOT:
        draw *= 1.1
    pr = int(m.get('Priority') or 0)
    if pr > 0 and mid not in ('AVALANCHE', 'REVENGE', 'VITALTHROW', 'CIRCLETHROW', 'DRAGONTAIL', 'DELUGE'):
        draw *= 1.4 if ctx['spe'] < 80 else 1.15
    if ctx.get('setup') and mid in STAT_DROP:
        draw *= 0.75
    if mid == 'KNOCKOFF':
        draw *= 1.35
    if mid in ('PAYBACK', 'AVALANCHE', 'REVENGE', 'ASSURANCE', 'DELUGE'):
        draw *= 0.8
    return p * accf, draw


def nature_for(focus, fast, wall_side=None, wall_attack=None, def_lower=None):
    if wall_side == 'Def':
        return 'Impish (+Def, -SpA)' if wall_attack == 'Physical' else 'Bold (+Def, -Atk)'
    if wall_side == 'SpD':
        return 'Careful (+SpD, -SpA)' if wall_attack == 'Physical' else 'Calm (+SpD, -Atk)'
    if focus == 'Physical':
        return 'Jolly (+Spe, -SpA)' if fast else 'Adamant (+Atk, -SpA)'
    if focus == 'Special':
        return 'Timid (+Spe, -Atk)' if fast else 'Modest (+SpA, -Atk)'
    # mixed
    if fast:
        return 'Hasty (+Spe, -Def)' if def_lower == 'Def' else 'Naive (+Spe, -SpD)'
    return 'Lonely (+Atk, -Def)' if def_lower == 'Def' else 'Naughty (+Atk, -SpD)'


def recommend(stats, types, abilities, learn, moves_db, chart, weight, is_nfe):
    """stats: dict; types: list of type ids; abilities: list of ability ids;
    learn: set of move ids; returns dict of recommendation fields."""
    hp, atk, de, spa, spd, spe = (stats[s] for s in STATS)
    ctx = {'weight': weight, 'spe': spe, 'setup': False}
    damaging = []
    for mid in learn:
        m = moves_db.get(mid)
        if not m or m['Category'] == 'Status' or mid in EXCLUDE or m['Type'] in ('SHADOW', 'QMARKS'):
            continue
        p, draw = move_base_value(mid, m, ctx)
        if p <= 0:
            continue
        m = dict(m); m['_power'] = p; m['_drawback'] = draw
        damaging.append((mid, m))

    def attack_stat(m, am):
        if m['MoveName'] == 'Body Press':
            return de
        if m['MoveName'] == 'Foul Play':
            return 80
        return atk * am[0] if m['Category'] == 'Physical' else spa * am[1]

    def build_attacks(ab, n_slots, restrict=None):
        am = ability_stat_mult(ab)
        scored = []
        for mid, m in damaging:
            t, mult, stab_o = ability_move_mult(ab, (mid, m), m['Type'], types)
            stab = stab_o if stab_o else (1.5 if t in types else 1.0)
            if restrict and m['Category'] != restrict and m['MoveName'] != 'Body Press':
                mult *= 0.35
            val = m['_power'] * m['_drawback'] * mult * stab * attack_stat(m, am) * am[2]
            scored.append((val, mid, t, m))
        scored.sort(reverse=True)
        # keep best 2 per type to limit search
        per_type, cands = {}, []
        for s in scored:
            if per_type.get(s[2], 0) < 2:
                cands.append(s); per_type[s[2]] = per_type.get(s[2], 0) + 1
        chosen = []
        if not cands:
            return [], 0.0, scored
        stab_c = [c for c in cands if c[2] in types or ab in ('PROTEAN', 'LIBERO')]
        if stab_c and stab_c[0][0] >= 0.6 * cands[0][0]:
            chosen.append(stab_c[0])
        else:
            chosen.append(cands[0])

        def objective(sel):
            tot = 0.0
            for dt in ATTACK_TYPES:
                tot += max(c[0] * type_eff(c[2], dt.capitalize(), chart) for c in sel)
            return tot / len(ATTACK_TYPES)
        while len(chosen) < n_slots:
            base = objective(chosen)
            best, gain = None, 0
            used_types = {c[2] for c in chosen}
            for c in cands:
                if c in chosen or c[2] in used_types:
                    continue
                g = objective(chosen + [c]) - base
                if g > gain:
                    best, gain = c, g
            if not best or gain < 0.02 * base:
                break
            chosen.append(best)
        return chosen, objective(chosen), scored

    # --- role
    fast = spe >= 70
    atk_for_role = atk * (2 if any(a in ('HUGEPOWER', 'PUREPOWER') for a in abilities) else 1)
    off = max(atk_for_role, spa)
    bulk_avg = (hp + de + spd) / 3
    if atk_for_role >= spa * 1.12:
        focus = 'Physical'
    elif spa >= atk_for_role * 1.12:
        focus = 'Special'
    else:
        # compare actual move quality
        phys = build_attacks(None, 2, 'Physical')[1]
        spec = build_attacks(None, 2, 'Special')[1]
        focus = 'Physical' if phys > spec * 1.1 else 'Special' if spec > phys * 1.1 else 'Mixed'
    is_wall = (off < 75 and bulk_avg >= 70) or (bulk_avg >= 70 and bulk_avg >= off * 0.95 and off < 100 and spe < 85)
    if hp == 1:  # Shedinja
        is_wall = False

    setup_list = SETUP_PHYS if focus == 'Physical' else SETUP_SPEC if focus == 'Special' else ['SHELLSMASH', 'WORKUP']
    setup = next((s for s in setup_list if s in learn and not (s == 'CURSE' and spe >= 60 and 'GHOST' not in types)
                  and not (s == 'CURSE' and 'GHOST' in types)), None)

    # --- ability choice
    restrict = None if focus == 'Mixed' else focus
    neutral_val = build_attacks(None, 4, restrict)[1] or 1
    role_tag = 'def' if is_wall else 'att'
    ab_scores = []
    for ab in abilities:
        if not ab:
            continue
        flat, applies = AB_FLAT.get(ab, (0, 'any'))
        ok = applies == 'any' or applies == role_tag or (applies in ('phys', 'spec') and not is_wall and
                                                          ((applies == 'phys') == (focus != 'Special')))
        if ab == 'SPEEDBOOST' and is_wall:
            ok = True; flat = 4
        if ab == 'SIMPLE' and setup:
            flat = 8
        if ab == 'CONTRARY' and any(x in learn for x in ('LEAFSTORM', 'OVERHEAT', 'DRACOMETEOR', 'SUPERPOWER',
                                                         'VCREATE', 'PSYCHOBOOST', 'FLEURCANNON')):
            flat = 9
        val = build_attacks(ab, 4, restrict)[1]
        weight_off = 0.35 if is_wall else 1.0
        total = (flat if ok else flat * 0.3) + 12 * (val / neutral_val - 1) * weight_off
        ab_scores.append((round(total, 2), ab))
    ab_scores.sort(key=lambda x: -x[0])
    best_ab = ab_scores[0][1] if ab_scores else None

    # --- moveset
    moveset, notes = [], []
    item = None
    if is_wall:
        wall_side = 'Def' if de >= spd else 'SpD'
        rec = next((r for r in RECOVERY if r in learn), None)
        if rec == 'REST' and 'LEECHSEED' in learn:
            rec = 'LEECHSEED'
        status_order = STATUS_PHYS_WALL if wall_side == 'Def' else STATUS_SPEC_WALL
        status = next((s for s in status_order if s in learn), None)
        hazard = next((h for h in HAZARDS if h in learn), None)
        util = next((u for u in UTILITY if u in learn and u != 'PROTECT'), None)
        n_att = 1 if rec else 2
        if not status:
            n_att += 1
        if not (hazard or util):
            n_att += 1
        attacks, _, _ = build_attacks(best_ab, n_att, None)
        wall_attack = attacks[0][3]['Category'] if attacks else 'Special'
        for x in (rec, status, hazard or util):
            if x:
                moveset.append(moves_db[x]['MoveName'])
        if rec == 'WISH' and 'PROTECT' in learn and len(moveset) < 4 and n_att > 1:
            moveset.append('Protect'); attacks = attacks[:max(0, 4 - len(moveset))]
        for a in attacks:
            if len(moveset) < 4:
                moveset.append(a[3]['MoveName'])
        if len(moveset) < 4 and 'PROTECT' in learn:
            moveset.append('Protect')
        role = ('Physical' if wall_side == 'Def' else 'Special') + ' Wall'
        nature = nature_for(None, False, wall_side, wall_attack)
        evs = {'HP': 252, wall_side: 252, ('SpD' if wall_side == 'Def' else 'Def'): 4}
        item = 'Eviolite' if is_nfe else ('Black Sludge' if 'POISON' in types else 'Leftovers')
        if hazard:
            notes.append('Hazard setter')
        if not rec:
            notes.append('No reliable recovery in learnset')
    else:
        use_setup = setup is not None and (fast or bulk_avg >= 80 or setup in ('SHELLSMASH', 'QUIVERDANCE',
                                                                              'DRAGONDANCE', 'TAILGLOW')) and (fast or setup in ('SWORDSDANCE', 'BULKUP', 'CALMMIND', 'NASTYPLOT', 'CURSE',
                                                             'QUIVERDANCE', 'SHELLSMASH', 'DRAGONDANCE', 'COIL'))
        n_att = 3 if use_setup else 4
        if use_setup:
            ctx['setup'] = True
            damaging[:] = [(mid, dict(m, _drawback=m['_drawback'] * (0.75 if mid in STAT_DROP else 1)))
                           for mid, m in damaging]
        attacks, _, _ = build_attacks(best_ab, n_att, restrict)
        if use_setup:
            moveset.append(moves_db[setup]['MoveName'])
        moveset += [a[3]['MoveName'] for a in attacks]
        if len(moveset) < 4:
            for extra in (['UTURN', 'VOLTSWITCH', 'KNOCKOFF', 'STEALTHROCK', 'TAUNT', 'PROTECT', 'SUBSTITUTE'] +
                          ['TOXIC']):
                if extra in learn and moves_db[extra]['MoveName'] not in moveset and len(moveset) < 4:
                    moveset.append(moves_db[extra]['MoveName'])
        speed_tier = 'Fast' if spe >= 90 else 'Mid-speed' if spe >= 70 else 'Slow'
        invest_speed = spe >= 55
        if hp == 1:
            role = 'Physical Sweeper' if focus != 'Special' else 'Special Sweeper'
            evs = {'Atk' if focus != 'Special' else 'SpA': 252, 'Spe': 252, 'Def': 4}
            nature = nature_for(focus if focus != 'Mixed' else 'Physical', True)
        else:
            if use_setup:
                role = ('Setup Sweeper' if fast else 'Bulky Setup Sweeper') + f' ({focus})'
            elif focus == 'Mixed':
                role = 'Mixed Attacker'
            elif invest_speed:
                role = f'{speed_tier} {focus} Attacker'
            else:
                role = f'Bulky {focus} Wallbreaker'
            off_key = {'Physical': ['Atk'], 'Special': ['SpA'], 'Mixed': ['Atk', 'SpA']}[focus]
            if focus == 'Mixed':
                evs = {'Atk': 128, 'SpA': 128, 'Spe': 252} if invest_speed else {'HP': 252, 'Atk': 128, 'SpA': 128}
            elif invest_speed:
                evs = {off_key[0]: 252, 'Spe': 252, 'HP': 4}
            else:
                evs = {'HP': 252, off_key[0]: 252, ('Def' if de < spd else 'SpD'): 4}
            nature = nature_for(focus, invest_speed and spe >= 70, def_lower='Def' if de < spd else 'SpD')
            if spe <= 45 and not use_setup:
                notes.append('Very slow: Trick Room variant = Brave/Quiet nature, 0 Spe EVs')
        # item
        if is_nfe:
            item = 'Eviolite'
        elif best_ab in ('GUTS', 'FLAREBOOST', 'QUICKFEET'):
            item = 'Flame Orb'
        elif best_ab in ('TOXICBOOST', 'POISONHEAL'):
            item = 'Toxic Orb'
        elif best_ab == 'MAGICGUARD':
            item = 'Life Orb'
        elif use_setup and setup == 'SHELLSMASH':
            item = 'White Herb'
        elif use_setup:
            item = 'Life Orb' if fast else 'Leftovers'
        elif focus == 'Mixed':
            item = 'Life Orb'
        elif best_ab == 'GORILLATACTICS' or spe >= 95 or spe < 55:
            item = 'Choice Band' if focus == 'Physical' else 'Choice Specs'
        else:
            item = 'Choice Scarf'
        if best_ab in ('UNBURDEN',):
            item = 'Sitrus Berry / White Herb'
    alt = []
    allscored = build_attacks(best_ab, 4, None if is_wall else restrict)[2]
    for s in allscored:
        nm = s[3]['MoveName']
        if nm not in moveset and nm not in alt:
            alt.append(nm)
        if len(alt) >= 3:
            break
    for extra in (['STEALTHROCK', 'UTURN', 'VOLTSWITCH', 'KNOCKOFF', 'TAUNT', 'SUBSTITUTE'] if not is_wall else
                  ['UTURN', 'KNOCKOFF', 'HAZE', 'DEFOG', 'RAPIDSPIN', 'LEECHSEED']):
        if extra in learn and moves_db[extra]['MoveName'] not in moveset + alt and len(alt) < 5:
            alt.append(moves_db[extra]['MoveName'])
    return {
        'role': role, 'focus': focus if not is_wall else '-', 'ability': best_ab, 'ability_scores': ab_scores,
        'nature': nature, 'evs': evs, 'item': item, 'moves': (moveset + ['', '', '', ''])[:4],
        'alts': alt, 'notes': '; '.join(notes),
    }
