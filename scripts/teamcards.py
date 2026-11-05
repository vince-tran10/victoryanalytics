"""Parse TeamCard / PokemonCard templates from Rejuvenation wiki pages into battle records."""
import json, re, sys


def parse_cards(w):
    """Return list of dicts: mode, section, subsection, intro, trainers, mons."""
    out = []
    mode = 'All'
    section = sub = ''
    intro = ''
    pos = 0
    tokens = re.finditer(r'(?P<mode>(?:^|\|-\||<tabber>)\s*(?P<mname>[A-Za-z ]+Mode)\s*=)|(?P<h>^(={3,5})\s*(?P<ht>.*?)\s*\4\s*$)|(?P<tc>\{\{\s*TeamCard)|(?P<party>\{\{\s*Party/(?!Footer)\w+)|(?P<sp>\{\{\s*(?:Single|Boss|Double|Shadow)[ _]Pokemon)',
                         w, re.M)
    for m in tokens:
        if m.group('mode'):
            mode = m.group('mname').strip()
            continue
        if m.group('h'):
            lvl = len(m.group(4))
            title = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', m.group('ht'))
            if lvl == 3:
                section, sub = title, ''
            else:
                sub = title
            # intro text = following lines until next template / heading
            rest = w[m.end():m.end() + 800]
            intro = re.split(r'\{\{|\n=', rest)[0]
            intro = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', intro).replace('<br>', ' ').strip()
            continue
        if m.group('party'):
            hdr = w[m.start():w.find('}}', m.start())]
            names = re.findall(r'\|\s*name\d?\s*=\s*([^\n|]*)', hdr)
            out.append(dict(mode=mode, section=section, sub=sub, intro=intro, trainers=names, mons=[]))
            continue
        if m.group('sp'):
            end = w.find('}}', m.start())
            d = {}
            for k, v in re.findall(r'\|[ \t]*(\w+)[ \t]*=[ \t]*([^\n|]*)', w[m.start():end]):
                d[k.strip()] = v.strip()
            mon = {'specie': d.get('pokemon', '?'), 'level': d.get('level', ''), 'ability': d.get('ability', ''),
                   'nature': d.get('nature', ''), 'heldItem': d.get('held', ''),
                   'types': '/'.join(x for x in [d.get('type1', ''), d.get('type2', '')] if x).lower(),
                   'boss': 'Boss' in m.group('sp'), 'shields': d.get('shields', ''),
                   'evs': ';'.join(d.get(k, '') for k in ('HPEVs', 'AtkEVs', 'DefEVs', 'SAtkEVs', 'SdefEVs', 'SpeEVs'))
                   if d.get('HPEVs') else ''}
            for i in range(1, 5):
                nm = d.get(f'move{i}', '')
                mon[f'move{i}'] = f"{nm};{d.get(f'move{i}type', '').lower()};{d.get(f'move{i}cat', '').lower()}" if nm else ''
            if out:
                out[-1]['mons'].append(mon)
            continue
        # TeamCard: find matching braces
        start = m.start('tc')
        depth, i = 0, start
        while i < len(w):
            if w.startswith('{{', i):
                depth += 1; i += 2; continue
            if w.startswith('}}', i):
                depth -= 1; i += 2
                if depth == 0:
                    break
                continue
            i += 1
        body = w[start:i]
        trainers = re.findall(r'\|\s*trainer\d\s*=\s*([^\n|]*)', body)
        mons = []
        for pc in re.finditer(r'\{\{\s*PokemonCard(.*?)\}\}', body, re.S):
            d = {}
            for k, v in re.findall(r'\|[ \t]*(\w+)[ \t]*=[ \t]*([^\n]*)', pc.group(1)):
                d[k.strip()] = v.strip()
            mons.append(d)
        out.append(dict(mode=mode, section=section, sub=sub, intro=intro, trainers=trainers, mons=mons))
    return out


def fmt_mon(d):
    moves = [d.get(f'move{i}', '').split(';')[0] for i in range(1, 5)]
    form = d.get('form', '')
    return (f"{d.get('specie', '?')}{(' (' + form + ')') if form else ''} Lv{d.get('level', '?')} [{d.get('types', '')}] "
            f"{d.get('ability', '')} / {d.get('nature', '')} @ {d.get('heldItem', '')} : {', '.join(x for x in moves if x)}")


if __name__ == '__main__':
    for f in sys.argv[1:]:
        w = json.load(open(f))['parse']['wikitext']
        for b in parse_cards(w):
            print(f"## {f.split('/')[-1]} | {b['mode']} | {b['section']} | {b['sub']} | {b['trainers']}")
            print('   ', b['intro'][:250])
            for mm in b['mons']:
                print('     -', fmt_mon(mm))
