"""Exact field effects from fieldtext.json, in the engine's FIELD format, + a comparison with bosses.FIELD."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gamedata as G
MAP = {'Mountain': 'MOUNTAIN', 'Mountain Field': 'MOUNTAIN', 'Volcanic Top': 'VOLCANICTOP', 'Volcanic Top Field': 'VOLCANICTOP',
       'Wasteland': 'WASTELAND', 'Beach Field': 'ASHENBEACH', 'Factory Field': 'FACTORY', 'Concert Venue': 'CONCERT1',
       'Water Surface': 'WATERSURFACE', 'Short-Circuit Field': 'SHORTCIRCUIT', 'Forest Field': 'FOREST', 'Swamp Field': 'SWAMP',
       'Big Top Arena': 'BIGTOP', 'Deep Earth Field': 'DEEPEARTH', 'Corrupted Cave': 'CORRUPTED'}
def game_field(key):
    f = G.load('fieldtext')[key]
    types = {t: float(m) for m, ts in f.get('typeBoosts', {}).items() for t in ts}
    moves = {mv: float(m) for m, ms in f.get('damageMods', {}).items() for mv in ms}
    add = {}
    for t2, ts in (f.get('typeAddOns') or {}).items():
        for t in ts: add[t] = t2
    return dict(name=f.get('name'), types=types, moves=moves, add=add, typeMods=f.get('typeMods') or {},
                fieldChange=f.get('fieldChange') or {}, accuracyMods=f.get('accuracyMods') or {}, raw=f)
if __name__ == '__main__':
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'team'))
    from bosses import FIELD
    for ours in ['Mountain Field', 'Volcanic Top Field', 'Wasteland', 'Beach Field', 'Factory Field', 'Concert Venue']:
        g = game_field(MAP[ours]); o = FIELD.get(ours) or {}
        print(f"\n=== {ours} -> {MAP[ours]} ({g['name']})")
        ot = o.get('types', {}); om = o.get('moves', {})
        for t in sorted(set(ot) | set(g['types'])):
            if ot.get(t, 1) != g['types'].get(t, 1): print(f"  type {t}: guide x{ot.get(t, 1)} -> game x{g['types'].get(t, 1)}")
        for mv in sorted(set(om) | set(g['moves'])):
            if om.get(mv, 1) != g['moves'].get(mv, 1): print(f"  move {mv}: guide x{om.get(mv, 1)} -> game x{g['moves'].get(mv, 1)}")
        if g['add']: print('  type add-ons (move type gains a 2nd type):', g['add'])
        if g['typeMods']: print('  typeMods:', g['typeMods'])
        if g['fieldChange']: print('  field changes:', {k: v for k, v in g['fieldChange'].items()})
