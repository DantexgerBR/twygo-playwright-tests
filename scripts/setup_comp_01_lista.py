"""Setup competencias: achar Lista de competencias + form de adicionar."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "responder_avaliacao_20224"
c = tw.cfg("")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/organization_chart_competencies?profile=admin", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    # clicar aba/tab "Lista de competencias" (tentar role=tab e texto)
    for how in ["tab", "text"]:
        try:
            if how == "tab":
                page.get_by_role("tab", name=re.compile("Lista de compet", re.I)).first.click(timeout=4000)
            else:
                page.get_by_text("Lista de competências", exact=True).first.click(timeout=4000)
            page.wait_for_timeout(2500); break
        except Exception:
            continue
    print("URL:", page.url)
    tw.snap(page, PASTA, "28-lista-competencias", full=True)
    info = page.evaluate(r"""()=>{
        const btns=[...new Set(Array.from(document.querySelectorAll('button,a')).map(b=>(b.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<35&&/Adicionar|Nova|Criar|compet|Import/i.test(t)))];
        const tids=Array.from(document.querySelectorAll('[data-test-id]')).map(e=>e.getAttribute('data-test-id')).filter(t=>/compet|add|create|skill/i.test(t));
        const body=(document.body.innerText||'').replace(/\n{2,}/g,'\n');const i=body.lastIndexOf('Competências');
        return {btns, tids:[...new Set(tids)].slice(0,20), snippet:body.slice(i, i+500)};
    }""")
    print("BTNS:", info["btns"])
    print("TIDS:", info["tids"])
    print("snippet:", info["snippet"][:400])
    ctx.close(); browser.close()
print("OK")
