import sys, os, itertools
sys.argv = ['x', '.', '30']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chapter_rules as C
keys = list(C.byk)
OFF = {k: [C.byk[k]['matchups'][bk][[fo2 is fo for fo2 in [f for b in C.HARD if b['key']==bk for f in b['foes']]].index(True)]['off'] for bk, fo in C.FOES] for k in keys}
def base_ok(combo):
    for s in C.MAJOR:
        if sum(C.WK[k][s] for k in combo) >= 3 or not any(C.RS[k][s] for k in combo): return False
    return True
res = {'k0': [], 'k1': [], 'k2': [], 'k3': [], 'seko': []}
for combo in itertools.combinations(keys, 6):
    if not base_ok(combo): continue
    miss = [i for i in range(len(C.FOES)) if not any(C.HT[k][i] for k in combo)]
    nm_miss = {C.FOES[i][1]['name'] for i in miss}
    for kk in (0, 1, 2, 3):
        if len(nm_miss) <= kk: res[f'k{kk}'].append(combo)
    if all(any(OFF[k][i] >= 100 for k in combo) for i in miss): res['seko'].append(combo)
cur = ['Golisopod-A', 'Annihilape', 'Glalie-A', 'Clawitzer', 'Gholdengo', 'Musharna-A']
ck = list({C.nm(C.byk[k]): k for k in keys if C.nm(C.byk[k]) in cur and C.byk[k]['src']['where'] == 'Party'}.values())
print('base (b)+(c) pass count, current passes b/c:', base_ok(ck), 'current score', round(C.score(ck), 4))
for v, L in res.items():
    r = sorted(((C.score(ks), C.exposure(ks), ks) for ks in L), reverse=True)
    print(f'\n== {v}: {len(L)} pass')
    for s, x, ks in r[:6]:
        miss = sorted({C.FOES[i][1]['name'] for i in range(len(C.FOES)) if not any(C.HT[k][i] for k in ks)})
        print(f"  {s:.4f} ({s/C.score(ck):.1%} of current) exp {x:+.2f}", [C.nm(C.byk[k]) for k in ks], 'no-SE:', miss)
    rank = [i for i, (s, x, ks) in enumerate(r) if set(ks) == set(ck)]
    print('  current rank:', rank[0] + 1 if rank else 'fails')
print()
for i in range(len(C.FOES)):
    if not any(C.HT[k][i] for k in ck):
        bk, fo = C.FOES[i]
        b = max(ck, key=lambda k: OFF[k][i])
        print(bk, fo['name'], fo['types'], fo['ability'], 'best', C.nm(C.byk[b]), round(OFF[b][i]))
