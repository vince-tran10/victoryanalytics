"""Build the Rejuvenation Pokemon workbook."""
import json, re, sys, os, glob
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.utils import get_column_letter, coordinate_to_tuple
from openpyxl.worksheet.views import Pane, Selection


def freeze(ws, ref):
    row, col = coordinate_to_tuple(ref)
    sv = ws.sheet_view
    sv.pane = Pane(xSplit=col - 1 or None, ySplit=row - 1 or None, topLeftCell=ref,
                   activePane='bottomRight' if col > 1 else 'bottomLeft', state='frozen')
    sv.selection = [Selection(pane=sv.pane.activePane, activeCell=ref, sqref=ref)]

sys.path.insert(0, os.path.dirname(__file__))
from dataset import Data
from recommend import recommend, STATS, AB_FLAT

BASE = sys.argv[1]
OUT = sys.argv[2]
D = Data(BASE)

FONT = Font(name='Arial', size=10)
BOLD = Font(name='Arial', size=10, bold=True)
HFONT = Font(name='Arial', size=10, bold=True, color='FFFFFF')
HFILL = PatternFill('solid', fgColor='1F3864')
RFILL = PatternFill('solid', fgColor='E2EFDA')   # recommendation columns
TITLE = Font(name='Arial', size=14, bold=True)
WRAP = Alignment(wrap_text=True, vertical='top')
TYPE_COLORS = {'Normal': 'A8A77A', 'Fire': 'EE8130', 'Water': '6390F0', 'Electric': 'F7D02C', 'Grass': '7AC74C',
               'Ice': '96D9D6', 'Fighting': 'C22E28', 'Poison': 'A33EA1', 'Ground': 'E2BF65', 'Flying': 'A98FF3',
               'Psychic': 'F95587', 'Bug': 'A6B91A', 'Rock': 'B6A136', 'Ghost': '735797', 'Dragon': '6F35FC',
               'Dark': '705746', 'Steel': 'B7B7CE', 'Fairy': 'D685AD'}
TYPE_FILLS = {k: PatternFill('solid', fgColor=v) for k, v in TYPE_COLORS.items()}
ATK_TYPES = list(TYPE_COLORS)


def cell(ws, v, font=FONT, fill=None, align=None, fmt=None):
    c = WriteOnlyCell(ws, value=v)
    c.font = font
    if fill:
        c.fill = fill
    if align:
        c.alignment = align
    if fmt:
        c.number_format = fmt
    return c


def header(ws, cols, widths):
    ws.append([cell(ws, h, HFONT, HFILL, Alignment(wrap_text=True, vertical='center')) for h in cols])
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def tname(t):
    return t.capitalize() if t else ''


# ------------------------------------------------------------- ability text
def clean_wiki(t):
    t = re.sub(r'\{\{bp\|([^}|]*)\|?([^}]*)\}\}', lambda m: (m.group(2) or m.group(1)).replace('_', ' '), t)
    t = re.sub(r'\{\{[^}]*\}\}', '', t)
    t = re.sub(r'\[https?://\S+ ([^\]]+)\]', r'\1', t)
    t = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', t)
    t = re.sub(r"'''?", '', t)
    t = re.sub(r'<br\s*/?>', ' ', t)
    t = re.sub(r'<[^>]+>', '', t)
    return re.sub(r'\s+', ' ', t).strip()


ab_desc = {}
for fpath in glob.glob(f'{BASE}/raw/abil/*.json'):
    j = json.load(open(fpath))
    key = j['name'].replace('-', '').upper()
    eff = next((e['short_effect'] for e in j.get('effect_entries', []) if e['language']['name'] == 'en'), '')
    if not eff:
        eff = next((e['flavor_text'] for e in reversed(j.get('flavor_text_entries', []))
                    if e['language']['name'] == 'en'), '')
    ab_desc[key] = (re.sub(r'\s+', ' ', eff), 'Mainline (PokeAPI)')
cust = json.load(open(f'{BASE}/raw/custabil/wikitext.json'))
for key, w in cust.items():
    m = re.search(r'==\s*Effect\s*==(.*?)(?:\n==[^=]|\Z)', w, re.S)
    body = m.group(1) if m else w
    body = re.split(r'\n===', body)[0]
    body = re.sub(r'=+\s*In battle\s*=+', '', body)
    ab_desc[key] = (clean_wiki(body), 'Rejuvenation custom (wiki)')
ab_desc['GORILLATACTICS'] = ('Boosts the Pokémon\'s Attack by 50%, but only allows the use of the first move selected.', 'Mainline (Bulbapedia summary)')
ab_desc['ASONECHILLING'] = ab_desc.get('ASONEGLASTRIER', ('Combines Unnerve and Chilling Neigh.', 'Mainline (PokeAPI)'))
ab_desc['ASONEGRIM'] = ab_desc.get('ASONESPECTRIER', ('Combines Unnerve and Grim Neigh.', 'Mainline (PokeAPI)'))


# ------------------------------------------------------------- per-entry records
def defensive(types):
    res = {}
    for at in ATK_TYPES:
        mult = 1.0
        for dt in types:
            d = D.chart.get(dt, {})
            A = at.upper()
            if A in d.get('Immunities', []):
                mult *= 0
            elif A in d.get('Weaknesses', []):
                mult *= 2
            elif A in d.get('Resistances', []):
                mult *= 0.5
        res[at] = mult
    return res


records, learn_rows = [], []
used_abilities = set()
for e in D.entries:
    f = D.form(e['sid'], e['form'])
    bs = dict(zip(STATS, f['BaseStats']))
    types_up = [t.upper() for t in e['page_types'] if t]
    abil = list(f.get('Abilities') or [])
    hidden = f.get('HiddenAbility') or ''
    used_abilities.update(abil + ([hidden] if hidden else []))
    ls = D.learnset(e['sid'], e['form'])
    learn = {m for m, _, _ in ls}
    nfe = D.is_nfe(e['sid'], e['form'])
    try:
        weight = float(f.get('Weight') or 0)
    except ValueError:
        weight = 0
    rec = recommend(bs, types_up, abil + ([hidden] if hidden else []), learn, D.moves, D.chart, weight, nfe)
    ev = f.get('EffortPoints') or [0] * 6
    ev_txt = ', '.join(f'{v} {s}' for s, v in zip(STATS, ev) if v)
    de = defensive([tname(t) for t in types_up])
    label = e['label'] or ''
    records.append(dict(e=e, f=f, bs=bs, types=[tname(t) for t in types_up], abil=abil, hidden=hidden,
                        rec=rec, ev_yield=ev_txt, de=de, nfe=nfe, evo=D.evolves_to(e['sid'], e['form']),
                        n_moves=len(learn)))
    # learnset rows: one row per move, methods merged
    bymove = {}
    for mid, method, detail in ls:
        bymove.setdefault(mid, []).append((method, detail))
    order = {'Level-up': 0, 'TM': 1, 'Tutor': 2, 'TM/Tutor': 3, 'Move Relearner': 4, 'Egg': 5}
    for mid, meths in bymove.items():
        m = D.moves[mid]
        lvls = [d for mm, d in meths if mm == 'Level-up']
        parts = []
        for mm, d in sorted(meths, key=lambda x: order.get(x[0], 9)):
            if mm == 'Level-up':
                parts.append('Evolution' if d == 'Evo' else f'Lv {d}')
            elif mm == 'TM':
                parts.append(d)
            elif mm == 'Tutor':
                parts.append(f'Tutor ({d})' if d else 'Tutor')
            elif mm == 'Egg':
                parts.append(f'Egg (via {d})' if d else 'Egg')
            else:
                parts.append(mm)
        first_lv = None
        for d in lvls:
            v = 0 if d == 'Evo' else int(d)
            first_lv = v if first_lv is None else min(first_lv, v)
        learn_rows.append((e['dex'], e['name'], label, m['MoveName'], tname(m['Type']), m['Category'],
                           m['Strength'], m['Accuracy'], m['PP'],
                           'Yes' if m['Type'] in types_up and m['Category'] != 'Status' else '',
                           '; '.join(dict.fromkeys(parts)), first_lv))

wb = Workbook(write_only=True)

# ------------------------------------------------------------- README
ws = wb.create_sheet('README')
ws.column_dimensions['A'].width = 26
ws.column_dimensions['B'].width = 120
rows = [
    ('Pokémon Rejuvenation – Team Builder Database', None),
    (None, None),
    ('What this is', 'Every Pokémon listed on the Rejuvenation wiki "Pokémon Locations" page (1,157 entries incl. regional/Aevian forms), '
                     'with base stats, types, abilities, full learnsets, and a suggested competitive set (role, ability, nature, EV spread, item, 4 moves).'),
    ('Source – list & locations', 'https://rejuvenation.wiki.gg/wiki/Pokémon_Locations (pulled via the wiki API)'),
    ('Source – stats/moves', 'The wiki\'s game-data modules, which are generated from the game files: Module:Database/Species, '
                             'Module:Database/Moves, Module:Database/TMs, Module:Database/Names, Module:Database/Types, Module:Database/Forms. '
                             'These are the same data the wiki uses to build each Pokémon page, so Rejuvenation-specific changes (Aevian forms, custom moves, '
                             'changed movepools) are reflected.'),
    ('Source – ability text', 'Mainline abilities: PokeAPI short effect text (pokeapi.co). Rejuvenation-custom abilities: the "Effect" section of each '
                              'ability\'s page on rejuvenation.wiki.gg. Note: Rejuvenation tweaks some mainline abilities; the mainline text is not always exact.'),
    (None, None),
    ('Tabs', None),
    ('Pokemon', 'One row per entry. Grey/blue columns = game data. Green columns = suggested set. BST and EV Total are live formulas. '
                'Use the filter arrows to sort by stat, type, role, etc.'),
    ('Learnsets', 'Every move each Pokémon can learn (one row per Pokémon + move), with how it is learned (level, TM number, tutor, egg, relearner), '
                  'type, category, power, accuracy, PP and whether it gets STAB. Filter column A/B to see one Pokémon\'s full movepool.'),
    ('Moves', 'All 950 moves in the game data, with Rejuvenation descriptions and a live count of how many listed Pokémon learn each.'),
    ('Abilities', 'Every ability that appears, with its effect and the rating used by the recommender.'),
    ('Natures', 'The 25 natures and their stat effects.'),
    (None, None),
    ('How sets are suggested', 'These are rules-based starting points, not tier-list gospel – adjust for your team and the field effects you\'ll face.'),
    ('1. Role', 'Physical vs Special focus from Atk vs SpA (Huge/Pure Power doubles Atk). Bulky Pokémon with modest offense become Physical/Special '
                'Walls (by whichever defence is higher). Others are Attackers / Setup Sweepers, split by speed (Fast ≥90, Mid 70–89, Slow <70).'),
    ('2. Ability', 'Each legal ability is scored = strategic value (e.g. Regenerator, Intimidate, Multiscale) + how much it actually raises the damage of '
                   'the best moveset (e.g. Technician only scores high if strong ≤60 BP moves are in the learnset; Huge Power doubles damage). '
                   'All candidate scores are shown in the "Ability Scores" column.'),
    ('3. Nature / EVs', 'Attackers with base Spe ≥55: 252 Atk|SpA / 252 Spe / 4 HP with Jolly/Timid (base Spe ≥70) or Adamant/Modest. Slower attackers: '
                        '252 HP / 252 Atk|SpA. Walls: 252 HP / 252 Def|SpD with Impish/Bold or Careful/Calm depending on their attack. Very slow '
                        'Pokémon get a Trick Room note.'),
    ('4. Moves', 'Damaging moves are scored by power × accuracy × STAB × ability boost × attacking stat, with penalties for recharge/charge turns, '
                 'recoil, self stat-drops and locking moves, and bonuses for pivoting (U-turn etc.), Knock Off and priority on slower Pokémon. '
                 'The best STAB move is taken first; remaining slots maximise type coverage across all 18 types. Setup sweepers get their best boosting move; '
                 'walls get recovery + status + hazard/utility + STAB attack. "Alternatives" lists the next-best options.'),
    ('5. Item', 'Eviolite for anything that can still evolve; Flame/Toxic Orb for Guts/Toxic Boost/Poison Heal etc.; Life Orb or Leftovers for setup; '
                'Choice Band/Specs/Scarf for non-setup attackers; Leftovers/Black Sludge for walls.'),
    (None, None),
    ('Not included', 'Mega / Giga / battle-only forms (they aren\'t separate entries on the Locations page). Learnsets for those forms match their base form.'),
    ('Rebuilding', 'The scripts in this repo (fetch_data.sh, luaparse.py, build_entries.py, build_workbook.py) re-pull the wiki data and regenerate this file.'),
]
for a, b in rows:
    if a and b is None:
        ws.append([cell(ws, a, TITLE if a.startswith('Pokémon Rej') else BOLD)])
    elif a is None:
        ws.append([])
    else:
        ws.append([cell(ws, a, BOLD, align=WRAP), cell(ws, b, FONT, align=WRAP)])

# ------------------------------------------------------------- Pokemon
ws = wb.create_sheet('Pokemon')
cols = ['Dex #', 'Pokémon', 'Form', 'Type 1', 'Type 2', 'Where to Find', 'Ability 1', 'Ability 2', 'Hidden Ability',
        'HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe', 'BST', 'EV Yield', 'Weak 4x', 'Weak 2x', 'Resists', 'Immune',
        'Evolves Into', 'Moves Learnable',
        'Suggested Role', 'Suggested Ability', 'Nature', 'HP EV', 'Atk EV', 'Def EV', 'SpA EV', 'SpD EV', 'Spe EV',
        'EV Total', 'Item', 'Move 1', 'Move 2', 'Move 3', 'Move 4', 'Alternative Moves', 'Notes', 'Ability Scores']
widths = [7, 14, 13, 9, 9, 45, 14, 14, 15, 5, 5, 5, 5, 5, 5, 6, 14, 14, 26, 30, 14, 26, 9,
          28, 16, 20, 6, 6, 6, 6, 6, 6, 7, 16, 16, 16, 16, 16, 40, 30, 40]
header(ws, cols, widths)
freeze(ws, 'C2')
REC_START = cols.index('Suggested Role') + 1
n = len(records)
for i, r in enumerate(records, start=2):
    e, rec, bs = r['e'], r['rec'], r['bs']
    de = r['de']
    w4 = ', '.join(t for t, m in de.items() if m >= 4)
    w2 = ', '.join(t for t, m in de.items() if m == 2)
    rs = ', '.join(t + (' (¼)' if m == 0.25 else '') for t, m in de.items() if 0 < m < 1)
    im = ', '.join(t for t, m in de.items() if m == 0)
    t1 = r['types'][0] if r['types'] else ''
    t2 = r['types'][1] if len(r['types']) > 1 else ''
    abil = r['abil'] + ['', '']
    evs = rec['evs']
    row = [
        cell(ws, e['dex']), cell(ws, e['name'], BOLD), cell(ws, e['label'] or ''),
        cell(ws, t1, fill=TYPE_FILLS.get(t1)), cell(ws, t2, fill=TYPE_FILLS.get(t2)),
        cell(ws, e['loc'], align=Alignment(wrap_text=False)),
        cell(ws, D.nm(abil[0])), cell(ws, D.nm(abil[1]) if abil[1] != abil[0] else ''), cell(ws, D.nm(r['hidden'])),
    ] + [cell(ws, bs[s]) for s in STATS] + [
        cell(ws, f'=SUM(J{i}:O{i})', BOLD),
        cell(ws, r['ev_yield']), cell(ws, w4), cell(ws, w2), cell(ws, rs), cell(ws, im), cell(ws, r['evo']),
        cell(ws, f'=COUNTIFS(Learnsets!$A:$A,$A{i},Learnsets!$B:$B,$B{i},Learnsets!$C:$C,$C{i}&"")'),
        cell(ws, rec['role'], BOLD, RFILL), cell(ws, D.nm(rec['ability']) if rec['ability'] else '', fill=RFILL),
        cell(ws, rec['nature'], fill=RFILL),
    ] + [cell(ws, evs.get(s, 0) or None, fill=RFILL) for s in STATS] + [
        cell(ws, f'=SUM(AA{i}:AF{i})', fill=RFILL),
        cell(ws, rec['item'], fill=RFILL),
    ] + [cell(ws, mv, fill=RFILL) for mv in rec['moves']] + [
        cell(ws, ', '.join(rec['alts']), fill=RFILL), cell(ws, rec['notes'], fill=RFILL),
        cell(ws, ', '.join(f'{D.nm(a)} {s:g}' for s, a in rec['ability_scores']), fill=RFILL),
    ]
    ws.append(row)
ws.auto_filter.ref = f'A1:{get_column_letter(len(cols))}{n + 1}'
ws.conditional_formatting.add(f'J2:O{n + 1}', ColorScaleRule(start_type='num', start_value=20, start_color='F8696B',
                                                             mid_type='num', mid_value=85, mid_color='FFEB84',
                                                             end_type='num', end_value=150, end_color='63BE7B'))
ws.conditional_formatting.add(f'P2:P{n + 1}', ColorScaleRule(start_type='min', start_color='F8696B',
                                                             mid_type='percentile', mid_value=50, mid_color='FFEB84',
                                                             end_type='max', end_color='63BE7B'))

# ------------------------------------------------------------- Learnsets
ws = wb.create_sheet('Learnsets')
header(ws, ['Dex #', 'Pokémon', 'Form', 'Move', 'Type', 'Category', 'Power', 'Accuracy', 'PP', 'STAB',
            'How Learned', 'Level (if level-up)'], [7, 14, 13, 18, 9, 9, 7, 8, 5, 6, 50, 10])
freeze(ws, 'E2')
for lr in learn_rows:
    dex, nm, form, mv, typ, cat, pw, acc, pp, stab, how, lv = lr
    def num(x):
        try:
            v = int(x)
            return v if v > 0 else None
        except (TypeError, ValueError):
            return None
    pwv = num(pw)
    pw_out = pwv if (pwv and pwv > 1) else ('Varies' if pw == '1' else '—')
    acc_out = num(acc) or '—'
    ws.append([cell(ws, dex), cell(ws, nm), cell(ws, form), cell(ws, mv, BOLD), cell(ws, typ, fill=TYPE_FILLS.get(typ)),
               cell(ws, cat), cell(ws, pw_out), cell(ws, acc_out), cell(ws, num(pp)), cell(ws, stab), cell(ws, how),
               cell(ws, lv)])
ws.auto_filter.ref = f'A1:L{len(learn_rows) + 1}'

# ------------------------------------------------------------- Moves
ws = wb.create_sheet('Moves')
header(ws, ['Move', 'Type', 'Category', 'Power', 'Accuracy', 'PP', 'Priority', 'Effect Chance %', 'Target', 'Flags',
            'TM / Tutor', 'Description', '# Listed Pokémon That Learn It'],
       [20, 9, 9, 7, 8, 5, 7, 8, 16, 26, 22, 80, 12])
freeze(ws, 'B2')
tutors = D.tms.get('TUTORS', {})
mv_rows = sorted(D.moves.items(), key=lambda kv: kv[1]['MoveName'])
for i, (mid, m) in enumerate(mv_rows, start=2):
    def num(x):
        try:
            return int(x)
        except (TypeError, ValueError):
            return None
    p = num(m['Strength'])
    tmn = D.tms.get(mid) if isinstance(D.tms.get(mid), str) else ''
    tut = tutors.get(mid)
    src = ', '.join(x for x in [tmn, ('Tutor: ' + ', '.join(tut)) if isinstance(tut, list) else ''] if x)
    ws.append([cell(ws, m['MoveName'], BOLD), cell(ws, tname(m['Type']), fill=TYPE_FILLS.get(tname(m['Type']))),
               cell(ws, m['Category']), cell(ws, p if p and p > 1 else ('Varies' if p == 1 else '—')),
               cell(ws, num(m['Accuracy']) or '—'), cell(ws, num(m['PP'])), cell(ws, num(m.get('Priority')) or 0),
               cell(ws, num(m.get('Chance'))), cell(ws, m.get('Target')), cell(ws, ', '.join(m.get('DataFlags') or [])),
               cell(ws, src), cell(ws, m['Description']),
               cell(ws, f'=COUNTIF(Learnsets!$D:$D,A{i})')])
ws.auto_filter.ref = f'A1:M{len(mv_rows) + 1}'

# ------------------------------------------------------------- Abilities
ws = wb.create_sheet('Abilities')
header(ws, ['Ability', 'Effect', 'Source of Text', 'Recommender Rating (-10..10)', 'Rating Applies To',
            '# Listed Pokémon With It'], [20, 100, 24, 12, 12, 12])
freeze(ws, 'B2')
APPLY = {'any': 'Any role', 'att': 'Attackers', 'def': 'Walls', 'phys': 'Physical attackers', 'spec': 'Special attackers'}
ab_sorted = sorted(used_abilities, key=lambda a: D.nm(a))
for i, a in enumerate(ab_sorted, start=2):
    desc, src = ab_desc.get(a, ('', ''))
    flat, app = AB_FLAT.get(a, (0, 'any'))
    note = APPLY.get(app, app)
    if a in ('TECHNICIAN', 'IRONFIST', 'STRONGJAW', 'MEGALAUNCHER', 'SHARPNESS', 'TOUGHCLAWS', 'RECKLESS', 'SHEERFORCE',
             'ADAPTABILITY', 'HUGEPOWER', 'PUREPOWER', 'AERILATE', 'PIXILATE', 'REFRIGERATE', 'GALVANIZE', 'SKILLLINK',
             'TINTEDLENS', 'PARENTALBOND', 'GORILLATACTICS', 'HUSTLE', 'WATERBUBBLE', 'TRANSISTOR', 'DRAGONSMAW',
             'STEELWORKER', 'PUNKROCK', 'ROCKYPAYLOAD', 'SOLARPOWER', 'GUTS', 'TOXICBOOST', 'FLAREBOOST', 'LIQUIDVOICE'):
        note += ' + scored by damage boost'
    ws.append([cell(ws, D.nm(a), BOLD), cell(ws, desc, align=Alignment(wrap_text=True, vertical='top')),
               cell(ws, src), cell(ws, flat), cell(ws, note),
               cell(ws, f'=COUNTIF(Pokemon!$G:$I,A{i})')])
ws.auto_filter.ref = f'A1:F{len(ab_sorted) + 1}'

# ------------------------------------------------------------- Natures
ws = wb.create_sheet('Natures')
header(ws, ['Nature', 'Raises (+10%)', 'Lowers (-10%)', 'Typical Use'], [12, 14, 14, 50])
NAT = [('Hardy', '', '', 'Neutral'), ('Docile', '', '', 'Neutral'), ('Serious', '', '', 'Neutral'),
       ('Bashful', '', '', 'Neutral'), ('Quirky', '', '', 'Neutral'),
       ('Lonely', 'Atk', 'Def', 'Mixed / physical attacker that ignores Def'),
       ('Brave', 'Atk', 'Spe', 'Trick Room physical attacker'),
       ('Adamant', 'Atk', 'SpA', 'Physical attacker (power over speed)'),
       ('Naughty', 'Atk', 'SpD', 'Mixed physical attacker'),
       ('Bold', 'Def', 'Atk', 'Physical wall that attacks specially'),
       ('Relaxed', 'Def', 'Spe', 'Trick Room physical wall'),
       ('Impish', 'Def', 'SpA', 'Physical wall that attacks physically'),
       ('Lax', 'Def', 'SpD', 'Rarely used'),
       ('Timid', 'Spe', 'Atk', 'Fast special attacker'),
       ('Hasty', 'Spe', 'Def', 'Fast mixed attacker'),
       ('Jolly', 'Spe', 'SpA', 'Fast physical attacker'),
       ('Naive', 'Spe', 'SpD', 'Fast mixed attacker'),
       ('Modest', 'SpA', 'Atk', 'Special attacker (power over speed)'),
       ('Mild', 'SpA', 'Def', 'Mixed special attacker'),
       ('Quiet', 'SpA', 'Spe', 'Trick Room special attacker'),
       ('Rash', 'SpA', 'SpD', 'Mixed special attacker'),
       ('Calm', 'SpD', 'Atk', 'Special wall that attacks specially'),
       ('Gentle', 'SpD', 'Def', 'Rarely used'),
       ('Sassy', 'SpD', 'Spe', 'Trick Room special wall'),
       ('Careful', 'SpD', 'SpA', 'Special wall that attacks physically')]
for nrow in NAT:
    ws.append([cell(ws, nrow[0], BOLD)] + [cell(ws, x) for x in nrow[1:]])

wb.save(OUT)
print('wrote', OUT, len(records), 'pokemon rows,', len(learn_rows), 'learnset rows')
