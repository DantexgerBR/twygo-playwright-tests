"""Investiga requisições de rede da tela Registros."""
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

requests_log = []
responses_log = []


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)

    # Capturar requests e responses
    def on_request(req):
        if any(kw in req.url for kw in ["learning_record", "records", "api/"]):
            requests_log.append(f"REQ {req.method} {req.url[:120]}")

    def on_response(resp):
        if any(kw in resp.url for kw in ["learning_record", "records", "api/"]):
            responses_log.append(f"RSP {resp.status} {resp.url[:120]}")

    page.on("request", on_request)
    page.on("response", on_response)

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

    page.goto(
        f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)

    # Navegar para registros e aguardar
    print(f"\n[network] Navegando para {RECORDS_URL}")
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(10000)  # Aguardar 10s para capturar requests

    tw.snap(page, EVID, "network_pos_10s")

    print("\n=== REQUESTS capturados ===")
    for r in requests_log:
        print(f"  {r}")

    print("\n=== RESPONSES capturados ===")
    for r in responses_log:
        print(f"  {r}")

    # Checar o que a página tem
    body_text = page.locator("body").inner_text()[:500]
    print(f"\n[body] Primeiros 500 chars: {body_text}")

    # Verificar console errors
    print("\n[URL atual]", page.url)

    ctx.close()
    browser.close()
