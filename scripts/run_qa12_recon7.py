"""Recon7 — estratégia definitiva: navegar para /records, aguardar API, analisar DOM."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = os.environ.get("REGISTROSF2_BASE_URL", "https://registrosf2.stage.twygoead.com").rstrip("/")
ORG_ID   = os.environ.get("REGISTROSF2_ORG_ID", "37079")
ADMIN_EMAIL    = os.environ.get("REGISTROSF2_ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.environ.get("REGISTROSF2_ADMIN_PASSWORD", "")

RECORDS_URL = f"{BASE_URL}/o/{ORG_ID}/records"
EVID = tw.ROOT / "evidencias" / "registros-f2-qa12"
EVID.mkdir(parents=True, exist_ok=True)


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)

    # Dialog handler
    page.on("dialog", lambda d: (print(f"[dialog] type={d.type} msg={d.message[:80]}"), d.accept()))

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

    # Switch admin
    page.goto(
        f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)

    # Navegar para records
    print(f"[recon7] Goto {RECORDS_URL}")
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(1000)
    tw.dispensar_nps(page)

    # Aguardar que API /records responda
    print("[recon7] Aguardando API /records responder...")
    try:
        with page.expect_response(
            lambda r: f"/api/v1/o/{ORG_ID}/records?" in r.url and r.status == 200,
            timeout=15000
        ) as resp_info:
            pass
        print(f"[recon7] API respondeu: {resp_info.value.url[:80]}")
    except Exception as e:
        print(f"[recon7] Timeout API: {e}")

    # Aguardar mais 8s para React processar
    page.wait_for_timeout(8000)

    spinner = page.locator(".chakra-spinner").count()
    table = page.locator("table").count()
    rows = page.locator("table tbody tr").count()
    print(f"[recon7] 8s após API — spinner={spinner}, table={table}, rows={rows}")
    tw.snap(page, EVID, "recon7_8s", full=True)

    if spinner > 0 or table == 0:
        # Tentar remover spinner via JS (forçar estado de UI)
        print("[recon7] Tentando remover spinner via JS...")
        page.evaluate("""
            () => {
                document.querySelectorAll('.chakra-spinner').forEach(el => el.remove());
            }
        """)
        page.wait_for_timeout(1000)
        spinner2 = page.locator(".chakra-spinner").count()
        table2 = page.locator("table").count()
        print(f"[recon7] Após remover spinner JS — spinner={spinner2}, table={table2}")
        tw.snap(page, EVID, "recon7_sem_spinner", full=True)

    # Analisar DOM real
    print("\n[recon7] Estado final do DOM:")
    print(f"  table: {page.locator('table').count()}")
    print(f"  tbody tr: {page.locator('table tbody tr').count()}")
    print(f"  chakra tabs: {page.locator('.chakra-tabs, [role=tablist]').count()}")

    # Body text para ver KPIs
    body = page.locator("body").inner_text()
    print(f"  Emitidos: {'Emitidos' in body}")
    print(f"  Provedores: {'Provedores' in body}")
    print(f"  Carga horária total: {'Carga horária total' in body}")

    ctx.close()
    browser.close()
