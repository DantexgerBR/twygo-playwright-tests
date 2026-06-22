"""TC2 check — verificar colunas exatas, 'Criado por', tooltip do Provedor."""
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
    page.evaluate("() => document.querySelectorAll('iframe').forEach(f => f.style.display='none')")

    # Pegar todos os headers da tabela
    headers = page.evaluate("""
        () => {
            const ths = document.querySelectorAll('table thead th');
            return Array.from(ths).map((th, i) => ({
                index: i,
                text: th.textContent.trim().substring(0, 80),
                hasIcon: th.querySelector('svg, [aria-label]') !== null
            }));
        }
    """)
    print("=== COLUNAS DA TABELA ===")
    for h in headers:
        print(f"  [{h['index']}] '{h['text']}' (icon={h['hasIcon']})")

    # Verificar se "Criado por" está presente
    criado_por_present = any("Criado" in h['text'] for h in headers)
    print(f"\nColuna 'Criado por' presente: {criado_por_present}")

    # Hover sobre o ícone de ajuda do header Provedor (deve ter tooltip)
    provedor_header = None
    for h in headers:
        if "Provedor" in h['text'] or "provedor" in h['text'].lower():
            provedor_header = h
            break
    print(f"\nHeader Provedor: {provedor_header}")

    if provedor_header is not None:
        # Encontrar o elemento th do Provedor
        th_locator = page.locator(f"table thead th").nth(provedor_header['index'])
        # Hover no ícone de ajuda (svg/circle-info) dentro do th
        icon = th_locator.locator("svg, [aria-label*='info'], [aria-label*='ajuda'], button")
        if icon.count() > 0:
            icon.first.hover()
            page.wait_for_timeout(1500)
            tw.snap(page, EVID, "tc2_tooltip_provedor")
            # Pegar texto do tooltip
            tooltip_text = page.evaluate("""
                () => {
                    const tooltips = document.querySelectorAll('[role="tooltip"], [class*="tooltip"], [class*="Tooltip"]');
                    return Array.from(tooltips).map(t => t.textContent.trim().substring(0, 200));
                }
            """)
            print(f"\nTooltip textos: {tooltip_text}")
        else:
            print("Sem ícone no header Provedor")
            # Hover no próprio th para tentar tooltip
            th_locator.hover()
            page.wait_for_timeout(1500)
            tooltip_text = page.evaluate("""
                () => {
                    const tooltips = document.querySelectorAll('[role="tooltip"], [class*="tooltip"], [class*="Tooltip"]');
                    return Array.from(tooltips).map(t => t.textContent.trim().substring(0, 200));
                }
            """)
            print(f"Tooltip após hover no th: {tooltip_text}")
            tw.snap(page, EVID, "tc2_tooltip_provedor_th")

    # Verificar coluna Criado por: pegar o valor da primeira célula
    if criado_por_present:
        criado_idx = next(i for i, h in enumerate(headers) if "Criado" in h['text'])
        criado_values = page.evaluate(f"""
            () => {{
                const rows = document.querySelectorAll('table tbody tr');
                const vals = [];
                for (const row of Array.from(rows).slice(0,3)) {{
                    const cells = row.querySelectorAll('td');
                    if (cells.length > {criado_idx}) {{
                        vals.push(cells[{criado_idx}].textContent.trim().substring(0,50));
                    }}
                }}
                return vals;
            }}
        """)
        print(f"\nValores 'Criado por' (primeiros 3): {criado_values}")
    else:
        print("\n'Criado por' ausente — TC2 FALHOU por ausência de coluna admin-exclusiva")

    ctx.close()
    browser.close()
