"""Build the set of Pokemon obtainable in chapters 1-7 and compare it with the user's export (family + form level)."""
import json, re, sys, collections
sys.path.insert(0, '/tmp/claude-0/-home-user-victoryanalytics/cbcbf9d1-8dc0-5ce1-a0fe-6353198d6d18/scratchpad/scripts')
from dataset import Data

BASE = '/tmp/claude-0/-home-user-victoryanalytics/cbcbf9d1-8dc0-5ce1-a0fe-6353198d6d18/scratchpad'
D = Data(BASE)
W = json.load(open(sys.argv[1]))
roster = json.load(open(f'{BASE}/team/roster.json'))

rev = {}
for k, v in D.names.items():
    if isinstance(v, str) and k in D.sp:
        rev[v.lower()] = k
rev.update({'nidoran♀': 'NIDORANfE', 'nidoran♂': 'NIDORANmA', 'flabébé': 'FLABEBE', 'nidoran-f': 'NIDORANfE',
            'nidoran-m': 'NIDORANmA', "farfetch'd": 'FARFETCHD', 'mr. mime': 'MRMIME', 'mime jr.': 'MIMEJR',
            'type: null': 'TYPENULL'})
REGIONS = ['Aevian', 'Alolan', 'Galarian', 'Hisuian', 'Paldean']


def base_of(sid, form):
    """Walk to the first stage of the evolution family, keeping the regional/Aevian form tag."""
    seen = 0
    cur, cf = sid, str(form)
    while seen < 6:
        pe, pf = D.prev_evo(cur, cf)
        if not pe:
            break
        cur, cf = pe, str(pf)
        seen += 1
    return cur


def form_tag(sid, form):
    fn = (D.sp[sid].get(str(form)) or {}).get('FormName', '') or ''
    for r in REGIONS:
        if r in fn:
            return r
    return ''


def family_key(sid, form):
    return (base_of(sid, form), form_tag(sid, form))


def parse_name(raw):
    """'Rattata (Alolan)' -> (sid, regional tag)."""
    raw = raw.strip()
    tag = ''
    m = re.match(r'^(.*?)\s*\(([^)]*)\)\s*$', raw)
    nm = raw
    if m:
        nm = m.group(1)
        inner = m.group(2)
        for r in REGIONS:
            if r.lower() in inner.lower():
                tag = r
        if 'aevian' in inner.lower():
            tag = 'Aevian'
    nm = re.sub(r'^(Shadow|Boss|SOS)\s+', '', nm).strip()
    sid = rev.get(nm.lower())
    if not sid:
        sid = rev.get(nm.split(' ')[0].lower())
    return sid, tag


def fam_of(sid, tag):
    # find the form index carrying the tag, then the family base
    form = '0'
    if tag:
        for k in [k for k in D.sp[sid] if k.isdigit()]:
            if tag in (D.sp[sid][k].get('FormName') or ''):
                form = k; break
    return (base_of(sid, form), tag)


avail = collections.defaultdict(list)   # family -> list of (source, chapter, area)
unknown = collections.Counter()
def clean_enc(nm):
    lines = [l.strip() for l in nm.split('\n') if l.strip()]
    first = re.sub(r',\s*Lv\..*$', '', lines[0])
    form = next((l for l in lines[1:] if l.endswith('Form')), '')
    if form:
        first += f' ({form.replace(" Form", "")})'
    return first


for e in W['encounters']:
    for nm in e['mons']:
        if nm.startswith('Shield Break') or nm.startswith('Shiny'):
            continue
        nm = clean_enc(nm)
        sid, tag = parse_name(nm)
        if not sid:
            unknown[nm] += 1; continue
        avail[fam_of(sid, tag)].append(('Wild: ' + e['title'].replace(' Encounters', ''), e['chapter'], e['area'], nm))
for dn in W['dens']:
    badges = re.search(r'\((\d+) Badges?\)', dn['text'])
    b = int(badges.group(1)) if badges else 0
    if b > 7:
        continue
    for nm in re.findall(r'Shadow ([A-Z][\w\.\'é\- ]+?), Lv\.', dn['text']):
        sid, tag = parse_name(nm)
        if not sid:
            unknown[nm] += 1; continue
        title = dn['text'].split('\n')[0].replace('Encounters: ', '')
        avail[fam_of(sid, tag)].append((f'Rift Den (shadow): {title}', dn['chapter'], dn['area'], 'Shadow ' + nm))

# prose: acquisition sentences
names_sorted = sorted(rev.keys(), key=len, reverse=True)
name_re = re.compile(r'\b(' + '|'.join(re.escape(n) for n in names_sorted if len(n) > 2) + r')\b(\s*\((?:[A-Za-z]+(?: Form)?)\))?', re.I)
VERB = re.compile(r'\b(catch|caught|receive|received|get|gets|got|obtain|gift|gifts|given|give you|gives you|trade|traded|egg|hatch|snag|snagged|find|found|encounter|static|wild|battle .{0,20}and catch|adopt|reward)\b', re.I)
prose_hits = []
for p in W['prose']:
    t = p['text']
    for sent in re.split(r'(?<=[.!?])\s+', t):
        if not VERB.search(sent):
            continue
        for m in name_re.finditer(sent):
            nm = m.group(1) + (m.group(2) or '')
            sid, tag = parse_name(nm)
            if not sid:
                continue
            # skip item-like or person names that collide (e.g. "Ditto" fine); keep
            prose_hits.append((fam_of(sid, tag), p['chapter'], p['area'], sent.strip()[:300], nm))
for fam, ch, area, sent, nm in prose_hits:
    avail[fam].append(('Story/gift/static (text)', ch, area, sent))

# owned families
owned = collections.defaultdict(list)
for m in roster:
    owned[family_key(m['sid'], m['form'])].append(m['name'])

missing = {f: v for f, v in avail.items() if f not in owned}
json.dump({'avail': {f'{k[0]}|{k[1]}': v for k, v in avail.items()},
           'missing': {f'{k[0]}|{k[1]}': v for k, v in missing.items()},
           'owned': {f'{k[0]}|{k[1]}': v for k, v in owned.items()}},
          open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
print('available families:', len(avail), 'owned families:', len(owned), 'missing:', len(missing))
print('unparsed names:', unknown.most_common(20))
wild_missing = {f: v for f, v in missing.items() if any(not s[0].startswith('Story') for s in v)}
text_only = {f: v for f, v in missing.items() if f not in wild_missing}
print('\nMISSING (wild / den):', len(wild_missing))
for f, v in sorted(wild_missing.items(), key=lambda x: x[1][0][1]):
    srcs = [s for s in v if not s[0].startswith('Story')]
    print(f"  {D.nm(f[0])}{' (' + f[1] + ')' if f[1] else ''}: " + '; '.join(sorted({f'{s[0]} [{s[1][:10]}]' for s in srcs}))[:300])
print('\nMISSING (mentioned in story text only – needs manual review):', len(text_only))
for f, v in sorted(text_only.items(), key=lambda x: x[1][0][1]):
    print(f"  {D.nm(f[0])}{' (' + f[1] + ')' if f[1] else ''}: [{v[0][1][:10]} / {v[0][2]}] {v[0][3][:220]}")
