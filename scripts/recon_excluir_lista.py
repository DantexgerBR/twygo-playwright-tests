# -*- coding: utf-8 -*-
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
c = tw.cfg("NOVOEST")
PASTA = tw.ROOT / "evidencias" / "qualidade_ia_cleanup"
with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(5000); tw.dispensar_nps(page)
    # procurar o curso SQL na lista e seus controles
    info = page.evaluate(r"""()=>{
        const card=[...document.querySelectorAll('*')].find(e=>/Domine SQL B[aá]sico/i.test(e.textContent||'') && (e.innerText||'').length<400 && e.querySelectorAll('button').length<15);
        if(!card) return {achou:false, body:document.body.innerText.slice(0,300)};
        const botoes=[...card.querySelectorAll('button,[role=button],a')].map(b=>({t:(b.innerText||b.getAttribute('aria-label')||b.title||'').replace(/\s+/g,' ').trim(), testid:b.getAttribute('data-test-id')})).filter(o=>o.t||o.testid);
        return {achou:true, classe:card.className, botoes};
    }""")
    print("INFO:", info)
    tw.snap(page, PASTA, "lista-conteudos")
    ctx.close(); browser.close()
