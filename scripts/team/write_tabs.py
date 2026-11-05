"""Add the Chapter 8 team-builder tabs to the user's workbook (v48 -> v49)."""
import json, sys, re
from copy import copy
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import ColorScaleRule, CellIsRule
from openpyxl.comments import Comment

SRC, FINAL, OUT, SENS = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
data = json.load(open(FINAL))
sens = json.load(open(SENS))
wb = load_workbook(SRC)

F = Font(name='Arial', size=10)
FB = Font(name='Arial', size=10, bold=True)
FT = Font(name='Arial', size=14, bold=True)
FS = Font(name='Arial', size=12, bold=True, color='1F3864')
FN = Font(name='Arial', size=9, color='595959')
FBLUE = Font(name='Arial', size=10, color='0000FF')
HF = Font(name='Arial', size=10, bold=True, color='FFFFFF')
H_BLUE = PatternFill('solid', fgColor='1F3864')
H_GREEN = PatternFill('solid', fgColor='375623')
H_GOLD = PatternFill('solid', fgColor='7F6000')
FILL_KEEP = PatternFill('solid', fgColor='E2EFDA')
FILL_CHANGE = PatternFill('solid', fgColor='FCE4D6')
FILL_IN = PatternFill('solid', fgColor='DDEBF7')
WRAP = Alignment(wrap_text=True, vertical='top')
TOP = Alignment(vertical='top')
BATTLE_KEYS = [p['key'] for p in data['plans']]
BATTLE_SHORT = {'texen': 'Texen', 'groudon': 'Groudon', 'crawli': 'Crawli', 'eli': 'Eli & Sharon',
                'giratina': 'Rift Giratina', 'geara': 'Geara & Zetta', 'amber': 'Amber'}
WEIGHTS = {'texen': 1, 'groudon': 1, 'crawli': 1, 'eli': 1, 'giratina': 1, 'geara': 1.5, 'amber': 1}


def put(ws, r, c, v, font=F, fill=None, align=None, fmt=None):
    cell = ws.cell(row=r, column=c, value=v)
    cell.font = font
    if fill:
        cell.fill = fill
    if align:
        cell.alignment = align
    if fmt:
        cell.number_format = fmt
    return cell


def header(ws, r, cols, fill=H_BLUE, start=1):
    for i, h in enumerate(cols):
        put(ws, r, start + i, h, HF, fill, Alignment(wrap_text=True, vertical='center'))


def widths(ws, ws_widths):
    for i, w in enumerate(ws_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def evs_txt(e):
    order = ['HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe']
    return ' / '.join(f"{e[k]} {k}" for k in order if e.get(k))


# ======================================================================= Ch8 Team Builder
ws = wb.create_sheet('Ch8 Team Builder', index=1)
widths(ws, [6, 24, 18, 9, 9, 16, 22, 24, 30, 16, 16, 16, 16, 40, 46, 60])
put(ws, 1, 1, 'Chapter 8 Team Builder – best six from your 406 mons vs every Chapter 8 hard-mode boss', FT)
put(ws, 2, 1, ('Built 2026-11-05 from your 23:15 export (406 mons) + this workbook\'s rules (cap 55, level-up/Egg/TM17 Protect/'
               'TM54 False Swipe + known moves only, no Life Orb, Megas locked, no Trick Room yet) + the Rejuvenation wiki: '
               'Classic-mode boss teams, field effects, base stats and learnsets. Every owned mon was evaluated fully evolved '
               'at Lv 55 against all 41 boss Pokémon with a damage calc that applies each battle\'s field.'), FN)
ws.merge_cells('A2:P2'); ws['A2'].alignment = WRAP; ws.row_dimensions[2].height = 38

r = 4
put(ws, r, 1, '1) Verdict – recommended six vs your current party (score = coverage of each boss team; higher is better)', FS)
r += 1
header(ws, r, ['', 'Battle', 'Field', 'Format', 'Weight', 'Current party', 'Recommended six', 'Change', 'Change %'], H_BLUE)
first = r + 1
for p in data['plans']:
    r += 1
    put(ws, r, 2, p['label'], FB)
    put(ws, r, 3, p['field'])
    put(ws, r, 4, p['format'])
    put(ws, r, 5, WEIGHTS[p['key']], FBLUE, fmt='0.0')
    put(ws, r, 6, p['score_current'], FBLUE, fmt='0.00')
    put(ws, r, 7, p['score_best'], FBLUE, fmt='0.00')
    put(ws, r, 8, f'=G{r}-F{r}', fmt='+0.00;-0.00;0.00')
    put(ws, r, 9, f'=IF(F{r}=0,"",G{r}/F{r}-1)', fmt='+0%;-0%;0%')
last = r
r += 1
put(ws, r, 2, 'Weighted chapter score', FB)
put(ws, r, 6, f'=SUMPRODUCT(F{first}:F{last},$E${first}:$E${last})/SUM($E${first}:$E${last})', FB, fmt='0.00')
put(ws, r, 7, f'=SUMPRODUCT(G{first}:G{last},$E${first}:$E${last})/SUM($E${first}:$E${last})', FB, fmt='0.00')
put(ws, r, 8, f'=G{r}-F{r}', FB, fmt='+0.00;-0.00;0.00')
put(ws, r, 9, f'=IF(F{r}=0,"",G{r}/F{r}-1)', FB, fmt='+0%;-0%;0%')
ws.conditional_formatting.add(f'H{first}:H{r}', CellIsRule(operator='greaterThan', formula=['0'], fill=FILL_KEEP))
ws.conditional_formatting.add(f'H{first}:H{r}', CellIsRule(operator='lessThan', formula=['0'], fill=FILL_CHANGE))
r += 1
put(ws, r, 2, ('Blue numbers are engine outputs (hardcoded). Weight: Geara & Zetta counts 1.5x because it is 12 mons. '
               'Groudon is low for every team: it is a 2-shield boss in sun – see the swap-in below.'), FN)
ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=16)

# ---------------- recommended six
r += 2
put(ws, r, 1, '2) Recommended six – builds (legal under your move rules)', FS)
r += 1
cols = ['Slot', 'Pokémon', 'Where it is now', 'Lv now', 'Lv to gain', 'Ability', 'Nature', 'EVs', 'Item',
        'Move 1', 'Move 2', 'Move 3', 'Move 4', 'Moves you know now', 'What to change in game', 'Why it made the six']
header(ws, r, cols, H_GREEN)
cur_names = {m['owned_as'] for m in data['current']}
order = sorted(data['best'], key=lambda m: -m['solo_total'])
for i, m in enumerate(order, 1):
    r += 1
    where = f"{m['where']} (#{m['dump']})"
    changes = []
    if m['where'] != 'Party':
        changes.append(f"Move into party from {m['where']}")
    if m['ability_change']:
        changes.append(f"Ability Capsule: {m['ability_now']} -> {m['ability']}")
    now_moves = set(m['moves_now'] or [])
    learn = [x for x in m['moves'] if x not in now_moves]
    drop = [x for x in (m['moves_now'] or []) if x not in m['moves']]
    if learn:
        changes.append('Learn: ' + ', '.join(learn))
    if drop:
        changes.append('Drop: ' + ', '.join(drop))
    if m['levels_needed']:
        changes.append(f"Level {m['level']} -> 55")
    if m['evolve']:
        changes.append('Evolve: ' + m['evolve'])
    fill = FILL_KEEP if m['where'] == 'Party' else FILL_IN
    put(ws, r, 1, i, FB)
    put(ws, r, 2, m['name'], FB, fill)
    put(ws, r, 3, where, fill=fill)
    put(ws, r, 4, m['level'])
    put(ws, r, 5, f'=MAX(0,VALUE(Settings!$B$3)-D{r})')
    put(ws, r, 6, m['ability'] + (' (capsule)' if m['ability_change'] else ''))
    put(ws, r, 7, m['nature'])
    put(ws, r, 8, evs_txt(m['evs']))
    put(ws, r, 9, m['item'], align=WRAP)
    for j, mv in enumerate((m['moves'] + ['', '', '', ''])[:4]):
        put(ws, r, 10 + j, mv, FB if mv not in now_moves else F, FILL_CHANGE if mv and mv not in now_moves else None)
    put(ws, r, 14, ' / '.join(m['moves_now'] or []), align=WRAP)
    put(ws, r, 15, '; '.join(changes) or 'Nothing to change', align=WRAP)
    put(ws, r, 16, m['why'], align=WRAP)
    ws.row_dimensions[r].height = 52
r += 1
put(ws, r, 2, ('Orange move = not on that mon right now (learn it: level-up at or below 55, or Egg move). EVs/nature assume you can '
               're-spread as you have been doing. Items: kept what each mon already holds; Sitrus Berry otherwise (your rule). '
               'Hariyama is in your Overflow box (Lv 45) – promote it.'), FN)
ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=16)

# ---------------- out of the party
r += 2
put(ws, r, 1, '3) Who leaves the current party, and why', FS)
r += 1
header(ws, r, ['', 'Pokémon', 'Chapter score (solo)', 'Best battle', 'Worst battle', 'Verdict'], H_BLUE)
best_names = {m['owned_as'] for m in data['best']}
for m in sorted(data['current'], key=lambda x: -x['solo_total']):
    r += 1
    solo = m['solo']
    bb = max(solo, key=solo.get)
    wb_ = min((k for k in solo if k != 'groudon'), key=solo.get)
    keep = m['owned_as'] in best_names
    put(ws, r, 2, m['name'], FB, FILL_KEEP if keep else FILL_CHANGE)
    put(ws, r, 3, m['solo_total'], FBLUE, fmt='0.00')
    put(ws, r, 4, f"{BATTLE_SHORT[bb]} ({solo[bb]:.2f})")
    put(ws, r, 5, f"{BATTLE_SHORT[wb_]} ({solo[wb_]:.2f})")
    verdict = {
        'Gholdengo': 'Bench to Active. Strong into Texen (Make It Rain 1.5x on Big Top) and Crawli, but Ground/Fire/Ghost/Dark is exactly what Chapter 8 throws: Groudon, Typhlosion Eruption (~2x HP on Volcanic Top), Krookodile, Marowak, Amber\'s all-Fire team. Bring it back for Texen.',
        'Lapras (Aevian Form)': 'Bench to Active. No Guard Sing is great utility, but at cap 55 its Rock moves are Rock Slide/Rock Tomb only (Stone Edge is Lv 65), and Steel/Water/Ground/Grass/Fighting weaknesses line up with Texen, Groudon and Geara.',
        'Leavanny (Aevian Form)': 'Bench to Active. Intimidate is good, but Dragon Claw/X-Scissor do too little to Chapter 8\'s Steel/Fairy/Fire mons and it is frail to Rock/Flying/Fire (all boosted on Mountain and Volcanic Top).',
        'Whiscash': 'Bench to Active. Crest is nice but Earthquake is 0.25x on Swamp and Wasteland, Water is 0.5x in Groudon\'s sun and 0.9x on Volcanic Top, and Earthquake hits your partner.',
    }.get(m['name'], 'KEEP – one of the most consistent picks across every battle.' if keep else '')
    put(ws, r, 6, verdict, align=WRAP)
    ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=16)
    ws.row_dimensions[r].height = 42 if not keep else 18

# ---------------- per battle
r += 2
put(ws, r, 1, '4) Battle-by-battle: who leads, and the best one-mon swap if you want to tune for that fight', FS)
r += 1
header(ws, r, ['', 'Battle', 'Field', 'Lead(s)', '', 'Best swap-in', 'Replaces', 'Where it is', 'Gain', 'Other options'], H_BLUE)
for p in data['plans']:
    r += 1
    put(ws, r, 2, p['label'], FB)
    put(ws, r, 3, p['field'])
    put(ws, r, 4, ' + '.join(p['leads']))
    ws.merge_cells(start_row=r, start_column=4, end_row=r, end_column=5)
    if p['swaps']:
        s0 = p['swaps'][0]
        put(ws, r, 6, s0['bring'], FB)
        put(ws, r, 7, s0['replace'])
        put(ws, r, 8, f"{s0['where']} Lv{s0['level']}")
        put(ws, r, 9, s0['gain'], FBLUE, fmt='+0.00')
        put(ws, r, 10, '; '.join(f"{s['bring']} for {s['replace']} (+{s['gain']:.2f})" for s in p['swaps'][1:]), align=WRAP)
        ws.merge_cells(start_row=r, start_column=10, end_row=r, end_column=16)
    else:
        put(ws, r, 6, 'No swap helps', FN)

# ---------------- robustness
r += 2
put(ws, r, 1, '5) How sure is this? – the search re-run with 8 different scoring weightings', FS)
r += 1
header(ws, r, ['', 'Pokémon', 'Picked in', 'Of', 'Share', 'Read'], H_BLUE)
counts = sens['counts']
n_runs = sens['runs']
for name, cnt in sorted(counts.items(), key=lambda x: -x[1]):
    r += 1
    put(ws, r, 2, name, FB)
    put(ws, r, 3, cnt, FBLUE)
    put(ws, r, 4, n_runs, FBLUE)
    put(ws, r, 5, f'=C{r}/D{r}', fmt='0%')
    put(ws, r, 6, f'=IF(E{r}>=0.85,"Core – lock it in",IF(E{r}>=0.5,"Strong","Situational"))')
r += 1
put(ws, r, 2, ('Weightings varied: how much a second answer to each boss mon counts (0.2–0.5), the penalty for mons that get '
               'OHKO\'d (0.15–0.6) and the bonus for doubles support (0–0.07).'), FN)
ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=16)

# ---------------- caveats
r += 2
put(ws, r, 1, '6) Assumptions & limits (read before acting)', FS)
for t in [
    'Damage is an average-roll estimate at Lv 55 vs the wiki\'s Classic-mode sets; field boosts, STAB, type, abilities (e.g. Skill Link, Pixilate, Intimidate, Levitate, Flash Fire, Solid Rock, Multiscale) and type items are applied. Crits, stat stages, weather other than Groudon\'s sun, Reflect/Light Screen, and partner AI (Aelita, Venam, Melia) are not.',
    'Guts / Toxic Boost are only counted when the mon holds a Flame/Toxic Orb (Corrupted Cave poisons you anyway).',
    'Evolutions that need an item (e.g. Ursaring -> Ursaluna with a Peat Block) were kept out of the six. Ursaluna would be the #1 pick if you get a Peat Block – see Ch8 Roster Ratings.',
    'Your move rules were applied as written in Legend: level-up at or below 55 (incl. evolution / Lv 1 moves), Egg moves, TM17 Protect, TM54 False Swipe, plus anything the mon already knows. No other TMs, tutors or relearner.',
    'Boss lists come from the wiki pages Texen, Cera, Crawli, Eli, Valor Summit, Zetta/Geara and Amber (Classic Mode tab). The Garufa ruin guards, Tommen and the optional Kyogre are not in the score.',
    'The engine scores raw matchups; it does not play out turns. Use the Ch8 Boss Matchups tab to sanity-check the specific threats before a fight.',
]:
    r += 1
    put(ws, r, 2, '• ' + t, align=WRAP)
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=16)
    ws.row_dimensions[r].height = 30
ws.freeze_panes = 'A4'

# ======================================================================= Ch8 Boss Matchups
ws = wb.create_sheet('Ch8 Boss Matchups', index=2)
widths(ws, [22, 6, 16, 16, 15, 44, 7, 24, 18, 9, 9, 24, 18, 9, 22, 9])
put(ws, 1, 1, 'Chapter 8 boss matchups – each boss mon vs the recommended six (Classic / hard mode)', FT)
put(ws, 2, 1, 'Damage % = estimated share of the target\'s HP from one hit (average roll, field applied). Speed = boss stat at its level. "Faster?" = your answer outspeeds it.', FN)
r = 4
for p in data['plans']:
    put(ws, r, 1, f"{p['label']}  –  {p['field']} ({p['format']})", FS)
    r += 1
    put(ws, r, 1, p['notes'], FN)
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=16)
    ws.row_dimensions[r].height = 26
    ws.cell(row=r, column=1).alignment = WRAP
    r += 1
    header(ws, r, ['Boss Pokémon', 'Lv', 'Type', 'Ability', 'Item', 'Moves', 'Speed',
                   'Your best answer', 'With', 'Damage', 'Faster?', 'Biggest threat to', 'Using', 'Damage',
                   'Safest switch-in', 'Takes'])
    for c in range(8, 12):
        ws.cell(row=r, column=c).fill = H_GREEN
    for c in range(12, 15):
        ws.cell(row=r, column=c).fill = H_GOLD
    top = r + 1
    for f in p['foes']:
        r += 1
        put(ws, r, 1, f['foe'], FB)
        put(ws, r, 2, f['lvl'])
        put(ws, r, 3, f['types'])
        put(ws, r, 4, f['ability'])
        put(ws, r, 5, f['item'])
        put(ws, r, 6, ', '.join(f['moves']))
        put(ws, r, 7, f['spe'])
        put(ws, r, 8, f['answer'], FB)
        put(ws, r, 9, f['answer_move'])
        put(ws, r, 10, f['answer_dmg'] / 100, FBLUE, fmt='0%')
        put(ws, r, 11, 'Yes' if f['answer_faster'] else 'No')
        put(ws, r, 12, f['threat_to'])
        put(ws, r, 13, f['threat_move'])
        put(ws, r, 14, f['threat_dmg'] / 100, FBLUE, fmt='0%')
        put(ws, r, 15, f['safest'])
        put(ws, r, 16, f['safest_dmg'] / 100, FBLUE, fmt='0%')
    ws.conditional_formatting.add(f'J{top}:J{r}', ColorScaleRule(start_type='num', start_value=0.3, start_color='F8696B',
                                                                mid_type='num', mid_value=0.8, mid_color='FFEB84',
                                                                end_type='num', end_value=1.2, end_color='63BE7B'))
    ws.conditional_formatting.add(f'N{top}:N{r}', ColorScaleRule(start_type='num', start_value=0.3, start_color='63BE7B',
                                                                mid_type='num', mid_value=0.7, mid_color='FFEB84',
                                                                end_type='num', end_value=1.0, end_color='F8696B'))
    r += 2
ws.freeze_panes = 'B4'

# ======================================================================= Ch8 Roster Ratings
ws = wb.create_sheet('Ch8 Roster Ratings', index=3)
cols = ['Rank', 'Evaluated as (fully evolved)', 'Owned as', 'Where', 'Dump #', 'Lv', 'Evolution needed',
        'Needs item to evolve', 'Ability used', 'Capsule?', 'Types', 'BST', 'Chapter attacks'] + \
       [BATTLE_SHORT[k] for k in BATTLE_KEYS] + ['Chapter score', 'In recommended six', 'In current party']
widths(ws, [6, 30, 24, 9, 7, 5, 26, 16, 14, 8, 16, 6, 40] + [9] * 7 + [10, 10, 10])
put(ws, 1, 1, 'Chapter 8 roster ratings – every owned mon (one row per species/form/ability), scored solo vs each boss team', FT)
put(ws, 2, 1, 'Battle weights (edit row 3 to re-weight; Chapter score recalculates):', FN)
for j, k in enumerate(BATTLE_KEYS):
    put(ws, 3, 14 + j, WEIGHTS[k], FBLUE, fmt='0.0').fill = PatternFill('solid', fgColor='FFFF00')
header(ws, 4, cols, H_BLUE)
for c in range(14, 14 + 7 + 1):
    ws.cell(row=4, column=c).fill = H_GREEN
rows = sorted(data['roster'], key=lambda x: -x['total'])
for i, x in enumerate(rows, start=5):
    put(ws, i, 1, f'=RANK(U{i},$U$5:$U${len(rows) + 4})')
    put(ws, i, 2, x['name'], FB if x['in_best'] else F, FILL_KEEP if x['in_best'] else None)
    put(ws, i, 3, x['owned_as'])
    put(ws, i, 4, x['where'])
    put(ws, i, 5, x['dump'])
    put(ws, i, 6, x['level'])
    put(ws, i, 7, x['evolve'])
    put(ws, i, 8, x['gate'])
    put(ws, i, 9, x['ability'])
    put(ws, i, 10, 'Yes' if x['ability_change'] else '')
    put(ws, i, 11, x['types'])
    put(ws, i, 12, x['bst'])
    put(ws, i, 13, ', '.join(x['attacks']))
    for j, k in enumerate(BATTLE_KEYS):
        put(ws, i, 14 + j, x['solo'][k], FBLUE, fmt='0.00')
    put(ws, i, 21, f'=SUMPRODUCT(N{i}:T{i},$N$3:$T$3)/SUM($N$3:$T$3)', FB, fmt='0.00')
    put(ws, i, 22, 'Yes' if x['in_best'] else '')
    put(ws, i, 23, 'Yes' if x['in_party'] else '')
end = len(rows) + 4
ws.auto_filter.ref = f'A4:W{end}'
ws.freeze_panes = 'C5'
ws.conditional_formatting.add(f'N5:U{end}', ColorScaleRule(start_type='percentile', start_value=5, start_color='F8696B',
                                                          mid_type='percentile', mid_value=50, mid_color='FFEB84',
                                                          end_type='percentile', end_value=95, end_color='63BE7B'))

# ======================================================================= Changelog + Legend
cl = wb['Changelog']
nr = cl.max_row + 1
best_list = ', '.join(m['name'] for m in sorted(data['best'], key=lambda m: -m['solo_total']))
put(cl, nr, 1, 'v63 (file v49)')
put(cl, nr, 2, '2026-11-05')
put(cl, nr, 3, (f"Chapter 8 team analysis vs every Classic-mode boss (Texen, Cera's Groudon, Crawli, Eli & Sharon, Rift Giratina, "
                f"Geara & Zetta, Amber) with field effects, from the wiki. New tabs: Ch8 Team Builder, Ch8 Boss Matchups, "
                f"Ch8 Roster Ratings. Recommended six: {best_list} (keeps Annihilape and Golisopod-Aevian; benches "
                f"Gholdengo, Lapras-Aevian, Leavanny-Aevian and Whiscash to Active; promotes Hariyama from Overflow). "
                f"Weighted chapter score {data['score_current']:.2f} -> {data['score_best']:.2f}. Party / Ideal Builds tabs "
                f"NOT changed yet – waiting for your OK."), align=WRAP)
for c in range(1, 4):
    src = cl.cell(row=nr - 1, column=c)
    cl.cell(row=nr, column=c).font = copy(src.font) if src.font else F
lg = wb['Legend']
nr = lg.max_row + 2
put(lg, nr, 1, ('Ch8 Team Builder / Ch8 Boss Matchups / Ch8 Roster Ratings (v49) – Chapter 8 boss analysis: recommended six with '
                'builds, every boss mon vs that six (best answer, biggest threat), and every owned mon scored solo per boss. '
                'Engine inputs are blue (hardcoded); battle weights in Ch8 Roster Ratings row 3 are editable (yellow).'), F, align=WRAP)

wb.save(OUT)
print('saved', OUT)
