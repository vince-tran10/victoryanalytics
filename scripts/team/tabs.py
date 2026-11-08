"""Group the report's sections into tabs (runs last, after box_audit.py and highlight.py).
usage: python3 -I tabs.py report.html"""
import re, sys
TABS = [('team', 'Team', ['s1']), ('fights', 'Fights', ['s1f']),
        ('todo', 'To do', ['s3', 's1b', 's1c']), ('tiers', 'Tier list', ['s2']), ('boxes', 'Boxes', ['s4'])]
p = sys.argv[1]; page = open(p, encoding='utf-8').read()
if 'id="tabbar"' in page:
    sys.exit('already tabbed')
secs = {}
for m in re.finditer(r'(?:<!--BOXAUDIT-->\s*)?<section aria-labelledby="(\w+)">.*?</section>(?:\s*<!--/BOXAUDIT-->)?', page, re.S):
    secs[m.group(1)] = m.group(0)
for blk in secs.values():
    page = page.replace(blk, '', 1)
bar = '<nav class="tabs" id="tabbar" role="tablist" aria-label="Report sections">' + ''.join(
    f'<button role="tab" type="button" data-tab="{k}" id="tab-{k}" aria-controls="panel-{k}">{t}</button>' for k, t, _ in TABS) + '</nav>'
panels = ''.join(f'<div class="tabp" id="panel-{k}" role="tabpanel" aria-labelledby="tab-{k}" data-tab="{k}">' +
                 '\n'.join(secs[s] for s in ids if s in secs) + '</div>' for k, _, ids in TABS)
page = page.replace('</header>', '</header>\n' + bar + '\n' + panels, 1)
css = '''<style id="tabs-css">
.tabs { position: sticky; top: 0; z-index: 5; display: flex; gap: 6px; overflow-x: auto; padding: 8px 0; background: var(--bg); border-bottom: 1px solid var(--line); scrollbar-width: none }
.tabs::-webkit-scrollbar { display: none }
.tabs button { font: 600 13px var(--display); letter-spacing: .03em; padding: 7px 14px; border-radius: 99px; border: 1px solid var(--line); background: var(--panel); color: var(--muted); cursor: pointer; white-space: nowrap }
.tabs button[aria-selected="true"] { background: var(--accent); border-color: var(--accent); color: #fff }
.tabs button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px }
.tabp { display: grid; gap: 28px } .tabp[hidden] { display: none }
h2 .n { display: none }
.gp > li { margin-bottom: 4px } .gp ul { margin: 2px 0 0; padding-left: 18px; display: grid; gap: 2px }
.panel.pad ul { margin: 0; padding-left: 18px; display: grid; gap: 4px; font-size: 13.5px }
.scores ul.legend { margin: 4px 0 0; padding-left: 18px; display: grid; gap: 3px }
</style>'''
js = '''<script id="tabs-js">
(function(){var bs=[].slice.call(document.querySelectorAll('#tabbar button')),ps=[].slice.call(document.querySelectorAll('.tabp'));
function show(k,push){var ok=bs.some(function(b){return b.dataset.tab===k});if(!ok)k=bs[0].dataset.tab;
bs.forEach(function(b){b.setAttribute('aria-selected',b.dataset.tab===k?'true':'false');b.tabIndex=b.dataset.tab===k?0:-1});
ps.forEach(function(p){p.hidden=p.dataset.tab!==k});try{localStorage.setItem('ch8-tab',k)}catch(e){}
if(push)history.replaceState(null,'','#'+k);}
bs.forEach(function(b,i){b.addEventListener('click',function(){show(b.dataset.tab,true);window.scrollTo(0,0)});
b.addEventListener('keydown',function(e){var j=e.key==='ArrowRight'?i+1:e.key==='ArrowLeft'?i-1:-9;if(j>-9){j=(j+bs.length)%bs.length;bs[j].focus();show(bs[j].dataset.tab,true)}})});
var start=(location.hash||'').slice(1);if(!start){try{start=localStorage.getItem('ch8-tab')||''}catch(e){}}
show(start||'team',false);
var f=document.getElementById('boxfind');if(f)f.addEventListener('focus',function(){show('boxes',true)});})();
</script>'''
page = page.replace('</style>', '</style>\n' + css, 1)
page = page.replace('</body>', js + '\n</body>') if '</body>' in page else page + '\n' + js
open(p, 'w', encoding='utf-8').write(page)
print('tabs:', [(k, [s for s in ids if s in secs]) for k, _, ids in TABS])
