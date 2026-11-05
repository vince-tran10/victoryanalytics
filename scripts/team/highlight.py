"""Bold + underline every Pokémon name in the report's visible text; party mons get their role colour.

usage: python3 -I highlight.py report.html
"""
import re, sys, os, json
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, '..'))
from dataset import Data
D = Data(os.path.join(here, '..', '..', 'workspace'))
ROLE = {'Annihilape': 'lead', 'Chandelure': 'lead', 'Rhyperior': 'mid', 'Exeggutor': 'mid', 'Golisopod': 'closer', 'Glalie': 'closer'}
names = {v for k, v in D.names.items() if k in D.sp and isinstance(v, str) and len(v) > 2}
SUF = r'(?:-(?:Aevian|Hisui|Galar|Alola|Idol|Paldea|M|F)(?: \(Icy\))?| \((?:Aevian|Hisuian|Galarian|Alolan|Icy Aevian)(?: Form)?(?: Male)?\)| \((?:Lunatone|Solrock) Dominant Fusion\))?'
pat = re.compile(r'(?<![\w\-#])(' + '|'.join(re.escape(n) for n in sorted(names, key=len, reverse=True)) + r')' + SUF + r"(?![\w])")
SKIP = {'script', 'style', 'title', 'a', 'th', 'textarea', 'option', 'b', 'label'}
SKIP = {'script', 'style', 'title', 'a', 'th', 'textarea', 'option'}


def wrap(m):
    base = m.group(1)
    role = ROLE.get(base, '')
    return f'<b class="pk{(" pk-" + role) if role else ""}">{m.group(0)}</b>'


page = open(sys.argv[1], encoding='utf-8').read()
page = re.sub(r'<b class="pk[^"]*">(.*?)</b>', r'\1', page)          # idempotent
page = re.sub(r'<style id="pk-css">.*?</style>\n?', '', page, flags=re.S)
out, stack = [], []
for tok in re.split(r'(<[^>]+>)', page):
    if tok.startswith('<'):
        m = re.match(r'<(/?)([a-zA-Z0-9]+)', tok)
        if m and not tok.endswith('/>'):
            tag = m.group(2).lower()
            if m.group(1):
                if tag in stack:
                    while stack and stack.pop() != tag:
                        pass
            elif tag not in ('br', 'img', 'input', 'meta', 'link', 'hr', 'wbr'):
                stack.append(tag)
        out.append(tok)
    elif tok.strip() and not (set(stack) & SKIP) and 'head' not in stack:
        out.append(pat.sub(wrap, tok))
    else:
        out.append(tok)
page = ''.join(out)
css = '''<style id="pk-css">
.pk { font-weight: 650; text-decoration: underline; text-decoration-thickness: 1.5px; text-underline-offset: 3px; text-decoration-color: color-mix(in srgb, currentColor 45%, transparent) }
:root { --lead: #1d5fd1; --mid: #b45309; --closer: #a3218f }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --lead: #7aa9ff; --mid: #f5a54a; --closer: #f07fd9 } }
:root[data-theme="dark"] { --lead: #7aa9ff; --mid: #f5a54a; --closer: #f07fd9 }
.pk-lead, .role-lead { color: var(--lead) !important } .pk-mid, .role-mid { color: var(--mid) !important } .pk-closer, .role-closer { color: var(--closer) !important }
strong .pk, h3 .pk { font-weight: inherit }
.roster .pk { text-decoration: none; font-weight: 500 }
.roster .pk-lead, .roster .pk-mid, .roster .pk-closer { font-weight: 650 }
</style>'''
page = page.replace('</style>', '</style>\n' + css, 1)
open(sys.argv[1], 'w', encoding='utf-8').write(page)
print('wrapped', page.count('class="pk'))
