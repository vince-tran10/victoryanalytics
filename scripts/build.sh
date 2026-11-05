#!/usr/bin/env bash
# Rebuild output/Rejuvenation_Pokemon_Database.xlsx from the Rejuvenation wiki + PokeAPI.
# Usage: scripts/build.sh [work_dir]   (needs curl, python3 with openpyxl; LibreOffice optional for cached values)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(dirname "$HERE")"
WORK="${1:-$REPO/build}"
UA="victoryanalytics-script/1.0"
WIKI="https://rejuvenation.wiki.gg"
mkdir -p "$WORK/raw/abil" "$WORK/raw/custabil" "$WORK/data"

echo "== Fetching Pokémon Locations page"
curl -sSf -A "$UA" "$WIKI/api.php?action=parse&page=Pok%C3%A9mon_Locations&prop=wikitext&format=json&formatversion=2" \
  -o "$WORK/raw/locations.json"

echo "== Fetching game-data modules"
for m in Database/Species Database/Moves Database/Forms Database/TMs Database/Names Database/Types; do
  curl -sSf -A "$UA" "$WIKI/index.php?title=Module:$m&action=raw" -o "$WORK/raw/$(echo "$m" | tr / _).lua"
done

echo "== Parsing Lua data tables (data-only parser, nothing is executed)"
args=()
for n in Database_Species Database_Moves Database_Names Database_TMs Database_Types Database_Forms; do
  args+=("$WORK/raw/$n.lua" "$WORK/data/$n.json")
done
python3 -I "$HERE/luaparse.py" "${args[@]}"

echo "== Matching Locations entries to species/forms"
python3 -I "$HERE/build_entries.py" "$WORK"

echo "== Fetching ability descriptions"
python3 -I - "$WORK" <<'EOF'
import json, subprocess, sys, urllib.parse, os
W = sys.argv[1]
UA = 'victoryanalytics-script/1.0'
def get(u):
    return json.loads(subprocess.run(['curl', '-sSf', '-A', UA, u], capture_output=True, text=True, check=True).stdout)
sp = json.load(open(f'{W}/data/species_patched.json'))
names = json.load(open(f'{W}/data/Database_Names.json'))
ab = set()
for s in sp.values():
    for f in s.values():
        if isinstance(f, dict):
            ab.update(f.get('Abilities') or [])
            if f.get('HiddenAbility'):
                ab.add(f['HiddenAbility'])
slugs = {x['name'].replace('-', '').upper(): x['name'] for x in get('https://pokeapi.co/api/v2/ability?limit=1000')['results']}
custom = {}
for a in sorted(ab):
    if a in slugs:
        out = f'{W}/raw/abil/{slugs[a]}.json'
        if not os.path.exists(out):
            json.dump(get(f'https://pokeapi.co/api/v2/ability/{slugs[a]}'), open(out, 'w'))
    elif a not in ('ASONECHILLING', 'ASONEGRIM'):
        title = {'SACCHARINENECTAR': 'Saccharine Nectar'}.get(a, names.get(a, a))
        r = get('https://rejuvenation.wiki.gg/api.php?action=parse&redirects=1&prop=wikitext&formatversion=2&format=json&page='
                + urllib.parse.quote(title))
        custom[a] = r.get('parse', {}).get('wikitext', '')
json.dump(custom, open(f'{W}/raw/custabil/wikitext.json', 'w'))
print(len(ab), 'abilities;', len(custom), 'Rejuvenation-custom')
EOF

echo "== Building workbook"
python3 -I "$HERE/build_workbook.py" "$WORK" "$WORK/workbook_raw.xlsx"
if [ -n "${RECALC:-}" ]; then
  python3 "$RECALC" "$WORK/workbook_raw.xlsx" 600   # optional: LibreOffice recalc so formulas have cached values
fi
python3 -I "$HERE/postprocess.py" "$WORK/workbook_raw.xlsx" "$REPO/output/Rejuvenation_Pokemon_Database.xlsx"
echo "Done -> output/Rejuvenation_Pokemon_Database.xlsx"
