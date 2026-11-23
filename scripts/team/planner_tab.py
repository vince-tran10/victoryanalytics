"""Planner tab (Vincent, 23 Nov): the next fight's six from team/planner.json. Inserts section 'splan' (before tabs.py).
One thought per line; explanations stay in chat. Tap a member -> the Dex sheet (same .bc[data-dn] handler as the Builder).
usage (from workspace/): python3 -I ../scripts/team/planner_tab.py <report.html>"""
import html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sprites as SP
from kits import disp
from cues import cues
os.environ.setdefault('MOVE_RULES', 'relearn')
import engine as _eng
_E = _eng.Engine(os.path.abspath('.'))
def _chart(t, types): return _E.chart_eff(t, types)
E = html.escape
OUT = sys.argv[1]
if not os.path.exists('team/planner.json'): sys.exit(0)
P = json.load(open('team/planner.json'))
TITLE = {'spector': 'Spector (day)', 'spector2': 'Spector (night)', 'jenner9': 'Spirit Jenner', 'erick': 'Erick', 'amanda': 'Amanda', 'karrina': 'Karrina'}
def pill(t): return f'<span class="tp ty-{t.lower()}">{t.title()}</span>'
def fx(m): return '0' if m == 0 else '¼' if m == .25 else '½' if m == .5 else '2×' if m == 2 else '4×' if m == 4 else ''
def fcls(m): return 'im' if m == 0 else 'rs' if m < 1 else 'w4' if m > 2 else 'wk' if m > 1 else ''
foes = P['foes']; L = 2 if P['format'] == 'Doubles' else 1
h = f'<div class="pl-head"><b>{E(TITLE.get(P["fight"], P["fight"]))}</b><span class="pchip">{E(P["field"] or "No field")}</span><span class="pchip">{E(P["format"])}</span></div>'
if P.get('break_field'):
    bf = P['break_field']
    h += f'<div class="pbreak">Turn 1: {E(disp(bf["user"]))} uses {E(bf["move"])} to break the field</div>'
# their team
h += '<article class="plc"><h3>Their team</h3><ol class="pfoes">' + ''.join(
    f'<li class="{"plead" if i < L else ""}"><span class="pn">{i + 1}</span>{SP.tag(f["sid"], "0", size="s")}<span>{E(f["name"])}</span></li>' for i, f in enumerate(foes)) + '</ol>'
h += '</article>'
# 23 Nov (Vincent): the game plan instead of rule text: leads + turn 1, then who takes each of their Pokémon
six = P['six']; FN = [f['name'] for f in foes]
def best_vs(j, pool):   # walls it (takes < 50%) and hits hardest; else the one that takes least
    w = [m for m in pool if m['take'][j] < 50]
    return max(w, key=lambda m: m['deal'][j]) if w else min(pool, key=lambda m: m['take'][j])
gp = []
ld = [m for m in six if m['lead']]
gp.append('Lead ' + ' + '.join(disp(m['name']) for m in ld))
for m in ld:
    j = max(range(L), key=lambda j: m['deal'][j])
    gp.append(f"Turn 1: {disp(m['name'])} hits {FN[j]} ({m['deal'][j]}%)")
for j in range(L, len(FN)):
    m = best_vs(j, six)
    gp.append(f"{FN[j]}: bring {disp(m['name'])} (takes {m['take'][j]}%)")
# our six
rows = ''
for m in P['six']:
    wc = 'bad' if m['worst'] >= 100 else 'ok' if m['worst'] < 50 else ''
    walls = [FN[j] for j in sorted(range(len(FN)), key=lambda j: m['take'][j]) if m['take'][j] < 50]   # takes < 50% from it
    beats = [FN[j] for j in sorted(range(len(FN)), key=lambda j: -m['deal'][j]) if m['deal'][j] >= 100]
    rows += (f'<li class="bc pmem{" plead" if m["lead"] else ""}" data-dn="{E(disp(m["name"]))}" tabindex="0" role="button"><div class="bct">'
             f'<span class="tier t{m["tier"]}">{m["tier"]}</span>{SP.tag(m["sid"], m["form"], size="s")}<b>{E(disp(m["name"]))}</b>'
             + ('<span class="plt">Lead</span>' if m['lead'] else '') + '</div><div class="bchips">'
             + (f'<span class="btool">{"Core" if m.get("core") else E((m.get("job") or "Flex").split(":")[0])}</span>')
             + ''.join(f'<span class="bstat bad">No Earthquake next to partner</span>' for _ in (m.get('warn') or [])[:1])
             + ''.join(f'<span class="{"btool" if k == "tool" else "bstat"}">{E(c)}</span>' for k, c in cues(m['types'], m['ability'], m['moves'], _chart)[:1 if m.get('warn') else 2])
             + '</div>'
             + '<details class="pwhy" onclick="event.stopPropagation()"><summary>Why these moves</summary><ul>' + ''.join(
                 f'<li class="{"pflag" if w["flag"] else ""}"><b>{E(w["move"])}</b><span>{E(w["why"])}</span></li>' for w in m.get('why') or []) + '</ul></details>'
             + (('<details class="pwhy" onclick="event.stopPropagation()"><summary>Swap options</summary><ul>' + ''.join(
                 f'<li><b>{SP.tag(x["sid"], x["form"], size="s")}{E(disp(x["name"]))} <span class="tier t{x["tier"]}">{x["tier"]}</span></b>'
                 f'<span>{"About as good" if x["delta"] > -3 else "Weaker for this fight"}</span>'
                 + ''.join(f'<span class="pgood">+ {E(g)}</span>' for g in x.get("gain") or [])
                 + ''.join(f'<span class="pbad">- {E(g)}</span>' for g in x.get("loss") or [])
                 + ('' if (x.get("gain") or x.get("loss")) else '<span>Same checks, lower score</span>') + '</li>'
                 for x in (P.get('swaps') or {}).get(m['name'], [])) + '</ul></details>') if (not m.get('core') and (P.get('swaps') or {}).get(m['name'])) else '')
             + '</li>')
h += f'<article class="plc"><h3>Your six</h3><ul class="bl">{rows}</ul></article>'
# 23 Nov (Vincent): the FORMAT MINDSET checklist, honest: a tick only when the six really does it in this fight
MS = P.get('mindset')
if MS:
    _foes = [f['name'] for f in P['foes']]
    def _ln(ok, txt, subs): return (f'<li class="{"pw-ok" if ok else "pw-no"}"><b>{"✓" if ok else "✗"}</b> {E(txt)}'
                                    + ''.join(f'<div class="pans">{E(x)}</div>' for x in subs) + '</li>')
    li_ = ''
    for f, (mv_, stg) in (MS.get('setup') or {}).items():
        sv = MS['layered'].get(f) or []
        li_ += _ln(bool(sv), f'{f} sets up: {mv_} (+{stg} here)', [f'Takes it after the boost: {", ".join(disp(x) for x in sv)}'] if sv else ['Nobody takes its boosted hit: KO it first or put it to sleep turn 1'])
    no_ = [f for f in _foes if not MS['layered'].get(f)]
    two = [f for f in _foes if len(MS['layered'].get(f) or []) >= 2]
    li_ += _ln(not no_, f'Two checks per threat: {len(two)} of {len(_foes)}', [f'{f}: ' + ', '.join(disp(x) for x in MS['layered'][f]) for f in _foes if MS['layered'].get(f)][:3] + (['No check for ' + ', '.join(no_)] if no_ else []))
    for f in _foes:   # speed: per foe faster than most of the six
        if sum(1 for v in MS['myspeed'].values() if v < MS['speeds'].get(f, 0)) < 4: continue
        rv = MS['revenge'].get(f) or []; pr = (MS.get('para') or {}).get(f) or []; sc = (MS.get('sc') or {}).get(f) or []
        if rv: li_ += _ln(True, f'{f} (Speed {MS["speeds"][f]}): outspeed and one-shot', [disp(rv[0])])
        elif pr: li_ += _ln(True, f'{f} (Speed {MS["speeds"][f]}): paralyse, then one-shot', [disp(sc[0].split(": ")[0]) + ': ' + sc[0].split(": ")[1], f'then {disp(pr[0])} outspeeds and one-shots'])
        elif sc: li_ += _ln(False, f'{f} (Speed {MS["speeds"][f]}): can be paralysed, nobody then one-shots it', [disp(sc[0].split(": ")[0]) + ': ' + sc[0].split(": ")[1]])
        else: li_ += _ln(False, f'{f} (Speed {MS["speeds"][f]}): no speed answer', [])
    li_ += _ln(bool(MS['priority']), 'Priority attack', [', '.join(disp(x) for x in MS['priority']) or 'None on the six'])
    li_ += _ln(len(MS['pivot']) >= 2, 'Safe switches (Regenerator / recovery / pivot)', [', '.join(disp(x) for x in MS['pivot']) or 'None'])
    for t_, w_ in (MS.get('immune') or {}).items():
        li_ += _ln(bool(w_), f'{t_.title()} immunity', [', '.join(disp(x) for x in w_) or 'None'])
    h += f'<article class="plc"><h3>{E(P["format"])} mindset</h3><ul class="pwin">{li_}</ul></article>'

# 23 Nov (Vincent): the guide's tips for this fight and how the six covers each one (collapsed)
TP = P.get('tips') or []
if TP:
    ok_ = sum(all(n['met_by'] for n in t['needs']) for t in TP)
    li_ = ''
    for t in TP:
        good = all(n['met_by'] for n in t['needs'])
        li_ += f'<li class="{"pw-ok" if good else "pw-no"}"><b>{"✓" if good else "✗"}</b> {E(t["tip"])}' + ''.join(
            ''.join(f'<div class="pans">{E(disp(x.split(": ", 1)[0]) + ": " + x.split(": ", 1)[1])}</div>' for x in n['met_by']) or '<div class="pans">Not covered on this six</div>'
            for n in t['needs']) + '</li>'
    h += f'<details class="plc pho"><summary>Guide tips: {ok_} of {len(TP)} covered</summary><ul class="pwin">{li_}</ul></details>'
# checks + alternatives
ck = P['checks']
lines = []
lines.append('✓ No attack type hits 3 of your six' if not ck['weak3'] else '✗ 3+ weak to ' + ', '.join(t.title() for t in ck['weak3']))
lines.append('✓ Every attack type they use is resisted' if not ck.get('nores') else '✗ Nobody resists: ' + ', '.join(t.title() for t in ck['nores']))
lines.append('✓ Each of their main attack types is resisted twice' if not ck['res_lt2'] else '✗ Resisted fewer than twice: ' + ', '.join(t.title() for t in ck['res_lt2']))
for n, f in ck['one_shot']: lines.append(f'! {disp(n)} can be one-shot by {f}: keep it away from it')
h += '<details class="plc pho"><summary>Details</summary><div class="psub">Game plan</div><ul class="pck">' + ''.join(f'<li>{E(x)}</li>' for x in gp) + '</ul><div class="psub">Checks</div><ul class="pck">' + ''.join(f'<li>{E(x)}</li>' for x in lines) + '</ul>'
if P['alts']:
    h += '<div class="psub">Close alternatives</div><ul class="pck">' + ''.join(
        f'<li>{E(", ".join(disp(n) for n in a["out"]))} → {E(", ".join(disp(n) for n in a["in"]))}</li>' for a in P['alts']) + '</ul>'
h += ('<div class="psub">How this six is picked</div><ol>'
      '<li>Pool = your Party + Active box</li><li>Scout: their six, their attack types after the field, how they win</li>'
      '<li>Defense first: every member takes their hits; no type hits 3; each type resisted twice</li>'
      '<li>Answers: one per way they win</li><li>Offense second</li><li>Leads: the pair that beats their lead pair</li>'
      '<li>Lost? Tell me what beat you: it becomes a threat to plan around</li></ol></details>')
css = '''<style id="plan-css">
.pl-head { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; font: 700 16px var(--display) }
.pchip { font: 600 11px var(--body); padding: 2px 8px; border-radius: 99px; background: var(--panel-2); color: var(--muted) }
.plc { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 12px 14px; display: grid; gap: 8px }
.plc h3 { margin: 0; font-size: 15px } .psub { font: 700 11px var(--body); letter-spacing: .05em; text-transform: uppercase; color: var(--muted) }
.pfoes { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 4px }
.pfoes li { display: flex; align-items: center; gap: 4px; font-size: 13px; padding: 3px 6px; border-radius: 8px; background: var(--panel-2) }
.pfoes li.plead { outline: 2px solid var(--accent) } .pn { font: 700 11px var(--body); color: var(--muted); width: 14px }
.pills { display: flex; flex-wrap: wrap; gap: 4px; align-items: center } .pills small { color: var(--muted); margin-right: 6px }
.pwin, .pck { list-style: none; margin: 0; padding: 0; display: grid; gap: 4px; font-size: 13px }
.pwin li.pw-ok b { color: #1f8a4c } .pwin li.pw-no b { color: #b3261e } .pans { padding-left: 18px; color: var(--muted); font-size: 12.5px }
.plt { margin-left: auto; font: 700 10px var(--body); text-transform: uppercase; color: var(--accent) }
.bc.pmem.plead { box-shadow: inset 0 0 0 2px var(--accent) }
.bstat.ok { background: rgba(31,138,76,.15); color: #1f8a4c } .bstat.bad { background: rgba(179,38,30,.15); color: #b3261e }
.ptm { overflow-x: auto }
.plc .tp { display: inline-block; padding: 1px 8px; border-radius: 6px; color: #fff; font: 600 11.5px var(--body); text-shadow: 0 1px 1px rgba(0,0,0,.35) }
.ptab { border-collapse: collapse; width: 100%; font-size: 12.5px } .ptab th, .ptab td { padding: 4px 3px; text-align: center; border-top: 1px solid var(--line) }
.ptab thead th { border-top: 0 } .ptab tbody th { text-align: left }
.ptab td.rs { background: var(--good-soft); color: var(--good); font-weight: 700 } .ptab td.im { background: var(--good-soft); color: var(--good); font-weight: 800 }
.ptab td.wk { background: var(--bad-soft, rgba(179,38,30,.12)); color: var(--bad); font-weight: 700 } .ptab td.w4 { background: var(--bad-soft, rgba(179,38,30,.2)); color: var(--bad); font-weight: 800 }
.ptab td.cnt.bad { color: var(--bad); font-weight: 800 } .ptab td.cnt.ok { color: var(--good) }
.plc .tp.ty-normal { background: #9a9a7a } .plc .tp.ty-fire { background: #e2703a } .plc .tp.ty-water { background: #4a86d8 } .plc .tp.ty-electric { background: #d6b21e } .plc .tp.ty-grass { background: #5ca83a } .plc .tp.ty-ice { background: #4fb3c4 } .plc .tp.ty-fighting { background: #b83a2e } .plc .tp.ty-poison { background: #9045a0 } .plc .tp.ty-ground { background: #b88a3a } .plc .tp.ty-flying { background: #7f8fe0 } .plc .tp.ty-psychic { background: #e0507a } .plc .tp.ty-bug { background: #8fa222 } .plc .tp.ty-rock { background: #a8923e } .plc .tp.ty-ghost { background: #6a5490 } .plc .tp.ty-dragon { background: #5a3fe0 } .plc .tp.ty-dark { background: #5a4a40 } .plc .tp.ty-steel { background: #8a8aa8 } .plc .tp.ty-fairy { background: #d97fae } 
.ptab .spr { transform: scale(.8) } .ptab th, .ptab td { padding: 3px 2px } .ptab thead th:nth-last-child(-n+2) { font-size: 10px }
.pcues { display: grid; gap: 2px; padding-left: 4px } .pcue { font-size: 12.5px; color: var(--ink) } .pcue::before { content: '▸ '; color: var(--accent) }
.pmt { table-layout: fixed } .pmt thead th:first-child { width: 36% } .pmt tbody th { font-weight: 600; font-size: 11.5px; white-space: normal; line-height: 1.25 } .pmv { display: block }
.pmt .tp { font-size: 9.5px; padding: 0 5px } .pmt .spr { transform: scale(.72); margin: -6px }
.pmt tr.pfo td { text-align: left; font: 700 11px var(--body); text-transform: uppercase; letter-spacing: .04em; color: var(--muted); padding-top: 8px; border-top: 0 }
.ptab td.fb { background: rgba(217,119,6,.14); color: #b45309; font-weight: 700 }
.pbreak { background: rgba(31,138,76,.12); color: #1f8a4c; font-weight: 700; padding: 8px 12px; border-radius: 10px; font-size: 13px }
.pwhy { margin-top: 4px; font-size: 12.5px } .pwhy summary { cursor: pointer; color: var(--muted); font-weight: 600 }
.pwhy ul { list-style: none; margin: 4px 0 0; padding: 0; display: grid; gap: 4px } .pwhy li { display: grid; gap: 1px } .pwhy li span { color: var(--muted) }
.pwhy li.pflag b { color: #b3261e } .pwhy li.pflag b::after { content: '  ⚠ check' }
.pwhy .pbad { color: #b3261e } .pwhy .pgood { color: #1f8a4c } .bc.pft.pin { box-shadow: inset 0 0 0 2px var(--accent) }
.plc ul.bl { padding: 0; margin: 0; list-style: none; display: grid; gap: 6px } .pho summary { cursor: pointer; font-weight: 700 } .pho ol { margin: 6px 0 0; padding-left: 20px; font-size: 13px; display: grid; gap: 3px }
#splan + .pgrid, .pgrid { display: grid; gap: 14px }
</style>'''
sec = f'<section aria-labelledby="splan">\n  <h2 id="splan">Flex</h2>\n{css}<div class="pgrid">{h}</div>\n</section>\n'
page = open(OUT, encoding='utf-8').read()
page = re.sub(r'<section aria-labelledby="splan">.*?</section>\s*', '', page, flags=re.S)
anchor = page.find('<section aria-labelledby="s1f">')
page = page[:anchor] + sec + page[anchor:] if anchor >= 0 else page.replace('</main>', sec + '</main>')
open(OUT, 'w', encoding='utf-8').write(page)
print('planner tab:', P['fight'], [m['name'] for m in P['six']])
