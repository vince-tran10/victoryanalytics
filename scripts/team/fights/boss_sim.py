"""Turn-by-turn boss simulator (Vincent, 18 Nov). For boss fights (bars of one boss): plays the fight bar by bar with
  * our ONE active Pokémon (Melia holds the other slot in partner fights), Melia's active Pokémon as a simple partner,
  * speed order (boss always last if slower), damage from the fight eval (team/<key>_eval.json; % of ONE bar),
  * boss healing per turn: Poison Heal (Corrupted Cave: no status needed) 1/8, Black Sludge 1/8 on Corrupted (1/16 else),
    Leftovers 1/16, Sitrus once at < 50%, drain moves heal 50% of the damage they deal (game code: Battle_Effects / Battle.rb),
  * our answers: Gastro Acid (Poison Heal off for the whole fight: no effectClear on its breaks), Heal Block (5 turns),
    Knock Off (this bar's item), Clear Smog / Haze (boss boosts), Unaware (ignores them), one setup turn (Swords Dance x2 ...),
  * the boss's setup move (e.g. Calm Mind) on its first turn of a bar, Reflect after a break where the boss data says so
    (Dark Gardevoir: Reflect + Safeguard 5 turns), overflow damage lost at each break, field poison on our grounded
    non-Poison/Steel Pokémon (Corrupted Cave, 1/8 a turn).
Not simulated: crits, misses, flinches, exact AI targeting (the boss hits whoever it hurts most), switching mid-bar by choice.
usage: from boss_sim import simulate; simulate(eval_json, six_rows, builds, key, with_partner=True)"""
import json, os, re

HEAL_MOVES_DRAIN = {'DRAINPUNCH', 'GIGADRAIN', 'HORNLEECH', 'LEECHLIFE', 'DRAININGKISS', 'OBLIVIONWING', 'PARABOLICCHARGE', 'BITTERBLADE'}
SETUP_FOE = {'CALMMIND': ('spa', 'spd'), 'NASTYPLOT': ('spa', 'spa'), 'SWORDSDANCE': ('atk', 'atk'), 'DRAGONDANCE': ('atk', 'spe'),
             'BULKUP': ('atk', 'def'), 'QUIVERDANCE': ('spa', 'spd'), 'SHIFTGEAR': ('atk', 'spe')}
STAGE = lambda s: (2 + s) / 2 if s >= 0 else 2 / (2 - s)
BREAK_REFLECT = {'darkgardevoir': {2: 5}}          # bar index (1-based) -> Reflect turns at the start of that bar
FIELD_POISON = {'garbodor'}                        # Corrupted Cave: grounded non-Poison/Steel get poisoned (1/8 a turn)
FIELD_HEAL2 = {'garbodor'}                         # Corrupted Cave: Black Sludge heals 1/8, Poison Heal needs no status


def _id(x): return re.sub(r'[^A-Z]', '', str(x or '').upper())


def simulate(R, six, builds, key, with_partner=True, lead=None, max_turns=60):
    n = len(R['foes']); bars = []
    for j in range(n):   # expand multi-bar rows (e.g. Dark Gardevoir: 1 row = 2 bars)
        for b in range(int(R.get('foe_bars', [1] * n)[j] or 1)):
            bars.append(j)
    mult = [R.get('foe_bars', [1] * n)[j] or 1 for j in range(n)]
    boss_spe = R['foe_spe'][0]; boss_hp = R.get('foe_hp', [300] * n)[0]
    team = []
    for r in six:
        b = builds.get(r['name']) or {}
        mv = {_id(m) for m in (b.get('moves') or r.get('moves') or [])}
        team.append(dict(name=r['name'], hp=100.0, spe=r['spe'], cov=[c * mult[j] for j, c in enumerate(r['cov'])], tk=list(r['taken']),
                         maxhp=r.get('hp') or 250, cat=r.get('cat', 'Physical'), mv=mv, ab=_id(b.get('ability') or r.get('ab')),
                         poison_ok=not ({'POISON', 'STEEL'} & set(r['types'])) and _id(b.get('ability') or r.get('ab')) != 'LEVITATE',
                         setup=(r.get('setup_mult') or 1) if (r.get('setup') and _id(r['setup']) in mv) else 1, boost=1.0, poisoned=False))
    part = [dict(p, hp=100.0, deal=[d * mult[j] for j, d in enumerate(p['deal'])]) for p in (R.get('partner') or [])] if with_partner else []
    order = sorted(range(len(team)), key=lambda i: (team[i]['name'] != lead, -team[i]['cov'][bars[0]]))
    act = order[0]; pi = 0
    gastro = False; healblock = 0; log = []; turns_per_bar = []; t_total = 0
    for bi, j in enumerate(bars):
        bar_hp = 100.0; knocked = False; sitrus = 'SITRUS' in _id(R['foe_item'][j]); boss_stage = {'atk': 0, 'spa': 0, 'spd': 0, 'def': 0, 'spe': 0}
        reflect = BREAK_REFLECT.get(key, {}).get(bi + 1, 0)
        foe_mv = {_id(m) for m in R['foe_moves'][j]}; setup_mv = next((m for m in foe_mv if m in SETUP_FOE), None); used_setup = False
        item = _id(R['foe_item'][j]); t_bar = 0; drain = [0.0]
        while bar_hp > 0:
            t_bar += 1; t_total += 1
            if healblock == 0 and False: pass
            if t_total > max_turns: return dict(ok=False, why='too slow', turns=turns_per_bar + [t_bar], log=log, team=team)
            if act is None: return dict(ok=False, why='your side fainted', turns=turns_per_bar + [t_bar], log=log, team=team)
            me = team[act]
            # --- our choice
            heals_ability = R['foe_ability'][j] == 'POISONHEAL' and not gastro
            boss_boosted = boss_stage['spa'] > 0 or boss_stage['atk'] > 0
            if heals_ability and 'GASTROACID' in me['mv']: action = 'Gastro Acid'
            elif heals_ability and not healblock and 'HEALBLOCK' in me['mv']: action = 'Heal Block'
            elif item in ('BLACKSLUDGE', 'LEFTOVERS', 'SITRUSBERRY', 'LUMBERRY') and not knocked and 'KNOCKOFF' in me['mv']: action = 'Knock Off'
            elif boss_boosted and me['ab'] != 'UNAWARE' and ({'CLEARSMOG', 'HAZE'} & me['mv']): action = 'Clear Smog' if 'CLEARSMOG' in me['mv'] else 'Haze'
            elif me['setup'] > 1 and me['boost'] == 1 and me['hp'] > me['tk'][j] / 1.3 * STAGE(max(boss_stage['atk'], boss_stage['spa'])) + 13 and me['cov'][j] < bar_hp:
                action = 'setup'
            else: action = 'attack'
            UTIL = {'GASTROACID', 'KNOCKOFF', 'HEALBLOCK', 'CLEARSMOG', 'HAZE'}
            if action == 'attack' and (me['mv'] & UTIL) and me['cov'][j] < 60:   # utility done: hand over to the best attacker (it takes the hit coming in)
                val = lambda i: team[i]['cov'][j] * (team[i]['setup'] if team[i]['boost'] == 1 else 1) / max(5, team[i]['tk'][j]) * (team[i]['hp'] / 100)
                alive = [i for i in order if team[i]['hp'] > 0 and i != act]
                if alive:
                    b_ = max(alive, key=val)
                    if val(b_) > 1.5 * val(act): action = 'switch'; act = b_; me = team[act]
            def our_hit():
                d = me['cov'][j] * me['boost']
                if me['cat'] == 'Special': d /= STAGE(boss_stage['spd'])
                if reflect and me['cat'] == 'Physical': d /= 2
                return d
            def act_us():
                nonlocal bar_hp, gastro, knocked, sitrus
                nonlocal healblock
                if action == 'Gastro Acid': gastro = True
                elif action == 'Heal Block': healblock = 5
                elif action == 'Knock Off': knocked = True; sitrus = False; bar_hp -= our_hit() * .5
                elif action in ('Clear Smog', 'Haze'):
                    for k_ in boss_stage: boss_stage[k_] = 0
                    if action == 'Haze': me['boost'] = 1
                    bar_hp -= our_hit() * .3 if action == 'Clear Smog' else 0
                elif action == 'setup': me['boost'] = me['setup']
                elif action == 'switch': pass
                else: bar_hp -= our_hit()
            def act_boss():
                nonlocal used_setup
                if bar_hp <= 0: return
                if setup_mv and not used_setup:
                    used_setup = True; a, b_ = SETUP_FOE[setup_mv]; boss_stage[a] += 1; boss_stage[b_] += 1 if b_ != a else 1; return
                st_ = 1 if me['ab'] == 'UNAWARE' else STAGE(max(boss_stage['atk'], boss_stage['spa']))
                dmg_me = me['tk'][j] / 1.3 * st_          # eval 'taken' includes the doubles x1.3 spread factor
                p = part[pi] if pi < len(part) else None
                dmg_p = (p['take'][j] / 1.3 * st_) if p else 0
                if p and dmg_p / max(1, p['hp']) > dmg_me / max(1, me['hp']):   # hits whoever it hurts most (relative)
                    p['hp'] -= dmg_p; dealt = dmg_p * p['hp'] / 100
                else:
                    me['hp'] -= dmg_me; dealt = dmg_me * me['maxhp'] / 100
                if foe_mv & HEAL_MOVES_DRAIN and not healblock:   # drains heal 50% of the damage; ~half its turns are drain moves
                    drain[0] += .5 * .5 * dealt / boss_hp * 100
            if action == 'switch': act_boss()
            elif me['spe'] > boss_spe: act_us(); act_boss()
            else: act_boss(); act_us() if me['hp'] > 0 else None
            # partner
            if pi < len(part) and part[pi]['hp'] > 0 and bar_hp > 0:
                bar_hp -= part[pi]['deal'][j] / (2 if reflect and part[pi]['name'] in ('Snorlax', 'Azumarill') else 1)
            # end of turn: boss healing, field poison, faints, reflect timer
            if bar_hp > 0 and not healblock:
                heal = 0
                if R['foe_ability'][j] == 'POISONHEAL' and not gastro and (key in FIELD_HEAL2): heal += 12.5
                if item == 'BLACKSLUDGE' and not knocked: heal += 12.5 if key in FIELD_HEAL2 else 6.25
                if item == 'LEFTOVERS' and not knocked: heal += 6.25
                if sitrus and bar_hp < 50: heal += 25; sitrus = False
                heal += drain[0]; drain[0] = 0
                bar_hp = min(100, bar_hp + heal)
            if key in FIELD_POISON and me['hp'] > 0 and me['poison_ok']: me['hp'] -= 12.5
            if healblock: healblock -= 1
            if reflect: reflect -= 1
            log.append(f"bar {bi + 1} t{t_bar}: {me['name'].split(' (')[0]} {action}, bar {max(0, bar_hp):.0f}% left, {me['name'].split(' (')[0]} {max(0, me['hp']):.0f}% HP")
            if me['hp'] <= 0:
                alive = [i for i in order if team[i]['hp'] > 0]
                nxt = [i for i in alive if (heals_ability and 'GASTROACID' in team[i]['mv'])] or sorted(alive, key=lambda i: -team[i]['cov'][j] / max(1, team[i]['tk'][j]))
                act = nxt[0] if nxt else None
            if pi < len(part) and part[pi]['hp'] <= 0: pi += 1
        turns_per_bar.append(t_bar)
    return dict(ok=True, turns=turns_per_bar, log=log, team=team, partner_left=sum(1 for p in part if p['hp'] > 0))


def summary(res):
    left = ', '.join(f"{t['name'].split(' (')[0]} {max(0, t['hp']):.0f}%" for t in res['team'] if t['hp'] < 100)
    return f"{'WIN' if res['ok'] else 'LOSS (' + res['why'] + ')'} · turns per bar {res['turns']} · damaged: {left or 'none'}"
