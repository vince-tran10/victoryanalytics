"""Condensed Chapter 8 report: team table, Active-box tier list, to-do list, hidden metadata."""
import json, sys, html

ROWS, F9N, F9S, F9D, OUT = sys.argv[1:6]
rows = json.load(open(ROWS))
fn, fs, fd = (json.load(open(p)) for p in (F9N, F9S, F9D))
E = html.escape
TYPE = {'Normal': ('#A8A77A', '#1d1d12'), 'Fire': ('#EE8130', '#2a1200'), 'Water': ('#6390F0', '#0a1530'),
        'Electric': ('#F7D02C', '#2b2300'), 'Grass': ('#7AC74C', '#132608'), 'Ice': ('#96D9D6', '#0d2a29'),
        'Fighting': ('#C22E28', '#ffffff'), 'Poison': ('#A33EA1', '#ffffff'), 'Ground': ('#E2BF65', '#2b2208'),
        'Flying': ('#A98FF3', '#1a1036'), 'Psychic': ('#F95587', '#2e0414'), 'Bug': ('#A6B91A', '#1c2003'),
        'Rock': ('#B6A136', '#221d05'), 'Ghost': ('#735797', '#ffffff'), 'Dragon': ('#6F35FC', '#ffffff'),
        'Dark': ('#705746', '#ffffff'), 'Steel': ('#B7B7CE', '#1b1b2a'), 'Fairy': ('#D685AD', '#2b0c1c')}
SHORT = {'texen': 'Texen', 'guard1': 'Guard #1', 'guard2': 'Guard #2', 'tommen': 'Tommen', 'groudon': 'Groudon',
         'crawli': 'Crawli', 'neved': 'Neved', 'eli': 'Eli & Sharon', 'jenner': 'Jenner', 'geara': 'Geara & Zetta',
         'giratina': 'Giratina', 'amber': 'Amber'}


def chips(types):
    out = []
    for t in [x for x in types.split('/') if x]:
        bg, fg = TYPE.get(t, ('#888', '#fff'))
        out.append(f'<span class="type" style="background:{bg};color:{fg}">{E(t)}</span>')
    return ''.join(out)


def disp(n):
    return (n.replace(' (Aevian Form Male)', '-Aevian').replace(' (Aevian Form)', '-Aevian')
             .replace(' (Icy Aevian Form)', '-Aevian (Icy)').replace(' (Hisuian Form)', '-Hisui')
             .replace(' (Lunatone Dominant Fusion)', '-Idol').replace(' (Solrock Dominant Fusion)', '-Idol'))


# ---------------------------------------------------------------- 1) team
# (role, name, types, ability, nature, evs, item, moves[(move, is_new)], change notes)
TEAM = [
    ('Lead', 'Annihilape', 'Fighting/Ghost', 'Defiant', 'Adamant', '252 Atk / 252 Spe / 4 HP', 'Black Belt',
     [('Close Combat', 0), ('Shadow Punch', 0), ('Fire Punch', 0), ('Protect', 0)], []),
    ('Lead', 'Gholdengo', 'Steel/Ghost', 'Good as Gold', 'Modest', '252 HP / 252 SpA / 4 SpD', 'Metal Coat',
     [('Make It Rain', 0), ('Shadow Ball', 0), ('Recover', 0), ('Protect', 0)], []),
    ('Mid', 'Rhyperior', 'Ground/Rock', 'Solid Rock', 'Adamant', '252 HP / 252 Atk / 4 SpD', 'Hard Stone',
     [('Stone Edge', 2), ('Headlong Rush', 0), ('Slack Off', 0), ('Protect', 0)],
     ['Item: Focus Sash → Hard Stone (take it from Lapras-Aevian). Stone Edge 1.2x; Rhyperior is too bulky to need a Sash.', 'Stone Edge comes at Lv 54 on its own; keep Rock Slide until then']),
    ('Mid', 'Glaceon', 'Ice', 'Ice Body', 'Modest', '252 HP / 252 SpA / 4 SpD', 'Never-Melt Ice',
     [('Freeze-Dry', 0), ('Blizzard', 0), ('Icy Wind', 0), ('Protect', 0)], []),
    ('Closer', 'Golisopod-Aevian', 'Bug/Ground', 'Skill Link', 'Adamant', '252 HP / 252 Atk / 4 SpD', 'Soft Sand',
     [('Bone Rush', 0), ('Pin Missile', 0), ('Swords Dance', 0), ('Protect', 0)], []),
    ('Closer', 'Leavanny-Aevian', 'Bug/Dragon', 'Intimidate', 'Adamant', '252 Atk / 252 Spe / 4 HP', 'Focus Sash',
     [('Rage Powder', 0), ('X-Scissor', 0), ('Dragon Claw', 0), ('Protect', 0)], ['Item: Dragon Fang → Focus Sash (from Rhyperior, or any spare Sash in your Active box). 16 boss hits one-shot it, so the Sash keeps it alive on the turn Golisopod sets up.']),
]
JOB = {'Annihilape': 'Fastest hitter. Breaks Dark, Normal and Steel; Defiant punishes Intimidate.',
       'Gholdengo': 'Make It Rain hits both foes (1.5x on Big Top). Immune to status moves.',
       'Rhyperior': 'Resists Fire. Stone Edge (Hard Stone, 1.5x on Mountain and Volcanic Top) deals with Fire mons and fliers.',
       'Glaceon': 'Icy Wind slows the back line for Golisopod. Freeze-Dry and Blizzard are your Groudon answer.',
       'Golisopod-Aevian': 'Win condition. Skill Link makes Bone Rush and Pin Missile 125 power. After one Swords Dance it one-shots 60 of 68 boss mons.',
       'Leavanny-Aevian': 'Rage Powder pulls attacks so Golisopod gets a free Swords Dance; Focus Sash guarantees it survives that turn. Intimidate on entry.'}
team_rows = []
prev = None
for role, name, types, ab, nat, evs, item, moves, changes in TEAM:
    mv = ''.join(f'<li class="{"new" if n == 1 else ("soon" if n == 2 else "")}">{E(m)}</li>' for m, n in moves)
    ch = ('<ul class="chg">' + ''.join(f'<li>{E(c)}</li>' for c in changes) + '</ul>') if changes else '<span class="ok">No change</span>'
    rc = f'<td class="role role-{role.lower()}" rowspan="2">{role}</td>' if role != prev else ''
    prev = role
    team_rows.append(f'''<tr>{rc}<td><strong>{E(name)}</strong><div class="chips">{chips(types)}</div><div class="job">{E(JOB[name])}</div></td>
<td>{E(ab)}</td><td>{E(nat)}</td><td class="evs">{E(evs)}</td><td>{E(item)}</td><td><ul class="mv">{mv}</ul></td><td>{ch}</td></tr>''')


def srow(label, d):
    g = (d['score_best'] / d['score_current'] - 1) * 100
    return f'<div class="score"><span>{label}</span><b class="num">{d["score_current"]:.2f} → {d["score_best"]:.2f}</b><i class="num">+{g:.0f}%</i></div>'


# ---------------------------------------------------------------- 2) tier list
FLAGS = {  # community / role notes (short)
    'Golisopod (Aevian Form)': ('', 'Forum: "THE MVP" of a V14 team'),
    'Lapras (Aevian Form)': ('', 'No Guard: Sing and Rock Slide never miss'),
    'Musharna (Aevian Form)': ('', 'Trick Room setter for Chapter 9 (forum pick)'),
    'Glalie (Aevian Form)': ('', 'Rock Head (no recoil) + Grassy Surge; forum: "don\'t sleep on it"'),
    'Electrode (Hisuian Form)': ('', 'Forum: "breaks the midgame", but only with its crest'),
    'Ampharos (Aevian Form)': ('', 'Forum: "Trick Room god" once crested (late game)'),
    'Sylveon': ('', 'Pixilate spread moves rated for doubles (Hyper Voice tutor needs 9 badges)'),
    'Whiscash': ('', 'Crest: no weaknesses, +20% Atk/SpA'),
    'Gholdengo': ('', 'Status-immune, spread Make It Rain'),
    'Rhyperior': ('', 'Best Fire answer in your boxes'),
    'Annihilape': ('', 'Fastest hard hitter you own'),
    'Leavanny (Aevian Form)': ('', 'Support: scores low alone, but Rage Powder is what lets Golisopod sweep'),
    'Tangrowth': ('', 'Rage Powder + Sleep Powder, Regenerator'),
    'Amoonguss': ('', 'Rage Powder + Spore-style support, Regenerator'),
    'Furret': ('', 'Crest: free Substitute on entry, Baton Pass'),
    'Meowstic': ('', 'Mega stone owned; Megas unlock in Chapter 12'),
    'Chandelure': ('', 'Mega stone owned; Megas unlock in Chapter 12'),
    'Crawdaunt': ('', 'Adaptability; rated for Trick Room teams'),
    'Donphan': ('', 'Strong alone, but doubles up on Rhyperior and Golisopod\'s Ground hits and weaknesses; makes the six weaker if swapped in'),
    'Azumarill': ('', 'Huge Power. Your best bench mon: basically ties Gholdengo in the six'),
    'Feraligatr': ('', 'Evolve Totodile first (next level-up). Crested Feraligatr is a forum favourite later'),
    'Froslass (Aevian Form)': ('', 'Adaptability; peaks once it gets Water Spout or Muddy Water (not available yet)'),
    'Throh': ('', 'Guts; Wide Guard support in doubles'),
    'Lunatone (Lunatone Dominant Fusion)': ('', 'Lunar Idol: Levitate + 1.5x Ice moves'),
    'Glaceon': ('', 'Speed control + Groudon answer'),
}
IN_SIX = {'Annihilape', 'Gholdengo', 'Rhyperior', 'Glaceon', 'Golisopod (Aevian Form)', 'Leavanny (Aevian Form)'}
TIERS = [('S', 0.70, 'Carries fights on its own'), ('A', 0.58, 'Strong all chapter'), ('B', 0.50, 'Good in several fights'),
         ('C', 0.40, 'Situational'), ('D', -9, 'Weak this chapter')]
seen, cards = set(), {t[0]: [] for t in TIERS}
for r in rows:
    if r['name'] in seen:
        continue
    seen.add(r['name'])
    tier = next(t for t, cut, _ in TIERS if r['score'] >= cut)
    flag, note = FLAGS.get(r['name'], ('', ''))
    best = ', '.join(SHORT[k] for k in r['best'][:2])
    badges = '<span class="b party">Party</span>' if r['where'] == 'Party' else ''
    if r['where'] == 'New catch':
        note = ('New catch (Overflow box). ' + note).strip()
    where = ''
    cards[tier].append(f'''<li class="mon"><div class="mtop"><strong>{E(disp(r["name"]))}</strong><span class="num sc">{r["score"]:.2f}</span></div>
<div class="chips">{chips(r["types"])}<span class="lv">Lv {r["level"]}</span>{where}{badges}</div>
<div class="mnote">Best vs {E(best)}{(" · " + E(note)) if note else ""}</div></li>''')
tier_html = ''.join(
    f'<div class="tier t{t}"><div class="tl"><b>{t}</b><span>{E(desc)}</span></div><ul class="tmons">{"".join(cards[t])}</ul></div>'
    for t, _, desc in TIERS if cards[t])

# ---------------------------------------------------------------- 3) to-do
TODO = [
    ('Team', [
        ('Rhyperior: give it the Hard Stone (from Lapras-Aevian).', 'high'),
        ('Leavanny-Aevian: give it a Focus Sash (Rhyperior\'s, or a spare from Pangoro, Espeon, Golem, etc.).', 'high'),
        ('Rhyperior learns Stone Edge at Lv 54 as it levels: replace Rock Slide then.', 'mid'),
        ('Move Rhyperior and Glaceon into the party; re-spread Annihilape; Leavanny learns Rage Powder.', 'done'),
    ]),
    ('New catches', [
        ('Totodile: evolves to Feraligatr on its next level-up (Lv 30 evolution). Worth doing; it lands in A tier.', 'mid'),
        ('Fidough → Dachsbun and Galarian Corsola → Cursola also evolve on their next level-up. Optional.', 'low'),
        ('Caught all 8 missing from Chapters 1–7, and the Mystery Egg hatched Azumarill (Huge Power).', 'done'),
    ]),
    ('Items', [
        ('Gourmet Treats used; Cairo\'s Red Essence crests bought (Plusle, Minun, Simisear, Simipour, Thievul, Noctowl, Simisage).', 'done'),
        ('All Chapter 1–7 world crests and Mega stones found.', 'done'),
    ]),
]
todo_html = ''
k = 0
for group, items in TODO:
    lis = ''
    for text, pri in items:
        k += 1
        chk = ' checked' if pri == 'done' else ''
        lis += (f'<li class="p-{pri}"><input type="checkbox" id="todo{k}"{chk}><label for="todo{k}">{E(text)}</label>'
                f'<span class="pri">{ {"high": "Priority", "mid": "Soon", "low": "Dex", "done": "Done"}[pri] }</span></li>')
    todo_html += f'<div class="tgroup"><h3>{E(group)}</h3><ul class="todo">{lis}</ul></div>'

# ---------------------------------------------------------------- 4) hidden metadata
meta = {
    'generated': '2026-11-05', 'trainer': 'Vincent', 'level_cap': 55, 'badges': 7, 'difficulty': 'Classic (walkthrough sets)',
    'move_rules': 'level-up <= 55, Egg, Chapter 1-7 TMs (71), tutors at 7 badges (Luck\'s Tent tiers 0/3/5/7, Wispy Shop, Kakori Beach), known moves; no Relearner, no Life Orb, no Megas, no Chapter 8 pickups',
    'scores': {'overall': [fn['score_current'], fn['score_best']], 'singles': [fs['score_current'], fs['score_best']],
               'doubles': [fd['score_current'], fd['score_best']]},
    'goli_swords_dance_ohko': {'no_boost': 51, 'after_sd': 60, 'of': 68},
    'battles': [{'key': p['key'], 'label': p['label'], 'field': p['field'], 'format': p['format'], 'notes': p['notes'],
                 'score_current': p['score_current'], 'score_new': p['score_best'], 'engine_leads': p['leads'],
                 'foes': [{'name': f['foe'], 'lvl': f['lvl'], 'types': f['types'], 'ability': f['ability'], 'item': f['item'],
                           'moves': f['moves'], 'best_answer': f['answer'], 'answer_move': f['answer_move'],
                           'answer_dmg_pct': f['answer_dmg'], 'threat_to': f['threat_to'], 'threat_move': f['threat_move'],
                           'threat_dmg_pct': f['threat_dmg']} for f in p['foes']]} for p in fn['plans']],
    'tier_inputs': [{'name': r['name'], 'where': r['where'], 'level': r['level'], 'score': r['score'], 'solo': r['solo'],
                     'attacks': r['attacks'], 'ability': r['ability']} for r in rows],
    'sources': ['https://bigjra.github.io/rejuvenation/', 'https://rejuvenation.wiki.gg/',
                'https://www.rebornevo.com/forums/topic/80802-list-your-endgame-v14-team-that-wasnt-made-just-to-cheese-v14-spoilers/',
                'https://www.rebornevo.com/forums/topic/66111-best-aevian-pokemon/',
                'https://www.rebornevo.com/forums/topic/66727-listing-of-pokemon-i-found-especially-strong-for-end-game/'],
}
meta_json = json.dumps(meta, ensure_ascii=False).replace('</', '<\\/')

page = f'''<title>Chapter 8 Team Report</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: one-screen-at-a-time trainer sheet: team table, tier board, checklist. */
:root {{
  --bg: #f3f5f6; --panel: #ffffff; --ink: #142026; --muted: #5a6a72; --line: #d7dfe3;
  --accent: #0e7c86; --accent-soft: #dff1f2; --good: #1f7a3d; --good-soft: #e1f3e6; --warn: #9a6200; --warn-soft: #fbefd9;
  --bad: #b3261e; --bad-soft: #fbe3e1;
  --tS: #c0392b; --tA: #d9822b; --tB: #c9a227; --tC: #5b8c5a; --tD: #6b7b84;
  --display: "Chakra Petch", "Arial Narrow", system-ui, sans-serif;
  --body: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #0f171b; --panel: #162127; --ink: #e5eef1; --muted: #93a6ae; --line: #26363e;
  --accent: #4cc3cc; --accent-soft: #12343a; --good: #6fd08f; --good-soft: #143222; --warn: #f0b85a; --warn-soft: #3a2c12;
  --bad: #ff8a80; --bad-soft: #3d1a18; --tS: #ff7b6b; --tA: #f5a55a; --tB: #e6c65a; --tC: #8cc48a; --tD: #9aaab2; color-scheme: dark }} }}
:root[data-theme="dark"] {{
  --bg: #0f171b; --panel: #162127; --ink: #e5eef1; --muted: #93a6ae; --line: #26363e;
  --accent: #4cc3cc; --accent-soft: #12343a; --good: #6fd08f; --good-soft: #143222; --warn: #f0b85a; --warn-soft: #3a2c12;
  --bad: #ff8a80; --bad-soft: #3d1a18; --tS: #ff7b6b; --tA: #f5a55a; --tB: #e6c65a; --tC: #8cc48a; --tD: #9aaab2; color-scheme: dark }}
* {{ box-sizing: border-box }}
body {{ background: var(--bg); color: var(--ink); font: 14.5px/1.5 var(--body); margin: 0 }}
.wrap {{ max-width: 1180px; margin: 0 auto; padding-block: 28px 56px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); display: grid; gap: 36px }}
h1, h2, h3 {{ font-family: var(--display); margin: 0; text-wrap: balance }}
h1 {{ font-size: clamp(26px, 4.4vw, 38px); line-height: 1.05 }}
h2 {{ font-size: 22px; display: flex; gap: 10px; align-items: baseline; flex-wrap: wrap }}
h2 .n {{ font: 600 13px var(--mono); color: var(--accent) }}
h2 .tag {{ font: 500 12px var(--mono); color: var(--muted); letter-spacing: .06em; text-transform: uppercase }}
h3 {{ font-size: 16px }}
p {{ margin: 0; max-width: 75ch }}
a {{ color: var(--accent) }}
.num {{ font-family: var(--mono); font-variant-numeric: tabular-nums }}
.legend {{ font-size: 13px; color: var(--muted) }}
section {{ display: grid; gap: 14px; min-width: 0 }}
header.mast {{ display: grid; gap: 10px; border-bottom: 2px solid var(--ink); padding-bottom: 18px }}
.eyebrow {{ font: 500 12px var(--mono); letter-spacing: .12em; text-transform: uppercase; color: var(--accent) }}
.facts {{ display: flex; flex-wrap: wrap; gap: 6px 18px; font: 13px var(--mono); color: var(--muted) }}
.facts b {{ color: var(--ink); font-weight: 500 }}
.panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 10px; min-width: 0 }}
.tablewrap {{ overflow-x: auto }}
table {{ border-collapse: collapse; width: 100% }}
th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid var(--line); vertical-align: top }}
thead th {{ font: 500 11px var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); white-space: nowrap }}
tbody tr:last-child td {{ border-bottom: 0 }}
.team td {{ font-size: 13.5px }}
.role {{ font: 700 13px var(--display); letter-spacing: .06em; text-transform: uppercase; border-right: 1px solid var(--line); width: 74px }}
.role-lead {{ color: var(--accent) }} .role-mid {{ color: var(--warn) }} .role-closer {{ color: var(--good) }}
.job {{ color: var(--muted); font-size: 12.5px; margin-top: 4px; max-width: 30ch }}
.evs {{ font-family: var(--mono); font-size: 12px; white-space: nowrap }}
.chips {{ display: flex; gap: 4px; flex-wrap: wrap; align-items: center; margin-top: 4px }}
.type {{ font: 600 10px var(--mono); letter-spacing: .05em; text-transform: uppercase; padding: 2px 6px; border-radius: 3px }}
.mv {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 3px; min-width: 120px }}
.mv li.new {{ color: var(--warn); font-weight: 600 }} .mv li.new::after {{ content: " · new"; font: 500 10px var(--mono); text-transform: uppercase }}
.mv li.soon {{ color: var(--accent); font-weight: 600 }} .mv li.soon::after {{ content: " · Lv 54"; font: 500 10px var(--mono); text-transform: uppercase }}
.chg {{ margin: 0; padding-left: 16px; color: var(--warn); font-size: 13px; display: grid; gap: 3px; min-width: 170px }}
.ok {{ color: var(--good); font: 500 12px var(--mono) }}
.plan {{ display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); gap: 16px }}
.plan .panel {{ padding: 16px 18px; display: grid; gap: 8px; align-content: start }}
.plan ul {{ margin: 0; padding-left: 18px; display: grid; gap: 6px; font-size: 13.5px }}
.scores {{ display: grid; gap: 8px }}
.score {{ display: grid; grid-template-columns: 1fr auto 44px; gap: 10px; align-items: baseline; font-size: 13.5px }}
.score i {{ font-style: normal; color: var(--good); text-align: right }}
.board {{ display: grid; gap: 8px }}
.tier {{ display: grid; grid-template-columns: 110px minmax(0, 1fr); background: var(--panel); border: 1px solid var(--line); border-radius: 10px; overflow: hidden }}
.tl {{ padding: 12px; display: grid; align-content: start; gap: 2px; color: #fff }}
.tl b {{ font: 700 30px var(--display); line-height: 1 }} .tl span {{ font-size: 11.5px; opacity: .92 }}
.tS .tl {{ background: var(--tS) }} .tA .tl {{ background: var(--tA) }} .tB .tl {{ background: var(--tB) }} .tC .tl {{ background: var(--tC) }} .tD .tl {{ background: var(--tD) }}
:root .tl {{ color: #fff }}
.tmons {{ list-style: none; margin: 0; padding: 10px; display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 8px }}
.mon {{ border: 1px solid var(--line); border-radius: 8px; padding: 8px 10px; display: grid; gap: 3px; min-width: 0 }}
.mtop {{ display: flex; justify-content: space-between; gap: 8px; align-items: baseline }}
.sc {{ font-size: 12px; color: var(--muted) }}
.lv {{ font: 11px var(--mono); color: var(--muted) }}
.b {{ font: 600 10px var(--mono); text-transform: uppercase; letter-spacing: .04em; padding: 1px 6px; border-radius: 99px }}
.b.six {{ background: var(--accent-soft); color: var(--accent) }} .b.op {{ background: var(--bad-soft); color: var(--bad) }}
.b.sup {{ background: var(--good-soft); color: var(--good) }} .b.party {{ background: var(--warn-soft); color: var(--warn) }}
.mnote {{ font-size: 12px; color: var(--muted) }}
.todos {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px }}
.tgroup {{ background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px; display: grid; gap: 8px; align-content: start }}
.todo {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 8px }}
.todo li {{ display: grid; grid-template-columns: 20px minmax(0, 1fr) auto; gap: 8px; align-items: start; font-size: 13.5px }}
.todo input {{ margin-top: 3px; accent-color: var(--accent) }}
.todo input:checked + label {{ color: var(--muted); text-decoration: line-through }}
.pri {{ font: 600 10px var(--mono); text-transform: uppercase; padding: 1px 6px; border-radius: 99px; white-space: nowrap }}
.p-high .pri {{ background: var(--bad-soft); color: var(--bad) }} .p-mid .pri {{ background: var(--warn-soft); color: var(--warn) }}
.p-low .pri {{ background: var(--accent-soft); color: var(--accent) }} .p-done .pri {{ background: var(--good-soft); color: var(--good) }}
footer {{ font-size: 12.5px; color: var(--muted); border-top: 1px solid var(--line); padding-top: 12px }}
input:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px }}
@media (max-width: 820px) {{ .plan {{ grid-template-columns: 1fr }} .tier {{ grid-template-columns: 1fr }} .tl {{ grid-auto-flow: column; justify-content: start; align-items: baseline; gap: 10px }} }}
</style>

<div class="wrap">
<header class="mast">
  <span class="eyebrow">Pokémon Rejuvenation · Chapter 8 · Classic teams</span>
  <h1>Chapter 8 Team Report</h1>
  <div class="facts"><span>Trainer <b>Vincent</b></span><span>Cap <b>55</b></span><span>Badges <b>7</b></span><span>Moves <b>Ch 1–7 TMs &amp; tutors only</b></span><span>Checked vs <b>68 boss mons, 12 battles</b></span><span>Export <b>5 Nov, 414 mons</b></span></div>
</header>

<section aria-labelledby="s1">
  <h2 id="s1"><span class="n">01</span> Your team <span class="tag">lead · mid · closer — same plan for singles and doubles</span></h2>
  <div class="panel tablewrap"><table class="team">
    <thead><tr><th>Role</th><th>Pokémon</th><th>Ability</th><th>Nature</th><th>EVs</th><th>Item</th><th>Moves</th><th>Change in game</th></tr></thead>
    <tbody>{"".join(team_rows)}</tbody>
  </table></div>
  <div class="plan">
    <div class="panel">
      <h3>Game plan</h3>
      <ul>
        <li><strong>Lead</strong> Annihilape + Gholdengo for fast damage. Remove Typhlosion before Eruption fires.</li>
        <li><strong>Mid</strong> Rhyperior handles Fire and fliers. Glaceon's Icy Wind slows the back line.</li>
        <li><strong>Closer</strong> Leavanny uses Rage Powder, Golisopod uses Swords Dance, then sweeps. In singles, Golisopod sets up on a switch-in it walls.</li>
        <li><strong>Only the lead changes, never the six.</strong> Eli &amp; Sharon: Rhyperior + Gholdengo lead. Groudon: Glaceon leads and Gholdengo sits out. Giratina: lead the closer pair. Amber: Rhyperior leads. Texen (bring 3): Gholdengo, Annihilape, Golisopod.</li>
      </ul>
    </div>
    <div class="panel scores">
      <h3>Team strength</h3>
      {srow("Overall", fn)}{srow("Doubles", fd)}{srow("Singles", fs)}
      <p class="legend">Today's build → after the two item swaps and Stone Edge at Lv 54. Higher is better: how much of each boss team the six can KO before being KO'd. No other six from your 414 scores higher.</p>
    </div>
  </div>
</section>

<section aria-labelledby="s2">
  <h2 id="s2"><span class="n">02</span> Chapter 8 tier list <span class="tag">party + Active box + new catches · {len(seen)} Pokémon</span></h2>
  <p class="legend">Ranked only for Chapter 8, the fights still ahead of you after Angie: Texen, Garufa (Guards, Tommen, Groudon), Crawli, Neved, Eli &amp; Sharon, Jenner, Geara &amp; Zetta, Rift Giratina, Amber. Each score is that Pokémon alone with its best legal moveset at Lv 55 and the fields applied, so a high tier doesn't guarantee a party spot (see Donphan). <b>Party</b> = in your six. The number is the score; "Best vs" lists its two best fights.</p>
  <div class="board">{tier_html}</div>
</section>

<section aria-labelledby="s3">
  <h2 id="s3"><span class="n">03</span> To do</h2>
  <div class="todos">{todo_html}</div>
  <p class="legend">Checkmarks are saved in this browser only. Let levels come naturally; nothing here needs grinding. Anything you pick up during Chapter 8 is left for your end-of-chapter review.</p>
</section>

<footer>Sources: <a href="https://bigjra.github.io/rejuvenation/">BIGJRA walkthrough</a> (Classic Mode), <a href="https://rejuvenation.wiki.gg/">Rejuvenation wiki</a>, <a href="https://www.rebornevo.com/forums/">Reborn Evolved forums</a>, your 406-Pokémon export. Damage is an average-roll estimate; turns, crits and partner AI aren't simulated.</footer>
</div>

<script type="application/json" id="report-data">{meta_json}</script>
<script>
(function () {{
  var KEY = 'ch8-todo';
  var saved = {{}};
  try {{ saved = JSON.parse(localStorage.getItem(KEY) || '{{}}') || {{}}; }} catch (e) {{ saved = {{}}; }}
  document.querySelectorAll('.todo input[type=checkbox]').forEach(function (cb) {{
    if (Object.prototype.hasOwnProperty.call(saved, cb.id)) cb.checked = !!saved[cb.id];
    cb.addEventListener('change', function () {{
      saved[cb.id] = cb.checked;
      try {{ localStorage.setItem(KEY, JSON.stringify(saved)); }} catch (e) {{}}
    }});
  }});
}})();
</script>
'''
open(OUT, 'w', encoding='utf-8').write(page)
print('wrote', OUT, len(page), 'tiers:', {t: len(v) for t, v in cards.items()})
