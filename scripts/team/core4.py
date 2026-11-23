"""Best CORE 4 (Vincent, 23 Nov): the strongest general four in his boxes, no opponent, no roles. Flexes (2 per fight) come later.
Pool = Party + Active + S / A in Overflow. Core score (shown on the Builder tab, 'How the core is picked'):
  STRENGTH  sum of the four tier scores (tier_all blend = 0.7 x meta / community + BST, 0.3 x in-game results across every fight) x 10
  DEFENSE   18 attacking types: -2 per type 2+ of the four are weak to and none resists, -4 per type 3+ are weak to, +0.3 per type resisted
  OFFENSE   +0.25 per defending type the four hit super effectively with the moves their builds run
  SYNERGY   physical + special mix, fast + slow split, redirection / sleep / Intimidate / speed control with partners, -1 per spread move
            that hits a teammate super effectively, + Aevian tiebreak (+0.3 each)
usage (from workspace/): python3 -I ../scripts/team/core4.py <report.html>   -> team/core4.json + Builder tab section 'sbuild'"""
import html, itertools, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('MOVE_RULES', 'relearn')
import engine
import sprites as SP
from kits import disp
from cues import cues
E_ = html.escape
OUT = sys.argv[1] if len(sys.argv) > 1 else None
st = json.load(open('team/state.json'))
E = engine.Engine(os.path.abspath('.'))
MV = json.load(open('gamedata/movetext.json')); BYNAME = {v['name'].lower(): k for k, v in MV.items()}
TA = {r['name']: r for r in json.load(open('team/tier_all.json'))['rows'] if r.get('kind') != 'crest' and r.get('owned_as')}
IB = json.load(open('team/ideal_builds.json')) if os.path.exists('team/ideal_builds.json') else {}
TYPES = ['NORMAL', 'FIRE', 'WATER', 'ELECTRIC', 'GRASS', 'ICE', 'FIGHTING', 'POISON', 'GROUND', 'FLYING', 'PSYCHIC', 'BUG', 'ROCK', 'GHOST',
         'DRAGON', 'DARK', 'STEEL', 'FAIRY']
RK = {'S': 4, 'A': 3, 'B': 2, 'C': 1, 'D': 0}
POOL = [n for n, r in TA.items() if (r.get('where') in ('Party', 'Active') and r['tier'] in ('S', 'A', 'B')) or (r.get('where') == 'Overflow' and r['tier'] in ('S', 'A'))]
POOL = sorted(POOL, key=lambda n: -TA[n]['blend'])[:26]   # the strongest 26 by tier score
def mvid(n): return BYNAME.get((n or '').lower())
def build(n):
    b = IB.get(n) or {}
    ms = (st.get('moves') or {}).get(n) or b.get('moves') or TA[n].get('attacks') or []
    ab = ((st.get('abilities') or {}).get(n) or b.get('ability') or TA[n].get('ability') or '').upper().replace(' ', '')
    return [mvid(m) or m.upper().replace(' ', '') for m in ms], ab, ms
ABSORB = {'FLASHFIRE': 'FIRE', 'WATERABSORB': 'WATER', 'STORMDRAIN': 'WATER', 'DRYSKIN': 'WATER', 'VOLTABSORB': 'ELECTRIC', 'LIGHTNINGROD': 'ELECTRIC',
          'MOTORDRIVE': 'ELECTRIC', 'SAPSIPPER': 'GRASS', 'LEVITATE': 'GROUND', 'EARTHEATER': 'GROUND', 'WELLBAKEDBODY': 'FIRE'}
DEF, OFFT, INFO, PRIO = {}, {}, {}, {}
for n in POOL:
    ms, ab, mnames = build(n)
    DEF[n] = {t: (0 if ABSORB.get(ab) == t else E.chart_eff(t, TA[n]['types'])) for t in TYPES}
    hit = set()
    cats = set()
    for m in ms:
        d = MV.get(m) or {}
        if int(d.get('basedamage') or 0) <= 0: continue
        cats.add((d.get('category') or '').lower())
        for t in TYPES:
            if E.chart_eff(d.get('type'), [t]) >= 2: hit.add(t)
    OFFT[n] = hit
    PRIO[n] = any(int((MV.get(m) or {}).get('priority') or 0) > 0 and int((MV.get(m) or {}).get('basedamage') or 0) > 0 and m != 'FAKEOUT' for m in ms)
    INFO[n] = dict(ms=set(ms), ab=ab, mnames=mnames, cats=cats, spe=TA[n]['base']['Spe'], natk=sum(int((MV.get(m) or {}).get('basedamage') or 0) > 0 for m in ms),
                   spread=[m for m in ms if (MV.get(m) or {}).get('target') == 'AllNonUsers' and int((MV.get(m) or {}).get('basedamage') or 0) > 0])
N = int(st.get('core_n') or 3)   # 23 Nov (Vincent): core of 3 + 3 flexes (Rejuvenation community mindset)
PIVOTM = {'UTURN', 'VOLTSWITCH', 'FLIPTURN', 'PARTINGSHOT', 'TELEPORT', 'CHILLYRECEPTION', 'SHEDTAIL'}
RECOV = {'RECOVER', 'ROOST', 'SLACKOFF', 'SOFTBOILED', 'MOONLIGHT', 'SYNTHESIS', 'MORNINGSUN', 'WISH', 'SHOREUP', 'STRENGTHSAP', 'MILKDRINK'}
DISRUPT_S = {'ENCORE', 'YAWN', 'WILLOWISP', 'TAUNT', 'THUNDERWAVE', 'GLARE', 'TOXIC', 'KNOCKOFF', 'HAZE', 'CLEARSMOG', 'SPORE', 'LOVELYKISS'}
FIELDDEP = {'SWIFTSWIM', 'CHLOROPHYLL', 'SANDRUSH', 'SLUSHRUSH', 'SOLARPOWER', 'SURGESURFER', 'SANDFORCE', 'RAINDISH', 'ICEBODY', 'LEAFGUARD',
            'HYDRATION', 'FLOWERGIFT', 'PROTOSYNTHESIS', 'QUARKDRIVE', 'GRASSPELT', 'SANDVEIL', 'SNOWCLOAK'}
def bst(n, k): return TA[n]['base'][k]
def fmt_fit(c):
    """Rejuvenation core mindset: singles = fast cleaner + bulky pivot + wallbreaker; doubles = Fake Out / redirection +
    spread or speed control + bulky attacker. -> (singles {role: member}, doubles {role: member})"""
    def pick(test): return next((n for n in c if test(n)), None)
    atk = lambda n: INFO[n]['natk'] >= 2
    bulk = lambda n: bst(n, 'HP') + bst(n, 'Def') + bst(n, 'SpD') >= 270
    sg = {'Fast cleaner': pick(lambda n: atk(n) and (bst(n, 'Spe') >= 95 or INFO[n]['ms'] & {'DRAGONDANCE', 'QUIVERDANCE', 'SHIFTGEAR'} or PRIO.get(n))),
          'Bulky pivot': pick(lambda n: bulk(n) and (INFO[n]['ab'] == 'REGENERATOR' or INFO[n]['ms'] & (PIVOTM | RECOV | DISRUPT_S))),
          'Wallbreaker': pick(lambda n: atk(n) and (max(bst(n, 'Atk'), bst(n, 'SpA')) >= 115 or INFO[n]['ab'] in ('SKILLLINK', 'PUNKROCK', 'ADAPTABILITY', 'HUGEPOWER', 'SHEERFORCE', 'TOUGHCLAWS', 'TECHNICIAN') or INFO[n]['ms'] & SETUP))}
    dg = {'Fake Out / redirection': pick(lambda n: INFO[n]['ms'] & {'FAKEOUT', 'FOLLOWME', 'RAGEPOWDER'} or INFO[n]['ab'] == 'INTIMIDATE'),
          'Spread or speed control': pick(lambda n: INFO[n]['spread'] or INFO[n]['ms'] & {'TAILWIND', 'ICYWIND', 'ELECTROWEB', 'TRICKROOM', 'THUNDERWAVE'}),
          'Bulky attacker': pick(lambda n: atk(n) and bulk(n))}
    return sg, dg
SETUP = {'SWORDSDANCE', 'NASTYPLOT', 'DRAGONDANCE', 'QUIVERDANCE', 'CALMMIND', 'BULKUP', 'CURSE', 'SHELLSMASH', 'COIL', 'BELLYDRUM', 'SHIFTGEAR'}
def synergy(c):
    s, why = 0.0, []
    cats = set().union(*(INFO[n]['cats'] for n in c if INFO[n]['natk'] >= 2))   # attackers only (2+ attacks in the build)
    if {'physical', 'special'} <= cats: s += 1; why.append('Physical and special attackers: one Intimidate or screen cannot stop both')
    sp = sorted(INFO[n]['spe'] for n in c)
    if sp[-1] >= 90 and sp[0] <= 60: s += .5; why.append('Fast and slow members: works with and without speed control')
    has = lambda ids: [n for n in c if INFO[n]['ms'] & ids]
    red, slp, setp = has({'RAGEPOWDER', 'FOLLOWME'}), has({'SPORE', 'SLEEPPOWDER', 'LOVELYKISS', 'SING', 'HYPNOSIS', 'YAWN'}), has(SETUP)
    if red and setp: s += 1.5; why.append(f'{disp(red[0])} redirects while {disp(setp[0])} sets up')
    if slp and setp and not red: s += .75; why.append(f'{disp(slp[0])} puts a foe to sleep: free turns for {disp(setp[0])}')
    if [n for n in c if INFO[n]['ab'] == 'INTIMIDATE']: s += .5; why.append('Intimidate support')
    sc = has({'TAILWIND', 'TRICKROOM', 'ICYWIND', 'THUNDERWAVE', 'ELECTROWEB', 'GLARE', 'NUZZLE'})   # 23 Nov (Vincent): the core needs its own speed control
    if sc: s += 1.5; why.append(f'Speed control: {disp(sc[0])}')
    else: s -= .75
    reset = has({'HAZE', 'CLEARSMOG', 'ROAR', 'WHIRLWIND'}) + [n for n in c if INFO[n]['ab'] == 'UNAWARE']
    if reset: s += .5; why.append(f'Answers setup: {disp(reset[0])}')
    for a in c:
        for b in c:
            if a != b:
                for m in INFO[a]['spread']:
                    e = E.chart_eff((MV.get(m) or {}).get('type'), TA[b]['types']) if DEF[b].get((MV.get(m) or {}).get('type'), 1) else 0
                    if e >= 2: s -= 1; why.append(f'Friction: {disp(a)} {MV[m]["name"]} hits {disp(b)} super effectively')
    piv = [n for n in c if INFO[n]['ms'] & PIVOTM]; reg = [n for n in c if INFO[n]['ab'] == 'REGENERATOR']
    if piv: s += 1; why.append(f'Pivot move: {disp(piv[0])}')
    elif reg: s += .5; why.append(f'Regenerator switches: {disp(reg[0])}')
    else: s -= .5
    dep = [n for n in c if INFO[n]['ab'] in FIELDDEP]
    for n in dep: s -= 1.5; why.append(f'Field-reliant: {disp(n)} ({INFO[n]["ab"].title()}) is weak when a boss sets its own field')
    sg, dg = fmt_fit(c)
    s += .75 * sum(v is not None for v in sg.values()) + .75 * sum(v is not None for v in dg.values())
    return s, why
def score(c):
    c = list(c)
    strength = sum(TA[n]['blend'] for n in c) * 10
    d = 0.0; shared, triple, res_ = [], [], 0
    for t in TYPES:
        w = sum(DEF[n][t] > 1 for n in c); r = sum(DEF[n][t] < 1 for n in c)
        if w >= 3 or (N == 3 and w >= 2 and r == 0 and w == len(c) - 1 and False): d -= 4; triple.append(t)
        elif w >= 2 and r == 0: d -= 2; shared.append(t)
        if r: d += .3; res_ += 1
    cov = set().union(*(OFFT[n] for n in c))
    off = .25 * len(cov)
    syn, why = synergy(c)
    aev = .3 * sum('Aevian' in n for n in c)
    total = strength + d + off + syn + aev
    return total, dict(strength=round(strength, 2), defense=round(d, 2), offense=round(off, 2), synergy=round(syn, 2), aevian=round(aev, 2),
                       shared=shared, triple=triple, resisted=res_, covered=len(cov), uncovered=[t for t in TYPES if t not in cov], why=why)
res = sorted(((score(c)[0], c) for c in itertools.combinations(POOL, N)), key=lambda x: -x[0])
best = list(res[0][1]); tot, br = score(best)
runners = []
for s_, c in res[1:60]:
    out_ = [n for n in best if n not in c]; in_ = [n for n in c if n not in best]
    if len(in_) == 1 and not any(r['in'] == in_[0] for r in runners):
        runners.append(dict(out=out_[0], **{'in': in_[0]}, delta=round(s_ - tot, 2)))
    if len(runners) >= 4: break
def mem(n):
    r = TA[n]
    return dict(name=n, tier=r['tier'], sid=r.get('sid'), form=str(r.get('form', '0')), blend=r['blend'], meta=r['meta'], game=r.get('game_pct'),
                types=r['types'], moves=INFO[n]['mnames'], ability=INFO[n]['ab'], aevian='Aevian' in n, where=r.get('where'),
                chips=cues(r['types'], INFO[n]['ab'], INFO[n]['mnames'], lambda t, ty: E.chart_eff(t, ty)))
_sg, _dg = fmt_fit(best)
out = dict(core=[mem(n) for n in best], n=N, score=round(tot, 2), parts=br, runners=runners, pool=len(POOL),
           singles={k: v for k, v in _sg.items()}, doubles={k: v for k, v in _dg.items()},
           matrix={n: DEF[n] for n in best})
json.dump(out, open('team/core4.json', 'w'), indent=1, ensure_ascii=False)
print('core4:', best, round(tot, 2), {k: v for k, v in br.items() if k in ('strength', 'defense', 'offense', 'synergy', 'aevian')})
if not OUT: sys.exit(0)
# ---- Builder tab: your best 4 (no opponent), how it is picked, close alternatives, type check
def pill(t): return f'<span class="tp ty-{t.lower()}">{t.title()}</span>'
h = f'<article class="plc"><h3>Your core of {N}</h3><ul class="bl">'
for m in out['core']:
    h += (f'<li class="bc" data-dn="{E_(disp(m["name"]))}" tabindex="0" role="button"><div class="bct"><span class="tier t{m["tier"]}">{m["tier"]}</span>'
          f'{SP.tag(m["sid"], m["form"], size="s")}<b>{E_(disp(m["name"]))}</b></div><div class="bchips">'
          + ''.join(f'<span class="{"btool" if k == "tool" else "bstat"}">{E_(c)}</span>' for k, c in m['chips'][:3]) + '</div></li>')
h += '</ul></article>'
def _fit(title, d):
    return (f'<article class="plc"><h3>{title}</h3><ul class="pwin">' + ''.join(
        f'<li class="{"pw-ok" if v else "pw-no"}"><b>{"✓" if v else "✗"}</b> {E_(k)}<div class="pans">{E_(disp(v)) if v else "A flex fills it"}</div></li>'
        for k, v in d.items()) + '</ul></article>')
h += _fit('Singles plan', out['singles']) + _fit('Doubles plan', out['doubles'])
P_ = out['parts']
rows = (f'<li><b>Strength</b><span>{P_["strength"]:.1f}</span></li><li><b>Defense</b><span>{P_["defense"]:+.1f}</span></li>'
        f'<li><b>Offense</b><span>{P_["offense"]:+.1f}</span></li><li><b>Synergy</b><span>{P_["synergy"]:+.1f}</span></li>'
        f'<li><b>Aevian bonus</b><span>{P_["aevian"]:+.1f}</span></li>')
mrows = ''.join(f'<li><b>{E_(disp(m["name"]))}</b><span>Tier score {m["blend"]:.2f}</span><span>Meta / community {m["meta"]:.2f}</span>'
                f'<span>In-game (every fight in the game): better than {round(100 * (m["game"] or 0))}% of your box</span></li>' for m in out['core'])
syn = ''.join(f'<li>{E_(w)}</li>' for w in P_['why']) or '<li>No special combos</li>'
dfn = [f'Resists {P_["resisted"]} of 18 attacking types']
dfn += [f'Shared weakness: {t.title()}' for t in P_['shared']] or ['No shared weakness']
dfn += [f'3 weak to {t.title()}' for t in P_['triple']]
ofn = [f'Super effective on {P_["covered"]} of 18 types'] + ([f'Not covered: {", ".join(t.title() for t in P_["uncovered"])}'] if P_['uncovered'] else [])
h += ('<article class="plc"><h3>How the core is picked</h3><ul class="pscore">' + rows + '</ul>'
      '<details class="pho"><summary>Each member</summary><ul class="pwhy2">' + mrows + '</ul></details>'
      '<details class="pho"><summary>Synergy</summary><ul class="pck">' + syn + '</ul></details>'
      '<details class="pho"><summary>Defense and offense</summary><ul class="pck">' + ''.join(f'<li>{E_(x)}</li>' for x in dfn + ofn) + '</ul></details>'
      '<details class="pho"><summary>How the score works</summary><ul class="pck"><li>Strength: the four tier scores (meta / community + in-game results)</li>'
      '<li>Defense: no type 2+ are weak to unless someone resists it</li><li>Offense: types the four hit super effectively</li>'
      '<li>Synergy: how they play together</li><li>Aevian: small tiebreak bonus</li><li>No opponent and no roles: flexes come per fight</li></ul></details></article>')
if out['runners']:
    h += '<article class="plc"><h3>Close alternatives</h3><ul class="pck">' + ''.join(
        f'<li>{E_(disp(r["out"]))} → {E_(disp(r["in"]))} <span class="pmuted">({r["delta"]:+.1f})</span></li>' for r in out['runners']) + '</ul></article>'
th = ''.join(f'<th>{SP.tag(m["sid"], m["form"], size="s")}</th>' for m in out['core'])
def fx(v): return '0' if v == 0 else '¼' if v == .25 else '½' if v == .5 else '2×' if v == 2 else '4×' if v == 4 else ''
def fc(v): return 'im' if v == 0 else 'rs' if v < 1 else 'w4' if v > 2 else 'wk' if v > 1 else ''
tr = ''
for t in TYPES:
    vs = [out['matrix'][m['name']][t] for m in out['core']]
    w = sum(v > 1 for v in vs); r = sum(v < 1 for v in vs)
    tr += (f'<tr><th>{pill(t)}</th>' + ''.join(f'<td class="{fc(v)}">{fx(v)}</td>' for v in vs)
           + f'<td class="cnt{" bad" if w >= 2 and not r else ""}">{w or ""}</td><td class="cnt{" ok" if r else ""}">{r or ""}</td></tr>')
h += (f'<article class="plc"><h3>Type check</h3><div class="ptm"><table class="ptab pmt"><thead><tr><th></th>{th}<th>Weak</th><th>Res.</th></tr></thead>'
      f'<tbody>{tr}</tbody></table></div></article>')
css = '''<style id="core4-css">.pscore { list-style: none; margin: 0; padding: 0; display: grid; gap: 4px; font-size: 13.5px }
.pscore li { display: flex; justify-content: space-between } .pwhy2 { list-style: none; margin: 4px 0 0; padding: 0; display: grid; gap: 6px; font-size: 12.5px }
.pwhy2 li { display: grid } .pwhy2 li span { color: var(--muted) } .pmuted { color: var(--muted) }</style>'''
sec = f'<section aria-labelledby="sbuild">\n  <h2 id="sbuild">Core</h2>\n{css}<div class="pgrid">{h}</div>\n</section>\n'
page = open(OUT, encoding='utf-8').read()
page = re.sub(r'<section aria-labelledby="sbuild">.*?</section>\s*', '', page, flags=re.S)
anchor = page.find('<section aria-labelledby="s1f">')
page = page[:anchor] + sec + page[anchor:] if anchor >= 0 else page.replace('</main>', sec + '</main>')
open(OUT, 'w', encoding='utf-8').write(page)
