"""Chapter brief (Vincent, 23 Nov): for every fight left this chapter, everything that makes it hard and how to beat it in its
format, and which of our Pokemon answer each point. Feeds the Core tab (all fights left, core of 3) and the Flex tab (next fight, six).
Sources: gamedata.fight_mons (their exact sets), fieldtext + fieldnotetext (field rules), the engine native run (damage / speed, field,
levels, our real builds). Every factor = dict(id, fight, kind, foe, text, how, need); cover(factor, members) -> [(member, how)].
A member = dict(name, types, ability, moves (ids), spe, mu {foe: {off, deff, faster}})."""
import json, os, re, math, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gamedata'))
import gamedata as G
import bosses
from fields import GUIDE_TO_FE

MV = json.load(open('gamedata/movetext.json'))
FT_ALL = json.load(open('gamedata/fieldtext.json'))
BYNAME = {v['name'].lower(): k for k, v in MV.items()}
def mid(n): return BYNAME.get((n or '').lower()) or (n or '').upper().replace(' ', '').replace('-', '')
B9 = {b[0]: b for b in bosses.CH9}
TITLE = {b[0]: b[1].split(' – ')[0] for b in bosses.CH9}

SETUP = {'WORKUP': 1, 'HOWL': 1, 'SWORDSDANCE': 2, 'NASTYPLOT': 2, 'DRAGONDANCE': 1, 'SHIFTGEAR': 1, 'CALMMIND': 1, 'BULKUP': 1,
         'QUIVERDANCE': 1, 'COIL': 1, 'CURSE': 1, 'GROWTH': 1, 'TAILGLOW': 3, 'SHELLSMASH': 2, 'VICTORYDANCE': 1, 'CLANGOROUSSOUL': 1,
         'FILLETAWAY': 2, 'TIDYUP': 1, 'BELLYDRUM': 6, 'GEOMANCY': 2, 'AGILITY': 0, 'ROCKPOLISH': 0, 'FELLSTINGER': 3}
RESET = {'HAZE', 'CLEARSMOG', 'ROAR', 'WHIRLWIND', 'DRAGONTAIL', 'CIRCLETHROW', 'ENCORE', 'PERISHSONG', 'TOPSYTURVY', 'SPECTRALTHIEF'}
PARA = {'THUNDERWAVE', 'GLARE', 'NUZZLE', 'STUNSPORE', 'ZAPCANNON'}
SPEED_D = {'TAILWIND', 'TRICKROOM', 'ICYWIND', 'ELECTROWEB', 'BULLDOZE', 'STICKYWEB'} | PARA
HEAL = {'RECOVER', 'ROOST', 'SLACKOFF', 'SOFTBOILED', 'MOONLIGHT', 'SYNTHESIS', 'MORNINGSUN', 'WISH', 'SHOREUP', 'STRENGTHSAP', 'MILKDRINK', 'DRAINPUNCH', 'GIGADRAIN', 'HORNLEECH'}
ABS = {'VOLTABSORB': 'ELECTRIC', 'LIGHTNINGROD': 'ELECTRIC', 'MOTORDRIVE': 'ELECTRIC', 'WATERABSORB': 'WATER', 'STORMDRAIN': 'WATER', 'DRYSKIN': 'WATER',
       'FLASHFIRE': 'FIRE', 'WELLBAKEDBODY': 'FIRE', 'SAPSIPPER': 'GRASS', 'LEVITATE': 'GROUND', 'EARTHEATER': 'GROUND'}
FOE_AB = {'SOUNDPROOF': 'immune to sound moves', 'LEVITATE': 'immune to Ground', 'MOTORDRIVE': 'absorbs Electric (+Speed)',
          'LIGHTNINGROD': 'absorbs Electric and pulls Electric moves to itself in doubles', 'VOLTABSORB': 'absorbs Electric',
          'STURDY': 'survives any one hit from full', 'ADAPTABILITY': 'STAB x2: hits very hard', 'SURGESURFER': 'Speed x2 on Electric Terrain',
          'PLUS': 'raises the crowd Hype on entry', 'FLASHFIRE': 'absorbs Fire', 'WATERABSORB': 'absorbs Water', 'SAPSIPPER': 'absorbs Grass'}
ITEMS = {'Choice Scarf': 'Speed x1.5 (locked into one move)', 'Focus Sash': 'survives one hit from full HP', 'Assault Vest': 'special bulk x1.5: hit it physically',
         'Synthetic Seed': 'field seed: boosts it on entry',
         'Elemental Seed': 'field seed: boosts it on entry', 'Magical Seed': 'field seed', 'Telluric Seed': 'field seed'}
MULTI = {'BONERUSH', 'PINMISSILE', 'ICICLESPEAR', 'ROCKBLAST', 'BULLETSEED', 'TAILSLAP', 'SCALESHOT', 'DOUBLEHIT', 'DUALWINGBEAT',
         'SURGINGSTRIKES', 'POPULATIONBOMB', 'TRIPLEAXEL', 'WATERSHURIKEN', 'DRAGONDARTS', 'DOUBLEKICK', 'ARMTHRUST', 'BULLETPUNCH'} - {'BULLETPUNCH'}


def field_notes(fe):
    """the field's rules that change decisions: end-of-turn damage, speed, blocked moves, sleep (fieldnotetext)"""
    out = []
    try:
        src = open('gamedata/fieldnotetext.rb', encoding='utf-8').read()
    except Exception:
        return out
    base = re.sub(r'\d+$', '', fe or '')
    for m in re.finditer(r'PBFieldNote\.new\(:(%s\d?),\s*"([^"]*)"(?:,\s*"([^"]*)")?' % re.escape(base), src):
        if '\\' in m.group(0): continue
        cl = lambda x: re.sub(r'<[^>]+>', '', re.sub(r'<icon=type(\w+)[^>]*>', lambda q: q.group(1).title(), x or ''))
        short = cl(m.group(2)).replace(' . . .', '').strip()
        long_ = cl(m.group(3)).strip().split('. ')[0].split('{')[0].rstrip(' ,:')
        txt = long_ if len(short.split()) < 4 else (short.split('{')[0] + ' ' + long_).strip()
        txt = re.sub(r'\s+', ' ', txt.replace('...', ' ')).replace('when when', 'when').replace('unless unless', 'unless').replace('unless Water or unless', 'unless').replace(', or the abilities', ' or Swift Swim / Surge Surfer').strip()
        if re.search(r'End of turn|Speed .*x0|Sleep|fail', txt) and 'Ground attacks' not in txt and 'Prevents' not in txt:
            out.append(re.sub(r'\s+', ' ', txt.replace('...', ' ').replace('  ', ' ')).strip())
    return list(dict.fromkeys(out))[:6]


def brief(fk, speeds=None):
    b = B9[fk]; fmt = b[3]; field = b[2]; fe = GUIDE_TO_FE.get(field)
    ft = FT_ALL.get(fe or '', {}) if fe else {}
    tb = {t: float(k) for k, ts in (ft.get('typeBoosts') or {}).items() for t in ts}
    sb = set(ft.get('statusBuffs') or [])
    foes = G.fight_mons(fk)
    for f in foes: f['spe'] = (speeds or {}).get(f['name'])
    F = []
    def add(kind, foe, text, how, need=1, **kw):
        F.append(dict(id=f'{fk}:{kind}:{foe}:{len(F)}', fight=fk, kind=kind, foe=foe, text=text, how=how, need=need, **kw))
    for f in foes:
        ms = [mid(x) for x in f['moves']]; ab = (f.get('ability') or '').upper().replace(' ', ''); it = f.get('item') or ''
        st = max([SETUP[m] + (1 if m in sb else 0) for m in ms if m in SETUP] or [-1])
        if st >= 0:
            sm = next(MV[m]['name'] for m in ms if m in SETUP)
            add('setup', f['name'], f"{f['name']}: {sm} (+{st}{' here' if any(m in sb for m in ms if m in SETUP) else ''})",
                'KO it before it boosts twice, or Haze / Clear Smog / Encore / Unaware / phazing', stage=st)
        if any(m in HEAL for m in ms):
            add('heal', f['name'], f"{f['name']} heals ({', '.join(MV[m]['name'] for m in ms if m in HEAL)})", 'One-shot it, or Knock Off / Heal Block / Toxic')
        pr = [m for m in ms if int(MV.get(m, {}).get('priority') or 0) > 0 and int(MV.get(m, {}).get('basedamage') or 0) > 0]
        if pr: add('priority', f['name'], f"{f['name']}: priority {MV[pr[0]]['name']}", 'Bulk that takes it, or Psychic Terrain / Quick Guard', move=pr[0])
        spr = [m for m in ms if MV.get(m, {}).get('target') in ('AllOpposing', 'AllNonUsers') and int(MV.get(m, {}).get('basedamage') or 0) > 0]
        if fmt == 'Doubles' and spr:
            add('spread', f['name'], f"{f['name']}: spread {', '.join(MV[m]['name'] for m in spr)}", 'Wide Guard, or resist / immune to it', moves=spr)
        if ab in FOE_AB:
            add('ability', f['name'], f"{f['name']}: {f.get('ability')} ({FOE_AB[ab]})",
                'Hit it with something its ability does not block' if ab in ABS or ab == 'SOUNDPROOF' else 'Plan around it', ability=ab)
        if it in ITEMS or 'Seed' in it or it.endswith(' Z') or (it.endswith('ite') and it != 'Eviolite'):
            why = ITEMS.get(it) or ('Z-move: one huge hit, once' if ' Z' in it else 'Mega Evolves' if it.endswith('ite') else 'field seed: boosts it on entry')
            add('item', f['name'], f"{f['name']}: {it} ({why})", 'Protect / resist the Z-move; multi-hit or priority breaks Sash / Sturdy' if ('Z' in it or 'Sash' in it) else 'Plan around it', item=it)
    # speed: foes at 150+ Speed (Scarf counted)
    for f in foes:
        sp = f.get('spe') or 0
        if sp >= 150:
            add('speed', f['name'], f"{f['name']}: Speed {sp}" + (' (Choice Scarf)' if f.get('item') == 'Choice Scarf' else ''),
                'Singles: outspeed and KO, priority, or paralyse it then outspeed' if fmt == 'Singles' else 'Doubles: Tailwind / Trick Room / Icy Wind / Electroweb / paralysis',
                spe=sp)
    # their main attack types after the field (2+ users or field-boosted)
    use = {}
    for f in foes:
        for x in f['moves']:
            m = mid(x); d = MV.get(m) or {}
            if int(d.get('basedamage') or 0) > 0: use.setdefault(d.get('type'), set()).add(f['name'])
    for t, who in sorted(use.items(), key=lambda kv: -len(kv[1])):
        if t in tb and tb[t] == 0: continue
        if len(who) >= 3 or (tb.get(t, 1) > 1 and len(who) >= 1):
            add('type', t, f"{t.title()} attacks from {len(who)}" + (f" (x{tb[t]:g} on this field)" if tb.get(t, 1) > 1 else ''),
                'Two of yours resist or are immune', need=2, atype=t)
    # field: what it does to us
    if fe:
        blocked = [t for t, k in tb.items() if k == 0]
        for t in blocked: add('fieldblock', field, f"{field}: {t.title()} attacks fail", f'Do not rely on {t.title()} moves', atype=t)
        sound = tb.get('soundmove')
        boosted = sorted(t for t, k in tb.items() if k > 1 and t != 'soundmove')
        add('fieldexploit', field, f"{field} boosts: " + ', '.join([t.title() for t in boosted] + (['sound moves'] if sound else [])) + ' x' + '/'.join(sorted({f'{k:g}' for t, k in tb.items() if k > 1})),
            'Bring a Pokemon whose best hit is field-boosted', boosted=boosted, sound=bool(sound))
        for n in field_notes(fe):
            add('fieldnote', field, n, 'Plan around it')
    return dict(fight=fk, title=TITLE[fk], format=fmt, field=field, fe=fe, foes=[dict(name=f['name'], sid=f.get('species'), form=f.get('form'),
                item=f.get('item'), ability=f.get('ability'), moves=f['moves'], types=f['types'], spe=f.get('spe')) for f in foes], factors=F, tb=tb)


def foe_speeds(E, fk):
    bt = next((b for b in E.battles if b['key'] == fk), None)
    return {f['name']: int(f['stats']['Spe'] * (1.5 if f.get('item') == 'Choice Scarf' else 1)) for f in (bt['foes'] if bt else [])}


def eff(E, atype, types, ab=''):
    if ABS.get(ab) == atype: return 0.0
    return E.chart_eff(atype, types)


def cover(fc, mem, E, tb=None, fmt='Singles'):
    """who on the team answers factor fc, and how -> [(name, how)]"""
    out = []
    k = fc['kind']; foe = fc.get('foe')
    for m in mem:
        mu = (m.get('mu') or {}).get(foe) or {}
        off, dff, fast = mu.get('off', 0), mu.get('deff', 100), mu.get('faster', False)
        mv = set(m['moves'])
        if k == 'setup':
            mult = (2 + fc.get('stage', 1)) / 2
            if fast and off >= 100: out.append((m['name'], 'outspeeds and one-shots it'))
            elif dff * mult < 50 and off >= 50: out.append((m['name'], f'takes the boosted hit ({int(dff * mult)}%)'))
            elif mv & RESET or m['ability'] == 'UNAWARE': out.append((m['name'], MV[next(iter(mv & RESET))]['name'] if mv & RESET else 'Unaware'))
        elif k == 'heal':
            if off >= 100: out.append((m['name'], 'one-shots it'))
            elif mv & {'KNOCKOFF', 'HEALBLOCK', 'TOXIC'}: out.append((m['name'], MV[next(iter(mv & {'KNOCKOFF', 'HEALBLOCK', 'TOXIC'}))]['name']))
        elif k == 'priority':
            if dff < 50: out.append((m['name'], f'takes {int(dff)}% from it'))
        elif k == 'spread':
            if 'WIDEGUARD' in mv: out.append((m['name'], 'Wide Guard'))
            elif all(eff(E, MV[x]['type'], m['types'], m['ability']) < 1 for x in fc['moves']): out.append((m['name'], 'resists it'))
        elif k == 'ability' and fc.get('ability') == 'STURDY':
            if m['ability'] == 'SKILLLINK' or mv & MULTI: out.append((m['name'], 'multi-hit breaks it'))
        elif k == 'ability':
            if off >= 60: out.append((m['name'], f'still hits it for {int(off)}%'))
        elif k == 'item':
            if 'Sash' in fc['item'] or 'Sturdy' in fc['item']:
                if m['ability'] == 'SKILLLINK' or mv & MULTI: out.append((m['name'], 'multi-hit breaks it'))
            elif off >= 100 or (fast and off >= 60): out.append((m['name'], f'beats it ({int(off)}%)'))
        elif k == 'speed':
            if fast and off >= 100: out.append((m['name'], 'outspeeds and one-shots it'))
            pr = [x for x in mv if int((MV.get(x) or {}).get('priority') or 0) > 0 and int((MV.get(x) or {}).get('basedamage') or 0) > 0 and x != 'FAKEOUT']
            if pr and off >= 60: out.append((m['name'], f"priority {MV[pr[0]]['name']}"))
            tool = (mv & SPEED_D) if fmt == 'Doubles' else (mv & (PARA | {'TRICKROOM', 'ICYWIND', 'ELECTROWEB', 'STICKYWEB'}))
            if tool:
                t0 = next(iter(tool))
                if t0 in PARA:   # paralysis needs someone who then outspeeds (Speed / 2) and hits hard
                    after = [o['name'] for o in mem if o['spe'] > fc.get('spe', 999) / 2 and ((o.get('mu') or {}).get(foe) or {}).get('off', 0) >= 100]
                    if after: out.append((m['name'], f"{MV[t0]['name']}, then {after[0]} one-shots it"))
                else: out.append((m['name'], MV[t0]['name']))
        elif k == 'type':
            e = eff(E, fc['atype'], m['types'], m['ability'])
            if e < 1: out.append((m['name'], 'immune' if e == 0 else 'resists'))
        elif k == 'fieldblock':
            if not any((MV.get(x) or {}).get('type') == fc['atype'] for x in mv if int((MV.get(x) or {}).get('basedamage') or 0) > 0):
                continue
            out.append((m['name'], f"has {fc['atype'].title()} moves: useless here"))
        elif k == 'fieldnote' and 'End of turn' in fc['text'] and 'Poison or Steel' in fc['text']:
            if {'POISON', 'STEEL', 'FLYING'} & set(m['types']) or m['ability'] == 'LEVITATE': out.append((m['name'], 'immune to it'))
        elif k == 'fieldexploit':
            best = None
            for x in mv:
                d = MV.get(x) or {}
                if int(d.get('basedamage') or 0) <= 0: continue
                if d.get('type') in fc.get('boosted', []) or (fc.get('sound') and d.get('soundmove')):
                    best = d['name']; break
            if best: out.append((m['name'], best))
    # dedupe by member
    seen, res = set(), []
    for n, h in out:
        if n not in seen: seen.add(n); res.append((n, h))
    return res


def ok(fc, cov):
    if fc['kind'] == 'fieldblock': return not cov          # nobody relies on a blocked type
    if fc['kind'] == 'fieldnote': return None               # info only
    return len(cov) >= fc.get('need', 1)


LABEL = [('setup', 'Setup'), ('speed', 'Faster than you'), ('priority', 'Priority'), ('spread', 'Spread moves'), ('type', 'Their main attacks'),
         ('ability', 'Abilities'), ('item', 'Items'), ('heal', 'Healing'), ('fieldexploit', 'Field boosts'), ('fieldblock', 'Field blocks'),
         ('fieldnote', 'Field rules')]


def group(fs):
    """factors (with ok / cov) -> one row per kind: dict(kind, label, items, ok (True / False / None), how)"""
    out = []
    for k, lab in LABEL:
        xs = [x for x in fs if x['kind'] == k]
        if not xs: continue
        oks = [x.get('ok') for x in xs if x.get('ok') is not None]
        out.append(dict(kind=k, label=lab, items=xs, how=xs[0]['how'], ok=None if not oks and 'ok' in xs[0] and xs[0].get('ok') is None else (all(oks) if oks else None)))
    return out


def short(x):   # the factor without its foe prefix
    t = x['text']
    return t.split(': ', 1)[1] if x.get('foe') and t.startswith(x['foe'] + ': ') else t


import html as _html
_E = _html.escape


def render(fs, post, disp=lambda x: x, miss='flex', todo=False):   # one row per kind of threat; post = after the pick: ✓ / ✗ with who answers each one
    li = ''
    for g in group(fs):
        sub = ''
        for x in g['items']:
            who = '' if x.get('foe') in (None, '') or x['kind'] in ('type', 'fieldexploit', 'fieldblock', 'fieldnote') else x['foe'] + ': '
            if post and x.get('ok') is not None:
                ans = ', '.join(f'{disp(a)} ({b})' for a, b in x['cov'][:2]) if x['ok'] and x['kind'] != 'fieldblock' else ('nobody relies on it' if x['ok'] else (miss if x['kind'] != 'fieldblock' else ', '.join(disp(a) for a, _ in x['cov'])))
                sub += f'<div class="pans {"cok" if x["ok"] else "cno"}">{"✓" if x["ok"] else "✗"} {_E(who + short(x) if who else x["text"])}: {_E(ans)}</div>'
            else:
                sub += f'<div class="pans">{_E(who + short(x) if who else x["text"])}</div>'
        st_ = '' if (not post or g['ok'] is None) else (' pw-ok' if g['ok'] else ' pw-no')
        mark = '☐' if todo else '•' if (not post or g['ok'] is None) else ('✓' if g['ok'] else '✗')
        li += f'<li class="{st_.strip() or "pw-nt"}"><b>{mark}</b> <b>{_E(g["label"])}</b>' + ('' if (post or todo) else f' <span class="pmuted">{_E(g["how"])}</span>') + sub + '</li>'
    return f'<ul class="pwin">{li}</ul>'


ROLE_WORD = {'A': 'Win con', 'B': 'Enabler', 'C': 'Wallbreaker', 'D': 'Pivot', 'E': 'Tech'}


def good_for(tags, fmt='Singles', field_move=None, beats=None, answers=None):
    """23 Nov (Vincent): what this Pokemon is good for, max 3 short chips, same on the Core and Flex tabs:
    its win-con job (wincon_tags), how it uses the field, then what it answers / who it beats"""
    t_ = (tags or {}).get('s' if fmt == 'Singles' else 'd') or (tags or {}).get('s') or []
    out = [f'{ROLE_WORD[k]}: {w}' for k, w in t_[:1]]
    if field_move: out.append(f'Field: {field_move}')
    if answers: out.append('Answers ' + ', '.join(answers[:2]) + (f' +{len(answers) - 2}' if len(answers) > 2 else ''))
    if beats and len(out) < 3: out.append('Beats ' + ', '.join(beats[:2]) + (f' +{len(beats) - 2}' if len(beats) > 2 else ''))
    return out[:3]
