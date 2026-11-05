"""Parse the Showdown-style party/box export and map each mon to wiki species/form data."""
import re, json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dataset import Data

SUFFIX_FORM = {'Aevian': 'Aevian', 'Hisui': 'Hisuian', 'Galar': 'Galarian', 'Alola': 'Alolan', 'Paldea': 'Paldean',
               'Idol': 'Dominant Fusion'}


def parse_export(path):
    txt = open(path, encoding='utf-8').read().strip()
    blocks = [b for b in re.split(r'\n\s*\n', txt) if b.strip()]
    mons = []
    for i, b in enumerate(blocks, 1):
        lines = [l.strip() for l in b.split('\n') if l.strip()]
        head = lines[0]
        item = ''
        if ' @ ' in head:
            head, item = head.split(' @ ', 1)
        gender = ''
        m = re.search(r'\s\((M|F)\)$', head)
        if m:
            gender = m.group(1); head = head[:m.start()]
        nick = None
        m = re.match(r'^(.*)\s\(([^()]+)\)$', head)
        if m:
            nick, head = m.group(1), m.group(2)
        d = dict(dump=i, raw=lines[0], name=head, nickname=nick, gender=gender, item=item, moves=[], shiny=False)
        for l in lines[1:]:
            if l.startswith('Ability:'):
                d['ability'] = l.split(':', 1)[1].strip()
            elif l.startswith('Level:'):
                d['level'] = int(l.split(':', 1)[1])
            elif l.startswith('EVs:'):
                evs = dict((s, int(v)) for v, s in re.findall(r'(\d+) (\w+)', l))
                d['evs'] = evs
            elif l.endswith('Nature'):
                d['nature'] = l.split()[0]
            elif l.startswith('- '):
                d['moves'].append(l[2:].strip())
            elif l.startswith('Shiny'):
                d['shiny'] = True
        mons.append(d)
    return mons


def resolve(D, mon):
    """Return (species_id, form_idx) for an exported name like 'Lapras-Aevian'."""
    name = mon['name']
    rev = {v: k for k, v in D.names.items() if isinstance(v, str) and k in D.sp}
    rev.update({'Flabébé': 'FLABEBE', 'Nidoran': 'NIDORANmA'})
    base, suf = name, None
    if name not in rev and '-' in name:
        parts = name.split('-')
        for k in range(len(parts) - 1, 0, -1):
            cand = '-'.join(parts[:k])
            if cand in rev:
                base, suf = cand, '-'.join(parts[k:]); break
    if base == "Farfetch'd":
        pass
    sid = rev.get(base)
    if sid is None:
        # names like 'Unown O', 'Vivillon Butterfly of Fate', 'Eiscue Noice Face'
        first = base.split(' ')[0]
        sid = rev.get(first)
        if sid is None:
            key = re.sub(r'[^a-z]', '', base.lower())
            sid = next((s for s in D.sp if re.sub(r'[^a-z]', '', s.lower()) == key), None)
    if sid is None:
        return None, None
    forms = [k for k in D.sp[sid] if k.isdigit()]
    # choose the form whose learnset best explains the exported moves
    mvids = set()
    byname = {v['MoveName'].lower(): k for k, v in D.moves.items()}
    for mv in mon.get('moves', []):
        if mv.lower() in byname:
            mvids.add(byname[mv.lower()])
    scores = []
    for k in forms:
        fn = D.sp[sid][k].get('FormName') or ''
        if re.search(r'\b(Mega|Giga|Primal|Zombie)\b', fn):
            continue
        ls = {m for m, _, _ in D.learnset(sid, k)}
        sc = len(mvids & ls)
        if suf and SUFFIX_FORM.get(suf, suf).lower().replace('-', ' ') in fn.lower().replace('-', ' '):
            sc += 0.5
        if not suf and k == '0':
            sc += 0.4
        scores.append((sc, k))
    scores.sort(key=lambda x: (-x[0], x[1]))
    if scores and (suf or scores[0][0] > 0.4 + 0.9):
        return sid, scores[0][1]
    if not suf:
        return sid, '0'
    want = SUFFIX_FORM.get(suf, suf).lower().replace('-', ' ')
    best = '0'
    for k in forms:
        fn = (D.sp[sid][k].get('FormName') or '').lower().replace('-', ' ')
        if want in fn or (suf in ('M', 'F') and k == '0'):
            best = k; break
        if all(w in fn for w in want.split()):
            best = k
    return sid, best


if __name__ == '__main__':
    base = sys.argv[1]
    D = Data(base)
    mons = parse_export(sys.argv[2])
    miss = []
    for m in mons:
        sid, f = resolve(D, m)
        if sid is None:
            miss.append(m['name'])
        else:
            m['sid'], m['form'] = sid, f
            m['formname'] = D.sp[sid][f].get('FormName')
    print(len(mons), 'parsed; unresolved:', miss)
    for m in mons:
        if m.get('form') not in (None, '0'):
            print(' ', m['name'], '->', m['sid'], m['form'], m['formname'])
    json.dump(mons, open(sys.argv[3], 'w'), ensure_ascii=False, indent=0)
