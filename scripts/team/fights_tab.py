"""Fights tab (Vincent, 25 Nov; pilot for Chapter 10): every fight of the chapter is a FOLDED card, a green check on the ones he beat.
Opened, an upcoming fight shows everything the team build needs: format, field, ALL field effects (the game's own field notes), their
Pokémon with level / types / ability / item / nature / EVs / stats / moves, and a 'Guide tips' area (team/fight_tips.json: tips from the
walkthrough or from him, with who on the recommended six covers each; they score in the planner's pick). Completed fights stay light
(format, field, their team). Called by theme.py: html(st, names) -> section body."""
import html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gamedata'))
import sprites as SP
import bosses, engine
import gamedata as G
import field_notes as FN
from fields import GUIDE_TO_FE
from kits import disp
E = html.escape
STATS = ['HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe']


def _pill(t): return f'<span class="tp ty-{t.lower()}">{t.title()}</span>'


def _stats(st_, spe_here=None):
    return ('<div class="mu-st">' + ''.join(f'<span><small>{x}</small><b>{st_.get(x, "?")}</b></span>' for x in STATS)
            + (f'<span class="mu-sh"><small>Speed here</small><b>{int(spe_here)}</b></span>' if spe_here and int(spe_here) != st_.get('Spe') else '') + '</div>')


def _foes(k, P):
    """their team: the planner's detail for the next fight (Mega forms, field Speed), else computed from the game data"""
    if P.get('fight') == k and P.get('foe_detail'):
        return [dict(f, sprite=SP.tag(f.get('sid') or '', '0', size='m')) for f in P['foe_detail']]
    out = []
    for f in G.fight_mons(k):
        bs = dict(zip(STATS, f.get('base') or [0] * 6)); ev = dict(zip(STATS, f.get('ev') or [0] * 6))
        try: stt = engine.calc_stats(bs, ev, (f.get('nature') or 'Hardy').title(), int(f.get('level') or 50), iv=int(f.get('iv') or 31))
        except Exception: stt = {}
        out.append(dict(name=f['name'], level=f.get('level'), types=f.get('types') or [], ability=f.get('ability'), item=f.get('item'),
                        nature=f.get('nature'), evs=' / '.join(f'{v} {s}' for s, v in zip(STATS, f.get('ev') or []) if v), stats=stt,
                        moves=f.get('moves') or [], mega=bool((f.get('item') or '').endswith('ite') and f.get('item') != 'Eviolite'),
                        shields=f.get('shields'), sprite=SP.tag(f.get('species') or '', '0', size='m')))
    return out


def _zmove(f):   # a species Z-Crystal: the AI uses its Z-move (Battle_AI checkZMoves)
    if not re.search(r'ium Z$', f.get('item') or ''): return ''
    ids = {re.sub(r'[^A-Z]', '', m.upper()) for m in f.get('moves') or []}
    z = [d.get('longname') or d.get('name') for d in FN.MV.values() if (d.get('zmovedata') or {}).get('basemove') in ids]
    return f'<li><b>Z-move</b> {E(", ".join(z))}</li>' if z else ''


def _field_html(field):
    fe = GUIDE_TO_FE.get(field)
    if not fe: return '<div class="pmuted">No field effect</div>'
    ns = FN.notes(fe)
    return (f'<ul class="fnl">' + ''.join(
        f'<li><div class="fn-t">{FN.to_html(n["title"])}' + (f'<span class="fn-stage">{E(n["stage"])}</span>' if n.get('stage') else '') + '</div>'
        + (f'<div class="fn-x">{FN.to_html(n["text"])}</div>' if n.get('text') else '') + '</li>' for n in ns) + '</ul>')


def _tips_html(k, P, TIPS):
    tips = TIPS.get(k) or []
    met = {t['tip']: t for t in (P.get('tips') or [])} if P.get('fight') == k else {}
    six = [m['name'] for m in P.get('six') or []] if P.get('fight') == k else []
    out = ''
    for t in tips:
        m_ = met.get(t['tip']) or {}
        who = sorted({disp(w) for nd in m_.get('needs') or [] for w in (nd.get('met_by') or []) if not six or w in six}) if m_ else []
        out += (f'<li class="{"tip-ok" if who else "tip-no"}"><b>{"✓" if who else "•"}</b> {E(t["tip"])}'
                + (f'<small>{E(t.get("src") or "")}</small>' if t.get('src') else '') + (f'<div class="tip-who">Covered by {E(", ".join(who))}</div>' if who else '') + '</li>')
    if not out:
        out = '<li class="tip-no"><b>•</b> No guide tips yet. Send me the walkthrough page or your notes for this fight: they go here and score in the team pick.</li>'
    return f'<ul class="tipl">{out}</ul>'


def html_(st, names):
    P = json.load(open('team/planner.json')) if os.path.exists('team/planner.json') else {}
    TIPS = json.load(open('team/fight_tips.json')) if os.path.exists('team/fight_tips.json') else {}
    done = set(st.get('done') or [])
    nxt = st.get('fight')
    cards = ''
    for i, (k, label, field, fmt, _w, note) in enumerate(bosses.CH9):
        is_done = k in done
        try: foes = _foes(k, P)
        except Exception: foes = []
        name = names.get(k, label.split(' – ')[0])
        ace = foes[-1]['sprite'] if foes else ''
        head = (f'<summary class="fx-sum">{ace}<span class="fx-t"><b>{E(name)}</b><span class="fchips"><span class="fchip">{E(fmt)}</span>'
                f'<span class="fchip">{E(field)}</span>' + ('<span class="fchip boss">Boss</span>' if '(boss)' in label else '') + '</span></span>'
                + ('<span class="fx-done" title="Beaten">✓</span>' if is_done else '<span class="fx-next">Next</span>' if k == nxt else '') + '</summary>')
        team_row = '<ol class="fx-team">' + ''.join(f'<li>{f["sprite"]}<span>{E(f["name"])}</span></li>' for f in foes) + '</ol>'
        if is_done:   # light: what it was, nothing more
            body = f'<div class="fx-body"><div class="psub">Their team</div>{team_row}<div class="pmuted">{E(note)}</div></div>'
        else:
            fl = ''.join(
                f'<li class="fx-foe"><div class="mu-h">{f["sprite"]}<b>{E(f["name"])}</b><span class="pchip">Lv {E(str(f.get("level") or ""))}</span>'
                + ('<span class="pchip">Mega</span>' if f.get('mega') else '') + (f'<span class="pchip">{f["shields"]} shields</span>' if f.get('shields') else '') + '</div>'
                + '<div class="ctr-types">' + ''.join(_pill(t) for t in f.get('types') or []) + '</div>'
                + f'<ul class="ctr-b"><li><b>Ability</b> {E(f.get("ability") or "")}</li><li><b>Item</b> {E(f.get("item") or "none")}</li>'
                + f'<li><b>Nature</b> {E((f.get("nature") or "").title())}</li><li><b>EVs</b> {E(f.get("evs") or "")}</li>' + _zmove(f) + '</ul>'
                + _stats(f.get('stats') or {}, f.get('spe_field'))
                + '<div class="ctr-mv">' + ''.join(f'<span>{E(x)}</span>' for x in f.get('moves') or []) + '</div></li>' for f in foes)
            body = (f'<div class="fx-body"><div class="fx-meta"><span><b>Format</b> {E(fmt)}</span><span><b>Field</b> {E(field)}</span></div>'
                    f'<div class="pmuted">{E(note)}</div>'
                    f'<details class="fx-sub"><summary>Field effects: {E(field)}</summary>{_field_html(field)}</details>'
                    f'<details class="fx-sub" open><summary>Their team</summary><ul class="fx-foes">{fl}</ul></details>'
                    f'<details class="fx-sub" open><summary>Guide tips</summary>{_tips_html(k, P, TIPS)}</details></div>')
        cards += f'<details class="fx{" fx-isdone" if is_done else ""}{" fx-isnext" if k == nxt else ""}">{head}{body}</details>'
    css = '''<style id="fx-css">.fxl { display: grid; gap: 10px }
.fx { border-radius: 14px; background: var(--panel); box-shadow: 0 1px 2px rgba(0,0,0,.08) } .fx-isnext { box-shadow: inset 0 0 0 2px var(--accent) }
.fx-sum { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 8px; padding: 10px; cursor: pointer; list-style: none }
.fx-sum::-webkit-details-marker { display: none } .fx-t { display: grid; gap: 3px; min-width: 0 } .fchips { display: flex; flex-wrap: wrap; gap: 4px }
.fx-done { width: 26px; height: 26px; border-radius: 50%; background: #1f8a4c; color: #fff; display: grid; place-items: center; font-weight: 800 }
.fx-next { font: 800 11px var(--body); color: var(--accent); text-transform: uppercase }
.fx-body { display: grid; gap: 8px; padding: 0 10px 12px; min-width: 0 } .fx-meta { display: flex; flex-wrap: wrap; gap: 12px; font-size: 13px } .fx-meta b { color: var(--muted); font-weight: 600 }
.fx-sub > summary { cursor: pointer; font-weight: 700; padding: 4px 0 } .fx-team { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 12.5px }
.fx-team li { display: flex; align-items: center; gap: 4px } .fx-foes { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px }
.fx-foe { display: grid; gap: 5px; padding: 8px; border-radius: 10px; background: var(--panel-2); min-width: 0 }
.tipl { list-style: none; margin: 0; padding: 0; display: grid; gap: 5px; font-size: 13px } .tipl li { padding: 6px 8px; border-radius: 8px; background: var(--panel-2) }
.tipl small { display: block; color: var(--muted) } .tip-ok b { color: #1f8a4c } .tip-who { font-size: 11.5px; font-weight: 700; color: #1f8a4c }
@media (min-width: 720px) { .fx-foes { grid-template-columns: 1fr 1fr } }
</style>'''
    return css + f'<div class="fxl">{cards}</div>'
