"""Planner tab (Vincent, 23 Nov): the next fight's six from team/planner.json. Inserts section 'splan' (before tabs.py).
One thought per line; explanations stay in chat. Tap a member -> the Dex sheet (same .bc[data-dn] handler as the Builder).
usage (from workspace/): python3 -I ../scripts/team/planner_tab.py <report.html>"""
import html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sprites as SP
import chapter_brief as CB
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
# 24 Nov (Vincent): the plan for the field (keep / break with Flash / change it, e.g. freeze Murkwater) + the model check, on top
_pl = P.get('plan') or 'keep'
_lead_alt = next((m['name'] for m in P['six'] if m.get('lead') and any(w.get('why', '').startswith('Turns the field') for w in m.get('why') or [])), None)
_gs = next((m['name'] for m in P['six'] if m.get('lead') and (m.get('ability') or '').upper().replace(' ', '') == 'GRASSYSURGE'), None)
_plan_txt = (f"Plan: {disp(_gs)} leads: Grassy Surge turns Murkwater into Grassy Terrain for 5 turns" if _pl == 'alt' and P.get('alt_field') == 'Grassy Terrain' and _gs
             else f"Plan: freeze the field ({P.get('alt_field')}): {disp(_lead_alt) if _lead_alt else 'the lead'} uses Blizzard turn 1" if _pl == 'alt'
             else 'Plan: break the field with Flash turn 1' if _pl == 'break' else f"Plan: fight on {P.get('field') or 'no field'}")
_alt = P.get('alt_plan') or {}
h += f'<article class="plc"><h3>{E(_plan_txt)}</h3>'
if _pl == 'alt' and P.get('alt_field') == 'Grassy Terrain':
    h += '<div class="pans cno">After 5 turns it is Murkwater again: Ground moves fail and Electric is x1.3</div><div class="pans cok">While it lasts: no Electric x1.3, no poison chip, no Speed drop, Raichu loses Surge Surfer</div>'
for fn_, mv_ in P.get('foe_break') or []:
    h += f'<div class="pans cno">{E(fn_)}: {E(mv_)} undoes it: KO it first or refreeze</div>'
if _alt.get('six'):
    h += f'<div class="pmuted">Other plan scored lower ({_alt.get("cmp")} vs {P.get("cmp")}): {E(", ".join(disp(x) for x in _alt["six"]))}</div>'
_mg = P.get('model_gaps') or []
h += ('<div class="pans cok">✓ Model check: every move, Mega and ability of theirs is modelled</div>' if not _mg
      else ''.join(f'<div class="pans cno">✗ Not modelled: {E(x)}</div>' for x in _mg)) + '</article>'
HB = h; h = ''   # 24 Nov (Vincent): BUILDER = header + plan + one dedicated counter per foe; everything else moves to Community > Checks
# their team
h += '<article class="plc"><h3>Their team</h3><ol class="pfoes">' + ''.join(
    f'<li class="{"plead" if i < L else ""}"><span class="pn">{i + 1}</span>{SP.tag(f["sid"], "0", size="s")}<span>{E(f["name"])}</span></li>' for i, f in enumerate(foes)) + '</ol>'
h += '</article>'
# 23 Nov (Vincent): 2) what makes this fight hard and how to beat it in this format (before the pick)
def _mind(items, miss):
    return ''.join(f'<li class="{"pw-ok" if x["ok"] else "pw-no"}"><b>{"✓" if x["ok"] else "✗"}</b> {E(x["text"])}'
                   + (f'<div class="pans">{E(", ".join(disp(w) for w in x["who"]))}</div>' if x['who'] else ('' if x['ok'] else f'<div class="pans">{E(miss)}</div>'))
                   + '</li>' for x in items)
if P.get('brief'):   # 23 Nov (Vincent): the Core check for THIS fight: green = the core covers it, red = what the flexes must bring
    _cv = [dict(x, ok=x.get('core_ok'), cov=x.get('core_cov') or []) for x in P['brief']]
    _ok = sum(1 for x in _cv if x['ok']); _no = sum(1 for x in _cv if x['ok'] is False)
    h += (f'<article class="plc"><h3>What the flexes must cover</h3><div class="pmuted">Core: {_ok} covered, {_no} left</div>'
          + CB.render(_cv, True, disp, 'flex')
          + (f'<div class="psub">{E(P["format"])} mindset: core only</div><ul class="pwin">{_mind(P.get("mind_core") or [], "flex")}</ul>' if P.get('mind_core') else '')
          + '</article>')
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
_BT = json.load(open('team/builder.json')).get('tags', {}) if os.path.exists('team/builder.json') else {}
def _short_fix(t):   # 'Stoutland: Work Up (+2 here)' -> 'Work Up'
    t = t.split(': ', 1)[1] if ': ' in t else t
    return re.sub(r'\s*\(.*$', '', t).replace(' heals', '')
def _good(m):   # 23 Nov (Vincent): what this Pokemon is good for (same chips as the Core tab)
    fu = next((b for x in P.get('brief') or [] if x['kind'] == 'fieldexploit' for a, b in x['cov'] if a == m['name']), None)
    fx_ = [_short_fix(t) for t in (P.get('flexwhy') or {}).get(m['name'], [])]
    return CB.good_for(_BT.get(disp(m['name'])), P['format'], fu, beats=[FN[j] for j in range(len(FN)) if m['deal'][j] >= 100], answers=fx_)
rows = ''
for m in [m for m in P['six'] if not m.get('core')]:   # 23 Nov (Vincent): only the 3 flexes here (the core is fixed for the chapter)
    wc = 'bad' if m['worst'] >= 100 else 'ok' if m['worst'] < 50 else ''
    walls = [FN[j] for j in sorted(range(len(FN)), key=lambda j: m['take'][j]) if m['take'][j] < 50]   # takes < 50% from it
    beats = [FN[j] for j in sorted(range(len(FN)), key=lambda j: -m['deal'][j]) if m['deal'][j] >= 100]
    rows += (f'<li class="bc pmem{" plead" if m["lead"] else ""}" data-dn="{E(disp(m["name"]))}" tabindex="0" role="button"><div class="bct">'
             f'<span class="tier t{m["tier"]}">{m["tier"]}</span>{SP.tag(m["sid"], m["form"], size="s")}<b>{E(disp(m["name"]))}</b>'
             + ('<span class="plt">Lead</span>' if m['lead'] else '') + '</div><div class="bchips">'
             + ''.join(f'<span class="btool">{E(c)}</span>' for c in _good(m))
             + '</div>'
             + ''.join(f'<div class="pans">{E(w)}</div>' for w in ((P.get('fbuild') or {}).get(m['name']) or {}).get('why', []) if 'replaces' in w)
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
_core = [m for m in P['six'] if m.get('core')]
_so = P.get('sitout') or {}
_nflex = len([m for m in P['six'] if not m.get('core')])
h += (f'<article class="plc"><h3>Your {_nflex} flexes</h3><div class="pmuted">Core: {E(", ".join(disp(m["name"]) for m in _core))}</div>'
      + ''.join(f'<div class="pans cno">{E(disp(n))} {E(w)}</div>' for n, w in _so.items())
      + f'<ul class="bl">{rows}</ul></article>')
# 23 Nov (Vincent): the FORMAT MINDSET checklist, honest: a tick only when the six really does it in this fight
MS = P.get('mindset')
if MS:
    _foes = [f['name'] for f in P['foes']]
    def _ln(ok, txt, subs): return (f'<li class="{"pw-ok" if ok else "pw-no"}"><b>{"✓" if ok else "✗"}</b> {E(txt)}'
                                    + ''.join(f'<div class="pans">{E(x)}</div>' for x in subs) + '</li>')
    li_ = ''
    no_ = [f for f in _foes if not MS['layered'].get(f)]
    two = [f for f in _foes if len(MS['layered'].get(f) or []) >= 2]
    li_ += _ln(not no_, f'Two checks per threat: {len(two)} of {len(_foes)}', [f'{f}: ' + ', '.join(disp(x) for x in MS['layered'][f]) for f in _foes if MS['layered'].get(f)][:3] + (['No check for ' + ', '.join(no_)] if no_ else []))
    li_ += _ln(bool(MS['priority']), 'Priority attack', [', '.join(disp(x) for x in MS['priority']) or 'None on the six'])
    li_ += _ln(len(MS['pivot']) >= 2, 'Safe switches (Regenerator / recovery / pivot)', [', '.join(disp(x) for x in MS['pivot']) or 'None'])
    for t_, w_ in (MS.get('immune') or {}).items():
        li_ += _ln(bool(w_), f'{t_.title()} immunity', [', '.join(disp(x) for x in w_) or 'None'])
    MSLI = li_

# 23 Nov (Vincent): 4) re-check with the whole six: every point answered, then the format mindset
if P.get('brief'):
    _ok = sum(1 for x in P['brief'] if x['ok']); _no = sum(1 for x in P['brief'] if x['ok'] is False)
    h += (f'<article class="plc"><h3>Re-check: your six</h3><div class="pmuted">{_ok} answered, {_no} not</div>'
          + CB.render(P['brief'], True, disp, 'not covered')
          + (f'<div class="psub">{E(P["format"])} mindset: your six</div><ul class="pwin">{_mind(P.get("mind_six") or [], "not covered")}</ul>' if P.get('mind_six') else '') + '</article>')
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
.pwhy .pbad { color: #b3261e } .pans.cok { color: #1f8a4c } .pans.cno { color: #b3261e } .pwin li.pw-nt b { color: var(--muted) } .pwhy .pgood { color: #1f8a4c } .bc.pft.pin { box-shadow: inset 0 0 0 2px var(--accent) }
.plc ul.bl { padding: 0; margin: 0; list-style: none; display: grid; gap: 6px } .pho summary { cursor: pointer; font-weight: 700 } .pho ol { margin: 6px 0 0; padding-left: 20px; font-size: 13px; display: grid; gap: 3px }
#splan + .pgrid, .pgrid { display: grid; gap: 14px }
</style>'''
# ---- 24 Nov (Vincent): their party in order, and for each one YOUR dedicated hard counter in the same slot (leads counter their leads)
_FB = P.get('fbuild') or {}; _MEM = {m['name']: m for m in P['six']}
_IBJ = json.load(open('team/ideal_builds.json')) if os.path.exists('team/ideal_builds.json') else {}
_FO = {f['name']: f for f in P['foes']}
try: _ABN = {k: v.get('name', k) for k, v in json.load(open('gamedata/abiltext.json')).items()}
except Exception: _ABN = {}
rows_ = ''
for k, c in enumerate(P.get('counters') or []):
    m = _MEM.get(c['member']) or {}; fb = _FB.get(c['member']) or {}; ib = _IBJ.get(c['member']) or {}
    f = _FO.get(c['foe']) or {}
    verdict = 'Hard counter' if c['hard'] else ('Wins the 1-v-1' if c['win'] else 'Best you have')
    lead_ = k < (2 if P['format'] == 'Doubles' else 1)
    moves_ = fb.get('moves') or m.get('moves') or []
    rows_ += (f'<li class="ctr{" ctr-lead" if lead_ else ""}"><div class="ctr-foe"><span class="pn">{k + 1}</span>{SP.tag(f.get("sid") or "", "0", size="s")}'
              f'<span>{E(c["foe"])}</span>' + (f'<small class="pmuted">{E(c["setup"])}</small>' if c.get('setup') else '') + '<span class="ctr-arrow">→</span></div>'
              f'<div class="ctr-me bc" data-dn="{E(disp(c["member"]))}" tabindex="0" role="button">'
              f'<div class="bct"><span class="pn">{k + 1}</span>{SP.tag(m.get("sid") or "", m.get("form") or "0", size="m")}<b>{E(disp(c["member"]))}</b>'
              + ('<span class="plt">Lead</span>' if lead_ else '') + '</div>'
              + '<div class="ctr-types">' + ''.join(pill(t) for t in (m.get('types') or [])) + '</div>'
              f'<div class="ctr-v {"ok" if c["hard"] else "mid" if c["win"] else "bad"}">{verdict}</div>'
              f'<div class="bchips"><span class="bstat">Deals {c["deal"]}%</span><span class="bstat">Takes {c["take_b"]}%' + (f' after {E(c["setup"])}' if c.get('setup') and c['take_b'] != c['take'] else '') + '</span>'
              f'<span class="bstat">{"Faster" if c["faster"] else "Slower"}</span></div>'
              f'<ul class="ctr-b"><li><b>Ability</b> {E(_ABN.get((m.get("ability") or ib.get("ability") or "").upper().replace(" ", ""), (m.get("ability") or ib.get("ability") or "").title()))}</li>'
              f'<li><b>Item</b> {E(fb.get("item") or ib.get("item") or "")}</li><li><b>Nature</b> {E(fb.get("nature") or ib.get("nature") or "")}</li>'
              f'<li><b>EVs</b> {E(fb.get("evs") or ib.get("evs") or "")}</li></ul>'
              '<div class="ctr-mv">' + ''.join(f'<span>{E(x)}</span>' for x in moves_) + '</div>'
              + ''.join(f'<div class="pans">{E(w)}</div>' for w in fb.get('why', []) if 'replaces' in w)
              + '<details class="pwhy" onclick="event.stopPropagation()"><summary>Why these moves</summary><ul>' + ''.join(
                  f'<li class="{"pflag" if w["flag"] else ""}"><b>{E(w["move"])}</b><span>{E(w["why"])}</span></li>' for w in m.get('why') or []) + '</ul></details>'
              + '<details class="pwhy" onclick="event.stopPropagation()"><summary>Other counters</summary><ul>' + ''.join(
                  f'<li><b>{E(disp(a["name"]))}</b><span>{"Hard counter" if a["hard"] else "Not a hard counter"}: deals {a["deal"]}%, takes {a["take_b"]}%, {"faster" if a["faster"] else "slower"}'
                  + (f' (already countering {E(a["used_for"])})' if a.get('used_for') else '') + '</span></li>' for a in c['alts']) + '</ul></details>'
              + '</div></li>')
nh = sum(1 for c in P.get('counters') or [] if c['hard'])
HB += (f'<article class="plc"><h3>Their team → your counters</h3><div class="pmuted">{nh} of {len(P.get("counters") or [])} are hard counters</div>'
       f'<ul class="ctrl">{rows_}</ul></article>')
css += '''<style id="ctr-css">.ctrl { list-style: none; margin: 0; padding: 0; display: grid; gap: 10px }
.ctr { display: grid; gap: 6px; padding: 8px; border-radius: 12px; background: var(--panel-2) } .ctr-lead { box-shadow: inset 0 0 0 2px var(--accent) }
.ctr-foe { display: flex; align-items: center; gap: 6px; font-weight: 700 } .ctr-arrow { margin-left: auto; color: var(--muted) }
.ctr-me { display: grid; gap: 4px; background: var(--panel); border-radius: 10px; padding: 8px } .ctr-types { display: flex; gap: 4px }
.ctr-v { font: 800 12px var(--body); text-transform: uppercase } .ctr-v.ok { color: #1f8a4c } .ctr-v.mid { color: #b45309 } .ctr-v.bad { color: #b3261e }
.ctr-b { list-style: none; margin: 0; padding: 0; display: grid; gap: 2px; font-size: 12.5px } .ctr-b b { color: var(--muted); font-weight: 600; margin-right: 4px }
.ctr-mv { display: grid; grid-template-columns: 1fr 1fr; gap: 4px } .ctr-mv span { font-size: 12.5px; padding: 4px 6px; border-radius: 8px; background: var(--panel-2) }
</style>'''
sec = f'<section aria-labelledby="splan">\n  <h2 id="splan">Builder</h2>\n{css}<div class="pgrid">{HB}</div>\n</section>\n'
sec += f'<section aria-labelledby="schk">\n  <h2 id="schk">Checks: {E(TITLE.get(P["fight"], P["fight"]))}</h2>\n<div class="pgrid">{h}</div>\n</section>\n'
page = open(OUT, encoding='utf-8').read()
page = re.sub(r'<section aria-labelledby="splan">.*?</section>\s*', '', page, flags=re.S)
page = re.sub(r'<section aria-labelledby="schk">.*?</section>\s*', '', page, flags=re.S)
anchor = page.find('<section aria-labelledby="s1f">')
page = page[:anchor] + sec + page[anchor:] if anchor >= 0 else page.replace('</main>', sec + '</main>')
open(OUT, 'w', encoding='utf-8').write(page)
print('planner tab:', P['fight'], [m['name'] for m in P['six']])
