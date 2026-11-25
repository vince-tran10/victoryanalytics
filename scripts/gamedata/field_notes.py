"""The game's OWN field notes (Vincent, 25 Nov: 'full field effect and all that it encompasses, so we don't miss anything').
Parses workspace/gamedata/fieldnotetext.rb (PBFieldNote.new(:FIELD, title, elaboration, stage, arguments: [...])) and resolves its
placeholders ({moves}, {abilities}...) from fieldtext.json, the same way the game's in-battle field-notes screen does.
notes(fe) -> [dict(title, text, stage, moves=[ids], abilities=[ids])]; to_html(s) turns the game markup into HTML."""
import html, json, os, re

GD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'workspace', 'gamedata')


def _load(n):
    try: return json.load(open(os.path.join(GD, n)))
    except Exception: return {}


FT, MV, AB = _load('fieldtext.json'), _load('movetext.json'), _load('abiltext.json')


def _calls(src, name):
    """every name( ... ) call with balanced parentheses (strings respected)"""
    out, i = [], 0
    while True:
        i = src.find(name + '(', i)
        if i < 0: return out
        j = i + len(name) + 1; depth = 1; q = None
        while j < len(src) and depth:
            c = src[j]
            if q:
                if c == '\\': j += 1
                elif c == q: q = None
            elif c in '"\'': q = c
            elif c == '(': depth += 1
            elif c == ')': depth -= 1
            j += 1
        out.append(src[i + len(name) + 1:j - 1]); i = j


def _split(args):
    """top-level comma split (strings / brackets / parens respected)"""
    out, cur, depth, q, k = [], '', 0, None, 0
    while k < len(args):
        c = args[k]
        if q:
            cur += c
            if c == '\\': cur += args[k + 1]; k += 1
            elif c == q: q = None
        elif c in '"\'': q = c; cur += c
        elif c in '([': depth += 1; cur += c
        elif c in ')]': depth -= 1; cur += c
        elif c == ',' and depth == 0: out.append(cur.strip()); cur = ''
        else: cur += c
        k += 1
    if cur.strip(): out.append(cur.strip())
    return out


def _str(tok):
    m = re.fullmatch(r'"(.*)"', tok.strip(), re.S)
    if not m: return None
    return m.group(1).encode().decode('unicode_escape') if '\\' in m.group(1) else m.group(1)


def _field_moves(expr):
    """fieldMoves(:F, :key, X) [- fieldMoves(...)]  ->  move ids"""
    def one(e):
        m = re.match(r'fieldMoves\(\s*:(\w+)\s*,\s*:(\w+)\s*,\s*:?([\w.]+)\s*\)', e.strip())
        if not m: return []
        f, key, x = m.groups(); d = (FT.get(f) or {}).get(key) or {}
        if key == 'damageMods': x = str(float(x)) if x.replace('.', '').isdigit() else x
        return list(d.get(x) or [])
    parts = [p for p in re.split(r'\s-\s', expr)]
    res = one(parts[0])
    for p in parts[1:]:
        sub = set(one(p)); res = [x for x in res if x not in sub]
    return res


def _syms(expr):
    return re.findall(r':(\w+)', expr) if expr.strip().startswith('[') else []


def mname(m): return (MV.get(m) or {}).get('longname') or (MV.get(m) or {}).get('name') or m.title()
def aname(a): return (AB.get(a) or {}).get('fullName') or (AB.get(a) or {}).get('name') or a.title()


def notes(fe):
    """the game's notes for field fe (staged fields like Concert Venue keep them all under the first stage, e.g. CONCERT1)"""
    src = open(os.path.join(GD, 'fieldnotetext.rb'), encoding='utf-8').read()
    base = re.sub(r'\d+$', '1', fe) if re.search(r'\d$', fe) else fe
    out = []
    for body in _calls(src, 'PBFieldNote.new'):
        a = _split(body)
        if not a or a[0].strip() != ':' + base: continue
        strs = [_str(x) for x in a[1:] if not x.startswith('arguments')]
        title = strs[0] if strs else ''
        text = strs[1] if len(strs) > 1 and strs[1] else ''
        stage = strs[2] if len(strs) > 2 and strs[2] else ''
        argx = next((x for x in a if x.startswith('arguments')), '')
        args = _split(argx.split(':', 1)[1].strip()[1:-1]) if argx else []
        moves, abils = [], []
        for e in args:
            if 'fieldMoves' in e: moves = _field_moves(e)
            elif _syms(e):
                ids = _syms(e)
                if all(i in AB for i in ids) and not all(i in MV for i in ids): abils = ids
                else: moves = moves or ids
        def fill(t):
            for k, lst, fn in (('moves', moves, mname), ('abilities', abils, aname)):
                for suf, j in (('Or', ' or '), ('And', ' and '), ('', ', ')):
                    t = t.replace('{' + k + suf + '}', j.join(fn(x) for x in lst))
            return t
        out.append(dict(title=fill(title), text=fill(text), stage=stage, moves=moves, abilities=abils))
    # the helper notes (nature power, natural type) from fieldtext
    d = FT.get(fe) or FT.get(base) or {}
    if d.get('naturePower'): out.append(dict(title=f"Nature Power becomes {mname(d['naturePower'])}", text='', stage='', moves=[], abilities=[]))
    if d.get('mimicry'): out.append(dict(title=f"Natural type: {d['mimicry'].title()} (Mimicry, Camouflage, Terrain Pulse, Shelter)", text='', stage='', moves=[], abilities=[]))
    return out


ICON = {'fieldUp': '▲', 'fieldDown': '▼', 'fieldChange': '→', 'fieldPlus': '+', 'fieldSleep': 'Sleep', 'fieldNoSleep': 'no sleep',
        'fieldBurn': 'burn', 'fieldParalyze': 'paralysis', 'fieldPoison': 'poison', 'fieldFreeze': 'freeze', 'field': ''}


def to_html(s):
    s = html.escape(s or '', quote=False)
    s = re.sub(r'&lt;c=(green|red|orange)&gt;(.*?)&lt;/c&gt;', lambda m: f'<b class="fn-{m.group(1)}">{m.group(2)}</b>', s)
    def icon(m):
        k = m.group(1).split(',')[0]
        if k.startswith('type'): return f'<span class="tp ty-{k[4:].lower()}">{k[4:].title()}</span>'
        tts = re.search(r'tts=\\?"([^"\\]*)', m.group(1))
        return ICON.get(k, tts.group(1) if tts else '')
    s = re.sub(r'&lt;icon=([^&]*?)&gt;', icon, s)
    return s.replace('\n', '<br>').replace(' . . .', '')


if __name__ == '__main__':
    import sys
    for n in notes(sys.argv[1] if len(sys.argv) > 1 else 'CONCERT1'):
        print(f"[{n['stage']}] {n['title']} | {n['text'][:160]}")
