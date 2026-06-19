"""Recon: opcoes do kebab de um usuario (achar 'redefinir senha')."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "filtros_dashboards_19363"
c = tw.cfg("")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/users?profile=admin", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)

    # achar a linha da Julia e clicar no kebab
    row = page.locator("tr", has_text="julia@sophia.tech.com.br").first
    print("achou linha julia?", row.count())
    row.locator("text=more_vert").last.click(timeout=5000)
    page.wait_for_timeout(1200)
    itens = tw.menu_visivel(page)
    print("MENU KEBAB JULIA:", itens)
    tw.snap(page, PASTA, "10-kebab-julia")

    ctx.close(); browser.close()
print("OK")
