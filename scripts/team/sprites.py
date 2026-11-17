"""Pokémon sprites from Vincent's game files (workspace/gamedata/Battlers/<species>/<form>.png, kept out of git).
Each file is a 2x2 sheet: front normal, front shiny / back normal, back shiny (192 px cells). The page uses CSS classes
(sp-<species>-<form>[s]); theme.py embeds every class used ONCE as a data URI, so a sprite shown 10 times costs one copy.
usage: from sprites import tag, css_for(page)"""
import base64, io, json, os, re
BASE = os.path.join('gamedata', 'Battlers')


def cls(sid, form='0', shiny=False):
    return f"sp-{re.sub(r'[^a-z0-9]', '', (sid or '').lower())}-{form or '0'}{'s' if shiny else ''}"


def tag(sid, form='0', shiny=False, size='m'):
    """An inline sprite element (CSS draws it); size s/m/l picks the box size."""
    if not sid: return ''
    return f'<i class="spr spr-{size} {cls(sid, form, shiny)}" aria-hidden="true"></i>'


def _png(species, form, shiny):
    from PIL import Image
    d = os.path.join(BASE, species)
    f = os.path.join(d, f'{form}.png')
    if not os.path.exists(f): f = os.path.join(d, '0.png')
    if not os.path.exists(f): return None
    im = Image.open(f).convert('RGBA')
    w, h = im.size; cw = w // 2 if w >= 2 * h // 2 and w > 200 else w; ch = h // 2 if h > 200 else h
    cell = im.crop((cw if shiny else 0, 0, (2 * cw) if shiny else cw, ch))
    if not cell.getbbox():   # some sheets only have one cell drawn (e.g. shiny-only bosses like Rift Garbodor)
        cell = im.crop((0 if shiny else cw, 0, cw if shiny else 2 * cw, ch))
    bb = cell.getbbox()
    if bb: cell = cell.crop(bb)
    cell.thumbnail((96, 96), Image.NEAREST)
    buf = io.BytesIO(); cell.save(buf, 'PNG', optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def css_for(page):
    """CSS for every sprite class the page uses (one data URI each)."""
    if not os.path.isdir(BASE): return ''
    out = []
    for c in sorted(set(re.findall(r'\bsp-([a-z0-9]+)-(\d+)(s?)(?=[\s"])', page))):
        species, form, shiny = c
        b = _png(species, form, bool(shiny))
        if b: out.append(f'.sp-{species}-{form}{shiny}{{background-image:url(data:image/png;base64,{b})}}')
    return '\n'.join(out)


def boss_forms():
    """fight key -> (species id, form) for boss fights, from the game's boss definitions."""
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gamedata'))
        import gamedata as G
        B = json.load(open(os.path.join('gamedata', 'bosstext.json')))
        out = {}
        for k, v in G.FIGHTS.items():
            for x in v:
                if x and x[0] == 'boss' and x[1] in B:
                    mi = B[x[1]]['moninfo']; out[k] = (mi['species'], str(mi.get('form', 0)))
        return out
    except Exception:
        return {}
