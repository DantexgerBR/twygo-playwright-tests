import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "competencias_20048"
c = tw.cfg("MIGR")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(c["base_url"] + "/o/19653/succession_people_analysis", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(4500)
    tw.dispensar_nps(page)
    page.get_by_text("Filtro", exact=False).first.click()
    page.wait_for_timeout(1800)
    tw.snap(page, PASTA, "FILTRO-drawer")
    # botão Novo dentro do drawer
    try:
        page.get_by_role("button", name="Novo", exact=True).click(timeout=4000)
    except Exception:
        # fallback: link/elemento com + Novo no painel direito
        page.locator("text=/^\\+?\\s*Novo$/").last.click(force=True, timeout=4000)
    page.wait_for_timeout(2500)
    tw.snap(page, PASTA, "FILTRO-novo-campos")
    # listar selects/labels do builder
    txt = page.evaluate(
        "()=>{const m=document.querySelector('.chakra-modal__content,[role=dialog],.chakra-slide,aside');"
        "return m?(m.innerText||'').trim():'(nenhum)';}"
    )
    print("=== BUILDER DE FILTRO ===\n", txt[:1500])

    # abrir o dropdown 'Colunas para filtrar'
    page.locator(".chakra-select, select, [role=combobox], input[readonly]").first.click(force=True)
    page.wait_for_timeout(1500)
    tw.snap(page, PASTA, "FILTRO-colunas-dropdown")
    opts = page.evaluate(
        "()=>Array.from(document.querySelectorAll('option,[role=option],li,[role=menuitem]'))"
        ".map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).filter(t=>t&&t.length<40)"
    )
    print("\nOPÇÕES DE COLUNA P/ FILTRAR:", sorted(set(opts)))
    ctx.close(); browser.close()
