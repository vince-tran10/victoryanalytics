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
