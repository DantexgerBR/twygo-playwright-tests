"""Teste decisivo: campanha 194 (admin) tem registro de avaliacao pendente da Julia c/ Adriana avaliadora?"""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "desempenho_seguir_33085519"
c = tw.cfg("")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles/178/campaigns", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    # abrir "Ver detalhes" da Campanha QA lider Julia
    row = page.locator("tr,[role=row]").filter(has_text=re.compile("Campanha QA lider Julia", re.I)).first
    row.get_by_text("more_vert", exact=True).last.click(timeout=4000); page.wait_for_timeout(1000)
    print("menu campanha:", tw.menu_visivel(page))
    # clicar Ver detalhes (nativo, menu unico)
    try:
        page.get_by_role("menuitem", name=re.compile("Ver detalhes|detalhes|resumo", re.I)).first.click(timeout=4000)
    except Exception:
        tw.click_menuitem(page, "detalhes")
    page.wait_for_timeout(3500)
    print("URL detalhe:", page.url)
    tw.snap(page, PASTA, "22-camp194-detalhe-admin", full=True)
    info = page.evaluate(r"""()=>{
        const rows=Array.from(document.querySelectorAll('tr,[role=row]')).map(r=>(r.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/Julia|Adriana|avalia|lider|pendente|iniciar|respond/i.test(t)).slice(0,15);
        const tabs=[...new Set(Array.from(document.querySelectorAll('[role=tab],button,a')).map(b=>(b.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<28&&/avalia|particip|respond|etapa|lider|resumo/i.test(t)))];
        const body=(document.body.innerText||'').replace(/\n{2,}/g,'\n');const i=body.search(/avalia[cç][aã]o do l[ií]der|respond|avaliador|Julia/i);
        return {rows, tabs, snippet:i>=0?body.slice(i, i+400):body.slice(0,300)};
    }""")
    print("ROWS:", info["rows"])
    print("TABS:", info["tabs"])
    print("SNIPPET:", info["snippet"][:400])
    ctx.close(); browser.close()
print("OK")
