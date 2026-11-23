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
 ({'UNAWARE'}, 'a foe has boosted its stats (Unaware ignores boosts)'),
 ({'INTIMIDATE'}, 'physical attackers are hitting hard (Intimidate)'),
 ({'SKILLLINK'}, 'a foe hides behind Focus Sash, Sturdy, Substitute or boss shields (5-hit moves)'),
 ({'GRASSYSURGE'}, 'you want Grassy Terrain: heals each turn, halves Earthquake'),
 ({'ELECTRICSURGE'}, 'you want Electric Terrain: no sleep, Electric moves x1.3'),
 ({'DROUGHT'}, 'you want sun: Fire moves up, Water moves down'),
 ({'SNOWWARNING'}, 'you want snow: Ice types get Def x1.5, Blizzard never misses'),
 ({'GOODASGOLD', 'MAGICBOUNCE'}, 'foes rely on status moves (Taunt, sleep, Perish Song)'),
 ({'INSOMNIA', 'VITALSPIRIT', 'SWEETVEIL', 'PURIFYINGSALT'}, 'sleep is the threat (it cannot fall asleep)'),
 ({'PUNKROCK'}, 'you want sound spam (Punk Rock)'),
]
JOB_MV = [
 ({'RAGEPOWDER', 'FOLLOWME'}, 'a partner needs free turns to attack or set up (redirection)'),
 ({'SPORE', 'LOVELYKISS', 'SLEEPPOWDER', 'HYPNOSIS', 'SING', 'DARKVOID'}, 'one foe has to be taken out of the fight (sleep)'),
 ({'TRICKROOM'}, 'their team is faster than yours (Trick Room)'),
 ({'TAILWIND'}, 'you need to outspeed them (Tailwind)'),
 ({'HAZE', 'CLEARSMOG', 'ROAR', 'WHIRLWIND', 'DRAGONTAIL', 'CIRCLETHROW'}, 'a foe has boosted its stats (reset / phaze)'),
 ({'FAKEOUT'}, 'you need a free turn right away (Fake Out)'),
 ({'TAUNT', 'ENCORE'}, 'a foe sets up, heals or uses status (Taunt / Encore)'),
 ({'WILLOWISP'}, 'a physical attacker is the problem (burn)'),
 ({'THUNDERWAVE', 'GLARE', 'NUZZLE'}, 'a fast foe outspeeds you (paralysis)'),
 ({'GASTROACID'}, 'a foe\'s ability is the problem (Gastro Acid)'),
 ({'KNOCKOFF'}, 'a foe leans on its item: Sash, berry, Eviolite (Knock Off)'),
 ({'GRASSYGLIDE', 'EXTREMESPEED', 'SUCKERPUNCH', 'AQUAJET', 'SHADOWSNEAK', 'BULLETPUNCH', 'ICESHARD', 'MACHPUNCH', 'VACUUMWAVE', 'JETPUNCH', 'ACCELEROCK'},
  'a weakened foe must go down before it moves (priority)'),
 ({'SWORDSDANCE', 'DRAGONDANCE', 'NASTYPLOT', 'QUIVERDANCE', 'CALMMIND', 'BULKUP', 'CURSE', 'SHELLSMASH', 'COIL'}, 'the board is safe enough to set up and sweep'),
 ({'RECOVER', 'ROOST', 'SLACKOFF', 'MOONLIGHT', 'SYNTHESIS', 'SOFTBOILED', 'WISH', 'SHOREUP', 'STRENGTHSAP', 'MORNINGSUN'}, 'you need to soak hits and stall (recovery)'),
 ({'UTURN', 'VOLTSWITCH', 'FLIPTURN', 'PARTINGSHOT', 'TELEPORT'}, 'you want to hit and switch to a better matchup (pivot)'),
 ({'EARTHQUAKE', 'ROCKSLIDE', 'SURF', 'HEATWAVE', 'BOOMBURST', 'DISCHARGE', 'HYPERVOICE', 'DAZZLINGGLEAM', 'MUDDYWATER', 'SLUDGEWAVE', 'BLIZZARD', 'ERUPTION', 'WATERSPOUT', 'BULLDOZE', 'ICYWIND', 'SNARL'},
  'you want to hit both foes at once (spread move)'),
]
def cues(types, ability, moves, chart):
    ab = _n(ability); mv = {_n(m) for m in moves}
    # defensive: immunities (incl. absorb abilities), then 4x resists, then resists, in order of how common the attack type is
    m = {t: chart(t, types) for t in ORDER}
    if ab in ABSORB: m[ABSORB[ab]] = 0
    imm = [t for t in ORDER if m[t] == 0]; dbl = [t for t in ORDER if 0 < m[t] <= .25]; res = [t for t in ORDER if .25 < m[t] < 1]
    pick = (imm + dbl + res)[:3]
    out = []
    if pick: out.append('Switch in on ' + ' / '.join(t.title() for t in pick) + ' moves' + (' (immune to ' + ' / '.join(t.title() for t in imm[:2]) + ')' if imm else ''))
    job = next((txt for s, txt in JOB_AB if ab in s), None) or next((txt for s, txt in JOB_MV if mv & s), None)
    if job: out.append('Bring in when ' + job)
    return out
