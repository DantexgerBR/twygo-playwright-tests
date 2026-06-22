"""Teste rápido: login direto para /records SEM switch events.
Verifica se chrome completo (KPIs, Provedores) aparece nessa navegação.
"""
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

os.environ["TW_HEADED"] = "1"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    page.on("dialog", lambda d: (print(f"[dialog] {d.type}: {d.message[:80]}"), d.dismiss()))

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
    print(f"Pós-login: {page.url}")

    # SEM switch — ir direto para records
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)

    body = page.locator("body").inner_text()
    print(f"Emitidos: {'Emitidos' in body}")
    print(f"Provedores: {'Provedores' in body}")
    print(f"Ações em massa: {'Ações em massa' in body}")
    print(f"Spinner: {page.locator('.chakra-spinner').count()}")
    print(f"URL: {page.url}")
    tw.snap(page, EVID, "sem_switch_3s", full=True)

    # Aguardar records/stats API
    try:
        page.wait_for_response(
            lambda r: "/records/stats" in r.url and r.status == 200,
            timeout=15000
        )
        print("Stats API respondeu!")
    except Exception as e:
        print(f"Stats timeout: {e}")

    page.wait_for_timeout(5000)
    body = page.locator("body").inner_text()
    print(f"\nApós 5s extra:")
    print(f"  Emitidos: {'Emitidos' in body}")
    print(f"  Provedores: {'Provedores' in body}")
    print(f"  Spinner: {page.locator('.chakra-spinner').count()}")
    print(f"  Rows: {page.locator('table tbody tr').count()}")
    tw.snap(page, EVID, "sem_switch_final", full=True)

    ctx.close()
    browser.close()
