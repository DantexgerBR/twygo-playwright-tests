"""Captura admin do módulo Continuidade/Sucessão + Competências (org 19653).
Fonte de verdade pros cards 19851 (Ações de resposta) e 20048 (Dashboard Competências)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "explore_19653"
c = tw.cfg("MIGR")

ROTAS = {
    "10-competencias": "/o/19653/organization_chart_competencies",
    "11-dashboard-geral": "/o/19653/succession_dashboards",
    "12-analise-individual": "/o/19653/succession_people_analysis",
    "13-acoes-resposta": "/o/19653/succession_actions",
    "14-parametros-iniciativas": "/o/19653/succession_initiatives",
    "15-funcoes-negocio": "/o/19653/roles",
}

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    for nome, rota in ROTAS.items():
        page.goto(c["base_url"] + rota, wait_until="domcontentloaded", timeout=40000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(4000)
        tw.dispensar_nps(page)
        tw.snap(page, PASTA, nome, full=True)
        # contar registros visíveis / texto-chave
        info = page.evaluate(
            "()=>({rows:document.querySelectorAll('tbody tr,[role=row]').length,"
            "h:(document.querySelector('h1,h2')||{}).innerText||'',"
            "empty:/nenhum|vazio|sem registro|não há|adicione/i.test(document.body.innerText||'')})"
        )
        print(f"{nome}: rows={info['rows']} h={info['h']!r} vazio?={info['empty']} url={page.url}")
    ctx.close()
    browser.close()
