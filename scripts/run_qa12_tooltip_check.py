"""Verificar tooltip do ícone de ajuda do header Provedor."""
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
    # NÃO suprimir iframes para não suprimir popovers do Chakra
    # page.evaluate("() => document.querySelectorAll('iframe').forEach(f => f.style.display='none')")

    # Encontrar o header Provedor (index 6) e seu ícone de info
    headers_info = page.evaluate("""
        () => {
            const ths = document.querySelectorAll('table thead th');
            for (const th of ths) {
                if (th.textContent.trim().includes('Provedor')) {
                    const rect = th.getBoundingClientRect();
                    const svgs = th.querySelectorAll('svg');
                    const buttons = th.querySelectorAll('button');
                    const icons = [];
                    for (const svg of svgs) {
                        const svgRect = svg.getBoundingClientRect();
                        icons.push({type:'svg', x: Math.round(svgRect.x + svgRect.width/2), y: Math.round(svgRect.y + svgRect.height/2)});
                    }
                    for (const btn of buttons) {
                        const btnRect = btn.getBoundingClientRect();
                        icons.push({type:'button', x: Math.round(btnRect.x + btnRect.width/2), y: Math.round(btnRect.y + btnRect.height/2)});
                    }
                    return {
                        th_x: Math.round(rect.x),
                        th_y: Math.round(rect.y),
                        th_w: Math.round(rect.width),
                        th_h: Math.round(rect.height),
                        icons: icons
                    };
                }
            }
            return null;
        }
    """)
    print(f"Header Provedor info: {headers_info}")

    if headers_info and headers_info.get('icons'):
        icon = headers_info['icons'][0]
        print(f"Hovering sobre ícone em ({icon['x']}, {icon['y']})")
        page.mouse.move(icon['x'], icon['y'])
        page.wait_for_timeout(2000)
        tw.snap(page, EVID, "tc2_tooltip_hover_icon")

        # Verificar tooltip via ARIA
        tooltip_aria = page.evaluate("""
            () => {
                const tooltips = document.querySelectorAll('[role="tooltip"]');
                const popover = document.querySelectorAll('[id*="tooltip"], [class*="tooltip"], [class*="Popover"], [class*="popover"]');
                const all_hidden = document.querySelectorAll('[style*="display: block"], [style*="visibility: visible"], [aria-hidden="false"]');
                const result = {
                    tooltips: Array.from(tooltips).map(t => ({text: t.textContent.trim().substring(0,200), visible: t.style.display !== 'none'})),
                    popover: Array.from(popover).map(t => ({text: t.textContent.trim().substring(0,100), class: t.className.substring(0,60)})),
                };
                return result;
            }
        """)
        print(f"Tooltips: {tooltip_aria}")
    else:
        # Fallback: hover no header inteiro
        th_x = headers_info['th_x'] + headers_info['th_w'] - 10 if headers_info else 900
        th_y = headers_info['th_y'] + 10 if headers_info else 400
        print(f"Hovering no header em ({th_x}, {th_y})")
        page.mouse.move(th_x, th_y)
        page.wait_for_timeout(2000)
        tw.snap(page, EVID, "tc2_tooltip_header_right")

    ctx.close()
    browser.close()
