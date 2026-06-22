"""Recon2 — espera resposta da API /records antes de inspecionar DOM."""
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

    # Navegar para records e aguardar resposta da API
    print(f"\n[recon2] Navegando para {RECORDS_URL}")
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)

    # Esperar pela resposta da API de records (não networkidle)
    try:
        with page.expect_response(
            lambda r: "/api/v1/o/37079/records" in r.url and "stats" not in r.url and r.status == 200,
            timeout=30000
        ) as resp_info:
            pass
        resp = resp_info.value
        body = resp.json()
        print(f"\n[API] Status: {resp.status}")
        print(f"[API] URL: {resp.url}")
        total = len(body) if isinstance(body, list) else body.get("total", "?") if isinstance(body, dict) else "?"
        print(f"[API] Registros retornados: {total}")
        if isinstance(body, dict):
            print(f"[API] Keys: {list(body.keys())[:10]}")
        elif isinstance(body, list) and len(body) > 0:
            print(f"[API] Primeiro item keys: {list(body[0].keys())[:10] if isinstance(body[0], dict) else str(body[0])[:100]}")
    except Exception as e:
        print(f"[API] Timeout esperando /records: {e}")

    # Aguardar mais 5s para React processar
    page.wait_for_timeout(5000)
    tw.dispensar_nps(page)
    tw.snap(page, EVID, "recon2_pos_api_load", full=True)

    # Inspecionar DOM
    dom_info = page.evaluate("""
        () => {
            const r = {};
            r.spinner = document.querySelectorAll('.chakra-spinner').length;
            r.table = document.querySelector('table') ? 'SIM' : 'NAO';
            r.table_th = document.querySelectorAll('table th').length;
            r.table_tr = document.querySelectorAll('table tbody tr').length;
            r.role_row = document.querySelectorAll('[role="row"]').length;
            r.role_columnheader = document.querySelectorAll('[role="columnheader"]').length;

            // Chakra checkbox
            r.chakra_cb = document.querySelectorAll('.chakra-checkbox__control').length;

            // Headers da tabela
            const ths = document.querySelectorAll('table th, [role="columnheader"]');
            r.header_texts = Array.from(ths).map(th => th.innerText.trim().replace(/\\n/g,' ').substring(0,40));

            // Primeiros TDs da tabela
            const tds = document.querySelectorAll('table tbody td');
            r.first_5_td = Array.from(tds).slice(0,5).map(td => td.innerText.trim().substring(0,60));

            // innerHTML da table completo (para debug de estrutura)
            const table = document.querySelector('table');
            r.table_structure = table ? table.outerHTML.substring(0, 5000) : 'sem table';

            return r;
        }
    """)
    print("\n=== DOM após carregar ===")
    for k, v in dom_info.items():
        if k == 'table_structure':
            print(f"\n--- table HTML ---\n{v[:3000]}\n---")
        else:
            print(f"  {k}: {v}")

    ctx.close()
    browser.close()
