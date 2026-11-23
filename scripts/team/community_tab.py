"""Community tab (Vincent, 23 Nov): every community input he sends is saved in team/community_inputs.json and shown here,
then consolidated against the guide's current Aevian ratings (community.py AEVIAN). Inserts section 'scomm' (before tabs.py).
Proposed rating = 2/3 V14 tier-list mark + 1/3 the older forum rating (newer group consensus weighs more). Not applied to the
tiers until Vincent says so (all inputs in).
usage (from workspace/): python3 -I ../scripts/team/community_tab.py <report.html>"""
import json, os, re, sys, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sprites as SP
import community as CM
E = html.escape
OUT = sys.argv[1]
D = json.load(open('team/community_inputs.json'))
TA = {(r['sid'], str(r['form'])): r for r in json.load(open('team/tier_all.json'))['rows'] if r.get('kind') == 'aevian' or 'Aevian' in r['name']}
NM = {'KOMMOO': 'Kommo-o'}
def nm(sid, form):
    base = NM.get(sid, sid.title())
    extra = {('PALOSSAND', '1'): ' Rocky', ('PALOSSAND', '2'): ' Fiery', ('PALOSSAND', '3'): ' Icy',
             ('GASTRODON', '2'): ' West', ('GASTRODON', '3'): ' East', ('FLORGES', '5'): ' Reborn'}.get((sid, form), '')
    return base + extra if sid == 'FLORGES' else base + '-A' + extra
def owned(sid, form):
    if sid == 'GASTRODON': form = '1' if form == '2' else 'x'   # tier_all keys the owned West Aevian form as 1
    r = TA.get((sid, form))
    return r if r and r.get('owned_as') else None

cards = ''
NAME = {}
def nm2(sid): return nm(sid, '2' if sid == 'TOXTRICITY' else '1')
# 1) the inputs
li = ''
for i in D['inputs']:
    li += f'<li><b>{i["id"]}</b> <a href="{E(i["url"])}" target="_blank" rel="noopener">{E(i["title"])}</a>'
    li += ''.join(f'<div class="cnote">{E(x)}</div>' for x in [i.get('source'), i.get('decoded'), i.get('ignored')] if x)
    li += '</li>'
cards += f'<article class="ccard"><h3>Inputs</h3><ol class="cin">{li}</ol><div class="cnote">{E(D.get("dropped", ""))}</div></article>'
# 23 Nov (Vincent): format MINDSETS (how a format is won); the planner scores the checks for that format
for fmt_, m_ in (D.get('mindset') or {}).items():
    li_ = ''.join(f'<li><b>{E(x["rule"])}</b><div class="cnote">{E(x["how"])}</div></li>' for x in m_['points'])
    src_ = ''.join(f'<div class="cnote"><a href="{E(u)}" target="_blank" rel="noopener">{E(u.split("//")[1][:48])}</a></div>' for u in m_.get('urls', []))
    cards += (f'<article class="ccard"><h3>{E(m_["title"])}</h3><div class="cnote">{"Used to pick the core and the flexes" if fmt_ == "rejuv" else "Used to pick flexes in every " + E(fmt_) + " fight"}</div>'
              f'<ol class="cin">{li_}</ol><details><summary>Sources</summary>{src_}</details></article>')
# 2) each tier list (folded)
for i in D['inputs']:
    if not i.get('tiers'): continue
    rows = ''
    for t in i['tiers']:
        tiles = ''.join(f'<span class="ctile{" own" if owned(m["sid"], m["form"]) else ""}">{SP.tag(m["sid"], m["form"], size="m")}'
                        f'<small>{E(nm(m["sid"], m["form"]))}</small></span>' for m in t['mons'])
        rows += f'<div class="crow"><span class="ctier">{E(t["tier"])}</span><div class="ctiles">{tiles}</div></div>'
    cards += (f'<article class="ccard"><details><summary><b>List {i["id"]}</b> tiers</summary>'
              f'<div class="cnote">Outlined = you own it</div>{rows}</details></article>')
# 3) every point players make, per Aevian (community.SENT); owned ones also show it on their Dex sheet
OWN = {k[0] for k, r in TA.items() if r.get('owned_as') or r.get('evo')}
def _pts(sid):
    return ''.join(f'<li class="{"pc-up" if v > 0 else "pc-dn" if v < 0 else "pc-nt"}"><b>{"▲" if v > 0 else "▼" if v < 0 else "•"}</b> {E(t)}</li>' for v, t in CM.SENT.get(sid, []))
def _grade(r): return 'S' if r >= .80 else 'A' if r >= .65 else 'B' if r >= .50 else 'C'
later = ''
for sid in sorted([k for k in CM.SENT if k not in OWN and k != 'PARAS' and not (k == 'PARASECT' and 'PARAS' in OWN)],
                  key=lambda k: -(CM.CONS.get(CM._sp(k), {}).get('rating') or 0)):
    rt = CM.CONS.get(CM._sp(sid), {}).get('rating')
    g = _grade(rt) if rt else '?'
    later += (f'<details class="cmon"><summary>{SP.tag(sid, "1", size="s")}<b>{E(nm2(sid))}</b> <span class="tier t{g}">{g}</span></summary>'
              f'<ul class="ds-pc">{_pts(sid)}</ul></details>')
cards += ('<article class="ccard"><h3>Not owned yet</h3><div class="cnote">Saved for when you get them</div>'
          '<div class="cnote">Grade = community rating only (before in-game results)</div>' + later + '</article>')
# 4) consolidated: his Aevians, before -> now (community.py AEVIAN = the blended rating, applied 23 Nov)
BEF = D.get('before', {})
POS = {}
for i in D['inputs']:
    for t in i.get('tiers') or []:
        for m in t['mons']: POS.setdefault((m['sid'], m['form']), {})[i['id']] = t['tier']
out = []; seen = set()
for (sid, form), r in TA.items():
    if not r.get('owned_as') and not r.get('evo'): continue
    lsid, lf = ('PARASECT', '1') if sid == 'PARAS' else (sid, '2' if sid == 'GASTRODON' else form)
    _n = nm('PARASECT', '1') + ' (Paras now)' if sid == 'PARAS' else nm(lsid, lf)
    if _n in seen: continue
    seen.add(_n)
    c = CM.CONS.get(CM._sp(lsid), {})
    b = BEF.get(f'{sid}:{form}', [r['tier'], r['meta']])
    out.append(dict(name=_n, sid=sid, form=form, l1=POS.get((lsid, lf), c.get('lists', {})).get(1, '—'), l2=POS.get((lsid, lf), c.get('lists', {})).get(2, '—'), net=c.get('net', 0),
                    t0=b[0], m0=b[1], t1=r['tier'], m1=r['meta'], rating=c.get('rating')))
RK = {'S': 4, 'A': 3, 'B': 2, 'C': 1, 'D': 0}
rows = ''
for o in sorted(out, key=lambda o: (-RK.get(o['t1'], 0), -o['m1'])):
    mv = RK.get(o['t1'], 0) - RK.get(o['t0'], 0)
    arrow = '<span class="cup">▲</span>' if mv > 0 else '<span class="cdn">▼</span>' if mv < 0 else ''
    talk = (f'<span class="cup">+{o["net"]}</span>' if o['net'] > 0 else f'<span class="cdn">{o["net"]}</span>' if o['net'] < 0 else '0')
    rows += (f'<tr><td>{SP.tag(o["sid"], o["form"], size="s")}{E(o["name"])}</td><td>{E(o["l1"])}</td><td>{E(o["l2"])}</td><td>{talk}</td>'
             f'<td><span class="tier t{o["t0"]}">{o["t0"]}</span></td><td>{arrow}<span class="tier t{o["t1"]}">{o["t1"]}</span></td></tr>')
json.dump(out, open('team/community_consolidated.json', 'w'), indent=1, ensure_ascii=False)
cards += ('<article class="ccard"><h3>Your Aevians: tier before → now</h3>'
          '<table class="ctab"><thead><tr><th>Pokémon</th><th>List 1</th><th>List 2</th><th>Talk</th><th>Before</th><th>Now</th></tr></thead>'
          f'<tbody>{rows}</tbody></table>'
          '<div class="cnote">Community rating = 2/3 both lists + 1/3 older forum posts</div>'
          '<div class="cnote">Talk = net gameplay comments, ±0.02 each (max 0.06)</div>'
          '<div class="cnote">Tier = 63% community rating + in-game results</div>'
          '<div class="cnote">Tap one in the Dex: "What players say" lists every point</div></article>')
css = '''<style id="comm-css">
#scomm ~ .cgrid, .cgrid { display: grid; gap: 14px }
.ccard { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 12px 14px; display: grid; gap: 8px }
.ccard h3 { margin: 0; font-size: 15px }
.cnote { font-size: 12.5px; color: var(--muted) }
.cin { margin: 0; padding-left: 0; list-style: none; display: grid; gap: 8px }
.cin a { color: var(--accent) }
.cst { font-size: 11px; font-weight: 700; padding: 1px 7px; border-radius: 99px; margin: 0 4px }
.cgrid { min-width: 0 } .cgrid > * { min-width: 0; max-width: 100% } .ccard { overflow-wrap: anywhere; box-sizing: border-box }
.cst.ok { background: #1f8a4c; color: #fff } .cst.no { background: #b3261e; color: #fff }
.crow { display: grid; grid-template-columns: 44px 1fr; gap: 8px; align-items: center; border-top: 1px solid var(--line); padding-top: 6px }
.ctier { font-weight: 800; font-size: 14px; text-align: center }
.ctiles { display: flex; flex-wrap: wrap; gap: 6px }
.ctile { display: grid; justify-items: center; width: 70px; padding: 3px; border-radius: 10px; border: 2px solid transparent }
.ctile small { font-size: 10.5px; text-align: center; line-height: 1.15 }
.ctile.own { border-color: var(--accent) }
.cq { margin: 0; padding: 0; list-style: none; display: grid; gap: 8px; font-size: 13px }
.cqh { display: flex; align-items: center; gap: 4px }
.cql { padding-left: 22px; color: var(--muted); font-size: 12.5px }
.ccard summary { cursor: pointer }
.ctab { width: 100%; border-collapse: collapse; font-size: 13px }
.ctab th, .ctab td { text-align: left; padding: 4px 6px; border-top: 1px solid var(--line); vertical-align: middle }
.ctab td:first-child { display: flex; align-items: center; gap: 4px }
.cup { color: #1f8a4c } .cdn { color: #b3261e } .ceq { color: var(--muted) }
.cmon summary { display: flex; align-items: center; gap: 6px; cursor: pointer; padding: 4px 0 }
.ds-pc { list-style: none; padding-left: 0; margin: 4px 0 8px; display: grid; gap: 3px; font-size: 13px } .ds-pc li { display: flex; gap: 6px }
.pc-up b { color: #1f8a4c } .pc-dn b { color: #b3261e } .pc-nt b { color: var(--muted) }
</style>'''
sec = (f'<section aria-labelledby="scomm">\n  <h2 id="scomm">Community</h2>\n{css}<div class="cgrid">{cards}</div>\n</section>\n')
page = open(OUT, encoding='utf-8').read()
page = re.sub(r'<section aria-labelledby="scomm">.*?</section>\s*', '', page, flags=re.S)
anchor = page.find('<section aria-labelledby="s1f">')
page = page[:anchor] + sec + page[anchor:] if anchor >= 0 else page.replace('</main>', sec + '</main>')
open(OUT, 'w', encoding='utf-8').write(page)
print('community tab:', len(D['inputs']), 'inputs,', len(seen), 'owned Aevians compared')
