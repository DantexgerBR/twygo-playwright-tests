"""Verifica corpo da resposta da API /records e inspeciona DOM mais a fundo."""
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

    # Capturar todas as respostas com body
    api_responses = {}

    def capture_response(resp):
        if f"/o/{ORG_ID}/records" in resp.url and "stats" not in resp.url:
            try:
                body = resp.json()
                api_responses[resp.url] = {
                    "status": resp.status,
                    "body_keys": list(body.keys()) if isinstance(body, dict) else f"list[{len(body)}]",
                    "data_count": len(body.get("data", [])) if isinstance(body, dict) else len(body) if isinstance(body, list) else "?",
                    "body_sample": str(body)[:500]
                }
            except Exception as e:
                api_responses[resp.url] = {"status": resp.status, "error": str(e)}

    page.on("response", capture_response)

    # Navegar para records
    print(f"\n[check] Navegando para {RECORDS_URL}")
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)

    # Aguardar resposta da API
    page.wait_for_timeout(8000)
    tw.dispensar_nps(page)

    print("\n=== Respostas /records ===")
    for url, info in api_responses.items():
        print(f"\nURL: {url}")
        for k, v in info.items():
            if k == "body_sample":
                print(f"  body_sample: {v[:400]}")
            else:
                print(f"  {k}: {v}")

    # Screenshot do estado atual
    tw.snap(page, EVID, "api_check_estado", full=True)

    # Inspecionar o que está no main content
    main_html = page.evaluate("""
        () => {
            const main = document.querySelector('main, [role="main"], .chakra-box, #root > div > div:last-child');
            const content = document.querySelector('[class*="records"], [class*="Records"], [class*="content"]');
            return {
                main_html: main ? main.outerHTML.substring(0, 3000) : 'sem main',
                content_html: content ? content.outerHTML.substring(0, 3000) : 'sem content div',
                all_divs_count: document.querySelectorAll('div').length,
                spinner_details: Array.from(document.querySelectorAll('.chakra-spinner')).map(s => s.outerHTML),
                body_text_500: document.body.innerText.substring(0, 500)
            };
        }
    """)

    print("\n=== DOM main content ===")
    print(f"div count: {main_html.get('all_divs_count')}")
    print(f"spinner details: {main_html.get('spinner_details')}")
    print(f"\nbody text 500:\n{main_html.get('body_text_500')}")
    print(f"\nmain_html sample:\n{main_html.get('main_html')[:2000]}")
    print(f"\ncontent_html sample:\n{main_html.get('content_html')[:2000]}")

    ctx.close()
    browser.close()
