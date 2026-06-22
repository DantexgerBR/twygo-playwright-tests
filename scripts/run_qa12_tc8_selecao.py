"""TC8 - testar seleção de card em modo grid + borda roxa."""
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

    # Ativar modo grid
    page.mouse.click(1295, 382)
    page.wait_for_timeout(2000)
    tw.snap(page, EVID, "tc8sel_01_grid_ativo")

    # Verificar cards
    cards = page.locator("[class*='card'], [class*='Card']")
    print(f"Cards em grid: {cards.count()}")

    # Marcar checkbox do primeiro card — canto superior direito
    # Localizar checkboxes nos cards
    card_cbs = page.locator("[class*='card'] input[type='checkbox'], [class*='Card'] input[type='checkbox']")
    if card_cbs.count() == 0:
        # Chakra checkbox control dentro de card
        card_cbs = page.locator("[class*='card'] .chakra-checkbox__control")
    print(f"Checkboxes nos cards: {card_cbs.count()}")

    if card_cbs.count() > 0:
        # Clicar no primeiro checkbox de card
        card_cbs.first.click(timeout=5000)
        page.wait_for_timeout(800)
        tw.snap(page, EVID, "tc8sel_02_card_marcado")

        # Verificar borda roxa do card
        borda_info = page.evaluate("""
            () => {
                // Procurar input checkbox marcado e subir para container do card
                const inputs = document.querySelectorAll('input[type="checkbox"]:checked');
                for (const inp of inputs) {
                    let el = inp.parentElement;
                    for (let i = 0; i < 15; i++) {
                        if (!el) break;
                        const style = window.getComputedStyle(el);
                        const border = style.border || '';
                        const borderColor = style.borderColor || '';
                        const outline = style.outline || '';
                        const boxShadow = style.boxShadow || '';
                        const combined = (border + borderColor + outline + boxShadow).toLowerCase();
                        // Roxo/purple: rgb(124, 58, 237) = #7c3aed
                        if (combined.includes('7c3aed') || combined.includes('124, 58, 237') ||
                            combined.includes('purple') || combined.includes('violet') ||
                            (combined.includes('rgb') && (combined.includes('58, 237') || combined.includes('100, 0, 255')))) {
                            return {level: i, class: el.className.substring(0,60), border: border.substring(0,80), borderColor: borderColor.substring(0,60)};
                        }
                        el = el.parentElement;
                    }
                }
                // Fallback: inspecionar o primeiro card selecionado visualmente
                const allInputs = document.querySelectorAll('input[type="checkbox"]');
                const results = [];
                for (const inp of allInputs) {
                    if (inp.checked) {
                        let el = inp.parentElement;
                        for (let i = 0; i < 6; i++) {
                            if (!el) break;
                            const style = window.getComputedStyle(el);
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 100) {
                                results.push({
                                    level: i,
                                    class: el.className.substring(0,60),
                                    border: style.border.substring(0,80),
                                    borderColor: style.borderColor.substring(0,60),
                                    boxShadow: style.boxShadow.substring(0,80),
                                    w: Math.round(rect.width)
                                });
                                break;
                            }
                            el = el.parentElement;
                        }
                    }
                }
                return results.length > 0 ? results[0] : 'nenhum_checked';
            }
        """)
        print(f"Borda card selecionado: {borda_info}")

        # Desmarcar
        card_cbs.first.click(timeout=5000)
        page.wait_for_timeout(500)
        tw.snap(page, EVID, "tc8sel_03_card_desmarcado")
    else:
        print("Sem checkboxes de card")

    ctx.close()
    browser.close()
