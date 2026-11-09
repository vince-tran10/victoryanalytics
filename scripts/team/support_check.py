"""Support-aware re-rank of the top passing sixes: setup moves, Glare / Sticky Web speed control, Fake Out."""
import sys, os, json, itertools
sys.argv = ['x', '.', '44']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chapter_rules as C
E = C.E; D = C.D
keys = list(C.byk)
SETUP = {'SWORDSDANCE': ('Atk', 2.0), 'DRAGONDANCE': ('Atk', 1.5), 'BULKUP': ('Atk', 1.5), 'HONECLAWS': ('Atk', 1.5),
         'NASTYPLOT': ('SpA', 2.0), 'CALMMIND': ('SpA', 1.5), 'QUIVERDANCE': ('SpA', 1.5), 'SHELLSMASH': ('Both', 2.0),
         'FILLETAWAY': ('Both', 2.0)}   # Veluza-A: +2 Atk/SpA/Spe for half its HP
info = {}
if os.environ.get('NO_PETALDANCE'):   # Petal Dance locks in 2-3 turns + confusion: re-score those mons without it
    for k in keys:
        c = C.byk[k]
        if 'PETALDANCE' in c['attacks'] or 'OUTRAGE' in c['attacks'] or 'THRASH' in c['attacks']:
            L0 = E.legal_moves(c['sid'], c['form'], c['src'].get('moves', []))
            alt = [m for m in L0 if m not in ('PETALDANCE', 'OUTRAGE', 'THRASH') and D.moves[m]['Category'] != 'Status' and int(D.moves[m].get('Strength') or 0) > 1]
            E.evaluate(c, moveset=set(alt))
            for b in C.HARD:
                for r in c['matchups'][b['key']]: r['q'] *= c.get('lvl_factor', 1)
            c['attacks'] = [m for m in E.pick_moves(c, 3)]
            for k2 in (C.I1, C.I2):
                if k in k2: k2[k] = ({b['key']: [r['q'] for r in c['matchups'][b['key']]] for b in C.HARD}, {b['key']: sum(1 for r in c['matchups'][b['key']] if r['deff'] >= 100) / len(b['foes']) for b in C.HARD})
            print('re-scored without lock-in moves:', C.nm(c), [D.moves[m]['MoveName'] for m in c['attacks']])
for k in keys:
    c = C.byk[k]
    L = E.legal_moves(c['sid'], c['form'], c['src'].get('moves', []))
    phys = sum(D.moves[m]['Category'] == 'Physical' for m in c['attacks']) >= sum(D.moves[m]['Category'] == 'Special' for m in c['attacks'])
    best_setup = None
    for m, (st, mult) in SETUP.items():
        if m in L and (st == 'Both' or (st == 'Atk') == phys):
            if not best_setup or mult > best_setup[1]: best_setup = (D.moves[m]['MoveName'], mult)
    info[k] = dict(setup=best_setup, glare='GLARE' in L or 'THUNDERWAVE' in L or 'STUNSPORE' in L, web='STICKYWEB' in L,
                   fakeout='FAKEOUT' in L, spe=c['stats']['Spe'], phys=phys)
FOESPE = [(bk, fo['stats']['Spe'], 'FLYING' in fo['types'] or (fo['ability'] or '').upper() == 'LEVITATE') for bk, fo in C.FOES]
fidx = {}
for i, (bk, fo) in enumerate(C.FOES): fidx.setdefault(bk, []).append(i)
def adj_q(k, bk, j, gi, team_glare, team_web):
    m = C.byk[k]['matchups'][bk][j]; q = m['q']
    off, taken, faster = m['off'], m['deff'], m['faster']
    i = fidx[bk][j]; fs = FOESPE[i][1]
    eff_fs = fs
    if team_glare: eff_fs = min(eff_fs, fs / 2)                    # paralysis halves Speed
    if team_web and not FOESPE[i][2]: eff_fs = min(eff_fs, fs * 2 / 3)
    f2 = faster or info[k]['spe'] > eff_fs
    sp_q = min(off, 120) / 100 * (1.15 if f2 else 1.0) * (1 - min(taken, 100) / 200) * (0.95 if f2 and not faster else 1)
    q = max(q, sp_q)
    s = info[k]['setup']
    if s and (taken < 100 or (f2 and taken < 100)):                     # survives a hit to set up
        su = min(off * s[1], 120) / 100 * (1.15 if f2 else 1.0) * (1 - min(taken * 2, 100) / 200) * 0.85
        q = max(q, su)
    return q
def score_support(ks):
    glare = any(info[k]['glare'] for k in ks); web = any(info[k]['web'] for k in ks); fo = any(info[k]['fakeout'] for k in ks)
    tot = tw = 0
    for b in C.HARD:
        n = len(b['foes']); s = 0
        for j in range(n):
            qs = sorted((adj_q(k, b['key'], j, 0, glare, web) for k in ks), reverse=True); s += qs[0] + .35 * qs[1]
        frag = sum(sum(1 for r in C.byk[k]['matchups'][b['key']] if r['deff'] >= 100) / n for k in ks) / 6
        v = s / n - .35 * frag
        if b['format'] == 'Doubles' and fo: v *= 1.03
        w = C.bw(b); tot += v * w; tw += w
    return tot / tw
def ok(ks): return all(sum(C.WK[k][s] for k in ks) < 3 and any(C.RS[k][s] for k in ks) for s in C.MAJOR) and len(C.misses(ks)) <= 2
L = [ks for ks in itertools.combinations(keys, 6) if ok(ks)]
L.sort(key=lambda ks: -C.score(ks)); top = L[:300]
def pick(n): return min((k for k in keys if C.nm(C.byk[k]) == n), key=lambda k: (C.byk[k]['src']['where'] != 'Party', -C.byk[k]['solo_total']))
NEW = tuple(pick(n) for n in ['Rhyperior', 'Musharna-A', 'Armarouge', 'Annihilape', 'Vikavolt', 'Ludicolo'])
OLD = tuple(pick(n) for n in ['Golisopod-A', 'Annihilape', 'Glalie-A', 'Clawitzer', 'Gholdengo', 'Musharna-A'])
pool = top + [NEW, OLD]
res = sorted(((score_support(ks), C.score(ks), ks) for ks in pool), reverse=True)
nb = score_support(NEW)
print('passing', len(L), '| NEW base', round(C.score(NEW), 4), 'support', round(nb, 4), '| OLD base', round(C.score(OLD), 4), 'support', round(score_support(OLD), 4))
rk = next(i for i, r in enumerate(res) if set(r[2]) == set(NEW)) + 1
print('NEW support rank', rk, 'of', len(res))
for sup, base, ks in res[:8]:
    tag = ' <- NEW' if set(ks) == set(NEW) else (' <- OLD' if set(ks) == set(OLD) else '')
    print(f"  support {sup:.4f} ({(sup / nb - 1) * 100:+.2f}%) base {base:.4f}  {[C.nm(C.byk[k]) for k in ks]}{tag}")
print('support tools in NEW:', {C.nm(C.byk[k]): {a: info[k][a] for a in ('setup', 'glare', 'web', 'fakeout')} for k in NEW})
