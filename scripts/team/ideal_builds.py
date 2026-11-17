"""Ideal build for every owned Pokémon (Vincent, 17 Nov): what the community / developers actually run, not just max damage.
Sources, weighted per move / ability:
  * Rejuvenation's own trainer sets (gamedata/trainertext.json, same species + form; higher level = more weight, crested sets
    count extra when Vincent holds that crest). This is the main source for Aevians, crests and Rejuv-only moves.
  * Smogon sets (SV + National Dex, singles + doubles) for species that exist there.
Kept: only moves Vincent can legally teach (engine legal set). 3 moves + Protect (Lapras-Aevian: 4 moves, No Guard).
Missing slots are filled with the engine's best attacks. Nature / EVs / item follow CLAUDE.md build rules.
usage (from workspace/): RUN=r123 python3 -I ../scripts/team/ideal_builds.py   -> team/ideal_builds.json"""
import collections, json, os, pickle, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import smogon_meta as SM
from dataset import Data
D = Data('.')
BYNAME = {v['MoveName'].lower(): k for k, v in D.moves.items()}
st = json.load(open('team/state.json'))
run = os.environ.get('RUN') or f"r{st['run']}"
cands = pickle.load(open(f'team/{run}_native.json.pkl', 'rb'))['cands']
TT = json.load(open('gamedata/trainertext.json'))
I = json.load(open('gamedata/itemtext.json')) if os.path.exists('gamedata/itemtext.json') else {}
import crests, current_box as cb
HELD = {d['item'] for d in cb.parse(st['export']) if d.get('item') and 'Crest' in d['item']}
OWNED_CRESTS = set(st.get('crests_owned') or []) | HELD
CREST_IDS = {k for k, v in I.items() if (v.get('name') or '') in OWNED_CRESTS}
# builds written into CLAUDE.md win over the generated ones; the team's own builds come from state.json
FIXED = {'Lapras (Aevian Form)': dict(ability='NOGUARD', moves=['Rock Slide', 'Zen Headbutt', 'Dragon Dance', 'Sing'], item='Hard Stone'),
         'Gastrodon': dict(ability='STORMDRAIN', moves=['Earth Power', 'Muddy Water', 'Yawn', 'Protect'], item='Sitrus Berry', nature='Modest', evs='252 HP / 252 SpA'),
         'Furret': dict(ability=None, moves=['Follow Me', 'Super Fang', 'Baton Pass', 'Protect'], item=None, role='support'),   # crest: free Substitute -> support
         'Ceruledge': dict(ability=None, moves=['Bitter Blade', 'Shadow Claw', 'Swords Dance', 'Protect'], item='Focus Sash', nature='Jolly', evs='252 Atk / 252 Spe')}
NO = {'PROTECT', 'DETECT', 'TRICK', 'SWITCHEROO', 'FLING', 'LASTRESORT', 'FRUSTRATION', 'RETURN', 'HIDDENPOWER', 'NATUREPOWER',
      'SECRETPOWER', 'SOLARBEAM', 'SKYATTACK', 'FOCUSPUNCH', 'EXPLOSION', 'SELFDESTRUCT', 'FINALGAMBIT', 'MEMENTO', 'HEALINGWISH',
      'LUNARDANCE', 'DOUBLETEAM', 'MINIMIZE', 'ATTRACT', 'SWAGGER', 'CONFIDE', 'REST', 'SLEEPTALK', 'SNORE', 'GIGAIMPACT', 'HYPERBEAM'}
BOOSTER = {'STEEL': 'Metal Coat', 'FIGHTING': 'Black Belt', 'ROCK': 'Hard Stone', 'GROUND': 'Soft Sand', 'DRAGON': 'Dragon Fang',
           'DARK': 'Black Glasses', 'ELECTRIC': 'Magnet', 'WATER': 'Mystic Water', 'ICE': 'Never-Melt Ice', 'POISON': 'Poison Barb',
           'FAIRY': 'Fairy Feather', 'FIRE': 'Charcoal', 'GRASS': 'Miracle Seed', 'FLYING': 'Sharp Beak', 'BUG': 'Silver Powder',
           'PSYCHIC': 'Twisted Spoon', 'GHOST': 'Spell Tag', 'NORMAL': 'Silk Scarf'}
PHYS_SETUP = {'SWORDSDANCE', 'DRAGONDANCE', 'BULKUP', 'SHIFTGEAR', 'COIL', 'BELLYDRUM', 'VICTORYDANCE', 'TIDYUP', 'HONECLAWS'}
SPEC_SETUP = {'NASTYPLOT', 'CALMMIND', 'QUIVERDANCE', 'TAILGLOW'}


def mid(name):
    return BYNAME.get(str(name).lower())


def dev_sets(sid, form):
    out = []
    for t in TT:
        for m in t.get('mons') or []:
            if m.get('species') == sid and str(m.get('form', 0)) == str(form) and m.get('moves'):
                w = (m.get('level') or 50) / 100
                if m.get('item') in CREST_IDS: w *= 1.5
                out.append((w, m))
    return sorted(out, key=lambda x: -x[0])[:8]


def smogon_sets(name):
    sd = SM.sd_name(name.replace(' (Hisuian Form)', '-Hisui').replace(' (Paldean Form)', '-Paldea'))
    if not sd: return []
    m = SM.meta(sd); out = []
    for group, w in (('singles_sets', 1.0), ('doubles_sets', .8)):
        for fmt, sets in m[group].items():
            for sname, s in sets.items():
                out.append((w, s))
    return out


def best_for(c):
    legal = set(c['legal']); score = collections.Counter(); abil = collections.Counter(); srcs = []
    for w, m in dev_sets(c['sid'], c['form']):
        srcs.append('game'); abil[m.get('ability')] += w
        for x in m['moves']:
            if x: score[x] += w
    for w, s in smogon_sets(c['name']):
        srcs.append('smogon')
        a = s.get('ability'); a = a if isinstance(a, list) else [a]
        for x in a:
            if x: abil[x.upper().replace(' ', '').replace('-', '')] += w / len(a)
        for slot in s.get('moves', []):
            opts = slot if isinstance(slot, list) else [slot]
            for o in opts:
                k = mid(o)
                if k: score[k] += w / len(opts)
    phys = c['cat'] == 'Physical'
    ranked = [k for k, _ in score.most_common() if k in legal and k not in NO and k in D.moves]
    # wrong-stat attacks out; setup only for the right side
    def fits(k):
        mv = D.moves[k]
        if mv['Category'] == 'Status':
            if k in PHYS_SETUP: return phys
            if k in SPEC_SETUP: return not phys
            return True
        return (mv['Category'] == 'Physical') == phys
    picks = []
    for k in ranked:
        if not fits(k): continue
        mv = D.moves[k]
        if mv['Category'] != 'Status' and any(D.moves[p]['Category'] != 'Status' and D.moves[p]['Type'] == mv['Type'] for p in picks):
            continue   # no weaker same-type duplicate
        picks.append(k)
        if len(picks) == 3: break
    attacks = [p for p in picks if D.moves[p]['Category'] != 'Status']
    for a in c['attacks']:   # at least 2 attacks: fill from the engine's best
        if len(attacks) >= 2 or len(picks) >= 3 and len(attacks) >= 2: break
        if a not in picks and all(D.moves[p]['Type'] != D.moves[a]['Type'] for p in attacks):
            if len(picks) == 3: picks.remove(next(p for p in reversed(picks) if D.moves[p]['Category'] == 'Status'))
            picks.append(a); attacks.append(a)
    for a in c['attacks']:
        if len(picks) >= 3: break
        if a not in picks: picks.append(a)
    lapras = c['sid'] == 'LAPRAS' and str(c['form']) == '1'
    moves = [D.moves[p]['MoveName'] for p in picks] + ([] if lapras else ['Protect'])
    ab_ok = list(dict.fromkeys(c['abilities']))
    ab = next((a for a, _ in abil.most_common() if a in ab_ok), c['ability'])
    status_n = sum(1 for p in picks if D.moves[p]['Category'] == 'Status' and p not in PHYS_SETUP | SPEC_SETUP)
    role = 'support' if status_n >= 2 else 'attacker'
    cid = crests.CREST_OF.get(c['sid'])
    crest = I[cid]['name'] if cid in CREST_IDS else None
    main = next((p for p in picks if D.moves[p]['Category'] != 'Status'), None)
    item = crest or ('Sitrus Berry' if role == 'support' else BOOSTER.get(D.moves[main]['Type'], 'Sitrus Berry') if main else 'Sitrus Berry')
    fast = c['base']['Spe'] >= 85
    stat_ = 'Atk' if phys else 'SpA'
    nat = ('Jolly' if phys else 'Timid') if fast else ('Adamant' if phys else 'Modest')
    evs = f'252 {stat_} / 252 Spe' if fast else f'252 HP / 252 {stat_}'
    return dict(ability=ab, nature=nat, evs=evs, item=item, moves=moves, move_ids=picks, role=role,
                source='+'.join(sorted(set(srcs))) or 'engine')


out = {}
for c in sorted(cands, key=lambda c: c['gate'] != ''):
    if c['gate'] or c['name'] in out: continue
    b = best_for(c)
    if c['name'] in FIXED:
        f = dict(FIXED[c['name']]); f['ability'] = f['ability'] or b['ability']; f['item'] = f.get('item') or b['item']
        f['moves'] = [m for m in f['moves'] if mid(m) in set(c['legal']) or m == 'Protect'] or b['moves']; b.update(f); b['source'] = 'your rules'
    if c['name'] in st.get('moves', {}):   # the six as it is built now
        b.update(moves=st['moves'][c['name']], ability=(st.get('abilities') or {}).get(c['name'], b['ability']), source='your team')
    out[c['name']] = b
json.dump(out, open('team/ideal_builds.json', 'w'), indent=1, ensure_ascii=False)
for n in ['Golisopod (Aevian Form)', 'Furret', 'Veluza (Aevian Form)', 'Glalie (Aevian Form)', 'Gholdengo', 'Clodsire', 'Musharna (Aevian Form)',
          'Lapras (Aevian Form)', 'Parasect (Aevian Form)', 'Zoroark (Hisuian Form)', 'Arcanine (Hisuian Form)', 'Whiscash']:
    if n in out: print(n, '|', out[n]['ability'], out[n]['item'], out[n]['moves'], out[n]['role'], out[n]['source'])
print(len(out), 'builds')
