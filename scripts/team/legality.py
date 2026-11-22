"""Legality audit (Vincent, 22 Nov): which owned Pokémon / moves he should NOT have yet at his story point.
1) Evolutions: walk each mon's pre-evolution chain in Rejuvenation's own montext (gamedata) and flag steps whose method is
   not reachable now: evolution items outside the Ch1-8 list, trades, CollectItem (Gimmighoul coins), UseMove / HasMove with a
   move he can't learn yet, other special methods (listed for a manual look).
2) Moves: every known move must be legal now (level-up <= cap, egg, relearner, Ch1-8 TMs, tutors <= 8 badges).
usage (from workspace/): python3 ../scripts/team/legality.py <export.txt>   -> team/legality.json + printout"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('MOVE_RULES', 'relearn')
import engine
from engine import Engine, ITEMS_CH1_7
from roster import parse_export, resolve
st = json.load(open('team/state.json'))
engine.CAP = st.get('cap', 60)
E = Engine(os.path.abspath('.'))
D = E.D
MT = json.load(open('gamedata/montext.json'))
MV = json.load(open('gamedata/movetext.json')) if os.path.exists('gamedata/movetext.json') else {}
IT = json.load(open('gamedata/itemtext.json')) if os.path.exists('gamedata/itemtext.json') else {}
def mvn(k): return (MV.get(k) or {}).get('name', k.title())
def itn(k): return (IT.get(k) or {}).get('name', k.title())
OK_METHODS = {'Level', 'LevelDay', 'LevelNight', 'LevelFemale', 'LevelMale', 'Happiness', 'HappinessDay', 'HappinessNight',
              'Silcoon', 'Cascoon', 'Ninjask', 'Shedinja', 'AttackGreater', 'DefenseGreater', 'AtkDefEqual', 'LevelRain', 'LevelDusk',
              'WalkSteps', 'Affection', 'LevelBattle', 'HasInParty'}

EXTRA_OK = {'NIGHTMAREFUEL', 'OVALSTONE', 'ELECTIRIZER'}   # Vincent 22 Nov: Electirizer = Ch9 / held by wild Electabuzz. Protector = Ch10, Xen Waste = Ch12, Armors / Dubious Disc = later (Shayda shop)
def mt_form(sid, form):
    fs = MT.get(sid) or {}
    names = list(fs)
    fn = (D.form(sid, str(form)).get('FormName') or '') if sid in D.sp else ''
    for k in names:
        if fn and fn.lower().split()[0] in k.lower(): return k
    return names[0] if names else None

def legal_now(sid, form, mid):
    return mid in E.legal_moves(sid, str(form), [])

def _fk(sp, idx):
    ks = list(MT.get(sp) or {})
    i = int(idx) if str(idx).isdigit() else 0
    return ks[i] if i < len(ks) else (ks[0] if ks else None)
def prevo_steps(sid, form):
    """[(from_sid, from_form_key, method, param)] from the base stage up to this mon (montext form order = form index)."""
    steps, cur, cf, seen = [], sid, form, set()
    while (cur, str(cf)) not in seen:
        seen.add((cur, str(cf)))
        f = (MT.get(cur) or {}).get(_fk(cur, cf)) or {}
        pre = f.get('preevo')
        if not pre: break
        psid, pform = pre['species'], pre.get('form', 0)
        pk = _fk(psid, pform)
        e = next((e for e in ((MT.get(psid) or {}).get(pk) or {}).get('evolutions') or [] if e['species'] == cur), None)
        if not e: break
        steps.insert(0, (psid, pform, e['method'], e.get('parameter')))
        cur, cf = psid, pform
    return steps

def judge(step, sid, form, name=''):
    psid, psid_form, method, param = step
    p = param if not isinstance(param, list) else param
    if method in OK_METHODS: return None
    if method in ('Item', 'ItemFemale', 'ItemMale', 'DayHoldItem', 'NightHoldItem'):
        return None if str(p).upper() in ITEMS_CH1_7 | EXTRA_OK else f'needs {itn(str(p))}, not obtainable yet'
    if method.startswith('Trade'):   # Rejuvenation: Link Heart (Ch2 shop $25,000, Oceana Pier Ch5, hidden ones) = trade evolution
        if method == 'TradeItem' and str(p).upper() not in ITEMS_CH1_7 | EXTRA_OK:
            return f'needs {itn(str(p))}, not obtainable yet'
        # Vincent 22 Nov: Link Hearts are limited; he allows ONE, for A tier or higher (state link_hearts = ['Slowking'])
        if name.split(' (')[0] in st.get('link_hearts', []): return None
        return 'trade evolution, and your one Link Heart went to ' + ', '.join(st.get('link_hearts', []) or ['none'])
    if method == 'CollectItem':
        return f'needs {p[0]} {itn(p[1])}'
    if method in ('UseMove', 'HasMove'):
        mv = p[1] if isinstance(p, list) else p
        try:
            ok = (legal_now(psid, str(psid_form), mv) if method == 'UseMove' else legal_now(sid, form, mv)) or mv in E.allowed_tms_ids
        except Exception:
            ok = False
        return None if ok else f'{"uses" if method == "UseMove" else "needs"} {mvn(mv)}{" x" + str(p[0]) if isinstance(p, list) else ""}, not learnable yet'
    if method in ('BadInfluence', 'Runerigus', 'DefeatEnemies', 'LandCritical', 'LevelPartner'): return None   # doable now (checked 22 Nov)
    return f'special method {method} {p or ""} (check by hand)'

E.allowed_tms_ids = set(json.load(open('team/allowed_tms.json'))['tms'].values())
mons = parse_export(sys.argv[1])
evo_flags, move_flags, devolve = [], [], []
def disp_name(sp, fi):
    fk = _fk(sp, fi) or ''
    return D.nm(sp) + ('' if not str(fi).isdigit() or int(fi) == 0 else f" ({fk})")
for m in mons:
    sid, form = resolve(D, m)
    if not sid: continue
    loc = 'Party' if m['dump'] <= 6 else f"#{m['dump']}"
    first_bad = None
    for stp in prevo_steps(sid, form):
        why = judge(stp, sid, form, m['name'])
        if why:
            evo_flags.append(dict(name=m['name'], where=loc, level=m.get('level'), step=f"{D.nm(stp[0])} -> {m['name']}", why=why))
            if first_bad is None: first_bad = (stp, why)
    if first_bad:   # de-evolve to the stage before the first step he can't do yet
        (psid, pf, _, _), why = first_bad
        devolve.append(dict(dump=m['dump'], name=m['name'], to_sid=psid, to_form=str(pf), to_name=disp_name(psid, pf), why=why))
    leg = E.legal_moves(sid, str(form), [])
    for mv in m['moves']:
        mid = E.move_id(mv)
        if mid and mid not in leg:
            move_flags.append(dict(name=m['name'], where=loc, move=mv))
json.dump(dict(evo=evo_flags, moves=move_flags, devolve=devolve), open('team/legality.json', 'w'), indent=1, ensure_ascii=False)
if __name__ == '__main__':
    import collections
    print('EVOLUTIONS not reachable at Ch9:')
    g = collections.defaultdict(list)
    for x in evo_flags: g[(x['name'], x['why'])].append(x['where'])
    for (n, w), locs in sorted(g.items()): print(f'  {n}: {w}  [{", ".join(locs)}]')
    print('DE-EVOLVE:')
    for x in devolve: print(f"  #{x['dump']} {x['name']} -> {x['to_name']}  ({x['why']})")
    print('MOVES not learnable yet:')
    g = collections.defaultdict(list)
    for x in move_flags: g[(x['name'], x['where'])].append(x['move'])
    for (n, w), mv in sorted(g.items(), key=lambda x: x[0][1] != 'Party'): print(f'  {n} [{w}]: {", ".join(mv)}')
