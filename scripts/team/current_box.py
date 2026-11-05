"""Map the latest export onto the engine's per-mon scores (f11 roster, scored from the 10:14 export).

current_rows(new_export, old_export, f11_json) -> list of dicts, one per mon in the new export:
  n, species, nick, gender, level, item, moves, box, final, score, solo, attacks, ability, types, gate, capsule
"""
import json, re, os, sys, collections, subprocess
here = os.path.dirname(os.path.abspath(__file__))
TIER = [('S', .60), ('A', .53), ('B', .48), ('C', .40), ('D', -9)]  # rescaled 11-05: remaining fights, singles x2
tier = lambda s: next(t for t, c in TIER if s >= c)


def parse(p):
    out = subprocess.run([sys.executable, '-I', os.path.join(here, 'parse_boxes.py'), p, '/dev/stdout'], capture_output=True, text=True).stdout
    return json.loads(out[:out.rindex(']') + 1])


def disp(n):
    return (n.replace(' (Aevian Form Male)', '-Aevian').replace(' (Aevian Form)', '-Aevian').replace(' (Icy Aevian Form)', '-Aevian')
             .replace(' (Hisuian Form)', '-Hisui').replace(' (Galarian Form)', '-Galar').replace(' (Alolan Form)', '-Alola')
             .replace(' (Lunatone Dominant Fusion)', '-Idol').replace(' (Solrock Dominant Fusion)', '-Idol'))


def party_size(N):
    """Party = entries before the Overflow A-Z run (first 'A…' name that sorts below the entry before it)."""
    def sorted_run(i, n=15):
        xs = [d['species'].lower() for d in N[i:i + n]]
        return len(xs) == n and all(a <= b for a, b in zip(xs, xs[1:]))
    for i in range(1, min(7, len(N))):
        if N[i]['species'][:1].upper() == 'A' and sorted_run(i):
            return i
    return 6


def active_start(N):
    """Active box = the last A–Z run that starts with an 'A'/'B' name after Overflow (a new-catch box may sit between)."""
    P = party_size(N)
    resets = [i for i in range(P + 1, len(N)) if N[i]['species'].lower() < N[i - 1]['species'].lower()]
    # Overflow ends at the first reset after a 'Z…' name; Active is the next reset that starts with an A/B name
    zend = next((i for i in resets if N[i - 1]['species'][:1].upper() >= 'W'), None)
    if zend is not None:
        ab = [i for i in resets if i >= zend and N[i]['species'][:1].upper() in 'AB' and len(N) - i >= 10]
        if ab:
            return N[ab[0]]['n']
    for i in range(P + 1, len(N)):
        if N[i]['species'].lower() < N[i - 1]['species'].lower() and all(
                N[j - 1]['species'].lower() <= N[j]['species'].lower() for j in range(i + 1, len(N))):
            return N[i]['n']
    return len(N) + 1


def current_rows(new_export, old_export, f11):
    N, O = parse(new_export), parse(old_export)
    R = json.load(open(f11))['roster']
    def owned_species(o):
        o = o.split(' @ ')[0].strip()
        o = re.sub(r'\s*\((M|F)\)$', '', o)
        m = re.match(r'.*\((.*)\)$', o)
        return m.group(1) if m else o
    by_sp, by_final = collections.defaultdict(list), collections.defaultdict(list)
    for r in R:
        by_sp[owned_species(r['owned_as'])].append(r)
        by_final[disp(r['name'])].append(r)
    act = active_start(N)
    rows = []
    for d in N:
        d['box'] = 'Party' if d['n'] <= party_size(N) else ('Active' if d['n'] >= act else 'Overflow')
        ents = by_sp.get(d['species']) or by_final.get(d['species']) or []
        if not ents:
            rows.append(dict(d, final=d['species'], score=None)); continue
        cur = max((e for e in ents if not e['ability_change']), key=lambda e: e['total'], default=ents[0])
        top = max(ents, key=lambda e: e['total'])
        rows.append(dict(d, final=disp(cur['name']), name=cur['name'], score=cur['total'], solo=cur['solo'], attacks=cur['attacks'],
                         ability=cur['ability'], types=cur['types'], gate=cur['gate'], evolve=cur.get('evolve', ''),
                         capsule=(top['ability'], top['total']) if top['total'] > cur['total'] + .01 else None))
    return rows, act


if __name__ == '__main__':
    rows, act = current_rows(*sys.argv[1:4])
    print('active start', act, 'unscored', [r['species'] for r in rows if r['score'] is None])
    have = {r['final'] for r in rows if r['box'] != 'Overflow'}
    print('ACTIVE below A:', sorted((round(r['score'], 2), r['final']) for r in rows if r['box'] == 'Active' and r['score'] < .58))
    print('OVERFLOW >= A:')
    for r in sorted((r for r in rows if r['box'] == 'Overflow' and r['score'] and r['score'] >= .5), key=lambda r: -r['score']):
        print(f"  {r['score']:.3f} {tier(r['score'])} #{r['n']} {r['species']} Lv{r['level']} -> {r['final']} | have={r['final'] in have} | gate={r['gate']} | evo={r['evolve']} | {r['ability']} {r['attacks']} cap={r['capsule']}")
