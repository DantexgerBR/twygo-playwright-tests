"""Probe complementar — hrefs das opções do dropdown "Adicionar" (org 36675).

Confirma se Trilha/Pacote do fluxo atual apontam pras mesmas URLs que os cards
do Novo Estúdio (/contents/new?kind=learning_path|package).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "novo_estudio_baseline_trilha_pacote"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, headless=True, slow_mo=150)
    c = tw.cfg("")
    tw.login(page, c)
    page.get_by_role("button", name="Adicionar").first.click()
    page.wait_for_timeout(1500)
    # Opções do dropdown: pega href + texto de cada link/menuitem visível
    for loc in ("[role=menu] a", "[role=menuitem]", ".dropdown-menu a"):
        itens = page.locator(loc)
        n = itens.count()
        if not n:
            continue
        print(f"-- seletor {loc!r} ({n} itens) --")
        for i in range(min(n, 10)):
            el = itens.nth(i)
            if not el.is_visible():
                continue
            txt = (el.inner_text() or "").strip().splitlines()[0] if el.inner_text() else ""
            href = el.get_attribute("href")
            onclick = el.get_attribute("onclick")
            print(f"   {txt!r:12} href={href!r} onclick={onclick!r}")
        break
    tw.snap(page, PASTA, "06-dropdown-hrefs")
    ctx.close()
    browser.close()
