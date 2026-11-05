"""Matchup engine: rate every owned Pokemon against the Chapter 8 hard-mode bosses at the level cap.

Rules mirrored from the user's workbook:
  * level cap 55; evaluate each mon fully evolved (if the evolution is reachable) with an optimised spread
  * legal moves = level-up at or below the cap (incl. evolution / Lv1 moves), Egg moves, TM17 Protect,
    TM54 False Swipe, plus anything the mon already knows
  * no Life Orb; Megas locked (Omni Ring is Chapter 12); no Trick Room yet
"""
import json, math, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dataset import Data
from recommend import (move_base_value, ability_move_mult, ability_stat_mult, EXCLUDE, TWO_TURN, type_eff as _te)
from bosses import load_battles, load_battles_walk, FIELD, HIGH_STRIKER

CAP = 55
# tutors open to a 7-badge player who has finished chapters 1-7 (Luck's Tent tiers up to 7 badges, Wispy Shop, Kakori/Terajuma Beach)
# Tutors count only when the wiki lists a badge number and it is <= 7 (Vincent's rule, 11-05).
# Tutors with no badge number (plain Luck's Tent, Wispy Path Shop, Akuwa Town, ...) are skipped.
ALLOWED_TUTORS = {"Luck's Tent, 3 Badges", "Luck's Tent, 5 Badges", "Luck's Tent, 7 Badges", "Terajuma Beach, 5 Badges",
                  "Luck's Tent, 3 Badges, Hiyoshi City", "Luck's Tent, 5 Badges, Hiyoshi City", "Luck's Tent, 7 Badges, Hiyoshi City"}
# evolution items obtainable in Chapters 1-7 (BIGJRA walkthrough). Not: Peat Block, Razor Claw/Fang, King's Rock,
# Prism Scale, Protector, Electirizer, Magmarizer, Dubious Disc, Oval Stone, Linking Cord.
ITEMS_CH1_7 = {'SUNSTONE', 'SHINYSTONE', 'MOONSTONE', 'LEAFSTONE', 'WATERSTONE', 'FIRESTONE', 'THUNDERSTONE', 'ICESTONE',
               'DUSKSTONE', 'DAWNSTONE', 'UPGRADE', 'REAPERCLOTH', 'SACHET', 'WHIPPEDDREAM', 'GALARICACUFF',
               'GALARICAWREATH', 'SWEETAPPLE', 'TARTAPPLE', 'METALCOAT'}
STATS = ['HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe']
NATURES = {
    'Hardy': (None, None), 'Docile': (None, None), 'Serious': (None, None), 'Bashful': (None, None), 'Quirky': (None, None),
    'Lonely': ('Atk', 'Def'), 'Brave': ('Atk', 'Spe'), 'Adamant': ('Atk', 'SpA'), 'Naughty': ('Atk', 'SpD'),
    'Bold': ('Def', 'Atk'), 'Relaxed': ('Def', 'Spe'), 'Impish': ('Def', 'SpA'), 'Lax': ('Def', 'SpD'),
    'Timid': ('Spe', 'Atk'), 'Hasty': ('Spe', 'Def'), 'Jolly': ('Spe', 'SpA'), 'Naive': ('Spe', 'SpD'),
    'Modest': ('SpA', 'Atk'), 'Mild': ('SpA', 'Def'), 'Quiet': ('SpA', 'Spe'), 'Rash': ('SpA', 'SpD'),
    'Calm': ('SpD', 'Atk'), 'Gentle': ('SpD', 'Def'), 'Sassy': ('SpD', 'Spe'), 'Careful': ('SpD', 'SpA')}
TYPE_ITEMS = {'Metal Coat': 'STEEL', 'Black Belt': 'FIGHTING', 'Hard Stone': 'ROCK', 'Soft Sand': 'GROUND',
              'Dragon Fang': 'DRAGON', 'Black Glasses': 'DARK', 'Magnet': 'ELECTRIC', 'Mystic Water': 'WATER',
              'Never-Melt Ice': 'ICE', 'Poison Barb': 'POISON', 'Fairy Feather': 'FAIRY', 'Charcoal': 'FIRE',
              'Miracle Seed': 'GRASS', 'Sharp Beak': 'FLYING', 'Silver Powder': 'BUG', 'Spell Tag': 'GHOST',
              'Twisted Spoon': 'PSYCHIC', 'Silk Scarf': 'NORMAL', 'Spooky Plate': 'GHOST'}
SPREAD_TARGETS = ('AllOpposing', 'AllNonUsers')
FOE_ABIL_IMMUNE = {'LEVITATE': 'GROUND', 'FLASHFIRE': 'FIRE', 'LIGHTNINGROD': 'ELECTRIC', 'LIGHTININGROD': 'ELECTRIC',
                   'VOLTABSORB': 'ELECTRIC', 'MOTORDRIVE': 'ELECTRIC', 'WATERABSORB': 'WATER', 'STORMDRAIN': 'WATER',
                   'DRYSKIN': 'WATER', 'SAPSIPPER': 'GRASS', 'EARTHEATER': 'GROUND', 'WELLBAKEDBODY': 'FIRE'}
SOUND = None


def norm_ab(a):
    return re.sub(r'[^A-Z]', '', (a or '').upper())


def stat(base, ev, nat_mult, level=CAP, iv=31, hp=False):
    if hp:
        if base == 1:
            return 1
        return math.floor((2 * base + iv + ev // 4) * level / 100) + level + 10
    return math.floor((math.floor((2 * base + iv + ev // 4) * level / 100) + 5) * nat_mult)


def calc_stats(bs, evs, nature, level=CAP):
    up, down = NATURES.get(nature, (None, None))
    out = {}
    for s in STATS:
        nm = 1.1 if s == up else 0.9 if s == down else 1.0
        if up == down:
            nm = 1.0
        out[s] = stat(bs[s], evs.get(s, 0), nm, level, hp=(s == 'HP'))
    return out


class Engine:
    def __init__(self, base):
        self.D = Data(base)
        self.byname = {}
        for k, v in self.D.moves.items():
            self.byname.setdefault(v['MoveName'].lower(), k)
        self.byname.update({'stomp tantrum': 'STOMPINGTANTRUM', 'lightiningrod': 'LIGHTNINGROD'})
        self.rev = {v: k for k, v in self.D.names.items() if isinstance(v, str) and k in self.D.sp}
        self.move_rules = os.environ.get('MOVE_RULES', 'strict')
        try:
            self.allowed_tms = set(json.load(open(f'{base}/team/allowed_tms.json'))['tms'])
            self.allowed_tms |= set(x for x in os.environ.get('EXTRA_TMS', '').split(',') if x)
        except OSError:
            self.allowed_tms = set()
        self.battles = load_battles_walk(base) if os.environ.get('WALK', '1') == '1' else load_battles(base)
        done = set(filter(None, os.environ.get('DONE', '').split(',')))      # fights already beaten
        self.battles = [b for b in self.battles if b['key'] not in done]
        sw = float(os.environ.get('SINGLES_W', '1'))                         # weight singles fights more
        for b in self.battles:
            if b['format'] == 'Singles':
                b['weight'] *= sw
        for b in self.battles:
            b['foes'] = [self.build_foe(m, b) for m in b['mons']]
            b['foe_intimidate'] = any(f['ability'] == 'INTIMIDATE' for f in b['foes'])
            if os.environ.get('FORCE_FORMAT') in ('Singles', 'Doubles'):
                b['format'] = os.environ['FORCE_FORMAT']

    # ------------------------------------------------------------ helpers
    def chart_eff(self, atk_type, def_types):
        e = 1.0
        for t in def_types:
            e *= _te(atk_type, t.capitalize(), self.D.chart)
        return e

    def move_id(self, name):
        return self.byname.get((name or '').strip().lower())

    def build_foe(self, m, battle):
        name = m['specie']
        sid = self.rev.get(name) or self.rev.get(name.split(' ')[0])
        types = [t.upper() for t in re.split(r'[/ ]', m.get('types') or '') if t]
        form = '0'
        if sid:
            for k in [k for k in self.D.sp[sid] if k.isdigit()]:
                f = self.D.form(sid, k)
                ft = [x for x in [f.get('Type1'), f.get('Type2')] if x]
                if types and set(ft) == set(types) and not re.search(r'Mega|Giga', f.get('FormName', '')):
                    form = k; break
            f = self.D.form(sid, form)
            bs = dict(zip(STATS, f['BaseStats']))
            if not types:
                types = [x for x in [f.get('Type1'), f.get('Type2')] if x]
        else:
            bs = {s: 90 for s in STATS}
        if m.get('base_override'):
            bs = dict(zip(STATS, m['base_override']))
        reg = next((r for r in ('Alolan', 'Galarian', 'Hisuian', 'Paldean', 'Aevian') if r in (m.get('form_text') or '')), None)
        if reg and sid and not m.get('base_override'):
            for k in [k for k in self.D.sp[sid] if k.isdigit()]:
                f = self.D.form(sid, k)
                if reg in (f.get('FormName') or ''):
                    form = k; bs = dict(zip(STATS, f['BaseStats']))
                    types = [x for x in [f.get('Type1'), f.get('Type2')] if x]
        if name == 'Silvally' and 'Memory' in (m.get('heldItem') or ''):
            types = [m['heldItem'].split()[0].upper()]
        if name == 'Minior':
            bs = {'HP': 60, 'Atk': 60, 'Def': 100, 'SpA': 60, 'SpD': 100, 'Spe': 60}  # Meteor form until 50% HP
        evs_raw = m.get('evs') or ''
        try:
            ev = [int(x) for x in evs_raw.split(';')] if evs_raw else [85] * 6
        except ValueError:
            ev = [85] * 6
        evs = dict(zip(STATS, ev + [0] * (6 - len(ev))))
        nat = (m.get('nature') or 'Hardy').capitalize()
        lvl = int(re.sub(r'\D', '', str(m.get('level') or '50')) or 50)
        st = calc_stats(bs, evs, nat, lvl)
        moves = []
        for i in range(1, 5):
            raw = m.get(f'move{i}', '')
            if not raw:
                continue
            parts = raw.split(';')
            mid = self.move_id(parts[0])
            if not mid:
                continue
            mv = dict(self.D.moves[mid])
            if mid == 'HIDDENPOWER' and len(parts) > 1 and parts[1]:
                mv['Type'] = parts[1].upper(); mv['Strength'] = '60'
            if mid == 'FEVERPITCH':
                mv['Strength'] = '80'
            if mid == 'MULTIATTACK':
                mv['Type'] = types[0]
            moves.append((mid, mv))
        ability = norm_ab(m.get('ability'))
        hp_mult = 1 + (int(m['shields']) if str(m.get('shields') or '').isdigit() else 0) * 0.6 if m.get('boss') else 1
        return dict(name=name, sid=sid, types=types, stats=st, level=lvl, moves=moves, ability=ability,
                    item=m.get('heldItem', ''), hp_mult=hp_mult, raw=m)

    # ------------------------------------------------------------ damage
    def damage_pct(self, att, dfn, mid, mv, battle, att_is_me):
        """Expected % of defender max HP for one use (average roll)."""
        cat = mv['Category']
        if cat == 'Status':
            return 0.0
        field = FIELD.get(battle['field'], {})
        ctx = {'weight': att.get('weight', 50), 'spe': att['stats']['Spe'], 'setup': False}
        p, _ = move_base_value(mid, mv, ctx)
        if p <= 0:
            return 0.0
        # accuracy: move_base_value folds accuracy into p; correct it for No Guard and Gravity (Deep Earth, 1.67x in Rejuv)
        acc = int(mv.get('Accuracy') or 0)
        if 0 < acc < 100:
            accf = acc / 100
            if att.get('ability') == 'NOGUARD' or dfn.get('ability') == 'NOGUARD':
                p = p / accf
            elif FIELD.get(battle['field'], {}).get('gravity'):
                p = p / accf * min(1.0, accf * 1.67)
        mtype = mv['Type']
        mult = 1.0
        ab = att['ability']
        if att_is_me:
            t2, am, stab_o = ability_move_mult(ab, (mid, dict(mv, _power=p, _drawback=1.0)), mtype, att['types'])
            mtype = t2; mult *= am
        else:
            stab_o = 2.0 if ab == 'ADAPTABILITY' and mtype in att['types'] else None
        if mid == 'SKILLLINK':
            pass
        # field
        flags = set(mv.get('DataFlags') or [])
        fm = field.get('types', {}).get(mtype, 1.0) * field.get('moves', {}).get(mid, 1.0)
        if 'Soundmove' in flags:
            fm *= field.get('sound', 1.0)
        if field.get('noncontact_flying') and mtype == 'FLYING' and 'Contact' not in flags:
            fm *= field['noncontact_flying']
        if field.get('striker') and ((mtype == 'FIGHTING' and cat == 'Physical') or mid in HIGH_STRIKER):
            fm *= 2.47 if ab in ('GUTS', 'HUGEPOWER', 'PUREPOWER', 'SHEERFORCE') else 1.33
        if battle['field'] == 'Corrupted Cave' and battle.get('sun'):
            pass
        if field.get('ground_vs_nonground') and mtype == 'GROUND':
            fm *= field['ground_vs_nonground'] if 'GROUND' not in dfn['types'] else 0.5
        if field.get('priority') and int(mv.get('Priority') or 0) > 0:
            fm *= field['priority']
        if battle['key'] == 'groudon':  # Drought sun
            fm *= 1.5 if mtype == 'FIRE' else 0.5 if mtype == 'WATER' else 1.0
        if battle['key'] == 'kyogre':   # Drizzle rain
            fm *= 1.5 if mtype == 'WATER' else 0.5 if mtype == 'FIRE' else 1.0
        if mid in ('FLOWERTRICK', 'FROSTBREATH', 'STORMTHROW', 'ZIPPYZAP'):
            fm *= 1.5   # always a critical hit
        if att_is_me and ab == 'GRASSYSURGE' and mtype == 'GRASS':
            fm *= 1.3   # Grassy Terrain on entry
        if not att_is_me:   # foe gems: 1.3x on the matching type; Acrobatics doubles once the gem is used
            it = (att.get('item') or '')
            if it.endswith(' Gem') and it.split()[0].upper() == mtype:
                fm *= 1.3 * (2 if mid == 'ACROBATICS' else 1)
            elif mid == 'ACROBATICS' and not it:
                fm *= 2
        mult *= fm
        # stats
        am_stat = ability_stat_mult(ab) if att_is_me else (1, 1, 1)
        if mv['MoveName'] == 'Body Press':
            A = att['stats']['Def']
        elif cat == 'Physical':
            A = att['stats']['Atk'] * am_stat[0]
        else:
            A = att['stats']['SpA'] * am_stat[1]
        mult *= am_stat[2]
        if att_is_me and ab in ('GUTS', 'TOXICBOOST', 'FLAREBOOST') and att.get('item') not in ('Flame Orb', 'Toxic Orb') \
                and battle['field'] not in ('Corrupted Cave',):
            A /= 1.5   # needs a status orb to switch on (Corrupted Cave poisons you anyway)
        if mid == 'FOULPLAY':
            A = dfn['stats']['Atk']
        Dv = dfn['stats']['Def'] if cat == 'Physical' or mid in ('PSYSHOCK', 'PSYSTRIKE', 'SECRETSWORD') else dfn['stats']['SpD']
        # items
        item = att.get('item', '') or ''
        if TYPE_ITEMS.get(item) == mtype:
            mult *= 1.2
        if item == 'Whiscash Crest':
            mult *= 1.2
        if item == 'Life Orb':
            mult *= 1.3
        if item in ('Wise Glasses',) and cat == 'Special':
            mult *= 1.1
        if item in ('Muscle Band',) and cat == 'Physical':
            mult *= 1.1
        if item == 'Thick Club':
            A *= 2
        if item in ('Choice Band',) and cat == 'Physical':
            A *= 1.5
        if item in ('Choice Specs',) and cat == 'Special':
            A *= 1.5
        if dfn.get('item') == 'Assault Vest' and cat == 'Special':
            Dv *= 1.5
        if dfn.get('item') == 'Eviolite':
            Dv *= 1.5
        # type effectiveness + immunities
        gravity = field.get('gravity')
        eff = self.chart_eff(mtype, [t for t in dfn['types'] if not (gravity and mtype == 'GROUND' and t == 'FLYING')])
        dab = dfn['ability']
        if gravity and mtype == 'GROUND' and dab == 'LEVITATE':
            dab = ''
        if FOE_ABIL_IMMUNE.get(dab) == mtype or (mtype == 'GROUND' and dfn.get('item') == 'Air Balloon' and not gravity):
            eff = 0
        if dfn.get('item') == 'Whiscash Crest' and mtype == 'GRASS':
            eff = 0
        if dfn.get('item') == 'Skuntank Crest' and mtype == 'GROUND':
            eff = 0
        if dab == 'GOODASGOLD' and cat == 'Status':
            eff = 0
        if dab == 'WONDERGUARD' and eff <= 1:
            eff = 0
        if eff == 0:
            return 0.0
        if dab in ('FILTER', 'SOLIDROCK', 'PRISMARMOR') and eff > 1:
            mult *= 0.75
        if dab == 'MULTISCALE' or dab == 'SHADOWSHIELD':
            mult *= 0.75  # full-HP halving, averaged over the fight
        if dab == 'THICKFAT' and mtype in ('FIRE', 'ICE'):
            mult *= 0.5
        if dab == 'HEATPROOF' and mtype == 'FIRE':
            mult *= 0.5
        if dab == 'WATERBUBBLE' and mtype == 'FIRE':
            mult *= 0.5
        if dab == 'FURCOAT' and cat == 'Physical':
            mult *= 0.5
        if dab == 'ICESCALES' and cat == 'Special':
            mult *= 0.5
        if dab == 'FLUFFY' and 'Contact' in flags:
            mult *= 0.5
        if dab == 'PUNKROCK' and 'Soundmove' in flags:
            mult *= 0.5
        if dab == 'DRYSKIN' and mtype == 'FIRE':
            mult *= 1.25
        if dab == 'BULLETPROOF' and ('BALL' in mid or 'BOMB' in mid or mid in ('FOCUSBLAST', 'AURASPHERE')):
            return 0.0
        if dab == 'SOUNDPROOF' and 'Soundmove' in flags:
            return 0.0
        if dab == 'INTIMIDATE' and cat == 'Physical' and not att_is_me:
            pass
        if dfn.get('my_intimidate_vs') and cat == 'Physical':
            mult *= 0.8
        if att_is_me and battle.get('foe_intimidate') and cat == 'Physical' and ab not in ('DEFIANT', 'CLEARBODY', 'INNERFOCUS', 'OWNTEMPO', 'OBLIVIOUS', 'SCRAPPY'):
            mult *= 0.85
        if att_is_me and ab == 'DEFIANT' and battle.get('foe_intimidate') and cat == 'Physical':
            mult *= 1.25
        # stab
        stab = stab_o if stab_o else (1.5 if mtype in att['types'] else 1.0)
        if item == 'Expert Belt' and eff > 1:
            mult *= 1.2
        # spread in doubles
        if battle['format'] == 'Doubles' and mv.get('Target') in SPREAD_TARGETS:
            mult *= 0.75
        if ab in ('TRUANT', 'SLOWSTART'):
            mult *= 0.5
        if ab == 'DEFEATIST':
            mult *= 0.8
        L = att['level']
        base = math.floor(math.floor(math.floor(2 * L / 5 + 2) * p * A / max(1, Dv)) / 50) + 2
        dmg = base * stab * eff * mult * 0.925
        hp = dfn['stats']['HP'] * dfn.get('hp_mult', 1)
        return 100.0 * dmg / max(1, hp)

    # ------------------------------------------------------------ my mons
    def legal_moves(self, sid, form, known):
        """Level-up <= cap, Egg moves, Protect, False Swipe, known moves."""
        legal = set()
        for mid, method, detail in self.D.learnset(sid, form):
            if method == 'Level-up' and (detail == 'Evo' or (detail.isdigit() and int(detail) <= CAP)):
                legal.add(mid)
            elif method == 'Egg':
                legal.add(mid)
            elif self.move_rules in ('ch7', 'ch7_notutor', 'relearn') and method == 'TM' and detail in self.allowed_tms:
                legal.add(mid)
            elif self.move_rules in ('ch7', 'relearn') and method in ('Tutor', 'TM/Tutor') and detail in ALLOWED_TUTORS:
                legal.add(mid)
            elif self.move_rules == 'relearn' and method == 'Move Relearner':
                legal.add(mid)   # Move Relearner unlocked (11-05): relearner-only moves + any level-up move <= cap
        legal |= {'PROTECT', 'FALSESWIPE'}
        for k in known:
            mid = self.move_id(k)
            if mid:
                legal.add(mid)
        return legal

    def final_form(self, sid, form, level):
        """Follow evolutions that can happen at or below the cap. Returns (sid, form, path_text)."""
        path = []
        self._gate = ''
        cur, cf = sid, form
        for _ in range(3):
            f = self.D.form(cur, cf)
            ev = f.get('Evolutions') or []
            if not (isinstance(ev, list) and ev and ev[0] in self.D.sp):
                break
            nxt, nform, method, param = ev[0], str(ev[1]) if len(ev) > 1 else '0', ev[2] if len(ev) > 2 else '', ev[3] if len(ev) > 3 else ''
            if method.startswith('Level') and str(param).isdigit() and int(param) > CAP:
                path.append(f'{self.D.nm(nxt)} needs Lv {param} (past cap)')
                break
            if str(nform) not in self.D.sp[nxt]:
                nform = '0'
            # regional forms evolve into the same regional form when it exists
            fn = self.D.sp[cur][str(cf)].get('FormName', '')
            if cf != '0':
                for k in [k for k in self.D.sp[nxt] if k.isdigit()]:
                    if self.D.sp[nxt][k].get('FormName', '').split()[0] == fn.split()[0]:
                        nform = k; break
            path.append(f'{self.D.nm(nxt)} ({method} {param})'.replace(' )', ')'))
            if (method.startswith('Item') or 'Item' in method) and str(param).upper() in ITEMS_CH1_7:
                pass   # evolution item obtainable in Chapters 1-7: evolve right away
            elif method.startswith('Item') or method.startswith('Trade') or 'Item' in method:
                self._gate = f'{method} {self.D.nm(param) if param else ""}'.strip()
            cur, cf = nxt, nform
        return cur, cf, '; '.join(path)

    def build_me(self, mon, evolve=True, ability_override=None):
        sid, form = mon['sid'], mon['form']
        evo_text = ''
        if evolve:
            sid2, form2, evo_text = self.final_form(sid, form, mon.get('level', 1))
            if 'past cap' in evo_text and sid2 == sid:
                pass
            sid, form = sid2, form2
        gate = getattr(self, '_gate', '') if evolve else ''
        f = self.D.form(sid, form)
        bs = dict(zip(STATS, f['BaseStats']))
        types = [x for x in [f.get('Type1'), f.get('Type2')] if x]
        abil_list = list(f.get('Abilities') or []) + ([f['HiddenAbility']] if f.get('HiddenAbility') else [])
        ab = norm_ab(mon.get('ability'))
        if ability_override:
            ab = ability_override
        if ab not in abil_list:
            # evolved: keep the same ability slot
            prev = self.D.form(mon['sid'], mon['form'])
            plist = list(prev.get('Abilities') or []) + ([prev['HiddenAbility']] if prev.get('HiddenAbility') else [])
            idx = plist.index(ab) if ab in plist else 0
            ab = abil_list[min(idx, len(abil_list) - 1)] if abil_list else ''
        legal = self.legal_moves(sid, form, mon.get('moves', []))
        try:
            weight = float(f.get('Weight') or 50)
        except ValueError:
            weight = 50
        final_name = self.D.nm(sid) + ('' if form == '0' else f" ({f.get('FormName')})")
        return dict(name=final_name, owned_as=mon['name'], sid=sid, form=form, formname=f.get('FormName'), types=types, base=bs,
                    abilities=abil_list, ability=ab, legal=legal, item=mon.get('item', ''), weight=weight,
                    evo=evo_text, gate=gate, level=CAP, src=mon)

    def spread_for(self, me):
        bs = me['base']
        # decide category by best damage potential later; default by base stats
        phys = bs['Atk'] * (2 if me['ability'] in ('HUGEPOWER', 'PUREPOWER') else 1)
        cat = 'Physical' if phys >= bs['SpA'] else 'Special'
        key = 'Atk' if cat == 'Physical' else 'SpA'
        fast = bs['Spe'] >= 85
        evs = {key: 252, ('Spe' if fast else 'HP'): 252, 'Def' if fast else 'SpD': 4}
        if bs['HP'] == 1:
            evs = {key: 252, 'Spe': 252}
        nature = {'Atk': 'Adamant', 'SpA': 'Modest'}[key]
        return cat, evs, nature

    def damaging_moves(self, me):
        return [(mid, self.D.moves[mid]) for mid in me['legal']
                if mid in self.D.moves and self.D.moves[mid]['Category'] != 'Status'
                and mid not in EXCLUDE and self.D.moves[mid]['Type'] not in ('SHADOW', 'QMARKS')]

    def pick_moves(self, me, n=3, threshold=0.04):
        """Greedy: choose n attacks maximising capped damage summed over every Chapter 8 foe."""
        cand = self.damaging_moves(me)
        known = {self.move_id(x) for x in me['src'].get('moves', [])}
        table = {}
        for mid, mv in cand:
            vals = []
            for b in self.battles:
                for foe in b['foes']:
                    d = self.damage_pct(me, foe, mid, mv, b, True)
                    if mid in TWO_TURN and not (b['key'] == 'groudon' and mid in ('SOLARBEAM', 'SOLARBLADE')):
                        d *= 0.5
                    if 'Cooldown' in (mv.get('DataFlags') or []):
                        d *= 0.6
                    _, draw = move_base_value(mid, mv, {'weight': me.get('weight', 50), 'spe': me['stats']['Spe'], 'setup': False})
                    d *= min(draw, 1.15)
                    if b['format'] == 'Doubles' and mid in ('OUTRAGE', 'PETALDANCE', 'THRASH', 'RAGINGFURY'):
                        d *= 0.8   # locked + confused while the AI retargets
                    if mid in known:
                        d *= 1.1   # already learned: keep unless clearly worse
                    vals.append(min(d, 100) * b['weight'])
            table[mid] = vals
        chosen = []
        while len(chosen) < n and table:
            def total(sel):
                if not sel:
                    return 0
                return sum(max(table[m][i] for m in sel) for i in range(len(next(iter(table.values())))))
            base = total(chosen)
            locking = {'OUTRAGE', 'PETALDANCE', 'THRASH', 'RAGINGFURY'}
            best = max((m for m in table if m not in chosen and not (m in locking and locking & set(chosen))),
                       key=lambda m: total(chosen + [m]), default=None)
            if best is None or total(chosen + [best]) - base < max(1, threshold * base):
                break
            chosen.append(best)
        return chosen

    def evaluate(self, me, moveset=None):
        cat, evs, nature = self.spread_for(me)
        me['stats'] = calc_stats(me['base'], evs, nature)
        me['nature'], me['evs'], me['cat'] = nature, evs, cat
        damaging = self.damaging_moves(me)
        if moveset is not None:
            damaging = [(m, mv) for m, mv in damaging if m in moveset]
        res = {}
        for b in self.battles:
            rows = []
            for foe in b['foes']:
                foe['my_intimidate_vs'] = False
                best, bestmv = 0.0, ''
                for mid, mv in damaging:
                    d = self.damage_pct(me, foe, mid, mv, b, True)
                    # penalise two-turn / recharge / self-KO for real usability
                    if mid in TWO_TURN and not (b['key'] == 'groudon' and mid in ('SOLARBEAM', 'SOLARBLADE')):
                        d *= 0.5
                    if mv.get('DataFlags') and 'Cooldown' in mv['DataFlags']:
                        d *= 0.6
                    if d > best:
                        best, bestmv = d, mv['MoveName']
                foe_for_def = dict(foe)
                taken, takenmv = 0.0, ''
                me_def = dict(me)
                me_def['hp_mult'] = 1
                for mid, mv in foe['moves']:
                    d = self.damage_pct(foe, me_def, mid, mv, b, False)
                    if me['ability'] == 'INTIMIDATE' and mv['Category'] == 'Physical':
                        d *= 0.8
                    if d > taken:
                        taken, takenmv = d, mv['MoveName']
                my_spe = me['stats']['Spe']
                foe_spe = foe['stats']['Spe'] * (1.5 if foe['item'] == 'Choice Scarf' else 1)
                if foe.get('ability') == 'SPEEDBOOST':
                    foe_spe *= 1.5   # one boost (Protect turn 1)
                elif foe.get('ability') == 'UNBURDEN' and (foe.get('item') or '').endswith((' Gem', 'Berry', 'Seed')):
                    foe_spe *= 2
                faster = my_spe > foe_spe
                hits_to_ko = math.ceil(100 / best) if best > 0 else 99
                hits_to_die = math.ceil(100 / taken) if taken > 0 else 99
                # win the 1v1? (who KOs first)
                wins = hits_to_ko < hits_to_die or (hits_to_ko == hits_to_die and faster)
                q = min(best, 120) / 100 * (1.15 if faster else 1.0) * (1 - min(taken, 100) / 200)
                rows.append(dict(foe=foe['name'], off=best, offmv=bestmv, deff=taken, defmv=takenmv,
                                 faster=faster, wins=wins, q=q, hko=hits_to_ko, hdie=hits_to_die))
            res[b['key']] = rows
        me['matchups'] = res
        # best 4 moves overall for the chapter (by sum of contribution across battles)
        return me


def load_roster(path):
    return json.load(open(path))
