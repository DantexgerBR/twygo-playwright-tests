"""Retrabalho 20048 — [Competências] Implementar dashboard e extração de dados.

AT (RH/admin):
 1) Filtrar por ÁREA, GESTOR e FUNÇÃO em todos os dashboards.
 2) Drill-down: clicar no indicador → ver registros/cálculo que originaram o valor.
 3) Exportar dados/gráficos/relatórios (Excel, PDF, imagem).

Env: testedemigracao / org 19653 (perfil MIGR).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "competencias_20048"
c = tw.cfg("MIGR")

DASHBOARDS = {
    "dashboard-geral": "/o/19653/succession_dashboards",
    "analise-individual": "/o/19653/succession_people_analysis",
    "competencias": "/o/19653/organization_chart_competencies",
}


def botoes(page):
    return page.evaluate(
        "()=>Array.from(document.querySelectorAll('button,[role=button],a'))"
        ".map(b=>(b.innerText||b.getAttribute('aria-label')||b.getAttribute('title')||'').replace(/\\s+/g,' ').trim())"
        ".filter(t=>t.length>0&&t.length<40)"
    )


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    for nome, rota in DASHBOARDS.items():
        page.goto(c["base_url"] + rota, wait_until="domcontentloaded", timeout=40000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(4500)
        tw.dispensar_nps(page)
        bs = sorted(set(botoes(page)))
        relevantes = [b for b in bs if any(k in b.lower() for k in
                      ["filtr", "export", "extra", "baixar", "pdf", "excel", "imagem", "download", "csv", "área", "area", "gestor", "função", "funcao"])]
        print(f"\n===== {nome} ({rota}) =====")
        print("  BOTÕES RELEVANTES:", relevantes or "NENHUM")
        print("  TODOS BOTÕES:", bs)
    ctx.close()
    browser.close()
