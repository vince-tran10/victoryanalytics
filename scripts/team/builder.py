"""Team Builder tab (Vincent, 22 Nov): how each of the 4 CORE slots was picked.
For every slot: the role's job, then the best candidates for THAT slot with the other three core members kept in place
(same core score as cores.py: strength + defence + coverage + answers + identity + role fit), your pick marked.
Writes team/builder.json and inserts section 'sbuild' into the report (before tabs.py).
usage (from workspace/): DONE=... CR_RUN=r<run> python3 -I ../scripts/team/builder.py <report.html>"""
import contextlib, html, io, json, os, re, runpy, shutil, sys, tempfile
OUT = sys.argv[1]
tmp = tempfile.NamedTemporaryFile(suffix='.html', delete=False).name
shutil.copy(OUT, tmp)
_cs = 'team/cores.json'; _bak = open(_cs).read() if os.path.exists(_cs) else None
sys.argv = ['cores.py', tmp]
with contextlib.redirect_stdout(io.StringIO()):
    G = runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cores.py'))
if _bak is not None: open(_cs, 'w').write(_bak)   # cores.py writes cores.json: keep the real one
os.unlink(tmp)
Mon, rows_all, TYPES = G['Mon'], G['rows'], G['TYPES']
from kits import disp
E = html.escape
st = json.load(open('team/state.json'))
MT = json.load(open('gamedata/movetext.json')) if os.path.exists('gamedata/movetext.json') else {}
def mname(k): return (MT.get(k) or {}).get('name', k.title())
ALLM = {}
for r in rows_all:
    if r['name'] not in ALLM: ALLM[r['name']] = Mon(r)
core = [n for n in st['core'] if n in ALLM]
SPREAD = ['MAKEITRAIN', 'HEATWAVE', 'EARTHQUAKE', 'ROCKSLIDE', 'MUDDYWATER', 'DAZZLINGGLEAM', 'HYPERVOICE', 'ICYWIND', 'BLIZZARD', 'DISCHARGE',
          'SURF', 'SLUDGEWAVE', 'ERUPTION', 'WATERSPOUT', 'SNARL', 'BREAKINGSWIPE', 'LAVAPLUME', 'BULLDOZE', 'ELECTROWEB', 'BOOMBURST', 'EXPANDINGFORCE']
def first(L, ids): return next((mname(x) for x in ids if x in L), None)
def tools(m, slot):   # the role's tools this Pokémon can legally run (moves) or has (ability)
    L, ab = m.legal, set(m.r.get('abilities') or [])
    t = []
    if slot in (1, 2):
        if 'INTIMIDATE' in ab: t.append('Intimidate')
        if 'FAKEOUT' in L: t.append('Fake Out')
    if slot == 2:
        x = first(L, ['FOLLOWME', 'RAGEPOWDER']);  t += [x] if x else []
        if 'TAILWIND' in L: t.append('Tailwind')
        x = first(L, SPREAD); t += [f'spread: {x}'] if x else []
    if slot == 1:
        x = first(L, ['THUNDERWAVE', 'ICYWIND', 'ELECTROWEB', 'TAILWIND', 'TRICKROOM', 'GLARE', 'SCARYFACE']); t += [x] if x else []
        x = first(L, ['TAUNT', 'ENCORE']); t += [x] if x else []
        if ab & {'GOODASGOLD', 'MAGICGUARD', 'INSOMNIA', 'VITALSPIRIT', 'COMATOSE', 'PURIFYINGSALT'}: t.append('status-proof')
    if slot == 3:
        x = first(L, ['HAZE', 'CLEARSMOG', 'ROAR', 'WHIRLWIND']); t += [x] if x else []
        x = first(L, ['RECOVER', 'ROOST', 'SLACKOFF', 'MOONLIGHT', 'SYNTHESIS', 'SOFTBOILED', 'WISH', 'SHOREUP', 'STRENGTHSAP', 'MILKDRINK'])
        t += [x] if x else []
        if 'REGENERATOR' in ab: t.append('Regenerator')
        x = first(L, ['UTURN', 'VOLTSWITCH', 'FLIPTURN', 'PARTINGSHOT', 'TELEPORT']); t += [x] if x else []
    if slot == 4:
        setv = {'SWORDSDANCE': '+2', 'NASTYPLOT': '+2', 'SHELLSMASH': '+2', 'BELLYDRUM': '+6', 'FILLETAWAY': '+2', 'TAILGLOW': '+3', 'GEOMANCY': '+2',
                'DRAGONDANCE': '+1/+1', 'QUIVERDANCE': '+1/+1', 'SHIFTGEAR': '+1/+2', 'TIDYUP': '+1/+1', 'VICTORYDANCE': '+1',
                'CALMMIND': '+1', 'BULKUP': '+1', 'COIL': '+1', 'CURSE': '+1'}
        phys = m.r.get('cat') == 'Physical'
        ok = [k for k in setv if k in L and ((phys and k not in ('NASTYPLOT', 'CALMMIND', 'QUIVERDANCE', 'TAILGLOW', 'GEOMANCY')) or (not phys and k in ('NASTYPLOT', 'CALMMIND', 'QUIVERDANCE', 'SHELLSMASH', 'FILLETAWAY', 'TAILGLOW', 'GEOMANCY')))]
        if ok:
            best_ = max(ok, key=lambda k: {'+6': 6, '+3': 3, '+2': 2, '+1/+2': 1.9, '+1/+1': 1.6, '+1': 1}[setv[k]])
            t.append(f"{mname(best_)} ({setv[best_]})")
        for a_ in ('SPEEDBOOST', 'MOXIE', 'BEASTBOOST'):
            if a_ in ab: t.append(a_.title().replace('boost', ' Boost'))
    return t
NEED = {1: lambda m, t: bool(t) and (m.spe >= 80 or m.bulk >= 270),
        2: lambda m, t: any(x in ('Intimidate', 'Fake Out', 'Tailwind', 'Follow Me', 'Rage Powder') for x in t),
        3: lambda m, t: m.bulk >= 270 and any(not x.startswith('spread') for x in t),
        4: lambda m, t: bool(t)}
RK = {'S': 4, 'A': 3, 'B': 2, 'C': 1, 'D': 0}
ROLES = [
    ('Core 1 · Lead', ['Leads singles', 'Left slot in doubles', 'Fast (80+ base Speed) or bulky', 'Turn-1 tools: Intimidate, Fake Out, speed control, Taunt', 'Status-proof is a plus']),
    ('Core 2 · Doubles lead', ['Right slot in doubles', 'Must bring Intimidate, Fake Out, Follow Me / Rage Powder or Tailwind', 'A spread move is a plus']),
    ('Core 3 · Mid game', ['Bulky pivot (HP + Def + SpD 270+)', 'Must bring an answer: Haze / phazing, recovery, Regenerator or a pivot move']),
    ('Core 4 · Closer', ['Must have a setup move (or a boosting ability)', 'Bigger boosts rank higher (+2 beats +1)']),
]
def weak3(ms):
    return any(sum(m.mult[a] > 1 for m in ms) >= 3 for a in TYPES)
out = []
if len(core) == 4:
    base = [ALLM[n] for n in core]
    for i, (title, needs) in enumerate(ROLES):
        slot = i + 1; others = [m for j, m in enumerate(base) if j != i]
        res = []
        for m in ALLM.values():
            if m.sp in {o.sp for o in others}: continue
            t = tools(m, slot)
            if not NEED[slot](m, t): continue
            if weak3(others + [m]): continue
            sz = max([{'(+6)': 6, '(+3)': 3, '(+2)': 2, '(+1/+2)': 1.9, '(+1/+1)': 1.6, '(+1)': 1}.get(x.split(' ')[-1], 0) for x in t] + [0]) if slot == 4 else len(t)
            res.append((RK.get(m.r['tier'], 0), sz, m.r['blend'], m, t))
        res.sort(key=lambda x: (-x[0], -x[1], -x[2]))
        names = [x[3].name for x in res]
        top = res[:6]
        mine = base[i].name
        if mine not in [x[3].name for x in top]:
            hit = next((x for x in res if x[3].name == mine), None)
            if hit: top = top[:5] + [hit]
        out.append(dict(slot=slot, title=title, needs=needs, pick=mine, rank=(names.index(mine) + 1) if mine in names else None, of=len(res),
                        meets=mine in names,
                        cands=[dict(name=m.name, tier=m.r['tier'], tools=t, sid=m.r.get('sid'), form=str(m.r.get('form', '0')), pick=m.name == mine)
                               for _, _, _, m, t in top]))
json.dump(dict(core=core, slots=out), open('team/builder.json', 'w'), indent=1, ensure_ascii=False)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sprites as SP
cards = ''
for s_ in out:
    rows = ''
    for c in s_['cands']:
        rows += ('<li class="bc' + (' pick' if c['pick'] else '') + '"><div class="bct"><span class="tier t' + c['tier'] + '">' + c['tier'] + '</span>' + SP.tag(c['sid'], c['form'], size='s')
                 + '<b>' + E(disp(c['name'])) + '</b>' + ('<span class="bpick">Your pick</span>' if c['pick'] else '') + '</div>'
                 + '<div class="btools">' + ''.join('<span class="btool">' + E(x) + '</span>' for x in c['tools']) + '</div></li>')
    rank = ('Your pick ranks #' + str(s_['rank']) + ' of ' + str(s_['of']) + ' that fit this role') if s_['meets'] else ('Your pick doesn’t meet this role’s requirements')
    cards += ('<article class="bslot"><header><span class="bn">' + str(s_['slot']) + '</span><b>' + E(s_['title']) + '</b></header>'
              + '<ul class="bneeds">' + ''.join('<li>' + E(x) + '</li>' for x in s_['needs']) + '</ul>'
              + '<div class="bhead">Best for this role</div><ol class="bcands">' + rows + '</ol>'
              + '<div class="brank">' + E(rank) + '</div></article>')
sec = ('<section aria-labelledby="sbuild">\n  <h2 id="sbuild">Team Builder</h2>\n  <ul class="legend"><li>Every Pokémon you own is checked against each slot’s requirements (moves it can legally learn).</li>'
       '<li>Only those that meet them are listed, ranked by tier, then by how many of the role’s tools they bring.</li>'
       '<li>Pokémon that would give the core a weakness shared by 3 members are left out.</li></ul>\n'
       '  <div class="bgrid">' + cards + '</div>\n</section>\n')
page = open(OUT, encoding='utf-8').read()
page = re.sub(r'<section aria-labelledby="sbuild">.*?</section>\s*', '', page, flags=re.S)
anchor = page.find('<section aria-labelledby="s1f">')
page = page[:anchor] + sec + page[anchor:] if anchor >= 0 else page.replace('</main>', sec + '</main>')
open(OUT, 'w', encoding='utf-8').write(page)
print('builder:', [(s_['title'], disp(s_['pick']), s_['rank']) for s_ in out])
