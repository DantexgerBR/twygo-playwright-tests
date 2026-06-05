"""Probe baseline QA 1.3 — rótulo da ação de edição de curso no fluxo atual (36675).

AT espera que "Gerenciar curso" vire "Editar curso" na listagem. Na org nova
(37061) o kebab mostra "Editar". Este probe captura o rótulo no fluxo atual
pra saber se houve rename (e se o esperado era "Gerenciar"/"Gerenciar curso").
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

    # abre o kebab do primeiro curso da listagem
    kebabs = page.locator('[data-test-id$="-actions-kebab"]')
    n = kebabs.count()
    print(f"kebabs na listagem: {n}")
    if n:
        kebabs.first.click()
        page.wait_for_timeout(1500)
        itens = page.evaluate(
            """() => [...document.querySelectorAll('[role="menuitem"], .chakra-menu__menuitem')]
                .filter(el => el.getBoundingClientRect().width > 0)
                .map(el => (el.textContent || '').trim())"""
        )
        print("KEBAB 36675 (visíveis):", itens)
        tw.snap(page, PASTA, "10-kebab-36675")
        # clica na ação de edição e captura breadcrumb
        alvo = next((i for i in itens if "ditar" in i or "erenciar" in i), None)
        if alvo:
            nome = alvo.replace("edit", "", 1) if alvo.startswith("edit") else alvo
            page.locator('[role="menuitem"], .chakra-menu__menuitem').filter(
                has_text=nome).locator("visible=true").first.click()
            page.wait_for_timeout(5000)
            print("URL destino:", page.url)
            bc = page.evaluate(
                """() => [...document.querySelectorAll('h1, h2, [class*="breadcrumb"], nav')]
                    .map(el => (el.textContent || '').trim().slice(0, 80))
                    .filter(Boolean).slice(0, 6)"""
            )
            print("Breadcrumb/headings destino:", bc)
            tw.snap(page, PASTA, "11-destino-editar-36675")
    ctx.close()
    browser.close()
