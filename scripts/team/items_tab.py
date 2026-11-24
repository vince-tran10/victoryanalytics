"""Items tab (Vincent, 24 Nov): every item he has (items_owned.py), grouped, with who on the six holds what. Section 'sitem'.
usage (from workspace/): python3 -I ../scripts/team/items_tab.py <report.html>"""
import html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import items_owned as IO
from kits import disp
E = html.escape
OUT = sys.argv[1]
st = json.load(open('team/state.json'))
IB = json.load(open('team/ideal_builds.json')) if os.path.exists('team/ideal_builds.json') else {}
IT = {v['name']: v for v in json.load(open('gamedata/itemtext.json')).values()} if os.path.exists('gamedata/itemtext.json') else {}
cats, flat = IO.owned(st)
held = {}   # item -> six members who hold it in the recommended builds
for n in st.get('team') or []:
    it = (st.get('items') or {}).get(n) or (IB.get(n) or {}).get('item')
    if it: held.setdefault(it, []).append(disp(n))
TYPES = {v: k for k, v in IO.BOOSTERS.items()}
def pill(t): return f'<span class="tp ty-{t.lower()}">{t.title()}</span>'
def row(name, extra=''):
    who = held.get(name)
    return (f'<li class="itr{" used" if who else ""}"><b>{E(name)}</b>{extra}'
            + (f'<span class="itw">{E(", ".join(who))}</span>' if who else '') + '</li>')
h = ''
if held:
    h += ('<article class="plc"><h3>Your six holds</h3><ul class="itl">' + ''.join(
        f'<li class="itr used"><b>{E(i)}</b><span class="itw">{E(", ".join(w))}</span></li>' for i, w in held.items()) + '</ul></article>')
h += ('<article class="plc"><h3>Type boosters</h3><div class="pmuted">x1.2 to moves of that type</div><ul class="itl">'
      + ''.join(row(i, pill(TYPES[i])) for i in cats['Type boosters']) + '</ul></article>')
# berries: the useful groups first
def btype(n):
    m = re.search(r'(\w+)-type attack', (IT.get(n) or {}).get('desc') or '')
    return m.group(1).upper() if m else None
key = [b for b in cats['Berries'] if b in ('Sitrus Berry', 'Lum Berry')]
resist = [b for b in cats['Berries'] if btype(b)]
pinch = [b for b in cats['Berries'] if 'in a pinch' in ((IT.get(b) or {}).get('desc') or '')]
rest = [b for b in cats['Berries'] if b not in key + resist + pinch]
h += ('<article class="plc"><h3>Berries</h3><ul class="itl">' + ''.join(row(b, f'<span class="pmuted">{E(((IT.get(b) or {}).get("desc") or ""))}</span>') for b in key) + '</ul>'
      + '<div class="psub">Resist berries (halve one super-effective hit)</div><ul class="itl">' + ''.join(row(b, pill(btype(b))) for b in resist) + '</ul>'
      + '<details class="pho"><summary>Pinch berries (' + str(len(pinch)) + ')</summary><ul class="itl">' + ''.join(row(b) for b in pinch) + '</ul></details>'
      + '<details class="pho"><summary>Other berries (' + str(len(rest)) + ')</summary><ul class="itl">' + ''.join(row(b) for b in rest) + '</ul></details></article>')
h += ('<article class="plc"><h3>Other held items</h3><ul class="itl">' + ''.join(
    row(i, f'<span class="pmuted">{E(((IT.get(i) or {}).get("desc") or ""))}</span>') for i in cats['Standard'] + cats['Also held']) + '</ul></article>')
h += ('<article class="plc"><h3>Crests</h3><div class="pmuted">Up to Chapter 8 in the walkthrough, plus the ones you told me about</div><ul class="itl">'
      + ''.join(row(c, f'<span class="pmuted">{E(((IT.get(c) or {}).get("desc") or ""))}</span>') for c in cats['Crests']) + '</ul></article>')
h += ('<article class="plc"><h3>Mega Stones</h3><div class="pmuted">Not used: no Megas in your rules</div><ul class="itl">'
      + ''.join(row(m) for m in cats['Mega Stones']) + '</ul></article>')
h += ('<article class="plc"><h3>Not in your bag</h3><ul class="itl">' + ''.join(f'<li class="itr no"><b>{E(i)}</b></li>' for i in IO.NOT_OWNED) + '</ul></article>')
css = '''<style id="items-css">.itl { list-style: none; margin: 0; padding: 0; display: grid; gap: 4px; font-size: 13px }
.itr { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; padding: 4px 6px; border-radius: 8px; background: var(--panel-2) }
.itr.used { box-shadow: inset 0 0 0 2px var(--accent) } .itr.no b { color: #b3261e; text-decoration: line-through }
.itw { margin-left: auto; font-size: 11.5px; font-weight: 700; color: var(--accent) }
.itr .tp { display: inline-block; padding: 1px 8px; border-radius: 6px; color: #fff; font: 600 11px var(--body) }
</style>'''
sec = f'<section aria-labelledby="sitem">\n  <h2 id="sitem">Items</h2>\n{css}<div class="pgrid">{h}</div>\n</section>\n'
page = open(OUT, encoding='utf-8').read()
page = re.sub(r'<section aria-labelledby="sitem">.*?</section>\s*', '', page, flags=re.S)
anchor = page.find('<section aria-labelledby="s1f">')
page = page[:anchor] + sec + page[anchor:] if anchor >= 0 else page.replace('</main>', sec + '</main>')
open(OUT, 'w', encoding='utf-8').write(page)
print('items tab:', {k: len(v) for k, v in cats.items()}, 'held by six:', held)
