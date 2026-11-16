"""Aevian kit notes (OP stars 1-3, signature tools + learn level, meta analog, catch). Shared by tier_tabs.py."""
import json, os, re
KIT = {
 'Golisopod': (3, 'Skill Link: Bone Rush (Lv 41) always hits 5× = 125 BP Ground STAB; Pin Missile (Lv 21) 125 BP Bug. Swords Dance Lv 16, Headlong Rush Lv 48',
               'Skill Link Cloyster / Cinccino: multi-hits break Sash, Sturdy, Substitute', '125 Atk / 130 Def, but base 50 Speed'),
 'Veluza': (3, 'Fillet Away (Lv 30): +2 Atk / SpA / Speed for half its HP. Reckless Wave Crash (Lv 45) + Flare Blitz (Lv 40) ×1.2, Extreme Speed Lv 50',
            'Shell Smash / Belly Drum sweepers (Cloyster, Azumarill) with Water + Fire STAB', '60 / 60 defences: needs a free turn, recoil adds up'),
 'Glalie': (2, 'Grassy Surge on entry: Grass moves ×1.3 + heal every turn. Grassy Glide (Move Relearner) = priority in terrain; Wood Hammer Lv 48',
            'Rillaboom (Grassy Surge + Grassy Glide, OU / VGC staple)', 'Weak to Bug, Fighting, Ice, Poison, Steel; base 50 Speed'),
 'Lapras': (2, 'No Guard: Sing (Lv 5) never misses = sleep on demand; Rock Slide (Lv 30) never misses + flinch; Dragon Dance (egg)',
            'Guaranteed sleep like Spore users (Amoonguss, Breloom)', 'Sleep is blocked by Electric / Misty terrain and sleep-immune bosses'),
 'Musharna': (2, 'Tough Claws: Play Rough / Throat Chop ×1.3; Glare (Lv 43 as Munna); Lovely Kiss Lv 41 + Bad Dreams as the sleep build',
              'Bulky Dark/Fairy hitter like Grimmsnarl; Bad Dreams = Darkrai\'s ability', 'Base 29 Speed: moves last'),
 'Drapion': (2, 'Fur Coat: physical damage halved (2× Defence). Merciless option: every hit on a poisoned foe crits (Toxic Spikes Lv 15)',
             'Fur Coat Alolan Persian; Merciless + Toxic combo like Toxapex', 'Ice/Poison: weak to Fire, Ground, Psychic, Steel'),
 'Froslass': (2, 'Adaptability: Grass + Water STAB ×2 (Hydro Pump Lv 41, Giga Drain Lv 48), base 110 Speed',
              'Adaptability Crawdaunt / Porygon-Z damage', 'Same Water/Grass role as your Ludicolo'),
 'Roserade': (1, 'Technician Vacuum Wave (priority, 40→60 BP) + Mud Shot; Aura Sphere (Lv 43 as Roselia), Earth Power (Relearner); 125 SpA',
              'Fast special Fighting/Ground with no direct meta analog', 'Dry Skin needs rain (none on the team): Technician only'),
 'Ampharos': (1, 'Filter (super-effective hits ×0.75) on Ice/Electric; Cotton Guard Lv 46 (+3 Def). Ice Ball (Lv 25) is weak',
              'Bulky special Electric like regular Ampharos', 'Its Aevian Ampharos Crest is not owned'),
 'Gastrodon': (1, 'Ground/Fairy with Storm Drain; Strange Steam (Lv 41), Earth Power (Lv 35), Recover (Lv 54)',
               'Bulky Ground pivot like Clodsire', 'Base 39 Speed, middling power'),
 'Unfezant': (1, 'Rock Head + Head Smash (Pidove Lv 52) with no recoil; Defiant; Tailwind only at Lv 60 (past the cap)',
              'Fast Rock/Fighting like Terrakion, but 115 Atk / 98 Spe', '55 / 55 special bulk'),
 'Palossand': (1, 'Rocky: Storm Drain, Power Gem. Fiery: Steam Engine (Fire/Water hit = +6 Speed), Lava Plume. Icy: Freeze-Dry (Lv 47)',
               'Bulky Ghost wall like regular Palossand', '35 Speed, 100 SpA'),
 'Leavanny': (1, 'Bug/Dragon with Intimidate, Swords Dance (Lv 46), Dragon Rush (Lv 50); Sticky Web as Swadloon (Lv 32)',
              'Physical Bug like Scizor without the bulk', '75 / 75 / 75 bulk'),
 'Mismagius': (1, 'Hexing Slash (learned on evolving): 90 BP Ghost, drains HP, may poison. Magic Bounce reflects status',
               'Mixed Ghost like regular Mismagius', '60 / 60 / 60 bulk: one-shot often'),
 'Parasect': (2, 'Resuscitation: when knocked out it comes back once as Zombie Form (pure Ghost, 130 Atk / 105 Spe). Gunk Shot Lv 56 is past the cap; Cross Poison Lv 41, Phantom Force',
              'Two lives in one slot, like a free Focus Sash plus a revenge-killer', 'Bug/Poison first life: 60 HP, base 30 Speed (effect not in the damage model)'),
}

SHORT = {'darkgardevoir': 'Dark Gardevoir', 'garbodor': 'Garbodor', 'karrina': 'Karrina', 'spector': 'Spector day',
         'spector2': 'Spector night', 'jenner9': 'Jenner', 'amanda': 'Amanda', 'erick': 'Erick'}
def disp(n):
    n = n.replace(' (Aevian Form Male)', '-Aevian').replace(' (Aevian Form)', '-Aevian').replace(' (West Aevian Form)', '-Aevian (West)')
    for a, b in ((' (Hisuian Form)', '-Hisui'), (' (Galarian Form)', '-Galar'), (' (Alolan Form)', '-Alola'), (' (Paldean Form)', '-Paldea')):
        n = n.replace(a, b)
    return re.sub(r' \((\w+) Aevian Form\)', r'-Aevian (\1)', n)


_AB = {}
def abn(a):
    if not _AB: _AB.update(json.load(open('gamedata/abiltext.json')))
    return (_AB.get(a) or {}).get('name', a.title())


