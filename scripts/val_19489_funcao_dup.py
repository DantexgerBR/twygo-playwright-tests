"""19489 — pessoas duplicadas no drawer de vincular pessoas a uma função.
Repro: Skills > Funções de negócio > editar > pessoas atribuídas > adicionar.
Esperado: pessoa em 2 áreas aparece só 1x (não duplica)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "funcao_dup_19489"
c = tw.cfg("MIGR")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)

    # 0) organograma: mapear pessoas e suas áreas (achar multi-área)
    page.goto(c["base_url"] + "/o/19653/organization_chart", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(5000)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, "00-organograma", full=True)
    print("Organograma URL:", page.url)

    # 1) Funções de negócio
    page.goto(c["base_url"] + "/o/19653/organization_chart_roles", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(4500)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, "01-funcoes-lista")
    # ações por linha (editar = pencil)
    icons = page.evaluate(
        "()=>Array.from(document.querySelectorAll('tbody tr [data-icon]')).slice(0,12)"
        ".map(e=>e.getAttribute('data-icon'))"
    )
    print("data-icons 1a linha:", icons)
    ctx.close(); browser.close()
