"""Validação 20048 — abrir Filtro / Extrair dados e testar drill-down."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "competencias_20048"
c = tw.cfg("MIGR")


def conteudo_painel(page):
    """Texto do drawer/popover/modal aberto."""
    return page.evaluate(
        "()=>{const sels=['.chakra-modal__content','[role=dialog]','.chakra-popover__content','[role=menu]','.chakra-slide'];"
        "for(const s of sels){const el=document.querySelector(s);"
        "if(el&&el.offsetParent!==null)return (el.innerText||'').replace(/\\n{2,}/g,'\\n').trim();}return '(nenhum painel aberto)';}"
    )


def clicar(page, texto):
    try:
        page.get_by_role("button", name=texto).first.click(timeout=4000)
        return True
    except Exception:
        try:
            page.get_by_text(texto, exact=False).first.click(timeout=3000)
            return True
        except Exception:
            return False


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)

    for nome, rota in [("analise-individual", "/o/19653/succession_people_analysis"),
                       ("competencias", "/o/19653/organization_chart_competencies")]:
        page.goto(c["base_url"] + rota, wait_until="domcontentloaded", timeout=40000)
        page.wait_for_timeout(4500)
        tw.dispensar_nps(page)

        # FILTRO
        if clicar(page, "Filtro"):
            page.wait_for_timeout(2000)
            tw.snap(page, PASTA, f"{nome}-filtro")
            print(f"\n### {nome} — FILTRO:\n", conteudo_painel(page)[:1500])
            page.keyboard.press("Escape")
            page.wait_for_timeout(1000)

        # EXTRAIR DADOS
        if clicar(page, "Extrair dados"):
            page.wait_for_timeout(2000)
            tw.snap(page, PASTA, f"{nome}-extrair")
            print(f"\n### {nome} — EXTRAIR DADOS:\n", conteudo_painel(page)[:1500])
            page.keyboard.press("Escape")
            page.wait_for_timeout(1000)

    # DRILL-DOWN no Dashboard geral
    page.goto(c["base_url"] + "/o/19653/succession_dashboards", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(4500)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, "dashboard-geral-topo")
    # tentar clicar no card "Risco atual" / "Áreas com maior risco"
    for alvo in ["Risco atual", "Áreas com maior risco", "Funções com maior risco"]:
        try:
            el = page.get_by_text(alvo, exact=False).first
            el.click(timeout=3000)
            page.wait_for_timeout(2500)
            print(f"\n### DRILL-DOWN clique em '{alvo}': url={page.url}")
            print("   painel:", conteudo_painel(page)[:400])
            tw.snap(page, PASTA, f"drill-{alvo[:12].replace(' ','_')}")
            page.keyboard.press("Escape")
            page.wait_for_timeout(800)
        except Exception as e:
            print(f"   '{alvo}' não clicável: {e!r}")

    ctx.close()
    browser.close()
