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

    # 1) clicar numa ÁREA -> deve filtrar (chip 'Filtrado por Área')
    page.get_by_text("Liderança", exact=True).first.click(timeout=5000)
    page.wait_for_timeout(2500)
    chip = page.evaluate("()=>{const m=(document.body.innerText||'').match(/Filtrado por[^\\n]+/);return m?m[0]:'(sem chip)';}")
    print("APÓS clicar Área 'Liderança' -> chip:", chip)
    tw.snap(page, PASTA, "FILTRO-INT-area-lideranca")

    # limpar filtro (X do chip) e clicar numa FUNÇÃO
    try:
        page.locator("xpath=//*[contains(text(),'Filtrado por')]/following::*[name()='svg' or self::button][1]").first.click(timeout=3000)
        page.wait_for_timeout(1500)
    except Exception:
        page.reload(); page.wait_for_timeout(5000); tw.dispensar_nps(page)

    page.get_by_text("QA", exact=True).first.click(timeout=5000)
    page.wait_for_timeout(2500)
    chip2 = page.evaluate("()=>{const m=(document.body.innerText||'').match(/Filtrado por[^\\n]+/);return m?m[0]:'(sem chip)';}")
    print("APÓS clicar Função 'QA' -> chip:", chip2)
    tw.snap(page, PASTA, "FILTRO-INT-funcao-qa")

    # 2) procurar painel/filtro por GESTOR no dashboard inteiro
    page.evaluate("()=>window.scrollTo(0,document.body.scrollHeight)")
    page.wait_for_timeout(1500)
    tem_gestor = page.evaluate("()=>/gestor|respons[áa]vel/i.test(document.body.innerText||'')")
    blocos = page.evaluate(
        "()=>Array.from(document.querySelectorAll('h2,h3,h4,[class*=title],[class*=Title]'))"
        ".map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).filter(t=>t&&t.length<50)"
    )
    print("\nDashboard menciona gestor/responsável?", tem_gestor)
    print("TÍTULOS de painéis:", sorted(set(blocos)))
    tw.snap(page, PASTA, "FILTRO-INT-dashboard-full", full=True)
    ctx.close(); browser.close()
