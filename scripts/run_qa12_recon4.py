"""Recon4 — estratégia: goto records DIRETO após login (sem passar pelo events admin)."""
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

    # Tratar dialogs automaticamente
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

    # Estratégia A: ir direto para records COM profile=admin
    print("\n[recon4] Estratégia A: goto records com profile=admin")
    page.goto(
        f"{BASE_URL}/o/{ORG_ID}/records?profile=admin",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    try:
        with page.expect_response(
            lambda r: f"/api/v1/o/{ORG_ID}/records?" in r.url and r.status == 200,
            timeout=20000
        ):
            pass
    except Exception as e:
        print(f"  Timeout API: {e}")
    page.wait_for_timeout(6000)
    tw.dispensar_nps(page)
    page.evaluate("() => document.querySelectorAll('iframe').forEach(f => f.style.display='none')")

    spinner_a = page.locator(".chakra-spinner").count()
    table_a = page.locator("table").count()
    print(f"  Estratégia A — spinner: {spinner_a}, table: {table_a}")
    tw.snap(page, EVID, "recon4_estrategia_a", full=True)

    if table_a == 0:
        # Estratégia B: ir para events (switch admin), depois ir direto para records (nova URL)
        print("\n[recon4] Estratégia B: events switch + nova goto records")
        page.goto(
            f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        page.wait_for_timeout(2000)
        tw.dispensar_nps(page)

        page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)
        try:
            with page.expect_response(
                lambda r: f"/api/v1/o/{ORG_ID}/records?" in r.url and r.status == 200,
                timeout=20000
            ):
                pass
        except Exception as e:
            print(f"  Timeout API: {e}")
        page.wait_for_timeout(6000)
        tw.dispensar_nps(page)
        page.evaluate("() => document.querySelectorAll('iframe').forEach(f => f.style.display='none')")

        spinner_b = page.locator(".chakra-spinner").count()
        table_b = page.locator("table").count()
        print(f"  Estratégia B — spinner: {spinner_b}, table: {table_b}")
        tw.snap(page, EVID, "recon4_estrategia_b", full=True)

    if table_a == 0:
        # Estratégia C: usar context fresh, ir direto para records
        print("\n[recon4] Estratégia C: contexto fresh, goto records")
        ctx2 = browser.new_context(locale="pt-BR", viewport={"width": 1500, "height": 950})
        page2 = ctx2.new_page()
        page2.on("dialog", lambda d: d.accept())

        # Restaurar session via cookies da ctx
        cookies = ctx.cookies()
        ctx2.add_cookies(cookies)

        page2.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)
        try:
            with page2.expect_response(
                lambda r: f"/api/v1/o/{ORG_ID}/records?" in r.url and r.status == 200,
                timeout=20000
            ):
                pass
        except Exception as e:
            print(f"  Timeout API: {e}")
        page2.wait_for_timeout(6000)
        tw.dispensar_nps(page2)
        page2.evaluate("() => document.querySelectorAll('iframe').forEach(f => f.style.display='none')")

        spinner_c = page2.locator(".chakra-spinner").count()
        table_c = page2.locator("table").count()
        print(f"  Estratégia C — spinner: {spinner_c}, table: {table_c}")
        tw.snap(page2, EVID, "recon4_estrategia_c", full=True)

        rows_c = page2.locator("table tbody tr").count()
        print(f"  Estratégia C — linhas: {rows_c}")

        # Inspecionar headers
        headers = page2.evaluate("""
            () => {
                const ths = document.querySelectorAll('table th, [role="columnheader"]');
                return Array.from(ths).map(th => th.innerText.trim().replace(/\\n/g,' ').substring(0,40));
            }
        """)
        print(f"  Headers: {headers}")

        ctx2.close()

    ctx.close()
    browser.close()
