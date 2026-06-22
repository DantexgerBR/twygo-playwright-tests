"""Captura erros de console e aguarda mais tempo para a tabela renderizar."""
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

console_errors = []
console_msgs = []


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)

    page.on("console", lambda msg: console_msgs.append(f"[{msg.type}] {msg.text[:200]}") if msg.type in ("error", "warning") else None)
    page.on("pageerror", lambda err: console_errors.append(str(err)[:300]))

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

    print(f"\n[console_check] Navegando para {RECORDS_URL}")
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)

    # Aguardar resposta da API
    try:
        with page.expect_response(
            lambda r: f"/api/v1/o/{ORG_ID}/records?" in r.url and r.status == 200,
            timeout=20000
        ):
            pass
    except Exception as e:
        print(f"Timeout esperando API: {e}")

    # Aguardar mais 10s para React renderizar
    page.wait_for_timeout(10000)
    tw.dispensar_nps(page)

    tw.snap(page, EVID, "console_check_estado", full=True)

    # Verificar tabela
    has_table = page.locator("table").count()
    spinner = page.locator(".chakra-spinner").count()
    print(f"\nTabela presente: {has_table}, Spinner: {spinner}")

    print(f"\n=== Console Errors ===")
    for e in console_errors:
        print(f"  PAGE ERROR: {e}")
    for m in console_msgs[:20]:
        print(f"  {m}")

    # Tentar clicar em algo para "acordar" o React
    print("\n[debug] Tentando interagir com a página...")
    # Clicar na aba Registros (já ativa, mas pode disparar re-render)
    tab_reg = page.locator("button, [role='tab']").filter(has_text="Registros").first
    if tab_reg.is_visible():
        tab_reg.click()
        page.wait_for_timeout(3000)
        tw.snap(page, EVID, "console_check_apos_click_tab", full=True)
        has_table2 = page.locator("table").count()
        spinner2 = page.locator(".chakra-spinner").count()
        print(f"Após clicar aba Registros — Tabela: {has_table2}, Spinner: {spinner2}")

    # Tentar recarregar a página via F5 (sem cache)
    print("\n[debug] Recarregando página...")
    page.reload(wait_until="domcontentloaded")
    try:
        with page.expect_response(
            lambda r: f"/api/v1/o/{ORG_ID}/records?" in r.url and r.status == 200,
            timeout=20000
        ):
            pass
    except Exception:
        pass
    page.wait_for_timeout(8000)
    tw.dispensar_nps(page)

    tw.snap(page, EVID, "console_check_apos_reload", full=True)
    has_table3 = page.locator("table").count()
    spinner3 = page.locator(".chakra-spinner").count()
    print(f"Após reload — Tabela: {has_table3}, Spinner: {spinner3}")

    # DOM inspection
    dom = page.evaluate("""
        () => ({
            spinner: document.querySelectorAll('.chakra-spinner').length,
            table: !!document.querySelector('table'),
            tbody_tr: document.querySelectorAll('table tbody tr').length,
            all_text_nodes_500: document.body.innerText.substring(0, 500),
            records_container: document.querySelector('[data-testid*="record"], [class*="records-list"], [class*="RecordsList"]') ? 'FOUND' : 'NOT FOUND',
            react_root: document.querySelector('#root, [data-reactroot]') ? 'FOUND' : 'NOT FOUND'
        })
    """)
    print("\n=== DOM após reload ===")
    for k, v in dom.items():
        print(f"  {k}: {v}")

    ctx.close()
    browser.close()
