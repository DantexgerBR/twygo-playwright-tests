"""Recon6 — estratégia definitiva com page.reload() + dialog accept."""
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

    # Aceitar dialogs automáticos (beforeunload, confirm, etc.)
    page.on("dialog", lambda d: (print(f"[dialog] {d.type}: {d.message[:100]}"), d.accept()))

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

    # Switch para admin
    page.goto(
        f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)

    # Navegar para records
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2000)

    spinner_before = page.locator(".chakra-spinner").count()
    print(f"[recon6] Spinner antes do reload: {spinner_before}")

    # Aguardar resposta da API
    try:
        with page.expect_response(
            lambda r: f"/api/v1/o/{ORG_ID}/records?" in r.url and r.status == 200,
            timeout=15000
        ):
            pass
        print("[recon6] API /records respondeu antes do reload")
    except Exception:
        print("[recon6] API /records não respondeu no timeout inicial")

    page.wait_for_timeout(3000)

    spinner_mid = page.locator(".chakra-spinner").count()
    table_mid = page.locator("table").count()
    print(f"[recon6] Mid-point — spinner: {spinner_mid}, table: {table_mid}")

    if spinner_mid > 0:
        print("[recon6] Spinner ativo — aplicando workaround reload()")
        page.reload(wait_until="domcontentloaded", timeout=30000)
        print("[recon6] Reload iniciado")
        # Aguardar API responder
        try:
            with page.expect_response(
                lambda r: f"/api/v1/o/{ORG_ID}/records?" in r.url and r.status == 200,
                timeout=20000
            ):
                pass
            print("[recon6] API /records respondeu após reload")
        except Exception as e:
            print(f"[recon6] Timeout API após reload: {e}")
        page.wait_for_timeout(5000)
        tw.dispensar_nps(page)
        page.evaluate("() => document.querySelectorAll('iframe').forEach(f => f.style.display='none')")

    spinner_after = page.locator(".chakra-spinner").count()
    table_after = page.locator("table").count()
    rows_after = page.locator("table tbody tr").count()
    print(f"[recon6] Final — spinner: {spinner_after}, table: {table_after}, rows: {rows_after}")

    tw.snap(page, EVID, "recon6_final", full=True)

    # Inspecionar se tabela carregou
    if table_after > 0:
        headers = []
        for th in page.locator("table th").all():
            t = th.inner_text().strip().replace("\n", " ")
            if t:
                headers.append(t[:40])
        print(f"[recon6] Headers: {headers}")

        # Checkboxes
        print(f"[recon6] chakra_cb_control: {page.locator('.chakra-checkbox__control').count()}")

        # Tabs
        tabs = []
        for t in page.locator("[role='tab'], button[data-selected], .chakra-tabs__tab").all():
            tabs.append(t.inner_text().strip()[:30])
        print(f"[recon6] Tabs: {tabs}")

        # KPIs
        body_text = page.locator("body").inner_text()
        print(f"[recon6] tem Emitidos: {'Emitidos' in body_text}")
        print(f"[recon6] tem Provedores: {'Provedores' in body_text}")
        print(f"[recon6] tem Carga horária total: {'Carga horária total' in body_text}")

        # Paginação
        pag = page.locator("[class*='pagination']")
        if pag.count() > 0:
            print(f"[recon6] Paginação: {pag.first.inner_text()[:200]}")

    ctx.close()
    browser.close()
