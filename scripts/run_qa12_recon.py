"""Recon rápido — inspeciona DOM da tabela de Registros."""
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


def login_admin(page):
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("#user_email", timeout=10000)
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


def ir_registros(page):
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(5000)
    tw.dispensar_nps(page)
    # Fechar sophia
    page.evaluate("() => { document.querySelectorAll('iframe').forEach(f => f.style.display='none'); }")
    # Aguardar spinner sumir
    try:
        page.wait_for_selector(".chakra-spinner, [class*='spinner']", state="hidden", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    login_admin(page)
    ir_registros(page)

    tw.snap(page, EVID, "recon_tabela_pos_load", full=True)

    # Inspecionar estrutura do header da tabela
    html_info = page.evaluate("""
        () => {
            const results = {};

            // Testar seletores de header
            results['table_th'] = document.querySelectorAll('table th').length;
            results['thead_th'] = document.querySelectorAll('thead th').length;
            results['role_columnheader'] = document.querySelectorAll('[role="columnheader"]').length;
            results['table_rows'] = document.querySelectorAll('table tbody tr').length;
            results['role_row'] = document.querySelectorAll('[role="row"]').length;

            // Pegar textos dos headers
            const ths = document.querySelectorAll('table th, [role="columnheader"]');
            results['header_texts'] = Array.from(ths).map(th => th.innerText.trim().replace(/\\n/g, ' ').substring(0,50));

            // Verificar se tabela tem conteúdo
            const tds = document.querySelectorAll('table td');
            results['table_tds'] = tds.length;
            results['first_row_text'] = tds.length > 0 ? tds[0].innerText.trim().substring(0,100) : 'vazio';

            // Chakra checkbox
            results['chakra_checkbox_input'] = document.querySelectorAll('.chakra-checkbox__input').length;
            results['chakra_checkbox_control'] = document.querySelectorAll('.chakra-checkbox__control').length;

            // Spinner
            results['spinner'] = document.querySelectorAll('.chakra-spinner, [class*="spinner"]').length;

            // Toda a tabela HTML (primeiros 2000 chars)
            const table = document.querySelector('table');
            results['table_html_sample'] = table ? table.outerHTML.substring(0, 3000) : 'table não encontrada';

            return results;
        }
    """)

    print("=== RECON DOM ===")
    for k, v in html_info.items():
        if k == 'table_html_sample':
            print(f"\n--- table HTML sample ---\n{v}\n---")
        else:
            print(f"  {k}: {v}")

    # Verificar se a tabela tem dados mas spinner ainda aparece
    spinner_count = page.locator(".chakra-spinner").count()
    print(f"\nSpinners visíveis: {spinner_count}")

    # Ver linhas
    trs = page.locator("table tbody tr").count()
    print(f"table tbody tr count: {trs}")

    # Ver via role=row
    rows = page.locator("[role='row']").count()
    print(f"role=row count: {rows}")

    ctx.close()
    browser.close()
