"""Smogon knowledge layer: written analysis sets (pkmn.github.io/smogon) + usage stats (smogon.com/stats chaos).
meta(species) -> dict with singles/doubles sets and usage (moves, abilities, items, spreads, teammates).
Rejuvenation-only forms (Aevian, Idol fusions) are mapped to SV analogs that share the ability (extrapolation)."""
import json, os, re, glob
HERE = os.path.dirname(os.path.abspath(__file__))
SM = os.path.join(HERE, '..', '..', 'workspace', 'smogon')
SINGLES = ['gen9ubers', 'gen9ou', 'gen9uu', 'gen9ru', 'gen9nu', 'gen9nationaldexubers', 'gen9nationaldex', 'gen9nationaldexuu']
DOUBLES = ['gen9doublesou', 'gen9nationaldexdoubles']   # National Dex = every species, incl. those cut from SV
def _load(pat):
    out = {}
    for f in sorted(glob.glob(os.path.join(SM, pat))):
        out[os.path.basename(f).split('_', 1)[1].rsplit('.', 1)[0]] = json.load(open(f))
    return out
SETS = _load('sets_*.json')
CHAOS = {k: v['data'] for k, v in _load('chaos_*.json').items()}
def sd_name(rej):
    """Rejuvenation export name -> Showdown species name (None if the form doesn't exist in SV)."""
    n = rej.replace(' (Aevian Form)', '-Aevian').replace(' (Galarian Form)', '-Galar').replace(' (Alolan Form)', '-Alola')
    if 'Aevian' in n or 'Idol' in n or 'Dominant Fusion' in n:
        return None
    return {'Unfezant-M': 'Unfezant', 'Meowstic': 'Meowstic'}.get(n, n)
def usage(name, fmt):
    d = CHAOS.get(fmt, {}).get(name)
    if not d: return None
    tot = sum(d['Abilities'].values()) or 1
    top = lambda key, n: [(k, round(100 * v / tot)) for k, v in sorted(d[key].items(), key=lambda x: -x[1])[:n] if v / tot >= .05]
    return dict(fmt=fmt, usage=round(100 * d['usage'], 2), moves=top('Moves', 8), abilities=top('Abilities', 3), items=top('Items', 4),
                spreads=top('Spreads', 3), teammates=[k for k, v in sorted(d['Teammates'].items(), key=lambda x: -x[1])[:6]])
def meta(name):
    out = dict(name=name, singles_sets={}, doubles_sets={}, singles_usage=None, doubles_usage=None)
    for f in SINGLES:
        if name in SETS.get(f, {}): out['singles_sets'][f] = SETS[f][name]
    for f in DOUBLES:
        if name in SETS.get(f, {}): out['doubles_sets'][f] = SETS[f][name]
    for f in ['gen9ou-1695', 'gen9uu-1630', 'gen9ru-1630', 'gen9nu-1630', 'gen9nationaldex-1630', 'gen9nationaldexuu-1630']:
        u = usage(name, f)
        if u and (out['singles_usage'] is None or u['usage'] > out['singles_usage']['usage']): out['singles_usage'] = u
    for f in ['gen9doublesou-1695', 'gen9vgc2024regg-1630', 'gen9nationaldexdoubles-1500']:
        u = usage(name, f)
        if u and (out['doubles_usage'] is None or u['usage'] > out['doubles_usage']['usage']): out['doubles_usage'] = u
    return out
def analogs(ability, types=None, n=4):
    """SV species that run this ability in the usage data (best-used first): templates for Rejuvenation-only forms."""
    ab = re.sub(r'[^a-z]', '', ability.lower()); hits = {}
    for fmt, data in CHAOS.items():
        for sp, d in data.items():
            tot = sum(d['Abilities'].values()) or 1
            if d['Abilities'].get(ab, 0) / tot >= .5:
                hits[sp] = max(hits.get(sp, 0), d['usage'])
    return sorted(hits, key=lambda s: -hits[s])[:n]
