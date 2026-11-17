"""App theme (Vincent, 17 Nov: "look like an app, Pokémon themed"). Runs LAST in update.py, after tabs.py.
Reskins the generated guide without touching any data: Rotom-Dex style app bar, party slots with level bars, a bottom tab bar
(phone) / side rail (desktop) with 6 tabs (the three tier tabs become one "Dex" tab with a switcher; C&A checks sit behind the
shield icon in the app bar), and the scoring explanations folded into "How this works".
usage (from workspace/): python3 -I ../scripts/team/theme.py <report.html>"""
import html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kits import disp
import current_box as cb
E = html.escape
OUT = sys.argv[1]
page = open(OUT, encoding='utf-8').read()
if 'id="app-theme"' in page:
    sys.exit('already themed')
st = json.load(open('team/state.json'))
CAP, CH = st.get('cap', 60), st.get('chapter', 9)
T = {r['name']: r for r in json.load(open('team/tier_all.json'))['rows']} if os.path.exists('team/tier_all.json') else {}
FP = json.load(open('team/fight_plans.json')) if os.path.exists('team/fight_plans.json') else {}
ROLES = json.load(open('team/team_roles.json')) if os.path.exists('team/team_roles.json') else {}
TYPE = {'NORMAL': '#9a9a7a', 'FIRE': '#e2703a', 'WATER': '#4a86d8', 'ELECTRIC': '#e8bf2a', 'GRASS': '#5aa24a', 'ICE': '#6cc4c4',
        'FIGHTING': '#b23a32', 'POISON': '#9a4aa2', 'GROUND': '#c9a24e', 'FLYING': '#8f8fe0', 'PSYCHIC': '#e2507a', 'BUG': '#98a828',
        'ROCK': '#b0a040', 'GHOST': '#6a5490', 'DRAGON': '#6a3ae8', 'DARK': '#6a5444', 'STEEL': '#9a9ab4', 'FAIRY': '#dc8ab0'}
FIGHT_NAME = {'darkgardevoir': 'Dark Gardevoir', 'garbodor': 'Rift Garbodor', 'karrina': 'Karrina', 'spector': 'Spector (day)',
              'spector2': 'Spector (night)', 'jenner9': 'Spirit Jenner', 'amanda': 'Amanda', 'erick': 'Erick'}

# ---------------------------------------------------------------- party slots (Team tab hero)
party = {d['species']: d for d in cb.parse(st['export'])[:6]}
core = set(st.get('core') or [])
slots = ''
for i, nm in enumerate(st['team']):
    d = disp(nm); r = T.get(nm, {}); p = party.get(d) or {}
    lv = p.get('level') or 0
    types = ''.join(f'<span class="pt" style="--tc:{TYPE.get(t, "#888")}">{E(t.title())}</span>' for t in r.get('types', []))
    tag = 'Core' if nm in core else 'Swap'
    role = (ROLES.get(d) or '').title()
    here = '' if p else '<span class="slot-miss">not in party</span>'
    slots += (f'<li class="slot{" is-core" if nm in core else ""}"><div class="slot-top"><span class="slot-n">{i + 1}</span>'
              f'<span class="slot-tag">{tag}{" · " + E(role) if role else ""}</span></div>'
              f'<b class="slot-name">{E(d)}</b><div class="slot-types">{types}</div>'
              f'<div class="slot-lv"><span>Lv {lv or "?"}</span><span class="lv-bar" role="img" aria-label="Level {lv} of {CAP}">'
              f'<i style="width:{min(100, round(100 * lv / CAP)) if lv else 0}%"></i></span><span class="lv-cap">{CAP}</span></div>'
              f'<div class="slot-sub">{E(p.get("item") or "no item")}{here}</div></li>')
nxt = ''
if st.get('fight') and st['fight'] in FP:
    p = FP[st['fight']]
    nxt = (f'<a class="next" href="#fights" data-go="fights"><span class="next-k">Next battle</span>'
           f'<b>{E(FIGHT_NAME.get(st["fight"], st["fight"]))}</b><span>{E(p["format"])} · lead {E(" + ".join(disp(x) for x in p["leads"]))}'
           f' · {p["counters"]}/{p["n"]} countered</span><span class="next-go" aria-hidden="true">›</span></a>')
low = sum(1 for nm in st['team'] if (party.get(disp(nm)) or {}).get('level', CAP) < CAP)
hero = (f'<div class="hero"><div class="hero-head"><h3>Your party</h3><span class="legend">Core of 4 stays all chapter · 2 swaps per fight'
        f'{" · " + str(low) + " to level up" if low else ""}</span></div><ol class="party">{slots}</ol>{nxt}</div>')
page = re.sub(r'(<section aria-labelledby="s1">\s*<h2 id="s1">.*?</h2>)', lambda m: m.group(1) + hero, page, count=1, flags=re.S)

page = re.sub(r'<div class="panel pad lvl">.*?</div>\s*', '', page, count=1, flags=re.S)   # the party slots show levels now

# ---------------------------------------------------------------- fold scoring explanations ("How this works")
def fold(m):
    return f'{m.group(1)}<details class="how"><summary>How this works</summary>{m.group(2)}</details>'
page = re.sub(r'(<h2 id="\w+">.*?</h2>\s*)(<ul class="legend">.*?</ul>)', fold, page, flags=re.S)
page = re.sub(r'(<h2 id="\w+">.*?</h2>\s*)(<p class="legend">.*?</p>)', fold, page, flags=re.S)

# ---------------------------------------------------------------- app bar
facts = re.search(r'<div class="facts">(.*?)</div>', page, re.S)
chips = re.sub(r'<span>(.*?)</span>', r'<span class="chip">\1</span>', facts.group(1)) if facts else ''
BALL = ('<svg class="ball" viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="14" fill="#fff"/>'
        '<path d="M2 16a14 14 0 0 1 28 0z" fill="var(--ball)"/><circle cx="16" cy="16" r="14" fill="none" stroke="#1d1d24" stroke-width="2.4"/>'
        '<path d="M2 16h28" stroke="#1d1d24" stroke-width="2.4"/><circle cx="16" cy="16" r="4.6" fill="#fff" stroke="#1d1d24" stroke-width="2.4"/></svg>')
SHIELD = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l8 3v6c0 4.5-3.4 8.1-8 9-4.6-.9-8-4.5-8-9V6z" fill="none" stroke="currentColor" '
          'stroke-width="2" stroke-linejoin="round"/><path d="M8.5 12l2.5 2.5 4.5-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>')
bar = (f'<header class="appbar"><div class="appbar-in"><div class="brand">{BALL}<div><b>Rejuv Dex</b>'
       f'<span>Chapter {CH} · Classic · Lv cap {CAP}</span></div></div>'
       f'<div class="appbar-chips">{chips}</div>'
       f'<button type="button" class="iconbtn" id="go-checks" aria-label="Checks and data sources" title="Checks and data sources">{SHIELD}</button>'
       f'</div><h1 class="viewtitle" id="viewtitle">Team</h1></header>')
page = re.sub(r'<header class="mast">.*?</header>', bar, page, count=1, flags=re.S)

# ---------------------------------------------------------------- navigation (6 tabs; the 3 tier tabs = Dex)
IC = {
 'team': '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17"/><circle cx="12" cy="12" r="2.6"/>',
 'fights': '<path d="M4 20l7-7M14 4h6v6L9 21l-3-3z"/><path d="M4 14l6 6"/>',
 'cores': '<rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/>',
 'todo': '<path d="M9 6h11M9 12h11M9 18h11"/><path d="M3.5 6l1.5 1.5L7.5 5M3.5 12l1.5 1.5L7.5 11M3.5 18l1.5 1.5L7.5 17"/>',
 'boxes': '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18M9 5v14M15 5v14"/>',
 'dex': '<rect x="5" y="3" width="14" height="18" rx="2"/><circle cx="12" cy="9" r="3"/><path d="M8.5 15h7M8.5 18h4"/>'}
NAV = [('team', 'Team'), ('fights', 'Fights'), ('cores', 'Cores'), ('todo', 'To do'), ('boxes', 'Boxes'), ('dex', 'Dex')]
nav = '<nav class="appnav" aria-label="Guide">' + ''.join(
    f'<button type="button" data-go="{k}"><svg viewBox="0 0 24 24" aria-hidden="true">{IC[k]}</svg><span>{t}</span></button>' for k, t in NAV) + '</nav>'
seg = ('<div class="seg" role="group" aria-label="Dex lists"><button type="button" data-go="tiers">Pokémon</button>'
       '<button type="button" data-go="aevian">Aevian</button><button type="button" data-go="crests">Crests</button></div>')
page = re.sub(r'(<div class="tabp" id="panel-(tiers|aevian|crests)"[^>]*>)', lambda m: m.group(1) + seg, page)
page = page.replace('</header>', '</header>' + nav, 1)

FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700'
         '&family=Nunito+Sans:opsz,wght@6..12,400;6..12,600;6..12,700;6..12,800&family=IBM+Plex+Mono:wght@400;500&display=swap">')
page = re.sub(r'<link rel="stylesheet" href="https://fonts.googleapis.com/css2[^"]*">', FONTS, page, count=1)

CSS = r'''<style id="app-theme">
/* Layout: a Rotom-Dex style app. Red app bar + party slots on top, one screen per tab, bottom tab bar on phones, side rail on desktop. */
:root {
  --dex: #d4253b; --dex-deep: #a3162a; --ball: #d4253b; --on-dex: #fff8f6;
  --bg: #edf1f4; --panel: #ffffff; --panel-2: #f6f8fa; --ink: #18202a; --muted: #5c6875; --line: #dbe2e8;
  --accent: #c81f36; --accent-soft: #fde6e8; --link: #1f64c4;
  --good: #1f8a4c; --good-soft: #e0f4e8; --warn: #a86400; --warn-soft: #fcf0da; --bad: #c4231d; --bad-soft: #fde4e2;
  --tS: #d4253b; --tA: #e07b19; --tB: #2f7fd1; --tC: #3d9a5b; --tD: #7a8794;
  --lv: #3ec26b; --shadow: 0 1px 2px rgba(24,32,42,.06), 0 6px 18px rgba(24,32,42,.06);
  --display: "Chakra Petch", "Arial Narrow", system-ui, sans-serif;
  --body: "Nunito Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
  --rail: 0px; --navh: 64px;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --dex: #b81d32; --dex-deep: #7e1222; --ball: #e2384d; --on-dex: #fff4f2;
  --bg: #0f1419; --panel: #182029; --panel-2: #1d2731; --ink: #e8eef3; --muted: #97a6b4; --line: #2a3643;
  --accent: #ff5a6e; --accent-soft: #3a1820; --link: #79b0ff;
  --good: #5fd38d; --good-soft: #15301f; --warn: #f2b65a; --warn-soft: #3a2b12; --bad: #ff8a80; --bad-soft: #3d1a18;
  --tS: #ff5a6e; --tA: #f6a04a; --tB: #6aaaf0; --tC: #6fcb8c; --tD: #9aa8b5; --lv: #4fd47e;
  --shadow: 0 1px 2px rgba(0,0,0,.3), 0 8px 22px rgba(0,0,0,.25); color-scheme: dark } }
:root[data-theme="dark"] {
  --dex: #b81d32; --dex-deep: #7e1222; --ball: #e2384d; --on-dex: #fff4f2;
  --bg: #0f1419; --panel: #182029; --panel-2: #1d2731; --ink: #e8eef3; --muted: #97a6b4; --line: #2a3643;
  --accent: #ff5a6e; --accent-soft: #3a1820; --link: #79b0ff;
  --good: #5fd38d; --good-soft: #15301f; --warn: #f2b65a; --warn-soft: #3a2b12; --bad: #ff8a80; --bad-soft: #3d1a18;
  --tS: #ff5a6e; --tA: #f6a04a; --tB: #6aaaf0; --tC: #6fcb8c; --tD: #9aa8b5; --lv: #4fd47e;
  --shadow: 0 1px 2px rgba(0,0,0,.3), 0 8px 22px rgba(0,0,0,.25); color-scheme: dark }
body { background: var(--bg); color: var(--ink); font: 15px/1.5 var(--body); padding-bottom: calc(var(--navh) + env(safe-area-inset-bottom, 0px) + 12px) }
body::before { content: ""; position: fixed; inset: 0 0 auto; height: env(safe-area-inset-top, 0px); z-index: 30; background: var(--dex) }
a { color: var(--link) }
.wrap { max-width: none; padding-block: 0 24px; gap: 0; padding-left: 0; padding-right: 0 }
.wrap > *:not(.appbar):not(.appnav):not(#tabbar) { margin-left: auto; margin-right: auto }
#tabbar { display: none !important }
.tabp { max-width: 1120px; margin: 0 auto; width: 100%; padding: 18px max(16px, env(safe-area-inset-right, 0px)) 8px max(16px, env(safe-area-inset-left, 0px)); gap: 22px }
/* app bar */
.appbar { position: sticky; top: env(safe-area-inset-top, 0px); z-index: 20; background: linear-gradient(180deg, var(--dex), var(--dex-deep)); color: var(--on-dex);
  box-shadow: 0 2px 0 rgba(0,0,0,.12); padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)) }
.appbar-in { max-width: 1120px; margin: 0 auto; display: flex; align-items: center; gap: 14px; padding-block: 10px 4px }
.brand { display: flex; align-items: center; gap: 10px; min-width: 0 }
.brand b { font: 700 19px/1 var(--display); letter-spacing: .02em; display: block }
.brand span { font: 500 11.5px var(--mono); opacity: .85; letter-spacing: .04em }
.ball { width: 34px; height: 34px; flex: none; --ball: #ff6b7c; filter: drop-shadow(0 1px 0 rgba(0,0,0,.25)) }
.appbar-chips { display: flex; gap: 6px; flex-wrap: wrap; margin-left: auto; justify-content: flex-end }
.appbar .chip { background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.22); border-radius: 99px; padding: 2px 10px; font: 500 12px var(--mono); white-space: nowrap }
.appbar .chip b { color: var(--on-dex); font-weight: 600 }
.iconbtn { flex: none; width: 38px; height: 38px; border-radius: 12px; border: 1px solid rgba(255,255,255,.3); background: rgba(255,255,255,.12); color: var(--on-dex); cursor: pointer; display: grid; place-items: center }
.iconbtn svg { width: 20px; height: 20px }
.iconbtn[aria-pressed="true"] { background: var(--on-dex); color: var(--dex-deep) }
.viewtitle { max-width: 1120px; margin: 0 auto; font: 700 24px/1.1 var(--display); padding-block: 2px 12px; letter-spacing: .01em }
@media (max-width: 720px) { .appbar-chips { display: none } .viewtitle { font-size: 21px } }
/* navigation: bottom bar (phone), side rail (desktop) */
.appnav { position: fixed; z-index: 25; left: 0; right: 0; bottom: 0; display: grid; grid-template-columns: repeat(6, 1fr);
  background: var(--panel); border-top: 1px solid var(--line); box-shadow: 0 -4px 16px rgba(0,0,0,.06);
  padding: 6px max(6px, env(safe-area-inset-right, 0px)) calc(6px + env(safe-area-inset-bottom, 0px)) max(6px, env(safe-area-inset-left, 0px)) }
.appnav button { display: grid; justify-items: center; gap: 2px; border: 0; background: none; color: var(--muted); font: 700 11px var(--body); padding: 6px 0; border-radius: 12px; cursor: pointer }
.appnav svg { width: 24px; height: 24px; fill: none; stroke: currentColor; stroke-width: 1.9; stroke-linecap: round; stroke-linejoin: round }
.appnav button[aria-current="page"] { color: var(--accent); background: var(--accent-soft) }
.appnav button:focus-visible, .seg button:focus-visible, .iconbtn:focus-visible, .next:focus-visible { outline: 2px solid var(--link); outline-offset: 2px }
@media (min-width: 980px) {
  :root { --rail: 92px }
  body { padding-bottom: 0; padding-left: var(--rail) }
  .appnav { top: 0; right: auto; bottom: 0; width: var(--rail); grid-template-columns: 1fr; align-content: start; gap: 6px; padding: calc(env(safe-area-inset-top, 0px) + 86px) 10px 16px max(10px, env(safe-area-inset-left, 0px));
    border-top: 0; border-right: 1px solid var(--line); box-shadow: none }
  .appnav button { padding: 10px 0 8px }
}
/* Dex switcher */
.seg { display: inline-flex; gap: 4px; padding: 4px; background: var(--panel); border: 1px solid var(--line); border-radius: 14px; justify-self: start; box-shadow: var(--shadow) }
.seg button { border: 0; background: none; font: 700 13.5px var(--body); color: var(--muted); padding: 7px 16px; border-radius: 10px; cursor: pointer }
.seg button[aria-pressed="true"] { background: var(--accent); color: #fff }
/* page sections */
section > h2 { display: none }
section { gap: 16px }
h3 { font: 700 16.5px/1.25 var(--display); letter-spacing: .01em }
.panel { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; box-shadow: var(--shadow) }
.panel.pad, .panel > .pad { padding: 16px 18px }
.legend { color: var(--muted) }
details.how { background: var(--panel-2); border: 1px dashed var(--line); border-radius: 12px; padding: 8px 14px; font-size: 13.5px }
details.how > summary { cursor: pointer; font: 700 13px var(--body); color: var(--muted); list-style: none }
details.how > summary::before { content: "i"; display: inline-grid; place-items: center; width: 18px; height: 18px; margin-right: 8px; border-radius: 50%;
  background: var(--muted); color: var(--panel); font: 700 11px var(--mono) }
details.how[open] > summary { margin-bottom: 6px }
table { font-size: 14px }
thead th { background: var(--panel-2); color: var(--muted); font: 600 11px var(--mono); letter-spacing: .08em }
tbody tr:hover td { background: color-mix(in srgb, var(--accent-soft) 45%, transparent) }
.tier { display: inline-grid !important; place-items: center; min-width: 26px; height: 26px; padding: 0 6px; border-radius: 8px; color: #fff !important; font: 700 14px var(--display) !important; margin-right: 8px }
.tS { background: var(--tS) !important } .tA { background: var(--tA) !important } .tB { background: var(--tB) !important } .tC { background: var(--tC) !important } .tD { background: var(--tD) !important }
.ok { color: var(--good) } .warn { color: var(--warn) } .bad { color: var(--bad) }
/* party hero */
.hero { display: grid; gap: 12px }
.hero-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 12px }
.party { list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; grid-template-columns: repeat(3, minmax(0, 1fr)) }
@media (max-width: 860px) { .party { grid-template-columns: repeat(2, minmax(0, 1fr)) } }
.slot { position: relative; background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 12px 14px 12px; display: grid; gap: 6px; box-shadow: var(--shadow); min-width: 0; overflow: hidden }
.slot::after { content: ""; position: absolute; right: -26px; top: -26px; width: 84px; height: 84px; border-radius: 50%; border: 10px solid var(--line); opacity: .55 }
.slot.is-core { border-color: color-mix(in srgb, var(--accent) 40%, var(--line)) }
.slot-top { display: flex; align-items: center; gap: 8px; position: relative; z-index: 1 }
.slot-n { display: grid; place-items: center; width: 22px; height: 22px; border-radius: 50%; background: var(--ink); color: var(--panel); font: 700 12px var(--mono) }
.slot-tag { font: 600 11px var(--mono); letter-spacing: .06em; text-transform: uppercase; color: var(--muted) }
.is-core .slot-tag { color: var(--accent) }
.slot-name { font: 700 17px/1.15 var(--display); overflow-wrap: anywhere; position: relative; z-index: 1 }
.slot-types { display: flex; gap: 4px; flex-wrap: wrap }
.pt { background: var(--tc); color: #fff; font: 700 10.5px var(--body); letter-spacing: .04em; text-transform: uppercase; padding: 1px 8px; border-radius: 99px; text-shadow: 0 1px 0 rgba(0,0,0,.25) }
.slot-lv { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 8px; font: 600 12px var(--mono); font-variant-numeric: tabular-nums }
.lv-bar { height: 7px; border-radius: 99px; background: var(--panel-2); border: 1px solid var(--line); overflow: hidden }
.lv-bar i { display: block; height: 100%; background: var(--lv); border-radius: 99px }
.lv-cap { color: var(--muted) }
.slot-sub { font-size: 12.5px; color: var(--muted); display: flex; gap: 8px; flex-wrap: wrap }
.slot-miss { color: var(--warn); font-weight: 700 }
.next { display: grid; grid-template-columns: 1fr auto; grid-template-areas: "k go" "t go" "s go"; gap: 2px 12px; text-decoration: none; color: var(--on-dex);
  background: linear-gradient(120deg, var(--dex-deep), var(--dex)); border-radius: 16px; padding: 14px 18px; box-shadow: var(--shadow) }
.next-k { grid-area: k; font: 600 11px var(--mono); letter-spacing: .1em; text-transform: uppercase; opacity: .85 }
.next b { grid-area: t; font: 700 20px var(--display) }
.next > span:nth-of-type(2) { grid-area: s; font-size: 13.5px; opacity: .92 }
.next-go { grid-area: go; align-self: center; font: 700 28px var(--display) }
@media (prefers-reduced-motion: no-preference) { .tabp:not([hidden]) { animation: rise .22s ease-out } @keyframes rise { from { transform: translateY(6px); opacity: .6 } to { transform: none; opacity: 1 } } }
.tier { width: auto !important; max-width: 44px; flex: none; justify-self: start }
@media (max-width: 680px) {
  .cft thead, .fplan thead { display: none }
  .cft, .cft tbody, .cft tr, .cft td, .fplan, .fplan tbody, .fplan tr, .fplan td { display: block; width: 100% }
  .cft tr, .fplan tr { padding: 10px 0; border-bottom: 1px solid var(--line) }
  .cft td, .fplan td { border: 0 !important; padding: 2px 0 }
  .cft td:first-child, .fplan td:first-child { font-size: 15.5px }
}
footer { max-width: 1120px; margin: 0 auto; padding: 0 max(16px, env(safe-area-inset-right, 0px)) 0 max(16px, env(safe-area-inset-left, 0px)) }
</style>'''
JS = r'''<script id="app-theme-js">
(function(){
  var NAMES = {team:'Team', fights:'Fights', cores:'Cores', todo:'To do', boxes:'Boxes', tiers:'Dex · Pokémon', aevian:'Dex · Aevian', crests:'Dex · Crests', checks:'Checks & data'};
  var DEX = {tiers:1, aevian:1, crests:1};
  var orig = function(k){ return document.querySelector('#tabbar button[data-tab="'+k+'"]'); };
  function current(){ var b = document.querySelector('#tabbar button[aria-selected="true"]'); return b ? b.dataset.tab : 'team'; }
  function paint(){
    var k = current(), top = DEX[k] ? 'dex' : k;
    document.querySelectorAll('.appnav button').forEach(function(b){ if (b.dataset.go === top) b.setAttribute('aria-current','page'); else b.removeAttribute('aria-current'); });
    document.querySelectorAll('.seg button').forEach(function(b){ b.setAttribute('aria-pressed', b.dataset.go === k ? 'true' : 'false'); });
    var c = document.getElementById('go-checks'); if (c) c.setAttribute('aria-pressed', k === 'checks' ? 'true' : 'false');
    var t = document.getElementById('viewtitle'); if (t) t.textContent = NAMES[k] || k;
  }
  function go(k){
    if (k === 'dex') { var last = 'tiers'; try { last = localStorage.getItem('dex-last') || 'tiers'; } catch(e) {} k = last; }
    if (DEX[k]) { try { localStorage.setItem('dex-last', k); } catch(e) {} }
    var b = orig(k); if (b) b.click(); paint();
  }
  document.addEventListener('click', function(e){
    var el = e.target.closest('[data-go]'); if (!el) return;
    e.preventDefault(); go(el.dataset.go);
  });
  var cb = document.getElementById('go-checks');
  if (cb) cb.addEventListener('click', function(){ go(current() === 'checks' ? 'team' : 'checks'); });
  window.addEventListener('hashchange', paint);
  paint();
})();
</script>'''
_i = page.rfind('</style>') + len('</style>')   # after every generated style block, so the theme wins the cascade
page = page[:_i] + '\n' + CSS + page[_i:]
page = page.replace('</body>', JS + '\n</body>') if '</body>' in page else page + '\n' + JS
open(OUT, 'w', encoding='utf-8').write(page)
print('theme: party slots', len(st['team']), '· nav', [k for k, _ in NAV])
