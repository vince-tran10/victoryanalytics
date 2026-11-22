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
ALL, core_score, id_balance, SFN, has_setup, real_builds, covered_of, ANS, strength = (G[k] for k in (
    'ALL', 'core_score', 'id_balance', 'SFN', 'has_setup', 'real_builds', 'covered_of', 'ANS', 'strength'))
from kits import disp
E = html.escape
st = json.load(open('team/state.json'))
core = [n for n in st['core'] if n in ALL]
ROLES = [
    ('Core 1 · Lead', ['Leads singles', 'Left slot in doubles', 'Fast or bulky enough to act on turn 1',
                       'Turn-1 tools: Intimidate, Fake Out, speed control, Taunt', 'Ideally immune or resistant to status']),
    ('Core 2 · Doubles lead', ['Right slot in doubles', 'Supports slot 1 on turn 1: Intimidate, Fake Out, redirection, Tailwind',
                               'Spread moves that hit both foes']),
    ('Core 3 · Mid game', ['Bulky pivot that comes in on hits aimed at the others', 'Covers the core\'s shared weaknesses',
                           'Brings an answer: Haze, recovery, pivoting']),
    ('Core 4 · Closer', ['One setup move, then sweeps (+2 beats +1)', 'Speed or bulk to survive the setup turn', 'Hits hard once boosted']),
]
def score(ms):
    _, bds = real_builds(tuple(ms), 'balance')
    fit = sum(f(m) for f, m in zip(SFN, ms)) / 4
    return core_score(tuple(ms), id_balance(tuple(ms)), len(covered_of(tuple(ms), bds)) / len(ANS)) + .15 * fit - (.05 if not has_setup(ms[3]) else 0)
out = []
if len(core) == 4:
    base = [ALL[n] for n in core]
    mine_sc = score(base)
    for i, (title, needs) in enumerate(ROLES):
        others = [m for j, m in enumerate(base) if j != i]
        res = []
        for m in ALL.values():
            if m.sp in {o.sp for o in others}: continue
            ms = list(base); ms[i] = m
            res.append((score(ms), SFN[i](m), m))
        res.sort(key=lambda x: -x[0])
        top = res[:5]
        if base[i].name not in [m.name for _, _, m in top]:
            top = top[:4] + [next(x for x in res if x[2].name == base[i].name)]
        rank = 1 + [m.name for _, _, m in res].index(base[i].name)
        out.append(dict(slot=i + 1, title=title, needs=needs, pick=base[i].name, rank=rank, of=len(res),
                        cands=[dict(name=m.name, tier=m.r['tier'], score=round(sc, 3), fit=round(f, 3), sid=m.r.get('sid'), form=str(m.r.get('form', '0')),
                                    pick=m.name == base[i].name) for sc, f, m in top]))
json.dump(dict(core=core, score=round(mine_sc, 3) if len(core) == 4 else None, slots=out), open('team/builder.json', 'w'), indent=1, ensure_ascii=False)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sprites as SP
cards = ''
for s_ in out:
    best = s_['cands'][0]['score']
    rows = ''
    for c in s_['cands']:
        gap = c['score'] - best
        rows += ('<li class="bc' + (' pick' if c['pick'] else '') + '"><span class="tier t' + c['tier'] + '">' + c['tier'] + '</span>' + SP.tag(c['sid'], c['form'], size='s')
                 + '<b>' + E(disp(c['name'])) + '</b>' + ('<span class="bpick">Your pick</span>' if c['pick'] else '')
                 + '<span class="bsc">' + f"{c['score']:.3f}" + '</span></li>')
    cards += ('<article class="bslot"><header><span class="bn">' + str(s_['slot']) + '</span><b>' + E(s_['title']) + '</b></header>'
              + '<ul class="bneeds">' + ''.join('<li>' + E(x) + '</li>' for x in s_['needs']) + '</ul>'
              + '<div class="bhead">Best for this slot <small>(other three kept)</small></div><ol class="bcands">' + rows + '</ol>'
              + '<div class="brank">Your pick ranks #' + str(s_['rank']) + ' of ' + str(s_['of']) + '</div></article>')
sec = ('<section aria-labelledby="sbuild">\n  <h2 id="sbuild">Team Builder</h2>\n  <ul class="legend"><li>Each core slot is scored with the other three core members kept in place: '
       'overall strength (tier), defence, coverage, answers, identity and how well it fills that role.</li></ul>\n'
       '  <div class="bgrid">' + cards + '</div>\n</section>\n')
page = open(OUT, encoding='utf-8').read()
page = re.sub(r'<section aria-labelledby="sbuild">.*?</section>\s*', '', page, flags=re.S)
anchor = page.find('<section aria-labelledby="s1f">')
page = page[:anchor] + sec + page[anchor:] if anchor >= 0 else page.replace('</main>', sec + '</main>')
open(OUT, 'w', encoding='utf-8').write(page)
print('builder:', [(s_['title'], disp(s_['pick']), f"#{s_['rank']}") for s_ in out])
