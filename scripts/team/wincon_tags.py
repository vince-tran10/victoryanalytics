"""Win-condition role tags (Vincent, 23 Nov): every Pokemon in his box is tagged by the job it does in a win condition.
  A Win con      ends the fight: setup sweeper, late-game speed cleaner, priority cleaner; doubles: also a strong spread attacker / weather abuser
  B Enabler      creates A's condition: Tailwind / Trick Room / screens / redirection / Encore / sleep / paralysis / weather or terrain setter
                 (singles: hazards too; doubles: Icy Wind / Electroweb / Helping Hand)
  C Wallbreaker  punches holes: very strong attack stat or a power ability, Knock Off
  D Pivot / glue bulky and brings A or C in safely: Regenerator, pivot moves, Intimidate, Will-O-Wisp, recovery; doubles: Fake Out, Snarl
  E Field / tech Unaware, Wide Guard, Perish Song, Haze / Clear Smog / phazing, Taunt, Leech Seed, Gastro Acid, Endeavor, field-changing moves
Tags come from what the BUILD runs (party moves, else the ideal build) plus base stats and ability. Singles and doubles are tagged separately;
they are usually the same."""
NAMES = {'A': 'Win con', 'B': 'Enabler', 'C': 'Wallbreaker', 'D': 'Pivot / glue', 'E': 'Field / tech'}
SETUP = {'SWORDSDANCE': 'Swords Dance', 'DRAGONDANCE': 'Dragon Dance', 'NASTYPLOT': 'Nasty Plot', 'CALMMIND': 'Calm Mind', 'QUIVERDANCE': 'Quiver Dance',
         'SHELLSMASH': 'Shell Smash', 'BULKUP': 'Bulk Up', 'CURSE': 'Curse', 'SHIFTGEAR': 'Shift Gear', 'COIL': 'Coil', 'BELLYDRUM': 'Belly Drum',
         'FILLETAWAY': 'Fillet Away', 'TIDYUP': 'Tidy Up', 'VICTORYDANCE': 'Victory Dance', 'TAILGLOW': 'Tail Glow', 'GEOMANCY': 'Geomancy',
         'AGILITY': 'Agility', 'ROCKPOLISH': 'Rock Polish', 'GROWTH': 'Growth', 'WORKUP': 'Work Up', 'IRONDEFENSE': 'Iron Defense',
         'ACIDARMOR': 'Acid Armor', 'COSMICPOWER': 'Cosmic Power', 'CLANGOROUSSOUL': 'Clangorous Soul', 'NORETREAT': 'No Retreat'}
SPEEDAB = {'MOXIE': 'Moxie', 'SPEEDBOOST': 'Speed Boost', 'BEASTBOOST': 'Beast Boost', 'CHILLINGNEIGH': 'Chilling Neigh', 'GRIMNEIGH': 'Grim Neigh',
           'ASONE': 'As One', 'SOULHEART': 'Soul-Heart', 'UNBURDEN': 'Unburden'}
WEATHERAB = {'SWIFTSWIM': 'rain', 'CHLOROPHYLL': 'sun', 'SANDRUSH': 'sand', 'SLUSHRUSH': 'snow', 'SURGESURFER': 'Electric Terrain', 'SOLARPOWER': 'sun',
             'SANDFORCE': 'sand', 'PROTOSYNTHESIS': 'sun', 'QUARKDRIVE': 'Electric Terrain'}
PRIO = {'EXTREMESPEED', 'SUCKERPUNCH', 'AQUAJET', 'BULLETPUNCH', 'SHADOWSNEAK', 'ICESHARD', 'MACHPUNCH', 'VACUUMWAVE', 'QUICKATTACK',
        'ACCELEROCK', 'JETPUNCH', 'GRASSYGLIDE', 'FIRSTIMPRESSION', 'THUNDERCLAP', 'WATERSHURIKEN'}
ENABLE = {'TAILWIND': 'Tailwind', 'TRICKROOM': 'Trick Room', 'REFLECT': 'Reflect', 'LIGHTSCREEN': 'Light Screen', 'AURORAVEIL': 'Aurora Veil',
          'FOLLOWME': 'Follow Me', 'RAGEPOWDER': 'Rage Powder', 'ENCORE': 'Encore', 'YAWN': 'Yawn', 'SPORE': 'Spore', 'SLEEPPOWDER': 'Sleep Powder',
          'LOVELYKISS': 'Lovely Kiss', 'SING': 'Sing', 'HYPNOSIS': 'Hypnosis', 'DARKVOID': 'Dark Void', 'GRASSWHISTLE': 'Grass Whistle',
          'THUNDERWAVE': 'Thunder Wave', 'GLARE': 'Glare', 'NUZZLE': 'Nuzzle', 'STUNSPORE': 'Stun Spore', 'BATONPASS': 'Baton Pass',
          'MEMENTO': 'Memento', 'SHEDTAIL': 'Shed Tail', 'DECORATE': 'Decorate', 'COACHING': 'Coaching'}
ENABLE_S = {'STEALTHROCK': 'Stealth Rock', 'SPIKES': 'Spikes', 'TOXICSPIKES': 'Toxic Spikes', 'STICKYWEB': 'Sticky Web'}
ENABLE_D = {'ICYWIND': 'Icy Wind', 'ELECTROWEB': 'Electroweb', 'HELPINGHAND': 'Helping Hand', 'BULLDOZE': 'Bulldoze', 'AFTERYOU': 'After You',
            'INSTRUCT': 'Instruct'}
SETTER = {'DROUGHT': 'Drought', 'DRIZZLE': 'Drizzle', 'SANDSTREAM': 'Sand Stream', 'SNOWWARNING': 'Snow Warning', 'GRASSYSURGE': 'Grassy Surge',
          'ELECTRICSURGE': 'Electric Surge', 'PSYCHICSURGE': 'Psychic Surge', 'MISTYSURGE': 'Misty Surge', 'ORICHALCUMPULSE': 'Orichalcum Pulse',
          'HADRONENGINE': 'Hadron Engine'}
POWERAB = {'HUGEPOWER': 'Huge Power', 'PUREPOWER': 'Pure Power', 'ADAPTABILITY': 'Adaptability', 'SHEERFORCE': 'Sheer Force', 'TOUGHCLAWS': 'Tough Claws',
           'PUNKROCK': 'Punk Rock', 'SKILLLINK': 'Skill Link', 'TECHNICIAN': 'Technician', 'GORILLATACTICS': 'Gorilla Tactics', 'STRONGJAW': 'Strong Jaw',
           'IRONFIST': 'Iron Fist', 'MEGALAUNCHER': 'Mega Launcher', 'SHARPNESS': 'Sharpness', 'RECKLESS': 'Reckless', 'WATERBUBBLE': 'Water Bubble',
           'TRANSISTOR': 'Transistor', 'DRAGONSMAW': "Dragon's Maw", 'STEELWORKER': 'Steelworker', 'ROCKYPAYLOAD': 'Rocky Payload',
           'AERILATE': 'Aerilate', 'PIXILATE': 'Pixilate', 'REFRIGERATE': 'Refrigerate', 'GALVANIZE': 'Galvanize', 'PARENTALBOND': 'Parental Bond',
           'GUTS': 'Guts', 'TINTEDLENS': 'Tinted Lens', 'SNIPER': 'Sniper', 'SUPREMEOVERLORD': 'Supreme Overlord'}
PIVOTM = {'UTURN': 'U-turn', 'VOLTSWITCH': 'Volt Switch', 'FLIPTURN': 'Flip Turn', 'PARTINGSHOT': 'Parting Shot', 'TELEPORT': 'Teleport',
          'CHILLYRECEPTION': 'Chilly Reception', 'BATONPASS': 'Baton Pass'}
GLUE = {'WILLOWISP': 'Will-O-Wisp', 'RECOVER': 'Recover', 'ROOST': 'Roost', 'SLACKOFF': 'Slack Off', 'SOFTBOILED': 'Soft-Boiled', 'MOONLIGHT': 'Moonlight',
        'SYNTHESIS': 'Synthesis', 'MORNINGSUN': 'Morning Sun', 'WISH': 'Wish', 'SHOREUP': 'Shore Up', 'STRENGTHSAP': 'Strength Sap', 'MILKDRINK': 'Milk Drink',
        'TOXIC': 'Toxic'}
GLUE_D = {'FAKEOUT': 'Fake Out', 'SNARL': 'Snarl', 'WIDEGUARD': 'Wide Guard'}
TECH = {'HAZE': 'Haze', 'CLEARSMOG': 'Clear Smog', 'ROAR': 'Roar', 'WHIRLWIND': 'Whirlwind', 'DRAGONTAIL': 'Dragon Tail', 'CIRCLETHROW': 'Circle Throw',
        'PERISHSONG': 'Perish Song', 'TAUNT': 'Taunt', 'IMPRISON': 'Imprison', 'LEECHSEED': 'Leech Seed', 'GASTROACID': 'Gastro Acid', 'ENDEAVOR': 'Endeavor',
        'WIDEGUARD': 'Wide Guard', 'QUICKGUARD': 'Quick Guard', 'DEFOG': 'Defog', 'RAPIDSPIN': 'Rapid Spin', 'MORTALSPIN': 'Mortal Spin',
        'GRASSYTERRAIN': 'Grassy Terrain', 'ELECTRICTERRAIN': 'Electric Terrain', 'PSYCHICTERRAIN': 'Psychic Terrain', 'MISTYTERRAIN': 'Misty Terrain',
        'RAINDANCE': 'Rain Dance', 'SUNNYDAY': 'Sunny Day', 'SANDSTORM': 'Sandstorm', 'SNOWSCAPE': 'Snowscape', 'HAIL': 'Hail', 'FLASH': 'Flash',
        'HEALBLOCK': 'Heal Block', 'KNOCKOFF': 'Knock Off', 'TRICK': 'Trick', 'SAFEGUARD': 'Safeguard', 'SKILLSWAP': 'Skill Swap', 'ENTRAINMENT': 'Entrainment',
        'WORRYSEED': 'Worry Seed', 'SIMPLEBEAM': 'Simple Beam', 'TOPSYTURVY': 'Topsy-Turvy', 'SPECTRALTHIEF': 'Spectral Thief'}
TECHAB = {'UNAWARE': 'Unaware', 'STURDY': 'Sturdy', 'MAGICBOUNCE': 'Magic Bounce', 'MAGICGUARD': 'Magic Guard', 'SOUNDPROOF': 'Soundproof',
          'GOODASGOLD': 'Good as Gold', 'NEUTRALIZINGGAS': 'Neutralizing Gas', 'MOLDBREAKER': 'Mold Breaker', 'CLOUDNINE': 'Cloud Nine',
          'AIRLOCK': 'Air Lock', 'PRANKSTER': 'Prankster'}


def tag(base, moves, ability, mv, crest=''):
    """base: base stats dict; moves: move ids the build runs; ability: id; mv: movetext (id -> {type, category, basedamage, target})
    -> {'s': [[letter, why], ...], 'd': [[letter, why], ...]}"""
    ms = set(moves); ab = (ability or '').upper().replace(' ', '')
    atk = [m for m in moves if int((mv.get(m) or {}).get('basedamage') or 0) > 0]
    cats = [(mv.get(m) or {}).get('category') for m in atk]
    phys = cats.count('physical') >= cats.count('special')
    off = base['Atk'] if phys else base['SpA']
    bulk = base['HP'] + base['Def'] + base['SpD']
    out = {}
    for fmt in ('s', 'd'):
        t = {}
        def add(k, why):
            if k not in t: t[k] = why
        # A: win con
        su = [SETUP[m] for m in moves if m in SETUP]
        if su and atk: add('A', f'{su[0]} sweeper')
        if ab in SPEEDAB and atk: add('A', f'{SPEEDAB[ab]} cleaner')
        if base['Spe'] >= 100 and off >= 100 and len(atk) >= 2: add('A', f'Fast cleaner (Speed {base["Spe"]})')
        pr = [m for m in atk if m in PRIO]
        if pr and off >= 90: add('A', f'Priority cleaner ({mv[pr[0]]["name"]})')
        if fmt == 'd':
            if ab in WEATHERAB and atk: add('A', f'{WEATHERAB[ab].title() if WEATHERAB[ab].islower() else WEATHERAB[ab]} abuser')
            sp = [m for m in atk if (mv.get(m) or {}).get('target') in ('AllOpposing', 'AllNonUsers') and int(mv[m].get('basedamage') or 0) >= 80]
            if sp and off >= 110: add('A', f'Spread attacker ({mv[sp[0]]["name"]})')
        # B: enabler
        en = [ENABLE[m] for m in moves if m in ENABLE] + ([ENABLE_S[m] for m in moves if m in ENABLE_S] if fmt == 's' else []) \
            + ([ENABLE_D[m] for m in moves if m in ENABLE_D] if fmt == 'd' else [])
        if ab in SETTER: en.insert(0, f'{SETTER[ab]} setter')
        if en: add('B', ' / '.join(en[:2]))
        # C: wallbreaker
        if atk and (off >= 120 or ab in POWERAB):
            add('C', POWERAB[ab] if ab in POWERAB else f'{"Attack" if phys else "Sp. Atk"} {off}')
        # D: pivot / glue
        gl = ([f'Regenerator'] if ab == 'REGENERATOR' else []) + (['Intimidate'] if ab == 'INTIMIDATE' else []) \
            + [PIVOTM[m] for m in moves if m in PIVOTM] + [GLUE[m] for m in moves if m in GLUE] + ([GLUE_D[m] for m in moves if m in GLUE_D] if fmt == 'd' else [])
        if gl and (bulk >= 270 or ab == 'INTIMIDATE' or any(m in PIVOTM for m in moves) or (fmt == 'd' and 'FAKEOUT' in ms)): add('D', ' / '.join(gl[:2]))
        # E: field / tech
        te = ([TECHAB[ab]] if ab in TECHAB else []) + [TECH[m] for m in moves if m in TECH]
        if te: add('E', ' / '.join(te[:2]))
        out[fmt] = [[k, t[k]] for k in 'ABCDE' if k in t]
    return out
