"""'Bring it in when...' cues (Vincent, 23 Nov): fight-independent tell-tale signs for switching a Pokémon in, from its typing, ability
and the moves its build runs (the job the old Lead / Mid / Closer roles used to tell him). Max 2 per Pokémon: one defensive
(what it switches in on), one job.
cues(types, ability, moves, chart) -> [str, str]   chart(atk_type, [def types]) -> multiplier (no field: general)"""
import re
ORDER = ['GROUND', 'FIRE', 'WATER', 'FIGHTING', 'GHOST', 'DARK', 'PSYCHIC', 'ELECTRIC', 'ICE', 'ROCK', 'FLYING', 'FAIRY', 'STEEL',
         'DRAGON', 'GRASS', 'POISON', 'BUG', 'NORMAL']
ABSORB = {'FLASHFIRE': 'FIRE', 'WELLBAKEDBODY': 'FIRE', 'WATERABSORB': 'WATER', 'STORMDRAIN': 'WATER', 'DRYSKIN': 'WATER', 'VOLTABSORB': 'ELECTRIC',
          'LIGHTNINGROD': 'ELECTRIC', 'MOTORDRIVE': 'ELECTRIC', 'SAPSIPPER': 'GRASS', 'LEVITATE': 'GROUND', 'EARTHEATER': 'GROUND'}
def _n(x): return re.sub(r'[^A-Z]', '', (x or '').upper())
# job cues, first match wins (ability, then moves)
JOB_AB = [
 ({'UNAWARE'}, 'Unaware'),
 ({'INTIMIDATE'}, 'Intimidate'),
 ({'SKILLLINK'}, 'Breaks Sash / shields'),
 ({'GRASSYSURGE'}, 'Grassy Terrain'),
 ({'ELECTRICSURGE'}, 'Electric Terrain'),
 ({'DROUGHT'}, 'Sun'),
 ({'SNOWWARNING'}, 'Snow'),
 ({'GOODASGOLD', 'MAGICBOUNCE'}, 'Status-proof'),
 ({'INSOMNIA', 'VITALSPIRIT', 'SWEETVEIL', 'PURIFYINGSALT'}, 'Sleep-proof'),
 ({'PUNKROCK'}, 'Punk Rock'),
]
JOB_MV = [
 ({'RAGEPOWDER', 'FOLLOWME'}, 'Redirection'),
 ({'SPORE', 'LOVELYKISS', 'SLEEPPOWDER', 'HYPNOSIS', 'SING', 'DARKVOID'}, 'Sleep'),
 ({'TRICKROOM'}, 'Trick Room'),
 ({'TAILWIND'}, 'Tailwind'),
 ({'HAZE', 'CLEARSMOG', 'ROAR', 'WHIRLWIND', 'DRAGONTAIL', 'CIRCLETHROW'}, 'Stat reset'),
 ({'FAKEOUT'}, 'Fake Out'),
 ({'TAUNT', 'ENCORE'}, 'Taunt'),
 ({'WILLOWISP'}, 'Burns'),
 ({'THUNDERWAVE', 'GLARE', 'NUZZLE'}, 'Paralysis'),
 ({'GASTROACID'}, 'Gastro Acid'),
 ({'KNOCKOFF'}, 'Knock Off'),
 ({'GRASSYGLIDE', 'EXTREMESPEED', 'SUCKERPUNCH', 'AQUAJET', 'SHADOWSNEAK', 'BULLETPUNCH', 'ICESHARD', 'MACHPUNCH', 'VACUUMWAVE', 'JETPUNCH', 'ACCELEROCK'},
  'Priority'),
 ({'SWORDSDANCE', 'DRAGONDANCE', 'NASTYPLOT', 'QUIVERDANCE', 'CALMMIND', 'BULKUP', 'CURSE', 'SHELLSMASH', 'COIL'}, 'Setup sweeper'),
 ({'RECOVER', 'ROOST', 'SLACKOFF', 'MOONLIGHT', 'SYNTHESIS', 'SOFTBOILED', 'WISH', 'SHOREUP', 'STRENGTHSAP', 'MORNINGSUN'}, 'Recovery'),
 ({'UTURN', 'VOLTSWITCH', 'FLIPTURN', 'PARTINGSHOT', 'TELEPORT'}, 'Pivot'),
 ({'EARTHQUAKE', 'ROCKSLIDE', 'SURF', 'HEATWAVE', 'BOOMBURST', 'DISCHARGE', 'HYPERVOICE', 'DAZZLINGGLEAM', 'MUDDYWATER', 'SLUDGEWAVE', 'BLIZZARD', 'ERUPTION', 'WATERSPOUT', 'BULLDOZE', 'ICYWIND', 'SNARL'},
  'Spread'),
]
def cues(types, ability, moves, chart):
    """23 Nov (Vincent): 1-3 word chips: [('tool', job)] green + [('stat', 'Immune X'), ('stat', 'Resists X / Y')] grey; max 3."""
    ab = _n(ability); mv = {_n(m) for m in moves}
    m = {t: chart(t, types) for t in ORDER}
    if ab in ABSORB: m[ABSORB[ab]] = 0
    imm = [t for t in ORDER if m[t] == 0]; res = [t for t in ORDER if 0 < m[t] < 1]
    out = []
    job = next((txt for s, txt in JOB_AB if ab in s), None) or next((txt for s, txt in JOB_MV if mv & s), None)
    if job: out.append(('tool', job))
    if imm: out.append(('stat', 'Immune ' + ' / '.join(t.title() for t in imm[:2])))
    if res: out.append(('stat', 'Resists ' + ' / '.join(t.title() for t in res[:2])))
    return out[:3]
