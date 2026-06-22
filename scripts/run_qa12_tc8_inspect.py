"""Inspeção DOM dos toggles grid/lista."""
import os, sys
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
    page.on("dialog", lambda d: d.accept())

    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.fill("#user_email", ADMIN_EMAIL)
    page.fill("#user_password", ADMIN_PASSWORD)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    page.goto(f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
              wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)

    # Inspecionar a área entre busca e Filtro
    html_toggle_area = page.evaluate("""
        () => {
            const busca = document.querySelector('input[placeholder*="Pesquise"]');
            const filtro = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Filtro'));
            if (!busca || !filtro) return 'não encontrou';
            const buscaRect = busca.getBoundingClientRect();
            const filtroRect = filtro.getBoundingClientRect();
            // Pegar todos os elementos interativos nessa área
            const result = [];
            document.querySelectorAll('button, [role="button"], [tabindex], a, div[class*="toggle"], div[class*="view"]').forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.x > buscaRect.right && rect.x < filtroRect.x && Math.abs(rect.y - filtroRect.y) < 30) {
                    result.push({
                        tag: el.tagName,
                        class: el.className.substring(0,80),
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        w: Math.round(rect.width),
                        h: Math.round(rect.height),
                        text: el.textContent.trim().substring(0,20),
                        role: el.getAttribute('role') || '',
                        ariLabel: el.getAttribute('aria-label') || ''
                    });
                }
            });
            return result;
        }
    """)
    print(f"\n=== Elementos entre busca e Filtro ===")
    if isinstance(html_toggle_area, list):
        for item in html_toggle_area:
            print(f"  tag={item['tag']} x={item['x']} y={item['y']} w={item['w']} h={item['h']}")
            print(f"    class='{item['class']}'")
            print(f"    text='{item['text']}' role='{item['role']}' aria='{item['ariLabel']}'")
    else:
        print(html_toggle_area)

    # Tentar clicar por coordenadas diretas (1295, 382 aprox)
    print("\n=== Clicando por coordenadas (aprox toggle grid: 1295, 382) ===")
    page.mouse.click(1295, 382)
    page.wait_for_timeout(1500)
    tw.snap(page, EVID, "tc8_inspect_apos_click_toggle")

    rows = page.locator("table tbody tr").count()
    cards_generic = page.locator("[class*='grid'], [class*='card-list'], [class*='CardList']").count()
    print(f"rows={rows}, cards={cards_generic}")

    ctx.close()
    browser.close()
