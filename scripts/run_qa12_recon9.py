"""Recon9 — aguardar stats KPI e verificar tela completa."""
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

    page.on("dialog", lambda d: (print(f"[dialog] {d.type}: {d.message[:80]}"), d.accept()))

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

    # Ir para records + reload
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)
    try:
        with page.expect_response(
            lambda r: f"/api/v1/o/{ORG_ID}/records?" in r.url and r.status == 200,
            timeout=15000
        ):
            pass
    except Exception:
        pass
    page.wait_for_timeout(1000)
    page.reload(wait_until="domcontentloaded", timeout=30000)

    # Aguardar stats (KPIs)
    print("[recon9] Aguardando /records/stats...")
    try:
        with page.expect_response(
            lambda r: f"/records/stats" in r.url and r.status == 200,
            timeout=20000
        ) as stats_info:
            pass
        stats_body = stats_info.value.json()
        print(f"[recon9] Stats: {stats_body}")
    except Exception as e:
        print(f"[recon9] Timeout stats: {e}")

    # Também aguardar records
    try:
        with page.expect_response(
            lambda r: f"/api/v1/o/{ORG_ID}/records?" in r.url and r.status == 200,
            timeout=15000
        ):
            pass
        print("[recon9] Records API respondeu")
    except Exception:
        pass

    page.wait_for_timeout(5000)
    tw.dispensar_nps(page)
    page.evaluate("() => document.querySelectorAll('iframe').forEach(f => f.style.display='none')")

    body = page.locator("body").inner_text()
    print(f"\n[recon9] Emitidos: {'Emitidos' in body}")
    print(f"[recon9] Provedores: {'Provedores' in body}")
    print(f"[recon9] Carga horária total: {'Carga horária total' in body}")
    print(f"[recon9] Spinner: {page.locator('.chakra-spinner').count()}")
    print(f"[recon9] Table: {page.locator('table').count()}")
    print(f"[recon9] Rows: {page.locator('table tbody tr').count()}")

    # Botões presentes
    btns = []
    for b in page.locator("button").all():
        t = b.inner_text().strip()[:30]
        if t and len(t) > 1:
            btns.append(t)
    print(f"[recon9] Botões: {btns[:20]}")

    tw.snap(page, EVID, "recon9_com_stats", full=True)

    ctx.close()
    browser.close()
