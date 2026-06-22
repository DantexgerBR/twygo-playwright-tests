"""Recon8 — teste simples: ir para records, aguardar API, depois reload, verificar."""
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

    # Dialog handler - MUITO IMPORTANTE
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

    # Ir para records
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)

    # Aguardar resposta da API de records
    try:
        with page.expect_response(
            lambda r: f"/api/v1/o/{ORG_ID}/records?" in r.url and r.status == 200,
            timeout=15000
        ):
            pass
        print("[recon8] API /records respondeu")
    except Exception:
        print("[recon8] Timeout API")

    page.wait_for_timeout(2000)

    # RELOAD — aceitar beforeunload automaticamente
    print("[recon8] Fazendo reload...")
    page.reload(wait_until="domcontentloaded", timeout=30000)
    print(f"[recon8] Reload OK, URL: {page.url}")

    # Aguardar API responder de novo
    try:
        with page.expect_response(
            lambda r: f"/api/v1/o/{ORG_ID}/records?" in r.url and r.status == 200,
            timeout=15000
        ):
            pass
        print("[recon8] API /records respondeu após reload")
    except Exception as e:
        print(f"[recon8] Timeout API após reload: {e}")

    page.wait_for_timeout(5000)
    tw.dispensar_nps(page)
    page.evaluate("() => document.querySelectorAll('iframe').forEach(f => f.style.display='none')")

    spinner = page.locator(".chakra-spinner").count()
    table = page.locator("table").count()
    rows = page.locator("table tbody tr").count()
    print(f"\n[recon8] Final — spinner={spinner}, table={table}, rows={rows}")
    print(f"[recon8] URL: {page.url}")

    body = page.locator("body").inner_text()
    print(f"[recon8] Emitidos: {'Emitidos' in body}")
    print(f"[recon8] Provedores: {'Provedores' in body}")
    print(f"[recon8] Carga horária total: {'Carga horária total' in body}")

    tw.snap(page, EVID, "recon8_final", full=True)

    # Se carregou, inspecionar headers
    if table > 0:
        headers = []
        for th in page.locator("table th").all():
            t = th.inner_text().strip().replace("\n", " ")
            if t:
                headers.append(t[:40])
        print(f"[recon8] Headers: {headers}")
        print(f"[recon8] Checkboxes: {page.locator('.chakra-checkbox__control').count()}")

    ctx.close()
    browser.close()
