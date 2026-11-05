"""Inject frozen panes into sheets (openpyxl's write-only mode cannot emit them)."""
import re, shutil, sys, zipfile

src, dst = sys.argv[1], sys.argv[2]
FREEZE = {'Pokemon': (2, 1, 'C2'), 'Learnsets': (4, 1, 'E2'), 'Moves': (1, 1, 'B2'), 'Abilities': (1, 1, 'B2'),
          'Natures': (0, 1, 'A2')}

zin = zipfile.ZipFile(src)
wbxml = zin.read('xl/workbook.xml').decode()
rels = zin.read('xl/_rels/workbook.xml.rels').decode()
sheet_files = {}
for name, rid in re.findall(r'<sheet [^>]*name="([^"]+)"[^>]*r:id="([^"]+)"', wbxml):
    target = re.search(r'Id="%s"[^>]*Target="([^"]+)"' % rid, rels) or re.search(r'Target="([^"]+)"[^>]*Id="%s"' % rid, rels)
    t = target.group(1).lstrip('/')
    sheet_files['xl/' + t if not t.startswith('xl/') else t] = name

tmp = dst + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        name = sheet_files.get(item.filename)
        if name in FREEZE:
            xs, ys, ref = FREEZE[name]
            pane_attr = (f'xSplit="{xs}" ' if xs else '') + f'ySplit="{ys}" topLeftCell="{ref}" '
            active = 'bottomRight' if xs else 'bottomLeft'
            pane = f'<pane {pane_attr}activePane="{active}" state="frozen"/><selection pane="{active}" activeCell="{ref}" sqref="{ref}"/>'
            x = data.decode()
            x, k = re.subn(r'(<sheetView\b[^>]*?)(/>)', r'\1>' + pane + '</sheetView>', x, count=1)
            if not k:
                x = re.sub(r'(<sheetView\b[^>]*>).*?(</sheetView>)', lambda m: m.group(1) + pane + m.group(2), x,
                           count=1, flags=re.S)
            data = x.encode()
        zout.writestr(item, data)
zin.close()
shutil.move(tmp, dst)
print('frozen panes added ->', dst)
