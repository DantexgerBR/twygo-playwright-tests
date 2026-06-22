import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "competencias_20048"
c = tw.cfg("MIGR")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(c["base_url"] + "/o/19653/organization_chart_roles", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(4500)
    tw.dispensar_nps(page)
    page.get_by_text("Filtro", exact=False).first.click()
    page.wait_for_timeout(1500)
    page.get_by_text("Novo", exact=True).last.click()
    page.wait_for_timeout(2000)
    # combobox react-select: clicar e ler opções via DOM (react-select abre uma lista)
    cb = page.locator("[class*='-control'], [role=combobox], .chakra-select__wrapper select").first
    cb.click(force=True)
    page.wait_for_timeout(1200)
    tw.snap(page, PASTA, "FUNCOES-filtro-opcoes")
    opts = page.evaluate(
        "()=>Array.from(document.querySelectorAll(\"[class*='-option'],[role=option],option\"))"
        ".map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<40)"
    )
    print("OPÇÕES FILTRO (funções):", opts)
    ctx.close(); browser.close()
