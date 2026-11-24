"""Items he owns (Vincent, 24 Nov): every standard type booster, every berry, Focus Sash and the other standard held items, as many as
needed; NOT Leftovers, Life Orb or any Choice item. Plus everything seen held in any export (state items_seen), the crests he has had
(walkthrough + community.CREST_CH up to his chapter, state crests_owned) and the Mega Stones the walkthrough gives up to now (Megas are
not used: game rule set). One source for ideal_builds.py, make_report5.py and the Items tab (items_tab.py)."""
import json, os, re

BOOSTERS = {'NORMAL': 'Silk Scarf', 'FIRE': 'Charcoal', 'WATER': 'Mystic Water', 'GRASS': 'Miracle Seed', 'ELECTRIC': 'Magnet', 'ICE': 'Never-Melt Ice',
            'FIGHTING': 'Black Belt', 'POISON': 'Poison Barb', 'GROUND': 'Soft Sand', 'FLYING': 'Sharp Beak', 'PSYCHIC': 'Twisted Spoon', 'BUG': 'Silver Powder',
            'ROCK': 'Hard Stone', 'GHOST': 'Spell Tag', 'DRAGON': 'Dragon Fang', 'DARK': 'Black Glasses', 'STEEL': 'Metal Coat', 'FAIRY': 'Fairy Feather'}
NOT_OWNED = ['Leftovers', 'Life Orb', 'Choice Band', 'Choice Specs', 'Choice Scarf']
STANDARD = ['Focus Sash']
GD = 'gamedata'


def _items():
    try: return json.load(open(os.path.join(GD, 'itemtext.json')))
    except Exception: return {}


def berries():
    skip = {'Berry Juice', 'Berry Ice Cream', 'Razz Berry Tart'}
    return [v['name'] for v in _items().values() if (v.get('name') or '').endswith(' Berry') and v['name'] not in skip and '?' not in v['name']]


def walkthrough_finds(pattern):
    out = set()
    for f in ('walkthrough/ch1_7.json', 'walkthrough/ch8.json'):
        try: out |= set(re.findall(pattern, open(f).read()))
        except Exception: pass
    return out


def crests(st):
    try:
        import community
        cch = community.CREST_CH
    except Exception:
        cch = {}
    ch = int(st.get('chapter') or 9)
    have = {c for c, k in cch.items() if k < ch} | walkthrough_finds(r'([A-Z][a-z]+ Crest)') | set(st.get('crests_owned') or []) \
        | {k for k in (st.get('items_seen') or {}) if k.endswith(' Crest')}
    told = set(st.get('crests_owned') or []) | {k for k in (st.get('items_seen') or {}) if k.endswith(' Crest')}
    return sorted(c for c in have if cch.get(c, 0) < ch or c in told)   # this chapter's crests only once he has them


MEGA_RE = r'\b([A-Z][a-z]+ite(?: [XY])?)\b'
NOT_MEGA = {'Eviolite', 'Dragonite', 'Bergmite', 'Gabite', 'Meditite', 'Vanillite', 'Despite', 'Excite', 'Spite', 'White', 'Infinite', 'Graphite', 'Granite',
            'Termite', 'Favorite', 'Opposite', 'Polite', 'Quite', 'Write', 'Bite', 'Kite', 'Site', 'Unite', 'Invite', 'Ignite', 'Elite', 'Satellite'}


def megas(st):
    seen = {k for k in (st.get('items_seen') or {}) if k.endswith('ite') and k not in NOT_MEGA}
    return sorted((walkthrough_finds(MEGA_RE) - NOT_MEGA) | seen)


def owned(st):
    """-> dict(category -> [item names]) and a flat set; standard items are unlimited (count 99)"""
    cats = {'Type boosters': list(BOOSTERS.values()), 'Berries': berries(), 'Standard': STANDARD[:]}
    seen = [k for k in (st.get('items_seen') or {}) if k not in sum(cats.values(), []) and not k.endswith(' Crest') and k not in NOT_OWNED
            and not (k.endswith('ite') and k not in NOT_MEGA)]
    cats['Also held'] = sorted(seen)
    cats['Crests'] = crests(st)
    cats['Mega Stones'] = megas(st)
    flat = set(sum(cats.values(), [])) - set(NOT_OWNED)
    return cats, flat


def counts(st):
    """how many of each he can use at once: standard ones unlimited, the rest = most seen held at once (1 for crests)"""
    cats, flat = owned(st)
    c = {k: 99 for k in cats['Type boosters'] + cats['Berries'] + cats['Standard']}
    for k, v in (st.get('items_seen') or {}).items():
        c.setdefault(k, v)
    for k in cats['Crests'] + cats['Mega Stones'] + cats['Also held']:
        c.setdefault(k, 1)
    return c
