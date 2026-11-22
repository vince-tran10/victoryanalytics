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


TIMES = []
def sh(args, env, quiet=True, log=None):
    import time as _tm; _t0 = _tm.time()
    r = subprocess.run([sys.executable, '-I'] + args, cwd=WS, env=env, capture_output=True, text=True)
    TIMES.append((round(_tm.time() - _t0, 1), os.path.basename(args[0]) + ' ' + ' '.join(os.path.basename(x) for x in args[1:2])))
    if log: open(log, 'w').write(r.stdout + r.stderr)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-3000:]); sys.exit(f'FAILED: {args[0]}')
    if not quiet: print(r.stdout.rstrip())
    return r.stdout



SETUP_MV = {'Swords Dance', 'Dragon Dance', 'Nasty Plot', 'Calm Mind', 'Shell Smash', 'Shift Gear', 'Quiver Dance', 'Bulk Up', 'Curse',
            'Fillet Away', 'Tidy Up', 'Victory Dance', 'Coil', 'Belly Drum'}
ZORO_AB = {'ADAPTABILITY': .33, 'SHEERFORCE': .3, 'PROTEAN': .3, 'LIBERO': .3, 'SPEEDBOOST': .3, 'GOODASGOLD': .25, 'TINTEDLENS': .2,
           'BEASTBOOST': .2, 'INTIMIDATE': .15, 'MAGICGUARD': .15, 'REGENERATOR': .1, 'MULTISCALE': .1, 'UNAWARE': .1, 'LEVITATE': .05}
def order_team(st):   # 22 Nov (Vincent): 1-3 core lead / lead partner / mid, 4 = mid-game flex, 5 = closer flex (has a setup move), 6 = core closer
    core = list(st.get('core') or []); sw = [n for n in st['team'] if n not in core]
    sw.sort(key=lambda n: bool(set((st.get('moves') or {}).get(n) or []) & SETUP_MV))
    st['team'] = core[:3] + sw + core[3:]
    st.pop('zoro_note', None)
    zo = next((n for n in st['team'] if n.startswith('Zoroark')), None)
    if not zo: return
    # 22 Nov (Vincent): Zoroark Crest copies the LAST living party member (ability + its types' STAB). ONLY then may slots 3-6 move;
    # slots 1-2 (the leads) never move. Pick the copy that makes Zoroark strongest; keep the standard order unless it gains.
    import re as _re
    T = {}
    for r in json.load(open(os.path.join(TEAMD, 'tier_all.json')))['rows']: T.setdefault(r['name'], r)
    IB = json.load(open(os.path.join(TEAMD, 'ideal_builds.json'))) if os.path.exists(os.path.join(TEAMD, 'ideal_builds.json')) else {}
    D = json.load(open(os.path.join(WS, 'data', 'Database_Moves.json')))
    zt = set((T.get(zo) or {}).get('types') or [])
    zatk = [D.get(_re.sub(r'[^A-Z]', '', m.upper()), {}) for m in (st.get('moves') or {}).get(zo, [])]
    zatk = [m for m in zatk if m.get('Category') in ('Physical', 'Special')]
    def val(n):
        ab = _re.sub(r'[^A-Z]', '', ((st.get('abilities') or {}).get(n) or (IB.get(n) or {}).get('ability') or (T.get(n) or {}).get('ability') or '').upper())
        tys = set((T.get(n) or {}).get('types') or [])
        stab = sum(.5 for m in zatk if m.get('Type') in tys and m.get('Type') not in zt) / max(1, len(zatk))
        return ZORO_AB.get(ab, 0) + stab, ab, sorted(tys)
    # 22 Nov (Vincent, clarified): leads CAN move, but only as a deliberate trade: a lead goes to slot 6 only if the copy makes
    # Zoroark OP (gain >= ZORO_OP) AND that gain beats what the team loses at lead. Slots 3-6 move for any real gain (> .05).
    ZORO_OP = .3
    def lead_q(n):
        r = T.get(n) or {}; ab = _re.sub(r'[^A-Z]', '', ((st.get('abilities') or {}).get(n) or r.get('ability') or '').upper())
        mv = {_re.sub(r'[^A-Z]', '', m.upper()) for m in (st.get('moves') or {}).get(n, [])}
        return (r.get('blend', 0) + .2 * min(1, (r.get('stats') or {}).get('Spe', 0) / 160) + .15 * (ab == 'INTIMIDATE' or 'FAKEOUT' in mv)
                + .05 * (ab in ('GOODASGOLD', 'MAGICGUARD')))
    team0 = list(st['team']); last = team0[-1]; base = val(last)[0]
    best_back = max([n for n in team0[2:] if n != zo], key=lambda n: (val(n)[0], n == last))
    plan = dict(kind='keep', target=last)
    if best_back != last and val(best_back)[0] > base + .05:
        plan = dict(kind='back', target=best_back)
    lead_opts = []
    for i, ld in enumerate(team0[:2]):
        if ld == zo: continue
        g = val(ld)[0]
        repl = max([n for n in team0[2:] if n not in (zo,)], key=lead_q)
        cost = lead_q(ld) - lead_q(repl)
        lead_opts.append(dict(lead=ld, slot=i + 1, gain=round(g, 2), replacement=repl, cost=round(cost, 2), ok=bool(g >= ZORO_OP and g - base > cost)))
    okl = [o for o in lead_opts if o['ok']]
    if okl:
        o = max(okl, key=lambda o: o['gain'] - o['cost'])
        t = [n for n in team0 if n not in (o['lead'], o['replacement'])]
        t.insert(o['slot'] - 1, o['replacement']) if o['slot'] == 1 else t.insert(1, o['replacement'])
        st['team'] = t[:5] + [o['lead']] if len(t) >= 5 else t + [o['lead']]
        plan = dict(kind='lead', target=o['lead'], replacement=o['replacement'])
    elif plan['kind'] == 'back':
        st['team'] = [n for n in team0 if n != plan['target']] + [plan['target']]
    tgt = st['team'][-1]; v, ab, tys = val(tgt)
    st['zoro_note'] = dict(zoroark=zo, copies=tgt, ability=ab, types=tys, gain=round(v, 2), moved=plan['kind'] != 'keep', kind=plan['kind'],
                           replacement=plan.get('replacement'), lead_options=lead_opts,
                           options={n: round(val(n)[0], 2) for n in team0 if n != zo})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('export'); ap.add_argument('--beat', default=''); ap.add_argument('--fight')
    ap.add_argument('--staging'); ap.add_argument('--active', type=int); ap.add_argument('--quick', action='store_true')
    ap.add_argument('--label')
    a = ap.parse_args()
    st = json.load(open(STATE))
    sys.path.insert(0, os.path.join(ROOT, 'scripts', 'gamedata'))
    import gamedata as _gd
    if not _gd.available():
        print('!! Game data missing (workspace/gamedata). Fights fall back to walkthrough data. Re-upload the Scripts zip, then:\n'
              '   ruby scripts/gamedata/to_json.rb <Scripts/Rejuv/Definitions> workspace/gamedata <Scripts>')

    # 1) copy the export in under a dated name
    m = re.search(r'(\d{4}-\d{2}-\d{2})_(\d{2})-?(\d{2})', os.path.basename(a.export))
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
    CAP_AFTER = {'erick': 65}   # 9th badge -> cap 65 (SystemConstants LEVELCAPS); only matters for legal level-up moves
    for k_, cap_ in CAP_AFTER.items():
        if k_ in st['done'] and st.get('cap', 0) < cap_:
            st['cap'] = cap_; print(f'Level cap raised to {cap_} ({k_} beaten)')

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
               SINGLES_W='2', LINK_HEARTS=json.dumps(st.get('link_hearts', [])), MOVES=json.dumps(st['moves']), CR_RUN=f'r{run}', TEAM_NAMES=json.dumps(st['team']))
    sh(['../scripts/team/roster.py', WS, new, f'team/roster{rost}.json'], env)
    R = json.load(open(os.path.join(TEAMD, f'roster{rost}.json')))
    # 22 Nov legality: score every Pokémon he can't have yet as its prior stage (To do card: de-evolve)
    sh(['../scripts/team/legality.py', new], env)
    _dev = {d['dump']: d for d in json.load(open(os.path.join(TEAMD, 'legality.json'))).get('devolve', [])}
    for x in R:
        d_ = _dev.get(x['dump'])
        if d_: x.update(sid=d_['to_sid'], form=d_['to_form'], devolved_from=x['name'], name=d_['to_name'].replace(' (Aevian Form)', '-Aevian'))
    for x in R: x['level'] = st.get('cap', 55)
    json.dump(R, open(os.path.join(TEAMD, f'roster{rost}_lv55.json'), 'w'))
    print('Scoring (6 engine runs, in parallel)...')   # 21 Nov: independent runs -> ~45s instead of ~110s
    import time as _tm; _t0 = _tm.time()
    jobs = [(['../scripts/team/run.py', WS, f'team/roster{rost}_lv55.json', f'team/r{run}_{f}.json'], dict(env, FORCE_FORMAT=f)) for f in ('native', 'Singles', 'Doubles')]
    jobs.append((['../scripts/team/run.py', WS, f'team/roster{rost}_lv55.json', f'team/r{run}n_native.json'], dict(env, FORCE_FORMAT='native', NOFIELD='1')))
    jobs.append((['../scripts/team/run.py', WS, f'team/roster{rost}_lv55.json', f'team/rc{run}_native.json'], dict(env, FORCE_FORMAT='native', CRESTS='1')))
    jobs.append((['../scripts/team/run.py', WS, f'team/roster{rost}_lv55.json', f'team/r{run}all_native.json'], dict(env, FORCE_FORMAT='native', DONE='')))   # 22 Nov: every hard fight in the game, for the general tiers
    procs = [(a_, subprocess.Popen([sys.executable, '-I'] + a_, cwd=WS, env=e_, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)) for a_, e_ in jobs]
    for a_, p_ in procs:
        o_, e_ = p_.communicate()
        if p_.returncode != 0: print(o_[-2000:], e_[-3000:]); sys.exit(f'FAILED: {a_[0]} {a_[-1]}')
    TIMES.append((round(_tm.time() - _t0, 1), 'engine runs x5 (parallel)'))
    if pick:
        out = sh(['../scripts/team/new_mons.py', WS, f"team/roster{st['roster']}.json", f'team/roster{rost}_lv55.json',
                  f'team/new_mons_{stamp}.json'], dict(env, PICK=','.join(map(str, pick))))
        print('New catches:'); [print('  ' + l[:150]) for l in out.splitlines() if re.match(r'^[SABCD] ', l)]
    for f in ('native', 'Singles', 'Doubles'):
        sh(['../scripts/team/finalize.py', WS, f'team/r{run}_{f}.json.pkl', f'team/f{fin}_{f}.json'],
           dict(env, TEAM='|'.join(st['team']), FORCE_FORMAT=f), log=os.path.join(TEAMD, f'f{fin}_{f}.log'))

    # 5b) ideal builds (game trainer sets + Smogon, legal only) -> every fight scored with them -> fight plans -> next fight's six
    sh(['../scripts/team/ideal_builds.py'], dict(env, RUN=f'r{run}'))
    IDEAL = json.load(open(os.path.join(TEAMD, 'ideal_builds.json')))
    FIX = {n: b['moves'] for n, b in IDEAL.items()}; FIX.update(st['moves'])
    FIXAB = {n: re.sub(r'[^A-Z]', '', (b['ability'] or '').upper()) for n, b in IDEAL.items()}
    FIXAB.update({n: re.sub(r'[^A-Z]', '', a_.upper()) for n, a_ in (st.get('abilities') or {}).items()})
    ORDER9 = ['darkgardevoir', 'garbodor', 'karrina', 'spector', 'spector2', 'jenner9', 'amanda', 'erick']
    def plans():
        fx = dict(env, MOVE_RULES='relearn', FORCE_FORMAT='native', FIXED=json.dumps(FIX), FIXED_AB=json.dumps(FIXAB))
        for k in ORDER9:
            if k not in st['done']:
                sh(['../scripts/team/fights/remaining_eval.py', k], dict(fx, EVAL_OUT=f'team/{k}_eval.json'))
        json.dump(dict(st, export=new), open(STATE, 'w'), indent=1, ensure_ascii=False)
        fp_out = sh(['../scripts/team/fights/fight_plans.py'], fx).rstrip()
        if st.get('fight') in ('darkgardevoir', 'garbodor') and st['fight'] not in st['done']:   # boss bar plan (20 Nov), Fights card
            sh(['../scripts/team/fights/bar_plan.py', st['fight']], fx)
        return fp_out
    if st.get('core'):
        out_ = plans()
        if st.get('one_six'):   # fight_plans picked ONE six for every remaining fight (21 Nov): take its team + swaps
            _s2 = json.load(open(STATE)); st['team'] = _s2['team']; st['plan_swaps'] = _s2.get('plan_swaps'); st['plan_pairs'] = _s2.get('plan_pairs')
            for n in st['team']:
                if n not in st['moves'] or n not in (st.get('abilities') or {}):
                    st['moves'][n] = st['moves'].get(n) or IDEAL.get(n, {}).get('moves') or []
                    st.setdefault('abilities', {})[n] = (st.get('abilities') or {}).get(n) or IDEAL.get(n, {}).get('ability') or ''
            print([l for l in open(os.path.join(TEAMD, 'one_six.json')).read().splitlines()][:1] and 'ONE SIX: ' + ', '.join(st['team']))
        nxt = next((k for k in ORDER9 if k not in st['done']), None)
        if not st.get('fight') and nxt:   # last fight beaten: the next fight's six becomes the team (core + its 2 swaps)
            P = json.load(open(os.path.join(TEAMD, 'fight_plans.json')))[nxt]
            sw = [r['name'] for r in P['swaps']]
            st['fight'] = nxt; st['team'] = list(st['core'][:3]) + sw + list(st['core'][3:]); order_team(st)   # closer last (21 Nov)
            PB = (st.get('plan_builds') or {}).get(nxt, {})   # hand-plan builds (fight protocol), e.g. Garbodor's Gastro Acid Muk
            for n in sw:
                st['moves'][n] = (PB.get(n) or {}).get('moves') or IDEAL.get(n, {}).get('moves') or st['moves'].get(n, [])
                st.setdefault('abilities', {})[n] = (PB.get(n) or {}).get('ability') or IDEAL.get(n, {}).get('ability') or ''
            for q in P['pairs']:   # answers the plan says to TEACH go into that swap's build (3rd slot), e.g. Taunt vs Perish Song
                for w in q.get('wincons') or []:
                    for a_ in w.get('answers') or []:
                        mt = re.match(r'teach (.+?) \((.+?)\)$', a_)
                        if not mt: continue
                        n = next((x for x in sw if x.split(' (')[0] == mt.group(2)), None)
                        if n and mt.group(1) not in st['moves'][n]:
                            mv_ = st['moves'][n]; slot = 2 if len(mv_) >= 3 else len(mv_)
                            st['moves'][n] = mv_[:slot] + [mt.group(1)] + mv_[slot + 1:]
            print(f'Next fight: {nxt} -> swaps {sw}')
            FIX.update(st['moves']); out_ = plans()
        print(out_)
        env.update(TEAM_NAMES=json.dumps(st['team']), MOVES=json.dumps(st['moves']))

    # 6) team rules + team search
    stat = json.loads(sh(['../scripts/team/chapter_rules.py', '.', '30', '--status'], env))
    print(f"Chapter rules: {stat['fights']} hard fights; 3+ weak {stat['weak3'] or 'none'}; unresisted {stat['nores'] or 'none'}; "
          f"misses {[x['foe'] + ' (' + x['fight'] + ')' for x in stat['misses']]}")
    if st.get('core'):   # core-of-4 model: core vs the whole chapter, the six vs the fight it is built for
        st['core_check'] = json.loads(sh(['../scripts/team/chapter_rules.py', '.', '30', '--sets'],
                                         dict(env, CORE_NAMES=json.dumps(st['core']), FIGHT_KEY=st.get('fight') or '', ALSO_OVF='|'.join(st['team']), FORCE_POOL='|'.join(st['team']))).strip().splitlines()[-1])
        print('Core / fight rules:', st['core_check'])
    if not a.quick:
        print('Team search (36-mon pool, ~1-2 min)...')
        tc = json.loads(sh(['../scripts/team/team_check.py', '36'], env).strip().splitlines()[-1])
        print(f"  current six: #{tc['rank']} of {tc['of']}; best is {tc['gap']:+.2f}% "
              f"({', '.join(tc['top'][0]['team'])})" if tc['top'] else '  no six passes')
        st['team_check'] = tc

    order_team(st); json.dump(dict(st, export=new), open(STATE, 'w'), indent=1, ensure_ascii=False)   # flex order before the page
    # 7) page
    pe = dict(env, EXPORT_LABEL=label)
    if st.get('fight'): pe['FIGHT'] = st['fight']
    sh(['../scripts/team/make_report5.py', new, st['base_export'], f'team/f{fin}_native.json', f'team/f{fin}_Singles.json',
        f'team/f{fin}_Doubles.json', st['promote'], OUT], pe)
    sh(['../scripts/team/box_audit.py', OUT, new, st['export'], str(st['active_start']), st['promote'], ''], pe)
    sh(['../scripts/team/highlight.py', OUT], pe)
    # crests: every crest-eligible Pokémon re-scored with its crest (game-code effects), then the Crests tab
    sh(['../scripts/team/crest_tier.py'], dict(env, CR_RUN=f'r{run}', CREST_RUN=f'rc{run}', BASE_RUN=f'r{run}'))
    # one blended tier scale (Ch9 fights + meta) for Crests / Aevians / all other Pokémon, then the Cores tab (16 Nov)
    sh(['../scripts/team/tier_all.py'], dict(env, BASE_RUN=f'r{run}', CREST_RUN=f'rc{run}', ALL_RUN=f'r{run}all'))
    sh(['../scripts/team/tier_tabs.py', OUT], pe)
    sh(['../scripts/team/builder.py', OUT], pe)   # 22 Nov: Team Builder tab (how each core slot was picked)
    # 22 Nov (Vincent): Cores tab removed; cores.py no longer runs (CORES=1 to run it for chat)
    if os.environ.get('CORES'): sh(['../scripts/team/cores.py', OUT], pe)
    sh(['../scripts/team/counters_tab.py', OUT], pe)
    sh(['../scripts/gamedata/compare.py', 'team/gamedata_compare.json'], pe)
    st['team_check_cache'] = True
    json.dump(dict(st, export=new), open(STATE, 'w'), indent=1, ensure_ascii=False)   # checks.py reads team_check
    r = subprocess.run([sys.executable, '-I', '../scripts/team/checks.py', OUT], cwd=WS, env=pe, capture_output=True, text=True)
    print('C&A checks:'); print('  ' + r.stdout.strip().replace('\n', '\n  '))
    blocked = r.returncode != 0
    sh(['../scripts/team/tabs.py', OUT], pe)
    sh(['../scripts/team/theme.py', OUT], pe)   # app look (17 Nov): runs last, data untouched

    # 8) summary
    acts = json.load(open(os.path.join(TEAMD, 'actions.json')))
    html = open(OUT).read()
    todo = re.search(r'<section aria-labelledby="s3">.*?</section>', html, re.S).group(0)
    cards = re.findall(r'<div class="tgroup pcard"><h3>(.*?) <span', todo)
    _tt = re.search(r'<section aria-labelledby="s1">.*?</section>', html, re.S)
    team_tab = _tt.group(0) if _tt else ''
    print(f"Page: party Done ✓ {team_tab.count('Done ✓')}/6 · To do cards {len(cards)} {cards} · "
          f"box moves: green {sum(1 for v in acts.values() if v.startswith(('Move to Active', 'Move into')))}, "
          f"red {sum(1 for v in acts.values() if not v.startswith(('Move to Active', 'Move into')))}")
    for n, v in sorted(acts.items(), key=lambda kv: int(kv[0])):
        print(f'  #{n}: {v}')

    st.update(export=new, export_label=label, active_start=stg[0] if stg else act, run=run, final=fin, roster=rost)
    json.dump(st, open(STATE, 'w'), indent=1, ensure_ascii=False)
    if os.environ.get('TIMING'):
        for t_, n_ in sorted(TIMES, reverse=True)[:15]: print(f'  {t_:6.1f}s  {n_}')
        print(f'  total {sum(t for t, _ in TIMES):.0f}s')
    if blocked:
        print('!! A blocking C&A check FAILED: fix it before publishing.')
    else:
        print('state.json updated. Next: publish output/chapter8_report.html (Artifact, same URL), commit, push.')


if __name__ == '__main__':
    main()
