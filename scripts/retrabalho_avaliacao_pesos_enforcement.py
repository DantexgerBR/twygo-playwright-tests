"""Distribuicao de peso por secao (20186) - captura legivel (recolhido)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "avaliacao_pesos_questionario"
c = tw.cfg("")


def ler_pesos(page):
    """Le valores dos inputs cujo container tem o label 'Peso' (heuristica que funcionou)."""
    return page.evaluate(r"""()=>{
        const out=[];
        document.querySelectorAll('input').forEach(inp=>{
            const prev=inp.parentElement&&inp.parentElement.previousElementSibling;
            const lab=(prev&&prev.innerText)||'';
            if(/Peso/.test(lab)) out.push(inp.value);
        });
        return out;
    }""")


def colapsar_tudo(page):
    # clicar nos chevrons de pergunta (keyboard_arrow_up) pra recolher
    for _ in range(6):
        try:
            btn = page.get_by_text("keyboard_arrow_up", exact=True).first
            if btn.count() and btn.is_visible():
                btn.click(timeout=1500); page.wait_for_timeout(400)
            else:
                break
        except Exception:
            break


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/assessments/new?profile=admin",
              wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    page.fill("input[placeholder*='nome do question']", "QA 20186 distribuicao peso")
    page.get_by_text("Avaliação de competências", exact=True).click()
    page.wait_for_timeout(1000)

    page.get_by_text("Adicionar pergunta à seção", exact=True).first.click(timeout=4000)
    page.wait_for_timeout(1200)
    colapsar_tudo(page)
    print("2 perguntas (recolhido):", ler_pesos(page))
    page.locator("text=Perguntas").first.scroll_into_view_if_needed()
    tw.snap(page, PASTA, "06-duas-perguntas-50-50-recolhido")

    page.get_by_text("Adicionar pergunta à seção", exact=True).first.click(timeout=4000)
    page.wait_for_timeout(1200)
    colapsar_tudo(page)
    print("3 perguntas (recolhido):", ler_pesos(page))
    tw.snap(page, PASTA, "07-tres-perguntas-distribuicao-recolhido")

    ctx.close(); browser.close()
print("OK")
