"""App theme (Vincent, 17 Nov: "look like an app, Pokémon themed"). Runs LAST in update.py, after tabs.py.
Reskins the generated guide without touching any data: Rotom-Dex style app bar, party slots with level bars, a bottom tab bar
(phone) / side rail (desktop) with 6 tabs (the three tier tabs become one "Dex" tab with a switcher; C&A checks sit behind the
shield icon in the app bar), and the scoring explanations folded into "How this works".
usage (from workspace/): python3 -I ../scripts/team/theme.py <report.html>"""
import html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kits import disp
import sprites as SP
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
def spr(n, size='s', shiny=False):
    r = T.get(n) or {}
    return SP.tag(r.get('sid'), r.get('form', '0'), shiny, size) if r.get('sid') else ''
BUILD = {}   # the team table's build per Pokémon (ability, nature, EVs, item, moves, open to-dos); the table itself is removed
def _t(x): return re.sub(r'<[^>]+>', '', x).strip()
for row in re.findall(r'<td class="tm-name">(.*?)</tr>', page, re.S):
    cell = lambda k, row=row: (re.search(r'<td data-l="' + k + r'">(.*?)</td>', row, re.S) or [None, ''])[1]
    ab = cell('Ability'); nat = re.search(r'<div class="legend">(.*?)</div>', ab)
    BUILD[_t(re.search(r'<strong>(.*?)</strong>', row, re.S).group(1))] = dict(
        ability=_t(re.sub(r'<div.*', '', ab, flags=re.S)), nature=nat.group(1) if nat else '',
        evs=' / '.join(_t(x) for x in re.findall(r'<li>(.*?)</li>', cell('EVs'))), item=_t(cell('Item')),
        moves=[_t(x) for x in re.findall(r'<li[^>]*>(.*?)</li>', cell('Moves'))],
        todo=[_t(x) for x in re.findall(r'<li>(.*?)</li>', cell('Status')) if not _t(x).startswith('Lv ')])
page = re.sub(r'<div class="panel tablewrap"><table class="team">.*?</table></div>\s*', '', page, count=1, flags=re.S)
def build_html(b, p, here):
    if not b: return '<div class="slot-sub">' + E(p.get('item') or 'no item') + here + '</div>'
    todo = ''.join('<li>' + E(t) + '</li>' for t in b['todo'])
    return ('<dl class="sb"><dt>Ability</dt><dd>' + E(b['ability']) + ' · ' + E(b['nature']) + '</dd><dt>EVs</dt><dd>' + E(b['evs']) +
            '</dd><dt>Item</dt><dd>' + E(b['item']) + '</dd></dl><ul class="mvs">' + ''.join('<li>' + E(m) + '</li>' for m in b['moves']) + '</ul>'
            + ('<ul class="todo-mini">' + todo + '</ul>' if todo else '') + ('<div class="slot-sub">' + here + '</div>' if here else ''))
slots = ''
for i, nm in enumerate(st['team']):
    d = disp(nm); r = T.get(nm, {}); p = party.get(d) or {}
    lv = p.get('level') or 0
    types = ''.join(f'<span class="pt" style="--tc:{TYPE.get(t, "#888")}">{E(t.title())}</span>' for t in r.get('types', []))
    # 21 Nov (Vincent): Core 1 lead · Core 2 lead partner · Core 3 mid game · Flex 1-2 (battle start / mid game / closer) · Core 4 closer
    _core = list(st.get('core') or [])
    if nm in _core:
        _ci = _core.index(nm); tag = f'Core {_ci + 1}'; role = ('Lead', 'Lead partner', 'Mid game', 'Closer')[min(_ci, 3)]
    else:
        _fl = [x for x in st['team'] if x not in _core]; tag = f'Flex {_fl.index(nm) + 1}'
        _mv = {re.sub(r'[^A-Z]', '', m.upper()) for m in (st.get('moves') or {}).get(nm, [])}
        _ld = (FP.get(st.get('fight')) or {}).get('leads') or []
        role = ('Battle start' if nm in _ld else 'Closer' if _mv & {'SWORDSDANCE', 'DRAGONDANCE', 'NASTYPLOT', 'CALMMIND', 'SHELLSMASH', 'SHIFTGEAR',
                'QUIVERDANCE', 'BULKUP', 'CURSE', 'FILLETAWAY', 'TIDYUP', 'VICTORYDANCE'} else 'Mid game')
    here = '' if p else '<span class="slot-miss">not in party</span>'
    slots += (f'<li class="slot{" is-core" if nm in core else ""}">' + spr(nm, 'l', bool(p.get('shiny'))) + f'<div class="slot-top"><span class="slot-n">{i + 1}</span>'
              f'<span class="slot-tag">{tag}{" · " + E(role) if role else ""}</span></div>'
              f'<b class="slot-name">{E(d)}</b><div class="slot-types">{types}</div>'
              f'<div class="slot-lv"><span>Lv {lv or "?"}</span><span class="lv-bar" role="img" aria-label="Level {lv} of {CAP}">'
              f'<i style="width:{min(100, round(100 * lv / CAP)) if lv else 0}%"></i></span><span class="lv-cap">{CAP}</span></div>'
              + build_html(BUILD.get(d), p, here) + f'<!--MW:{nm}--></li>')
nxt = ''
if st.get('fight') and st['fight'] in FP:
    p = FP[st['fight']]
    nxt = (f'<a class="next" href="#fights" data-go="fights"><span class="next-k">Next battle</span>'
           f'<b>{E(FIGHT_NAME.get(st["fight"], st["fight"]))}</b><span>{E(p["format"])} · bring {E(" + ".join(disp(r["name"]) for r in p["swaps"]))}'
           f'</span><span class="next-go" aria-hidden="true">›</span></a>')
low = sum(1 for nm in st['team'] if (party.get(disp(nm)) or {}).get('level', CAP) < CAP)
hero = f'<div class="hero"><div class="hero-head"><h3>Your party</h3></div><ol class="party">{slots}</ol>{nxt}</div>'
page = re.sub(r'(<section aria-labelledby="s1">\s*<h2 id="s1">.*?</h2>)', lambda m: m.group(1) + hero, page, count=1, flags=re.S)

page = re.sub(r'<div class="panel pad lvl">.*?</div>\s*', '', page, count=1, flags=re.S)   # the party slots show levels now

# ---------------------------------------------------------------- trim caption text (Vincent, 17 Nov: only what's truly needed)
page = re.sub(r'(<div class="panel pad cf"><h3>.*?)\s*<span class="legend">.*?</span>(</h3>)', r'\1\2', page, flags=re.S)   # boss caption
page = re.sub(r'(<h3>Hard fights left)\s*<span class="legend">.*?</span>', r'\1', page)
page = re.sub(r'\s*<span class="legend">\((?:plan: your core \+ 2 swaps|box preview[^)]*|your lineup)\)</span>', '', page)
def chip(m):   # lineup notes -> a short role chip ("LEAD · BAR 1 COUNTER (swap): ..." -> "Lead · Bar 1 counter")
    lab = re.sub(r'\s*\(.*?\)', '', m.group(2).split(':')[0]).strip()
    lab = ' · '.join(x[:1].upper() + x[1:].lower() for x in lab.split(' · ')).replace('alm mind', 'alm Mind').replace('calm Mind', 'Calm Mind')
    lab = {'Back': 'In the back', 'Backup Calm Mind answer': 'Backup · Calm Mind answer'}.get(lab, lab)
    return f'{m.group(1)}<td><span class="role-chip">{html.escape(lab)}</span></td>'
def cft(m):
    return re.sub(r'(<td>[^<]*?/ Protect</td>)<td>([^<]*)</td>', chip, m.group(0))
page = re.sub(r'<table class="cft">.*?</table>', cft, page, flags=re.S)
page = re.sub(r"(<h3>Fight plans: your core \+ 2 swaps per fight</h3>)(<ul class='legend'>.*?</ul>)",
              r'\1<details class="how"><summary>How this works</summary>\2</details>', page, flags=re.S)

# ---------------------------------------------------------------- Fights tab (17 Nov): one card per fight, single source = fight_plans.json
def _txt(x): return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', x)).strip()
HF = []   # (name, format, boss, field) from the "Hard fights left" table, story order
for r in re.findall(r'<tr><td class="c hn">\d+</td>(.*?)</tr>', page, re.S):
    nm_ = _txt(re.search(r'<td class="hf"><b>(.*?)</b> <span', r, re.S).group(1))
    HF.append(dict(name=nm_, boss='bossb' in r, field=_txt((re.search(r'<td data-l="Field">(.*?)</td>', r, re.S) or [0, ''])[1])))
FB = [_txt(m) for m in re.findall(r'<div><b>Field boosts:</b>(.*?)</div>', page, re.S)]
FBX = {}
_cards = re.findall(r'<div class="panel pad nf"><h4>(.*?)</h4>(.*?)</div>(?=<div class="panel pad nf">|</div>)', page, re.S)
for h4, body in _cards:
    m_ = re.search(r'<b>Field boosts:</b>(.*?)</div>', body, re.S)
    FBX[_txt(re.sub(r'<span class="legend">.*', '', h4, flags=re.S))] = _txt(m_.group(1)) if m_ else ''
def tname(n):
    return tchip_s(n) + spr(n) + '<span>' + E(disp(n)) + '</span>'
def tchip_s(n):
    t = (T.get(n) or {}).get('tier', '?')
    return '<span class="tier t' + t + '">' + t + '</span>'
def bar(v, cls):
    return '<span class="mbar ' + cls + '"><i style="width:' + str(min(100, v)) + '%"></i></span><b class="mv">' + str(v) + '%</b>'
BOSSF = SP.boss_forms()
def wc_html(q):   # the foe's win conditions and your answer to each (fight protocol step 2)
    w = q.get('wincons') or []
    if not w: return ''
    return '<div class="wc">' + ''.join(('<span class="wc-ok">' + E(x['what']) + ' → ' + E(', '.join(x['answers'][:2])) + '</span>') if x['answers']
                                        else ('<span class="wc-no">' + E(x['what']) + ': no answer</span>') for x in w) + '</div>'

FT = json.load(open('gamedata/fieldtext.json')) if os.path.exists('gamedata/fieldtext.json') else {}
TN = {'Atk': 'atk', 'Def': 'def', 'SpA': 'spa', 'SpD': 'spd'}
def _t(x): return x.title() if x else ''
def field_line(fname):   # the field's real effects (fieldtext typeBoosts) + end-of-turn chip
    fv = next((v for v in FT.values() if v.get('name') == fname), None)
    if not fv: return ''
    tc = fv.get('typeCondition') or {}
    lab = lambda t: _t(t) + (' (special)' if 'Special' in str(tc.get(t, '')) else ' (physical)' if 'Physical' in str(tc.get(t, '')) else '')
    parts = [' · '.join(', '.join(lab(t) for t in ts) + ' ×' + m.rstrip('0').rstrip('.') for m, ts in sorted((fv.get('typeBoosts') or {}).items(), key=lambda kv: -float(kv[0])))]
    mvb = {}
    for m, ms in (fv.get('damageMods') or {}).items(): mvb.setdefault(float(m), []).extend(ms)
    for m, ms in sorted(mvb.items(), key=lambda kv: -kv[0]):
        rows += ('<div class="fx ' + ('up' if m > 1 else 'down') + '"><span class="fx-ar">' + (f'▲ ×{m:g}' if m > 1 else '✕ fails' if m == 0 else f'▼ ×{m:g}') + '</span>'
                 + f'<span class="fx-note">{len(ms)} named moves</span></div>')
    if fname == 'Corrupted Cave': parts.append('your grounded non-Poison/Steel Pokémon lose 1/8 HP a turn')
    return ' · '.join(p for p in parts if p)
MVN = {}
try: MVN = {k: v.get('name', k) for k, v in json.load(open('gamedata/movetext.json')).items()}
except Exception: pass
ITN = {}
try: ITN = {k: v.get('name', k) for k, v in json.load(open('gamedata/itemtext.json')).items()}
except Exception: pass
def bar_plan_html(k, bsprite):
    fp = f'team/bar_plan_{k}.json'
    if not os.path.exists(fp) or k != st.get('fight'): return None
    bp = json.load(open(fp)); pl = bp.get('melia') or bp.get('solo')
    if not pl: return None
    out = '<div class="frow"><span class="fk">Speed</span><span class="fbo">Boss Speed ' + str(bp['boss_spe']) + ' → ' + (
        'all six move first' if all(m['spe'] > bp['boss_spe'] for m in bp['mons'].values()) else
        'slower than it: ' + ', '.join(disp(n) for n, m in bp['mons'].items() if m['spe'] <= bp['boss_spe'])) + '</span></div>'
    out += '<ol class="bars">'
    prev = None
    for j, B in enumerate(bp['bars']):
        st_ = {a: v for a, v in B['stg'].items() if v}
        chips = []
        if B.get('types'): chips.append('/'.join(_t(t) for t in B['types']))
        if B.get('item'): chips.append(ITN.get(B['item'], _t(B['item'])))
        if st_: chips.append(' '.join(('+' if v > 0 else '') + str(v) + ' ' + {'atk': 'Atk', 'def': 'Def', 'spa': 'SpA', 'spd': 'SpD'}[a] for a, v in st_.items()))
        new = [MVN.get(m, m) for m in B['moves'] if prev and m not in prev['moves']]
        if new: chips.append('new: ' + ', '.join(new))
        prev = B
        steps, cur = [], None
        for l in [l for l in pl['log'] if l['bar'] == j]:
            a = 'switch in' if l['act'] == 'switch' else ((bp.get('move', {}).get(l['mon'], [''] * 9)[j] or 'attack') + (f" (+{l['stage']})" if l.get('stage') else '') if l['act'] == 'attack' else l['act'])
            if cur and cur[0] == l['mon']: cur[1].append(a)
            else: cur = [l['mon'], [a]]; steps.append(cur)
        def comp(acts):
            o = []
            for a in acts:
                if o and o[-1][0] == a: o[-1][1] += 1
                else: o.append([a, 1])
            return ' → '.join(a + (' ×' + str(c) if c > 1 else '') for a, c in o)
        rows = ''
        for n, acts in steps:
            m = bp['mons'][n]
            rows += ('<li><span class="ctr-m">' + tname(n) + '</span><span class="acts">' + E(comp(acts)) + '</span><span class="dt"><span class="lab">Hit +0</span>'
                     + bar(m['d'][j], 'deal') + '<span class="lab">Takes</span>' + bar(m['t'][j], 'take') + '</span></li>')
        out += ('<li class="barc"><div class="barh">' + bsprite + '<b>Bar ' + str(j + 1) + '</b><span class="fchips">'
                + ''.join('<span class="fchip">' + E(c) + '</span>' for c in chips) + '</span></div><ul class="steps">' + rows + '</ul></li>')
    out += '</ol>'
    car = bp.get('carrier'); bk = bp.get('backup')
    if car:
        out += ('<div class="frow"><span class="fk">Key</span><span class="fbo">' + E(disp(car)) + ' carries it. ' +
                ('If it falls: ' + ' → '.join(disp(x) for x in bk['order'][1:]) if bk else 'No sure win without it: Recover early') + '</span></div>')
    return out

FLAGK = {'soundmove': ('Soundmove', 'Sound moves'), 'sharpmove': ('Sharpmove', 'Slicing moves'), 'windmove': ('Windmove', 'Wind moves'),
         'punchmove': ('Punchmove', 'Punch moves'), 'beammove': ('Beammove', 'Beam moves'), 'bitingmove': ('Bitingmove', 'Biting moves')}
def cond_note(c):   # Battle_Field.rb typeCondition (eval'd Ruby) -> plain words
    c = str(c or '')
    if not c or 'YVELTAL' in c: return ''
    if 'pbIsSpecial' in c: return 'special moves only'
    if 'pbIsPhysical' in c: return 'physical moves only'
    if 'makesContact' in c: return 'non-contact moves only'
    if 'SCALD' in c and 'attacker.isAirborne' in c: return 'grounded user only, not Scald / Steam moves'
    if 'SCALD' in c: return 'not Scald / Steam moves'
    if 'attacker.isAirborne' in c: return 'grounded user only'
    if 'opponent.isAirborne' in c: return 'vs grounded targets only'
    if 'hasType?(:GROUND)' in c: return 'not vs Ground types'
    if 'WATER' in c and 'STEEL' in c: return 'vs Water / Steel targets only'
    if 'totalhp' in c: return 'vs targets at half HP or less'
    return 'conditional'
def cond_ok(c, d, flags, n):   # True / False for conditions on our move or user; None = depends on the target
    c = str(c or '')
    if not c or 'YVELTAL' in c: return True
    if 'pbIsSpecial' in c: return d.get('category') == 'special'
    if 'pbIsPhysical' in c: return d.get('category') == 'physical'
    if 'makesContact' in c: return 'Contact' not in flags
    mid = re.sub(r'[^A-Z]', '', (d.get('name') or '').upper())
    if 'SCALD' in c and mid in ('SCALD', 'HYDROSTEAM', 'STEAMERUPTION'): return False
    if 'attacker.isAirborne' in c:
        r = T.get(n) or {}
        return 'FLYING' not in (r.get('types') or []) and re.sub(r'[^A-Z]', '', str((st.get('abilities') or {}).get(n, r.get('ability', ''))).upper()) != 'LEVITATE'
    return None
def boosted_line(fname, names, rows=False):   # our six's moves the field changes, exactly as Battle_Move.rb: move bonus x max(flag bonus, type bonus)
    fv = next((v for v in FT.values() if v.get('name') == fname), None)
    if not fv: return [] if rows else ''
    MT = MTX; tc = fv.get('typeCondition') or {}
    tb = {t: float(m) for m, ts in (fv.get('typeBoosts') or {}).items() for t in ts}
    dm = {mv: float(m) for m, ms in (fv.get('damageMods') or {}).items() for mv in ms}
    DBM = DBMOVES
    out = []
    for n in names:
        for m in ((st.get('moves') or {}).get(n) or (IBX.get(n) or {}).get('moves') or []):
            k = re.sub(r'[^A-Z]', '', m.upper()); d = MT.get(k) or {}
            if d.get('category') not in ('physical', 'special'): continue
            flags = set((DBM.get(k) or {}).get('DataFlags') or [])
            why = []; dep = []
            mb = dm.get(k, 1.0)
            if mb != 1: why.append('field bonus')
            cands = []   # flag boosts and the type boost: the game takes the largest (typeFieldBoost)
            for key, mult in tb.items():
                if key in FLAGK and FLAGK[key][0] in flags:
                    ok = cond_ok(tc.get(key), d, flags, n)
                    if ok is not False: cands.append((mult, FLAGK[key][1], ok))
            t = (d.get('type') or '').upper()
            if t in tb:
                ok = cond_ok(tc.get(t), d, flags, n)
                if ok is not False: cands.append((tb[t], t, ok))
            tbm = 1.0
            if cands:
                if any(x[0] == 0 for x in cands): tbm = 0.0; best = min(cands)
                else: best = max(cands); tbm = best[0]
                if tbm != 1:
                    why.append(best[1])
                    if best[2] is None: dep.append(cond_note(tc.get(best[1] if best[1] in tb else t)))
            x = mb * tbm
            if x != 1: out.append((n, d.get('name', m), x, why + [f'({q})' for q in dep if q]))
    if rows: return out
    return ', '.join(f"{disp(n)} ({mv} ×{x:g})" for n, mv, x, _ in out if x > 1)
IBX = {}
try: IBX = json.load(open('team/ideal_builds.json'))
except Exception: pass
DBMOVES = {}
try: DBMOVES = json.load(open('data/Database_Moves.json'))
except Exception: pass
MTX = {}
try: MTX = json.load(open('gamedata/movetext.json'))
except Exception: pass

def field_html(fname, names):   # 21 Nov (Vincent): type pills with green ▲ / red ▼ multipliers + your boosted moves
    fv = next((v for v in FT.values() if v.get('name') == fname), None)
    if not fv: return ''
    tc = fv.get('typeCondition') or {}
    groups = {}
    for m, ts in (fv.get('typeBoosts') or {}).items():
        for t in ts:
            groups.setdefault((float(m), cond_note(tc.get(t))), []).append(t)
    rows = ''
    for (m, note), ts in sorted(groups.items(), key=lambda kv: (-kv[0][0], kv[0][1])):
        up = m > 1
        rows += ('<div class="fx ' + ('up' if up else 'down') + '"><span class="fx-ar">' + (('▲ ×' + f'{m:g}') if up else ('✕ fails' if m == 0 else '▼ ×' + f'{m:g}')) + '</span>'
                 + ''.join(f'<span class="pt" style="--tc:{TYPE.get(t, "#888")}">{E(FLAGK[t][1] if t in FLAGK else t.title())}</span>' for t in ts)
                 + (f'<span class="fx-note">{E(note)}</span>' if note else '') + '</div>')
    mvb = {}
    for m, ms in (fv.get('damageMods') or {}).items(): mvb.setdefault(float(m), []).extend(ms)
    for m, ms in sorted(mvb.items(), key=lambda kv: -kv[0]):
        rows += ('<div class="fx ' + ('up' if m > 1 else 'down') + '"><span class="fx-ar">' + (f'▲ ×{m:g}' if m > 1 else '✕ fails' if m == 0 else f'▼ ×{m:g}') + '</span>'
                 + f'<span class="fx-note">{len(ms)} named moves</span></div>')
    if fname == 'Corrupted Cave':
        rows += '<div class="fx down"><span class="fx-ar">▼ 1/8 HP</span><span class="fx-note">a turn for your grounded non-Poison / non-Steel Pokémon</span></div>'
    mine = boosted_line(fname, names, rows=True)
    if mine:
        rows += '<div class="fx-h">Your moves here</div>'
        for n, mv, x, why in sorted(mine, key=lambda r: -r[2]):
            up = x > 1
            tag = ''.join(f'<span class="pt" style="--tc:{TYPE.get(w, "#888")}">{E(w.title())}</span>' if w in TYPE else f'<span class="fx-note">{E(w)}</span>' for w in why)
            rows += ('<div class="fx mv ' + ('up' if up else 'down') + '"><span class="fx-ar">' + (f'▲ ×{x:g}' if up else '✕ fails' if x == 0 else f'▼ ×{x:g}') + '</span>'
                     + spr(n) + f'<div class="mvc"><b>{E(disp(n))}</b><div class="mvl"><span>{E(mv)}</span>' + tag + '</div></div></div>')
    return '<div class="fxs">' + rows + '</div>'

def _six_rows(k, names):
    try: R = json.load(open(f'team/{k}_eval.json'))
    except Exception: return None, {}
    rows = {}
    for y in R['rows']:
        if y['name'] in names and (y['name'] not in rows or y.get('fixed')): rows[y['name']] = y
    return R, rows
def speed_html(k, names):   # 21 Nov: foes faster than every member of your six
    R, rows = _six_rows(k, names)
    if not R or not rows: return ''
    fast_n, fast_s = max(((n, y['spe']) for n, y in rows.items()), key=lambda x: x[1])
    ids = R.get('foe_ids') or []
    out = [(R['foes'][j][1], s_, ids[j] if j < len(ids) else None) for j, s_ in enumerate(R['foe_spe']) if s_ > fast_s]
    if not out: return '<span class="fx-note">None: your ' + E(disp(fast_n)) + ' (' + str(fast_s) + ') outspeeds all of them</span>'
    return ('<div class="spd">' + ''.join('<span class="spc">' + (SP.tag(*i_, size='s') if i_ else '') + E(n_.split(' (')[0]) + ' <b>' + str(s_) + '</b></span>'
                                          for n_, s_, i_ in sorted(out, key=lambda x: -x[1]))
            + '<span class="fx-note">your fastest: ' + E(disp(fast_n)) + ' ' + str(fast_s) + '</span></div>')
HAZ = {'TOXICSPIKES': 'Toxic Spikes', 'STEALTHROCK': 'Stealth Rock', 'SPIKES': 'Spikes', 'STICKYWEB': 'Sticky Web'}
def watch_html(k, p, names):   # 21 Nov: each foe's trick -> your answer (win conditions + hazards + crit setup)
    R, rows = _six_rows(k, names)
    ids = (R or {}).get('foe_ids') or []
    items = []
    for j, q in enumerate(p['pairs']):
        for w in q.get('wincons') or []:
            items.append((j, q['foe'], w['what'], ', '.join(w['answers'][:2]) if w['answers'] else ''))
    for j, mv in enumerate((R or {}).get('foe_moves') or []):
        foe = R['foes'][j][1]; mv = {re.sub(r'[^A-Z]', '', m.upper()) for m in mv}
        for h in sorted(mv & set(HAZ)):
            imm = []
            for n, y in rows.items():
                ty = set(y['types']); ab = re.sub(r'[^A-Z]', '', str(y.get('ab') or ''))
                air = 'FLYING' in ty or ab == 'LEVITATE'
                if ab == 'MAGICGUARD' or (h == 'TOXICSPIKES' and (ty & {'POISON', 'STEEL'} or air)) or (h in ('SPIKES', 'STICKYWEB') and air):
                    imm.append(disp(n))
            items.append((j, foe, HAZ[h], ('immune: ' + ', '.join(imm)) if imm else ''))
        if 'FOCUSENERGY' in mv: items.append((j, foe, 'Focus Energy (then every hit crits)', 'hit it before it sets up'))
    if not items: return ''
    return '<div class="wl">' + ''.join('<div class="wi ' + ('w-ok' if a else 'w-no') + '">' + (SP.tag(*ids[j], size='s') if j < len(ids) else '')
                                        + '<b>' + E(foe.split(' (')[0]) + '</b><span>' + E(what) + '</span><span class="wa">' + ('→ ' + E(a) if a else 'no answer') + '</span></div>'
                                        for j, foe, what, a in items) + '</div>'
def fight_cards():
    order = [k for k in ['darkgardevoir', 'garbodor', 'karrina', 'spector', 'spector2', 'jenner9', 'amanda', 'erick'] if k in FP]
    out = ''
    for idx, k in enumerate(order):
        p = FP[k]; hf = HF[idx] if idx < len(HF) else {}
        name = FIGHT_NAME.get(k, k); nb = sum(1 for q in p['pairs'] if q['ok'])
        good = nb >= p['n'] - 1
        try: _ids0 = json.load(open(f'team/{k}_eval.json')).get('foe_ids') or []
        except Exception: _ids0 = []
        _ace = (BOSSF.get(k) or (_ids0[-1] if _ids0 else None))   # 21 Nov: the fight's ace (last Pokémon) / the boss as its icon
        _ic = ('<span class="fn fn-ace">' + SP.tag(*_ace, size='m') + '</span>') if _ace else ('<span class="fn">' + str(idx + 1) + '</span>')
        head = ('<summary>' + _ic + '<span class="ft"><b>' + E(name) + '</b><span class="fchips">'
                + '<span class="fchip">' + E(p['format']) + '</span>' + ('<span class="fchip boss">Boss</span>' if hf.get('boss') else '')
                + ('<span class="fchip">' + E(hf.get('field', '')) + '</span>' if hf.get('field') else '') + '</span></span>'
                + ('<span class="needs">Needs a plan</span>' if p.get('note') else '')
                + ('<span class="cnt ok">Plan ✓</span>' if os.path.exists(f'team/bar_plan_{k}.json') and k == st.get('fight') and hf.get('boss') else '') + '</summary>')
        bring = ''.join('<li>' + tname(r['name']) + '</li>' for r in p['swaps'])
        lead = ''.join('<li>' + tname(x) + '</li>' for x in p['leads'])
        fb = FBX.get(name, '') or FBX.get(hf.get('name', ''), '')
        rows = p['pairs'] if all('(bar ' in q['foe'] for q in p['pairs']) else sorted(p['pairs'], key=lambda q: q['ok'])   # boss bars stay in order
        try: _ids = json.load(open(f'team/{k}_eval.json')).get('foe_ids') or []
        except Exception: _ids = []
        _bf = BOSSF.get(k)
        _fs = {q['foe']: (SP.tag(*(_bf or _ids[j]), size='m') if (_bf or j < len(_ids)) else '') for j, q in enumerate(p['pairs'])}
        foes = ''.join('<li class="' + ('is-ok' if q['ok'] else 'is-weak') + '"><span class="foe">' + _fs.get(q['foe'], '') + E(q['foe']) + '</span><span class="arrow">→</span>'
                       '<span class="ctr-m">' + tname(q['mon']) + '</span><span class="dt"><span class="lab">Deals</span>' + bar(q['dealt'], 'deal')
                       + '<span class="lab">Takes</span>' + bar(q['taken'], 'take') + '</span><span class="st">'
                       + (('✓ after ' + E(q['setup'])) if q.get('setup') else ('✓' if q['ok'] else 'weak')) + '</span>' + wc_html(q) + '</li>' for q in rows)
        _bp = bar_plan_html(k, SP.tag(*(_bf or _ids[0]), size='m') if (_bf or _ids) else '') if hf.get('boss') else None
        out += ('<details class="fc' + (' is-next' if idx == 0 else '') + '"' + (' open' if idx == 0 else '') + '>' + head
                + '<div class="fbody"><div class="frow"><span class="fk">Bring</span><ul class="mons">' + bring + '</ul></div>'
                + (('<div class="frow ftop"><span class="fk">Field</span>' + _fh + '</div>') if (_fh := field_html(hf.get('field', ''), list(st.get('core') or []) + [r['name'] for r in p['swaps']])) else '')
                + ((('<div class="frow ftop"><span class="fk">Faster</span>' + _sp + '</div>') if (_sp := speed_html(k, list(st.get('core') or []) + [r['name'] for r in p['swaps']])) else '') if idx == 0 and not hf.get('boss') else '')
                + ((('<div class="frow ftop"><span class="fk">Watch</span>' + _wh + '</div>') if (_wh := watch_html(k, p, list(st.get('core') or []) + [r['name'] for r in p['swaps']])) else '') if idx == 0 else '')
                + (_bp or '') + '</div></details>')   # 21 Nov (Vincent): foe -> counter list removed; boss fights keep the bar plan
    # 21 Nov (Vincent): only the upcoming fight shows; the rest fold away (fights can come out of order)
    cards_ = re.findall(r'<details class="fc.*?</details>', out, re.S)
    if len(cards_) > 1:
        out = cards_[0] + ('<details class="later"><summary>Later fights · ' + str(len(cards_) - 1) + '</summary><div class="fcards">'
                           + ''.join(cards_[1:]) + '</div></details>')
    return '<div class="fcards">' + out + '</div>'
if FP and st.get('fight') in FP:   # 21 Nov (Vincent, trial): party cards warn about moves the next fight's field weakens / blocks
    _ord = [k_ for k_ in ['darkgardevoir', 'garbodor', 'karrina', 'spector', 'spector2', 'jenner9', 'amanda', 'erick'] if k_ in FP]
    _fld = (HF[_ord.index(st['fight'])] if _ord.index(st['fight']) < len(HF) else {}).get('field', '')
    for n_, mv_, x_, why_ in boosted_line(_fld, st['team'], rows=True):
        if x_ < 1:
            page = page.replace(f'<!--MW:{n_}-->', f'<div class="mw">{E(mv_)} ' + ('fails' if x_ == 0 else f'×{x_:g}') + f' on {E(_fld)}</div><!--MW:{n_}-->', 1)
page = re.sub(r'<!--MW:[^>]*-->', '', page)
if FP:
    page = re.sub(r'(<section aria-labelledby="s1f">\s*<h2 id="s1f">.*?</h2>).*?</section>', lambda m: m.group(1) + fight_cards() + '</section>', page, count=1, flags=re.S)
    page = re.sub(r'<section aria-labelledby="sctr">.*?</section>\s*', '', page, count=1, flags=re.S)

page = page.replace('<th>Best opener (matchup)</th>', '').replace('<th>Your six</th>', '')
page = re.sub(r'<td class="st[^"]*" data-l="Your six">.*?</td>', '', page, flags=re.S)
page = re.sub(r'<td data-l="Opener">.*?</td>', '', page, flags=re.S)

# ---------------------------------------------------------------- panels Vincent doesn't need on screen (17 Nov); data stays in team/*.json
page = re.sub(r'<div class="panel pad cf">.*?</ol></div>\s*', '', page, flags=re.S)                       # fight lineup + turn plan
page = re.sub(r'<div class="panel pad"><h3>Team rules \(core of 4 \+ 2 swaps\)</h3>.*?</ul></div>\s*', '', page, flags=re.S)
page = re.sub(r'<div class="panel pad"><h3>How to play it</h3>.*?</ul>\s*</div>\s*', '', page, flags=re.S)
page = re.sub(r"<div class='panel pad'><h3>Fight plans: your core.*?</table></div></div>", '', page, flags=re.S)
page = re.sub(r'<div class="legend nfn">.*?</div>\s*', '', page, flags=re.S)                 # fight cards: description line
page = re.sub(r'(<div class="panel pad nf">.*?)<ul class="plain">.*?</ul>(</div>)', r'\1\2', page, flags=re.S)   # fight cards: threat notes
CTITLE = {'balance': 'Balance / tempo', 'tr': 'Trick Room', 'setup': 'Setup / hyper offense', 'grassy': 'Grassy Terrain',
          'electric': 'Electric Terrain', 'sun': 'Sun', 'snow': 'Snow'}
def tchip(n):
    t = (T.get(n) or {}).get('tier', '?')
    return '<span class="tier t' + t + '">' + t + '</span>'
def core_grid():   # Cores: one compact card per style; key piece marked; the alt folded in as a swap option
    C = json.load(open('team/cores.json')) if os.path.exists('team/cores.json') else {}
    mine = sorted(st.get('core') or [])
    out = ''
    for k, v in C.items():
        if not v: continue
        main = v[0]['members']; key = main[0]; yours = sorted(main) == mine
        sw = {}
        if len(v) > 1:   # the alternative: each swapped member gets its replacement in grey on the same row
            am = v[1]['members']; RK = {'S': 4, 'A': 3, 'B': 2, 'C': 1, 'D': 0}; tr_ = lambda n: -RK.get((T.get(n) or {}).get('tier', 'D'), 0)
            o = sorted([n for n in main if n not in am], key=tr_); i_ = sorted([n for n in am if n not in main], key=tr_)   # same pairing as cores.py
            sw = dict(zip(o, i_))
        lis = ''.join('<li' + (' class="key"' if n == key else '') + '><span class="cm">' + tchip(n) + spr(n) + '<span class="nm">' + E(disp(n)) + '</span>' +
                      ('<small>key</small>' if n == key else '') + '</span>' +
                      ('<span class="alt" title="swap option"><span class="swp">⇄</span>' + tchip(sw[n]) + spr(sw[n]) + '<span class="nm">' + E(disp(sw[n])) + '</span></span>' if n in sw else '') +
                      '</li>' for n in main)
        alt = ''
        out += ('<article class="cc' + (' is-yours' if yours else '') + '"><header><b>' + E(CTITLE.get(k, k)) + '</b>' +
                ('<span class="yours">your core</span>' if yours else '') + '</header><ul class="cc-m">' + lis + '</ul>' + alt + '</article>')
    return '<div class="cgrid">' + out + '</div>'
page = re.sub(r'(<section aria-labelledby="s9">\s*<h2 id="s9">.*?</h2>\s*(?:<details class="how">.*?</details>)?).*?(</section>)',
              lambda m: m.group(1) + core_grid() + m.group(2), page, count=1, flags=re.S)

# ---------------------------------------------------------------- Boxes (17 Nov): two to-do lists in box-number order; full rosters folded below
SPN = {disp(r['name']): (r.get('sid'), r.get('form', '0')) for r in T.values()}
def spr_species(sp_, size='s'):
    if sp_ in SPN: return SP.tag(*SPN[sp_], size=size)
    return SP.tag(re.sub(r'[^A-Za-z]', '', sp_.split('-')[0]).upper(), '0', size=size)
try: ACT = json.load(open('team/actions.json'))
except Exception: ACT = {}
ENT = {d['n']: d for d in cb.parse(st['export'])}
def dest(a):
    a = a.lower()
    return 'Party' if 'into the party' in a else 'Overflow' if 'overflow' in a else 'Active'
gin, gout = [], []
for n_, a in sorted(ACT.items(), key=lambda kv: int(kv[0])):
    d = ENT.get(int(n_)) or {}
    row = ('<li><span class="bxn">#' + n_ + '</span>' + spr_species(d.get('species', '')) + '<b>' + E(d.get('species', '?')) + '</b>'
           + '<span class="blv">Lv ' + str(d.get('level', '?')) + '</span><span class="to">→ ' + dest(a) + '</span></li>')
    (gin if a.startswith(('Move to Active', 'Move into')) else gout).append(row)
def blist(title, rows, cls):
    return ('<div class="bxl ' + cls + '"><h3>' + title + ' <span class="bxc">' + str(len(rows)) + '</span></h3>'
            + ('<ul>' + ''.join(rows) + '</ul>' if rows else '<p class="none">Nothing to move</p>') + '</div>')
BOXMOVES = '<div class="bxmoves">' + blist('Move in', gin, 'in') + blist('Move out', gout, 'out') + '</div>'
page = re.sub(r'(<section aria-labelledby="s4">\s*<h2 id="s4">.*?</h2>)', lambda m: m.group(1) + BOXMOVES, page, count=1, flags=re.S)
page = re.sub(r'<div class="panel pad"><h3>Since last export</h3><div class="chgcols"><p>No changes\.</p></div></div>', '', page)
page = re.sub(r'<p class="legend"><span class="actkey in">Green</span>.*?</p>', '', page, flags=re.S)
page = page.replace('<details class="bx panel" open>', '<details class="bx panel">')

# ---------------------------------------------------------------- To do (17 Nov): cards with sprite, place chip, level chip, clean fix rows (no checkboxes)
def todo_card(m):
    name_html, sub, items = m.group(1), m.group(2), m.group(3)
    nm_ = _txt(name_html); place = _txt(sub).split('·')[-1].strip()
    lis = re.findall(r'<label[^>]*>(.*?)</label>', items, re.S)
    lv = next((_txt(x) for x in lis if _txt(x).startswith('Lv ')), '')
    rows = ''
    for x in lis:
        t = _txt(x)
        if t.startswith('Lv '): continue
        mt = re.match(r'Teach (.*?) \(replaces (.*?)\)$', t)
        if mt: rows += f'<li><span class="tk">Teach</span><b>{E(mt.group(1))}</b><span class="tr">replaces {E(mt.group(2))}</span></li>'; continue
        mk = re.match(r'(Item|Ability|Nature|EVs|Evolve into|Evolve)[: ]\s*(.*)$', t)
        if mk: rows += f'<li><span class="tk">{E(mk.group(1))}</span><span>{E(mk.group(2))}</span></li>'; continue
        rows += f'<li><span>{E(t)}</span></li>'
    done = '' if rows else '<p class="tdone">Build done ✓</p>'
    return (f'<div class="tcard"><div class="thead">{spr_species(nm_, "m")}<div><b>{E(nm_)}</b><span class="tplace">{E(place)}</span></div>'
            + (f'<span class="tlv">{E(lv)}</span>' if lv else '') + f'</div>' + (f'<ul class="tfix">{rows}</ul>' if rows else done) + '</div>')
page = re.sub(r'<div class="tgroup pcard"><h3>(.*?) <span class="legend">(.*?)</span></h3><ul class="todo">(.*?)</ul></div>', todo_card, page, flags=re.S)

# ---------------------------------------------------------------- Checks (17 Nov): summary + problems first; passed checks and reference panels folded
def checks(m):
    sec = m.group(0)
    rows = re.findall(r'<tr><td><span class=(ok|warn|bad)>.*?</span></td><td>(.*?)</td><td class="legend">(.*?)</td></tr>', sec, re.S)
    if not rows: return sec
    bad = [r for r in rows if r[0] != 'ok']; good = [r for r in rows if r[0] == 'ok']
    li = lambda r: f'<li class="ck {r[0]}"><span class="dot"></span><div><b>{r[1]}</b>' + (f'<span>{r[2]}</span>' if r[2].strip() else '') + '</div></li>'
    top = (f'<div class="ckhead"><b>{len(good)}/{len(rows)}</b><span>checks passed · run on every update</span></div>'
           + (f'<ul class="cks">{"".join(li(r) for r in bad)}</ul>' if bad else '')
           + f'<details class="ckmore"><summary>Passed ({len(good)})</summary><ul class="cks">{"".join(li(r) for r in good)}</ul></details>')
    rest = re.sub(r'<div class="panel pad"><h3>Automatic checks.*?</table></div>\s*</div>', '', sec, count=1, flags=re.S)
    rest = re.sub(r'<div class="panel pad"><h3>(.*?)</h3>(.*?)</div>(?=\s*(?:<div class="panel|</section>))',
                  lambda x: f'<details class="panel pad ckref"><summary>{x.group(1)}</summary>{x.group(2)}</details>', rest, flags=re.S)
    return rest.replace('</h2>', '</h2>' + '<div class="panel pad">' + top + '</div>', 1)
page = re.sub(r'<section aria-labelledby="s5">.*?</section>', checks, page, count=1, flags=re.S)

# ---------------------------------------------------------------- Dex detail sheet (tap a Pokémon in the Dex tables)
from kits import abn
DEX = {}
IDB = json.load(open('team/ideal_builds.json')) if os.path.exists('team/ideal_builds.json') else {}
for r in T.values():
    by = {}
    for c in r.get('counters', []):
        k_, f_ = c.split(':', 1); by.setdefault(FIGHT_NAME.get(k_, k_), []).append(f_)
    ib = IDB.get(r['name']) or {}
    DEX[disp(r['name'])] = dict(t=r['tier'], s=r['blend'], f=r['fight'], m=r['meta_label'], ty=r['types'], b=r['base'],
                                a=abn(re.sub(r'[^A-Z]', '', (ib.get('ability') or r['ability']).upper())), n=ib.get('nature') or r.get('nature', ''),
                                e=ib.get('evs') or ' / '.join(f"{v} {k}" for k, v in (r.get('evs') or {}).items() if v >= 100),
                                mv=(ib.get('moves') or r['attacks']) + ([ib['item']] if ib.get('item') else []), c=by, w=f"{r.get('where')} #{r.get('dump')}", sp=SP.cls(r.get('sid'), r.get('form', '0'))[3:])   # without 'sp-': only sprites the tables already use get embedded
SHEET = ('<div class="sheet" id="dexsheet" hidden><div class="sheet-bg" data-close></div><div class="sheet-card" role="dialog" aria-modal="true" aria-labelledby="ds-name">'
         '<button type="button" class="sheet-x" data-close aria-label="Close">×</button><div id="ds-body"></div></div></div>'
         '<script type="application/json" id="dexdata">' + json.dumps(DEX).replace('</', '<\\/') + '</script>')
page = page.replace('</body>', SHEET + '</body>') if '</body>' in page else page + SHEET

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
@media (max-width: 640px) { .party { grid-template-columns: 1fr } }
.slot-top, .slot-name, .slot-types, .slot-lv { margin-right: 92px; position: relative; z-index: 1 }
.slot { position: relative; background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 12px 14px 12px; display: grid; gap: 6px; box-shadow: var(--shadow); min-width: 0; overflow: hidden }
.slot > .spr-l { position: absolute; right: 8px; top: 6px; z-index: 0; filter: drop-shadow(0 2px 2px rgba(0,0,0,.18)) }
.slot::after { display: none; content: ""; position: absolute; right: -26px; top: -26px; width: 84px; height: 84px; border-radius: 50%; border: 10px solid var(--line); opacity: .55 }
.slot.is-core { border-color: color-mix(in srgb, var(--accent) 40%, var(--line)) }
.slot-top { display: flex; align-items: center; gap: 8px; position: relative; z-index: 1 }
.slot-n { display: grid; place-items: center; width: 22px; height: 22px; border-radius: 50%; background: var(--ink); color: var(--panel); font: 700 12px var(--mono) }
.slot-tag { font: 600 11px var(--mono); letter-spacing: .06em; text-transform: uppercase; color: var(--muted) }
.is-core .slot-tag { color: var(--accent) }
.slot-name { font: 700 17px/1.15 var(--display); overflow-wrap: anywhere; position: relative; z-index: 1 }
.slot-types { display: flex; gap: 4px; flex-wrap: wrap; align-items: flex-start; align-content: flex-start } .slot-types .pt { line-height: 1.4 }
.pt { background: var(--tc); color: #fff; font: 700 10.5px var(--body); letter-spacing: .04em; text-transform: uppercase; padding: 1px 8px; border-radius: 99px; text-shadow: 0 1px 0 rgba(0,0,0,.25) }
.slot-lv { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 8px; font: 600 12px var(--mono); font-variant-numeric: tabular-nums }
.lv-bar { height: 7px; border-radius: 99px; background: var(--panel-2); border: 1px solid var(--line); overflow: hidden }
.lv-bar i { display: block; height: 100%; background: var(--lv); border-radius: 99px }
.lv-cap { color: var(--muted) }
.sb { display: grid; grid-template-columns: auto 1fr; gap: 2px 10px; margin: 2px 0 0; font-size: 13px; position: relative; z-index: 1 }
.sb dt { font: 600 10.5px var(--mono); letter-spacing: .06em; text-transform: uppercase; color: var(--muted); padding-top: 2px }
.sb dd { margin: 0; min-width: 0 }
.mvs { list-style: none; margin: 2px 0 0; padding: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 4px }
.mvs li { background: var(--panel-2); border: 1px solid var(--line); border-radius: 8px; padding: 3px 8px; font: 600 12.5px var(--body); white-space: nowrap; overflow: hidden; text-overflow: ellipsis }
.todo-mini { list-style: none; margin: 0; padding: 0; display: grid; gap: 3px; font-size: 12.5px; color: var(--warn); font-weight: 700 }
.cgrid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)) }
.cc { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 14px 16px; box-shadow: var(--shadow); display: grid; gap: 10px; align-content: start }
.cc.is-yours { border: 2px solid var(--accent) }
.cc header { display: flex; align-items: center; justify-content: space-between; gap: 8px }
.cc header b { font: 700 16px var(--display) }
.cc .yours { background: var(--accent); color: #fff; font: 700 10.5px var(--mono); letter-spacing: .06em; text-transform: uppercase; padding: 2px 8px; border-radius: 99px }
.cc-m { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: 1fr; gap: 6px }
.cc-m li { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); align-items: center; gap: 8px; font: 700 13.5px var(--body); min-width: 0 }
.cc-m .cm, .cc-m .alt { display: flex; align-items: center; min-width: 0 }
.cc-m .nm { overflow: hidden; text-overflow: ellipsis; white-space: nowrap }
.cc-m .alt { color: var(--muted); font-weight: 600; opacity: .8 }
.cc-m .alt .tier { filter: grayscale(.6); opacity: .85 } .cc-m .swp { margin: 0 10px 0 2px; font-size: 15px }
.cc-m li span:not(.tier) { overflow: hidden; text-overflow: ellipsis; white-space: nowrap }
.cc-m .tier { min-width: 22px; height: 22px; font-size: 12px !important; margin-right: 6px }
.cc-m small { margin-left: 6px; font: 600 10px var(--mono); text-transform: uppercase; color: var(--accent) }
@media (max-width: 520px) { .cc-m li { grid-template-columns: 1fr; gap: 2px } .cc-m .alt { padding-left: 30px; font-size: 12.5px } .cc-m .alt .spr { width: 22px; height: 22px } .cgrid { grid-template-columns: 1fr } }
@media (max-width: 680px) { .tlx td.c br { display: none } .tlx td.c .legend { display: inline; margin-left: 6px } }
.cc-alt { font-size: 12.5px; color: var(--muted); border-top: 1px dashed var(--line); padding-top: 8px }
.cc-alt b { color: var(--ink) } .cc-alt .k { font: 600 10px var(--mono); text-transform: uppercase; color: var(--accent) }
.cc-alt span { font: 700 10.5px var(--mono); text-transform: uppercase; letter-spacing: .06em; margin-right: 6px; color: var(--ink) }
.fcards { display: grid; gap: 12px }
.fc { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; box-shadow: var(--shadow); overflow: hidden }
.fc.is-next { border: 2px solid var(--accent) }
.fc > summary { list-style: none; cursor: pointer; display: flex; align-items: center; gap: 12px; padding: 14px 16px }
.fc > summary::-webkit-details-marker { display: none }
.fn { flex: none; display: grid; place-items: center; width: 28px; height: 28px; border-radius: 50%; background: var(--ink); color: var(--panel); font: 700 13px var(--mono) }
.is-next .fn { background: var(--accent); color: #fff }
.ft { display: grid; gap: 4px; min-width: 0; flex: 1 }
.ft b { font: 700 17px/1.15 var(--display) }
.fchips { display: flex; flex-wrap: wrap; gap: 4px }
.fchip { font: 600 11px var(--mono); color: var(--muted); background: var(--panel-2); border: 1px solid var(--line); border-radius: 99px; padding: 1px 8px }
.fchip.boss { color: var(--accent); border-color: color-mix(in srgb, var(--accent) 40%, var(--line)) }
.needs { flex: none; font: 700 11px var(--mono); text-transform: uppercase; letter-spacing: .05em; color: var(--warn); background: var(--warn-soft); border-radius: 99px; padding: 3px 9px }
.cnt { flex: none; font: 700 14px var(--mono); padding: 4px 10px; border-radius: 10px }
.cnt.ok { background: var(--good-soft); color: var(--good) } .cnt.warn { background: var(--warn-soft); color: var(--warn) }
.fc > summary::after { content: "›"; font: 700 22px var(--display); color: var(--muted); transition: transform .15s }
.fc[open] > summary::after { transform: rotate(90deg) }
.fbody { display: grid; gap: 10px; padding: 0 16px 16px; border-top: 1px solid var(--line); padding-top: 12px }
.frow { display: flex; align-items: center; gap: 10px; flex-wrap: wrap }
.fk { font: 600 10.5px var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); min-width: 48px }
.mons { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 6px }
.mons li { display: flex; align-items: center; background: var(--panel-2); border: 1px solid var(--line); border-radius: 99px; padding: 3px 12px 3px 4px; font: 700 13.5px var(--body) }
.mons .tier, .foes .tier { min-width: 22px; height: 22px; font-size: 12px !important; margin-right: 6px }
.fbo { font-size: 13px; color: var(--muted) }
.frow.ftop { align-items: flex-start }
.fxs { display: grid; gap: 6px; flex: 1; min-width: 0 }
.fx { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; font-size: 13px }
.fx-ar { font: 700 12px var(--mono); min-width: 64px; padding: 2px 8px; border-radius: 99px; text-align: center }
.fx.up .fx-ar { color: var(--good); background: color-mix(in srgb, var(--good) 14%, transparent) }
.fx.down .fx-ar { color: var(--bad); background: color-mix(in srgb, var(--bad) 14%, transparent) }
.fx-note { color: var(--muted); font-size: 12px }
.spd { display: flex; flex-wrap: wrap; gap: 6px; align-items: center }
.spc { display: inline-flex; align-items: center; gap: 4px; font-size: 13px; padding: 2px 8px 2px 2px; border-radius: 99px; background: color-mix(in srgb, var(--bad) 10%, transparent) }
.spc b { font-family: var(--mono) }
.wl { display: grid; gap: 4px; flex: 1; min-width: 0 }
.wi { display: grid; grid-template-columns: auto auto 1fr; align-items: center; gap: 2px 8px; font-size: 13px }
.wi { color: var(--ink, inherit) } .wi .wa { grid-column: 2 / -1; color: var(--good); font-size: 12.5px } .wi.w-no .wa { color: var(--bad) }
.mw { margin-top: 6px; font-size: 12px; color: var(--bad); font-weight: 600 }
.fn.fn-ace { background: transparent !important; box-shadow: none !important; width: 48px; height: 48px; display: grid; place-items: center; overflow: visible }
.later > summary { cursor: pointer; font: 600 12px var(--mono); text-transform: uppercase; color: var(--muted); padding: 10px 4px; list-style: none }
.later > summary::before { content: '▸ ' } .later[open] > summary::before { content: '▾ ' }
.fx .pt { font-size: 11px }
.fx-h { font: 600 10px var(--mono); text-transform: uppercase; color: var(--muted); margin-top: 6px }
.fx.mv { display: grid; grid-template-columns: auto auto 1fr; align-items: center; gap: 8px; flex-wrap: nowrap }
.mvc { min-width: 0; display: grid; gap: 2px; text-align: left; justify-items: start } .mvc b { font-size: 13px } .mvl { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; font-size: 12.5px }
.bars { list-style: none; margin: 4px 0 0; padding: 0; display: grid; gap: 8px }
.barc { background: var(--card-2, rgba(127,127,127,.06)); border-radius: 12px; padding: 10px 12px }
.barh { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 6px }
.steps { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px }
.steps li { display: grid; grid-template-columns: minmax(150px, 1fr) minmax(150px, 1.4fr) minmax(170px, 1.4fr); align-items: center; gap: 10px }
.steps .acts { font-size: 13px }
@media (max-width: 680px) { .steps li { grid-template-columns: 1fr; gap: 4px; padding-bottom: 6px; border-bottom: 1px solid var(--line) } .steps li:last-child { border: 0 } .steps .ctr-m, .steps .dt, .steps .acts { grid-area: auto } }
.foes { list-style: none; margin: 4px 0 0; padding: 0; display: grid; gap: 6px }
.foes li { display: grid; grid-template-columns: minmax(90px, 1fr) auto minmax(120px, 1.2fr) minmax(170px, 1.4fr) 92px; align-items: center; gap: 10px;
  padding: 8px 10px; border-radius: 12px; background: var(--panel-2); font-size: 13.5px }
.foes li.is-weak { background: var(--warn-soft) }
.foe { font-weight: 800; display: flex; align-items: center; min-width: 0 }
.dexname { display: flex; align-items: center; gap: 4px } .arrow { color: var(--muted) }
.ctr-m { display: flex; align-items: center; font-weight: 700; min-width: 0 }
.dt { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 3px 8px }
.lab { font: 600 10px var(--mono); text-transform: uppercase; color: var(--muted) }
.mbar { height: 6px; border-radius: 99px; background: var(--line); overflow: hidden; min-width: 50px }
.mbar i { display: block; height: 100% }
.mbar.deal i { background: var(--good) } .mbar.take i { background: var(--bad) }
.mv { font: 600 12px var(--mono); font-variant-numeric: tabular-nums; text-align: right; min-width: 40px }
.wc { grid-column: 1 / -1; display: flex; flex-wrap: wrap; gap: 6px; margin-top: 2px }
.wc span { font: 700 11.5px var(--body); padding: 2px 9px; border-radius: 99px }
.wc-ok { background: var(--good-soft); color: var(--good) } .wc-no { background: var(--bad-soft); color: var(--bad) }
@media (max-width: 680px) { .wc { grid-area: auto } .foes li { grid-template-areas: "foe st" "ctr ctr" "dt dt" "wc wc" } .wc { grid-area: wc } }
.foes .st { font: 700 12px var(--body); color: var(--good); text-align: right }
.foes li.is-weak .st { color: var(--warn) }
@media (max-width: 680px) {
  .foes li { grid-template-columns: 1fr auto; grid-template-areas: "foe st" "ctr ctr" "dt dt" }
  .foe { grid-area: foe } .arrow { display: none } .ctr-m { grid-area: ctr } .dt { grid-area: dt } .foes .st { grid-area: st }
  .fc > summary { flex-wrap: wrap }
}
.bxmoves { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)) }
.bxl { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 14px 16px; box-shadow: var(--shadow); border-top: 4px solid var(--good) }
.bxl.out { border-top-color: var(--bad) }
.bxl h3 { display: flex; align-items: center; gap: 8px; margin-bottom: 8px }
.bxc { font: 700 12px var(--mono); background: var(--panel-2); border-radius: 99px; padding: 1px 8px }
.bxl ul { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px }
.bxl li { display: flex; align-items: center; gap: 8px; padding: 6px 10px; border-radius: 12px; background: var(--panel-2) }
.bxn { font: 700 12px var(--mono); color: var(--muted); min-width: 40px }
.bxl .blv { font: 600 12px var(--mono); color: var(--muted) }
.bxl .to { margin-left: auto; font: 700 12.5px var(--body); color: var(--good) }
.bxl.out .to { color: var(--bad) }
.bxl .none { margin: 0; color: var(--muted); font-size: 13.5px }
.tlx tbody tr { cursor: pointer }
.sheet { position: fixed; inset: 0; z-index: 50; display: grid; place-items: center } .sheet[hidden] { display: none }
.sheet-bg { position: absolute; inset: 0; background: rgba(10,14,20,.5) }
.sheet-card { position: relative; width: min(520px, calc(100% - 24px)); max-height: 86vh; overflow: auto; background: var(--panel); border-radius: 20px; padding: 18px 20px 20px; box-shadow: 0 20px 60px rgba(0,0,0,.35) }
@media (max-width: 680px) { .sheet { place-items: end center } .sheet-card { width: 100%; border-radius: 20px 20px 0 0; padding-bottom: calc(20px + env(safe-area-inset-bottom, 0px)) } }
.sheet-x { position: absolute; right: 12px; top: 10px; width: 34px; height: 34px; border-radius: 50%; border: 1px solid var(--line); background: var(--panel-2); color: var(--ink); font-size: 20px; cursor: pointer }
.ds-head { display: flex; align-items: center; gap: 12px; margin-bottom: 10px }
.ds-head .spr { width: 96px; height: 96px; margin: 0 }
.ds-head h3 { font-size: 21px }
.ds-sub { color: var(--muted); font-size: 13px }
.ds-stats { display: grid; grid-template-columns: repeat(6, 1fr); gap: 4px; margin: 8px 0 12px }
.ds-stats div { background: var(--panel-2); border-radius: 10px; text-align: center; padding: 4px 0; font: 700 14px var(--mono) }
.ds-stats small { display: block; font: 600 9.5px var(--mono); color: var(--muted); text-transform: uppercase }
.ds-sec { font: 600 10.5px var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin: 12px 0 6px }
.ds-c li { margin-bottom: 4px } .ds-c { margin: 0; padding-left: 18px; font-size: 13.5px }
.todos.pcards { display: grid !important; gap: 12px; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)) }
.tcard { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 12px 14px; box-shadow: var(--shadow); display: grid; gap: 8px; align-content: start }
.thead { display: flex; align-items: center; gap: 4px }
.thead > div { display: grid; min-width: 0 }
.thead b { font: 700 16px var(--display) }
.tplace { font: 600 11px var(--mono); color: var(--muted) }
.tlv { margin-left: auto; flex: none; font: 700 12px var(--mono); color: var(--warn); background: var(--warn-soft); border-radius: 99px; padding: 3px 9px }
.tfix { list-style: none; margin: 0; padding: 0; display: grid; gap: 4px }
.tfix li { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px; padding: 6px 10px; border-radius: 10px; background: var(--panel-2); font-size: 13.5px }
.tk { font: 600 10.5px var(--mono); text-transform: uppercase; letter-spacing: .06em; color: var(--muted); min-width: 52px }
.tr { color: var(--muted); font-size: 12.5px }
.tdone { margin: 0; color: var(--good); font-weight: 700; font-size: 13.5px }
.ckhead { display: flex; align-items: baseline; gap: 10px; margin-bottom: 10px }
.ckhead b { font: 700 28px var(--display); color: var(--good) }
.ckhead span { color: var(--muted); font-size: 13px }
.cks { list-style: none; margin: 0 0 8px; padding: 0; display: grid; gap: 6px }
.ck { display: flex; gap: 10px; align-items: flex-start; padding: 8px 10px; border-radius: 12px; background: var(--panel-2); font-size: 13.5px }
.ck .dot { flex: none; width: 10px; height: 10px; border-radius: 50%; margin-top: 5px; background: var(--good) }
.ck.warn .dot { background: var(--warn) } .ck.bad .dot { background: var(--bad) }
.ck.warn { background: var(--warn-soft) } .ck.bad { background: var(--bad-soft) }
.ck div { display: grid; gap: 2px } .ck div span { color: var(--muted); font-size: 12.5px }
.ckmore > summary, .ckref > summary { cursor: pointer; font: 700 14px var(--display) }
details.ckref { display: block }
.slot-sub { font-size: 12.5px; color: var(--muted); display: flex; gap: 8px; flex-wrap: wrap }
.slot-miss { color: var(--warn); font-weight: 700 }
.next { display: grid; grid-template-columns: 1fr auto; grid-template-areas: "k go" "t go" "s go"; gap: 2px 12px; text-decoration: none; color: var(--on-dex);
  background: linear-gradient(120deg, var(--dex-deep), var(--dex)); border-radius: 16px; padding: 14px 18px; box-shadow: var(--shadow) }
.next-k { grid-area: k; font: 600 11px var(--mono); letter-spacing: .1em; text-transform: uppercase; opacity: .85 }
.next b { grid-area: t; font: 700 20px var(--display) }
.next > span:nth-of-type(2) { grid-area: s; font-size: 13.5px; opacity: .92 }
.next-go { grid-area: go; align-self: center; font: 700 28px var(--display) }
@media (prefers-reduced-motion: no-preference) { .tabp:not([hidden]) { animation: rise .22s ease-out } @keyframes rise { from { transform: translateY(6px); opacity: .6 } to { transform: none; opacity: 1 } } }
.role-chip { display: inline-block; background: var(--accent-soft); color: var(--accent); font: 700 11.5px var(--body); letter-spacing: .02em; padding: 3px 10px; border-radius: 99px; white-space: nowrap }
.tier { width: auto !important; max-width: 44px; flex: none; justify-self: start; grid-template-columns: auto !important; border: 0 !important; overflow: visible !important; background-clip: padding-box }
@media (max-width: 680px) {
  .cft thead, .fplan thead { display: none }
  .cft, .cft tbody, .cft tr, .cft td, .fplan, .fplan tbody, .fplan tr, .fplan td { display: block; width: 100% }
  .cft tr, .fplan tr { padding: 10px 0; border-bottom: 1px solid var(--line) }
  .cft td, .fplan td { border: 0 !important; padding: 2px 0 }
  .cft td:first-child, .fplan td:first-child { font-size: 15.5px }
}
footer { max-width: 1120px; margin: 0 auto; padding: 0 max(16px, env(safe-area-inset-right, 0px)) 0 max(16px, env(safe-area-inset-left, 0px)) }
</style>'''
DEXJS = r'''<script id="dex-js">
(function(){
  var el = document.getElementById('dexdata'); if (!el) return;
  var D = {}; try { D = JSON.parse(el.textContent); } catch (e) { return; }
  var sheet = document.getElementById('dexsheet'), body = document.getElementById('ds-body'), last = null;
  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function open(name){
    var d = D[name]; if (!d) return;
    var st = ['HP','Atk','Def','SpA','SpD','Spe'].map(function(k){ return '<div><small>'+k+'</small>'+d.b[k]+'</div>'; }).join('');
    var ctr = Object.keys(d.c).map(function(f){ return '<li><b>'+esc(f)+'</b>: '+d.c[f].map(esc).join(', ')+'</li>'; }).join('');
    body.innerHTML = '<div class="ds-head"><i class="spr sp-'+d.sp+'" aria-hidden="true"></i><div><h3 id="ds-name">'+esc(name)+'</h3>'
      + '<div class="ds-sub"><span class="tier t'+d.t+'">'+d.t+'</span> score '+d.s.toFixed(2)+' · '+d.ty.map(function(t){return t[0]+t.slice(1).toLowerCase();}).join('/')+' · '+esc(d.w)+'</div>'
      + '<div class="ds-sub">'+esc(d.m)+'</div></div></div><div class="ds-stats">'+st+'</div>'
      + '<div class="ds-sec">Ideal build</div><div>'+esc(d.a)+(d.n?' · '+esc(d.n):'')+(d.e?' · '+esc(d.e):'')+'</div><div>'+d.mv.map(esc).join(' / ')+'</div>'
      + '<div class="ds-sec">Counters in Chapter 9</div>'+(ctr ? '<ul class="ds-c">'+ctr+'</ul>' : '<div class="ds-sub">None of the remaining hard-fight Pokémon</div>');
    last = document.activeElement; sheet.hidden = false; sheet.querySelector('.sheet-x').focus();
  }
  function close(){ sheet.hidden = true; if (last) last.focus(); }
  document.addEventListener('click', function(e){
    if (e.target.closest('[data-close]')) { close(); return; }
    var tr = e.target.closest('.tlx tbody tr'); if (!tr) return;
    var b = tr.querySelector('b'); if (b) open(b.textContent.trim());
  });
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape' && !sheet.hidden) close(); });
})();
</script>
'''
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
page = page.replace('</body>', DEXJS + '</body>') if '</body>' in page else page + DEXJS
_sp = SP.css_for(page)
page = page.replace('</style>', '</style>\n<style id="sprites">.spr{display:inline-block;flex:none;background:center/contain no-repeat;image-rendering:pixelated}'
                    '.spr-s{width:28px;height:28px;margin-right:4px}.spr-m{width:44px;height:44px;margin-right:8px}.spr-l{width:88px;height:88px}'
                    + _sp + '</style>', 1) if _sp else page
open(OUT, 'w', encoding='utf-8').write(page)
print('theme: party slots', len(st['team']), '· nav', [k for k, _ in NAV])
