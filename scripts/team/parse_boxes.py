import re,sys,json
txt=open(sys.argv[1]).read().strip()
blocks=[b for b in re.split(r'\n\s*\n',txt) if b.strip()]
out=[]
for i,b in enumerate(blocks,1):
    L=b.strip().split('\n'); h=L[0]
    item=h.split(' @ ')[1].strip() if ' @ ' in h else ''
    head=h.split(' @ ')[0].strip()
    g=re.search(r'\((M|F)\)\s*$',head); gender=g.group(1) if g else ''
    head=re.sub(r'\s*\((M|F)\)\s*$','',head)
    m=re.match(r'(.*)\((.*)\)$',head); nick,sp=(m.group(1).strip(),m.group(2)) if m else ('',head)
    d=dict(n=i,species=sp,nick=nick,gender=gender,item=item,moves=[x[2:] for x in L if x.startswith('- ')])
    for x in L:
        if x.startswith('Ability:'): d['ability']=x[8:].strip()
        if x.startswith('Level:'): d['level']=int(x[6:])
        if x.endswith(' Nature'): d['nature']=x[:-7]
    out.append(d)
json.dump(out,open(sys.argv[2],'w'),indent=0)
print(len(out))
for d in out:
    print(d['n'],d['species'],d['level'])
