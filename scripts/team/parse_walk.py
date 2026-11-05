"""Parse BIGJRA walkthrough HTML (one chapter slice) into an ordered list of events + trainer teams."""
import html, json, re, sys

src = open(sys.argv[1], encoding='utf-8').read()


def text(s):
    s = re.sub(r'<br\s*/?>', '\n', s)
    s = re.sub(r'<[^>]+>', '', s)
    return html.unescape(s).strip()


events = []
pos = 0
pat = re.compile(r'<h(\d)[^>]*id="([^"]+)"[^>]*>(.*?)</h\1>|<div class="trainer_section">(.*?)</table></div>|<p>(.*?)</p>|<li>(.*?)</li>', re.S)
heading = []
for m in pat.finditer(src):
    if m.group(1):
        lvl = int(m.group(1))
        heading = heading[:lvl - 1] + [text(m.group(3))]
        events.append({'type': 'heading', 'level': lvl, 'text': text(m.group(3))})
    elif m.group(4) is not None:
        body = m.group(4)
        head = re.search(r'<th colspan="3"[^>]*>(.*?)</th>', body, re.S)
        htxt = text(head.group(1)) if head else ''
        htxt = htxt.replace('[show]', '').strip()
        lines = [l.strip() for l in htxt.split('\n') if l.strip()]
        trainer = lines[0] if lines else ''
        extra = lines[1:]
        field = next((l.split(':', 1)[1].strip() for l in extra if l.lower().startswith('field')), '')
        mons = []
        for row in re.findall(r'<tr>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>', body, re.S):
            a, b, c = (text(x) for x in row)
            al = [l.strip() for l in a.split('\n') if l.strip()]
            first = al[0] if al else ''
            mm = re.match(r'(.+?)(?:\s*\((M|F)\))?,\s*Lv\.\s*(\d+)', first)
            name = mm.group(1).strip() if mm else first
            lv = int(mm.group(3)) if mm else None
            item = next((l[1:].strip() for l in al if l.startswith('@')), '')
            ability = next((l.split(':', 1)[1].strip() for l in al if l.startswith('Ability')), '')
            typing = next((l.split(':', 1)[1].strip() for l in al if l.startswith('Typing')), '')
            form = next((l for l in al[1:] if not (l.startswith('@') or l.startswith('Ability') or l.startswith('Typing'))), '')
            moves = [l[1:].strip() for l in b.split('\n') if l.strip().startswith('-')]
            cl = [l.strip() for l in c.split('\n') if l.strip()]
            nature = next((l.replace(' Nature', '') for l in cl if l.endswith('Nature')), '')
            evs = next((l for l in cl if l.startswith('EVs')), '')
            ivs = next((l for l in cl if l.startswith('IVs')), '')
            base = next((l for l in cl if l.startswith('Base Stats')), '')
            mons.append(dict(name=name, level=lv, form=form, item=item, ability=ability, typing=typing, moves=moves,
                             nature=nature, evs=evs, ivs=ivs, base=base))
        events.append({'type': 'trainer', 'trainer': trainer, 'extra': extra, 'field': field, 'mons': mons,
                       'path': ' > '.join(heading)})
    else:
        t = text(m.group(5) or m.group(6) or '')
        if t:
            events.append({'type': 'text', 'text': t})
json.dump(events, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
for e in events:
    if e['type'] == 'heading':
        print('#' * e['level'], e['text'])
    elif e['type'] == 'trainer':
        lv = [m['level'] for m in e['mons']]
        print(f"   [T] {e['trainer']} | {e['field']} | {' ; '.join(e['extra'][1:] if e['field'] else e['extra'])} | n={len(lv)} lv={min(lv) if lv else ''}-{max(lv) if lv else ''} | "
              + ', '.join(m['name'] for m in e['mons']))
