import json,pickle,sys,itertools,numpy as np,os
sys.path.insert(0,'../scripts/team');sys.path.insert(0,'../scripts')
from engine import Engine; E=Engine('.'); D=E.D
b=[b for b in E.battles if b['key']=='giratina'][0]; FO=b['foes']
st=json.load(open('team/state.json')); C=pickle.load(open(f"team/r{st['run']}_native.json.pkl",'rb'))['cands']
SKIP={'SOLARBEAM','SOLARBLADE','SKYATTACK','DIG','FLY','BOUNCE','DIVE','SKULLBASH','METEORBEAM','HYPERBEAM','GIGAIMPACT','FOCUSPUNCH','FUTURESIGHT','DOOMDESIRE','EXPLOSION','SELFDESTRUCT','MISTYEXPLOSION','FINALGAMBIT','LASTRESORT','DREAMEATER','BELCH','STEELBEAM','MINDBLOWN','OUTRAGE','PETALDANCE','THRASH','RAGINGFURY','FAKEOUT','FIRSTIMPRESSION','SUCKERPUNCH','SNORE','SPITUP','COUNTER','MIRRORCOAT','METALBURST','BIDE','ENDEAVOR','FLING','NATURALGIFT','SYNCHRONOISE','LOWKICK','GRASSKNOT','HEAVYSLAM','HEATCRASH'}
DRAIN={'GIGADRAIN','DRAININGKISS','DRAINPUNCH','HORNLEECH','LEECHLIFE','PARABOLICCHARGE','OBLIVIONWING','ABSORB','MEGADRAIN','BITTERBLADE','HEXINGSLASH','INJECTION','MATCHAGOTCHA'}
W=np.array([1.0,1.0,0.5,0.5])   # Giratina rows (2 bars, final bar) carry the fight; partners matter less
def foe_moves(f):
    m=f['moves']; return [x for x,_ in m] if m and isinstance(m[0],(list,tuple)) else list(m)
def airborne(c): return 'FLYING' in c['types'] or c['ability']=='LEVITATE'
def hazards(c):
    """expected % HP lost per turn to field hazards (game code: Spikes 1/3 grounded, SR 1/4 x Rock eff, TSpikes 1/8 + poison after break 1)"""
    if c['ability']=='MAGICGUARD': return 0,0
    rock=1.0
    for t in c['types']: rock*={'FIRE':2,'ICE':2,'FLYING':2,'BUG':2,'FIGHTING':.5,'GROUND':.5,'STEEL':.5}.get(t,1)
    sr=25*rock
    spk=0 if airborne(c) else 33
    ts=0 if (airborne(c) or 'POISON' in c['types'] or 'STEEL' in c['types']) else 25   # 12.5 + 12.5 poison
    heal=12.5 if (c['ability']=='POISONHEAL' and not airborne(c)) else 0
    if c['ability']=='MAGICBOUNCE': spk=0; sr=0          # bounced back onto their side
    p1=spk*0.25+sr*0.15-heal     # phase 1-2 / partners: Giratina Spikes ~1 in 4 turns, Relicanth SR once
    p3=spk*0.25+sr*0.25+ts-heal  # final bar: Toxic Spikes every turn, SR+Spikes in its moveset
    return p1,p3
def evaluate(c):
    L=[m for m in E.legal_moves(c['sid'],c['form'],c['src'].get('moves',[])) if m not in SKIP]
    cat='Physical' if c['stats']['Atk']>=c['stats']['SpA'] else 'Special'
    L=[m for m in L if D.moves[m]['Category']==cat and int(D.moves[m].get('Strength') or 0)>1]
    tab={}
    for m in L:
        row=[]
        for j,f in enumerate(FO):
            try: d=E.damage_pct(c,f,m,D.moves[m],b,True)
            except Exception: d=0
            if j==0: d*=2      # 'bars 1-2' row is % of two bars: per-bar
            if f['name']=='Swalot' and m in DRAIN: d*=0.3
            row.append(min(d,160))
        tab[m]=row
    if not tab: return None
    best=None
    for ms in itertools.combinations(tab,min(3,len(tab))):
        cov=np.max([tab[m] for m in ms],axis=0); s=(cov*W).sum()
        if not best or s>best[0]: best=(s,ms,cov)
    taken=[]
    for f in FO:
        t=0
        for m in foe_moves(f):
            mv=D.moves.get(m)
            if not mv or mv['Category']=='Status': continue
            try: t=max(t,E.damage_pct(f,c,m,mv,b,False))
            except Exception: pass
        taken.append(t)
    return best,taken
out=[]
seen=set()
for c in sorted(C,key=lambda c:-sum(r['q'] for r in c['matchups']['giratina'])):
    if c['gate']: continue
    k=(c['name'],c['ability'])
    if k in seen: continue
    seen.add(k)
    r=evaluate(c)
    if not r: continue
    (s,ms,cov),taken=r
    p1,p3=hazards(c)
    spe=c['stats']['Spe']
    q=[]
    for j,f in enumerate(FO):
        tk=taken[j]*1.3+(p3 if j==1 else p1)
        fast=spe>f['stats']['Spe']
        qq=min(cov[j],100)/100*(1.15 if fast else 1)*(1-min(tk,100)/200)
        if tk>=100 and not(fast and cov[j]>=100): qq*=.5
        q.append(qq)
    out.append(dict(name=c['name'],ab=c['ability'],types=c['types'],moves=[D.moves[m]['MoveName'] for m in ms],cov=[round(x) for x in cov],
                    taken=[round(x) for x in taken],haz=(round(p1),round(p3)),q=q,score=float((np.array(q)*W).sum()/W.sum()),
                    where=c['src']['where'],dump=c['src'].get('dump'),spe=spe,nature=c['nature'],evs=c['evs'],item=c['item'],now=c['src'].get('moves'),nowab=c['src'].get('ability')))
out.sort(key=lambda x:-x['score'])
json.dump(out,open('/tmp/claude-0/-home-user-victoryanalytics/cbcbf9d1-8dc0-5ce1-a0fe-6353198d6d18/scratchpad/gira_eval.json','w'),default=str)
for x in out[:35]:
    print(f"{x['score']:.3f} {x['name'][:22]:22s} {x['ab'][:12]:12s} {'/'.join(x['types']):15s} haz{x['haz']} spe{x['spe']} {x['moves']} off{x['cov']} took{x['taken']} {x['where']}#{x['dump']}")
