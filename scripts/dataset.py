"""Assemble per-entry data (stats, abilities, learnset) from the parsed game modules."""
import json, re

UNIVERSAL = ["ATTRACT", "CAPTIVATE", "CONFIDE", "DOUBLETEAM", "ENDURE", "FACADE", "FRUSTRATION", "HIDDENPOWER",
             "NATURALGIFT", "PROTECT", "REST", "RETURN", "ROUND", "SECRETPOWER", "SLEEPTALK", "SNORE", "SUBSTITUTE",
             "SWAGGER", "TOXIC"]


class Data:
    def __init__(self, base):
        self.sp = json.load(open(f'{base}/data/species_patched.json'))
        self.moves = json.load(open(f'{base}/data/Database_Moves.json'))
        self.names = json.load(open(f'{base}/data/Database_Names.json'))
        self.tms = json.load(open(f'{base}/data/Database_TMs.json'))
        types = json.load(open(f'{base}/data/Database_Types.json'))
        self.chart = {k: v for k, v in types.items() if isinstance(v, dict)}
        self.entries = json.load(open(f'{base}/data/entries.json'))

    def form(self, sid, idx):
        species = self.sp[sid]
        f = species[str(idx)]
        fb = f.get('formBase')
        parent = self.form(sid, fb) if fb not in (None, '', 0, '0') and str(fb) != str(idx) else species['0']
        merged = dict(parent)
        merged.update(f)
        return merged

    def prev_evo(self, sid, idx):
        f = self.sp[sid].get(str(idx)) or self.sp[sid]['0']
        pe = f.get('PreEvolutions') or (self.sp[sid]['0'].get('PreEvolutions') if str(idx) == '0' else None)
        if pe and isinstance(pe, list) and pe and pe[0] in self.sp:
            pidx = pe[1] if len(pe) > 1 else 0
            if str(pidx) not in self.sp[pe[0]]:
                pidx = 0
            return pe[0], pidx
        return None, None

    def learnset(self, sid, idx):
        """list of (move_id, method, detail)"""
        f = self.form(sid, idx)
        out, seen = [], set()

        def add(mid, method, detail=''):
            key = (mid, method)
            if mid in self.moves and key not in seen:
                seen.add(key); out.append((mid, method, detail))
        lv = f.get('Moves') or []
        for i in range(0, len(lv) - 1, 2):
            lvl = lv[i]
            add(lv[i + 1], 'Level-up', 'Evo' if lvl == 0 else str(lvl))
        comp = list(f.get('CompatibleMoves') or []) + list(f.get('Tutor') or [])
        if comp:
            comp = comp + [u for u in UNIVERSAL if u not in comp]
            exc = set(f.get('MoveExceptions') or [])
            tutors = self.tms.get('TUTORS', {})
            for mid in comp:
                if mid in exc:
                    continue
                tm = self.tms.get(mid)
                if isinstance(tm, str):
                    add(mid, 'TM', tm)
                if mid in tutors:
                    loc = tutors[mid]
                    add(mid, 'Tutor', ', '.join(loc) if isinstance(loc, list) else str(loc))
                if not isinstance(tm, str) and mid not in tutors:
                    add(mid, 'TM/Tutor', '')
        for mid in f.get('RelearnerMoves') or []:
            add(mid, 'Move Relearner', '')
        # egg moves along the pre-evolution chain
        cur, ci, guard = sid, idx, 0
        while cur and guard < 5:
            cf = self.sp[cur].get(str(ci)) or self.sp[cur]['0']
            em = cf.get('EggMoves') if 'EggMoves' in cf else (self.sp[cur]['0'].get('EggMoves') if str(ci) == '0' else None)
            for mid in em or []:
                add(mid, 'Egg', '' if cur == sid else self.names.get(cur, cur))
            cur, ci = self.prev_evo(cur, ci)
            guard += 1
        return out

    def is_nfe(self, sid, idx):
        f = self.form(sid, idx)
        ev = f.get('Evolutions') or []
        return isinstance(ev, list) and len(ev) > 0 and ev[0] in self.sp

    def evolves_to(self, sid, idx):
        f = self.form(sid, idx)
        ev = f.get('Evolutions') or []
        res = []
        if isinstance(ev, list):
            for i in range(0, len(ev), 5):
                chunk = ev[i:i + 5]
                if chunk and chunk[0] in self.sp:
                    method = ' '.join(str(x) for x in chunk[2:] if x not in ('', None))
                    res.append(f"{self.names.get(chunk[0], chunk[0])} ({method})")
        return '; '.join(res)

    def nm(self, key):
        return self.names.get(key, key.title() if key else '')
