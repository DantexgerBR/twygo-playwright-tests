import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "competencias_20048"
c = tw.cfg("MIGR")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(c["base_url"] + "/o/19653/succession_dashboards", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(6000)
    tw.dispensar_nps(page)

    # TODOS os controles de filtro/select/combobox na ÁREA DE CONTEÚDO (não a sidebar)
    ctrls = page.evaluate(r"""()=>{
        const out=[];
        document.querySelectorAll('select,[role=combobox],[class*=select],[class*=Select],input[placeholder],[role=listbox],button').forEach(e=>{
            const r=e.getBoundingClientRect();
            if(r.left<260) return;           // ignora sidebar
            if(r.width===0||r.height===0) return;
            const t=(e.innerText||e.getAttribute('placeholder')||e.getAttribute('aria-label')||'').replace(/\s+/g,' ').trim();
            out.push({tag:e.tagName, t:t.slice(0,40), x:Math.round(r.left), y:Math.round(r.top)});
        });
        return out;
    }""")
    print("=== CONTROLES NA ÁREA DE CONTEÚDO (x>=260) ===")
    vist=set()
    for x in ctrls:
        k=x['tag']+x['t']+str(x['y'])
        if k in vist: continue
        vist.add(k)
        print(f"  [{x['tag']}] {x['t']!r}  @({x['x']},{x['y']})")

    # rolar até o fim e capturar full page
    page.evaluate("()=>window.scrollTo(0,document.body.scrollHeight)")
    page.wait_for_timeout(1500)
    tw.snap(page, PASTA, "RECHECK-dashboard-full", full=True)
    ctx.close(); browser.close()
