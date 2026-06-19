"""20224: inspecionar edicao do ciclo 174 ativo (da pra adicionar competencias?)."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "responder_avaliacao_20224"
c = tw.cfg("")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles/174/edit", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    print("URL:", page.url)
    tw.snap(page, PASTA, "21-ciclo174-edit", full=True)
    info = page.evaluate(r"""()=>{
        const tids=Array.from(document.querySelectorAll('[data-test-id]')).map(e=>e.getAttribute('data-test-id')).filter(t=>/cycle-form|tab|evaluation|competency/i.test(t));
        const tabs=[...new Set(Array.from(document.querySelectorAll('[role=tab],button')).map(b=>(b.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<30))];
        const body=(document.body.innerText||'').replace(/\n{2,}/g,'\n').slice(0,400);
        return {tids:[...new Set(tids)].slice(0,25), tabs:tabs.slice(0,20), body};
    }""")
    print("DATA-TEST-IDS:", info["tids"])
    print("TABS/BTNS:", info["tabs"])
    print("BODY:", info["body"])
    ctx.close(); browser.close()
print("OK")
