"""Recon3 — inspeciona DOM da tabela após reload."""
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

    # Navegar + reload para forçar carga
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(1500)
    page.reload(wait_until="domcontentloaded")
    try:
        with page.expect_response(
            lambda r: f"/api/v1/o/{ORG_ID}/records?" in r.url and r.status == 200,
            timeout=20000
        ):
            pass
    except Exception as e:
        print(f"Timeout: {e}")
    page.wait_for_timeout(5000)
    tw.dispensar_nps(page)

    # Fechar sophia
    page.evaluate("() => document.querySelectorAll('iframe').forEach(f => f.style.display='none')")

    tw.snap(page, EVID, "recon3_tabela_carregada", full=True)

    dom_info = page.evaluate("""
        () => {
            const r = {};
            r.spinner = document.querySelectorAll('.chakra-spinner').length;
            r.table = !!document.querySelector('table');
            r.tbody_tr = document.querySelectorAll('table tbody tr').length;

            // Headers da tabela
            const ths = document.querySelectorAll('table th, [role="columnheader"]');
            r.headers = Array.from(ths).map(th => th.innerText.trim().replace(/\\n/g,' ').substring(0,40));

            // Chakra checkboxes
            r.chakra_cb_control = document.querySelectorAll('.chakra-checkbox__control').length;
            r.chakra_cb_input = document.querySelectorAll('.chakra-checkbox__input').length;

            // First row cells
            const firstRow = document.querySelector('table tbody tr');
            if (firstRow) {
                r.first_row_cells = Array.from(firstRow.querySelectorAll('td')).map(td => td.innerText.trim().substring(0,60));
            }

            // Toggle grid button (aria-label)
            const btns = Array.from(document.querySelectorAll('button'));
            r.buttons_texts = btns.map(b => b.innerText.trim().substring(0,30) + '|aria=' + (b.getAttribute('aria-label')||'')).filter(t => t.length > 2).slice(0,30);

            // Pagination elements
            const pag = document.querySelector('[class*="pagination"], [class*="Pagination"]');
            r.pagination_text = pag ? pag.innerText.trim().substring(0,200) : 'sem paginacao';

            // Breadcrumb
            const nav = document.querySelector('[aria-label="breadcrumb"], nav');
            r.breadcrumb = nav ? nav.innerText.trim().substring(0,100) : 'sem breadcrumb';

            return r;
        }
    """)
    print("=== RECON3 DOM ===")
    for k, v in dom_info.items():
        print(f"  {k}: {v}")

    ctx.close()
    browser.close()
