"""Recon5 — inspeciona DOM completo da tela records?profile=admin."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = os.environ.get("REGISTROSF2_BASE_URL", "https://registrosf2.stage.twygoead.com").rstrip("/")
ORG_ID   = os.environ.get("REGISTROSF2_ORG_ID", "37079")
ADMIN_EMAIL    = os.environ.get("REGISTROSF2_ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.environ.get("REGISTROSF2_ADMIN_PASSWORD", "")

RECORDS_URL_ADMIN = f"{BASE_URL}/o/{ORG_ID}/records?profile=admin"
EVID = tw.ROOT / "evidencias" / "registros-f2-qa12"
EVID.mkdir(parents=True, exist_ok=True)


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    page.on("dialog", lambda d: d.accept())

    # Login
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.fill("#user_email", ADMIN_EMAIL)
    page.fill("#user_password", ADMIN_PASSWORD)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2000)

    # Ir direto para records com profile=admin
    page.goto(RECORDS_URL_ADMIN, wait_until="domcontentloaded", timeout=30000)
    try:
        with page.expect_response(
            lambda r: f"/api/v1/o/{ORG_ID}/records?" in r.url and r.status == 200,
            timeout=20000
        ):
            pass
    except Exception as e:
        print(f"Timeout: {e}")
    page.wait_for_timeout(6000)
    tw.dispensar_nps(page)
    page.evaluate("() => document.querySelectorAll('iframe').forEach(f => f.style.display='none')")

    # Usar Playwright locators para inspecionar
    print("=== RECON5 ===")
    print(f"spinner: {page.locator('.chakra-spinner').count()}")
    print(f"table: {page.locator('table').count()}")
    print(f"tbody tr: {page.locator('table tbody tr').count()}")

    # Headers da tabela
    headers = []
    for th in page.locator("table th").all():
        t = th.inner_text().strip().replace("\n", " ")
        if t:
            headers.append(t[:40])
    print(f"headers: {headers}")

    # Checkboxes
    print(f"chakra_cb_control: {page.locator('.chakra-checkbox__control').count()}")
    print(f"chakra_cb_input: {page.locator('.chakra-checkbox__input').count()}")

    # Tabs
    tabs = []
    for t in page.locator("[role='tab']").all():
        tabs.append(t.inner_text().strip()[:30])
    print(f"tabs: {tabs}")

    # Botões
    btns = []
    for b in page.locator("button").all():
        t = b.inner_text().strip()[:30]
        if t:
            btns.append(t)
    print(f"buttons: {btns[:25]}")

    # KPIs
    body_text = page.locator("body").inner_text()
    print(f"tem Emitidos: {'Emitidos' in body_text}")
    print(f"tem Provedores tab: {'Provedores' in body_text}")
    print(f"tem Carga horária: {'Carga horária' in body_text}")

    # Paginação
    pag = page.locator("[class*='pagination']")
    pag_text = pag.first.inner_text()[:200] if pag.count() > 0 else "sem paginação"
    print(f"paginação: {pag_text}")

    # First row cells
    first_row = page.locator("table tbody tr").first
    if page.locator("table tbody tr").count() > 0:
        cells = []
        for td in first_row.locator("td").all():
            cells.append(td.inner_text().strip()[:50])
        print(f"first row cells: {cells}")

    # Screenshot
    tw.snap(page, EVID, "recon5_topo")
    tw.snap(page, EVID, "recon5_full", full=True)

    ctx.close()
    browser.close()
