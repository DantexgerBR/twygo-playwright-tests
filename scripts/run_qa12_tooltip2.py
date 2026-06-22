"""Tooltip do Provedor — tentar segundo ícone SVG."""
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

    # Hover no segundo SVG do header Provedor (1147, 446)
    page.mouse.move(400, 600)  # mover para longe primeiro
    page.wait_for_timeout(500)
    page.mouse.move(1147, 446)
    page.wait_for_timeout(2000)
    tw.snap(page, EVID, "tc2_tooltip_svg2")

    # Verificar tooltip via chakra tooltip
    tooltip_data = page.evaluate("""
        () => {
            // Procurar qualquer elemento com text visível após o hover
            const tooltips = document.querySelectorAll('[role="tooltip"], .chakra-tooltip, [id*="tooltip-"]');
            const result = [];
            for (const t of tooltips) {
                const style = window.getComputedStyle(t);
                result.push({
                    text: t.textContent.trim().substring(0, 200),
                    visible: style.display !== 'none' && style.visibility !== 'hidden',
                    class: t.className.substring(0, 60)
                });
            }
            // Também verificar o aria-describedby do elemento focado
            const focused = document.activeElement;
            return {
                tooltips: result,
                focused_describedby: focused ? focused.getAttribute('aria-describedby') : null
            };
        }
    """)
    print(f"Tooltip data: {tooltip_data}")

    # Tentar via Playwright locator — chakra tooltip aparece com [role=tooltip]
    tooltips = page.locator('[role="tooltip"]')
    print(f"Tooltips via locator: {tooltips.count()}")
    if tooltips.count() > 0:
        for i in range(tooltips.count()):
            t = tooltips.nth(i)
            try:
                print(f"  tooltip[{i}]: '{t.text_content()[:200]}'")
            except Exception as e:
                print(f"  tooltip[{i}]: erro {e}")

    # Verificar o HTML do header Provedor para entender a estrutura
    provedor_html = page.evaluate("""
        () => {
            const ths = document.querySelectorAll('table thead th');
            for (const th of ths) {
                if (th.textContent.trim().includes('Provedor')) {
                    return th.innerHTML.substring(0, 500);
                }
            }
            return 'não encontrado';
        }
    """)
    print(f"\nHTML do header Provedor:\n{provedor_html}")

    ctx.close()
    browser.close()
