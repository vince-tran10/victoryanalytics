"""Chapter 8 (Classic / hard mode) boss battles pulled from the Rejuvenation wiki."""
import json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from teamcards import parse_cards

# (key, label, page, section filter, field, format, weight, notes)
BATTLES = [
    ('texen', 'Texen (Fighting gym) - Sheridan Village', 'Texen', ("Texen's House", ''), 'Big Top Arena', 'Doubles', 1.0,
     '6v6 double battle, Aelita is your partner. High Striker: physical Fighting & slam moves roll 0.5x-3x; Swords Dance = +3, Dragon Dance = +2/+2, Sing never misses; Make It Rain & Acrobatics 1.5x.'),
    ('groudon', "Cera's Groudon - Garufa Ruins", 'Cera', ('Garufa Ruins', ''), 'Corrupted Cave', 'Singles', 1.0,
     'Boss Groudon (2 shields, Drought sun, Lum Berry). Poison 1.5x, Grass/Rock 1.2x, Fairy 0.5x; grounded non-Poison/Steel mons get poisoned every turn. Lava Plume turns the field Volcanic (50% to everything).'),
    ('crawli', 'Crawli (Head Ranger) - Jynnobi Pass', 'Crawli', ('Jynnobi Pass', ''), 'Swamp Field', 'Doubles', 1.0,
     'Bug/Grass/Water 1.3x, Fire 0.8x, Earthquake/Bulldoze 0.25x; grounded mons lose 1 Speed every turn; Sticky Web lead.'),
    ('eli', 'Eli & Sharon - Valor Cliffside', 'Eli', ('', 'Valor Cliffside'), 'Mountain', 'Doubles', 1.0,
     'Venam is your partner. Rock & Flying 1.5x, Hyper Voice/Icy Wind/Thunder 1.5x (Thunder never misses).'),
    ('giratina', 'Rift Giratina (Taken Tyrant) - Valor Summit', 'Valor_Summit', ('Rift Distortion', ''), 'Wasteland', 'Doubles', 1.0,
     'Hazards are consumed for big effects (Spikes 1/3 HP per layer, double Stealth Rock); Earthquake 0.25x; sludge moves 1.2x and can inflict random status.'),
    ('geara', 'Geara & Zetta - Valor Summit', 'Zetta', ('Valor Mountain', ''), 'Volcanic Top Field', 'Doubles', 1.5,
     '12 mons, Melia is your partner. Fire/Flying/Rock 1.5x (Rock gains Fire), Ice 0.5x, Water 0.9x, Surf/Muddy Water/Hydro Pump/Water Spout 0.5x; Earthquake/Earth Power cause eruptions (1/8 to non-Fire).'),
    ('amber', 'Amber (Lyric Badge gym) - Club STFU', 'Amber', ('Club STFU', ''), 'Concert Venue', 'Singles', 1.0,
     'Sound 1.5x; starts at No Hype (minimum damage rolls). Sound moves, spread moves, crits and dance moves raise Hype; at Hyped nothing can sleep.'),
]

# field multipliers: by attacking type and by move id
FIELD = {
    'Big Top Arena': {'types': {}, 'moves': {'MAKEITRAIN': 1.5, 'PAYDAY': 1.5, 'ACROBATICS': 1.5 * 2, 'AQUASTEP': 1.5,
                                            'FIERYDANCE': 1.5, 'FIRELASH': 1.5, 'FIRSTIMPRESSION': 1.5, 'FLOWERTRICK': 1.5,
                                            'FLY': 1.5, 'PETALDANCE': 1.5, 'POWERWHIP': 1.5, 'REVELATIONDANCE': 1.5,
                                            'VINEWHIP': 1.5, 'DRUMBEATING': 1.5},
                      'sound': 1.5, 'striker': True},
    'Corrupted Cave': {'types': {'POISON': 1.5, 'GRASS': 1.2, 'ROCK': 1.2, 'FAIRY': 0.5}, 'moves': {'APPLEACID': 1.5, 'SEEDFLARE': 1.5},
                       'noncontact_flying': 0.5, 'sun': True},
    'Swamp Field': {'types': {'BUG': 1.3, 'GRASS': 1.3, 'WATER': 1.3, 'FIRE': 0.8},
                    'moves': {'EARTHQUAKE': 0.25, 'BULLDOZE': 0.25, 'MAGNITUDE': 0.25, 'SMACKDOWN': 1.5, 'THOUSANDARROWS': 1.5,
                              'BRINE': 1.5, 'GUNKSHOT': 1.5, 'MUDBOMB': 1.5, 'MUDSHOT': 1.5, 'MUDSLAP': 1.5, 'MUDDYWATER': 1.5,
                              'SLUDGEWAVE': 1.5, 'EXPLOSION': 0, 'SELFDESTRUCT': 0, 'MINDBLOWN': 0}},
    'Mountain': {'types': {'ROCK': 1.5, 'FLYING': 1.5},
                 'moves': {'AVALANCHE': 1.5, 'ERUPTION': 1.5, 'THUNDER': 1.5, 'CIRCLETHROW': 1.5, 'STORMTHROW': 1.5,
                           'VITALTHROW': 1.5, 'FAIRYWIND': 1.5, 'ICYWIND': 1.5, 'OMINOUSWIND': 1.5, 'RAZORWIND': 1.5,
                           'SILVERWIND': 1.5, 'TWISTER': 1.5, 'HYPERVOICE': 1.5}},
    'Wasteland': {'types': {}, 'moves': {'POWERWHIP': 1.5, 'VINEWHIP': 1.5, 'MUDBOMB': 1.5, 'MUDSHOT': 1.5, 'MUDSLAP': 1.5,
                                         'GUNKSHOT': 1.2, 'OCTAZOOKA': 1.2, 'SLUDGE': 1.2, 'SLUDGEBOMB': 1.2, 'SLUDGEWAVE': 1.2,
                                         'EARTHQUAKE': 0.25, 'BULLDOZE': 0.25, 'MAGNITUDE': 0.25, 'VENOSHOCK': 2.0,
                                         'BARBBARRAGE': 2.0, 'SPITUP': 2.0}},
    'Volcanic Top Field': {'types': {'FIRE': 1.5, 'FLYING': 1.5, 'ROCK': 1.5, 'WATER': 0.9, 'ICE': 0.5},
                           'moves': {'THUNDER': 1.5, 'SCALD': 1.5 / 0.9, 'HYDROSTEAM': 1.5 / 0.9, 'STEAMERUPTION': 1.5 / 0.9,
                                     'ICYWIND': 1.5 / 0.5, 'PRECIPICEBLADES': 1.5, 'ERUPTION': 1.2, 'HEATWAVE': 1.2,
                                     'LAVAPLUME': 1.2, 'MAGMADRIFT': 1.2, 'HYDROPUMP': 0.5, 'MUDDYWATER': 0.5, 'SURF': 0.5,
                                     'WATERSPOUT': 0.5, 'WATERPLEDGE': 0.5, 'SPARKLINGARIA': 0.5}},
    'Concert Venue': {'types': {}, 'moves': {'ACID': 1.5, 'ACIDSPRAY': 1.5, 'CIRCLETHROW': 1.5, 'DRAGONTAIL': 1.5,
                                             'DRUMBEATING': 1.5, 'FAKEOUT': 1.5, 'FIRSTIMPRESSION': 1.5, 'OUTRAGE': 1.5,
                                             'THRASH': 1.5, 'STOMPINGTANTRUM': 1.5},
                      'sound': 1.5},
}
HIGH_STRIKER = set('''BEHEMOTHBASH BLAZEKICK BODYSLAM BOUNCE BRUTALSWING BULLDOZE CRABHAMMER DOUBLEIRONBASH DRAGONHAMMER
DRAGONRUSH DUALCHOP EARTHQUAKE GIGAIMPACT GIGATONHAMMER GLAIVERUSH GRAVAPPLE HARDPRESS HEADLONGRUSH HEATCRASH HEAVYSLAM
HIGHHORSEPOWER ICEHAMMER ICICLECRASH IRONTAIL IVYCUDGEL MAGNITUDE METEORMASH MIGHTYCLEAVE POUND SKYDROP SLAM SMACKDOWN
STOMP STOMPINGTANTRUM STRENGTH SUPERCELLSLAM TEMPERFLARE WOODHAMMER'''.split())


def load_battles(base):
    out = []
    for key, label, page, (sec, sub), field, fmt, weight, notes in BATTLES:
        w = json.load(open(f'{base}/raw/story/{page}.json'))['parse']['wikitext']
        cards = parse_cards(w)
        classic = [c for c in cards if c['mode'] == 'Classic Mode']
        pool = classic if classic else [c for c in cards if c['mode'] == 'All']
        sel = [c for c in pool if (not sec or c['section'] == sec) and (not sub or c['sub'] == sub)]
        mons, seen = [], set()
        for c in sel:
            for m in c['mons']:
                k = (m.get('specie'), m.get('level'), m.get('move1'))
                if k in seen:
                    continue
                seen.add(k); mons.append(m)
        if key == 'giratina':
            # page lists alternative Giratina forms in a tabber; keep Relicanth, one Giratina of each typing, Swalot
            keep, gseen = [], set()
            for m in mons:
                if m['specie'] == 'Giratina':
                    if m['types'] in gseen:
                        continue
                    gseen.add(m['types'])
                if m['specie'] in ('Relicanth', 'Giratina', 'Swalot'):
                    keep.append(m)
            mons = keep
        out.append(dict(key=key, label=label, field=field, format=fmt, weight=weight, notes=notes, mons=mons))
    return out


if __name__ == '__main__':
    for b in load_battles(sys.argv[1]):
        print(b['key'], b['field'], len(b['mons']), [m['specie'] for m in b['mons']])


# ---------------------------------------------------------------- BIGJRA walkthrough (Classic Mode) version
FIELD.update({
    'Deep Earth Field': {'types': {'ROCK': 1.3, 'PSYCHIC': 1.3}, 'moves': {}, 'ground_vs_nonground': 1.5, 'gravity': True,
                         'priority': 0.7},
    'Beach Field': {'types': {}, 'moves': {'MUDBOMB': 2, 'MUDSHOT': 2, 'MUDSLAP': 2, 'SANDTOMB': 2, 'BRINE': 1.5,
                                           'CRABHAMMER': 1.5, 'MUDDYWATER': 1.5, 'RAZORSHELL': 1.5, 'SURF': 1.5,
                                           'SCORCHINGSANDS': 1.5, 'WAVECRASH': 1.5, 'FOCUSBLAST': 1.3, 'AURASPHERE': 1.3,
                                           'ZENHEADBUTT': 1.3, 'PSYCHIC': 1.2}},
    'Volcanic Top': None,
    # approximations for the late-chapter fields (main type boosts only)
    'Haunted Field': {'types': {'GHOST': 1.5}, 'moves': {}},
    'Water Surface': {'types': {'WATER': 1.5, 'ELECTRIC': 1.5}, 'moves': {}},
    'Short-Circuit Field': {'types': {'ELECTRIC': 1.5}, 'moves': {}},
    'Factory Field': {'types': {'ELECTRIC': 1.2}, 'moves': {}},
    'Forest Field': {'types': {'GRASS': 1.5, 'BUG': 1.5}, 'moves': {}},
})
FIELD['Volcanic Top'] = FIELD['Volcanic Top Field']
FIELD['Mountain Field'] = FIELD['Mountain']

# (match in trainer header, key, label, field, format, weight, notes)
WALK = [
    ('VS: Student Aelita', 'aelita', 'Aelita – Kristiline Town', 'Beach Field', 'Singles', 0.8,
     'Fighting/Flying team: Unfezant-Aevian (Sturdy, Stealth Rock), Pawmot (Fake Out, Iron Fist punches), Lucario (Sash, Calm Mind), Hawlucha (Unburden + Flying Gem Acrobatics), Blaziken (Speed Boost), Staraptor (Reckless). Beach: Aura Sphere/Focus Blast 1.3x, Water/mud moves boosted.'),
    ('Pseudo Sensei Texen', 'texen', 'Texen (Fighting gym) – Sheridan', 'Big Top Arena', 'Doubles', 1.0,
     'Multi battle: you bring 3, Aelita brings Staraptor/Blaziken/Hawlucha. High Striker physical Fighting & slam moves roll 0.5x–3x; Swords Dance +3, Dragon Dance +2/+2, Sing never misses; Make It Rain & Acrobatics 1.5x.'),
    ('Ancient Guard Escavalier', 'guard1', 'Ancient Guard #1 (Gravity/Trick Room) – Garufa Sanctuary (Adam path)', 'Deep Earth Field', 'Singles', 0.5,
     'Only if you brought Adam. Gravity + Trick Room team. Deep Earth: Ground 1.5x vs non-Ground, Rock & Psychic 1.3x, Gravity always on (Levitate/Flying get hit by Ground), priority moves 0.7x.'),
    ('Ancient Guard Escavalier#2', 'guard2', 'Ancient Guard #2 (Rock team) – Garufa Sanctuary (Adam path)', 'Deep Earth Field', 'Singles', 0.5,
     'Only if you brought Adam. Tyranitar/Gigalith sand; Matrix Shot on most of them.'),
    ('Team Xen Tommen', 'tommen', 'Tommen – Garufa Sanctuary', 'Deep Earth Field', 'Singles', 0.6,
     'Bronzong, Coalossal, Salazzle (Corrosion), Perrserker.'),
    ('Behemoth Groudon', 'groudon', 'Behemoth Groudon (boss) – Garufa Sanctuary', 'Deep Earth Field', 'Singles', 1.0,
     'Boss, 1 shield, Drought sun. Its Earthquake gets Deep Earth\'s 1.5x vs non-Ground; Ground types resist Ground here. Water is halved in sun.'),
    ('Head Ranger Crawli', 'crawli', 'Crawli (Head Ranger) – Jynnobi Pass', 'Swamp Field', 'Doubles', 1.0,
     'Bug/Grass/Water 1.3x, Fire 0.8x, Earthquake/Bulldoze 0.25x; grounded mons lose 1 Speed every turn; Sticky Web lead.'),
    ('Xen Executive Neved', 'neved', 'Neved (optional) – Valor Shore', 'Beach Field', 'Singles', 0.5,
     'Only if you choose "We win and save Nim". Beach: Surf/Muddy Water/Razor Shell/Crabhammer 1.5x, mud moves 2x, Aura Sphere/Focus Blast/Zen Headbutt 1.3x.'),
    ('Misfortunate Duo', 'eli', 'Eli & Sharon (10 mons) – Valor Cliffside', 'Mountain Field', 'Doubles', 1.2,
     'Venam is your partner. Rock & Flying 1.5x, Hyper Voice/Icy Wind/Thunder 1.5x (Thunder never misses).'),
    ('Professor Jenner', 'jenner', 'Jenner – Valor Summit', 'Volcanic Top', 'Singles', 0.6,
     '6v4. Volcanic Top: Fire/Flying/Rock 1.5x, Ice 0.5x, Surf/Muddy Water 0.5x.'),
    ('Xen Executive Geara', 'geara', 'Geara & Zetta (12 mons) – Valor Summit', 'Volcanic Top Field', 'Doubles', 1.5,
     'Melia is your partner. Fire/Flying/Rock 1.5x (Rock gains Fire), Ice 0.5x, Water 0.9x, Surf/Muddy Water/Hydro Pump/Water Spout 0.5x; Earthquake/Earth Power cause eruptions (1/8 to non-Fire).'),
    ('Taken Tyrant', 'giratina', 'Rift Giratina (boss) – Rift Distortion', 'Wasteland', 'Doubles', 1.0,
     'Boss Rift Giratina (Ghost/Poison) + crested Relicanth + crested Swalot. Hazards are consumed (Spikes 1/3 HP per layer); Earthquake 0.25x; sludge moves 1.2x.'),
    ('Guardian Spectre Narcissa#1', 'narcissa1', 'Narcissa 1/3 – Haunted Field', 'Haunted Field', 'Singles', 0.4,
     'Gauntlet part 1: Golurk (Iron Fist), Sableye (Will-O-Wisp, Recover).'),
    ('Guardian Spectre Narcissa#2', 'narcissa2', 'Narcissa 2/3 – Haunted Field', 'Haunted Field', 'Singles', 0.5,
     'Gauntlet part 2: Banette (Quick Claw, Shadow Sneak), Decidueye (Baton Pass), Oricorio-Sensu (Calm Mind).'),
    ('Guardian Spectre Narcissa#3', 'narcissa', 'Narcissa 3/3 – Haunted Field', 'Haunted Field', 'Singles', 0.6,
     'Gauntlet part 3: Swoobat (Unaware, Calm Mind), Haunter (Perish Song + Mean Look), Mismagius (Nasty Plot), Shedinja (Wonder Guard + Focus Sash).'),
    ('Team Xen Danni', 'danni', 'Danni & Layla (7 mons) – Beach', 'Beach Field', 'Doubles', 0.6, 'Bug-heavy doubles.'),
    ('Team Xen Troye', 'troye', 'Troye & Helen – Beach', 'Beach Field', 'Doubles', 0.8, 'Gigalith sand, Scizor, Ambipom, Bibarel, Decidueye (Lv 57–59).'),
    ('Xen Analyst Zena', 'zena', 'Zena – Short-Circuit Field', 'Short-Circuit Field', 'Singles', 0.5, 'Skuntank, Seismitoad, Cursola, Shadow Purugly.'),
    ('Leviathan Kyogre', 'kyogre', 'Leviathan Kyogre (boss) – Water Surface', 'Water Surface', 'Singles', 1.0, 'Boss Kyogre Lv 60 with Drizzle rain.'),
    ('Commander Holly', 'holly', 'Holly & Rorim – Beach', 'Beach Field', 'Doubles', 1.0, 'Scizor, Escavalier, Speed Boost Scolipede, Oricorio, Bellossom, Quaquaval (Lv 55–58).'),
    ('Manaphy', 'manaphy', 'Manaphy (boss) – Beach', 'Beach Field', 'Singles', 0.8, 'Boss Manaphy Lv 60 calling Phione.'),
    ('VS: ??? ???', 'factory', '??? – Factory Field', 'Factory Field', 'Singles', 1.2, 'Raichu, Clawitzer, Orthworm, Rotom, Swampert, Xurkitree (Lv 60–64).'),
    ('Team Anti-Assist Marcie', 'marcie', 'Marcie & Chikie – Forest', 'Forest Field', 'Doubles', 0.5, 'Rillaboom, Tsareena, Porygon2, Eelektross.'),
    ('Music Enthusiast Amber', 'amber', 'Amber (Lyric Badge gym) – Club STFU', 'Concert Venue', 'Singles', 1.0,
     'Sound 1.5x; starts at No Hype (minimum rolls). All-Fire team.'),
]


def _evs(s):
    s = (s or '').replace('EVs:', '').strip()
    order = ['HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe']
    m = re.match(r'All (\d+)', s)
    if m:
        return ';'.join([m.group(1)] * 6)
    d = dict((k, int(v)) for v, k in re.findall(r'(\d+) (HP|Atk|Def|SpA|SpD|Spe)', s))
    return ';'.join(str(d.get(k, 0)) for k in order) if d else ''


def load_battles_walk(base):
    ev = json.load(open(f'{base}/team/walk_ch8.json'))
    trainers = [e for e in ev if e['type'] == 'trainer']
    out = []
    used = set()
    for match, key, label, field, fmt, weight, notes in WALK:
        nth = int(match.rsplit('#', 1)[1]) if re.search(r'#\d+$', match) else 0
        want_second = nth == 2
        mt = re.sub(r'#\d+$', '', match)
        hits = [i for i, t in enumerate(trainers) if mt in t['trainer'] and 'Partner' not in t['trainer']]
        if not hits:
            continue
        idx = hits[nth - 1] if nth and len(hits) >= nth else hits[0]
        # if the same trainer appears twice in the chapter (e.g. two difficulty sets), keep the bigger / higher one
        if not nth and len(hits) > 1 and key not in ('guard1',):
            idx = max(hits, key=lambda i: (len(trainers[i]['mons']), max(m['level'] or 0 for m in trainers[i]['mons'])))
        t = trainers[idx]
        mons = []
        for m in t['mons']:
            name = re.sub(r'^(Boss|Shadow|SOS)\s+', '', m['name']).strip()
            shields = re.search(r'Shields:\s*(\d+)', m['form'] or '')
            base_override = None
            if m['base']:
                vals = [int(x) for x in re.findall(r'(\d+) (?:HP|Atk|Def|SpA|SpD|Spe)', m['base'])]
                if len(vals) == 6:
                    base_override = vals
            mons.append({'specie': name, 'level': m['level'], 'types': (m['typing'] or '').lower(),
                         'ability': (m['ability'] or '').split('/')[0], 'nature': m['nature'], 'heldItem': m['item'],
                         'evs': _evs(m['evs']), 'boss': m['name'].startswith('Boss'),
                         'shields': shields.group(1) if shields else '', 'form_text': m['form'],
                         'base_override': base_override,
                         **{f'move{i + 1}': f'{mv};;' for i, mv in enumerate(m['moves'][:4])}})
        src = 'walkthrough'
        if _GD is not None and key in _GD.FIGHTS and os.environ.get('GAMEDATA', '1') == '1':
            mons, src = _GD.walk_mons(key), 'game'   # exact Classic data from the game's own files
        out.append(dict(key=key, label=label, field=field, format=fmt, weight=weight, notes=notes, mons=mons,
                        trainer=t['trainer'], source=src))
    return out


# ---------------------------------------------------------------- game data (exact) overrides, when available
try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gamedata'))
    import gamedata as _GD, fields as _GF
    if not _GD.available():
        _GD = None
except Exception:
    _GD = None
if _GD is not None and os.environ.get('GAMEDATA', '1') == '1':
    for _ours, _gk in _GF.MAP.items():
        _g = _GF.game_field(_gk)
        _keep = {k: v for k, v in (FIELD.get(_ours) or {}).items() if k not in ('types', 'moves', 'sound')}
        _types = dict(_g['types']); _sound = _types.pop('soundmove', None)
        FIELD[_ours] = dict(_keep, types=_types, moves=_g['moves'], add=_g['add'],
                            mtype2={mv: t for t, mvs in _g['typeMods'].items() for mv in mvs}, game=_gk,
                            **({'sound': _sound} if _sound else {}))

    # Concert Venue starts at hype level 1: every damage roll is the minimum, 85% (game: Battle_Move.rb, random = 85 if CONCERT1)
    if 'Concert Venue' in FIELD:
        FIELD['Concert Venue']['roll'] = 0.85
