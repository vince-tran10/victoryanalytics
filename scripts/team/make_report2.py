"""Generate the Chapter 8 team report (HTML) from the engine's output."""
import json, sys, html

FINAL, FS, FD, SENS, OUT = sys.argv[1:6]
d = json.load(open(FINAL))
fs = json.load(open(FS))
fd = json.load(open(FD))
sens = json.load(open(SENS))
E = html.escape

TYPE = {'Normal': ('#A8A77A', '#1d1d12'), 'Fire': ('#EE8130', '#2a1200'), 'Water': ('#6390F0', '#0a1530'),
        'Electric': ('#F7D02C', '#2b2300'), 'Grass': ('#7AC74C', '#132608'), 'Ice': ('#96D9D6', '#0d2a29'),
        'Fighting': ('#C22E28', '#ffffff'), 'Poison': ('#A33EA1', '#ffffff'), 'Ground': ('#E2BF65', '#2b2208'),
        'Flying': ('#A98FF3', '#1a1036'), 'Psychic': ('#F95587', '#2e0414'), 'Bug': ('#A6B91A', '#1c2003'),
        'Rock': ('#B6A136', '#221d05'), 'Ghost': ('#735797', '#ffffff'), 'Dragon': ('#6F35FC', '#ffffff'),
        'Dark': ('#705746', '#ffffff'), 'Steel': ('#B7B7CE', '#1b1b2a'), 'Fairy': ('#D685AD', '#2b0c1c')}


def chips(types):
    out = []
    for t in [x.strip().capitalize() for x in types.replace(' ', '').split('/') if x]:
        bg, fg = TYPE.get(t, ('#888', '#fff'))
        out.append(f'<span class="type" style="background:{bg};color:{fg}">{E(t)}</span>')
    return ''.join(out)


ROLE = {
    'Golisopod (Aevian Form)': ('Win condition', 'Skill Link Bone Rush hits 5 times. That\'s 1.5x more on Deep Earth (Tommen, Guards, Groudon section), and Swords Dance is +3 on Big Top. Slow, so let Tangrowth\'s Rage Powder or Hariyama\'s Fake Out cover it while it sets up.'),
    'Annihilape': ('Fast lead / cleaner', 'The fastest hard hitter you have (155 Speed at cap). Defiant punishes Intimidate (Krookodile, Stoutland). Fire Punch covers the Steel and Fairy types its STABs miss.'),
    'Gholdengo': ('Special lead', 'Good as Gold blocks status (Toxic, Will-O-Wisp, Thunder Wave). Make It Rain hits both foes in doubles and is 1.5x on Big Top. It\'s weak to Ground, so keep it out of the Groudon fight.'),
    'Rhyperior': ('Physical tank / rock nuke', 'Solid Rock bulk, Stone Edge at Lv 54. Rock is 1.5x on Mountain and Volcanic Top and 1.3x on Deep Earth. Best counter to Amber\'s all-Fire team and Geara\'s fliers.'),
    'Glaceon': ('Speed control / Groudon answer', 'Icy Wind slows both foes in doubles (1.5x on Mountain). Freeze-Dry hits Water and Ground super-effectively, and Blizzard hits both foes. It\'s your best Groudon answer: your team\'s score in that fight more than doubles with it. Weak to Fire, so swap it out for Amber.'),
    'Leavanny (Aevian Form)': ('Intimidate lead / fast cleaner', 'The fastest mon on the team (163 Speed). Intimidate softens Chapter 8\'s many physical attackers. Swords Dance and Dragon Claw clean up late. It also has Rage Powder and Electroweb if you want a support set.'),
}
ORDER = ['Golisopod (Aevian Form)', 'Annihilape', 'Gholdengo', 'Rhyperior', 'Glaceon', 'Leavanny (Aevian Form)']
best = {m['name']: m for m in d['best']}
cur = {m['name']: m for m in d['current']}
STAT_ORDER = ['HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe']


def evs(e):
    return ' / '.join(f"{e[k]} {k}" for k in STAT_ORDER if e.get(k))


def disp(n):
    return n.replace(' (Aevian Form)', '-Aevian')


def stat_rows(st):
    rows = []
    for k in STAT_ORDER:
        v = st[k]
        rows.append(f'<div class="srow"><span class="sk">{k}</span><span class="sbar"><i style="width:{min(100, v / 2.8):.0f}%"></i></span><span class="sv">{v}</span></div>')
    return ''.join(rows)


cards = []
for i, n in enumerate(ORDER, 1):
    m = best[n]
    role, blurb = ROLE[n]
    now = set(m['moves_now'] or [])
    mv = ''.join(f'<li class="{"new" if x not in now else ""}">{E(x)}{"<b>learn</b>" if x not in now else ""}</li>' for x in m['moves'])
    where = m['where']
    status = 'In party' if where == 'Party' else f'From {where} box'
    lvl = f"Lv {m['level']} → 55"
    cards.append(f'''
<article class="mon">
  <header><span class="slot">{i}</span><div><h3>{E(disp(n))}</h3><div class="chips">{chips(m["types"])}</div></div><span class="where {"in" if where == "Party" else "out"}">{status}</span></header>
  <p class="role">{E(role)}</p>
  <dl class="kv">
    <div><dt>Ability</dt><dd>{E(m["ability"])}</dd></div>
    <div><dt>Nature</dt><dd>{E(m["nature"])}</dd></div>
    <div><dt>EVs</dt><dd>{E(evs(m["evs"]))}</dd></div>
    <div><dt>Item</dt><dd>{E(m["item"].replace(" (already holding)", ""))}</dd></div>
    <div><dt>Level</dt><dd>{lvl}</dd></div>
  </dl>
  <ul class="moves">{mv}</ul>
  <div class="stats" aria-label="Stats at level 55">{stat_rows(m["stats55"])}</div>
  <p class="blurb">{E(blurb)}</p>
</article>''')

# current party verdicts
VERD = {
    'Golisopod (Aevian Form)': ('keep', 'Your best mon. Picked in 8 of 8 weightings.'),
    'Annihilape': ('keep', 'Picked in 8 of 8 weightings.'),
    'Gholdengo': ('keep', 'Picked in 6 of 8. Sit it out for Groudon.'),
    'Whiscash': ('bench', 'First pick off the bench: swap it in for Glaceon against Amber. The crest makes it weakness-free. In doubles its Earthquake hits your partner, and it\'s 0.25x on Swamp and Wasteland.'),
    'Lapras (Aevian Form)': ('bench', 'No Guard Sing is great, but its only Rock moves at cap are Rock Slide and Rock Tomb (Stone Edge is Lv 65). Seven weaknesses line up with Texen, Groudon and Geara.'),
    'Leavanny (Aevian Form)': ('keep', 'Back in the six now that TMs and tutors are allowed. Intimidate plus the team\'s best Speed.'),
}
cur_rows = ''.join(
    f'<tr><td><strong>{E(disp(n))}</strong><div class="chips">{chips(cur[n]["types"])}</div></td>'
    f'<td><span class="pill {VERD[n][0]}">{"Keep" if VERD[n][0] == "keep" else "Bench"}</span></td>'
    f'<td class="num">{cur[n]["solo_total"]:.2f}</td><td>{E(VERD[n][1])}</td></tr>'
    for n in ['Golisopod (Aevian Form)', 'Annihilape', 'Gholdengo', 'Whiscash', 'Lapras (Aevian Form)', 'Leavanny (Aevian Form)'])

# battle route
OPTIONAL = {'guard1': 'Adam path only', 'guard2': 'Adam path only', 'neved': 'Only if you choose "We win and save Nim"'}
route = []
for i, p in enumerate(d['plans'], 1):
    foes = ''.join(
        f'<tr><td><strong>{E(f["foe"])}</strong> <span class="lv">Lv {f["lvl"]}</span><div class="chips">{chips(f["types"])}</div>'
        f'<div class="sub">{E(f["ability"])}{(" · " + E(f["item"])) if f["item"] else ""}</div></td>'
        f'<td>{E(disp(f["answer"]))}<div class="sub">{E(f["answer_move"])}</div></td>'
        f'<td class="num {"good" if f["answer_dmg"] >= 100 else ("ok" if f["answer_dmg"] >= 50 else "bad")}">{"OHKO" if f["answer_dmg"] >= 100 else str(f["answer_dmg"]) + "%"}</td>'
        f'<td>{"Yes" if f["answer_faster"] else "No"}</td>'
        f'<td>{E(disp(f["threat_to"]))}<div class="sub">{E(f["threat_move"])}</div></td>'
        f'<td class="num {"bad" if f["threat_dmg"] >= 100 else ("ok" if f["threat_dmg"] >= 50 else "good")}">{f["threat_dmg"]}%</td></tr>'
        for f in p['foes'])
    sw = p['swaps'][0] if p['swaps'] else None
    swap = f'{E(disp(sw["bring"]))} for {E(disp(sw["replace"]))} <span class="sub">({E(sw["where"])}, Lv {sw["level"]})</span>' if sw else 'None needed'
    delta = p['score_best'] - p['score_current']
    opt = f'<span class="opt">{E(OPTIONAL[p["key"]])}</span>' if p['key'] in OPTIONAL else ''
    route.append(f'''
<details class="battle">
  <summary>
    <span class="step">{i}</span>
    <span class="bname"><strong>{E(p["label"].split(" – ")[0])}</strong> <span class="sub">{E(p["label"].split(" – ")[-1])}</span> {opt}</span>
    <span class="meta"><span class="fmt {p["format"].lower()}">{E(p["format"])}</span><span class="field">{E(p["field"])}</span></span>
    <span class="leads">Lead: {E(" + ".join(disp(x) for x in p["leads"]))}</span>
    <span class="num delta {"up" if delta > 0.005 else ("down" if delta < -0.005 else "")}">{"+" if delta >= 0 else ""}{delta:.2f}</span>
  </summary>
  <div class="bbody">
    <p class="note">{E(p["notes"])}</p>
    <p class="note"><strong>Best one-mon swap:</strong> {swap}</p>
    <div class="tablewrap"><table class="foes"><thead><tr><th>Boss Pokémon</th><th>Your best answer</th><th>Damage</th><th>Faster?</th><th>Biggest threat to</th><th>Takes</th></tr></thead><tbody>{foes}</tbody></table></div>
  </div>
</details>''')

counts = sorted(sens['counts'].items(), key=lambda x: -x[1])
sens_rows = ''.join(f'<li><span>{E(disp(n))}</span><span class="dots">{"".join("<i class=on></i>" if k < c else "<i></i>" for k in range(sens["runs"]))}</span><span class="num">{c}/{sens["runs"]}</span></li>' for n, c in counts[:8])


def score_row(label, s):
    dv = s['score_best'] - s['score_current']
    pct = dv / s['score_current'] * 100
    return (f'<tr><th scope="row">{label}</th><td class="num">{s["score_current"]:.2f}</td><td class="num">{s["score_best"]:.2f}</td>'
            f'<td class="num delta {"up" if dv > 0 else ""}">{"+" if dv >= 0 else ""}{pct:.0f}%</td></tr>')


exec(open('/tmp/claude-0/-home-user-victoryanalytics/cbcbf9d1-8dc0-5ce1-a0fe-6353198d6d18/scratchpad/report/extra_sections.py').read())
page = f'''<title>Chapter 8 Team Report</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: a trainer's scouting dossier — verdict first, then the six as profile cards, then the battle route in story order. */
:root {{
  --bg: #f3f5f6; --panel: #ffffff; --ink: #142026; --muted: #5a6a72; --line: #d7dfe3;
  --accent: #0e7c86; --accent-soft: #dff1f2; --good: #1f7a3d; --good-soft: #e1f3e6; --warn: #9a6200; --warn-soft: #fbefd9;
  --bad: #b3261e; --bad-soft: #fbe3e1; --bar: #c9d6db;
  --display: "Chakra Petch", "Arial Narrow", system-ui, sans-serif;
  --body: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #0f171b; --panel: #162127; --ink: #e5eef1; --muted: #93a6ae; --line: #26363e;
  --accent: #4cc3cc; --accent-soft: #12343a; --good: #6fd08f; --good-soft: #143222; --warn: #f0b85a; --warn-soft: #3a2c12;
  --bad: #ff8a80; --bad-soft: #3d1a18; --bar: #2b3c44; color-scheme: dark }} }}
:root[data-theme="dark"] {{
  --bg: #0f171b; --panel: #162127; --ink: #e5eef1; --muted: #93a6ae; --line: #26363e;
  --accent: #4cc3cc; --accent-soft: #12343a; --good: #6fd08f; --good-soft: #143222; --warn: #f0b85a; --warn-soft: #3a2c12;
  --bad: #ff8a80; --bad-soft: #3d1a18; --bar: #2b3c44; color-scheme: dark }}
* {{ box-sizing: border-box }}
body {{ background: var(--bg); color: var(--ink); font: 15px/1.55 var(--body); margin: 0 }}
.wrap {{ max-width: 1120px; margin: 0 auto; padding-block: 32px 64px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: grid; gap: 40px }}
h1, h2, h3 {{ font-family: var(--display); text-wrap: balance; margin: 0; letter-spacing: .01em }}
h1 {{ font-size: clamp(30px, 5vw, 44px); line-height: 1.05 }}
h2 {{ font-size: 24px; display: flex; gap: 12px; align-items: baseline }}
h2 .tag {{ font: 500 12px var(--mono); color: var(--muted); letter-spacing: .08em; text-transform: uppercase }}
h3 {{ font-size: 20px }}
p {{ margin: 0; max-width: 70ch }}
a {{ color: var(--accent) }}
a:focus-visible, summary:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px }}
.sub {{ color: var(--muted); font-size: 13px }}
.num {{ font-family: var(--mono); font-variant-numeric: tabular-nums }}
section {{ display: grid; gap: 16px; min-width: 0 }}
.masthead {{ display: grid; gap: 14px; border-bottom: 2px solid var(--ink); padding-bottom: 22px }}
.eyebrow {{ font: 500 12px var(--mono); letter-spacing: .12em; text-transform: uppercase; color: var(--accent) }}
.facts {{ display: flex; flex-wrap: wrap; gap: 8px 20px; font: 13px var(--mono); color: var(--muted) }}
.facts b {{ color: var(--ink); font-weight: 500 }}
.verdict {{ display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr); gap: 24px; align-items: start }}
.answer {{ background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 20px 22px; display: grid; gap: 12px }}
.answer .big {{ font-family: var(--display); font-size: 22px; line-height: 1.25 }}
.answer .big em {{ font-style: normal; color: var(--accent) }}
table {{ border-collapse: collapse; width: 100% }}
th, td {{ text-align: left; padding: 9px 10px; border-bottom: 1px solid var(--line); vertical-align: top }}
thead th {{ font: 500 11px var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted) }}
.scores td.num, .scores thead th:not(:first-child) {{ text-align: right }}
.delta.up {{ color: var(--good) }} .delta.down {{ color: var(--bad) }}
.tablewrap {{ overflow-x: auto; min-width: 0 }}
.chips {{ display: flex; gap: 4px; flex-wrap: wrap; margin-top: 4px }}
.type {{ font: 600 10.5px var(--mono); letter-spacing: .06em; text-transform: uppercase; padding: 2px 7px; border-radius: 3px }}
.team {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px }}
.mon {{ background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 18px; display: grid; gap: 12px; align-content: start; min-width: 0 }}
.mon header {{ display: grid; grid-template-columns: auto 1fr auto; gap: 12px; align-items: start }}
.slot {{ font: 700 26px var(--display); color: var(--accent); line-height: 1 }}
.where {{ font: 500 11px var(--mono); padding: 3px 8px; border-radius: 99px; white-space: nowrap }}
.where.in {{ background: var(--good-soft); color: var(--good) }}
.where.out {{ background: var(--warn-soft); color: var(--warn) }}
.role {{ font: 600 13px var(--mono); text-transform: uppercase; letter-spacing: .08em; color: var(--muted) }}
.kv {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px 14px; margin: 0 }}
.kv div {{ min-width: 0 }}
.kv dt {{ font: 500 11px var(--mono); text-transform: uppercase; letter-spacing: .08em; color: var(--muted) }}
.kv dd {{ margin: 0; font-weight: 500 }}
.moves {{ list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 6px }}
.moves li {{ border: 1px solid var(--line); border-radius: 6px; padding: 6px 9px; font-weight: 500; display: flex; justify-content: space-between; gap: 6px }}
.moves li.new {{ border-color: var(--warn); background: var(--warn-soft) }}
.moves li b {{ font: 500 10px var(--mono); text-transform: uppercase; color: var(--warn); align-self: center }}
.stats {{ display: grid; gap: 3px }}
.srow {{ display: grid; grid-template-columns: 34px 1fr 34px; gap: 8px; align-items: center; font: 12px var(--mono) }}
.sk {{ color: var(--muted) }} .sv {{ text-align: right; font-variant-numeric: tabular-nums }}
.sbar {{ height: 6px; background: var(--bar); border-radius: 3px; overflow: hidden }}
.sbar i {{ display: block; height: 100%; background: var(--accent) }}
.blurb {{ color: var(--muted); font-size: 14px }}
.pill {{ font: 600 11px var(--mono); text-transform: uppercase; letter-spacing: .06em; padding: 3px 9px; border-radius: 99px }}
.pill.keep {{ background: var(--good-soft); color: var(--good) }} .pill.bench {{ background: var(--warn-soft); color: var(--warn) }}
.battle {{ background: var(--panel); border: 1px solid var(--line); border-radius: 10px }}
.battle + .battle {{ margin-top: 8px }}
.battle summary {{ cursor: pointer; list-style: none; display: grid; grid-template-columns: 32px minmax(0, 2fr) minmax(0, 1.2fr) minmax(0, 1.4fr) 56px; gap: 12px; align-items: center; padding: 14px 16px }}
.battle summary::-webkit-details-marker {{ display: none }}
.step {{ font: 700 18px var(--display); color: var(--accent) }}
.bname {{ min-width: 0 }}
.meta {{ display: flex; flex-wrap: wrap; gap: 6px; align-items: center }}
.fmt {{ font: 600 10.5px var(--mono); text-transform: uppercase; letter-spacing: .06em; padding: 2px 7px; border-radius: 3px; border: 1px solid var(--line) }}
.fmt.doubles {{ background: var(--accent-soft); color: var(--accent); border-color: transparent }}
.field {{ font-size: 13px; color: var(--muted) }}
.leads {{ font-size: 13px }}
.opt {{ display: inline-block; font: 500 10.5px var(--mono); color: var(--warn); background: var(--warn-soft); padding: 1px 6px; border-radius: 3px }}
.bbody {{ padding: 0 16px 16px; display: grid; gap: 10px; min-width: 0 }}
.note {{ font-size: 14px }}
.foes td.num {{ font-weight: 500 }}
.good {{ color: var(--good) }} .ok {{ color: var(--warn) }} .bad {{ color: var(--bad) }}
.lv {{ font: 12px var(--mono); color: var(--muted) }}
.two {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 24px }}
.box {{ background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 18px 20px; display: grid; gap: 10px; align-content: start; min-width: 0 }}
.box h3 {{ font-size: 17px }}
.box ul {{ margin: 0; padding-left: 18px; display: grid; gap: 8px }}
.sens {{ list-style: none; padding: 0; margin: 0; display: grid; gap: 6px }}
.sens li {{ display: grid; grid-template-columns: minmax(0, 1fr) auto 40px; gap: 10px; align-items: center; font-size: 14px }}
.dots {{ display: flex; gap: 3px }} .dots i {{ width: 10px; height: 10px; border-radius: 2px; background: var(--bar) }} .dots i.on {{ background: var(--accent) }}
.legend {{ font-size: 13px; color: var(--muted) }}
footer {{ font-size: 13px; color: var(--muted); border-top: 1px solid var(--line); padding-top: 16px; display: grid; gap: 6px }}
@media (max-width: 820px) {{
  .verdict, .two {{ grid-template-columns: 1fr }}
  .battle summary {{ grid-template-columns: 28px minmax(0, 1fr) 52px; }}
  .battle summary .meta, .battle summary .leads {{ grid-column: 2 / 3 }}
  .battle summary .delta {{ grid-row: 1; grid-column: 3 }}
}}
@media (max-width: 420px) {{ .moves, .kv {{ grid-template-columns: 1fr }} .team {{ grid-template-columns: 1fr }} }}
@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important }} }}
</style>

<div class="wrap">
<header class="masthead">
  <span class="eyebrow">Pokémon Rejuvenation · Chapter 8: Those We Lose</span>
  <h1>Chapter 8 Team Report</h1>
  <p>Is your current party good for singles and doubles, what players on the forums rate, what you missed in Chapters 1–7, and the six I'd take through the rest of Chapter 8, with full builds.</p>
  <div class="facts"><span>Trainer <b>Vincent</b></span><span>Level cap <b>55</b></span><span>Difficulty <b>Classic teams</b></span><span>Roster <b>406 mons</b></span><span>Boss Pokémon checked <b>64 across 12 battles</b></span></div>
</header>

<section aria-labelledby="v">
  <h2 id="v">Verdict <span class="tag">singles vs doubles</span></h2>
  <div class="verdict">
    <div class="answer">
      <p class="big">Your party is <em>excellent in singles</em> and <em>a few swaps from its best in doubles</em>.</p>
      <p>With Chapter 1–7 TMs and tutors allowed, the best six keeps four of your current party. Swap <strong>Lapras-Aevian → Rhyperior</strong> and <strong>Whiscash → Glaceon</strong>. In singles nothing does meaningfully better. In doubles the new six is about 3–4% stronger, and five of Chapter 8's biggest fights are doubles.</p>
      <p>Rhyperior resists the Fire attacks that dominate the chapter and gets 1.5x Rock on Volcanic Top and Mountain. Glaceon fixes your worst fight, Groudon, and adds Icy Wind speed control. Whiscash stays on the bench for Amber, because its Earthquake hits your partner in doubles.</p>
      <p>Your instincts were right, and players agree: Golisopod-Aevian is the best mon you own. A V14 player called it "THE MVP" of a team that beat Madame X.</p>
    </div>
    <div class="answer">
      <div class="tablewrap"><table class="scores">
        <thead><tr><th>Every fight scored as</th><th>Your party</th><th>Recommended</th><th>Gain</th></tr></thead>
        <tbody>{score_row("Singles", fs)}{score_row("Doubles", fd)}{score_row("As the game plays them", d)}</tbody>
      </table></div>
      <p class="legend">Score = how much of each boss team the six can knock out before getting knocked out, at Lv 55 with each battle's field applied. Higher is better. Your current party is scored with the moves it runs today.</p>
    </div>
  </div>
</section>

<section aria-labelledby="six">
  <h2 id="six">Recommended six <span class="tag">full profiles</span></h2>
  <p class="legend">Every move is legal under your updated rules: level-up at or below 55, Egg moves, the 71 TMs obtainable in Chapters 1–7, tutors unlocked at 7 badges (Luck's Tent up to Marnie, Wispy Shop, Kakori Beach), or already known. Highlighted moves are ones the mon doesn't know yet. Stat bars are actual stats at Lv 55 with this spread.</p>
  <div class="team">{"".join(cards)}</div>
  <div class="two">
    <div class="box">
      <h3>Bench to keep ready</h3>
      <ul>
        <li><strong>Whiscash (crest) or Jellicent:</strong> swap in for Glaceon against Amber's all-Fire team.</li>
        <li><strong>Hariyama</strong> (Overflow, Fake Out, Thick Fat): the best doubles-support alternative. It came close to making the six.</li>
        <li><strong>Lapras-Aevian:</strong> No Guard Sing for a singles boss where you need a free turn.</li>
        <li><strong>Appletun</strong> (Overflow, Thick Fat): an extra Groudon specialist.</li>
      </ul>
    </div>
    <div class="box">
      <h3>How stable is this pick?</h3>
      <p class="legend">The team search re-run with 8 different scoring weightings.</p>
      <ul class="sens">{sens_rows}</ul>
      <p class="legend">Slots 5 and 6 are the close calls. Every top pair scores within about 1%. Glaceon + Leavanny-Aevian wins because both are Lv 50 and ready now. Meganium is 0.5% better but needs your Lv 25 Chikorita raised 30 levels.</p>
    </div>
  </div>
</section>

<section aria-labelledby="cur">
  <h2 id="cur">Your current party, mon by mon</h2>
  <div class="tablewrap"><table>
    <thead><tr><th>Pokémon</th><th>Call</th><th>Solo score</th><th>Why</th></tr></thead>
    <tbody>{cur_rows}</tbody>
  </table></div>
</section>

<section aria-labelledby="route">
  <h2 id="route">Battle route <span class="tag">story order, from the walkthrough</span></h2>
  <p class="legend">Open any battle to see every boss Pokémon, your best answer from the recommended six, and its biggest threat. The number on the right is the recommended six's gain over your current party. Texen is a multi battle: you bring 3 (Gholdengo, Annihilape, Golisopod) and Aelita brings 3.</p>
  <div>{"".join(route)}</div>
</section>

{ORDER_HTML}{COMMUNITY}{CHECKLIST}

<footer>
  <p><strong>Sources.</strong> Boss teams and story order: <a href="https://bigjra.github.io/rejuvenation/">BIGJRA walkthrough</a> (Classic Mode, the larger set you fight). Field effects, base stats, learnsets, crests and shadow data: <a href="https://rejuvenation.wiki.gg/">rejuvenation.wiki.gg</a>. Roster: your 2026-11-04 23:15 export (406 Pokémon).</p>
  <p><strong>Move rules.</strong> Level-up at or below Lv 55, Egg moves, Chapter 1–7 TMs, tutors unlocked at 7 badges, and known moves. No Move Relearner, no Life Orb, no Megas until Chapter 12.</p>
  <p><strong>Limits.</strong> Damage is an average-roll estimate at Lv 55. It applies field boosts, STAB, abilities, crests and type items. It doesn't simulate turns, crits, stat boosts, screens or your AI partners. Optional fights (Ancient Guards, Neved) count half. Use the battle tables to sanity-check a fight before you go in.</p>
</footer>
</div>
'''
open(OUT, 'w', encoding='utf-8').write(page)
print('wrote', OUT, len(page))
