"""Community ratings for Rejuvenation-only kits (Vincent, 22 Nov): Aevians and crests have no Smogon / VGC data, so their
'meta' part of the tier score comes from what players say about the kit and its best use. Sources (fetched 22 Nov):
  F1 Reborn Evolved forum 'Best Aevian Pokemon' (Nov 2023, v13.5)
  F2 'Aevian pokemon & Strategy' (Jul 2023, v13.5)
  F3 'Listing of Pokemon I found especially strong for end game' (Dec 2023 - Jan 2024)
  F4 'Crests and what an opinionated man opines about them' (Aug 2021, v13)
  F5 'Using crest pokemon as god intended' (Nov 2023 - Feb 2024)
  W  rejuvenation.wiki.gg/wiki/Crests (effects + the chapter each crest is obtained)
rating 0-1 replaces the Smogon meta dominance (same scale: .95 = top meta, .7 = strong, .5 = fine, .3 = weak).
'kit' = not discussed by the community: my rating from the kit vs real-meta analogs (said so on the page)."""
FORUM = {   # 22 Nov baseline (older forum posts, v13.5); the live AEVIAN ratings below blend in Vincent's 23 Nov Reddit inputs
 'Golisopod': (.95, 'community', ['F1: "Best Bug type ever made"', 'F1: "tank like a champ and hit like a truck"', 'F3: "Especially strong against shielded foes"']),
 'Veluza':    (.78, 'kit', ['Not discussed by the community', 'Kit: Reckless Wave Crash + Flare Blitz (x1.2)', 'Kit: Head Smash covers Water and Dragon', 'Kit: frail (60 / 60 defences)', 'Fillet Away left out: it halves HP on that frame']),
 'Glalie':    (.74, 'community', ['F1: "Do not sleep on Grassy Glide Grassy Terrain Glalie"', 'F1: Rock Head Head Smash under Trick Room "smashes"']),
 'Musharna':  (.50, 'community', ['F2: "Much better Dark/Fairy typing"', 'F2: "nonexistent speed: mostly a Trick Room Pokemon. It is alright"']),
 'Lapras':    (.70, 'community', ['F2: "utilise No Guard to use very powerful moves like Sing, Zap Cannon, Blizzard"', 'F1: "can utilize No Guard really well"', 'F2: "stat spread is still garbage"']),
 'Drapion':   (.60, 'kit', ['Not discussed by the community', 'Kit: Fur Coat halves physical damage', 'Kit: Merciless crits on poisoned foes']),
 'Froslass':  (.74, 'community', ['F1: "basically carried me" with Muddy Water', 'F3: Adaptability Muddy Water / Water Spout "can do her job even in late game"', 'Water Spout is not legal yet: Hydro Pump instead']),
 'Gastrodon': (.40, 'community', ['F1: the form posters are "more conflicted" about']),
 'Toxtricity':(.66, 'community', ['F1: "Galvanize boosted Boombursts are ridiculous"', 'F2: "a special attacker. That is kinda it"', 'Build: Punk Rock Boomburst (x1.3) scored higher than Galvanize']),
 'Palossand': (.30, 'community', ['F2: "would not even bother with them"', 'F1: "there are better choices"']),
 'Ampharos':  (.50, 'community', ['F1: "Trick Room god" with its Crest (not owned)', 'F2: "kinda bad normally"']),
 'Roserade':  (.75, 'community', ['F1: "ridiculously strong priority Vacuum Wave"', 'F2: "pretty strong overall"']),
 'Leavanny':  (.60, 'community', ['F3: "the fastest Sticky Web setter and it has Intimidate"', 'F3: "can deal decent damage"']),
 'Mismagius': (.74, 'community', ['F1: "a very very good sweeper with 3 fantastic abilities"', 'F2: "pretty fast and hits pretty hard"']),
 'Unfezant':  (.45, 'kit', ['Not discussed by the community', 'Kit: Rock Head Head Smash', 'Kit: Tailwind only past the level cap']),
 'Parasect':  (.65, 'community', ['F1: "essentially 2 lives"', 'F1: second life "130 base attack with 105 base speed"', 'F2: "a glass cannon"']),
 'Paras':     (.30, 'kit', ['Cannot evolve yet (Xen Waste = Chapter 12)']),
 'Gyarados':  (.85, 'community', ['F1/F3: Multiscale + Fiery Dance "wrecks so hard"']),
 'Bronzong':  (.70, 'community', ['F3: "invaluable for setting up Trick Room"']),
 'Kommo-o':   (.70, 'community', ['F3: Dragon Dance with speed control']),
 'Chandelure':(.70, 'community', ['F1: "earth shattering amounts of special attack"']),
 'Sigilyph':  (.65, 'community', ['F1: "fantastic Fairy/Ghost type"']),
 'Breloom':   (.70, 'community', ['F1: "a breloom that does more damage thanks to Tough Claws"']),
 'Milotic':   (.50, 'community', ['F1: "conditional"']),
}
# 23 Nov (Vincent): three Reddit inputs (team/community_inputs.json, shown on the Community tab): two V14 tier lists + one
# discussion. Rating = 2/3 x average tier-list mark + 1/3 x FORUM, then +/-0.02 per net gameplay comment (max 0.06).
import json as _json, os as _os
_INP = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..', 'workspace', 'team', 'community_inputs.json')
_KEY = {'KOMMOO': 'Kommo-o'}
def _sp(sid): return _KEY.get(sid, sid.title())
def consolidate():
    """{species: dict(rating, lists {input id: tier}, net, comments, base)} from the saved inputs."""
    try: D = _json.load(open(_INP))
    except Exception: return {}
    out = {}
    for i in D['inputs']:
        for t in i.get('tiers') or []:
            for m in t['mons']:
                if m['sid'] == 'PALOSSAND' and m['form'] != '1': continue   # Rocky = the best Palossand (input 2 OP)
                if m['sid'] == 'GASTRODON' and m['form'] != '2': continue   # West = the one he owns
                o = out.setdefault(_sp(m['sid']), dict(lists={}, marks=[], net=0, comments=[]))
                o['lists'][i['id']] = t['tier']; o['marks'].append(i['marks'][t['tier']])
        for c in i.get('comments') or []:
            o = out.setdefault(_sp(c['sid']), dict(lists={}, marks=[], net=0, comments=[]))
            o['net'] += c['v']; o['comments'].append(c)
    for sp, o in out.items():
        base = FORUM.get(sp, (None,))[0]
        avg = sum(o['marks']) / len(o['marks']) if o['marks'] else None
        r = (2 / 3 * avg + 1 / 3 * (base if base is not None else avg)) if avg is not None else base
        if r is None: continue
        o['base'] = base
        o['rating'] = round(min(.97, max(.2, r + max(-.06, min(.06, .02 * o['net'])))), 2)
    return {k: v for k, v in out.items() if 'rating' in v}
CONS = consolidate()
AEVIAN = dict(FORUM)
for _sp_, _o in CONS.items():
    _lines = [f'Reddit list {k}: {v}' for k, v in sorted(_o['lists'].items())]
    _cm = sorted(_o['comments'], key=lambda c: -abs(c['v']))[:2]
    _lines += ['Reddit: ' + c['text'] for c in _cm]
    if _sp_ == 'Paras': continue
    AEVIAN[_sp_] = (_o['rating'], 'community', _lines)

CREST = {
 'Zoroark Crest':  (.72, ['F5: crested Zoroark copying a strong partner is "pretty strong"', 'F3: Zoroark-Hisui: "almost every pokemon in the game dies to one of its moves"']),
 'Phione Crest':   (.55, ['W: +50% defences and Aqua Ring', 'F4: "whoever designed Phione Crest has my respect"']),
 'Furret Crest':   (.45, ['W: free Substitute (25% HP) on every switch-in', 'F4: listed among crests that "deserve more love"']),
 'Ariados Crest':  (.35, ['W: +50% Speed, crits on slowed / poisoned foes', 'F4: "barely useable on its own"']),
 'Whiscash Crest': (.40, ['F4: C tier', 'W: immune to Grass moves (they raise Attack instead)', 'W: +20% Atk and SpA']),
 'Dedenne Crest':  (.40, ['Game text: physical attacks use its Speed (base 101) instead of Attack (58)', 'Not discussed by the community']),
 'Typhlosion Crest': (.70, ['W: Atk = SpA', 'W: contact moves hit an extra time']),
}
# chapter each crest is FIRST obtainable (Vincent 22 Nov: earliest instance of wiki.gg Crests vs the BIGJRA walkthrough)
CREST_CH = {
 "Ariados Crest": 5,
 "Bastiodon Crest": 14,
 "Beheeyem Crest": 15,
 "Boltund Crest": 14,
 "Castform Crest": 13,
 "Celebi Crest": 16,
 "Cherrim Crest": 14,
 "Cinccino Crest": 14,
 "Claydol Crest": 14,
 "Cofagrigus Crest": 14,
 "Crabominable Crest": 13,
 "Cryogonal Crest": 13,
 "Darmanitan Crest": 14,
 "Dedenne Crest": 9,   # Vincent 23 Nov: available to him now (wiki listed Ch14)
 "Druddigon Crest": 9,
 "Dusknoir Crest": 14,
 "Electrode Crest": 8,
 "Empoleon Crest": 14,
 "Entei Crest": 16,
 "Fearow Crest": 8,
 "Feraligatr Crest": 9,
 "Flygon Crest": 13,
 "Furret Crest": 7,
 "Glaceon Crest": 13,
 "Gothitelle Crest": 13,
 "Hypno Crest": 13,
 "Infernape Crest": 14,
 "Leafeon Crest": 13,
 "Ledian Crest": 15,
 "Luvdisc Crest": 14,
 "Luxray Crest": 9,
 "Magcargo Crest": 13,
 "Meganium Crest": 9,
 "Minun Crest": 5,
 "Noctowl Crest": 5,
 "Oricorio Crest": 13,
 "Pangoro Crest": 16,
 "Phione Crest": 8,
 "Plusle Crest": 5,
 "Probopass Crest": 14,
 "Raikou Crest": 16,
 "Rampardos Crest": 14,
 "Relicanth Crest": 8,
 "Reuniclus Crest": 13,
 "Samurott Crest": 9,
 "Sawsbuck Crest": 12,
 "Seviper Crest": 13,
 "Shiinotic Crest": 15,
 "Silvally Crest": 8,
 "Simipour Crest": 5,
 "Simisage Crest": 5,
 "Simisear Crest": 5,
 "Skuntank Crest": 14,
 "Spiritomb Crest": 14,
 "Stantler Crest": 13,
 "Suicune Crest": 16,
 "Sunflora Crest": 14,
 "Swalot Crest": 8,
 "Thievul Crest": 5,
 "Torterra Crest": 14,
 "Typhlosion Crest": 9,
 "Vespiquen Crest": 13,
 "Whiscash Crest": 7,
 "Zangoose Crest": 14,
 "Zoroark Crest": 8,
 "Zorua Crest": 16
}

# 23 Nov (Vincent): every point players make that makes an Aevian strong (+1) or weak (-1), one thought per line, from all
# community inputs (L1 = 'tierslop' V14 list thread, L2 = UNSUBRAMEN V14 list thread, T3 = 'favorite Aevium form' thread,
# F = older forum posts). Kept for EVERY Aevian, owned or not: the Dex sheet shows it for his; the Community tab keeps the rest
# ('Not owned yet') so it is ready when he unlocks them. Game notes (legality / his box) are marked 'Note' (sign 0).
SENT = {
 'GOLISOPOD': [(1, 'Skill Link breaks several boss shields with one attack (L2, T3)'), (1, '"Hits like a truck" and tanks hits (T3, F)'),
               (1, 'Great under Trick Room (T3)'), (1, '6 players call it a favourite or a carry (T3)'),
               (-1, 'Can\'t set itself up as well as the top tier (L1)'), (-1, 'No First Impression (L1)')],
 'TOXTRICITY': [(1, 'Fire / Poison / Electric: "three crazy offensive types" (L2)'), (1, 'Players confirm it learns Torch Song (L2)'),
                (1, 'Punk Rock beats Galvanize: x1.3 vs x1.2, boosts Torch Song too (T3)'), (1, 'Punk Rock halves sound damage taken (T3)'),
                (1, '"An absolute beast with a bit of support" (T3)'), (1, '"One of my MVPs, controls the field" (T3)'),
                (1, 'Aevian-only run: belongs in A+ (L2)'), (-1, '"A special attacker. That\'s kinda it" (F, older version)')],
 'LAPRAS': [(1, 'No Guard Sing + Dragon Dance "can trivialise 2/3rds of the fights" (L1)'), (1, 'Swept about 2/3 of Ch7+ singles fights alone (L1)'),
            (1, 'Bulky enough to live a hit vs bosses (L1)'), (1, 'Trick Room and Perish Song options (L1)'),
            (-1, 'Slow: often hit before it can Sing (L2)'), (-1, 'Poor defensive typing (L2)'), (-1, '"Less good in doubles" (L1)'),
            (-1, '"Sleep strats are always inconsistent" (T3)')],
 'FROSLASS': [(1, 'Adaptability spread Water moves hit very hard (L2, T3, F)'), (1, 'Soak removes the foe\'s STAB, then Giga Drain heals (L2, T3)'),
              (1, 'The most-named favourite: 9 players (T3)'), (1, 'Common priority doesn\'t hurt it (L2)'),
              (-1, 'Weak defensive typing: many Fire / Flying / Ice foes (T3)'), (-1, '"Good for about half the game", then gets one-shot (T3)'),
              (0, 'Note: Water Spout is not legal for you yet'), (0, 'Note: its best sets want rain; you own no rain setter')],
 'DRAPION': [(1, '"My GOAT": carried hard trainer and Rift fights through Ch14 on Classic (T3)'), (1, '"A really fun mon to use" (T3)'),
             (1, 'S++ on list 1 (L1)')],
 'MUSHARNA': [(1, 'Sets Trick Room itself as a Dark/Fairy, not a Psychic type (L1, L2)'), (1, 'Tough Claws: hits very hard under Trick Room (L1, L2)'),
              (1, '"A must have for every dedicated Trick Room team" (L2)'), (1, 'Calm Mind egg move from the early egg (L2)'),
              (-1, 'Almost no speed: only good under Trick Room (F)'), (0, 'Note: Trick Room is not learnable for it in your game yet (only Oranguru)')],
 'GLALIE': [(1, 'Grassy Glide priority on Grassy Terrain (T3, F)'), (1, 'Helps set up grass teammates (T3)'),
            (-1, 'Low BST hurts it later in the game (L2)'), (-1, '"A bit one-note" (T3)')],
 'ROSERADE': [(1, 'Technician Vacuum Wave priority "goes hard" (L2, T3, F)'), (1, 'Mud Barrage coverage; Dry Skin (L2)'),
              (1, 'Pairs well with Golisopod-A: they cover a lot together (T3)'), (1, 'Helped beat Madame Shogun (T3)'),
              (-1, 'Fairly low speed (T3)')],
 'LEAVANNY': [(1, 'Intimidate + the fastest Sticky Web (T3, F)'), (1, 'On teams "pretty much the whole game" (T3)'),
              (1, 'Fell Stinger, then Baton Pass the boost (T3)'), (-1, 'Fragile in later fights (T3)'), (-1, 'One player dropped it as underwhelming (T3)')],
 'MISMAGIUS': [(1, 'Fast and hits hard; a good mixed attacker (T3, F)'), (1, 'Early Magic Guard, 3 good abilities (T3, F)'),
               (-1, 'Only A- / A on both V14 lists (L1, L2)')],
 'UNFEZANT': [(1, 'Sturdy + Tailwind "trivialises" many fights (L2, T3)'), (1, '"Carried me through gym battles" (L2, T3)'),
              (0, 'Note: Tailwind is past your level cap')],
 'AMPHAROS': [(1, 'Trick Room attacker with STAB Bolt-Beam (F)'), (1, '"Very useful" (T3)'),
              (-1, 'Fragile even with its crest and Filter (T3)'), (-1, 'Slow, with a weak defensive typing (F)')],
 'GASTRODON': [(1, 'Unique Ground/Fairy typing; Poison Heal setup (L1)'), (-1, '"Not especially great at any one thing" (L1)'),
               (-1, 'Slow; Gliscor does its job better (L1)')],
 'PALOSSAND': [(1, 'Rocky: early Stealth Rock, the best of the three (L2)'), (1, 'Fiery: an early Fire type with Will-O-Wisp (L2, T3)'),
               (1, 'Ghost Curse user (L2)'), (-1, 'Bottom tier on both V14 lists (L1, L2)'), (-1, '"Would not even bother" (F)')],
 'VELUZA': [(1, '"A much needed upgrade" over regular Veluza (T3)'), (1, 'Amazing (A+) on list 2 (L2)')],
 'PARASECT': [(1, 'Two lives: Sturdy, then its Ghost form (L1, F)'), (1, 'After the change: 105 Speed Spore + Rage Powder (L1)'),
              (1, 'Cheese KOs and counter-sweeps (T3)'), (-1, 'V14 changed Bad Poison on bosses: lost its boss-killer role (L2)'),
              (-1, 'Frail glass cannon (F)'), (0, 'Note: needs Xen Waste (Chapter 12)')],
 # not owned yet: saved for when he unlocks them
 'GLIMMORA': [(1, '"Quite possibly the most broken Pokémon ever created" (L1)'), (1, 'Steel/Flying: only 2 weaknesses (L1, L2)'),
              (1, 'Memory Leak: strong doubles support (L2, T3)'), (1, 'Healing Steel STAB keeps it alive (L1, L2)'),
              (1, 'Download; the mega never misses (L1, L2)'), (-1, 'One player could not make it work (L2)')],
 'SNEASLER': [(1, 'Better typing: an extra immunity, no 4x weakness (L1)'), (1, 'A "monster" under Tailwind (Wind Rider) (L1, L2, T3)'),
              (1, 'Sworn Duty heals allies; After You (L1)'), (1, '120 base Speed (L1)')],
 'VOLCARONA': [(1, 'Peak on list 2 (L2)'), (1, 'Quiver Dance + Roost with wide coverage (L1)'), (1, '"Busted as hell" (T3)'),
               (-1, 'Regular Volcarona does the same job better (L1)'), (-1, 'Loses Fire STAB on Heat Wave (L1)'), (-1, 'Fragile, no stand-out trait (T3)')],
 'KOMMOO': [(1, 'Sets itself up with Dragon Dance (L1)'), (1, 'Dragon Dance + Inexorable "is evil" (T3)'),
            (1, '"Carried half the major V14 fights" (L1)'), (1, 'A physical Poison/Dragon (T3)')],
 'GYARADOS': [(1, 'Multiscale or Intimidate (L1, L2)'), (1, 'Fiery Dance snowballs; Morning Sun / Roost heal (L1, L2)'),
              (1, 'MVP of several mono-Fire runs (L2, T3)'), (1, 'Dragon/Fire typing (L2)'),
              (-1, 'Fiery Dance boosts only 50% of the time (T3)'), (-1, 'Rock / Ground hits hurt (L1)')],
 'BRONZONG': [(1, 'V14 buff: takes the foe\'s type and resists it (L1)'), (1, 'Mirror Beam picks the best type (L1)'),
              (1, 'Bulky Trick Room setter (L1)'), (-1, '"Godsend or useless" depending on the fight; fell off late (T3)')],
 'MILOTIC': [(1, 'Defiant; Coil + Gunk Shot (L1)'), (1, '125 Sp. Def, Pain Split (L1)'), (1, 'Tanky: set up, then sweep (T3)'),
             (-1, 'Needs support to set up (T3)')],
 'SIGILYPH': [(1, 'Fairy/Ghost: a great defensive typing (T3, F)'), (1, 'Calm Mind + Roost; Magic Guard or Tinted Lens (T3)'),
              (1, 'Supreme on list 2 (L2)')],
 'CHANDELURE': [(1, 'Early Mystery Egg: Levitate, Eerie Impulse, Volt Switch (L2)'), (1, '"Won me over" (T3)'), (-1, 'Only B on list 2 (L2)')],
 'BRELOOM': [(1, 'Fast Spore is always good (L1, T3)'), (1, 'Fake Out; Tough Claws (F)'),
             (-1, 'Nerfed in V14; slow; falls off later (L2)'), (-1, '"A sidegrade" to regular Breloom (T3)')],
}
SENT['PARAS'] = SENT['PARASECT']
