"""Insert/replace the Box audit section (04) in the report from an export.

usage: python3 -I box_audit.py report.html new_export.txt old_export.txt OLD_ACTIVE_START
Box layout in an export: party = first 6; then Overflow sorted A-Z; then Active sorted A-Z.
The Active box starts where the alphabetical order resets after the party.
"""
import re, sys, json, html, collections, subprocess, os
REPORT, NEW, OLD, OLD_START = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
PROMO = {p['n']: p for p in json.load(open(sys.argv[5]))} if len(sys.argv) > 5 else {}
NOTE = sys.argv[6] if len(sys.argv) > 6 else ''
CUTS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[5])), 'cuts.json'))) if len(sys.argv) > 5 else {'move': {}, 'maybe': {}}
here = os.path.dirname(os.path.abspath(__file__))


def parse(p):
    out = subprocess.run([sys.executable, '-I', os.path.join(here, 'parse_boxes.py'), p, '/dev/stdout'],
                         capture_output=True, text=True).stdout
    return json.loads(out[:out.rindex(']') + 1])


N, O = parse(NEW), parse(OLD)
# Active box = last alphabetical reset after #7
resets = [b['n'] for a, b in zip(N, N[1:]) if b['n'] > 7 and b['species'].lower() < a['species'].lower()]
starts = [r for r in resets if all(N[i - 1]['species'].lower() <= N[i]['species'].lower() for i in range(r, len(N)))]
ACT = starts[0]
box = lambda n, s: 'Party' if n <= 6 else ('Active' if n >= s else 'Overflow')
for d in N:
    d['box'] = box(d['n'], ACT)
PARTY_SP = {d['species'] for d in N if d['box'] == 'Party'}
oddsort = [b for a, b in zip(N, N[1:]) if b['n'] not in (7, ACT) and b['n'] > 7
           and b['species'].lower() < a['species'].lower()
           and not (b['species'].split('-')[0] == a['species'].split('-')[0])]
k = lambda d: (d['species'], d['gender'], d['nick'])
oc = collections.Counter((k(d), box(d['n'], OLD_START)) for d in O)
nc = collections.Counter((k(d), d['box']) for d in N)
moved_in = nc - oc
changes = sorted(f"{s} → {b}" for (kk, b), c in moved_in.items() for s in [kk[0]] * c)
gone = sorted(f"{kk[0]} (was {b})" for (kk, b), c in (oc - nc).items() for _ in range(c))
sys.path.insert(0, os.path.join(here, '..'))
from dataset import Data
DD = Data(os.path.join(here, '..', '..', 'workspace'))


def descendants(name):
    sid = re.sub(r'[^A-Z]', '', name.split('-')[0].upper())
    seen, todo = set(), [sid]
    while todo:
        x = todo.pop()
        for idx in (DD.sp.get(x) or {}):
            if not str(idx).isdigit():
                continue
            ev = DD.sp[x][idx].get('Evolutions') or []
            for i in range(0, len(ev), 5):
                if ev[i] in DD.sp and ev[i] not in seen:
                    seen.add(ev[i]); todo.append(ev[i])
    return {DD.nm(x).lower() for x in seen}


gone_l = [(kk, b) for (kk, b), c in (oc - nc).items() for _ in range(c)]
new_l = [(kk, b) for (kk, b), c in moved_in.items() for _ in range(c)]
rows = []
for kk, b in list(new_l):
    hit = next((g for g in gone_l if g[0] == kk), None) or next(
        (g for g in gone_l if g[0][1:] == kk[1:] and kk[0].split('-')[0].lower() in descendants(g[0][0])), None)
    if hit:
        gone_l.remove(hit)
        what = kk[0] if hit[0][0] == kk[0] else f"{hit[0][0]} evolved into {kk[0]}"
        rows.append(f"{what}: {hit[1]} → {b}" if hit[1] != b else f"{what} (stayed in {b})")
    else:
        rows.append(f"{kk[0]}: new, in {b}")
rows += [f"{kk[0]}: gone (was {b})" for kk, b in gone_l]
changes, gone = sorted(rows), []
cnt = collections.Counter(d['box'] for d in N)
esc = html.escape


def li(d):
    name = esc(d['species']) + (f' <span class="nick">“{esc(d["nick"])}”</span>' if d['nick'] else '')
    tag = ' <span class="b party">changed</span>' if (k(d), d['box']) in moved_in else ''
    if d['box'] == 'Active' and (d['species'] in CUTS['move'] or d['species'] in PARTY_SP):
        tag += ' <span class="b cut">to overflow</span>'
    elif d['box'] == 'Active' and d['species'] in CUTS['maybe']:
        tag += ' <span class="b maybe">your call</span>'
    if d['n'] in PROMO and d['box'] == 'Overflow':
        tag += ' <span class="b promote">promote</span>'
    return (f'<li data-n="{esc(d["species"].lower())} {esc(d["nick"].lower())}"><span class="idx num">#{d["n"]}</span>'
            f'<span class="nm">{name}{tag}</span><span class="lv num">Lv {d.get("level", "?")}</span></li>')


def group(title, b, opened, note):
    items = [d for d in N if d['box'] == b]
    return (f'<details class="bx panel"{" open" if opened else ""}><summary><b>{title}</b> '
            f'<span class="num">{len(items)}</span><span class="legend">{note}</span></summary>'
            f'<ul class="roster">{"".join(li(d) for d in items)}</ul></details>')


checks0 = [f'Total <b class="num">{len(N)}</b> = Party <b class="num">{cnt["Party"]}</b> + Active <b class="num">{cnt["Active"]}</b> + Overflow <b class="num">{cnt["Overflow"]}</b>',
          f'Active box starts at export entry <b class="num">#{ACT}</b> ({esc(N[ACT-1]["species"])}); each box is A–Z']
checks = checks0
if PROMO:
    checks.append(f'Overflow scan: <b class="num">{len(PROMO)}</b> Pokémon clear the Active-box bar (A tier or better on their own) and aren\'t already in your party or Active box. Tagged <span class="b promote">promote</span> below')
else:
    checks.append('Overflow scan: nobody else clears the Active-box bar (A tier or better on their own, ready now, not already owned in Active). Closest: Clawitzer, Scraggy → Scrafty (Lv 39), Ursaring → Ursaluna (needs a Peat Block)')
if oddsort:
    checks.append('Out of A–Z order in Overflow: ' + ', '.join(f'{esc(d["species"])} (#{d["n"]})' for d in oddsort))
chg = ('<li>' + '</li><li>'.join(esc(c) for c in changes) + '</li>') if changes else '<li>No changes</li>'
gn = ('<li>' + '</li><li>'.join(esc(c) for c in gone) + '</li>') if gone else '<li>None</li>'
sec = f'''<!--BOXAUDIT-->
<section aria-labelledby="s4">
  <h2 id="s4"><span class="n">04</span> Box audit <span class="tag">who you own, and where · export {len(N)} mons</span></h2>
  <div class="audit-top">
    <!-- completeness check (hidden): {' | '.join(re.sub('<[^>]+>', '', c) for c in checks)} -->
    <div class="panel pad"><h3>Since last export</h3>{('<p class="legend">' + esc(NOTE) + '</p>') if NOTE else ''}<ul class="plain">{chg}</ul></div>
  </div>
  <label class="find">Find a Pokémon <input type="search" id="boxfind" placeholder="e.g. Furret" autocomplete="off"></label>
  {group("Party", "Party", True, "")}
  {group("Active box", "Active", True, (str(sum(1 for d in N if d['box'] == 'Active' and (d['species'] in CUTS['move'] or d['species'] in PARTY_SP))) + " to move back to Overflow · see To do") if CUTS['move'] else "")}
  {group("Overflow boxes", "Overflow", bool(PROMO), (str(len(PROMO)) + " to promote · see To do") if PROMO else "tap to expand")}
</section>
<!--/BOXAUDIT-->'''
css = '''<style id="boxaudit-css">
.audit-top { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px }
.pad { padding: 14px 16px; display: grid; gap: 8px; align-content: start }
.plain { margin: 0; padding-left: 18px; display: grid; gap: 4px; font-size: 13.5px }
.bx summary { cursor: pointer; padding: 12px 16px; display: flex; gap: 10px; align-items: baseline; font-family: var(--display); font-size: 16px }
.bx summary .num { font-size: 13px; color: var(--accent) }
.roster { list-style: none; margin: 0; padding: 0 12px 12px; display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 0 14px }
.roster li { display: grid; grid-template-columns: 44px minmax(0, 1fr) auto; gap: 6px; padding: 4px 2px; border-bottom: 1px solid var(--line); font-size: 13px; align-items: baseline }
.roster .idx { font-size: 11px; color: var(--muted) } .nick { color: var(--muted) }
.find { display: flex; gap: 10px; align-items: center; font-size: 13.5px; flex-wrap: wrap }
.find input { font: inherit; padding: 6px 10px; border: 1px solid var(--line); border-radius: 6px; background: var(--panel); color: var(--ink); min-width: 0; flex: 1; max-width: 280px }
.roster li[hidden] { display: none }
.b.promote { background: var(--good-soft); color: var(--good) }
.b.cut { background: var(--bad-soft); color: var(--bad) } .b.maybe { background: var(--line); color: var(--muted) }
</style>'''
js = '''<script id="boxaudit-js">
(function(){var i=document.getElementById('boxfind');if(!i)return;i.addEventListener('input',function(){var q=i.value.trim().toLowerCase();
document.querySelectorAll('.roster li').forEach(function(li){li.hidden=q&&li.dataset.n.indexOf(q)<0;});
if(q)document.querySelectorAll('details.bx').forEach(function(d){d.open=!!d.querySelector('.roster li:not([hidden])');});});})();
</script>'''
page = open(REPORT, encoding='utf-8').read()
page = re.sub(r'<!--BOXAUDIT-->.*?<!--/BOXAUDIT-->\n?', '', page, flags=re.S)
page = re.sub(r'<style id="boxaudit-css">.*?</style>\n?', '', page, flags=re.S)
page = re.sub(r'<script id="boxaudit-js">.*?</script>\n?', '', page, flags=re.S)
page = page.replace('</style>', '</style>\n' + css, 1)
i = page.rindex('<footer')
page = page[:i] + sec + '\n\n' + page[i:]
page = page.replace('</body>', js + '\n</body>') if '</body>' in page else page + '\n' + js
open(REPORT, 'w', encoding='utf-8').write(page)
print('active start', ACT, dict(cnt), 'oddsort', [(d['species'], d['n']) for d in oddsort])
print('changes', changes); print('gone', gone)
