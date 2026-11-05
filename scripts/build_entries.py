"""Match every row on the Pokemon Locations page to species/form data from the game files."""
import json, re, sys

BASE = sys.argv[1]
w = json.load(open(f'{BASE}/raw/locations.json'))['parse']['wikitext']
sp = json.load(open(f'{BASE}/data/Database_Species.json'))
names = json.load(open(f'{BASE}/data/Database_Names.json'))


def split_args(s):
    parts, depth, cur, i = [], 0, '', 0
    while i < len(s):
        if s.startswith('[[', i):
            depth += 1; cur += '[['; i += 2; continue
        if s.startswith(']]', i):
            depth = max(0, depth - 1); cur += ']]'; i += 2; continue
        if s[i] == '|' and depth == 0:
            parts.append(cur); cur = ''; i += 1; continue
        cur += s[i]; i += 1
    parts.append(cur)
    return parts


def clean_loc(s):
    s = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


# display name -> species id
disp2id = {}
for k, v in names.items():
    if isinstance(v, str) and v.isupper() and v in sp:
        disp2id[k] = v
for sid in sp:
    disp2id.setdefault(names.get(sid, sid), sid)
disp2id.update({'Nidoran♀': 'NIDORANfE', 'Nidoran♂': 'NIDORANmA', 'Flabébé': 'FLABEBE'})

# Galarian Darmanitan only exists in the Forms module; graft it on as a proper form.
forms_mod = json.load(open(f'{BASE}/data/Database_Forms.json'))
gd = dict(next(f for f in forms_mod['DARMANITAN'] if f.get('FormName') == 'Galarian Darmanitan'))
gd['FormName'] = 'Galarian Form'
gd['CompatibleMoves'] = gd.pop('TMs', [])
gd['EggMoves'] = sp['DARUMAKA']['1'].get('EggMoves', [])
gd['_source'] = 'Module:Database/Forms'
sp['DARMANITAN']['1'] = gd
json.dump(sp, open(f'{BASE}/data/species_patched.json', 'w'), ensure_ascii=False)

SYN = {'sand': 'sandy', 'origin': 'origin', 'east': 'east', 'west': 'west', 'midday': 'midday',
       'midnight': 'midnight', 'dusk': 'dusk', 'crowned': 'crowned'}


def norm_tokens(s):
    s = s.lower().replace('-', ' ')
    return [SYN.get(t, t) for t in re.findall(r"[a-z']+", s) if t not in ('form', 'forme', 'sea', 'style')]


def form_fields(species, idx):
    f = species[str(idx)]
    parent = form_fields(species, f['formBase']) if f.get('formBase') not in (None, '', 0, '0') and str(f.get('formBase')) != str(idx) else species['0']
    merged = dict(parent)
    for k, v in f.items():
        merged[k] = v
    # explicit Type2 removal is not representable; if form sets Type1 but not Type2, keep base Type2 (game behaviour)
    return merged


rows = re.findall(r'\{\{rdex\|(.*?)\}\}\s*\n', w)
entries, problems = [], []
for r in rows:
    p = split_args(r)
    p += [''] * (6 - len(p))
    loc, dex, name, label, t1, t2 = [x.strip() for x in p[:6]]
    sid = disp2id.get(name)
    if sid is None:
        # try loose match
        key = re.sub(r'[^a-z0-9]', '', name.lower())
        sid = next((s for s in sp if re.sub(r'[^a-z0-9]', '', s.lower()) == key), None)
    if sid is None:
        problems.append(('nospecies', name, label)); continue
    species = sp[sid]
    forms = [k for k in species if k.isdigit()]
    want_types = {t1.upper(), t2.upper()} - {''}
    lt = norm_tokens(label)
    best, best_score = '0', -99
    for k in forms:
        f = form_fields(species, k)
        fname = f.get('FormName', '')
        ft = norm_tokens(fname)
        score = 0
        if lt:
            score += 3 * sum(1 for t in lt if t in ft)
            score -= 2 * sum(1 for t in ft if t not in lt and t not in ('normal',))
        else:
            score += 2 if k == '0' else 0
        if re.search(r'\b(Mega|Giga|Primal|Zombie)\b', fname) and not re.search(r'mega|giga|primal|zombie', label.lower()):
            score -= 10
        types = {f.get('Type1')} | ({f.get('Type2')} if f.get('Type2') else set())
        if f.get('Type1') and f.get('Type2') == f.get('Type1'):
            types = {f.get('Type1')}
        score += 4 if types == want_types else 0
        if score > best_score:
            best, best_score = k, score
    f = form_fields(species, best)
    types = [x for x in [f.get('Type1'), f.get('Type2')] if x]
    if set(types) != want_types:
        problems.append(('typemismatch', name, label, best, f.get('FormName'), types, sorted(want_types)))
    entries.append({'loc': clean_loc(loc), 'dex': dex, 'name': name, 'label': label, 'sid': sid,
                    'form': best, 'formname': f.get('FormName'), 'page_types': [t1, t2]})

json.dump(entries, open(f'{BASE}/data/entries.json', 'w'), ensure_ascii=False)
print(len(entries), 'entries;', len(problems), 'problems')
for pr in problems:
    print(pr)
