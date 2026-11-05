"""Extract Pokemon availability, crests, mega stones, TMs and tutors from the BIGJRA walkthrough, chapters 1-7."""
import html, json, re, sys

h = open(sys.argv[1], encoding='utf-8').read()


def text(s):
    s = re.sub(r'<br\s*/?>', '\n', s)
    s = re.sub(r'<[^>]+>', '', s)
    return html.unescape(s).strip()


# walk the document in order, tracking chapter (h1) and area (h2/h3) headings
pat = re.compile(r'<h(\d)[^>]*id="([^"]+)"[^>]*>(.*?)</h\1>'
                 r'|<div class="encounter_section">(.*?)</table>\s*</div>'
                 r'|<div class="den_table">(.*?)</table></div>'
                 r'|<div class="shop_section">(.*?)</table></div>'
                 r'|<div class="trainer_section">(.*?)</table></div>'
                 r'|<p>(.*?)</p>|<li>(.*?)</li>', re.S)
chapter, area = '', ''
encounters, prose, shops, dens, trainers = [], [], [], [], []
for m in pat.finditer(h):
    if m.group(1):
        lvl, hid, t = int(m.group(1)), m.group(2), text(m.group(3))
        if lvl == 1:
            chapter = t
        if lvl in (2, 3):
            area = t
        continue
    ctx = dict(chapter=chapter, area=area)
    if m.group(4) is not None:
        for tbl in re.split(r'<table>', m.group(4)):
            if '<td' not in tbl:
                continue
            tm = re.search(r'<th colspan="\d+" class="table-header"[^>]*><strong>(.*?)</strong>', tbl)
            title = text(tm.group(1)) if tm else ''
            mons = []
            for row in re.findall(r'<tr>\s*<td[^>]*>(.*?)</td>(.*?)</tr>', tbl, re.S):
                nm = text(row[0])
                if nm and nm.lower() != 'pokemon':
                    mons.append(nm)
            encounters.append(dict(ctx, title=title, mons=mons))
    elif m.group(5) is not None:
        dens.append(dict(ctx, text=text(m.group(5))))
    elif m.group(6) is not None:
        shops.append(dict(ctx, text=text(m.group(6))))
    elif m.group(7) is not None:
        head = re.search(r'<th colspan="3"[^>]*>(.*?)</th>', m.group(7), re.S)
        trainers.append(dict(ctx, trainer=text(head.group(1)).replace('[show]', '').strip() if head else ''))
    else:
        t = text(m.group(8) or m.group(9) or '')
        if t:
            prose.append(dict(ctx, text=t))

# keep only chapters 1-7 (plus the prologue segment that precedes chapter 1)
def in_scope(c):
    mm = re.match(r'Chapter (\d+)', c)
    return (mm and 1 <= int(mm.group(1)) <= 7) or c in ('Prologue', '')

out = dict(
    encounters=[e for e in encounters if in_scope(e['chapter'])],
    prose=[p for p in prose if in_scope(p['chapter'])],
    shops=[s for s in shops if in_scope(s['chapter'])],
    dens=[d for d in dens if in_scope(d['chapter'])],
    trainers=[t for t in trainers if in_scope(t['chapter'])],
)
json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
print({k: len(v) for k, v in out.items()})
print(sorted({e['chapter'] for e in encounters}))
