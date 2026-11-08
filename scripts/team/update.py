"""ONE COMMAND per export. Re-scores everything, re-checks the team, rebuilds the guide page.

usage (from the repo root):
  python3 scripts/team/update.py <export .txt> [--beat kyogre,eli] [--fight manaphy|none]
                                 [--staging 403-417 --active 418] [--quick]

Reads/writes workspace/team/state.json (beaten fights, the six + moves, box-layout overrides, last export, file
counters). After it finishes: publish output/chapter8_report.html with the Artifact tool (same URL), commit, push.
--staging/--active: only when the printed box layout is wrong (the export has no box boundaries).
--quick: skip the slow team search (36-mon pool).
"""
import argparse, collections, json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WS, TEAMD, SCR = os.path.join(ROOT, 'workspace'), os.path.join(ROOT, 'workspace', 'team'), os.path.join(ROOT, 'scripts', 'team')
STATE = os.path.join(TEAMD, 'state.json')
OUT = os.path.join(ROOT, 'output', 'chapter8_report.html')
sys.path.insert(0, SCR)


def sh(args, env, quiet=True, log=None):
    r = subprocess.run([sys.executable, '-I'] + args, cwd=WS, env=env, capture_output=True, text=True)
    if log: open(log, 'w').write(r.stdout + r.stderr)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-3000:]); sys.exit(f'FAILED: {args[0]}')
    if not quiet: print(r.stdout.rstrip())
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('export'); ap.add_argument('--beat', default=''); ap.add_argument('--fight')
    ap.add_argument('--staging'); ap.add_argument('--active', type=int); ap.add_argument('--quick', action='store_true')
    ap.add_argument('--label')
    a = ap.parse_args()
    st = json.load(open(STATE))

    # 1) copy the export in under a dated name
    m = re.search(r'(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})', os.path.basename(a.export))
    stamp = f'{m.group(1)}_{m.group(2)}{m.group(3)}' if m else 'latest'
    new = f'party_and_boxes_{stamp}.txt'
    if os.path.abspath(a.export) != os.path.join(WS, new):
        shutil.copy(a.export, os.path.join(WS, new))
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    label = a.label or (f'{int(m.group(1)[8:])} {months[int(m.group(1)[5:7]) - 1]} {m.group(2)}:{m.group(3)}' if m else stamp)

    # 2) fights / fight mode
    st['done'] = list(dict.fromkeys(st['done'] + [x for x in a.beat.split(',') if x]))
    if a.fight is not None:
        st['fight'] = None if a.fight in ('', 'none') else a.fight
    if st.get('fight') in st['done']:
        st['fight'] = None

    # 3) box layout
    import current_box as cb
    def env_overrides():
        e = dict(os.environ)
        for k in ('ACTIVE_AT', 'STAGING_AT'):
            e[k] = ','.join(st['overrides'].get(k, []))
        return e
    os.environ.update({k: v for k, v in env_overrides().items() if k in ('ACTIVE_AT', 'STAGING_AT')})
    N = cb.parse(os.path.join(WS, new))
    if a.staging or a.active:
        sp = {d['n']: d['species'] for d in N}
        anchor = int(a.staging.split('-')[0]) if a.staging else a.active
        key = f"{len(N)}@{anchor}={sp[anchor]}"
        if a.active: st['overrides'].setdefault('ACTIVE_AT', []).append(f'{key}:{a.active}')
        if a.staging: st['overrides'].setdefault('STAGING_AT', []).append(f'{key}:{a.staging}')
        os.environ.update({k: ','.join(v) for k, v in st['overrides'].items()})
    stg, act = cb.staging_range(N), cb.active_start(N)
    print(f'Export {new} ({len(N)} mons, label "{label}"): party {cb.party_size(N)}, staging {stg}, Active from #{act}')
    print('  check: around Active start ->', [(d['n'], d['species']) for d in N if act - 3 <= d['n'] <= act + 2])

    # 4) new catches (species count went up vs the last export)
    O = cb.parse(os.path.join(WS, st['export']))
    up = collections.Counter(d['species'] for d in N) - collections.Counter(d['species'] for d in O)
    pick = sorted({d['n'] for d in N if up.get(d['species'])} | ({d['n'] for d in N if stg and stg[0] <= d['n'] <= stg[1]}))

    # 5) re-score everything
    run, fin, rost = st['run'] + 1, st['final'] + 1, st['roster'] + 1
    env = env_overrides(); env.update(os.environ)
    env.update(MOVE_RULES='relearn', PARTY_N='6', ACTIVE_START=str(stg[0] if stg else act), DONE=','.join(st['done']),
               SINGLES_W='2', MOVES=json.dumps(st['moves']), CR_RUN=f'r{run}', TEAM_NAMES=json.dumps(st['team']))
    sh(['../scripts/team/roster.py', WS, new, f'team/roster{rost}.json'], env)
    R = json.load(open(os.path.join(TEAMD, f'roster{rost}.json')))
    for x in R: x['level'] = 55
    json.dump(R, open(os.path.join(TEAMD, f'roster{rost}_lv55.json'), 'w'))
    print('Scoring (4 engine runs)...')
    for f in ('native', 'Singles', 'Doubles'):
        sh(['../scripts/team/run.py', WS, f'team/roster{rost}_lv55.json', f'team/r{run}_{f}.json'], dict(env, FORCE_FORMAT=f))
    sh(['../scripts/team/run.py', WS, f'team/roster{rost}_lv55.json', f'team/r{run}n_native.json'], dict(env, FORCE_FORMAT='native', NOFIELD='1'))
    if pick:
        out = sh(['../scripts/team/new_mons.py', WS, f"team/roster{st['roster']}.json", f'team/roster{rost}_lv55.json',
                  f'team/new_mons_{stamp}.json'], dict(env, PICK=','.join(map(str, pick))))
        print('New catches:'); [print('  ' + l[:150]) for l in out.splitlines() if re.match(r'^[SABCD] ', l)]
    for f in ('native', 'Singles', 'Doubles'):
        sh(['../scripts/team/finalize.py', WS, f'team/r{run}_{f}.json.pkl', f'team/f{fin}_{f}.json'],
           dict(env, TEAM='|'.join(st['team']), FORCE_FORMAT=f), log=os.path.join(TEAMD, f'f{fin}_{f}.log'))

    # 6) team rules + team search
    stat = json.loads(sh(['../scripts/team/chapter_rules.py', '.', '30', '--status'], env))
    print(f"Chapter rules: {stat['fights']} hard fights; 3+ weak {stat['weak3'] or 'none'}; unresisted {stat['nores'] or 'none'}; "
          f"misses {[x['foe'] + ' (' + x['fight'] + ')' for x in stat['misses']]}")
    if not a.quick:
        print('Team search (36-mon pool, ~1-2 min)...')
        tc = json.loads(sh(['../scripts/team/team_check.py', '36'], env).strip().splitlines()[-1])
        print(f"  current six: #{tc['rank']} of {tc['of']}; best is {tc['gap']:+.2f}% "
              f"({', '.join(tc['top'][0]['team'])})" if tc['top'] else '  no six passes')
        st['team_check'] = tc

    # 7) page
    pe = dict(env, EXPORT_LABEL=label)
    if st.get('fight'): pe['FIGHT'] = st['fight']
    sh(['../scripts/team/make_report5.py', new, st['base_export'], f'team/f{fin}_native.json', f'team/f{fin}_Singles.json',
        f'team/f{fin}_Doubles.json', st['promote'], OUT], pe)
    sh(['../scripts/team/box_audit.py', OUT, new, st['export'], str(st['active_start']), st['promote'], ''], pe)
    sh(['../scripts/team/highlight.py', OUT], pe); sh(['../scripts/team/tabs.py', OUT], pe)

    # 8) summary
    acts = json.load(open(os.path.join(TEAMD, 'actions.json')))
    html = open(OUT).read()
    todo = re.search(r'<section aria-labelledby="s3">.*?</section>', html, re.S).group(0)
    cards = re.findall(r'<div class="tgroup pcard"><h3>(.*?) <span', todo)
    team_tab = re.search(r'<section aria-labelledby="s1">.*?Team rules', html, re.S).group(0)
    print(f"Page: party Done ✓ {team_tab.count('Done ✓')}/6 · To do cards {len(cards)} {cards} · "
          f"box moves: green {sum(1 for v in acts.values() if v.startswith(('Move to Active', 'Move into')))}, "
          f"red {sum(1 for v in acts.values() if not v.startswith(('Move to Active', 'Move into')))}")
    for n, v in sorted(acts.items(), key=lambda kv: int(kv[0])):
        print(f'  #{n}: {v}')

    st.update(export=new, export_label=label, active_start=stg[0] if stg else act, run=run, final=fin, roster=rost)
    json.dump(st, open(STATE, 'w'), indent=1, ensure_ascii=False)
    print('state.json updated. Next: publish output/chapter8_report.html (Artifact, same URL), commit, push.')


if __name__ == '__main__':
    main()
