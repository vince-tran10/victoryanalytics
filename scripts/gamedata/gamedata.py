"""Rejuvenation's own data (converted from Scripts/Rejuv/Definitions/*.rb by to_json.rb) as Python helpers.

Classic difficulty = trainertext / bosstext (the *_story files are Story mode and are ignored).
Forms: montext[SPECIES] is an ordered dict of forms; form n = n-th key; a form only lists what differs from form 0.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
GD = os.path.join(HERE, '..', '..', 'workspace', 'gamedata')
STATS = ['HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe']   # game order (PBStats HP=0 … SPEED=5, SPATK=3, SPDEF=4)
STAT_IDX = {1: 'Atk', 2: 'Def', 3: 'SpA', 4: 'SpD', 5: 'Spe', 6: 'Acc', 7: 'Eva'}
_C = {}


def load(name):
    if name not in _C:
        _C[name] = json.load(open(os.path.join(GD, name + '.json')))
    return _C[name]


def available():
    return os.path.exists(os.path.join(GD, 'trainertext.json'))


def mon(species, form=0):
    """name, form name, types, base stats (list in STATS order), abilities for species/form."""
    forms = load('montext')[species]
    keys = list(forms)
    base = forms[keys[0]]
    f = dict(base); f.update({k: v for k, v in forms[keys[min(int(form or 0), len(keys) - 1)]].items() if v is not None})
    types = [t for t in (f.get('Type1'), f.get('Type2')) if t]
    if not types:   # e.g. Minior: core forms carry no types in montext; the typed form holds them
        tf = next((v for v in forms.values() if v.get('Type1')), {})
        types = [t for t in (tf.get('Type1'), tf.get('Type2')) if t]
    if len(types) == 2 and types[0] == types[1]:
        types = types[:1]
    return dict(name=base.get('name', species.title()), form=keys[min(int(form or 0), len(keys) - 1)], types=types,
                base=f['BaseStats'], abilities=f.get('Abilities', []), hidden=f.get('HiddenAbility'))


def move_name(m): return load('movetext').get(m, {}).get('name', m.title())
def item_name(i): return load('itemtext').get(i, {}).get('name', (i or '').title()) if i else ''
def abil_name(a): return load('abiltext').get(a, {}).get('name', (a or '').title()) if a else ''


def trainer(name, ttype, tid):
    for t in load('trainertext'):
        if t['teamid'] == [name, ttype, tid]:
            return t
    raise KeyError((name, ttype, tid))


def boss(key):
    return load('bosstext')[key]


def norm_mon(m, src):
    """One opposing Pokémon in a flat, comparable form. Boss mons take the boss file's moninfo (it overrides)."""
    shields, phases, sos = 0, {}, None
    if m.get('boss'):
        b = boss(m['boss'])
        bi = dict(m); bi.update(b['moninfo'])
        m, shields, phases, sos = bi, b.get('shieldCount', 0), b.get('onBreakEffects', {}), b.get('sosDetails')
    info = mon(m['species'], m.get('form', 0))
    if m['species'] == 'SILVALLY' and (m.get('item') or '').endswith('MEMORY'):   # RKS System: type = Memory
        info = dict(info, types=[m['item'][:-6]])
    ab = m.get('ability') or (info['abilities'][0] if info['abilities'] else '')
    # game defaults (Pokemon.rb applyIVs/applyEVs): NPC IVs 10 if unset, EVs min(85, level*3/2) if unset
    iv = m.get('iv', 10)
    ev = m.get('ev') if m.get('ev') is not None else [min(85, m['level'] * 3 // 2)] * 6
    return dict(src=src, species=m['species'], name=info['name'], form=info['form'], types=info['types'], base=info['base'],
                level=m['level'], item=item_name(m.get('item')), ability=abil_name(ab), nature=(m.get('nature') or 'HARDY').title(),
                moves=[move_name(x) + (f" ({m['hptype'].title()})" if x == 'HIDDENPOWER' and m.get('hptype') else '') for x in m.get('moves', [])],
                ev=ev, iv=iv, hptype=m.get('hptype'), shields=shields, phases=phases, sos=sos)


# Chapter 8 hard fights -> exact game entries (Classic). Two-trainer fights list both sides.
FIGHTS = {
    'eli':      [('Eli and Sharon', 'MISFORTUNATEDUO', 10)],
    'geara':    [('Geara', 'XENEXECUTIVE_3', 2), ('Zetta', 'XENEXECUTIVE_1', 8)],
    'giratina': [('???', 'ALGRISELDA', 0)],
    'holly':    [('Holly', 'COMMANDER', 0), ('Rorim B.', 'DISCOTEEN', 3)],
    'manaphy':  [('boss', 'SEAPRINCE')],
    'factory':  [('???', 'UNKNOWN_1', 1)],
    'amber':    [('Amber', 'LEADER_AMBER', 0)],
    'kyogre':   [('boss', 'BOSSKYOGRE')],
}


def fight_mons(key):
    out = []
    for e in FIGHTS[key]:
        if e[0] == 'boss':
            b = boss(e[1]); m = dict(b['moninfo'], boss=e[1])
            out.append(norm_mon(m, f'boss {e[1]}'))
        else:
            t = trainer(*e)
            out += [norm_mon(m, f'{e[0]} ({e[1]} #{e[2]})') for m in t['mons']]
    return out


# ---------------------------------------------------------------- engine feed (walkthrough-format dicts)
FIELD_NAME = {'WATERSURFACE': 'Water Surface', 'VOLCANICTOP': 'Volcanic Top Field', 'MOUNTAIN': 'Mountain',
              'ASHENBEACH': 'Beach Field', 'FACTORY': 'Factory Field', 'SHORTCIRCUIT': 'Short-Circuit Field', 'WASTELAND': 'Wasteland'}
STAGE = {-6: 2/8, -5: 2/7, -4: 2/6, -3: 2/5, -2: 2/4, -1: 2/3, 0: 1, 1: 1.5, 2: 2, 3: 2.5, 4: 3, 5: 3.5, 6: 4}


def _walk_mon(m, extra=None):
    """game mon dict -> the walkthrough dict format engine.build_foe expects."""
    info = mon(m['species'], m.get('form', 0))
    types = [m['item'][:-6]] if m['species'] == 'SILVALLY' and (m.get('item') or '').endswith('MEMORY') else info['types']
    ab = m.get('ability') or (info['abilities'][0] if info['abilities'] else '')
    ev = m.get('ev') if m.get('ev') is not None else [min(85, m['level'] * 3 // 2)] * 6
    d = {'specie': info['name'], 'level': m['level'], 'types': '/'.join(t.lower() for t in types), 'ability': abil_name(ab),
         'nature': (m.get('nature') or 'HARDY').title(), 'heldItem': item_name(m.get('item')), 'evs': ';'.join(map(str, ev)),
         'iv': m.get('iv', 10), 'boss': False, 'shields': '', 'form_text': info['form'], 'base_override': list(info['base']),
         'game': True}
    for i, mv in enumerate(m.get('moves', [])[:4]):
        d[f'move{i + 1}'] = f"{move_name(mv)};{(m.get('hptype') or '') if mv == 'HIDDENPOWER' else ''};"
    d.update(extra or {})
    return d


def boss_rows(m, bkey):
    """A shielded boss as one row per phase. N shields = N+1 full HP bars (Battler.rb pbReduceHP: a broken shield heals
    to full, overflow damage is lost). onBreakEffects[k] fire when the bar with k shields left breaks."""
    b = boss(bkey)
    base = dict(m); base.update(b['moninfo'])
    S = b.get('shieldCount', 0); eff = b.get('onBreakEffects', {})
    state = dict(moves=list(base.get('moves', [])), form=base.get('form', 0), item=base.get('item'), stages={}, field=None)
    bars = [dict(state, stages=dict(state['stages']))]
    for k in range(S, 0, -1):
        e = eff.get(str(k)) or {}
        if e.get('movesetUpdate'): state['moves'] = list(e['movesetUpdate'])
        if e.get('formchange') is not None: state['form'] = e['formchange']
        if e.get('itemchange'): state['item'] = e['itemchange']
        if e.get('fieldChange'): state['field'] = FIELD_NAME.get(e['fieldChange'], e['fieldChange'])
        for s, c in (e.get('bossStatChanges') or {}).items():
            st = STAT_IDX.get(int(s)); state['stages'][st] = max(-6, min(6, state['stages'].get(st, 0) + c))
        bars.append(dict(state, stages=dict(state['stages'])))
    rows, i = [], 0
    while i < len(bars):
        j = i
        while j + 1 < len(bars) and bars[j + 1] == bars[i]:
            j += 1
        st = bars[i]; n = j - i + 1
        gm = dict(base, moves=st['moves'], form=st['form'], item=st['item'])
        label = '' if len(bars) == 1 or (i == 0 and j == len(bars) - 1) else (f' (bars {i + 1}-{j + 1})' if n > 1 else f' (bar {i + 1})')
        rows.append(_walk_mon(gm, {'boss': True, 'bars': n, 'shields': str(n - 1), 'stages': st['stages'], 'field_override': st['field'],
                                  'phase': label.strip(' ()'), 'phase_label': label}))
        i = j + 1
    for sm in ((b.get('sosDetails') or {}).get('moninfos') or {}).values():
        rows.append(_walk_mon(sm, {'sos': True}))
    return rows


def walk_mons(key):
    out = []
    for e in FIGHTS[key]:
        if e[0] == 'boss':
            out += boss_rows({}, e[1])
        else:
            for m in trainer(*e)['mons']:
                out += boss_rows(m, m['boss']) if m.get('boss') else [_walk_mon(m)]
    return out
