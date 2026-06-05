"""Probe complementar 2 — clicar em Trilha/Pacote/Curso do dropdown "Adicionar"
(org 36675, fluxo atual) e registrar a URL + heading de destino."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "novo_estudio_baseline_trilha_pacote"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, headless=True, slow_mo=150)
    c = tw.cfg("")
    tw.login(page, c)
    for opcao, slug in [("Trilha", "07-destino-trilha"),
                        ("Pacote", "08-destino-pacote"),
                        ("Curso", "09-destino-curso")]:
        page.goto(f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin",
                  wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2500)
        tw.dispensar_nps(page)
        page.get_by_role("button", name="Adicionar").first.click()
        page.wait_for_timeout(1200)
        page.get_by_role("menuitem", name=opcao, exact=True).first.click()
        page.wait_for_timeout(3000)
        h1 = [t.strip() for t in page.locator("h1").all_inner_texts() if t.strip()]
        print(f"[{opcao}] url = {page.url}")
        print(f"[{opcao}] h1  = {h1}")
        tw.snap(page, PASTA, slug)
    ctx.close()
    browser.close()
